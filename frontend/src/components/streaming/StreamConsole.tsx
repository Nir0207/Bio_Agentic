import { Box, Chip, Divider, Typography } from '@mui/material';

import type { StreamEvent } from '../../types/api';

interface StreamConsoleProps {
  events: StreamEvent[];
}

export function StreamConsole({ events }: StreamConsoleProps) {
  return (
    <Box className='rounded-xl border border-slate-200 bg-slate-950/95 p-3 text-slate-50'>
      <Typography variant='subtitle2' className='mb-3 font-heading text-cyan-200'>
        Stream Console
      </Typography>
      <Box className='max-h-72 overflow-auto rounded-lg bg-slate-900 p-3'>
        {events.length === 0 ? (
          <Typography variant='body2' className='text-slate-300'>
            No streaming events yet.
          </Typography>
        ) : (
          events.map((event, index) => (
            <Box key={`${event.event}-${index}`} className='mb-2'>
              <Box className='mb-1 flex items-center gap-2'>
                <Chip size='small' label={event.event} color='primary' />
                <Typography variant='caption' className='text-slate-400'>
                  #{index + 1}
                </Typography>
              </Box>
              <pre className='whitespace-pre-wrap text-xs text-slate-100'>
                {JSON.stringify(event.data, null, 2)}
              </pre>
              {index < events.length - 1 ? <Divider className='!my-2 !border-slate-700' /> : null}
            </Box>
          ))
        )}
      </Box>
    </Box>
  );
}
