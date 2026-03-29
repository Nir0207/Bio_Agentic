from __future__ import annotations

from answering.schemas.answer_models import AnswerStyle


_STYLE_PROMPTS = {
    AnswerStyle.CONCISE: (
        "Style=concise. Keep answer short, prioritize direct findings, "
        "show caveats briefly, and keep inline evidence density moderate."
    ),
    AnswerStyle.DETAILED: (
        "Style=detailed. Use clear structure, include more claim context, "
        "and include caveats explicitly in a dedicated section."
    ),
    AnswerStyle.TECHNICAL: (
        "Style=technical. Use precise wording, include support directness when known, "
        "surface caveats prominently, and preserve exact claim boundaries."
    ),
}


def style_prompt_for(style: AnswerStyle) -> str:
    return _STYLE_PROMPTS[style]
