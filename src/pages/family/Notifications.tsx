'use client';
import React, { useState } from 'react';
import {
  Container,
  Typography,
  Box,
  Paper,
  List,
  ListItem,
  ListItemText,
  ListItemIcon,
  ListItemSecondaryAction,
  IconButton,
  Chip,
  Tabs,
  Tab,
  Badge,
  Button,
  Divider,
} from '@mui/material';
import NotificationsIcon from '@mui/icons-material/Notifications';
import MedicationIcon from '@mui/icons-material/Medication';
import EventIcon from '@mui/icons-material/Event';
import WarningIcon from '@mui/icons-material/Warning';
import InfoIcon from '@mui/icons-material/Info';
import CheckCircleIcon from '@mui/icons-material/CheckCircle';
import DeleteIcon from '@mui/icons-material/Delete';
import MarkEmailReadIcon from '@mui/icons-material/MarkEmailRead';

// 通知類型
type NotificationType = 'alert' | 'reminder' | 'event' | 'info';
type NotificationPriority = 'high' | 'medium' | 'low';

interface Notification {
  id: string;
  type: NotificationType;
  priority: NotificationPriority;
  title: string;
  message: string;
  residentName: string;
  timestamp: Date;
  read: boolean;
}

// 類型配置
const typeConfig: Record<NotificationType, { icon: React.ReactNode; color: 'error' | 'warning' | 'info' | 'success' }> = {
  alert: { icon: <WarningIcon />, color: 'error' },
  reminder: { icon: <EventIcon />, color: 'warning' },
  event: { icon: <MedicationIcon />, color: 'info' },
  info: { icon: <InfoIcon />, color: 'success' },
};

// 模擬通知資料
const mockNotifications: Notification[] = [
  {
    id: '1',
    type: 'alert',
    priority: 'high',
    title: '跌倒風險警示',
    message: '王奶奶表示頭暈不適，照護人員已前往查看',
    residentName: '王奶奶',
    timestamp: new Date('2026-08-01T14:30:00'),
    read: false,
  },
  {
    id: '2',
    type: 'reminder',
    priority: 'high',
    title: '回診提醒',
    message: '王奶奶明天下午三點需至心臟科回診',
    residentName: '王奶奶',
    timestamp: new Date('2026-08-01T10:00:00'),
    read: false,
  },
  {
    id: '3',
    type: 'event',
    priority: 'medium',
    title: '用藥紀錄',
    message: '王奶奶已於早上八點服用降血壓藥',
    residentName: '王奶奶',
    timestamp: new Date('2026-08-01T08:05:00'),
    read: true,
  },
  {
    id: '4',
    type: 'info',
    priority: 'low',
    title: '每日摘要已更新',
    message: '王奶奶今日摘要已生成，可前往查看',
    residentName: '王奶奶',
    timestamp: new Date('2026-08-01T20:00:00'),
    read: true,
  },
  {
    id: '5',
    type: 'event',
    priority: 'medium',
    title: '活動紀錄',
    message: '王奶奶今日散步 30 分鐘',
    residentName: '王奶奶',
    timestamp: new Date('2026-08-01T10:30:00'),
    read: true,
  },
];

export default function Notifications() {
  const [notifications, setNotifications] = useState<Notification[]>(mockNotifications);
  const [tabValue, setTabValue] = useState(0);

  // 計算未讀數量
  const unreadCount = notifications.filter((n) => !n.read).length;
  const alertCount = notifications.filter((n) => n.type === 'alert' && !n.read).length;

  // 依分頁篩選
  const filteredNotifications =
    tabValue === 0
      ? notifications
      : tabValue === 1
        ? notifications.filter((n) => !n.read)
        : notifications.filter((n) => n.type === 'alert');

  // 標記已讀
  const markAsRead = (id: string) => {
    setNotifications((prev) => prev.map((n) => (n.id === id ? { ...n, read: true } : n)));
  };

  // 標記全部已讀
  const markAllAsRead = () => {
    setNotifications((prev) => prev.map((n) => ({ ...n, read: true })));
  };

  // 刪除通知
  const deleteNotification = (id: string) => {
    setNotifications((prev) => prev.filter((n) => n.id !== id));
  };

  // 格式化時間
  const formatTime = (date: Date) => {
    const now = new Date();
    const diff = now.getTime() - date.getTime();
    const hours = Math.floor(diff / (1000 * 60 * 60));
    if (hours < 1) return '剛剛';
    if (hours < 24) return `${hours} 小時前`;
    const days = Math.floor(hours / 24);
    if (days < 7) return `${days} 天前`;
    return date.toLocaleDateString('zh-TW');
  };

  return (
    <Container maxWidth="md" sx={{ py: 2 }}>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
        <Typography variant="h4" sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
          <Badge badgeContent={unreadCount} color="error">
            <NotificationsIcon color="primary" />
          </Badge>
          通知中心
        </Typography>
        {unreadCount > 0 && (
          <Button startIcon={<MarkEmailReadIcon />} onClick={markAllAsRead}>
            全部標為已讀
          </Button>
        )}
      </Box>

      {/* 分頁 */}
      <Paper sx={{ mb: 2 }}>
        <Tabs value={tabValue} onChange={(_, v) => setTabValue(v)}>
          <Tab label={`全部 (${notifications.length})`} />
          <Tab
            label={
              <Badge badgeContent={unreadCount} color="error" sx={{ pr: 2 }}>
                未讀
              </Badge>
            }
          />
          <Tab
            label={
              <Badge badgeContent={alertCount} color="error" sx={{ pr: 2 }}>
                警示
              </Badge>
            }
          />
        </Tabs>
      </Paper>

      {/* 通知列表 */}
      <Paper>
        <List>
          {filteredNotifications.length === 0 ? (
            <ListItem>
              <ListItemText
                primary={
                  <Typography color="text.secondary" align="center">
                    沒有通知
                  </Typography>
                }
              />
            </ListItem>
          ) : (
            filteredNotifications.map((notification, index) => (
              <React.Fragment key={notification.id}>
                <ListItem
                  sx={{
                    bgcolor: notification.read ? 'inherit' : 'action.hover',
                    '&:hover': { bgcolor: 'action.selected' },
                  }}
                >
                  <ListItemIcon sx={{ color: `${typeConfig[notification.type].color}.main` }}>
                    {typeConfig[notification.type].icon}
                  </ListItemIcon>
                  <ListItemText
                    primary={
                      <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                        <Typography fontWeight={notification.read ? 'normal' : 'bold'}>
                          {notification.title}
                        </Typography>
                        <Chip
                          size="small"
                          label={notification.residentName}
                          variant="outlined"
                        />
                        {notification.priority === 'high' && (
                          <Chip size="small" label="重要" color="error" />
                        )}
                      </Box>
                    }
                    secondary={
                      <Box>
                        <Typography variant="body2" color="text.secondary">
                          {notification.message}
                        </Typography>
                        <Typography variant="caption" color="text.secondary">
                          {formatTime(notification.timestamp)}
                        </Typography>
                      </Box>
                    }
                  />
                  <ListItemSecondaryAction>
                    {!notification.read && (
                      <IconButton
                        size="small"
                        onClick={() => markAsRead(notification.id)}
                        title="標為已讀"
                      >
                        <CheckCircleIcon />
                      </IconButton>
                    )}
                    <IconButton
                      size="small"
                      onClick={() => deleteNotification(notification.id)}
                      title="刪除"
                    >
                      <DeleteIcon />
                    </IconButton>
                  </ListItemSecondaryAction>
                </ListItem>
                {index < filteredNotifications.length - 1 && <Divider />}
              </React.Fragment>
            ))
          )}
        </List>
      </Paper>
    </Container>
  );
}
