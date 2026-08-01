import * as React from 'react';
import type { AppProps } from 'next/app';
import { Provider } from 'react-redux';
import { store } from '../store';
import { ThemeProvider, createTheme, CssBaseline } from '@mui/material';
import Layout from '../layout/Layout';

const lightTheme = createTheme({
  palette: { mode: 'light' },
});
const darkTheme = createTheme({
  palette: { mode: 'dark' },
});

export default function MyApp({ Component, pageProps }: AppProps) {
  const [mode, setMode] = React.useState<'light' | 'dark'>('light');
  const theme = React.useMemo(() => (mode === 'light' ? lightTheme : darkTheme), [mode]);

  return (
    <Provider store={store}>
      <ThemeProvider theme={theme}>
        <CssBaseline />
        {/* 包裹全局 Layout */}
        <Layout>
          <Component {...pageProps} />
        </Layout>
      </ThemeProvider>
    </Provider>
  );
}
