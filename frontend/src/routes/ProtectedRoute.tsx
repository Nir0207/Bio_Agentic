import { Navigate, useLocation } from 'react-router-dom';

import { useAuthStore } from '../store/authStore';

interface ProtectedRouteProps {
  children: JSX.Element;
}

export function ProtectedRoute({ children }: ProtectedRouteProps) {
  const isAuthenticated = useAuthStore((state) => state.isAuthenticated);
  const location = useLocation();

  if (!isAuthenticated) {
    return <Navigate to='/login' state={{ from: location.pathname }} replace />;
  }

  return children;
}
