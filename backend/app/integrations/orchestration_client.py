from __future__ import annotations

import json
import subprocess
from pathlib import Path
from typing import Any

from app.core.logging import get_logger
from app.integrations.graph_client import GraphClient
from app.integrations.modeling_client import ModelingClient
from app.utils.helpers import utc_now_iso

logger = get_logger('orchestration_client')


class OrchestrationClient:
    def __init__(self) -> None:
        self.graph_client = GraphClient()
        self.modeling_client = ModelingClient()
        self.repo_root = Path(__file__).resolve().parents[3]

    def run(self, query: str, high_stakes: bool = False) -> dict[str, Any]:
        cli_result = self._try_run_phase_cli(query=query, high_stakes=high_stakes)
        if cli_result is not None:
            return cli_result
        return self._fallback_payload(query=query, high_stakes=high_stakes)

    def _try_run_phase_cli(self, query: str, high_stakes: bool) -> dict[str, Any] | None:
        command = [
            'python',
            '-m',
            'orchestration.app.cli',
            'run',
            'query',
            '--text',
            query,
        ]
        if high_stakes:
            command.append('--high-stakes')

        try:
            result = subprocess.run(
                command,
                cwd=str(self.repo_root),
                capture_output=True,
                text=True,
                timeout=45,
                check=False,
            )
        except Exception as exc:
            logger.error('Orchestration phase invocation failed.', extra={'error_details': str(exc)})
            return None

        if result.returncode != 0 or not result.stdout.strip():
            logger.info(
                'Orchestration phase unavailable, using fallback adapter.',
                extra={'error_details': {'returncode': result.returncode, 'stderr': result.stderr[-500:]}},
            )
            return None

        parsed = self._parse_json_payload(result.stdout)
        if not parsed:
            return None

        payload = parsed.get('final_payload') if isinstance(parsed, dict) and 'final_payload' in parsed else parsed
        if not isinstance(payload, dict):
            return None

        return {
            'query': query,
            'candidates': payload.get('candidate_bundle', {}).get('candidates', []),
            'evidence_bundle': payload.get('evidence_bundle', {}).get('evidence_rows', []),
            'metadata': {
                'high_stakes': high_stakes,
                'integration_mode': 'phase_cli',
                'timestamp': utc_now_iso(),
                'sources': ['orchestration', 'embeddings', 'graphML', 'modeling'],
            },
        }

    @staticmethod
    def _parse_json_payload(raw_output: str) -> dict[str, Any] | None:
        stripped = raw_output.strip()
        try:
            return json.loads(stripped)
        except json.JSONDecodeError:
            lines = stripped.splitlines()
            for idx in range(len(lines)):
                chunk = '\n'.join(lines[idx:])
                try:
                    return json.loads(chunk)
                except json.JSONDecodeError:
                    continue
        return None

    def _fallback_payload(self, query: str, high_stakes: bool) -> dict[str, Any]:
        candidates = self.graph_client.extract_candidate_entities(query)
        scored_candidates = self.modeling_client.score_candidates(candidates)

        evidence_bundle = [
            {
                'evidence_id': f'EV{idx + 1}',
                'candidate_id': candidate.get('entity_id'),
                'summary': f"Evidence snippet for {candidate.get('name')} from embeddings retrieval.",
                'source': 'embeddings',
            }
            for idx, candidate in enumerate(scored_candidates)
        ]

        return {
            'query': query,
            'candidates': scored_candidates,
            'evidence_bundle': evidence_bundle,
            'metadata': {
                'high_stakes': high_stakes,
                'integration_mode': 'fallback_adapter',
                'timestamp': utc_now_iso(),
                'sources': ['embeddings', 'graphML', 'modeling', 'orchestration'],
            },
        }
