from __future__ import annotations

from orchestration.app.config import Settings
from orchestration.app.state import OrchestrationState, add_stage_metadata
from orchestration.schemas.candidate_models import CandidateEntity
from orchestration.schemas.evidence_models import EvidenceBundle, GraphPath, ModelScore, ProvenanceRecord, SemanticHit
from orchestration.services.evidence_service import EvidenceService
from orchestration.tools.evidence_tools import EvidenceTools, ProvenanceRequest


def build_evidence_bundle_node(
    state: OrchestrationState,
    *,
    settings: Settings,
    evidence_service: EvidenceService,
    evidence_tools: EvidenceTools,
) -> dict:
    candidates = _coerce_candidates(state.get("candidate_entities") or [])
    graph_paths = [path if isinstance(path, GraphPath) else GraphPath(**path) for path in (state.get("graph_evidence") or [])]
    semantic_hits = [hit if isinstance(hit, SemanticHit) else SemanticHit(**hit) for hit in (state.get("semantic_evidence") or [])]
    model_scores = [score if isinstance(score, ModelScore) else ModelScore(**score) for score in (state.get("model_scores") or [])]

    bundles: list[EvidenceBundle] = []
    all_provenance: list[ProvenanceRecord] = []

    metadata = dict(state.get("execution_metadata", {}))
    tool_runs = list(metadata.get("tool_runs", []))

    for candidate in candidates[: max(settings.graph_top_k, 5)]:
        linked_hits = [hit for hit in semantic_hits if candidate.candidate_id in hit.linked_candidate_ids]
        citation_ids = sorted(
            {
                str(hit.citation_handle)
                for hit in linked_hits
                if hit.citation_handle and str(hit.citation_handle).strip()
            }
        )
        provenance_result = evidence_tools.get_provenance_for_claim(
            ProvenanceRequest(claim_id=candidate.candidate_id, citation_ids=citation_ids)
        )
        tool_runs.append(provenance_result.execution_metadata.model_dump())

        bundle = evidence_service.build_evidence_bundle(
            candidate=candidate,
            graph_paths=graph_paths,
            semantic_hits=semantic_hits,
            model_scores=model_scores,
            neo4j_service=evidence_tools.neo4j_service,
            provenance_records=provenance_result.provenance,
        )
        bundles.append(bundle)
        all_provenance.extend(provenance_result.provenance)

    metadata["tool_runs"] = tool_runs
    metadata = add_stage_metadata(
        {**state, "execution_metadata": metadata},
        "build_evidence_bundle",
        {
            "bundle_count": len(bundles),
            "provenance_count": len(all_provenance),
        },
    )

    return {
        "evidence_bundle": bundles,
        "provenance": all_provenance,
        "execution_metadata": metadata,
    }


def _coerce_candidates(candidates: list[CandidateEntity | dict]) -> list[CandidateEntity]:
    return [candidate if isinstance(candidate, CandidateEntity) else CandidateEntity(**candidate) for candidate in candidates]
