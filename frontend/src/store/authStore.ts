import { create } from 'zustand';

import type { LoginPayload, RegisterPayload, User } from '../types/auth';
import { authService } from '../services/auth.service';
import { clearToken, getToken, setToken } from '../utils/token';

interface AuthState {
  user: User | null;
  token: string | null;
  isAuthenticated: boolean;
  loading: boolean;
  hydrate: () => Promise<void>;
  login: (payload: LoginPayload) => Promise<void>;
  register: (payload: RegisterPayload) => Promise<void>;
  logout: () => void;
}

export const useAuthStore = create<AuthState>((set) => ({
  user: null,
  token: getToken(),
  isAuthenticated: Boolean(getToken()),
  loading: false,

  hydrate: async () => {
    const existingToken = getToken();
    if (!existingToken) {
      set({ user: null, token: null, isAuthenticated: false });
      return;
    }

    set({ loading: true });
    try {
      const user = await authService.me();
      set({ user, token: existingToken, isAuthenticated: true, loading: false });
    } catch {
      clearToken();
      set({ user: null, token: null, isAuthenticated: false, loading: false });
    }
  },

  login: async (payload) => {
    set({ loading: true });
    const response = await authService.login(payload);
    setToken(response.access_token);
    set({
      user: response.user,
      token: response.access_token,
      isAuthenticated: true,
      loading: false,
    });
  },

  register: async (payload) => {
    set({ loading: true });
    await authService.register(payload);
    set({ loading: false });
  },

  logout: () => {
    clearToken();
    set({ user: null, token: null, isAuthenticated: false, loading: false });
  },
}));
