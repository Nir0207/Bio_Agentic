import { create } from 'zustand';

import type { AnsweringPayload } from '../types/answering';
import type { OrchestrationPayload } from '../types/orchestration';
import type { VerificationPayload } from '../types/verification';

export type SnackbarSeverity = 'success' | 'error' | 'info' | 'warning';

interface SnackbarState {
  open: boolean;
  message: string;
  severity: SnackbarSeverity;
}

interface AppState {
  selectedQuery: string;
  latestOrchestration: OrchestrationPayload | null;
  latestVerification: VerificationPayload | null;
  latestAnswering: AnsweringPayload | null;
  loading: boolean;
  snackbar: SnackbarState;

  setSelectedQuery: (query: string) => void;
  setLatestOrchestration: (payload: OrchestrationPayload | null) => void;
  setLatestVerification: (payload: VerificationPayload | null) => void;
  setLatestAnswering: (payload: AnsweringPayload | null) => void;
  setLoading: (loading: boolean) => void;
  showSnackbar: (message: string, severity?: SnackbarSeverity) => void;
  hideSnackbar: () => void;
}

export const useAppStore = create<AppState>((set) => ({
  selectedQuery: '',
  latestOrchestration: null,
  latestVerification: null,
  latestAnswering: null,
  loading: false,
  snackbar: {
    open: false,
    message: '',
    severity: 'info',
  },

  setSelectedQuery: (query) => set({ selectedQuery: query }),
  setLatestOrchestration: (payload) => set({ latestOrchestration: payload }),
  setLatestVerification: (payload) => set({ latestVerification: payload }),
  setLatestAnswering: (payload) => set({ latestAnswering: payload }),
  setLoading: (loading) => set({ loading }),
  showSnackbar: (message, severity = 'info') =>
    set({ snackbar: { open: true, message, severity } }),
  hideSnackbar: () =>
    set((state) => ({ snackbar: { ...state.snackbar, open: false } })),
}));
