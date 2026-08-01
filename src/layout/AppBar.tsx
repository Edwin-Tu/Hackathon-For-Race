'use client';
import React, { useState, useEffect } from 'react';
import {
  AppBar as MuiAppBar,
  Toolbar,
  Typography,
  IconButton,
  Box,
  Avatar,
  Menu,
  MenuItem,
  Divider,
  ListItemIcon,
  ListItemText,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Button,
  Chip,
  Tooltip,
  Fade,
  useMediaQuery,
} from '@mui/material';
import Brightness4Icon from '@mui/icons-material/Brightness4';
import Brightness7Icon from '@mui/icons-material/Brightness7';
import BrightnessAutoIcon from '@mui/icons-material/BrightnessAuto';
import ShieldIcon from '@mui/icons-material/Shield';
import PersonIcon from '@mui/icons-material/Person';
import LogoutIcon from '@mui/icons-material/Logout';
import SettingsIcon from '@mui/icons-material/Settings';
import MenuIcon from '@mui/icons-material/Menu';
import { useTheme, alpha } from '@mui/material/styles';
import { useRouter } from 'next/router';
import { useThemeMode } from '../context/ThemeContext';

// 角色配置
const roleConfig: Record<string, { label: string; color: 'error' | 'info' | 'success' | 'warning' }> = {
  ADMIN: { label: '系統管理者', color: 'error' },
  CAREGIVER: { label: '照護人員', color: 'info' },
  FAMILY: { label: '家屬', color: 'success' },
  RESIDENT: { label: '住民', color: 'warning' },
};

// 從 Token 解析使用者資訊
function parseUserFromToken(token: string | null) {
  if (!token) return null;
  try {
    const parts = token.split('.');
    const payloadPart = parts[1];
    if (!payloadPart) return null;
    const payload = JSON.parse(atob(payloadPart));
    return {
      sub: payload.sub,
      displayName: payload.displayName || payload.sub,
      role: payload.role?.toUpperCase() || 'CAREGIVER',
      exp: payload.exp,
    };
  } catch {
    return null;
  }
}

interface AppBarProps {
  onMenuClick?: () => void;
}

export default function AppBar({ onMenuClick }: AppBarProps) {
  const theme = useTheme();
  const router = useRouter();
  const isMobile = useMediaQuery(theme.breakpoints.down('md'));
  const { mode, toggleTheme } = useThemeMode();
  
  const [user, setUser] = useState<ReturnType<typeof parseUserFromToken>>(null);
  const [anchorEl, setAnchorEl] = useState<null | HTMLElement>(null);
  const [logoutDialogOpen, setLogoutDialogOpen] = useState(false);
  const [mounted, setMounted] = useState(false);

  // 讀取使用者資訊
  useEffect(() => {
    setMounted(true);
    const token = localStorage.getItem('auth');
    const parsedUser = parseUserFromToken(token);
    setUser(parsedUser);

    // 檢查 Token 是否過期
    if (parsedUser && parsedUser.exp && parsedUser.exp < Date.now()) {
      handleLogout(true);
    }
  }, []);

  // 取得主題圖示
  const getThemeIcon = () => {
    switch (mode) {
      case 'light':
        return <Brightness7Icon />;
      case 'dark':
        return <Brightness4Icon />;
      case 'system':
        return <BrightnessAutoIcon />;
    }
  };

  // 取得主題提示文字
  const getThemeTooltip = () => {
    switch (mode) {
      case 'light':
        return '淺色主題（點擊切換）';
      case 'dark':
        return '深色主題（點擊切換）';
      case 'system':
        return '跟隨系統（點擊切換）';
    }
  };

  // 開啟使用者選單
  const handleMenuOpen = (event: React.MouseEvent<HTMLElement>) => {
    setAnchorEl(event.currentTarget);
  };

  // 關閉選單
  const handleMenuClose = () => {
    setAnchorEl(null);
  };

  // 處理登出
  const handleLogout = (expired = false) => {
    localStorage.removeItem('auth');
    document.cookie = 'auth=; path=/; expires=Thu, 01 Jan 1970 00:00:00 GMT';
    
    if (expired) {
      router.push('/login?expired=1');
    } else {
      router.push('/login');
    }
  };

  // 確認登出
  const confirmLogout = () => {
    setLogoutDialogOpen(false);
    handleLogout();
  };

  // 登入頁面不顯示 AppBar 內容
  const isLoginPage = router.pathname === '/login';

  return (
    <>
      <MuiAppBar 
        position="fixed" 
        sx={{ 
          zIndex: (theme) => theme.zIndex.drawer + 1,
          backdropFilter: 'blur(8px)',
        }}
      >
        <Toolbar sx={{ gap: 1 }}>
          {/* 行動版選單按鈕 */}
          {isMobile && !isLoginPage && mounted && (
            <IconButton
              color="inherit"
              onClick={onMenuClick}
              edge="start"
              sx={{ mr: 1 }}
            >
              <MenuIcon />
            </IconButton>
          )}

          {/* Logo */}
          <Box 
            sx={{ 
              display: 'flex', 
              alignItems: 'center', 
              gap: 1.5,
              cursor: 'pointer',
              transition: 'transform 0.2s ease',
              '&:hover': {
                transform: 'scale(1.02)',
              },
            }}
            onClick={() => router.push('/')}
          >
            <Avatar 
              sx={{ 
                bgcolor: alpha(theme.palette.common.white, 0.15),
                backdropFilter: 'blur(4px)',
                width: 40, 
                height: 40,
                boxShadow: '0 2px 8px rgba(0,0,0,0.15)',
              }}
            >
              <ShieldIcon sx={{ fontSize: 24 }} />
            </Avatar>
            <Box>
              <Typography 
                variant="h6" 
                component="div" 
                sx={{ 
                  fontWeight: 700,
                  letterSpacing: '0.02em',
                  lineHeight: 1.2,
                }}
              >
                智護聲盾
              </Typography>
              {!isMobile && (
                <Typography 
                  variant="caption" 
                  sx={{ 
                    opacity: 0.85,
                    letterSpacing: '0.05em',
                  }}
                >
                  SecretGuard
                </Typography>
              )}
            </Box>
          </Box>

          <Box sx={{ flexGrow: 1 }} />

          {/* 右側功能區 */}
          <Fade in={mounted}>
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
              {/* 使用者角色標籤 - 非登入頁面才顯示 */}
              {!isLoginPage && user && !isMobile && (
                <Chip
                  size="small"
                  label={roleConfig[user.role]?.label || user.role}
                  color={roleConfig[user.role]?.color || 'default'}
                  sx={{ 
                    mr: 1,
                    fontWeight: 600,
                    backdropFilter: 'blur(4px)',
                  }}
                />
              )}

              {/* 主題切換 */}
              <Tooltip title={getThemeTooltip()} arrow>
                <IconButton 
                  color="inherit" 
                  onClick={toggleTheme}
                  sx={{
                    bgcolor: alpha(theme.palette.common.white, 0.1),
                    '&:hover': {
                      bgcolor: alpha(theme.palette.common.white, 0.2),
                    },
                  }}
                >
                  {getThemeIcon()}
                </IconButton>
              </Tooltip>

              {/* 使用者頭像與選單 - 非登入頁面才顯示 */}
              {!isLoginPage && user && (
                <Tooltip title={user.displayName} arrow>
                  <IconButton
                    onClick={handleMenuOpen}
                    sx={{ 
                      p: 0.5, 
                      ml: 0.5,
                      border: `2px solid ${alpha(theme.palette.common.white, 0.3)}`,
                      transition: 'all 0.2s ease',
                      '&:hover': {
                        borderColor: alpha(theme.palette.common.white, 0.6),
                      },
                    }}
                  >
                    <Avatar 
                      sx={{ 
                        width: 36, 
                        height: 36, 
                        bgcolor: theme.palette.secondary.main,
                        fontWeight: 600,
                      }}
                    >
                      {user.displayName?.[0] || <PersonIcon />}
                    </Avatar>
                  </IconButton>
                </Tooltip>
              )}
            </Box>
          </Fade>
        </Toolbar>
      </MuiAppBar>

      {/* 使用者選單 */}
      <Menu
        anchorEl={anchorEl}
        open={Boolean(anchorEl)}
        onClose={handleMenuClose}
        transformOrigin={{ horizontal: 'right', vertical: 'top' }}
        anchorOrigin={{ horizontal: 'right', vertical: 'bottom' }}
        slotProps={{
          paper: {
            sx: { 
              width: 240, 
              mt: 1.5,
              overflow: 'visible',
              '&:before': {
                content: '""',
                display: 'block',
                position: 'absolute',
                top: 0,
                right: 18,
                width: 12,
                height: 12,
                bgcolor: 'background.paper',
                transform: 'translateY(-50%) rotate(45deg)',
                zIndex: 0,
                boxShadow: '-2px -2px 4px rgba(0,0,0,0.05)',
              },
            },
          },
        }}
      >
        {/* 使用者資訊 */}
        <Box sx={{ px: 2.5, py: 2 }}>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1.5, mb: 1 }}>
            <Avatar sx={{ bgcolor: 'primary.main', width: 44, height: 44 }}>
              {user?.displayName?.[0]}
            </Avatar>
            <Box>
              <Typography variant="subtitle1" sx={{ fontWeight: 600 }}>
                {user?.displayName}
              </Typography>
              <Typography variant="caption" color="text.secondary">
                {user?.sub}
              </Typography>
            </Box>
          </Box>
          {user && (
            <Chip
              size="small"
              label={roleConfig[user.role]?.label || user.role}
              color={roleConfig[user.role]?.color || 'default'}
              sx={{ mt: 0.5 }}
            />
          )}
        </Box>
        <Divider />

        {/* 設定選項 */}
        <MenuItem 
          onClick={handleMenuClose}
          sx={{ py: 1.5, px: 2.5 }}
        >
          <ListItemIcon>
            <SettingsIcon fontSize="small" />
          </ListItemIcon>
          <ListItemText 
            primary="設定" 
            primaryTypographyProps={{ fontWeight: 500 }}
          />
        </MenuItem>

        <Divider />

        {/* 登出 */}
        <MenuItem
          onClick={() => {
            handleMenuClose();
            setLogoutDialogOpen(true);
          }}
          sx={{ 
            py: 1.5, 
            px: 2.5,
            color: 'error.main',
            '&:hover': {
              bgcolor: alpha(theme.palette.error.main, 0.08),
            },
          }}
        >
          <ListItemIcon>
            <LogoutIcon fontSize="small" color="error" />
          </ListItemIcon>
          <ListItemText 
            primary="登出" 
            primaryTypographyProps={{ fontWeight: 500 }}
          />
        </MenuItem>
      </Menu>

      {/* 登出確認對話框 */}
      <Dialog 
        open={logoutDialogOpen} 
        onClose={() => setLogoutDialogOpen(false)}
        PaperProps={{
          sx: { minWidth: 340 }
        }}
      >
        <DialogTitle sx={{ pb: 1 }}>確認登出</DialogTitle>
        <DialogContent>
          <Typography color="text.secondary">
            確定要登出系統嗎？您的工作階段將會結束。
          </Typography>
        </DialogContent>
        <DialogActions sx={{ px: 3, pb: 2.5 }}>
          <Button 
            onClick={() => setLogoutDialogOpen(false)}
            sx={{ minWidth: 80 }}
          >
            取消
          </Button>
          <Button 
            variant="contained" 
            color="error" 
            onClick={confirmLogout}
            sx={{ minWidth: 80 }}
          >
            登出
          </Button>
        </DialogActions>
      </Dialog>
    </>
  );
}
