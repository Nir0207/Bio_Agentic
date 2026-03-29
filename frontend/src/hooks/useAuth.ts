import { useNavigate } from 'react-router-dom';

import type { LoginPayload, RegisterPayload } from '../types/auth';
import { useAuthStore } from '../store/authStore';
import { useAppStore } from '../store/appStore';

export function useAuth() {
  const navigate = useNavigate();
  const authStore = useAuthStore();
  const showSnackbar = useAppStore((state) => state.showSnackbar);

  const login = async (payload: LoginPayload) => {
    await authStore.login(payload);
    showSnackbar('Login successful.', 'success');
    navigate('/dashboard');
  };

  const register = async (payload: RegisterPayload) => {
    await authStore.register(payload);
    showSnackbar('Registration successful. Please login.', 'success');
    navigate('/login');
  };

  const logout = () => {
    authStore.logout();
    showSnackbar('Logged out.', 'info');
    navigate('/login');
  };

  return {
    user: authStore.user,
    loading: authStore.loading,
    isAuthenticated: authStore.isAuthenticated,
    login,
    register,
    logout,
  };
}
