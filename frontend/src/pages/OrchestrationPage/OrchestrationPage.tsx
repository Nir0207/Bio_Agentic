import { useState } from 'react';
import { Box, Grid, List, ListItem, ListItemText, Paper, Typography } from '@mui/material';

import { AppLayout } from '../../components/layout/AppLayout';
import { EmptyState } from '../../components/common/EmptyState';
import { PageHeader } from '../../components/common/PageHeader';
import { SectionCard } from '../../components/common/SectionCard';
import { StreamConsole } from '../../components/streaming/StreamConsole';
import { StreamStatusBar } from '../../components/streaming/StreamStatusBar';
import { useStreaming } from '../../hooks/useStreaming';
import { QueryInputPanel } from '../../modules/orchestration/components/QueryInputPanel';
import { orchestrationService } from '../../services/orchestration.service';
import type { OrchestrationPayload } from '../../types/orchestration';
import { useAppStore } from '../../store/appStore';

export function OrchestrationPage() {
  const [query, setQuery] = useState('Map evidence for KRAS inhibitor efficacy by mutation context.');
  const latestPayload = useAppStore((state) => state.latestOrchestration);
  const setLatestPayload = useAppStore((state) => state.setLatestOrchestration);
  const setSelectedQuery = useAppStore((state) => state.setSelectedQuery);
  const showSnackbar = useAppStore((state) => state.showSnackbar);

  const stream = useStreaming<OrchestrationPayload>();

  const run = async () => {
    try {
      const response = await orchestrationService.run({ query });
      setLatestPayload(response.payload);
      setSelectedQuery(query);
      showSnackbar('Orchestration run completed.', 'success');
    } catch (error) {
      showSnackbar(error instanceof Error ? error.message : 'Orchestration run failed.', 'error');
    }
  };

  const runStream = async () => {
    await stream.run(async (onEvent) => {
      await orchestrationService.streamRun({ query }, (event) => {
        onEvent(event);
        if (event.event === 'payload') {
          setLatestPayload(event.data as OrchestrationPayload);
          setSelectedQuery(query);
        }
      });
    });
  };

  const payload = stream.payload || latestPayload;

  return (
    <AppLayout withSidebar>
      <PageHeader
        title='Orchestration'
        subtitle='Retrieve graph and semantic evidence bundles with streaming intermediate states.'
      />

      <Grid container spacing={2}>
        <Grid size={{ xs: 12, lg: 8 }}>
          <SectionCard title='Query Input' subtitle='Submit query and trigger run or stream'>
            <QueryInputPanel
              query={query}
              setQuery={setQuery}
              onRun={run}
              onStream={runStream}
              busy={stream.status === 'running'}
            />
          </SectionCard>

          <Box className='mt-2'>
            <StreamStatusBar status={stream.status} error={stream.error} />
          </Box>

          <Box className='mt-2'>
            <StreamConsole events={stream.events} />
          </Box>

          <Box className='mt-2'>
            <SectionCard title='Candidate Entities'>
              {payload?.candidates?.length ? (
                <List dense>
                  {payload.candidates.map((candidate) => (
                    <ListItem key={candidate.entity_id} divider>
                      <ListItemText
                        primary={`${candidate.name} (${candidate.source})`}
                        secondary={candidate.relationship_hint || 'No relationship hint'}
                      />
                    </ListItem>
                  ))}
                </List>
              ) : (
                <EmptyState title='No candidates yet' description='Run orchestration to inspect candidate entities.' />
              )}
            </SectionCard>
          </Box>
        </Grid>

        <Grid size={{ xs: 12, lg: 4 }}>
          <Paper className='space-y-3 rounded-xl border border-slate-200 p-4'>
            <Typography variant='h6' className='font-heading'>
              Evidence Bundle Preview
            </Typography>
            {payload?.evidence_bundle?.length ? (
              <List dense>
                {payload.evidence_bundle.slice(0, 4).map((evidence, index) => (
                  <ListItem key={index} divider>
                    <ListItemText primary={String(evidence.summary || 'Evidence row')} secondary={String(evidence.source || '')} />
                  </ListItem>
                ))}
              </List>
            ) : (
              <Typography variant='body2' color='text.secondary'>
                Evidence bundle appears after run.
              </Typography>
            )}
          </Paper>

          <Paper className='mt-2 rounded-xl border border-slate-200 p-4'>
            <Typography variant='h6' className='font-heading'>
              Metadata / Status
            </Typography>
            <pre className='mt-2 whitespace-pre-wrap text-xs'>
              {payload?.metadata ? JSON.stringify(payload.metadata, null, 2) : 'No metadata yet.'}
            </pre>
          </Paper>

          <Paper className='mt-2 rounded-xl border border-amber-200 bg-amber-50 p-4'>
            <Typography variant='h6' className='font-heading'>
              Warnings / Notes
            </Typography>
            <Typography variant='body2'>Streaming run disables repeated submissions while active.</Typography>
          </Paper>
        </Grid>
      </Grid>
    </AppLayout>
  );
}
