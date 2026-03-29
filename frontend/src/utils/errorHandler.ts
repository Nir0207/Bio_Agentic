import type { ApiErrorEnvelope } from '../types/api';

export class AppError extends Error {
  code: string;

  constructor(message: string, code = 'unknown_error') {
    super(message);
    this.name = 'AppError';
    this.code = code;
  }
}

export function mapApiError(payload: unknown): AppError {
  if (payload && typeof payload === 'object' && 'error' in payload) {
    const envelope = payload as ApiErrorEnvelope;
    return new AppError(envelope.error.message, envelope.error.code);
  }
  return new AppError('Unexpected API error.', 'unexpected_error');
}
