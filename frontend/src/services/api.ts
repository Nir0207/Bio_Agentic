import { getToken } from '../utils/token';
import { AppError, mapApiError } from '../utils/errorHandler';
import type { StreamEvent, StreamEventType } from '../types/api';

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000/api/v1';

interface RequestOptions {
  method?: string;
  body?: unknown;
  withAuth?: boolean;
  headers?: Record<string, string>;
}

export async function apiRequest<T>(path: string, options: RequestOptions = {}): Promise<T> {
  const { method = 'GET', body, withAuth = true, headers = {} } = options;
  const token = getToken();

  const response = await fetch(`${API_URL}${path}`, {
    method,
    headers: {
      'Content-Type': 'application/json',
      ...(withAuth && token ? { Authorization: `Bearer ${token}` } : {}),
      ...headers,
    },
    body: body !== undefined ? JSON.stringify(body) : undefined,
  });

  if (!response.ok) {
    let payload: unknown = null;
    try {
      payload = await response.json();
    } catch {
      throw new AppError('Request failed and response was not JSON.', 'network_error');
    }
    throw mapApiError(payload);
  }

  return (await response.json()) as T;
}

export async function streamRequest(
  path: string,
  body: unknown,
  onEvent: (event: StreamEvent) => void,
): Promise<void> {
  const token = getToken();
  const response = await fetch(`${API_URL}${path}`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      Accept: 'text/event-stream',
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
    },
    body: JSON.stringify(body),
  });

  if (!response.ok || !response.body) {
    let payload: unknown = null;
    try {
      payload = await response.json();
    } catch {
      throw new AppError('Streaming request failed.', 'stream_error');
    }
    throw mapApiError(payload);
  }

  const reader = response.body.getReader();
  const decoder = new TextDecoder();
  let buffer = '';

  while (true) {
    const { done, value } = await reader.read();
    if (done) {
      break;
    }

    buffer += decoder.decode(value, { stream: true });
    const parts = buffer.split('\n\n');
    buffer = parts.pop() || '';

    for (const raw of parts) {
      const lines = raw.split('\n');
      const eventLine = lines.find((line) => line.startsWith('event:'));
      const dataLine = lines.find((line) => line.startsWith('data:'));
      if (!eventLine || !dataLine) {
        continue;
      }

      const event = eventLine.replace('event:', '').trim() as StreamEventType;
      const dataText = dataLine.replace('data:', '').trim();
      let data: unknown;

      try {
        data = JSON.parse(dataText);
      } catch {
        data = { raw: dataText };
      }

      onEvent({ event, data });
    }
  }
}
