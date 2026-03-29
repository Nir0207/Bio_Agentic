import { Box, Container } from '@mui/material';
import type { ReactNode } from 'react';

import { SideNav } from './SideNav';
import { TopNav } from './TopNav';

interface AppLayoutProps {
  children: ReactNode;
  withSidebar?: boolean;
}

export function AppLayout({ children, withSidebar = false }: AppLayoutProps) {
  return (
    <Box className='min-h-screen'>
      <TopNav />
      <Container maxWidth='xl' className='py-6'>
        <Box className='flex gap-6'>
          {withSidebar ? <SideNav /> : null}
          <Box className='flex-1'>{children}</Box>
        </Box>
      </Container>
    </Box>
  );
}
