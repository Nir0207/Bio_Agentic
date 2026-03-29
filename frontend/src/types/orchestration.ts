export interface QueryRequest {
  query: string;
  high_stakes?: boolean;
}

export interface OrchestrationCandidate {
  entity_id: string;
  name: string;
  source: string;
  relationship_hint?: string;
  score?: number;
}

export interface OrchestrationPayload {
  query: string;
  candidates: OrchestrationCandidate[];
  evidence_bundle: Array<Record<string, unknown>>;
  metadata: Record<string, unknown>;
}

export interface OrchestrationResponse {
  payload: OrchestrationPayload;
}
