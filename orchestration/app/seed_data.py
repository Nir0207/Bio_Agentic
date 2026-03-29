from __future__ import annotations

import time
from dataclasses import dataclass

from orchestration.services.neo4j_service import Neo4jService


@dataclass(frozen=True)
class SeedResult:
    attempts: int
    created_entities: dict[str, int]


def wait_for_neo4j(service: Neo4jService, *, retries: int = 30, sleep_seconds: float = 2.0) -> int:
    for attempt in range(1, retries + 1):
        status = service.verify_connectivity()
        if bool(status.get("ok")):
            return attempt
        time.sleep(sleep_seconds)
    raise RuntimeError(f"Neo4j did not become reachable after {retries} attempts.")


def seed_sample_graph(service: Neo4jService, *, sample_query: str) -> SeedResult:
    attempts = wait_for_neo4j(service)

    params = {"sample_query": sample_query}
    create_query = """
    MERGE (egfr:Protein {id: "EGFR"})
      SET egfr.name = "EGFR",
          egfr.symbol = "EGFR",
          egfr.target_score = 0.92,
          egfr.target_score_model_name = "seed_model",
          egfr.target_score_model_version = "1",
          egfr.target_score_run_id = "seed-run",
          egfr.target_score_created_at = datetime().epochMillis

    MERGE (mapk:Protein {id: "MAPK"})
      SET mapk.name = "MAPK",
          mapk.symbol = "MAPK",
          mapk.target_score = 0.86,
          mapk.target_score_model_name = "seed_model",
          mapk.target_score_model_version = "1",
          mapk.target_score_run_id = "seed-run",
          mapk.target_score_created_at = datetime().epochMillis

    MERGE (pw:Pathway {id: "PATHWAY_LUNG_EGFR_MAPK"})
      SET pw.name = "Lung cancer EGFR-MAPK pathway"

    MERGE (pub:Publication {id: "PUB_EGFR_MAPK_LUNG"})
      SET pub.title = "EGFR and MAPK pathway evidence in lung cancer",
          pub.abstract = $sample_query,
          pub.source = "seed_pubmed"

    MERGE (e1:Evidence {id: "EVI_EGFR_1"})
      SET e1.text = $sample_query + " with direct EGFR support",
          e1.evidence_type = "literature",
          e1.source = "seed",
          e1.confidence = 0.94,
          e1.publication_id = "PUB_EGFR_MAPK_LUNG",
          e1.protein_id = "EGFR"

    MERGE (e2:Evidence {id: "EVI_MAPK_1"})
      SET e2.text = $sample_query + " with direct MAPK support",
          e2.evidence_type = "literature",
          e2.source = "seed",
          e2.confidence = 0.91,
          e2.publication_id = "PUB_EGFR_MAPK_LUNG",
          e2.protein_id = "MAPK"

    MERGE (egfr)-[pi1:PARTICIPATES_IN]->(pw)
      SET pi1.confidence = 0.95, pi1.source = "seed"

    MERGE (mapk)-[pi2:PARTICIPATES_IN]->(pw)
      SET pi2.confidence = 0.93, pi2.source = "seed"

    MERGE (egfr)-[iw:INTERACTS_WITH]->(mapk)
      SET iw.confidence = 0.9, iw.source = "seed", iw.similarity = 0.88, iw.score = 0.88

    MERGE (pub)-[:HAS_EVIDENCE]->(e1)
    MERGE (pub)-[:HAS_EVIDENCE]->(e2)
    MERGE (e1)-[:SUPPORTS]->(egfr)
    MERGE (e2)-[:SUPPORTS]->(mapk)
    RETURN 1 AS ok
    """.strip()
    service.run(create_query, params)

    count_query = """
    MATCH (p:Protein)
    WITH count(p) AS protein_count
    MATCH (pw:Pathway)
    WITH protein_count, count(pw) AS pathway_count
    MATCH (pub:Publication)
    WITH protein_count, pathway_count, count(pub) AS publication_count
    MATCH (e:Evidence)
    RETURN
      protein_count,
      pathway_count,
      publication_count,
      count(e) AS evidence_count
    """.strip()
    rows = service.run(count_query)
    counts = rows[0] if rows else {}

    return SeedResult(
        attempts=attempts,
        created_entities={
            "Protein": int(counts.get("protein_count", 0)),
            "Pathway": int(counts.get("pathway_count", 0)),
            "Publication": int(counts.get("publication_count", 0)),
            "Evidence": int(counts.get("evidence_count", 0)),
        },
    )
