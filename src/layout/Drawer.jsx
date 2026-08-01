import React from 'react';
import { Drawer as MuiDrawer, List, ListItemButton, ListItemText, Toolbar } from '@mui/material';
import Link from 'next/link';
import { getUserRole } from '../utils/auth';

const drawerWidth = 240;

const routes = {
  CAREGIVER: [
    { href: '/caregiver', label: '住民列表' },
    { href: '/caregiver/summary', label: '每日摘要' },
    { href: '/caregiver/alerts', label: '高風險警示' },
  ],
  FAMILY: [
    { href: '/family/dashboard', label: '概況' },
    { href: '/family/notifications', label: '通知' },
    { href: '/family/authorizations', label: '授權管理' },
  ],
  ADMIN: [
    { href: '/admin/users', label: '使用者管理' },
    { href: '/admin/roles', label: '角色管理' },
    { href: '/admin/assets', label: '資產設定' },
    { href: '/admin/audit', label: '稽核日誌' },
    { href: '/admin/policy', label: '政策編輯' },
    { href: '/admin/benchmark', label: '測試報告' },
  ],
};

export default function Drawer() {
  const token = typeof window !== 'undefined' ? localStorage.getItem('auth') : null;
  const role = getUserRole(token);
  const menu = role ? routes[role] || [] : [];

  return (
    <MuiDrawer
      variant="permanent"
      sx={{
        width: drawerWidth,
        flexShrink: 0,
        [`& .MuiDrawer-paper`]: { width: drawerWidth, boxSizing: 'border-box' },
      }}
    >
      <Toolbar />
      <List>
        {menu.map((item) => (
          <ListItemButton component={Link} href={item.href} key={item.href}>
            <ListItemText primary={item.label} />
          </ListItemButton>
        ))}
      </List>
    </MuiDrawer>
  );
}
