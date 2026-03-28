from __future__ import annotations

from orchestration.tools.evidence_tools import ProvenanceRequest
from orchestration.tools.neo4j_tools import PathwayContextRequest, SimilarEntitiesRequest, SubgraphRequest
from orchestration.tools.scoring_tools import ModelScoreRequest
from orchestration.tools.semantic_search_tools import EvidenceSearchRequest, PublicationSearchRequest


def test_tool_wrappers_return_typed_contracts(runtime) -> None:
    subgraph = runtime.neo4j_tools.get_subgraph_for_entity(SubgraphRequest(entity_id="EGFR"))
    similar = runtime.neo4j_tools.get_similar_entities(SimilarEntitiesRequest(entity_id="EGFR"))
    pathway = runtime.neo4j_tools.get_pathway_context(PathwayContextRequest(entity_id="EGFR"))
    publications = runtime.semantic_tools.search_publications(PublicationSearchRequest(query_text="EGFR evidence", top_k=3))
    evidence = runtime.semantic_tools.search_evidence(EvidenceSearchRequest(query_text="EGFR evidence", top_k=3))
    score = runtime.scoring_tools.get_model_score(ModelScoreRequest(candidate_id="EGFR"))
    provenance = runtime.evidence_tools.get_provenance_for_claim(
        ProvenanceRequest(claim_id="EGFR", citation_ids=["PMID:1"])
    )

    assert subgraph.execution_metadata.tool_name == "get_subgraph_for_entity"
    assert similar.execution_metadata.tool_name == "get_similar_entities"
    assert pathway.execution_metadata.tool_name == "get_pathway_context"
    assert publications.execution_metadata.tool_name == "search_publications"
    assert evidence.execution_metadata.tool_name == "search_evidence"
    assert score.execution_metadata.tool_name == "get_model_score"
    assert provenance.execution_metadata.tool_name == "get_provenance_for_claim"

    assert len(subgraph.graph_paths) >= 1
    assert len(similar.candidates) >= 1
    assert score.model_score is not None
    assert len(provenance.provenance) == 1
