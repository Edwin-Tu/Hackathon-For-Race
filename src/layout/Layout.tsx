'use client';
import React, { useEffect, useState } from 'react';
import AppBar from './AppBar';
import Drawer from './Drawer';
import BottomNav from '../components/BottomNav';
import BottomNavSheet from '../components/BottomNavSheet';
import { Box, Snackbar, Alert, Fade, useMediaQuery } from '@mui/material';
import { useTheme } from '@mui/material/styles';
import { useRouter } from 'next/router';

const drawerWidth = 260;

// 檢查 Token 是否過期
function isTokenExpired(token: string | null): boolean {
  if (!token) return true;
  try {
    const tokenPart = token.split('.')[1];
    if (!tokenPart) return true;
    const payload = JSON.parse(atob(tokenPart));
    return payload.exp < Date.now();
  } catch {
    return true;
  }
}

export default function Layout({ children }: { children: React.ReactNode }) {
  const theme = useTheme();
  const router = useRouter();
  const isMobile = useMediaQuery(theme.breakpoints.down('md'));
  
  const [sessionExpired, setSessionExpired] = useState(false);
  const [mounted, setMounted] = useState(false);
  const [mobileOpen, setMobileOpen] = useState(false);
  const [moreSheetOpen, setMoreSheetOpen] = useState(false);

  // 檢查 Token 過期
  useEffect(() => {
    setMounted(true);
    
    // 登入頁面不需要檢查
    if (router.pathname === '/login') return;

    const checkSession = () => {
      const token = localStorage.getItem('auth');
      if (isTokenExpired(token)) {
        setSessionExpired(true);
        // 3 秒後自動重導
        setTimeout(() => {
          localStorage.removeItem('auth');
          document.cookie = 'auth=; path=/; expires=Thu, 01 Jan 1970 00:00:00 GMT';
          router.push('/login?expired=1');
        }, 3000);
      }
    };

    // 初次檢查
    checkSession();

    // 每分鐘檢查一次
    const interval = setInterval(checkSession, 60000);

    return () => clearInterval(interval);
  }, [router.pathname]);

  // 檢查 URL 參數顯示過期提示
  useEffect(() => {
    if (router.query.expired === '1') {
      setSessionExpired(true);
      // 清除 URL 參數
      router.replace('/login', undefined, { shallow: true });
    }
  }, [router.query]);

  // 處理行動版 Drawer 開關
  const handleDrawerToggle = () => {
    setMobileOpen(!mobileOpen);
  };

  // 登入頁面使用簡化 Layout
  if (router.pathname === '/login') {
    return (
      <Fade in={mounted} timeout={300}>
        <Box>
          {children}
          <Snackbar
            open={sessionExpired}
            autoHideDuration={5000}
            onClose={() => setSessionExpired(false)}
            anchorOrigin={{ vertical: 'top', horizontal: 'center' }}
            slots={{ transition: Fade }}
          >
            <Alert 
              severity="warning" 
              onClose={() => setSessionExpired(false)}
              variant="filled"
              sx={{ 
                width: '100%',
                boxShadow: '0 8px 24px rgba(0,0,0,0.15)',
              }}
            >
              登入已過期，請重新登入
            </Alert>
          </Snackbar>
        </Box>
      </Fade>
    );
  }

  return (
    <Box sx={{ display: 'flex', minHeight: '100vh' }}>
      <AppBar onMenuClick={handleDrawerToggle} />
      <Drawer 
        mobileOpen={mobileOpen} 
        onClose={() => setMobileOpen(false)} 
      />
      
      <Box 
        component="main" 
        sx={{ 
          flexGrow: 1, 
          p: { xs: 2, sm: 3 },
          pt: { xs: 2, sm: 3 },
          pb: { xs: 9, sm: 3 },  // 手機版增加底部空間給 BottomNav (56px + 16px)
          mt: 8,
          width: { 
            xs: '100%', 
            md: `calc(100% - ${drawerWidth}px)` 
          },
          transition: theme.transitions.create(['width', 'margin'], {
            easing: theme.transitions.easing.sharp,
            duration: theme.transitions.duration.leavingScreen,
          }),
          bgcolor: 'background.default',
          minHeight: 'calc(100vh - 64px)',
        }}
      >
        <Fade in={mounted} timeout={400}>
          <Box>
            {children}
          </Box>
        </Fade>
      </Box>

      {/* Session 過期提示 */}
      <Snackbar
        open={sessionExpired}
        autoHideDuration={5000}
        anchorOrigin={{ vertical: 'top', horizontal: 'center' }}
        slots={{ transition: Fade }}
      >
        <Alert 
          severity="warning"
          variant="filled"
          sx={{ 
            boxShadow: '0 8px 24px rgba(0,0,0,0.15)',
          }}
        >
          登入已過期，將自動重導至登入頁面...
        </Alert>
      </Snackbar>

      {/* 手機版底部導航 */}
      <BottomNav onMoreClick={() => setMoreSheetOpen(true)} />
      <BottomNavSheet 
        open={moreSheetOpen} 
        onClose={() => setMoreSheetOpen(false)} 
      />
    </Box>
  );
}
