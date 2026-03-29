import { Box, Chip, Typography } from '@mui/material';

import type { AnsweringPayload } from '../../../types/answering';
import { pct, titleCase } from '../../../utils/format';

interface AnswerPanelProps {
  payload: AnsweringPayload;
}

export function AnswerPanel({ payload }: AnswerPanelProps) {
  return (
    <Box className='space-y-4'>
      <Typography variant='body1'>{payload.answer_text}</Typography>
      <Box className='flex flex-wrap gap-2'>
        <Chip label={`Verdict: ${titleCase(payload.verdict)}`} color='primary' />
        <Chip label={`Confidence: ${pct(payload.confidence)}`} color='secondary' />
        <Chip label={`Style: ${titleCase(payload.style)}`} variant='outlined' />
      </Box>
    </Box>
  );
}
