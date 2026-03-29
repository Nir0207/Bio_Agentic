import { useAppStore } from '../store/appStore';

export function useSnackbar() {
  const showSnackbar = useAppStore((state) => state.showSnackbar);
  const hideSnackbar = useAppStore((state) => state.hideSnackbar);

  return {
    success: (message: string) => showSnackbar(message, 'success'),
    error: (message: string) => showSnackbar(message, 'error'),
    info: (message: string) => showSnackbar(message, 'info'),
    warning: (message: string) => showSnackbar(message, 'warning'),
    close: hideSnackbar,
  };
}
