import { useState } from 'react';
import { Box, Button, Card, CardContent, Container, Link, TextField, Typography } from '@mui/material';
import { Link as RouterLink } from 'react-router-dom';

import { AppLayout } from '../../components/layout/AppLayout';
import { ErrorState } from '../../components/common/ErrorState';
import { useAuth } from '../../hooks/useAuth';

export function RegisterPage() {
  const { register, loading } = useAuth();
  const [fullName, setFullName] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [error, setError] = useState<string | null>(null);

  const onSubmit = async (event: React.FormEvent) => {
    event.preventDefault();
    setError(null);

    if (password !== confirmPassword) {
      setError('Passwords do not match.');
      return;
    }

    try {
      await register({ full_name: fullName, email, password });
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unable to register.');
    }
  };

  return (
    <AppLayout>
      <Container maxWidth='sm' className='py-10'>
        <Card className='rounded-2xl'>
          <CardContent className='space-y-4'>
            <Typography variant='h4' className='font-heading'>
              Register
            </Typography>
            <form className='space-y-4' onSubmit={onSubmit}>
              <TextField
                fullWidth
                label='Full name'
                value={fullName}
                onChange={(event) => setFullName(event.target.value)}
              />
              <TextField fullWidth label='Email' value={email} onChange={(event) => setEmail(event.target.value)} />
              <TextField
                fullWidth
                type='password'
                label='Password'
                value={password}
                onChange={(event) => setPassword(event.target.value)}
              />
              <TextField
                fullWidth
                type='password'
                label='Confirm password'
                value={confirmPassword}
                onChange={(event) => setConfirmPassword(event.target.value)}
              />
              {error ? <ErrorState message={error} /> : null}
              <Button type='submit' variant='contained' fullWidth disabled={loading}>
                Register
              </Button>
            </form>
            <Box>
              <Typography variant='body2'>
                Already have an account?{' '}
                <Link component={RouterLink} to='/login'>
                  Login
                </Link>
              </Typography>
            </Box>
          </CardContent>
        </Card>
      </Container>
    </AppLayout>
  );
}
