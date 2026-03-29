import { Button, Container, Typography } from '@mui/material';
import { Link as RouterLink } from 'react-router-dom';

import { AppLayout } from '../../components/layout/AppLayout';

export function NotFoundPage() {
  return (
    <AppLayout>
      <Container className='py-16 text-center'>
        <Typography variant='h3' className='font-heading'>
          404
        </Typography>
        <Typography variant='h6' className='mb-4'>
          Page not found.
        </Typography>
        <Button component={RouterLink} to='/' variant='contained'>
          Go Home
        </Button>
      </Container>
    </AppLayout>
  );
}
