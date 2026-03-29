import React from 'react';
import ReactDOM from 'react-dom/client';
import { BrowserRouter } from 'react-router-dom';
import { CssBaseline, ThemeProvider, createTheme } from '@mui/material';

import App from './App';
import './styles.css';

const theme = createTheme({
  palette: {
    primary: { main: '#0e7490' },
    secondary: { main: '#2563eb' },
    background: { default: '#f8fafc' },
  },
  typography: {
    fontFamily: '"IBM Plex Sans", sans-serif',
    h1: { fontFamily: '"Space Grotesk", sans-serif' },
    h2: { fontFamily: '"Space Grotesk", sans-serif' },
    h3: { fontFamily: '"Space Grotesk", sans-serif' },
  },
});

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <ThemeProvider theme={theme}>
      <CssBaseline />
      <BrowserRouter>
        <App />
      </BrowserRouter>
    </ThemeProvider>
  </React.StrictMode>,
);
