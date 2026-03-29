from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import typer

from verification.app.config import Settings, get_settings
from verification.app.logging import configure_logging
from verification.app.state import VerificationState
from verification.nodes.compute_verdict import compute_verdict_node
from verification.nodes.extract_claims import extract_claims_node
from verification.nodes.finalize_verified_payload import finalize_verified_payload_node
from verification.nodes.request_human_review import request_human_review_node
from verification.nodes.verify_citations import verify_citations_node
from verification.nodes.verify_graph_support import verify_graph_support_node
from verification.nodes.verify_scores import verify_scores_node
from verification.schemas.evidence_models import VerificationInputPayload
from verification.schemas.verification_models import VerifiedPayload
from verification.services.claim_extractor import ClaimExtractor
from verification.services.citation_verifier import CitationVerifier
from verification.services.graph_verifier import GraphVerifier
from verification.services.score_verifier import ScoreVerifier
from verification.services.verdict_builder import VerdictBuilder

app = typer.Typer(add_completion=False, help="Standalone verification phase for structured claim validation")
verify_app = typer.Typer(add_completion=False)
inspect_app = typer.Typer(add_completion=False)
run_app = typer.Typer(add_completion=False)

app.add_typer(verify_app, name="verify")
app.add_typer(inspect_app, name="inspect")
app.add_typer(run_app, name="run")


def _load_payload(input_path: Path) -> dict[str, Any]:
    if not input_path.exists():
        raise typer.BadParameter(f"Payload file not found: {input_path}")

    try:
        return json.loads(input_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise typer.BadParameter(f"Invalid JSON payload: {input_path} ({exc})") from exc


def _load_sample_payload(settings: Settings) -> dict[str, Any]:
    path = settings.resolved_sample_payload_path
    return _load_payload(path)


def _parse_review_edits(raw: str | None) -> dict[str, Any] | None:
    if raw is None or not raw.strip():
        return None
    try:
        parsed = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise typer.BadParameter(f"review-edits must be valid JSON ({exc})") from exc
    if not isinstance(parsed, dict):
        raise typer.BadParameter("review-edits must decode to a JSON object")
    return parsed


def _run_verification_pipeline(
    payload_data: dict[str, Any],
    *,
    settings: Settings,
    review_action: str | None = None,
    review_edits: dict[str, Any] | None = None,
    emit_steps: bool = False,
) -> VerifiedPayload:
    state: VerificationState = {
        "input_payload": VerificationInputPayload.model_validate(payload_data),
    }

    claim_extractor = ClaimExtractor()
    graph_verifier = GraphVerifier()
    citation_verifier = CitationVerifier()
    score_verifier = ScoreVerifier()
    verdict_builder = VerdictBuilder()

    if emit_steps:
        typer.echo("1) load payload")

    updates = extract_claims_node(state, extractor=claim_extractor)
    state.update(updates)
    if emit_steps:
        typer.echo("2) extract claims")

    updates = verify_graph_support_node(state, verifier=graph_verifier)
    state.update(updates)
    if emit_steps:
        typer.echo("3) verify graph support")

    updates = verify_citations_node(state, verifier=citation_verifier)
    state.update(updates)
    if emit_steps:
        typer.echo("4) verify citations")

    updates = verify_scores_node(state, verifier=score_verifier)
    state.update(updates)
    if emit_steps:
        typer.echo("5) verify scores")

    updates = compute_verdict_node(state, builder=verdict_builder, settings=settings)
    state.update(updates)
    if emit_steps:
        typer.echo("6) compute verdict")

    updates = request_human_review_node(
        state,
        enable_human_review=settings.enable_human_review,
        review_action=review_action,
        review_edits=review_edits,
    )
    state.update(updates)

    review_status = state.get("review_status")
    if emit_steps and review_status and review_status.status == "pending":
        typer.echo("7) review required: pass --review-action approve|reject|edit|continue_with_caveats")

    updates = finalize_verified_payload_node(state)
    state.update(updates)
    if emit_steps:
        typer.echo("8) finalize verified payload")

    return state["final_verified_payload"]


@verify_app.command("payload")
def verify_payload(
    input: Path = typer.Option(..., "--input", exists=False, readable=True),
    review_action: str | None = typer.Option(None, "--review-action"),
    review_edits: str | None = typer.Option(None, "--review-edits"),
) -> None:
    settings = get_settings()
    configure_logging(settings.log_level)

    payload_data = _load_payload(input)
    final_payload = _run_verification_pipeline(
        payload_data,
        settings=settings,
        review_action=review_action,
        review_edits=_parse_review_edits(review_edits),
    )
    typer.echo(json.dumps(final_payload.model_dump(mode="json"), indent=2))


@verify_app.command("sample")
def verify_sample(
    review_action: str | None = typer.Option(None, "--review-action"),
    review_edits: str | None = typer.Option(None, "--review-edits"),
) -> None:
    settings = get_settings()
    configure_logging(settings.log_level)

    payload_data = _load_sample_payload(settings)
    final_payload = _run_verification_pipeline(
        payload_data,
        settings=settings,
        review_action=review_action,
        review_edits=_parse_review_edits(review_edits),
    )
    typer.echo(json.dumps(final_payload.model_dump(mode="json"), indent=2))


@inspect_app.command("claims")
def inspect_claims(input: Path = typer.Option(..., "--input", exists=False, readable=True)) -> None:
    settings = get_settings()
    configure_logging(settings.log_level)

    payload = VerificationInputPayload.model_validate(_load_payload(input))
    extractor = ClaimExtractor()
    claims = extractor.extract_claims(payload)

    typer.echo(
        json.dumps(
            {
                "claim_count": len(claims),
                "claims": [claim.model_dump(mode="json") for claim in claims],
            },
            indent=2,
        )
    )


@inspect_app.command("verdict")
def inspect_verdict(
    input: Path = typer.Option(..., "--input", exists=False, readable=True),
) -> None:
    settings = get_settings()
    configure_logging(settings.log_level)

    payload_data = _load_payload(input)
    final_payload = _run_verification_pipeline(payload_data, settings=settings)

    claim_status = {
        verdict.claim.claim_id: verdict.final_status.value
        for verdict in final_payload.claim_verdicts
    }
    summary = {
        "overall_verdict": final_payload.overall_verdict.value,
        "overall_confidence": final_payload.overall_confidence,
        "unsupported_claims": final_payload.unsupported_claims,
        "missing_citations": final_payload.missing_citations,
        "claim_status": claim_status,
        "review_status": final_payload.review_status.model_dump(mode="json"),
    }

    typer.echo(json.dumps(summary, indent=2))


@run_app.command("all")
def run_all(
    review_action: str | None = typer.Option(None, "--review-action"),
    review_edits: str | None = typer.Option(None, "--review-edits"),
) -> None:
    settings = get_settings()
    configure_logging(settings.log_level)

    payload_data = _load_sample_payload(settings)
    final_payload = _run_verification_pipeline(
        payload_data,
        settings=settings,
        review_action=review_action,
        review_edits=_parse_review_edits(review_edits),
        emit_steps=True,
    )

    if final_payload.review_status.status == "pending":
        typer.echo(
            "Review pending. Re-run with --review-action approve|reject|edit|continue_with_caveats and optional --review-edits JSON."
        )

    typer.echo(json.dumps(final_payload.model_dump(mode="json"), indent=2))


if __name__ == "__main__":
    app()
