import { apiRequest, streamRequest } from './api';
import type { AnsweringResponse } from '../types/answering';
import type { StreamEvent } from '../types/api';

interface AnsweringRequest {
  query?: string;
  verified_payload?: unknown;
  style?: string;
}

export const answeringService = {
  run: (payload: AnsweringRequest) =>
    apiRequest<AnsweringResponse>('/answering/run', {
      method: 'POST',
      body: payload,
    }),

  streamRun: (payload: AnsweringRequest, onEvent: (event: StreamEvent) => void) =>
    streamRequest('/answering/stream', payload, onEvent),
};
