import { apiRequest } from './api';
import type { AuthResponse, LoginPayload, RegisterPayload, User } from '../types/auth';

export const authService = {
  register: (payload: RegisterPayload) =>
    apiRequest<User>('/auth/register', {
      method: 'POST',
      body: payload,
      withAuth: false,
    }),

  login: (payload: LoginPayload) =>
    apiRequest<AuthResponse>('/auth/login', {
      method: 'POST',
      body: payload,
      withAuth: false,
    }),

  me: () => apiRequest<User>('/auth/me'),
};
