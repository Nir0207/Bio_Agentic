import { Box, Typography } from '@mui/material';

export function TestUserHint() {
  return (
    <Box className='rounded-lg border border-sky-100 bg-sky-50 p-3'>
      <Typography variant='subtitle2'>Default Test User</Typography>
      <Typography variant='body2'>Email: admin@pharma.ai</Typography>
      <Typography variant='body2'>Password: admin123</Typography>
    </Box>
  );
}
