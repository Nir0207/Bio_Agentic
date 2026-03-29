from __future__ import annotations

import re

from verification.schemas.claim_models import ExtractedClaim
from verification.schemas.evidence_models import CandidateEntity, SemanticEvidence, VerificationInputPayload
from verification.schemas.verification_models import CitationVerificationResult

_TOKEN_PATTERN = re.compile(r"\b[a-zA-Z0-9_-]{4,}\b")


class CitationVerifier:
    """Citation completeness + provenance coverage checks."""

    def verify_claims(self, claims: list[ExtractedClaim], payload: VerificationInputPayload) -> list[CitationVerificationResult]:
        resolvable_ids = self._collect_resolvable_ids(payload)
        entity_lookup = self._entity_lookup(payload.candidate_entities)
        results: list[CitationVerificationResult] = []

        for claim in claims:
            relevant_hits = [
                hit for hit in payload.semantic_evidence if self._is_semantic_hit_relevant(hit, claim, entity_lookup)
            ]

            supporting_citations = []
            for hit in relevant_hits:
                supporting_citations.append(hit.citation_id or hit.evidence_id)
            supporting_citations.extend(claim.referenced_citation_ids)
            supporting_citations = sorted({cid for cid in supporting_citations if cid})

            if not supporting_citations:
                results.append(
                    CitationVerificationResult(
                        claim_id=claim.claim_id,
                        citation_supported="false",
                        supporting_citation_ids=[],
                        missing_citation_reason="No semantic evidence or citation id linked to claim.",
                    )
                )
                continue

            resolvable = [cid for cid in supporting_citations if cid in resolvable_ids]
            material_hits = [hit for hit in relevant_hits if self._materially_relates(hit, claim, entity_lookup)]

            if resolvable and material_hits:
                support = "true"
                reason = None
            elif resolvable or material_hits:
                support = "partial"
                reason = "Citation coverage is incomplete or weakly grounded to claim target."
            else:
                support = "false"
                reason = "Citation ids are not resolvable or snippets do not match claim target."

            results.append(
                CitationVerificationResult(
                    claim_id=claim.claim_id,
                    citation_supported=support,
                    supporting_citation_ids=supporting_citations,
                    missing_citation_reason=reason,
                )
            )

        return results

    def _collect_resolvable_ids(self, payload: VerificationInputPayload) -> set[str]:
        ids: set[str] = set()

        for record in payload.provenance:
            if record.source_ref:
                ids.add(record.source_ref)

        for hit in payload.semantic_evidence:
            if hit.citation_id:
                ids.add(hit.citation_id)
            if hit.node_type in {"Publication", "Evidence"}:
                ids.add(hit.evidence_id)

        for bundle in payload.evidence_bundle:
            ids.update(bundle.citation_ids)

        return ids

    def _entity_lookup(self, entities: list[CandidateEntity]) -> dict[str, set[str]]:
        lookup: dict[str, set[str]] = {}
        for entity in entities:
            names = {entity.candidate_id.lower()}
            if entity.display_name:
                names.add(entity.display_name.lower())
            names.update(alias.lower() for alias in entity.aliases)
            lookup[entity.candidate_id] = names
        return lookup

    def _is_semantic_hit_relevant(
        self,
        hit: SemanticEvidence,
        claim: ExtractedClaim,
        entity_lookup: dict[str, set[str]],
    ) -> bool:
        if not claim.target_entity_ids:
            return True

        linked = set(hit.linked_candidate_ids)
        if linked.intersection(claim.target_entity_ids):
            return True

        snippet_lower = hit.snippet.lower()
        for entity_id in claim.target_entity_ids:
            if any(name in snippet_lower for name in entity_lookup.get(entity_id, {entity_id.lower()})):
                return True
        return False

    def _materially_relates(
        self,
        hit: SemanticEvidence,
        claim: ExtractedClaim,
        entity_lookup: dict[str, set[str]],
    ) -> bool:
        snippet_tokens = set(_TOKEN_PATTERN.findall(hit.snippet.lower()))
        claim_tokens = set(_TOKEN_PATTERN.findall(claim.claim_text.lower()))
        overlap = snippet_tokens.intersection(claim_tokens)

        target_present = False
        if not claim.target_entity_ids:
            target_present = True
        else:
            snippet_lower = hit.snippet.lower()
            for entity_id in claim.target_entity_ids:
                if any(name in snippet_lower for name in entity_lookup.get(entity_id, {entity_id.lower()})):
                    target_present = True
                    break

        return target_present and bool(overlap)
