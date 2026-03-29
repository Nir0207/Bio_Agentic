import { useState } from 'react';
import { Box, Button, Chip, Grid, Paper, TextField, Typography } from '@mui/material';

import { AppLayout } from '../../components/layout/AppLayout';
import { EmptyState } from '../../components/common/EmptyState';
import { PageHeader } from '../../components/common/PageHeader';
import { ClaimsTable } from '../../modules/verification/components/ClaimsTable';
import { verificationService } from '../../services/verification.service';
import { useAppStore } from '../../store/appStore';
import { pct, titleCase } from '../../utils/format';

export function VerificationPage() {
  const selectedQuery = useAppStore((state) => state.selectedQuery);
  const orchestrationPayload = useAppStore((state) => state.latestOrchestration);
  const payload = useAppStore((state) => state.latestVerification);
  const setPayload = useAppStore((state) => state.setLatestVerification);
  const showSnackbar = useAppStore((state) => state.showSnackbar);

  const [query, setQuery] = useState(selectedQuery || 'Verify claims for recent orchestration output.');

  const run = async () => {
    try {
      const response = await verificationService.run({
        query,
        orchestration_payload: orchestrationPayload || undefined,
      });
      setPayload(response.payload);
      showSnackbar('Verification completed.', 'success');
    } catch (error) {
      showSnackbar(error instanceof Error ? error.message : 'Verification failed.', 'error');
    }
  };

  return (
    <AppLayout withSidebar>
      <PageHeader
        title='Verification'
        subtitle='Inspect claim-level support, warnings, and citation evidence.'
      />

      <Grid container spacing={2}>
        <Grid size={{ xs: 12 }}>
          <Paper className='rounded-xl border border-slate-200 p-4'>
            <TextField fullWidth value={query} onChange={(event) => setQuery(event.target.value)} />
            <Button className='mt-3' variant='contained' onClick={run}>
              Run Verification
            </Button>
          </Paper>
        </Grid>

        <Grid size={{ xs: 12 }}>
          {payload ? (
            <Paper className='rounded-xl border border-slate-200 p-4'>
              <Typography variant='h6' className='font-heading'>
                Summary
              </Typography>
              <Box className='mt-2 flex flex-wrap gap-2'>
                <Chip label={`Verdict: ${titleCase(payload.overall_verdict)}`} color='primary' />
                <Chip label={`Confidence: ${pct(payload.overall_confidence)}`} color='secondary' />
                <Chip label='Review: Ready' variant='outlined' />
              </Box>
            </Paper>
          ) : (
            <EmptyState title='No verification result' description='Run verification to populate summary and claims.' />
          )}
        </Grid>

        <Grid size={{ xs: 12, lg: 8 }}>
          <Paper className='rounded-xl border border-slate-200 p-4'>
            <Typography variant='h6' className='mb-2 font-heading'>
              Claims
            </Typography>
            {payload?.claims?.length ? (
              <ClaimsTable claims={payload.claims} />
            ) : (
              <EmptyState title='No claims yet' description='Claim cards appear after verification run.' />
            )}
          </Paper>
        </Grid>

        <Grid size={{ xs: 12, lg: 4 }}>
          <Paper className='rounded-xl border border-amber-200 bg-amber-50 p-4'>
            <Typography variant='h6' className='font-heading'>
              Warnings
            </Typography>
            {payload?.warnings?.length ? (
              payload.warnings.map((warning, index) => (
                <Typography key={`${warning}-${index}`} variant='body2'>
                  - {warning}
                </Typography>
              ))
            ) : (
              <Typography variant='body2'>No warnings.</Typography>
            )}
          </Paper>

          <Paper className='mt-2 rounded-xl border border-slate-200 p-4'>
            <Typography variant='h6' className='font-heading'>
              Missing Evidence
            </Typography>
            <Typography variant='body2' color='text.secondary'>
              Review partially supported and unsupported claims for gaps.
            </Typography>
          </Paper>
        </Grid>

        <Grid size={{ xs: 12 }}>
          <Paper className='rounded-xl border border-slate-200 p-4'>
            <Typography variant='h6' className='font-heading'>
              Citations / Evidence Appendix
            </Typography>
            {payload?.citations?.length ? (
              payload.citations.map((citation, index) => (
                <Typography key={`${citation}-${index}`} variant='body2'>
                  - {citation}
                </Typography>
              ))
            ) : (
              <Typography variant='body2' color='text.secondary'>
                No citations yet.
              </Typography>
            )}
          </Paper>
        </Grid>
      </Grid>
    </AppLayout>
  );
}
