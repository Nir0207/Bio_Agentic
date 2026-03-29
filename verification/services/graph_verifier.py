from __future__ import annotations

from verification.schemas.claim_models import ClaimType, DirectnessLevel, ExtractedClaim
from verification.schemas.evidence_models import GraphPath, VerificationInputPayload
from verification.schemas.verification_models import GraphVerificationResult

_DIRECT_RELATION_HINTS = {
    ClaimType.ENTITY_ASSOCIATION: {"INTERACTS_WITH", "ASSOCIATED_WITH", "BINDS", "REGULATES", "ACTIVATES", "INHIBITS"},
    ClaimType.PATHWAY_PARTICIPATION: {"PARTICIPATES_IN", "IN_PATHWAY", "MEMBER_OF_PATHWAY"},
    ClaimType.SIMILARITY_CLAIM: {"SIMILAR_TO", "KNN_SIMILAR", "NEAREST_NEIGHBOR"},
}

_INDIRECT_RELATION_HINTS = {"CONNECTED_TO", "NETWORK_LINK", "CO_OCCURS_WITH", "RELATED_TO", "PATHWAY_LINK"}


class GraphVerifier:
    """Structured graph-evidence checks per claim."""

    def verify_claims(self, claims: list[ExtractedClaim], payload: VerificationInputPayload) -> list[GraphVerificationResult]:
        results: list[GraphVerificationResult] = []
        indexed_paths = self._index_paths(payload.graph_evidence)

        for claim in claims:
            relevant = [item for item in indexed_paths if self._path_matches_claim(item[1], claim)]
            path_ids = [path_id for path_id, _ in relevant]
            path_count = len(path_ids)

            if not relevant:
                results.append(
                    GraphVerificationResult(
                        claim_id=claim.claim_id,
                        graph_supported="false",
                        supporting_graph_evidence_ids=[],
                        path_count=0,
                        support_notes=["No graph path aligned to claim targets."],
                        unsupported_reason="No matching graph evidence found for claim targets.",
                    )
                )
                continue

            has_direct = self._has_direct_support(claim, [path for _, path in relevant])
            has_indirect = self._has_indirect_support(claim, [path for _, path in relevant])

            support_notes = [
                "Graph paths are treated as network support and not automatic causal proof.",
            ]

            graph_supported = "false"
            unsupported_reason = None

            if has_direct:
                graph_supported = "true"
                support_notes.append("Observed at least one relation aligned with claim type.")
            elif has_indirect:
                graph_supported = "partial"
                support_notes.append("Only indirect/network support found.")
                unsupported_reason = "Only indirect graph support available."
            else:
                graph_supported = "partial"
                support_notes.append("Graph path exists but relation type does not directly support this claim.")
                unsupported_reason = "Graph relation metadata does not align with claim semantics."

            if claim.directness_level == DirectnessLevel.DIRECT and not has_direct:
                graph_supported = "partial"
                support_notes.append("Claim states direct support but evidence is indirect.")
                unsupported_reason = "Direct relation was not observed in graph metadata."

            if claim.claim_type in {ClaimType.RANKING_CLAIM, ClaimType.EVIDENCE_STRENGTH_CLAIM} and path_count > 0 and graph_supported == "true":
                graph_supported = "partial"
                support_notes.append("Graph evidence is contextual for ranking/strength claims.")

            results.append(
                GraphVerificationResult(
                    claim_id=claim.claim_id,
                    graph_supported=graph_supported,
                    supporting_graph_evidence_ids=path_ids,
                    path_count=path_count,
                    support_notes=support_notes,
                    unsupported_reason=unsupported_reason,
                    direct_support=has_direct,
                    indirect_support=has_indirect,
                )
            )

        return results

    def _index_paths(self, paths: list[GraphPath]) -> list[tuple[str, GraphPath]]:
        indexed = []
        for idx, path in enumerate(paths, start=1):
            path_id = path.path_id or path.source_metadata.get("path_id") or f"graph-path-{idx:03d}"
            indexed.append((str(path_id), path))
        return indexed

    def _path_matches_claim(self, path: GraphPath, claim: ExtractedClaim) -> bool:
        if not claim.target_entity_ids:
            return True

        node_ids = {node.node_id for node in path.nodes}
        if path.candidate_id:
            node_ids.add(path.candidate_id)

        return any(target in node_ids for target in claim.target_entity_ids)

    def _has_direct_support(self, claim: ExtractedClaim, paths: list[GraphPath]) -> bool:
        relation_hints = _DIRECT_RELATION_HINTS.get(claim.claim_type, _DIRECT_RELATION_HINTS[ClaimType.ENTITY_ASSOCIATION])
        for path in paths:
            rels = self._relation_set(path)
            if rels.intersection(relation_hints):
                return True
        return False

    def _has_indirect_support(self, claim: ExtractedClaim, paths: list[GraphPath]) -> bool:
        for path in paths:
            rels = self._relation_set(path)
            if rels.intersection(_INDIRECT_RELATION_HINTS):
                return True
            if len(path.nodes) > 2:
                return True
        return False

    def _relation_set(self, path: GraphPath) -> set[str]:
        rels = {relation.upper() for relation in path.relation_types}
        for edge in path.edges:
            rels.add(edge.relation_type.upper())
        return rels
