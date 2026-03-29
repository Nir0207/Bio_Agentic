from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

from orchestration.app.constants import (
    CANDIDATE_WEIGHT_GRAPH,
    CANDIDATE_WEIGHT_MODEL,
    CANDIDATE_WEIGHT_SEMANTIC,
    HITL_REASON_CONTRADICTORY,
    HITL_REASON_HIGH_STAKES,
    HITL_REASON_LOW_CITATIONS,
    HITL_REASON_LOW_CONFIDENCE,
)
from orchestration.schemas.candidate_models import CandidateEntity
from orchestration.schemas.evidence_models import (
    ConfidenceSummary,
    EvidenceBundle,
    GraphPath,
    ModelScore,
    ProvenanceRecord,
    SemanticHit,
)
from orchestration.services.neo4j_service import Neo4jService


@dataclass
class ReviewPolicy:
    enabled: bool
    low_confidence_threshold: float
    min_citations: int
    review_on_contradiction: bool
    review_high_stakes: bool


class EvidenceService:
    def merge_candidates(
        self,
        graph_candidates: list[CandidateEntity],
        semantic_hits: list[SemanticHit],
        model_scores: list[ModelScore],
    ) -> list[CandidateEntity]:
        merged: dict[str, CandidateEntity] = {}

        for candidate in graph_candidates:
            merged[candidate.candidate_id] = candidate.model_copy(deep=True)

        for hit in semantic_hits:
            for candidate_id in hit.linked_candidate_ids:
                candidate = merged.get(candidate_id)
                if candidate is None:
                    candidate = CandidateEntity(candidate_id=candidate_id, candidate_type="Protein", sources=[])
                    merged[candidate_id] = candidate
                candidate.semantic_support = max(candidate.semantic_support, float(hit.retrieval_score))
                if "semantic" not in candidate.sources:
                    candidate.sources.append("semantic")

        for score in model_scores:
            candidate = merged.get(score.candidate_id)
            if candidate is None:
                candidate = CandidateEntity(candidate_id=score.candidate_id, candidate_type="Protein", sources=[])
                merged[score.candidate_id] = candidate
            candidate.model_support = max(candidate.model_support, float(score.score_value))
            if "model" not in candidate.sources:
                candidate.sources.append("model")

        if not merged and semantic_hits:
            for hit in semantic_hits[:3]:
                fallback_id = hit.linked_candidate_ids[0] if hit.linked_candidate_ids else hit.node_id
                merged[fallback_id] = CandidateEntity(
                    candidate_id=fallback_id,
                    candidate_type="Protein" if hit.linked_candidate_ids else hit.node_type,
                    sources=["semantic"],
                    semantic_support=float(hit.retrieval_score),
                )

        for candidate in merged.values():
            candidate.rank_score = self._rank_score(candidate)

        return sorted(merged.values(), key=lambda c: (-c.rank_score, c.candidate_id))

    def build_evidence_bundle(
        self,
        *,
        candidate: CandidateEntity,
        graph_paths: list[GraphPath],
        semantic_hits: list[SemanticHit],
        model_scores: list[ModelScore],
        neo4j_service: Neo4jService,
        provenance_records: list[ProvenanceRecord] | None = None,
    ) -> EvidenceBundle:
        linked_semantic_hits = [
            hit for hit in semantic_hits if candidate.candidate_id in hit.linked_candidate_ids
        ]
        if not linked_semantic_hits:
            linked_semantic_hits = semantic_hits[:2]

        linked_graph_paths = [path for path in graph_paths if path.candidate_id == candidate.candidate_id]
        linked_model_scores = [score for score in model_scores if score.candidate_id == candidate.candidate_id]

        citation_ids = sorted(
            {
                str(hit.citation_handle)
                for hit in linked_semantic_hits
                if hit.citation_handle and str(hit.citation_handle).strip()
            }
        )

        provenance_rows = provenance_records or neo4j_service.get_provenance_for_claim(candidate.candidate_id, citation_ids)
        confidence = self.compute_confidence(
            graph_paths=linked_graph_paths,
            semantic_hits=linked_semantic_hits,
            model_scores=linked_model_scores,
        )

        warnings: list[str] = []
        unresolved_gaps: list[str] = []
        if not linked_graph_paths:
            warnings.append("No graph paths found for candidate")
            unresolved_gaps.append("graph_context_missing")
        if not linked_semantic_hits:
            warnings.append("No semantic evidence found for candidate")
            unresolved_gaps.append("semantic_context_missing")
        if not linked_model_scores:
            warnings.append("No model score found for candidate")
            unresolved_gaps.append("model_score_missing")

        return EvidenceBundle(
            candidate_id=candidate.candidate_id,
            candidate_type=candidate.candidate_type,
            graph_paths=linked_graph_paths,
            semantic_hits=linked_semantic_hits,
            model_scores=linked_model_scores,
            provenance=provenance_rows,
            confidence_summary=confidence,
            citation_ids=citation_ids,
            warnings=warnings,
            unresolved_gaps=unresolved_gaps,
        )

    def compute_confidence(
        self,
        *,
        graph_paths: Iterable[GraphPath],
        semantic_hits: Iterable[SemanticHit],
        model_scores: Iterable[ModelScore],
    ) -> ConfidenceSummary:
        graph_values = [float(path.confidence or 0.0) for path in graph_paths]
        semantic_values = [float(hit.retrieval_score or 0.0) for hit in semantic_hits]
        model_values = [float(score.score_value or 0.0) for score in model_scores]

        graph_conf = sum(graph_values) / len(graph_values) if graph_values else 0.0
        semantic_conf = sum(semantic_values) / len(semantic_values) if semantic_values else 0.0
        score_conf = sum(model_values) / len(model_values) if model_values else 0.0

        overall = (
            CANDIDATE_WEIGHT_GRAPH * self._clamp(graph_conf)
            + CANDIDATE_WEIGHT_SEMANTIC * self._clamp(semantic_conf)
            + CANDIDATE_WEIGHT_MODEL * self._clamp(score_conf)
        )

        reasons: list[str] = []
        if graph_conf > 0.6:
            reasons.append("strong_graph_support")
        if semantic_conf > 0.6:
            reasons.append("strong_semantic_support")
        if score_conf > 0.6:
            reasons.append("strong_model_support")
        if overall < 0.4:
            reasons.append("overall_low_confidence")

        return ConfidenceSummary(
            overall_confidence=round(self._clamp(overall), 4),
            graph_confidence=round(self._clamp(graph_conf), 4),
            semantic_confidence=round(self._clamp(semantic_conf), 4),
            score_confidence=round(self._clamp(score_conf), 4),
            reasons=reasons,
        )

    def review_decision(
        self,
        *,
        evidence_bundles: list[EvidenceBundle],
        policy: ReviewPolicy,
        high_stakes: bool,
    ) -> tuple[bool, str | None]:
        if not policy.enabled:
            return False, None

        if high_stakes and policy.review_high_stakes:
            return True, HITL_REASON_HIGH_STAKES

        for bundle in evidence_bundles:
            if bundle.confidence_summary.overall_confidence < policy.low_confidence_threshold:
                return True, HITL_REASON_LOW_CONFIDENCE
            if len(bundle.citation_ids) < policy.min_citations:
                return True, HITL_REASON_LOW_CITATIONS

            if policy.review_on_contradiction and self._has_contradiction(bundle):
                return True, HITL_REASON_CONTRADICTORY

        return False, None

    def _has_contradiction(self, bundle: EvidenceBundle) -> bool:
        score_conf = bundle.confidence_summary.score_confidence
        semantic_conf = bundle.confidence_summary.semantic_confidence
        graph_conf = bundle.confidence_summary.graph_confidence
        strong_model_weak_evidence = score_conf >= 0.7 and (semantic_conf <= 0.3 and graph_conf <= 0.3)
        weak_model_strong_evidence = score_conf <= 0.3 and (semantic_conf >= 0.7 or graph_conf >= 0.7)
        return strong_model_weak_evidence or weak_model_strong_evidence

    def _rank_score(self, candidate: CandidateEntity) -> float:
        rank = (
            CANDIDATE_WEIGHT_GRAPH * self._clamp(candidate.graph_support)
            + CANDIDATE_WEIGHT_SEMANTIC * self._clamp(candidate.semantic_support)
            + CANDIDATE_WEIGHT_MODEL * self._clamp(candidate.model_support)
        )
        return round(rank, 4)

    def _clamp(self, value: float) -> float:
        return max(0.0, min(1.0, float(value)))
