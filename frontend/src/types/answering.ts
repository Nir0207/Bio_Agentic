export interface AnsweringPayload {
  answer_text: string;
  verdict: string;
  confidence: number;
  citations: string[];
  evidence_appendix: string[];
  style: string;
}

export interface AnsweringResponse {
  payload: AnsweringPayload;
}
