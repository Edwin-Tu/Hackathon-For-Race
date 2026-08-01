import * as React from 'react';
import type { AppProps } from 'next/app';
import Head from 'next/head';
import { Provider } from 'react-redux';
import { store } from '../store';
import { CssBaseline } from '@mui/material';
import { ThemeContextProvider } from '../context/ThemeContext';
import Layout from '../layout/Layout';

export default function MyApp({ Component, pageProps }: AppProps) {
  return (
    <>
      <Head>
        <meta name="viewport" content="width=device-width, initial-scale=1" />
        <link
          href="https://fonts.googleapis.com/css2?family=Noto+Sans+TC:wght@400;500;600;700&family=Roboto:wght@400;500;600;700&display=swap"
          rel="stylesheet"
        />
        <title>智護聲盾 - Smart Care Voice Agent</title>
      </Head>
      <Provider store={store}>
        <ThemeContextProvider>
          <CssBaseline />
          <Layout>
            <Component {...pageProps} />
          </Layout>
        </ThemeContextProvider>
      </Provider>
    </>
  );
}
