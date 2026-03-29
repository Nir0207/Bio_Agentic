export interface ApiErrorBody {
  code: string;
  message: string;
  request_id: string;
}

export interface ApiErrorEnvelope {
  error: ApiErrorBody;
}

export type StreamEventType = 'start' | 'progress' | 'partial_text' | 'payload' | 'done' | 'error';

export interface StreamEvent<T = unknown> {
  event: StreamEventType;
  data: T;
}
