import { apiRequest } from './api';
import type { VerificationResponse } from '../types/verification';

interface VerificationRequest {
  query?: string;
  orchestration_payload?: unknown;
}

export const verificationService = {
  run: (payload: VerificationRequest) =>
    apiRequest<VerificationResponse>('/verification/run', {
      method: 'POST',
      body: payload,
    }),
};
