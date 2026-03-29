import { useCallback, useState } from 'react';

import type { StreamEvent } from '../types/api';

interface UseStreamingState<TPayload> {
  status: 'idle' | 'running' | 'done' | 'error';
  events: StreamEvent[];
  payload: TPayload | null;
  error: string | null;
  clear: () => void;
  run: (executor: (onEvent: (event: StreamEvent) => void) => Promise<void>) => Promise<void>;
}

export function useStreaming<TPayload = unknown>(): UseStreamingState<TPayload> {
  const [status, setStatus] = useState<'idle' | 'running' | 'done' | 'error'>('idle');
  const [events, setEvents] = useState<StreamEvent[]>([]);
  const [payload, setPayload] = useState<TPayload | null>(null);
  const [error, setError] = useState<string | null>(null);

  const clear = useCallback(() => {
    setStatus('idle');
    setEvents([]);
    setPayload(null);
    setError(null);
  }, []);

  const run = useCallback(async (executor: (onEvent: (event: StreamEvent) => void) => Promise<void>) => {
    setStatus('running');
    setEvents([]);
    setPayload(null);
    setError(null);

    const handleEvent = (event: StreamEvent) => {
      setEvents((prev) => [...prev, event]);
      if (event.event === 'payload') {
        setPayload(event.data as TPayload);
      }
      if (event.event === 'error') {
        setStatus('error');
        setError(typeof event.data === 'string' ? event.data : 'Stream error occurred.');
      }
      if (event.event === 'done') {
        setStatus('done');
      }
    };

    try {
      await executor(handleEvent);
      setStatus((prev) => (prev === 'error' ? 'error' : 'done'));
    } catch (err) {
      setStatus('error');
      setError(err instanceof Error ? err.message : 'Unknown streaming error.');
    }
  }, []);

  return { status, events, payload, error, clear, run };
}
