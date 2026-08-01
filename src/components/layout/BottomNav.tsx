// src/components/BottomNav.tsx
'use client';
import React, { useState, useEffect } from 'react';
import {
  BottomNavigation,
  BottomNavigationAction,
  Paper,
  Badge,
  useMediaQuery,
} from '@mui/material';
import { useTheme } from '@mui/material/styles';
import { useRouter } from 'next/router';
import { getUserRole } from '../utils/auth';

// 圖示
import PeopleIcon from '@mui/icons-material/People';
import SummarizeIcon from '@mui/icons-material/Summarize';
import NotificationsActiveIcon from '@mui/icons-material/NotificationsActive';
import MoreHorizIcon from '@mui/icons-material/MoreHoriz';
import DashboardIcon from '@mui/icons-material/Dashboard';
import NotificationsIcon from '@mui/icons-material/Notifications';
import GroupIcon from '@mui/icons-material/Group';
import AdminPanelSettingsIcon from '@mui/icons-material/AdminPanelSettings';
import SecurityIcon from '@mui/icons-material/Security';
import RecordVoiceOverIcon from '@mui/icons-material/RecordVoiceOver';
import VideocamIcon from '@mui/icons-material/Videocam';

// 底部導航項目介面
interface BottomNavItem {
  key: string;
  label: string;
  icon: React.ReactNode;
  href: string;
  badge?: number;
}

// 各角色的底部導航配置
const bottomNavRoutes: Record<string, { items: BottomNavItem[]; moreItems?: BottomNavItem[] }> = {
  RESIDENT: {
    items: [
      { key: 'voice', label: '語音互動', icon: <RecordVoiceOverIcon />, href: '/resident/voice' },
    ],
  },
  CAREGIVER: {
    items: [
      { key: 'residents', label: '住民列表', icon: <PeopleIcon />, href: '/caregiver' },
      { key: 'summary', label: '每日摘要', icon: <SummarizeIcon />, href: '/caregiver/summary' },
      { key: 'reminders', label: '提醒', icon: <NotificationsActiveIcon />, href: '/caregiver/reminders', badge: 5 },
      { key: 'more', label: '更多', icon: <MoreHorizIcon />, href: '' },
    ],
    moreItems: [
      { key: 'alerts', label: '高風險警示', icon: <NotificationsActiveIcon />, href: '/caregiver/alerts' },
      { key: 'timeline', label: '事件時間軸', icon: <SummarizeIcon />, href: '/caregiver/timeline' },
      { key: 'memory', label: '記憶修正', icon: <SummarizeIcon />, href: '/caregiver/memory' },
    ],
  },
  FAMILY: {
    items: [
      { key: 'dashboard', label: '概況', icon: <DashboardIcon />, href: '/family/Dashboard' },
      { key: 'notifications', label: '通知', icon: <NotificationsIcon />, href: '/family/Notifications', badge: 3 },
      { key: 'video', label: '動圖', icon: <VideocamIcon />, href: '/family/VideoUpload' },
      { key: 'authorizations', label: '授權', icon: <GroupIcon />, href: '/family/Authorizations' },
    ],
  },
  ADMIN: {
    items: [
      { key: 'users', label: '用戶', icon: <PeopleIcon />, href: '/admin/Users' },
      { key: 'roles', label: '角色', icon: <AdminPanelSettingsIcon />, href: '/admin/Roles' },
      { key: 'audit', label: '稽核', icon: <SecurityIcon />, href: '/admin/AuditLog' },
      { key: 'more', label: '更多', icon: <MoreHorizIcon />, href: '' },
    ],
    moreItems: [
      { key: 'assets', label: '資產設定', icon: <AdminPanelSettingsIcon />, href: '/admin/Assets' },
      { key: 'policy', label: '政策編輯', icon: <AdminPanelSettingsIcon />, href: '/admin/PolicyEditor' },
      { key: 'security', label: '安全風險', icon: <SecurityIcon />, href: '/admin/Security' },
      { key: 'benchmark', label: '測試報告', icon: <SecurityIcon />, href: '/admin/Benchmark' },
    ],
  },
};

interface BottomNavProps {
  onMoreClick?: () => void;
}

export default function BottomNav({ onMoreClick }: BottomNavProps) {
  const theme = useTheme();
  const router = useRouter();
  const isMobile = useMediaQuery(theme.breakpoints.down('sm'));
  
  const [role, setRole] = useState<string | null>(null);
  const [mounted, setMounted] = useState(false);

  useEffect(() => {
    setMounted(true);
    const token = localStorage.getItem('auth');
    const userRole = getUserRole(token);
    setRole(userRole);
  }, []);

  // 登入頁面或非手機版不顯示
  if (router.pathname === '/login' || !isMobile || !mounted || !role) {
    return null;
  }

  const config = bottomNavRoutes[role];
  if (!config) return null;

  // 找出當前選中的導航項目
  const currentValue = config.items.findIndex(
    (item) => item.href && router.pathname.startsWith(item.href)
  );

  const handleChange = (_event: React.SyntheticEvent, newValue: number) => {
    const item = config.items[newValue];
    if (!item) return;
    if (item.key === 'more') {
      onMoreClick?.();
    } else if (item.href) {
      router.push(item.href);
    }
  };

  return (
    <Paper
      sx={{
        position: 'fixed',
        bottom: 0,
        left: 0,
        right: 0,
        zIndex: theme.zIndex.appBar,
        borderTop: `1px solid ${theme.palette.divider}`,
      }}
      elevation={3}
    >
      <BottomNavigation
        value={currentValue >= 0 ? currentValue : false}
        onChange={handleChange}
        showLabels
        sx={{
          height: 56,
          '& .MuiBottomNavigationAction-root': {
            minWidth: 'auto',
            padding: '6px 12px',
            '&.Mui-selected': {
              color: theme.palette.primary.main,
            },
          },
          '& .MuiBottomNavigationAction-label': {
            fontSize: '0.7rem',
            '&.Mui-selected': {
              fontSize: '0.75rem',
            },
          },
        }}
      >
        {config.items.map((item) => (
          <BottomNavigationAction
            key={item.key}
            label={item.label}
            icon={
              item.badge ? (
                <Badge badgeContent={item.badge} color="error" max={99}>
                  {item.icon}
                </Badge>
              ) : (
                item.icon
              )
            }
          />
        ))}
      </BottomNavigation>
    </Paper>
  );
}

// 匯出配置供 BottomNavSheet 使用
export { bottomNavRoutes };
export type { BottomNavItem };
