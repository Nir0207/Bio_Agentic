from __future__ import annotations

from answering.schemas.answer_models import FinalAnswerPayload


class MarkdownRenderer:
    def render(self, payload: FinalAnswerPayload) -> str:
        lines: list[str] = []
        lines.append(f"# {payload.original_query}")
        lines.append("")
        lines.append(payload.answer_text)

        if payload.summary_points:
            lines.append("")
            lines.append("## Evidence-Backed Points")
            for point in payload.summary_points:
                lines.append(f"- {point}")

        lines.append("")
        lines.append("## Caveats")
        if payload.caveats:
            for item in payload.caveats:
                lines.append(f"- {item}")
        else:
            lines.append("- None")

        lines.append("")
        lines.append("## Citations")
        for citation in payload.citations:
            lines.append(f"- {citation.citation_tag} {citation.source_label}")

        return "\n".join(lines)
