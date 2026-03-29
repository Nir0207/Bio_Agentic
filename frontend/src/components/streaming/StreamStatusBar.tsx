import { Alert, AlertTitle } from '@mui/material';

interface StreamStatusBarProps {
  status: 'idle' | 'running' | 'done' | 'error';
  error?: string | null;
}

export function StreamStatusBar({ status, error }: StreamStatusBarProps) {
  if (status === 'error') {
    return (
      <Alert severity='error'>
        <AlertTitle>Streaming Error</AlertTitle>
        {error || 'The stream failed.'}
      </Alert>
    );
  }

  if (status === 'running') {
    return (
      <Alert severity='info'>
        <AlertTitle>Streaming In Progress</AlertTitle>
        Live events are being processed.
      </Alert>
    );
  }

  if (status === 'done') {
    return (
      <Alert severity='success'>
        <AlertTitle>Streaming Complete</AlertTitle>
        Final payload was received.
      </Alert>
    );
  }

  return (
    <Alert severity='warning'>
      <AlertTitle>Idle</AlertTitle>
      Start a stream run to see live events.
    </Alert>
  );
}
