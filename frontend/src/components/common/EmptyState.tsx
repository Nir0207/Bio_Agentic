import InboxOutlinedIcon from '@mui/icons-material/InboxOutlined';
import { Box, Typography } from '@mui/material';

interface EmptyStateProps {
  title: string;
  description: string;
}

export function EmptyState({ title, description }: EmptyStateProps) {
  return (
    <Box className='rounded-xl border border-dashed border-slate-300 bg-white p-6 text-center'>
      <InboxOutlinedIcon className='mb-2 text-slate-400' />
      <Typography variant='h6' className='font-heading'>
        {title}
      </Typography>
      <Typography variant='body2' color='text.secondary'>
        {description}
      </Typography>
    </Box>
  );
}
