import { Navigate, Route, Routes } from 'react-router-dom';

import { ProtectedRoute } from './ProtectedRoute';
import { HeroPage } from '../pages/HeroPage/HeroPage';
import { LoginPage } from '../pages/LoginPage/LoginPage';
import { RegisterPage } from '../pages/RegisterPage/RegisterPage';
import { DashboardPage } from '../pages/DashboardPage/DashboardPage';
import { OrchestrationPage } from '../pages/OrchestrationPage/OrchestrationPage';
import { VerificationPage } from '../pages/VerificationPage/VerificationPage';
import { AnsweringPage } from '../pages/AnsweringPage/AnsweringPage';
import { NotFoundPage } from '../pages/NotFoundPage/NotFoundPage';

export function AppRoutes() {
  return (
    <Routes>
      <Route path='/' element={<HeroPage />} />
      <Route path='/login' element={<LoginPage />} />
      <Route path='/register' element={<RegisterPage />} />

      <Route
        path='/dashboard'
        element={
          <ProtectedRoute>
            <DashboardPage />
          </ProtectedRoute>
        }
      />
      <Route
        path='/orchestration'
        element={
          <ProtectedRoute>
            <OrchestrationPage />
          </ProtectedRoute>
        }
      />
      <Route
        path='/verification'
        element={
          <ProtectedRoute>
            <VerificationPage />
          </ProtectedRoute>
        }
      />
      <Route
        path='/answering'
        element={
          <ProtectedRoute>
            <AnsweringPage />
          </ProtectedRoute>
        }
      />

      <Route path='/home' element={<Navigate to='/' replace />} />
      <Route path='*' element={<NotFoundPage />} />
    </Routes>
  );
}
