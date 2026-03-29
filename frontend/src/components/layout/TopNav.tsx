import ScienceOutlinedIcon from '@mui/icons-material/ScienceOutlined';
import { AppBar, Box, Button, Toolbar, Typography } from '@mui/material';
import { Link as RouterLink, useLocation } from 'react-router-dom';

import { useAuth } from '../../hooks/useAuth';

export function TopNav() {
  const location = useLocation();
  const { isAuthenticated, logout } = useAuth();

  const publicActions = (
    <Box className='flex items-center gap-3'>
      <Button color='inherit' component={RouterLink} to='/#features'>
        Features
      </Button>
      <Button color='inherit' component={RouterLink} to='/login'>
        Login
      </Button>
      <Button variant='outlined' color='inherit' component={RouterLink} to='/register'>
        Register
      </Button>
    </Box>
  );

  const privateActions = (
    <Box className='flex items-center gap-2'>
      <Button color='inherit' component={RouterLink} to='/dashboard'>
        Dashboard
      </Button>
      <Button color='inherit' component={RouterLink} to='/orchestration'>
        Orchestration
      </Button>
      <Button color='inherit' component={RouterLink} to='/verification'>
        Verification
      </Button>
      <Button color='inherit' component={RouterLink} to='/answering'>
        Answering
      </Button>
      <Button variant='outlined' color='inherit' onClick={logout}>
        Logout
      </Button>
    </Box>
  );

  return (
    <AppBar position='sticky' elevation={0} className='!bg-slate-900/95'>
      <Toolbar className='mx-auto w-full max-w-7xl'>
        <Box component={RouterLink} to='/' className='flex items-center gap-2 no-underline text-white'>
          <ScienceOutlinedIcon />
          <Typography variant='h6' className='font-heading'>
            Pharma Intelligence
          </Typography>
        </Box>

        <Box className='ml-auto'>
          {isAuthenticated || location.pathname.startsWith('/dashboard') ? privateActions : publicActions}
        </Box>
      </Toolbar>
    </AppBar>
  );
}
