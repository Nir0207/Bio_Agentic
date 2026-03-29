from __future__ import annotations

from collections import OrderedDict
from dataclasses import dataclass

from answering.schemas.citation_models import CitationEntry, CitationKind, CitationMap
from answering.schemas.verified_payload_models import ClaimVerdict, VerifiedPayload


@dataclass(frozen=True)
class _SourceKey:
    kind: CitationKind
    source_id: str


class CitationFormatter:
    """Deterministic citation map builder from verified evidence ids."""

    def format(self, payload: VerifiedPayload) -> CitationMap:
        refs: OrderedDict[_SourceKey, set[str]] = OrderedDict()
        claim_to_keys: dict[str, list[_SourceKey]] = {}

        for verdict in self._supported_verdicts(payload):
            claim_id = verdict.claim.claim_id
            keys_for_claim: list[_SourceKey] = []

            graph_ids = list(verdict.graph_check.supporting_graph_evidence_ids)
            citation_ids = list(verdict.citation_check.supporting_citation_ids)
            score_ids = [
                self._score_block_id(block)
                for block in verdict.score_check.supporting_score_blocks
                if self._score_block_id(block)
            ]

            for graph_id in graph_ids:
                keys_for_claim.append(_SourceKey(kind=CitationKind.GRAPH_PATH, source_id=str(graph_id)))

            for citation_id in citation_ids:
                keys_for_claim.append(
                    _SourceKey(kind=self._infer_doc_kind(citation_id), source_id=str(citation_id))
                )

            for score_id in score_ids:
                keys_for_claim.append(_SourceKey(kind=CitationKind.MODEL_SCORE, source_id=score_id))

            if not keys_for_claim:
                fallback_ids = payload.supporting_evidence_index.get(claim_id, [])
                for source_id in fallback_ids:
                    keys_for_claim.append(
                        _SourceKey(kind=self._infer_fallback_kind(source_id), source_id=str(source_id))
                    )

            deduped_claim_keys: list[_SourceKey] = []
            seen_claim_keys: set[_SourceKey] = set()
            for key in keys_for_claim:
                if key in seen_claim_keys:
                    continue
                seen_claim_keys.add(key)
                deduped_claim_keys.append(key)

                if key not in refs:
                    refs[key] = set()
                refs[key].add(claim_id)

            claim_to_keys[claim_id] = deduped_claim_keys

        entries: list[CitationEntry] = []
        key_to_tag: dict[_SourceKey, str] = {}

        for index, key in enumerate(refs.keys(), start=1):
            tag = f"[C{index}]"
            key_to_tag[key] = tag
            entries.append(
                CitationEntry(
                    citation_number=index,
                    citation_tag=tag,
                    source_id=key.source_id,
                    source_label=self._source_label(key),
                    kind=key.kind,
                    claim_ids=sorted(refs[key]),
                )
            )

        claim_to_tags = {
            claim_id: [key_to_tag[key] for key in keys if key in key_to_tag]
            for claim_id, keys in claim_to_keys.items()
        }

        return CitationMap(entries=entries, claim_to_tags=claim_to_tags)

    @staticmethod
    def _supported_verdicts(payload: VerifiedPayload) -> list[ClaimVerdict]:
        return [
            verdict
            for verdict in payload.claim_verdicts
            if verdict.final_status.value in {"supported", "partially_supported"}
        ]

    @staticmethod
    def _infer_doc_kind(source_id: str) -> CitationKind:
        upper = str(source_id).upper()
        if upper.startswith("PMID:") or upper.startswith("DOI:") or upper.startswith("PMC"):
            return CitationKind.PUBLICATION
        return CitationKind.EVIDENCE_NODE

    @staticmethod
    def _infer_fallback_kind(source_id: str) -> CitationKind:
        source = str(source_id)
        upper = source.upper()
        if upper.startswith("PMID:") or upper.startswith("DOI:") or upper.startswith("PMC"):
            return CitationKind.PUBLICATION
        if ":" in source and "path" not in source.lower():
            return CitationKind.MODEL_SCORE
        if source.lower().startswith("path"):
            return CitationKind.GRAPH_PATH
        return CitationKind.EVIDENCE_NODE

    @staticmethod
    def _score_block_id(block: dict) -> str | None:
        candidate_id = block.get("candidate_id")
        score_name = block.get("score_name")
        if candidate_id is None or score_name is None:
            return None
        return f"{candidate_id}:{score_name}"

    @staticmethod
    def _source_label(source: _SourceKey) -> str:
        if source.kind == CitationKind.GRAPH_PATH:
            return f"Graph path {source.source_id}"
        if source.kind == CitationKind.PUBLICATION:
            return f"Publication {source.source_id}"
        if source.kind == CitationKind.MODEL_SCORE:
            return f"Model score {source.source_id}"
        return f"Evidence node {source.source_id}"
