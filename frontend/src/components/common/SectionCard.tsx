import { Card, CardContent, Typography } from '@mui/material';
import type { ReactNode } from 'react';

interface SectionCardProps {
  title: string;
  subtitle?: string;
  children: ReactNode;
}

export function SectionCard({ title, subtitle, children }: SectionCardProps) {
  return (
    <Card className='rounded-2xl'>
      <CardContent>
        <Typography variant='h6' className='font-heading'>
          {title}
        </Typography>
        {subtitle ? (
          <Typography variant='body2' color='text.secondary' className='mb-4'>
            {subtitle}
          </Typography>
        ) : null}
        {children}
      </CardContent>
    </Card>
  );
}
