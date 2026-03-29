import { Box, Typography } from '@mui/material';
import type { ReactNode } from 'react';

interface PageHeaderProps {
  title: string;
  subtitle: string;
  rightSlot?: ReactNode;
}

export function PageHeader({ title, subtitle, rightSlot }: PageHeaderProps) {
  return (
    <Box className='mb-6 flex flex-col justify-between gap-3 sm:flex-row sm:items-center'>
      <Box>
        <Typography variant='h4' className='font-heading'>
          {title}
        </Typography>
        <Typography color='text.secondary'>{subtitle}</Typography>
      </Box>
      {rightSlot ? <Box>{rightSlot}</Box> : null}
    </Box>
  );
}
