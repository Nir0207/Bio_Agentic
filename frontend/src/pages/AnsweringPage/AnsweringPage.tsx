import { useState } from 'react';
import { Box, Button, FormControl, Grid, InputLabel, MenuItem, Paper, Select, Typography } from '@mui/material';

import { AppLayout } from '../../components/layout/AppLayout';
import { EmptyState } from '../../components/common/EmptyState';
import { PageHeader } from '../../components/common/PageHeader';
import { StreamConsole } from '../../components/streaming/StreamConsole';
import { StreamStatusBar } from '../../components/streaming/StreamStatusBar';
import { useStreaming } from '../../hooks/useStreaming';
import { AnswerPanel } from '../../modules/answering/components/AnswerPanel';
import { answeringService } from '../../services/answering.service';
import type { AnsweringPayload } from '../../types/answering';
import { useAppStore } from '../../store/appStore';

export function AnsweringPage() {
  const verificationPayload = useAppStore((state) => state.latestVerification);
  const payload = useAppStore((state) => state.latestAnswering);
  const setPayload = useAppStore((state) => state.setLatestAnswering);
  const showSnackbar = useAppStore((state) => state.showSnackbar);
  const [style, setStyle] = useState('concise');

  const stream = useStreaming<AnsweringPayload>();

  const run = async () => {
    try {
      const response = await answeringService.run({ verified_payload: verificationPayload || undefined, style });
      setPayload(response.payload);
      showSnackbar('Answer generated.', 'success');
    } catch (error) {
      showSnackbar(error instanceof Error ? error.message : 'Answer generation failed.', 'error');
    }
  };

  const runStream = async () => {
    await stream.run(async (onEvent) => {
      await answeringService.streamRun({ verified_payload: verificationPayload || undefined, style }, (event) => {
        onEvent(event);
        if (event.event === 'payload') {
          setPayload(event.data as AnsweringPayload);
        }
      });
    });
  };

  const currentPayload = stream.payload || payload;

  return (
    <AppLayout withSidebar>
      <PageHeader
        title='Answering'
        subtitle='Generate final explainable answers with confidence and citation traces.'
        rightSlot={
          <FormControl size='small' className='min-w-[180px]'>
            <InputLabel id='answer-style'>Answer Style</InputLabel>
            <Select
              labelId='answer-style'
              value={style}
              label='Answer Style'
              onChange={(event) => setStyle(event.target.value)}
            >
              <MenuItem value='concise'>Concise</MenuItem>
              <MenuItem value='detailed'>Detailed</MenuItem>
              <MenuItem value='technical'>Technical</MenuItem>
            </Select>
          </FormControl>
        }
      />

      <Box className='mb-3 flex gap-2'>
        <Button variant='contained' onClick={run} disabled={stream.status === 'running'}>
          Run
        </Button>
        <Button variant='outlined' onClick={runStream} disabled={stream.status === 'running'}>
          Stream
        </Button>
      </Box>

      <Grid container spacing={2}>
        <Grid size={{ xs: 12, lg: 8 }}>
          <Paper className='rounded-xl border border-slate-200 p-4'>
            <Typography variant='h6' className='mb-2 font-heading'>
              Final Answer
            </Typography>
            {currentPayload ? (
              <AnswerPanel payload={currentPayload} />
            ) : (
              <EmptyState title='No answer yet' description='Run answer generation to view final output.' />
            )}
          </Paper>
        </Grid>

        <Grid size={{ xs: 12, lg: 4 }}>
          <Paper className='rounded-xl border border-slate-200 p-4'>
            <Typography variant='h6' className='font-heading'>
              Confidence + Verdict
            </Typography>
            <Typography variant='body2'>
              {currentPayload
                ? `${currentPayload.verdict} (${Math.round(currentPayload.confidence * 100)}%)`
                : 'No result yet.'}
            </Typography>
          </Paper>

          <Paper className='mt-2 rounded-xl border border-slate-200 p-4'>
            <Typography variant='h6' className='font-heading'>
              Source Payload Info
            </Typography>
            <Typography variant='body2'>
              Uses verification payload from backend integration APIs.
            </Typography>
          </Paper>
        </Grid>

        <Grid size={{ xs: 12 }}>
          <StreamStatusBar status={stream.status} error={stream.error} />
          <Box className='mt-2'>
            <StreamConsole events={stream.events} />
          </Box>
        </Grid>

        <Grid size={{ xs: 12, md: 6 }}>
          <Paper className='rounded-xl border border-slate-200 p-4'>
            <Typography variant='h6' className='font-heading'>
              Citations
            </Typography>
            {currentPayload?.citations?.length ? (
              currentPayload.citations.map((citation, index) => (
                <Typography key={`${citation}-${index}`} variant='body2'>
                  - {citation}
                </Typography>
              ))
            ) : (
              <Typography variant='body2' color='text.secondary'>
                No citations available yet.
              </Typography>
            )}
          </Paper>
        </Grid>

        <Grid size={{ xs: 12, md: 6 }}>
          <Paper className='rounded-xl border border-slate-200 p-4'>
            <Typography variant='h6' className='font-heading'>
              Evidence Appendix
            </Typography>
            {currentPayload?.evidence_appendix?.length ? (
              currentPayload.evidence_appendix.map((line, index) => (
                <Typography key={`${line}-${index}`} variant='body2'>
                  - {line}
                </Typography>
              ))
            ) : (
              <Typography variant='body2' color='text.secondary'>
                Evidence appendix appears after generation.
              </Typography>
            )}
          </Paper>
        </Grid>
      </Grid>
    </AppLayout>
  );
}
