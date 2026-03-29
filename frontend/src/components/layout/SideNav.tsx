import DashboardIcon from '@mui/icons-material/Dashboard';
import LightbulbIcon from '@mui/icons-material/Lightbulb';
import SafetyCheckIcon from '@mui/icons-material/SafetyCheck';
import SettingsSuggestIcon from '@mui/icons-material/SettingsSuggest';
import { Box, List, ListItemButton, ListItemIcon, ListItemText, Paper } from '@mui/material';
import { Link as RouterLink, useLocation } from 'react-router-dom';

const navItems = [
  { icon: <DashboardIcon />, label: 'Dashboard', path: '/dashboard' },
  { icon: <SettingsSuggestIcon />, label: 'Orchestration', path: '/orchestration' },
  { icon: <SafetyCheckIcon />, label: 'Verification', path: '/verification' },
  { icon: <LightbulbIcon />, label: 'Answering', path: '/answering' },
];

export function SideNav() {
  const location = useLocation();

  return (
    <Paper className='hidden md:block md:w-64 md:self-start md:sticky md:top-24'>
      <Box className='p-2'>
        <List>
          {navItems.map((item) => (
            <ListItemButton
              key={item.path}
              component={RouterLink}
              to={item.path}
              selected={location.pathname === item.path}
              className='rounded-lg'
            >
              <ListItemIcon>{item.icon}</ListItemIcon>
              <ListItemText primary={item.label} />
            </ListItemButton>
          ))}
        </List>
      </Box>
    </Paper>
  );
}
