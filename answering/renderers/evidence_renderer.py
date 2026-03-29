from __future__ import annotations

import logging
from collections import OrderedDict

from answering.app.config import Settings
from answering.schemas.answer_models import EvidenceAppendix
from answering.schemas.citation_models import CitationKind, CitationMap
from answering.schemas.verified_payload_models import ClaimVerdict, VerifiedPayload

logger = logging.getLogger(__name__)

try:
    from neo4j import GraphDatabase
except Exception:  # noqa: BLE001
    GraphDatabase = None


class EvidenceAppendixRenderer:
    def render(
        self,
        payload: VerifiedPayload,
        citations: CitationMap,
        *,
        settings: Settings,
    ) -> EvidenceAppendix:
        graph_items = self._graph_items(payload)

        if settings.enable_optional_enrichment:
            graph_items = self._enrich_graph_items(graph_items, settings=settings)

        publication_and_evidence = [
            f"{entry.citation_tag} {entry.source_label}"
            for entry in citations.entries
            if entry.kind in {CitationKind.PUBLICATION, CitationKind.EVIDENCE_NODE, CitationKind.MODEL_SCORE}
        ]

        unresolved = [
            f"{claim_id}: {', '.join(gaps)}"
            for claim_id, gaps in payload.missing_evidence_index.items()
            if gaps
        ]

        return EvidenceAppendix(
            graph_evidence_items=graph_items,
            publication_and_evidence_citations=publication_and_evidence,
            unresolved_gaps=unresolved,
            warnings=list(payload.warnings),
        )

    @staticmethod
    def _supported_verdicts(payload: VerifiedPayload) -> list[ClaimVerdict]:
        return [
            verdict
            for verdict in payload.claim_verdicts
            if verdict.final_status.value in {"supported", "partially_supported"}
        ]

    def _graph_items(self, payload: VerifiedPayload) -> list[str]:
        ordered: OrderedDict[str, None] = OrderedDict()
        for verdict in self._supported_verdicts(payload):
            claim_id = verdict.claim.claim_id
            for graph_id in verdict.graph_check.supporting_graph_evidence_ids:
                ordered[f"{claim_id}: graph_path={graph_id}"] = None
        return list(ordered.keys())

    def _enrich_graph_items(self, graph_items: list[str], *, settings: Settings) -> list[str]:
        if GraphDatabase is None:
            logger.warning("Optional enrichment enabled but neo4j package is not installed.")
            return graph_items

        try:
            driver = GraphDatabase.driver(
                settings.neo4j_uri,
                auth=(settings.neo4j_username, settings.neo4j_password),
            )
        except Exception as exc:  # noqa: BLE001
            logger.warning("Unable to initialize Neo4j driver for optional enrichment: %s", exc)
            return graph_items

        enriched: list[str] = []
        with driver:
            for item in graph_items:
                path_id = item.split("graph_path=", maxsplit=1)[-1]
                extra = self._lookup_path_summary(driver=driver, path_id=path_id, settings=settings)
                enriched.append(f"{item} | enrichment={extra}" if extra else item)

        return enriched

    @staticmethod
    def _lookup_path_summary(*, driver, path_id: str, settings: Settings) -> str | None:
        query = """
        MATCH (n)-[r]->(m)
        WHERE coalesce(r.edge_id, r.id, '') = $path_id OR coalesce(r.path_id, '') = $path_id
        RETURN labels(n) AS src_labels, labels(m) AS dst_labels, type(r) AS rel_type
        LIMIT 1
        """

        try:
            with driver.session(database=settings.neo4j_database) as session:
                record = session.run(query, path_id=path_id).single()
                if not record:
                    return None
                src = "/".join(record.get("src_labels") or [])
                dst = "/".join(record.get("dst_labels") or [])
                rel = record.get("rel_type") or "RELATED_TO"
                return f"{src} -[{rel}]-> {dst}".strip()
        except Exception as exc:  # noqa: BLE001
            logger.warning("Optional enrichment lookup failed for path %s: %s", path_id, exc)
            return None
