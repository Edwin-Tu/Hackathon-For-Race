import React from 'react';
import { AppBar as MuiAppBar, Toolbar, Typography, IconButton } from '@mui/material';
import Brightness4Icon from '@mui/icons-material/Brightness4';
import Brightness7Icon from '@mui/icons-material/Brightness7';
import { useTheme } from '@mui/material/styles';

export default function AppBar() {
  const theme = useTheme();
  const [mode, setMode] = React.useState(theme.palette.mode);
  const toggle = () => {
    const next = mode === 'light' ? 'dark' : 'light';
    setMode(next);
    // 在真實 app 中應該把 mode 存到 context 或 localStorage
  };

  return (
    <MuiAppBar position="fixed" sx={{ zIndex: (theme) => theme.zIndex.drawer + 1 }}>
      <Toolbar>
        <Typography variant="h6" component="div" sx={{ flexGrow: 1 }}>
          智護聲盾管理介面
        </Typography>
        <IconButton color="inherit" onClick={toggle}>
          {mode === 'light' ? <Brightness4Icon /> : <Brightness7Icon />}
        </IconButton>
      </Toolbar>
    </MuiAppBar>
  );
}
