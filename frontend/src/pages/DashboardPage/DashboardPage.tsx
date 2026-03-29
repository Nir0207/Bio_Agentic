import { useState } from 'react';
import { Box, Button, Grid, Paper, TextField, Typography } from '@mui/material';
import { Link as RouterLink } from 'react-router-dom';

import { AppLayout } from '../../components/layout/AppLayout';
import { PageHeader } from '../../components/common/PageHeader';
import { CapabilityCards } from '../../modules/dashboard/components/CapabilityCards';
import { orchestrationService } from '../../services/orchestration.service';
import { useAppStore } from '../../store/appStore';

export function DashboardPage() {
  const [query, setQuery] = useState('Summarize EGFR inhibitor evidence in NSCLC.');
  const latestOrchestration = useAppStore((state) => state.latestOrchestration);
  const setLatestOrchestration = useAppStore((state) => state.setLatestOrchestration);
  const showSnackbar = useAppStore((state) => state.showSnackbar);

  const runQuickQuery = async () => {
    try {
      const response = await orchestrationService.run({ query });
      setLatestOrchestration(response.payload);
      showSnackbar('Quick run completed.', 'success');
    } catch (error) {
      showSnackbar(error instanceof Error ? error.message : 'Quick run failed.', 'error');
    }
  };

  return (
    <AppLayout withSidebar>
      <PageHeader title='Dashboard' subtitle='Overview of orchestration, verification, and answering.' />

      <Box className='space-y-6'>
        <CapabilityCards />

        <Grid container spacing={2}>
          <Grid size={{ xs: 12, md: 8 }}>
            <Paper className='rounded-xl border border-slate-200 p-4'>
              <Typography variant='h6' className='mb-2 font-heading'>
                Quick Query Runner
              </Typography>
              <TextField fullWidth value={query} onChange={(event) => setQuery(event.target.value)} />
              <Button className='mt-3' variant='contained' onClick={runQuickQuery}>
                Run Query
              </Button>
            </Paper>
          </Grid>

          <Grid size={{ xs: 12, md: 4 }}>
            <Paper className='rounded-xl border border-slate-200 p-4'>
              <Typography variant='h6' className='font-heading'>
                Recent Status
              </Typography>
              <Typography variant='body2' color='text.secondary'>
                {latestOrchestration ? 'Latest orchestration payload is available.' : 'No recent orchestration run.'}
              </Typography>
            </Paper>
          </Grid>
        </Grid>

        <Grid container spacing={2}>
          <Grid size={{ xs: 12, md: 4 }}>
            <Paper className='rounded-xl border border-slate-200 p-4'>
              <Typography variant='h6' className='font-heading'>
                Go to Orchestration
              </Typography>
              <Button component={RouterLink} to='/orchestration' variant='outlined'>
                Open
              </Button>
            </Paper>
          </Grid>
          <Grid size={{ xs: 12, md: 4 }}>
            <Paper className='rounded-xl border border-slate-200 p-4'>
              <Typography variant='h6' className='font-heading'>
                Go to Verification
              </Typography>
              <Button component={RouterLink} to='/verification' variant='outlined'>
                Open
              </Button>
            </Paper>
          </Grid>
          <Grid size={{ xs: 12, md: 4 }}>
            <Paper className='rounded-xl border border-slate-200 p-4'>
              <Typography variant='h6' className='font-heading'>
                Go to Answering
              </Typography>
              <Button component={RouterLink} to='/answering' variant='outlined'>
                Open
              </Button>
            </Paper>
          </Grid>
        </Grid>
      </Box>
    </AppLayout>
  );
}
