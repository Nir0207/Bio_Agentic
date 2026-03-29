import { Grid, Paper, Typography } from '@mui/material';

const cards = [
  { title: 'Orchestration', detail: 'Graph and semantic retrieval flow.' },
  { title: 'Verification', detail: 'Claim-level evidence checks.' },
  { title: 'Answering', detail: 'Explainable response generation.' },
  { title: 'Auth/User', detail: 'JWT security and identity controls.' },
];

export function CapabilityCards() {
  return (
    <Grid container spacing={2}>
      {cards.map((card) => (
        <Grid key={card.title} size={{ xs: 12, sm: 6, lg: 3 }}>
          <Paper className='h-full rounded-xl border border-slate-200 p-4'>
            <Typography variant='h6' className='font-heading'>
              {card.title}
            </Typography>
            <Typography color='text.secondary' variant='body2'>
              {card.detail}
            </Typography>
          </Paper>
        </Grid>
      ))}
    </Grid>
  );
}
