import ErrorOutlineIcon from '@mui/icons-material/ErrorOutline';
import { Box, Typography } from '@mui/material';

interface ErrorStateProps {
  message: string;
}

export function ErrorState({ message }: ErrorStateProps) {
  return (
    <Box className='rounded-xl border border-rose-200 bg-rose-50 p-4 text-rose-700'>
      <Box className='mb-2 flex items-center gap-2'>
        <ErrorOutlineIcon fontSize='small' />
        <Typography variant='subtitle1'>Something went wrong</Typography>
      </Box>
      <Typography variant='body2'>{message}</Typography>
    </Box>
  );
}
