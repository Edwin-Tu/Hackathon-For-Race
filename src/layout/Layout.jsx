import React from 'react';
import AppBar from './AppBar';
import Drawer from './Drawer';
import { Box } from '@mui/material';

export default function Layout({ children }) {
  return (
    <Box sx={{ display: 'flex' }}>
      <AppBar />
      <Drawer />
      <Box component="main" sx={{ flexGrow: 1, p: 3, mt: 8 }}>
        {children}
      </Box>
    </Box>
  );
}
