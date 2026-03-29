from __future__ import annotations

import re
from dataclasses import dataclass

from verification.schemas.claim_models import ClaimType, DirectnessLevel, ExtractedClaim, SourceSpan
from verification.schemas.evidence_models import VerificationInputPayload

_SENTENCE_SPLIT_PATTERN = re.compile(r"(?<=[.!?])\s+")
_CITATION_PATTERN = re.compile(r"\b(?:PMID:\d+|DOI:[^\s,;]+|EVI-[A-Za-z0-9_-]+|CIT-[A-Za-z0-9_-]+|PUB:[A-Za-z0-9_-]+)\b")

_DIRECT_TERMS = {"directly", "causes", "inhibits", "activates", "binds", "drives"}
_INDIRECT_TERMS = {"associated", "linked", "network", "correlated", "suggests", "indirect", "participates"}
_CRITICAL_TERMS = {"dose", "toxic", "toxicity", "contraindication", "life-threatening", "critical", "safety"}


@dataclass(frozen=True)
class _EntityAlias:
    alias: str
    entity_id: str


class ClaimExtractor:
    """Deterministic claim extraction from draft answers or evidence summaries."""

    def extract_claims(self, payload: VerificationInputPayload) -> list[ExtractedClaim]:
        source_text, spans_enabled = self._build_source_text(payload)
        sentences = [s.strip() for s in _SENTENCE_SPLIT_PATTERN.split(source_text) if s and s.strip()]

        if not sentences:
            fallback = payload.normalized_query or payload.original_query
            sentences = [fallback] if fallback else []

        aliases = self._build_aliases(payload)
        claims: list[ExtractedClaim] = []
        cursor = 0

        for idx, sentence in enumerate(sentences, start=1):
            claim_type = self._infer_claim_type(sentence)
            target_entity_ids = self._extract_target_entity_ids(sentence, aliases, payload)
            directness = self._infer_directness(sentence)
            citation_ids = sorted(set(_CITATION_PATTERN.findall(sentence)))
            score_ids = self._extract_score_refs(sentence, payload)
            source_span = None

            if spans_enabled:
                start = source_text.find(sentence, cursor)
                if start >= 0:
                    end = start + len(sentence)
                    source_span = SourceSpan(start_char=start, end_char=end, text=sentence)
                    cursor = end

            claims.append(
                ExtractedClaim(
                    claim_id=f"claim-{idx:03d}",
                    claim_text=sentence,
                    claim_type=claim_type,
                    target_entity_ids=target_entity_ids,
                    directness_level=directness,
                    source_span=source_span,
                    referenced_citation_ids=citation_ids,
                    referenced_score_ids=score_ids,
                    critical=self._is_critical(sentence, payload),
                )
            )

        return claims

    def _build_source_text(self, payload: VerificationInputPayload) -> tuple[str, bool]:
        draft = (payload.draft_answer_text or "").strip()
        if draft:
            return draft, True

        parts: list[str] = []

        for bundle in payload.evidence_bundle:
            if bundle.summary:
                parts.append(bundle.summary.strip())

        for path in payload.graph_evidence[:5]:
            if path.path_summary:
                parts.append(path.path_summary.strip())

        for hit in payload.semantic_evidence[:5]:
            if hit.snippet:
                parts.append(hit.snippet.strip())

        if not parts:
            parts.append(payload.normalized_query or payload.original_query)

        return ". ".join(part for part in parts if part).strip(), False

    def _build_aliases(self, payload: VerificationInputPayload) -> list[_EntityAlias]:
        aliases: list[_EntityAlias] = []

        for candidate in payload.candidate_entities:
            aliases.append(_EntityAlias(alias=candidate.candidate_id.lower(), entity_id=candidate.candidate_id))
            if candidate.display_name:
                aliases.append(_EntityAlias(alias=candidate.display_name.lower(), entity_id=candidate.candidate_id))
            for alias in candidate.aliases:
                aliases.append(_EntityAlias(alias=alias.lower(), entity_id=candidate.candidate_id))

        unique = {}
        for item in aliases:
            unique[(item.alias, item.entity_id)] = item
        return list(unique.values())

    def _extract_target_entity_ids(
        self,
        sentence: str,
        aliases: list[_EntityAlias],
        payload: VerificationInputPayload,
    ) -> list[str]:
        lower_sentence = sentence.lower()
        matches: list[tuple[int, str]] = []

        for alias in aliases:
            idx = lower_sentence.find(alias.alias)
            if idx >= 0:
                matches.append((idx, alias.entity_id))

        ordered = []
        for _, entity_id in sorted(matches, key=lambda item: item[0]):
            if entity_id not in ordered:
                ordered.append(entity_id)

        if ordered:
            return ordered

        if payload.candidate_entities:
            return [payload.candidate_entities[0].candidate_id]
        return []

    def _infer_claim_type(self, sentence: str) -> ClaimType:
        lower = sentence.lower()

        if any(token in lower for token in {"rank", "higher", "lower", "top", "best", "priority"}):
            return ClaimType.RANKING_CLAIM
        if any(token in lower for token in {"pathway", "participates", "participation", "signaling"}):
            return ClaimType.PATHWAY_PARTICIPATION
        if any(token in lower for token in {"similar", "similarity", "resembles", "nearest", "knn"}):
            return ClaimType.SIMILARITY_CLAIM
        if any(token in lower for token in {"score", "confidence", "strong evidence", "weak evidence", "evidence strength"}):
            return ClaimType.EVIDENCE_STRENGTH_CLAIM
        return ClaimType.ENTITY_ASSOCIATION

    def _infer_directness(self, sentence: str) -> DirectnessLevel:
        lower = sentence.lower()
        if any(term in lower for term in _DIRECT_TERMS):
            return DirectnessLevel.DIRECT
        if any(term in lower for term in _INDIRECT_TERMS):
            return DirectnessLevel.INDIRECT
        return DirectnessLevel.UNSPECIFIED

    def _extract_score_refs(self, sentence: str, payload: VerificationInputPayload) -> list[str]:
        lower = sentence.lower()
        refs: list[str] = []
        for score in payload.model_scores:
            if score.score_name.lower() in lower:
                refs.append(f"{score.candidate_id}:{score.score_name}")
        return sorted(set(refs))

    def _is_critical(self, sentence: str, payload: VerificationInputPayload) -> bool:
        lower = sentence.lower()
        if any(term in lower for term in _CRITICAL_TERMS):
            return True
        if payload.high_stakes:
            return True
        query = (payload.normalized_query or payload.original_query).lower()
        return any(term in query for term in _CRITICAL_TERMS)
