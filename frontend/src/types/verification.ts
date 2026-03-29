export interface ClaimResult {
  claim: string;
  status: string;
  confidence: number;
  citations: string[];
}

export interface VerificationPayload {
  overall_verdict: string;
  overall_confidence: number;
  claims: ClaimResult[];
  warnings: string[];
  citations: string[];
}

export interface VerificationResponse {
  payload: VerificationPayload;
}
