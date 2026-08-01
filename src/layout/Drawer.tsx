'use client';
import React, { useState, useEffect } from 'react';
import {
  Drawer as MuiDrawer,
  SwipeableDrawer,
  List,
  ListItemButton,
  ListItemIcon,
  ListItemText,
  Toolbar,
  Box,
  Divider,
  Typography,
  Collapse,
  useMediaQuery,
  alpha,
} from '@mui/material';
import { useTheme } from '@mui/material/styles';
import { useRouter } from 'next/router';
import { getUserRole } from '../utils/auth';

// 圖示
import RecordVoiceOverIcon from '@mui/icons-material/RecordVoiceOver';
import PeopleIcon from '@mui/icons-material/People';
import PersonIcon from '@mui/icons-material/Person';
import SummarizeIcon from '@mui/icons-material/Summarize';
import WarningIcon from '@mui/icons-material/Warning';
import TimelineIcon from '@mui/icons-material/Timeline';
import NotificationsActiveIcon from '@mui/icons-material/NotificationsActive';
import MemoryIcon from '@mui/icons-material/Memory';
import DashboardIcon from '@mui/icons-material/Dashboard';
import NotificationsIcon from '@mui/icons-material/Notifications';
import GroupIcon from '@mui/icons-material/Group';
import AdminPanelSettingsIcon from '@mui/icons-material/AdminPanelSettings';
import VpnKeyIcon from '@mui/icons-material/VpnKey';
import SecurityIcon from '@mui/icons-material/Security';
import PolicyIcon from '@mui/icons-material/Policy';
import AssessmentIcon from '@mui/icons-material/Assessment';
import ShieldIcon from '@mui/icons-material/Shield';
import ExpandMoreIcon from '@mui/icons-material/ExpandMore';
import ExpandLessIcon from '@mui/icons-material/ExpandLess';

const drawerWidth = 260;

interface RouteItem {
  href: string;
  label: string;
  icon: React.ReactNode;
  badge?: number;
}

interface RouteGroup {
  title: string;
  items: RouteItem[];
}

const routes: Record<string, RouteGroup[]> = {
  RESIDENT: [
    {
      title: '語音服務',
      items: [
        { href: '/resident/voice', label: '語音互動', icon: <RecordVoiceOverIcon /> },
      ],
    },
  ],
  CAREGIVER: [
    {
      title: '住民管理',
      items: [
        { href: '/caregiver', label: '住民列表', icon: <PeopleIcon /> },
        { href: '/caregiver/resident', label: '住民詳情', icon: <PersonIcon /> },
      ],
    },
    {
      title: '日常照護',
      items: [
        { href: '/caregiver/summary', label: '每日摘要', icon: <SummarizeIcon /> },
        { href: '/caregiver/alerts', label: '高風險警示', icon: <WarningIcon />, badge: 2 },
        { href: '/caregiver/timeline', label: '事件時間軸', icon: <TimelineIcon /> },
        { href: '/caregiver/reminders', label: '提醒管理', icon: <NotificationsActiveIcon />, badge: 5 },
      ],
    },
    {
      title: '進階功能',
      items: [
        { href: '/caregiver/memory', label: '記憶修正', icon: <MemoryIcon /> },
      ],
    },
  ],
  FAMILY: [
    {
      title: '概覽',
      items: [
        { href: '/family/Dashboard', label: '概況', icon: <DashboardIcon /> },
        { href: '/family/Notifications', label: '通知', icon: <NotificationsIcon />, badge: 3 },
      ],
    },
    {
      title: '設定',
      items: [
        { href: '/family/Authorizations', label: '授權管理', icon: <GroupIcon /> },
      ],
    },
  ],
  ADMIN: [
    {
      title: '帳號管理',
      items: [
        { href: '/admin/Users', label: '使用者管理', icon: <PeopleIcon /> },
        { href: '/admin/Roles', label: '角色管理', icon: <AdminPanelSettingsIcon /> },
      ],
    },
    {
      title: '系統設定',
      items: [
        { href: '/admin/Assets', label: '資產設定', icon: <VpnKeyIcon /> },
        { href: '/admin/PolicyEditor', label: '政策編輯', icon: <PolicyIcon /> },
      ],
    },
    {
      title: '安全與稽核',
      items: [
        { href: '/admin/AuditLog', label: '稽核日誌', icon: <SecurityIcon /> },
        { href: '/admin/Security', label: '安全風險', icon: <ShieldIcon /> },
        { href: '/admin/Benchmark', label: '測試報告', icon: <AssessmentIcon /> },
      ],
    },
  ],
};

// 角色標題配置
const roleTitleConfig: Record<string, { title: string; icon: React.ReactNode }> = {
  RESIDENT: { title: '住民介面', icon: <RecordVoiceOverIcon /> },
  CAREGIVER: { title: '照護者介面', icon: <PeopleIcon /> },
  FAMILY: { title: '家屬介面', icon: <GroupIcon /> },
  ADMIN: { title: '管理介面', icon: <AdminPanelSettingsIcon /> },
};

interface DrawerProps {
  mobileOpen?: boolean;
  onClose?: () => void;
}

export default function Drawer({ mobileOpen = false, onClose }: DrawerProps) {
  const theme = useTheme();
  const isMobile = useMediaQuery(theme.breakpoints.down('md'));
  
  const [menu, setMenu] = useState<RouteGroup[]>([]);
  const [role, setRole] = useState<string | null>(null);
  const [mounted, setMounted] = useState(false);
  const [expandedGroups, setExpandedGroups] = useState<Record<string, boolean>>({});
  const router = useRouter();

  useEffect(() => {
    setMounted(true);
    const token = localStorage.getItem('auth');
    const userRole = getUserRole(token);
    setRole(userRole);
    const roleRoutes = userRole ? routes[userRole] || [] : [];
    setMenu(roleRoutes);
    
    // 預設展開所有群組
    const initialExpanded: Record<string, boolean> = {};
    roleRoutes.forEach((group) => {
      initialExpanded[group.title] = true;
    });
    setExpandedGroups(initialExpanded);
  }, []);

  // 登入頁面不顯示 Drawer
  if (router.pathname === '/login') {
    return null;
  }

  // 切換群組展開狀態
  const toggleGroup = (title: string) => {
    setExpandedGroups((prev) => ({
      ...prev,
      [title]: !prev[title],
    }));
  };

  // 導覽點擊處理
  const handleNavClick = (href: string) => {
    router.push(href);
    if (isMobile && onClose) {
      onClose();
    }
  };

  // Drawer 內容
  const drawerContent = (
    <>
      <Toolbar />
      
      {/* 角色標題區 */}
      {mounted && role && roleTitleConfig[role] && (
        <Box 
          sx={{ 
            px: 2.5, 
            py: 2,
            background: alpha(theme.palette.primary.main, 0.08),
            borderBottom: `1px solid ${theme.palette.divider}`,
          }}
        >
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1.5 }}>
            <Box
              sx={{
                width: 36,
                height: 36,
                borderRadius: 2,
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                bgcolor: theme.palette.primary.main,
                color: theme.palette.primary.contrastText,
              }}
            >
              {roleTitleConfig[role].icon}
            </Box>
            <Typography variant="subtitle1" sx={{ fontWeight: 600 }}>
              {roleTitleConfig[role].title}
            </Typography>
          </Box>
        </Box>
      )}
      
      {/* 導覽選單 */}
      <Box sx={{ overflow: 'auto', flex: 1, py: 1 }}>
        {mounted && menu.map((group, groupIndex) => (
          <Box key={group.title}>
            {/* 群組標題（可摺疊） */}
            <ListItemButton
              onClick={() => toggleGroup(group.title)}
              sx={{
                py: 1,
                px: 2.5,
                minHeight: 40,
                '&:hover': {
                  bgcolor: 'transparent',
                },
              }}
            >
              <Typography 
                variant="overline" 
                color="text.secondary"
                sx={{ 
                  flex: 1,
                  fontSize: '0.7rem',
                  fontWeight: 600,
                  letterSpacing: '0.08em',
                }}
              >
                {group.title}
              </Typography>
              {expandedGroups[group.title] ? (
                <ExpandLessIcon sx={{ fontSize: 18, color: 'text.secondary' }} />
              ) : (
                <ExpandMoreIcon sx={{ fontSize: 18, color: 'text.secondary' }} />
              )}
            </ListItemButton>

            {/* 群組項目 */}
            <Collapse in={expandedGroups[group.title]} timeout="auto">
              <List disablePadding>
                {group.items.map((item) => {
                  const isActive = router.pathname === item.href;
                  return (
                    <ListItemButton
                      key={item.href}
                      onClick={() => handleNavClick(item.href)}
                      selected={isActive}
                      sx={{
                        py: 1.25,
                        px: 2,
                        mx: 1.5,
                        mb: 0.5,
                        borderRadius: 2,
                        transition: 'all 0.2s ease',
                        '&.Mui-selected': {
                          bgcolor: alpha(theme.palette.primary.main, 0.12),
                          '&:hover': {
                            bgcolor: alpha(theme.palette.primary.main, 0.18),
                          },
                          '&::before': {
                            content: '""',
                            position: 'absolute',
                            left: 0,
                            top: '50%',
                            transform: 'translateY(-50%)',
                            width: 4,
                            height: '60%',
                            borderRadius: 2,
                            bgcolor: theme.palette.primary.main,
                          },
                        },
                        '&:hover': {
                          bgcolor: alpha(theme.palette.primary.main, 0.06),
                        },
                      }}
                    >
                      <ListItemIcon
                        sx={{
                          color: isActive ? 'primary.main' : 'text.secondary',
                          minWidth: 40,
                          transition: 'color 0.2s ease',
                        }}
                      >
                        {item.icon}
                      </ListItemIcon>
                      <ListItemText
                        primary={item.label}
                        slotProps={{
                          primary: {
                            sx: {
                              fontWeight: isActive ? 600 : 500,
                              fontSize: '0.9rem',
                              color: isActive ? 'primary.main' : 'text.primary',
                            }
                          }
                        }}
                      />
                      {/* 徽章 */}
                      {item.badge && item.badge > 0 && (
                        <Box
                          sx={{
                            minWidth: 22,
                            height: 22,
                            borderRadius: 11,
                            bgcolor: isActive ? 'primary.main' : 'error.main',
                            color: 'white',
                            display: 'flex',
                            alignItems: 'center',
                            justifyContent: 'center',
                            fontSize: '0.75rem',
                            fontWeight: 600,
                          }}
                        >
                          {item.badge > 99 ? '99+' : item.badge}
                        </Box>
                      )}
                    </ListItemButton>
                  );
                })}
              </List>
            </Collapse>

            {/* 群組分隔線 */}
            {groupIndex < menu.length - 1 && (
              <Divider sx={{ my: 1.5, mx: 2 }} />
            )}
          </Box>
        ))}
      </Box>

      {/* 底部版權資訊 */}
      <Box 
        sx={{ 
          p: 2, 
          borderTop: `1px solid ${theme.palette.divider}`,
          textAlign: 'center',
        }}
      >
        <Typography variant="caption" color="text.secondary">
          © 2026 404 Not Sleep
        </Typography>
      </Box>
    </>
  );

  // 避免 SSR 與 CSR 不一致
  if (!mounted) {
    return (
      <MuiDrawer
        variant="permanent"
        sx={{
          display: { xs: 'none', md: 'block' },
          width: drawerWidth,
          flexShrink: 0,
          [`& .MuiDrawer-paper`]: { 
            width: drawerWidth, 
            boxSizing: 'border-box',
          },
        }}
      >
        <Toolbar />
      </MuiDrawer>
    );
  }

  // 行動版：使用 SwipeableDrawer
  if (isMobile) {
    return (
      <SwipeableDrawer
        variant="temporary"
        open={mobileOpen}
        onClose={onClose || (() => {})}
        onOpen={() => {}}
        ModalProps={{
          keepMounted: true, // 提升行動裝置效能
        }}
        sx={{
          display: { xs: 'block', md: 'none' },
          '& .MuiDrawer-paper': { 
            width: drawerWidth,
            boxSizing: 'border-box',
          },
        }}
      >
        {drawerContent}
      </SwipeableDrawer>
    );
  }

  // 桌面版：使用 permanent Drawer
  return (
    <MuiDrawer
      variant="permanent"
      sx={{
        display: { xs: 'none', md: 'block' },
        width: drawerWidth,
        flexShrink: 0,
        [`& .MuiDrawer-paper`]: { 
          width: drawerWidth, 
          boxSizing: 'border-box',
        },
      }}
    >
      {drawerContent}
    </MuiDrawer>
  );
}
