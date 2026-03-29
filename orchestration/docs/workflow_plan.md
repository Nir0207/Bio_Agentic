# Workflow Plan

## Node-by-node flow

1. `route_query`
- normalize text
- classify intent (`target_prioritization`, `pathway_exploration`, `evidence_lookup`, `similarity_lookup`)
- extract obvious entity mentions

2. `retrieve_graph`
- call graph tools (`get_subgraph_for_entity`, optional `get_similar_entities`, optional `get_pathway_context`)
- assemble graph candidates and structured path evidence

3. `retrieve_semantic`
- call semantic tools (`search_publications`, `search_evidence`)
- attach retrieval score/snippet/source/citation

4. `fetch_scores`
- call `get_model_score` for candidate entities
- include model name/version/run metadata

5. `assemble_candidates`
- deterministic merge and dedupe across graph/semantic/model signals
- deterministic ranking weights

6. `build_evidence_bundle`
- per-candidate evidence package with graph paths, semantic hits, model scores, provenance, confidence

7. `request_human_review`
- evaluate policy
- interrupt if needed
- support resume with continue/reject/edit actions

8. `finalize_payload`
- output final structured payload only

## Routing strategy

Routing is deterministic keyword-based matching with fallback to `evidence_lookup`.

## Merge strategy

Candidate rank combines clamped signals with fixed weights:
- graph: 0.40
- semantic: 0.25
- model: 0.35

## Interruption points

One explicit interruption node (`request_human_review`) after evidence-bundle construction and before final payload output.
