import { Box, Button, TextField } from '@mui/material';

interface QueryInputPanelProps {
  query: string;
  setQuery: (value: string) => void;
  onRun: () => void;
  onStream: () => void;
  busy: boolean;
}

export function QueryInputPanel({ query, setQuery, onRun, onStream, busy }: QueryInputPanelProps) {
  return (
    <Box className='flex flex-col gap-3'>
      <TextField
        label='Research Query'
        value={query}
        onChange={(event) => setQuery(event.target.value)}
        multiline
        minRows={4}
        placeholder='Ask a mechanistic or evidence-backed pharma query...'
      />
      <Box className='flex flex-wrap gap-2'>
        <Button variant='contained' disabled={busy} onClick={onRun}>
          Run
        </Button>
        <Button variant='outlined' disabled={busy} onClick={onStream}>
          Stream
        </Button>
      </Box>
    </Box>
  );
}
