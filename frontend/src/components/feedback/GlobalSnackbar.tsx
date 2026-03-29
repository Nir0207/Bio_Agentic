import { Alert, Snackbar } from '@mui/material';

import { useAppStore } from '../../store/appStore';

export function GlobalSnackbar() {
  const snackbar = useAppStore((state) => state.snackbar);
  const hideSnackbar = useAppStore((state) => state.hideSnackbar);

  return (
    <Snackbar
      open={snackbar.open}
      autoHideDuration={3500}
      onClose={hideSnackbar}
      anchorOrigin={{ vertical: 'bottom', horizontal: 'right' }}
    >
      <Alert onClose={hideSnackbar} severity={snackbar.severity} variant='filled'>
        {snackbar.message}
      </Alert>
    </Snackbar>
  );
}
