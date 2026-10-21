'use client';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { CssBaseline, ThemeProvider, createTheme } from '@mui/material';
import { useState, type ReactNode } from 'react';
import { Toaster } from 'react-hot-toast';

const theme = createTheme({
  palette: {
    primary: { main: '#126b55' },
    secondary: { main: '#e96b3d' },
    background: { default: '#f3f5f0' },
    text: { primary: '#17202f', secondary: '#68717d' },
  },
  typography: {
    fontFamily: 'var(--font-manrope), sans-serif',
    h3: { fontWeight: 800, letterSpacing: '-.035em' },
    h5: { fontWeight: 800 },
    button: { textTransform: 'none', fontWeight: 700 },
  },
  shape: { borderRadius: 14 },
});
export default function Providers({ children }: { children: ReactNode }) {
  //================================>
  // Stable query client for the browser session
  //================================>
  const [client] = useState(
    () => new QueryClient({ defaultOptions: { queries: { retry: 1, staleTime: 10000 } } }),
  );
  return (
    <QueryClientProvider client={client}>
      <ThemeProvider theme={theme}>
        <CssBaseline />
        {children}
        <Toaster position="top-right" />
      </ThemeProvider>
    </QueryClientProvider>
  );
}
