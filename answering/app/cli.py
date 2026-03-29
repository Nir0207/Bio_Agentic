from __future__ import annotations

import json
import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import typer

from answering.app.config import Settings, get_settings
from answering.app.logging import configure_logging
from answering.renderers import EvidenceAppendixRenderer, JSONRenderer, MarkdownRenderer
from answering.schemas.answer_models import AnswerStyle, FinalAnswerPayload, ModelInfo
from answering.schemas.render_models import LLMAnswerDraft
from answering.schemas.verified_payload_models import VerifiedPayload
from answering.services import (
    AnswerRenderer,
    CitationFormatter,
    FallbackRenderer,
    LLMClient,
    LLMRunMetadata,
    LLMUnavailableError,
    PromptBuilder,
    ResponsePackager,
)

logger = logging.getLogger(__name__)

app = typer.Typer(add_completion=False, help="Standalone answering phase for verified payload rendering")
answer_app = typer.Typer(add_completion=False, invoke_without_command=True)
render_app = typer.Typer(add_completion=False)
run_app = typer.Typer(add_completion=False)

app.add_typer(answer_app, name="answer")
app.add_typer(render_app, name="render")
app.add_typer(run_app, name="run")


@dataclass
class PipelineResult:
    final_payload: FinalAnswerPayload
    markdown_output: str
    json_output: str
    appendix_output: str


def _load_payload(input_path: Path) -> dict[str, Any]:
    if not input_path.exists():
        raise typer.BadParameter(f"Payload file not found: {input_path}")

    try:
        return json.loads(input_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise typer.BadParameter(f"Invalid JSON payload: {input_path} ({exc})") from exc


def _load_sample_payload(settings: Settings) -> dict[str, Any]:
    return _load_payload(settings.resolved_sample_payload_path)


def _run_pipeline(
    payload_data: dict[str, Any],
    *,
    settings: Settings,
    style: AnswerStyle | None = None,
) -> PipelineResult:
    answer_style = style or settings.answer_style
    verified_payload = VerifiedPayload.model_validate(payload_data)

    citation_formatter = CitationFormatter()
    prompt_builder = PromptBuilder()
    llm_client = LLMClient(settings)
    fallback_renderer = FallbackRenderer()
    answer_renderer = AnswerRenderer()
    appendix_renderer = EvidenceAppendixRenderer()
    response_packager = ResponsePackager()
    markdown_renderer = MarkdownRenderer()
    json_renderer = JSONRenderer()

    citations = citation_formatter.format(verified_payload)
    prompt_bundle = prompt_builder.build(verified_payload, citations, style=answer_style)

    llm_draft: LLMAnswerDraft
    run_meta: LLMRunMetadata
    try:
        llm_draft, run_meta = llm_client.generate(prompt_bundle)
    except LLMUnavailableError as exc:
        logger.warning("LLM unavailable, switching to fallback renderer: %s", exc)
        llm_draft = fallback_renderer.render(verified_payload, citations, style=answer_style)
        run_meta = LLMRunMetadata(
            provider=settings.answering_provider,
            model_name=settings.answering_model_name,
            fallback_used=True,
        )

    rendered_answer = answer_renderer.render(
        verified_payload,
        llm_draft,
        citations,
        style=answer_style,
    )
    evidence_appendix = appendix_renderer.render(verified_payload, citations, settings=settings)

    model_info = ModelInfo(
        provider=run_meta.provider,
        model_name=run_meta.model_name,
        temperature=settings.answering_temperature,
        fallback_used=run_meta.fallback_used,
    )

    final_payload = response_packager.package(
        verified_payload,
        rendered_answer,
        citations,
        answer_style=answer_style,
        model_info=model_info,
        evidence_appendix=evidence_appendix,
    )

    markdown_output = markdown_renderer.render(final_payload)
    json_output = json_renderer.render(final_payload)
    appendix_output = _render_appendix_text(final_payload)

    return PipelineResult(
        final_payload=final_payload,
        markdown_output=markdown_output,
        json_output=json_output,
        appendix_output=appendix_output,
    )


def _render_appendix_text(payload: FinalAnswerPayload) -> str:
    appendix = payload.evidence_appendix
    lines: list[str] = []

    lines.append("Graph Evidence Items:")
    if appendix.graph_evidence_items:
        lines.extend([f"- {item}" for item in appendix.graph_evidence_items])
    else:
        lines.append("- None")

    lines.append("")
    lines.append("Publication and Evidence Citations:")
    if appendix.publication_and_evidence_citations:
        lines.extend([f"- {item}" for item in appendix.publication_and_evidence_citations])
    else:
        lines.append("- None")

    lines.append("")
    lines.append("Unresolved Gaps:")
    if appendix.unresolved_gaps:
        lines.extend([f"- {item}" for item in appendix.unresolved_gaps])
    else:
        lines.append("- None")

    lines.append("")
    lines.append("Warnings:")
    if appendix.warnings:
        lines.extend([f"- {item}" for item in appendix.warnings])
    else:
        lines.append("- None")

    return "\n".join(lines)


@answer_app.callback()
def answer_payload(
    ctx: typer.Context,
    input: Path | None = typer.Option(None, "--input", exists=False, readable=True),
    style: AnswerStyle | None = typer.Option(None, "--style"),
) -> None:
    if ctx.invoked_subcommand:
        return

    if input is None:
        raise typer.BadParameter("--input is required when calling 'answer' directly")

    settings = get_settings()
    configure_logging(settings.log_level)

    result = _run_pipeline(_load_payload(input), settings=settings, style=style)
    typer.echo(result.final_payload.answer_text)


@answer_app.command("sample")
def answer_sample(
    style: AnswerStyle | None = typer.Option(None, "--style"),
) -> None:
    settings = get_settings()
    configure_logging(settings.log_level)

    result = _run_pipeline(_load_sample_payload(settings), settings=settings, style=style)
    typer.echo(result.final_payload.answer_text)


@render_app.command("markdown")
def render_markdown(
    input: Path = typer.Option(..., "--input", exists=False, readable=True),
    style: AnswerStyle | None = typer.Option(None, "--style"),
) -> None:
    settings = get_settings()
    configure_logging(settings.log_level)

    result = _run_pipeline(_load_payload(input), settings=settings, style=style)
    typer.echo(result.markdown_output)


@render_app.command("json")
def render_json(
    input: Path = typer.Option(..., "--input", exists=False, readable=True),
    style: AnswerStyle | None = typer.Option(None, "--style"),
) -> None:
    settings = get_settings()
    configure_logging(settings.log_level)

    result = _run_pipeline(_load_payload(input), settings=settings, style=style)
    typer.echo(result.json_output)


@render_app.command("appendix")
def render_appendix(
    input: Path = typer.Option(..., "--input", exists=False, readable=True),
    style: AnswerStyle | None = typer.Option(None, "--style"),
) -> None:
    settings = get_settings()
    configure_logging(settings.log_level)

    result = _run_pipeline(_load_payload(input), settings=settings, style=style)
    typer.echo(result.appendix_output)


@run_app.command("all")
def run_all(
    input: Path | None = typer.Option(None, "--input", exists=False, readable=True),
    style: AnswerStyle | None = typer.Option(None, "--style"),
) -> None:
    settings = get_settings()
    configure_logging(settings.log_level)

    typer.echo("1) load verified payload")
    payload_data = _load_payload(input) if input else _load_sample_payload(settings)

    typer.echo("2) build grounded prompt")
    typer.echo("3) generate answer (LLM or fallback)")
    typer.echo("4) format deterministic citations")
    typer.echo("5) package structured answer JSON")
    typer.echo("6) render markdown + appendix")

    result = _run_pipeline(payload_data, settings=settings, style=style)
    payload = result.final_payload
    typer.echo("7) pipeline complete")
    typer.echo(
        f"summary: verdict={payload.overall_verdict}, confidence={payload.overall_confidence:.2f}, "
        f"style={payload.answer_style.value}, fallback={payload.model_info.fallback_used}"
    )


if __name__ == "__main__":
    app()
