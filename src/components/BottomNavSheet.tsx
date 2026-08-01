// src/components/BottomNavSheet.tsx
'use client';
import React, { useState, useEffect } from 'react';
import {
  Drawer,
  List,
  ListItemButton,
  ListItemIcon,
  ListItemText,
  Typography,
  Box,
  Divider,
} from '@mui/material';
import { useTheme, alpha } from '@mui/material/styles';
import { useRouter } from 'next/router';
import { getUserRole } from '../utils/auth';
import { bottomNavRoutes, BottomNavItem } from './BottomNav';

interface BottomNavSheetProps {
  open: boolean;
  onClose: () => void;
}

export default function BottomNavSheet({ open, onClose }: BottomNavSheetProps) {
  const theme = useTheme();
  const router = useRouter();
  const [role, setRole] = useState<string | null>(null);

  useEffect(() => {
    const token = localStorage.getItem('auth');
    const userRole = getUserRole(token);
    setRole(userRole);
  }, []);

  if (!role) return null;

  const config = bottomNavRoutes[role];
  const moreItems = config?.moreItems || [];

  const handleItemClick = (item: BottomNavItem) => {
    router.push(item.href);
    onClose();
  };

  return (
    <Drawer
      anchor="bottom"
      open={open}
      onClose={onClose}
      PaperProps={{
        sx: {
          borderTopLeftRadius: 16,
          borderTopRightRadius: 16,
          maxHeight: '60vh',
        },
      }}
    >
      {/* 拖曳指示條 */}
      <Box sx={{ display: 'flex', justifyContent: 'center', py: 1.5 }}>
        <Box
          sx={{
            width: 40,
            height: 4,
            borderRadius: 2,
            bgcolor: alpha(theme.palette.text.primary, 0.2),
          }}
        />
      </Box>

      {/* 標題 */}
      <Box sx={{ px: 2, pb: 1 }}>
        <Typography variant="subtitle1" fontWeight={600}>
          更多功能
        </Typography>
      </Box>

      <Divider />

      {/* 選單項目 */}
      <List sx={{ px: 1, py: 1 }}>
        {moreItems.map((item) => {
          const isActive = router.pathname === item.href;
          return (
            <ListItemButton
              key={item.key}
              onClick={() => handleItemClick(item)}
              sx={{
                borderRadius: 2,
                mb: 0.5,
                minHeight: 48,
                '&:hover': {
                  bgcolor: alpha(theme.palette.primary.main, 0.08),
                },
                ...(isActive && {
                  bgcolor: alpha(theme.palette.primary.main, 0.12),
                }),
              }}
            >
              <ListItemIcon
                sx={{
                  minWidth: 40,
                  color: isActive ? 'primary.main' : 'text.secondary',
                }}
              >
                {item.icon}
              </ListItemIcon>
              <ListItemText
                primary={item.label}
                primaryTypographyProps={{
                  fontWeight: isActive ? 600 : 400,
                  color: isActive ? 'primary.main' : 'text.primary',
                }}
              />
            </ListItemButton>
          );
        })}
      </List>

      {/* 底部安全區域 */}
      <Box sx={{ height: 'env(safe-area-inset-bottom, 0px)' }} />
    </Drawer>
  );
}
