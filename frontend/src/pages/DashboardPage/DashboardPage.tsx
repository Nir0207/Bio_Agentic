import { useMemo, useState } from 'react';
import {
  Alert,
  Box,
  Button,
  Chip,
  Divider,
  Grid,
  List,
  ListItem,
  ListItemText,
  Paper,
  Tab,
  Tabs,
  TextField,
  Typography,
} from '@mui/material';
import { Link as RouterLink } from 'react-router-dom';

import { AppLayout } from '../../components/layout/AppLayout';
import { EmptyState } from '../../components/common/EmptyState';
import { PageHeader } from '../../components/common/PageHeader';
import { CapabilityCards } from '../../modules/dashboard/components/CapabilityCards';
import { orchestrationService } from '../../services/orchestration.service';
import { useAppStore } from '../../store/appStore';

function DashboardTabPanel({
  active,
  index,
  children,
}: {
  active: number;
  index: number;
  children: React.ReactNode;
}) {
  if (active !== index) {
    return null;
  }
  return <Box className='pt-4'>{children}</Box>;
}

export function DashboardPage() {
  const [query, setQuery] = useState('Summarize EGFR inhibitor evidence in NSCLC.');
  const [activeTab, setActiveTab] = useState(0);

  const latestOrchestration = useAppStore((state) => state.latestOrchestration);
  const setLatestOrchestration = useAppStore((state) => state.setLatestOrchestration);
  const setSelectedQuery = useAppStore((state) => state.setSelectedQuery);
  const showSnackbar = useAppStore((state) => state.showSnackbar);

  const summary = useMemo(() => {
    if (!latestOrchestration) {
      return null;
    }
    return {
      candidateCount: latestOrchestration.candidates.length,
      evidenceCount: latestOrchestration.evidence_bundle.length,
      integrationMode: String(latestOrchestration.metadata.integration_mode || 'unknown'),
      sourceCount: Array.isArray(latestOrchestration.metadata.sources)
        ? latestOrchestration.metadata.sources.length
        : 0,
    };
  }, [latestOrchestration]);

  const runQuickQuery = async () => {
    try {
      const response = await orchestrationService.run({ query });
      setLatestOrchestration(response.payload);
      setSelectedQuery(query);
      setActiveTab(1);
      showSnackbar('Quick run completed. Result is now in Result Snapshot.', 'success');
    } catch (error) {
      showSnackbar(error instanceof Error ? error.message : 'Quick run failed.', 'error');
    }
  };

  return (
    <AppLayout withSidebar>
      <PageHeader
        title='Dashboard'
        subtitle='Run one query, inspect results, then move step-by-step through verification and answering.'
      />

      <Box className='space-y-6'>
        <CapabilityCards />

        <Paper className='rounded-xl border border-slate-200 p-4'>
          <Tabs
            value={activeTab}
            onChange={(_, nextValue) => setActiveTab(nextValue)}
            variant='scrollable'
            allowScrollButtonsMobile
          >
            <Tab label='Run Query' />
            <Tab label='Result Snapshot' />
            <Tab label='Guided Flow' />
          </Tabs>

          <DashboardTabPanel active={activeTab} index={0}>
            <Typography variant='h6' className='mb-2 font-heading'>
              Quick Query Runner
            </Typography>
            <Typography variant='body2' color='text.secondary' className='mb-3'>
              This runs orchestration only and prepares context for the next pages.
            </Typography>
            <TextField
              fullWidth
              multiline
              minRows={3}
              value={query}
              onChange={(event) => setQuery(event.target.value)}
            />
            <Box className='mt-3 flex flex-wrap gap-2'>
              <Button variant='contained' onClick={runQuickQuery}>
                Run Query
              </Button>
              <Button component={RouterLink} to='/orchestration' variant='outlined'>
                Open Full Orchestration Page
              </Button>
            </Box>
          </DashboardTabPanel>

          <DashboardTabPanel active={activeTab} index={1}>
            {latestOrchestration ? (
              <Box className='space-y-4'>
                <Alert severity='success'>
                  Latest orchestration payload is ready. You can verify claims next.
                </Alert>

                <Box className='flex flex-wrap gap-2'>
                  <Chip label={`Candidates: ${summary?.candidateCount ?? 0}`} color='primary' />
                  <Chip label={`Evidence rows: ${summary?.evidenceCount ?? 0}`} color='secondary' />
                  <Chip label={`Mode: ${summary?.integrationMode ?? 'unknown'}`} variant='outlined' />
                  <Chip label={`Sources: ${summary?.sourceCount ?? 0}`} variant='outlined' />
                </Box>

                <Grid container spacing={2}>
                  <Grid size={{ xs: 12, md: 6 }}>
                    <Typography variant='subtitle1' className='font-heading'>
                      Top Candidates
                    </Typography>
                    <List dense>
                      {latestOrchestration.candidates.slice(0, 5).map((candidate) => (
                        <ListItem key={candidate.entity_id} divider>
                          <ListItemText
                            primary={`${candidate.name} (${candidate.source})`}
                            secondary={candidate.relationship_hint || 'No hint'}
                          />
                        </ListItem>
                      ))}
                    </List>
                  </Grid>

                  <Grid size={{ xs: 12, md: 6 }}>
                    <Typography variant='subtitle1' className='font-heading'>
                      Evidence Preview
                    </Typography>
                    <List dense>
                      {latestOrchestration.evidence_bundle.slice(0, 5).map((evidence, index) => (
                        <ListItem key={index} divider>
                          <ListItemText
                            primary={String(evidence.summary || 'Evidence row')}
                            secondary={String(evidence.source || 'Unknown source')}
                          />
                        </ListItem>
                      ))}
                    </List>
                  </Grid>
                </Grid>

                <Divider />

                <Box className='flex flex-wrap gap-2'>
                  <Button component={RouterLink} to='/verification' variant='contained'>
                    Continue to Verification
                  </Button>
                  <Button component={RouterLink} to='/orchestration' variant='outlined'>
                    Inspect Full Orchestration
                  </Button>
                </Box>
              </Box>
            ) : (
              <EmptyState
                title='No quick-run result yet'
                description='Run a query first, then this tab will show a concise orchestration snapshot.'
              />
            )}
          </DashboardTabPanel>

          <DashboardTabPanel active={activeTab} index={2}>
            <Typography variant='h6' className='mb-3 font-heading'>
              Recommended Flow
            </Typography>
            <Grid container spacing={2}>
              <Grid size={{ xs: 12, md: 3 }}>
                <Paper className='h-full rounded-xl border border-slate-200 p-3'>
                  <Typography variant='overline'>Step 1</Typography>
                  <Typography variant='subtitle1' className='font-heading'>
                    Run
                  </Typography>
                  <Typography variant='body2' color='text.secondary'>
                    Run orchestration here or in the orchestration page.
                  </Typography>
                </Paper>
              </Grid>
              <Grid size={{ xs: 12, md: 3 }}>
                <Paper className='h-full rounded-xl border border-slate-200 p-3'>
                  <Typography variant='overline'>Step 2</Typography>
                  <Typography variant='subtitle1' className='font-heading'>
                    Verify
                  </Typography>
                  <Typography variant='body2' color='text.secondary'>
                    Validate claims and inspect support levels.
                  </Typography>
                </Paper>
              </Grid>
              <Grid size={{ xs: 12, md: 3 }}>
                <Paper className='h-full rounded-xl border border-slate-200 p-3'>
                  <Typography variant='overline'>Step 3</Typography>
                  <Typography variant='subtitle1' className='font-heading'>
                    Answer
                  </Typography>
                  <Typography variant='body2' color='text.secondary'>
                    Generate the final explainable answer.
                  </Typography>
                </Paper>
              </Grid>
              <Grid size={{ xs: 12, md: 3 }}>
                <Paper className='h-full rounded-xl border border-slate-200 p-3'>
                  <Typography variant='overline'>Step 4</Typography>
                  <Typography variant='subtitle1' className='font-heading'>
                    Review
                  </Typography>
                  <Typography variant='body2' color='text.secondary'>
                    Cross-check citations and confidence before use.
                  </Typography>
                </Paper>
              </Grid>
            </Grid>

            <Box className='mt-4 flex flex-wrap gap-2'>
              <Button component={RouterLink} to='/orchestration' variant='outlined'>
                Orchestration
              </Button>
              <Button
                component={RouterLink}
                to='/verification'
                variant='outlined'
                disabled={!latestOrchestration}
              >
                Verification
              </Button>
              <Button component={RouterLink} to='/answering' variant='outlined'>
                Answering
              </Button>
            </Box>
          </DashboardTabPanel>
        </Paper>
      </Box>
    </AppLayout>
  );
}
