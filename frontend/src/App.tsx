import { useEffect } from 'react';

import { AppRoutes } from './routes';
import { GlobalSnackbar } from './components/feedback/GlobalSnackbar';
import { useAuthStore } from './store/authStore';

export default function App() {
  const hydrate = useAuthStore((state) => state.hydrate);

  useEffect(() => {
    void hydrate();
  }, [hydrate]);

  return (
    <>
      <AppRoutes />
      <GlobalSnackbar />
    </>
  );
}
