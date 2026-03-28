from __future__ import annotations

import hashlib
import logging
import re
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any

from neo4j import GraphDatabase

logger = logging.getLogger(__name__)

_IDENTIFIER_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")


@dataclass
class Neo4jService:
    uri: str
    username: str
    password: str
    database: str
    allow_mock_fallback_data: bool = True
    _driver: Any | None = field(default=None, init=False, repr=False)

    def _ensure_driver(self) -> Any:
        if self._driver is None:
            self._driver = GraphDatabase.driver(self.uri, auth=(self.username, self.password))
        return self._driver

    def close(self) -> None:
        if self._driver is not None:
            self._driver.close()
            self._driver = None

    def __enter__(self) -> "Neo4jService":
        self._ensure_driver()
        return self

    def __exit__(self, *_args: object) -> None:
        self.close()

    def verify_connectivity(self) -> dict[str, Any]:
        try:
            self._ensure_driver().verify_connectivity()
            return {"ok": True, "uri": self.uri}
        except Exception as exc:
            logger.warning("Neo4j connectivity check failed: %s", exc)
            return {"ok": False, "uri": self.uri, "error": str(exc)}

    def run(self, query: str, parameters: dict[str, Any] | None = None) -> list[dict[str, Any]]:
        params = parameters or {}
        with self._ensure_driver().session(database=self.database) as session:
            result = session.run(query, params)
            return [record.data() for record in result]

    def resolve_entities_by_text(self, text: str, top_k: int = 5) -> list[dict[str, Any]]:
        query = """
        MATCH (n)
        WHERE (n:Protein OR n:Pathway)
          AND (
            toLower(coalesce(n.id, "")) CONTAINS $text
            OR toLower(coalesce(n.name, "")) CONTAINS $text
            OR toLower(coalesce(n.symbol, "")) CONTAINS $text
          )
        RETURN
          coalesce(n.id, toString(id(n))) AS candidate_id,
          head(labels(n)) AS candidate_type,
          coalesce(n.name, n.symbol, n.title, n.id) AS display_name
        ORDER BY candidate_id
        LIMIT $top_k
        """.strip()
        try:
            rows = self.run(query, {"text": text.lower(), "top_k": int(top_k)})
            if rows:
                return rows
        except Exception as exc:
            logger.warning("Entity resolution failed, using fallback candidates: %s", exc)

        if not self.allow_mock_fallback_data:
            return []

        token = text.strip().upper().replace(" ", "_")
        if not token:
            token = "UNKNOWN"
        return [
            {
                "candidate_id": token,
                "candidate_type": "Protein",
                "display_name": token,
            }
        ]

    def get_subgraph_for_entity(self, entity_id: str, max_hops: int = 2, max_paths: int = 4) -> list[dict[str, Any]]:
        hops = max(1, min(int(max_hops), 3))
        path_limit = max(1, int(max_paths))
        query = f"""
        MATCH (start)
        WHERE toLower(coalesce(start.id, "")) = toLower($entity_id)
           OR toLower(coalesce(start.name, "")) = toLower($entity_id)
           OR toLower(coalesce(start.symbol, "")) = toLower($entity_id)
        OPTIONAL MATCH p=(start)-[*1..{hops}]-(neighbor)
        WITH start, p
        LIMIT $max_paths
        RETURN
          coalesce(start.id, toString(id(start))) AS candidate_id,
          head(labels(start)) AS candidate_type,
          coalesce(start.name, start.symbol, start.title, start.id) AS candidate_name,
          CASE WHEN p IS NULL THEN [] ELSE
            [n IN nodes(p) | {{
              node_id: coalesce(n.id, toString(id(n))),
              node_labels: labels(n),
              display_name: coalesce(n.name, n.symbol, n.title, n.id)
            }}]
          END AS nodes,
          CASE WHEN p IS NULL THEN [] ELSE
            [r IN relationships(p) | {{
              edge_id: coalesce(r.id, toString(id(r))),
              relation_type: type(r),
              source_node_id: coalesce(startNode(r).id, toString(id(startNode(r)))),
              target_node_id: coalesce(endNode(r).id, toString(id(endNode(r)))),
              confidence: toFloat(coalesce(r.confidence, 0.5)),
              source_system: coalesce(r.source, "neo4j")
            }}]
          END AS edges
        """.strip()

        try:
            rows = self.run(query, {"entity_id": entity_id, "max_paths": path_limit})
            if rows:
                return [self._format_path_row(row) for row in rows]
        except Exception as exc:
            logger.warning("Subgraph retrieval failed for %s: %s", entity_id, exc)

        if not self.allow_mock_fallback_data:
            return []
        return self._mock_subgraph(entity_id)

    def get_similar_entities(self, entity_id: str, top_k: int = 5) -> list[dict[str, Any]]:
        query = """
        MATCH (p:Protein {id: $entity_id})-[r:SIMILAR_TO|INTERACTS_WITH]-(other:Protein)
        RETURN
          coalesce(other.id, toString(id(other))) AS candidate_id,
          "Protein" AS candidate_type,
          coalesce(other.name, other.symbol, other.id) AS display_name,
          toFloat(coalesce(r.score, r.similarity, 0.5)) AS similarity
        ORDER BY similarity DESC, candidate_id
        LIMIT $top_k
        """.strip()
        try:
            rows = self.run(query, {"entity_id": entity_id, "top_k": int(top_k)})
            if rows:
                return rows
        except Exception as exc:
            logger.warning("Similar entity lookup failed for %s: %s", entity_id, exc)

        if not self.allow_mock_fallback_data:
            return []
        return self._mock_similar_entities(entity_id, top_k)

    def get_pathway_context(self, entity_id: str, top_k: int = 5) -> list[dict[str, Any]]:
        query = """
        MATCH (p:Protein {id: $entity_id})-[rel:PARTICIPATES_IN]->(pw:Pathway)
        OPTIONAL MATCH chain=(pw)-[:PARENT_OF*0..2]->(child:Pathway)
        WITH p, pw, rel, chain
        LIMIT $top_k
        RETURN
          p.id AS candidate_id,
          "Protein" AS candidate_type,
          coalesce(p.name, p.symbol, p.id) AS candidate_name,
          CASE WHEN chain IS NULL THEN [
            {
              node_id: pw.id,
              node_labels: labels(pw),
              display_name: coalesce(pw.name, pw.id)
            }
          ] ELSE [n IN nodes(chain) | {
              node_id: coalesce(n.id, toString(id(n))),
              node_labels: labels(n),
              display_name: coalesce(n.name, n.id)
            }] END AS nodes,
          CASE WHEN chain IS NULL THEN [
            {
              edge_id: toString(id(rel)),
              relation_type: type(rel),
              source_node_id: p.id,
              target_node_id: pw.id,
              confidence: toFloat(coalesce(rel.confidence, 0.6)),
              source_system: coalesce(rel.source, "neo4j")
            }
          ] ELSE [r in relationships(chain) | {
              edge_id: toString(id(r)),
              relation_type: type(r),
              source_node_id: coalesce(startNode(r).id, toString(id(startNode(r)))),
              target_node_id: coalesce(endNode(r).id, toString(id(endNode(r)))),
              confidence: toFloat(coalesce(r.confidence, 0.6)),
              source_system: coalesce(r.source, "neo4j")
            }] END AS edges
        """.strip()
        try:
            rows = self.run(query, {"entity_id": entity_id, "top_k": int(top_k)})
            if rows:
                return [self._format_path_row(row) for row in rows]
        except Exception as exc:
            logger.warning("Pathway context lookup failed for %s: %s", entity_id, exc)

        if not self.allow_mock_fallback_data:
            return []
        return self._mock_pathway_context(entity_id)

    def search_publications_keyword(self, query_text: str, top_k: int = 5) -> list[dict[str, Any]]:
        query = """
        MATCH (p:Publication)
        WHERE toLower(coalesce(p.title, "")) CONTAINS $text
           OR toLower(coalesce(p.abstract, "")) CONTAINS $text
        RETURN
          coalesce(p.id, toString(id(p))) AS node_id,
          "Publication" AS node_type,
          coalesce(p.title, p.id) AS title,
          substring(coalesce(p.abstract, ""), 0, 300) AS snippet,
          CASE WHEN toLower(coalesce(p.title, "")) CONTAINS $text THEN 1.0 ELSE 0.6 END AS score,
          coalesce(p.source, "neo4j") AS source,
          coalesce(p.pmid, p.id) AS citation_handle
        ORDER BY score DESC, node_id
        LIMIT $top_k
        """.strip()

        try:
            rows = self.run(query, {"text": query_text.lower(), "top_k": int(top_k)})
            if rows:
                return rows
        except Exception as exc:
            logger.warning("Publication keyword search failed: %s", exc)

        if not self.allow_mock_fallback_data:
            return []
        return self._mock_publication_hits(query_text, top_k)

    def search_evidence_keyword(self, query_text: str, top_k: int = 5) -> list[dict[str, Any]]:
        query = """
        MATCH (e:Evidence)
        WHERE toLower(coalesce(e.text, "")) CONTAINS $text
           OR toLower(coalesce(e.evidence_type, "")) CONTAINS $text
        RETURN
          coalesce(e.id, toString(id(e))) AS node_id,
          "Evidence" AS node_type,
          NULL AS title,
          substring(coalesce(e.text, ""), 0, 300) AS snippet,
          CASE WHEN toLower(coalesce(e.text, "")) CONTAINS $text THEN 0.9 ELSE 0.55 END AS score,
          coalesce(e.source, "neo4j") AS source,
          coalesce(e.publication_id, e.id) AS citation_handle,
          coalesce(e.protein_id, "") AS linked_candidate_id
        ORDER BY score DESC, node_id
        LIMIT $top_k
        """.strip()

        try:
            rows = self.run(query, {"text": query_text.lower(), "top_k": int(top_k)})
            if rows:
                return rows
        except Exception as exc:
            logger.warning("Evidence keyword search failed: %s", exc)

        if not self.allow_mock_fallback_data:
            return []
        return self._mock_evidence_hits(query_text, top_k)

    def search_publications_vector(self, query_embedding: list[float], index_name: str, top_k: int = 5) -> list[dict[str, Any]]:
        query = """
        CALL db.index.vector.queryNodes($index_name, toInteger($top_k), $query_embedding)
        YIELD node, score
        RETURN
          coalesce(node.id, toString(id(node))) AS node_id,
          "Publication" AS node_type,
          coalesce(node.title, node.id) AS title,
          substring(coalesce(node.abstract, ""), 0, 300) AS snippet,
          toFloat(score) AS score,
          coalesce(node.source, "neo4j") AS source,
          coalesce(node.pmid, node.id) AS citation_handle
        ORDER BY score DESC
        """.strip()
        return self.run(
            query,
            {
                "index_name": index_name,
                "top_k": int(top_k),
                "query_embedding": query_embedding,
            },
        )

    def search_evidence_vector(self, query_embedding: list[float], index_name: str, top_k: int = 5) -> list[dict[str, Any]]:
        query = """
        CALL db.index.vector.queryNodes($index_name, toInteger($top_k), $query_embedding)
        YIELD node, score
        RETURN
          coalesce(node.id, toString(id(node))) AS node_id,
          "Evidence" AS node_type,
          NULL AS title,
          substring(coalesce(node.text, ""), 0, 300) AS snippet,
          toFloat(score) AS score,
          coalesce(node.source, "neo4j") AS source,
          coalesce(node.publication_id, node.id) AS citation_handle,
          coalesce(node.protein_id, "") AS linked_candidate_id
        ORDER BY score DESC
        """.strip()
        return self.run(
            query,
            {
                "index_name": index_name,
                "top_k": int(top_k),
                "query_embedding": query_embedding,
            },
        )

    def get_model_score_from_neo4j(self, entity_id: str, score_props: dict[str, str]) -> dict[str, Any] | None:
        score_prop = self._safe_property(score_props.get("score", "target_score"))
        model_name_prop = self._safe_property(score_props.get("model_name", "target_score_model_name"))
        model_version_prop = self._safe_property(score_props.get("model_version", "target_score_model_version"))
        run_id_prop = self._safe_property(score_props.get("run_id", "target_score_run_id"))
        timestamp_prop = self._safe_property(score_props.get("timestamp", "target_score_created_at"))

        query = f"""
        MATCH (p:Protein)
        WHERE toLower(coalesce(p.id, "")) = toLower($entity_id)
        RETURN
          p.id AS candidate_id,
          p.{score_prop} AS score_value,
          p.{model_name_prop} AS model_name,
          p.{model_version_prop} AS model_version,
          p.{run_id_prop} AS run_id,
          p.{timestamp_prop} AS timestamp
        LIMIT 1
        """.strip()
        try:
            rows = self.run(query, {"entity_id": entity_id})
            if rows and rows[0].get("score_value") is not None:
                return rows[0]
        except Exception as exc:
            logger.warning("Model score lookup failed for %s: %s", entity_id, exc)

        if not self.allow_mock_fallback_data:
            return None
        return self._mock_model_score(entity_id)

    def get_provenance_for_claim(self, candidate_id: str, citation_ids: list[str]) -> list[dict[str, Any]]:
        now = datetime.now(timezone.utc).isoformat()
        if citation_ids:
            query = """
            MATCH (n)
            WHERE (n:Publication OR n:Evidence)
              AND coalesce(n.id, "") IN $citation_ids
            RETURN
              coalesce(n.id, toString(id(n))) AS source_ref,
              CASE WHEN n:Publication THEN "publication" ELSE "evidence" END AS source_system,
              coalesce(n.source, "neo4j") AS source_name
            LIMIT 50
            """.strip()
            try:
                rows = self.run(query, {"citation_ids": citation_ids})
                if rows:
                    return [
                        {
                            "claim_id": candidate_id,
                            "source_system": str(row.get("source_system") or "neo4j"),
                            "source_ref": str(row.get("source_ref") or "unknown"),
                            "retrieved_at": now,
                            "metadata": {"source_name": row.get("source_name")},
                        }
                        for row in rows
                    ]
            except Exception as exc:
                logger.warning("Citation provenance lookup failed: %s", exc)

        query_fallback = """
        MATCH (p:Protein {id: $candidate_id})<-[:SUPPORTS]-(e:Evidence)
        OPTIONAL MATCH (pub:Publication)-[:HAS_EVIDENCE]->(e)
        RETURN
          coalesce(pub.id, e.id, toString(id(e))) AS source_ref,
          CASE WHEN pub IS NULL THEN "evidence" ELSE "publication" END AS source_system,
          coalesce(pub.source, e.source, "neo4j") AS source_name
        LIMIT 10
        """.strip()
        try:
            rows = self.run(query_fallback, {"candidate_id": candidate_id})
            if rows:
                return [
                    {
                        "claim_id": candidate_id,
                        "source_system": str(row.get("source_system") or "neo4j"),
                        "source_ref": str(row.get("source_ref") or "unknown"),
                        "retrieved_at": now,
                        "metadata": {"source_name": row.get("source_name")},
                    }
                    for row in rows
                ]
        except Exception as exc:
            logger.warning("Provenance fallback lookup failed: %s", exc)

        return [
            {
                "claim_id": candidate_id,
                "source_system": "synthetic",
                "source_ref": f"fallback:{candidate_id}",
                "retrieved_at": now,
                "metadata": {"reason": "neo4j_unavailable_or_no_rows"},
            }
        ]

    def _safe_property(self, name: str) -> str:
        candidate = str(name or "").strip()
        if not _IDENTIFIER_RE.fullmatch(candidate):
            raise ValueError(f"Invalid Neo4j property name: {name}")
        return candidate

    def _format_path_row(self, row: dict[str, Any]) -> dict[str, Any]:
        nodes = list(row.get("nodes") or [])
        edges = list(row.get("edges") or [])
        relation_types = sorted({str(edge.get("relation_type") or "UNKNOWN") for edge in edges})
        source_systems = sorted({str(edge.get("source_system") or "neo4j") for edge in edges})
        avg_confidence = 0.0
        if edges:
            confidences = [float(edge.get("confidence") or 0.0) for edge in edges]
            avg_confidence = sum(confidences) / len(confidences)

        if nodes:
            path_summary = " -> ".join(str(node.get("display_name") or node.get("node_id")) for node in nodes)
        else:
            path_summary = f"No multi-hop path returned for {row.get('candidate_id', 'unknown')}"

        return {
            "candidate_id": row.get("candidate_id"),
            "candidate_type": row.get("candidate_type") or "Unknown",
            "path_summary": path_summary,
            "nodes": nodes,
            "edges": edges,
            "relation_types": relation_types,
            "supporting_source_systems": source_systems,
            "confidence": avg_confidence if edges else 0.0,
            "source_metadata": {"source_system": "neo4j"},
        }

    def _mock_subgraph(self, entity_id: str) -> list[dict[str, Any]]:
        normalized = entity_id.strip().upper() or "UNKNOWN"
        pathway_id = f"PWY_{normalized[:6]}"
        return [
            {
                "candidate_id": normalized,
                "candidate_type": "Protein",
                "path_summary": f"{normalized} participates in {pathway_id}",
                "nodes": [
                    {"node_id": normalized, "node_labels": ["Protein"], "display_name": normalized},
                    {"node_id": pathway_id, "node_labels": ["Pathway"], "display_name": pathway_id},
                ],
                "edges": [
                    {
                        "edge_id": f"edge:{normalized}:pathway",
                        "relation_type": "PARTICIPATES_IN",
                        "source_node_id": normalized,
                        "target_node_id": pathway_id,
                        "confidence": 0.55,
                        "source_system": "synthetic",
                    }
                ],
                "relation_types": ["PARTICIPATES_IN"],
                "supporting_source_systems": ["synthetic"],
                "confidence": 0.55,
                "source_metadata": {"source_system": "synthetic"},
            }
        ]

    def _mock_similar_entities(self, entity_id: str, top_k: int) -> list[dict[str, Any]]:
        rows: list[dict[str, Any]] = []
        root = entity_id.strip().upper() or "UNKNOWN"
        for idx in range(max(1, int(top_k))):
            sibling = f"{root}_SIM_{idx + 1}"
            rows.append(
                {
                    "candidate_id": sibling,
                    "candidate_type": "Protein",
                    "display_name": sibling,
                    "similarity": max(0.1, 0.85 - idx * 0.1),
                }
            )
        return rows

    def _mock_pathway_context(self, entity_id: str) -> list[dict[str, Any]]:
        protein = entity_id.strip().upper() or "UNKNOWN"
        pathway = f"PWY_{protein[:6]}"
        return [
            {
                "candidate_id": protein,
                "candidate_type": "Protein",
                "path_summary": f"{protein} -> {pathway}",
                "nodes": [
                    {"node_id": protein, "node_labels": ["Protein"], "display_name": protein},
                    {"node_id": pathway, "node_labels": ["Pathway"], "display_name": pathway},
                ],
                "edges": [
                    {
                        "edge_id": f"edge:{protein}:ctx",
                        "relation_type": "PARTICIPATES_IN",
                        "source_node_id": protein,
                        "target_node_id": pathway,
                        "confidence": 0.52,
                        "source_system": "synthetic",
                    }
                ],
                "relation_types": ["PARTICIPATES_IN"],
                "supporting_source_systems": ["synthetic"],
                "confidence": 0.52,
                "source_metadata": {"source_system": "synthetic"},
            }
        ]

    def _mock_publication_hits(self, query_text: str, top_k: int) -> list[dict[str, Any]]:
        out: list[dict[str, Any]] = []
        for idx in range(max(1, int(top_k))):
            out.append(
                {
                    "node_id": f"PUB_FAKE_{idx + 1}",
                    "node_type": "Publication",
                    "title": f"Synthetic publication for: {query_text}",
                    "snippet": f"Mock abstract snippet {idx + 1} for query '{query_text}'.",
                    "score": max(0.1, 0.8 - idx * 0.1),
                    "source": "synthetic",
                    "citation_handle": f"PMID_FAKE_{idx + 1}",
                }
            )
        return out

    def _mock_evidence_hits(self, query_text: str, top_k: int) -> list[dict[str, Any]]:
        out: list[dict[str, Any]] = []
        for idx in range(max(1, int(top_k))):
            out.append(
                {
                    "node_id": f"EVI_FAKE_{idx + 1}",
                    "node_type": "Evidence",
                    "title": None,
                    "snippet": f"Mock evidence snippet {idx + 1} for query '{query_text}'.",
                    "score": max(0.1, 0.75 - idx * 0.08),
                    "source": "synthetic",
                    "citation_handle": f"EVI_CIT_{idx + 1}",
                    "linked_candidate_id": "",
                }
            )
        return out

    def _mock_model_score(self, entity_id: str) -> dict[str, Any]:
        digest = hashlib.md5(entity_id.encode("utf-8")).hexdigest()
        numeric = int(digest[:6], 16)
        score = round((numeric % 1000) / 1000, 4)
        return {
            "candidate_id": entity_id,
            "score_value": score,
            "model_name": "mock_model",
            "model_version": "0",
            "run_id": "mock-run",
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
