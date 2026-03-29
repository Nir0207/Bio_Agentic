import { apiRequest, streamRequest } from './api';
import type { OrchestrationResponse, QueryRequest } from '../types/orchestration';
import type { StreamEvent } from '../types/api';

export const orchestrationService = {
  run: (payload: QueryRequest) =>
    apiRequest<OrchestrationResponse>('/orchestration/run', {
      method: 'POST',
      body: payload,
    }),

  streamRun: (payload: QueryRequest, onEvent: (event: StreamEvent) => void) =>
    streamRequest('/orchestration/stream', payload, onEvent),
};
