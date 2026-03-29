import { Box, CircularProgress, Typography } from '@mui/material';

interface LoaderProps {
  message?: string;
}

export function Loader({ message = 'Loading...' }: LoaderProps) {
  return (
    <Box className='flex min-h-[160px] items-center justify-center gap-3'>
      <CircularProgress size={24} />
      <Typography>{message}</Typography>
    </Box>
  );
}
