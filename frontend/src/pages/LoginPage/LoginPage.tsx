import { useState } from 'react';
import { Box, Button, Card, CardContent, Container, Link, TextField, Typography } from '@mui/material';
import { Link as RouterLink } from 'react-router-dom';

import { AppLayout } from '../../components/layout/AppLayout';
import { ErrorState } from '../../components/common/ErrorState';
import { TestUserHint } from '../../modules/auth/components/TestUserHint';
import { useAuth } from '../../hooks/useAuth';

export function LoginPage() {
  const { login, loading } = useAuth();
  const [email, setEmail] = useState('admin@pharma.ai');
  const [password, setPassword] = useState('admin123');
  const [error, setError] = useState<string | null>(null);

  const onSubmit = async (event: React.FormEvent) => {
    event.preventDefault();
    setError(null);
    try {
      await login({ email, password });
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unable to login.');
    }
  };

  return (
    <AppLayout>
      <Container maxWidth='sm' className='py-10'>
        <Card className='rounded-2xl'>
          <CardContent className='space-y-4'>
            <Typography variant='h4' className='font-heading'>
              Login
            </Typography>
            <form className='space-y-4' onSubmit={onSubmit}>
              <TextField fullWidth label='Email' value={email} onChange={(event) => setEmail(event.target.value)} />
              <TextField
                fullWidth
                type='password'
                label='Password'
                value={password}
                onChange={(event) => setPassword(event.target.value)}
              />
              {error ? <ErrorState message={error} /> : null}
              <Button type='submit' variant='contained' fullWidth disabled={loading}>
                Login
              </Button>
            </form>
            <TestUserHint />
            <Box>
              <Typography variant='body2'>
                Need an account?{' '}
                <Link component={RouterLink} to='/register'>
                  Register
                </Link>
              </Typography>
            </Box>
          </CardContent>
        </Card>
      </Container>
    </AppLayout>
  );
}
