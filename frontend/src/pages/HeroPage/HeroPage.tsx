import { Box, Button, Card, CardContent, Container, Grid, Typography } from '@mui/material';
import { Link as RouterLink } from 'react-router-dom';

import { TopNav } from '../../components/layout/TopNav';

const featureCards = [
  'Graph-aware search',
  'Semantic evidence retrieval',
  'ML-driven scoring',
  'Claim verification',
  'Citation-backed answers',
  'Streaming workflows',
];

const steps = ['Retrieve', 'Verify', 'Explain', 'Decide'];

export function HeroPage() {
  return (
    <Box className='min-h-screen'>
      <TopNav />
      <Container maxWidth='lg' className='space-y-12 py-10'>
        <Grid container spacing={4} className='items-center'>
          <Grid size={{ xs: 12, md: 7 }}>
            <Typography variant='h2' className='font-heading'>
              Explainable Pharma Intelligence Platform
            </Typography>
            <Typography className='mt-4 max-w-2xl text-slate-600'>
              Run graph intelligence, verification, and answering in one auditable pipeline with secure auth,
              modular APIs, and streaming workflows.
            </Typography>
            <Box className='mt-6 flex flex-wrap gap-3'>
              <Button variant='contained' component={RouterLink} to='/login'>
                Get Started
              </Button>
              <Button variant='outlined' component={RouterLink} to='/dashboard'>
                View Modules
              </Button>
            </Box>
          </Grid>
          <Grid size={{ xs: 12, md: 5 }}>
            <Card className='rounded-2xl bg-slate-900 text-white'>
              <CardContent className='space-y-3'>
                <Typography variant='h6'>Graph Retrieval</Typography>
                <Typography variant='body2' className='text-slate-300'>
                  Candidate entity expansion from graph neighborhood and semantic vectors.
                </Typography>
                <Typography variant='h6'>Verification</Typography>
                <Typography variant='body2' className='text-slate-300'>
                  Claim-level verdicts with citation traces.
                </Typography>
                <Typography variant='h6'>Answering</Typography>
                <Typography variant='body2' className='text-slate-300'>
                  Explainable response with confidence and evidence appendix.
                </Typography>
              </CardContent>
            </Card>
          </Grid>
        </Grid>

        <Grid container spacing={2} id='features'>
          {featureCards.map((feature) => (
            <Grid key={feature} size={{ xs: 12, sm: 6, md: 4 }}>
              <Card className='h-full rounded-2xl border border-slate-200'>
                <CardContent>
                  <Typography variant='h6' className='font-heading'>
                    {feature}
                  </Typography>
                </CardContent>
              </Card>
            </Grid>
          ))}
        </Grid>

        <Card className='rounded-2xl border border-slate-200'>
          <CardContent>
            <Typography variant='h5' className='mb-4 font-heading'>
              How It Works
            </Typography>
            <Box className='grid grid-cols-2 gap-3 md:grid-cols-4'>
              {steps.map((step, idx) => (
                <Box key={step} className='rounded-xl bg-slate-900 p-4 text-white'>
                  <Typography variant='caption'>Step {idx + 1}</Typography>
                  <Typography variant='h6'>{step}</Typography>
                </Box>
              ))}
            </Box>
          </CardContent>
        </Card>

        <Card className='rounded-2xl bg-cyan-900 text-white'>
          <CardContent className='flex flex-col items-start gap-3 sm:flex-row sm:items-center sm:justify-between'>
            <Typography variant='h6'>Start with a secure test user or create your own account</Typography>
            <Box className='flex gap-2'>
              <Button variant='contained' color='secondary' component={RouterLink} to='/login'>
                Login
              </Button>
              <Button variant='outlined' color='inherit' component={RouterLink} to='/register'>
                Register
              </Button>
            </Box>
          </CardContent>
        </Card>
      </Container>
    </Box>
  );
}
