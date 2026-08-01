'use client';
import React, { useState } from 'react';
import {
  Container,
  Typography,
  Box,
  Paper,
  Card,
  CardContent,
  CardActions,
  Button,
  Avatar,
  Chip,
  Divider,
  List,
  ListItem,
  ListItemIcon,
  ListItemText,
  Badge,
  Alert,
} from '@mui/material';
import Grid from '@mui/material/Grid';
import DashboardIcon from '@mui/icons-material/Dashboard';
import PersonIcon from '@mui/icons-material/Person';
import NotificationsIcon from '@mui/icons-material/Notifications';
import EventIcon from '@mui/icons-material/Event';
import MedicationIcon from '@mui/icons-material/Medication';
import DirectionsWalkIcon from '@mui/icons-material/DirectionsWalk';
import RestaurantIcon from '@mui/icons-material/Restaurant';
import MoodIcon from '@mui/icons-material/Mood';
import WarningIcon from '@mui/icons-material/Warning';
import AccessTimeIcon from '@mui/icons-material/AccessTime';
import ArrowForwardIcon from '@mui/icons-material/ArrowForward';
import { useRouter } from 'next/router';

// 授權住民摘要
interface AuthorizedResidentSummary {
  id: string;
  name: string;
  lastUpdate: Date;
  todaySummary: string;
  pendingReminders: number;
  recentAlerts: number;
  moodTrend: 'positive' | 'neutral' | 'negative';
  lastMedication?: string;
  lastActivity?: string;
}

// 通知摘要
interface NotificationSummary {
  id: string;
  type: 'alert' | 'reminder' | 'event' | 'info';
  title: string;
  residentName: string;
  timestamp: Date;
  read: boolean;
}

// 情緒趨勢配置
const moodTrendConfig: Record<string, { label: string; color: 'success' | 'warning' | 'error' }> = {
  positive: { label: '良好', color: 'success' },
  neutral: { label: '平穩', color: 'warning' },
  negative: { label: '需關注', color: 'error' },
};

// 模擬授權住民資料
const mockAuthorizedResidents: AuthorizedResidentSummary[] = [
  {
    id: 'r1',
    name: '王奶奶',
    lastUpdate: new Date('2026-08-01T20:00:00'),
    todaySummary: '今日用藥正常，早上八點已服用降血壓藥。活動量適中，上午散步 30 分鐘。情緒良好，下午與女兒通電話後心情愉快。',
    pendingReminders: 2,
    recentAlerts: 0,
    moodTrend: 'positive',
    lastMedication: '今天 08:00 降血壓藥',
    lastActivity: '今天 10:00 散步 30 分鐘',
  },
];

// 模擬通知資料
const mockNotifications: NotificationSummary[] = [
  {
    id: '1',
    type: 'reminder',
    title: '回診提醒：明天下午三點心臟科',
    residentName: '王奶奶',
    timestamp: new Date('2026-08-01T10:00:00'),
    read: false,
  },
  {
    id: '2',
    type: 'event',
    title: '用藥紀錄：早上八點已服藥',
    residentName: '王奶奶',
    timestamp: new Date('2026-08-01T08:05:00'),
    read: true,
  },
  {
    id: '3',
    type: 'info',
    title: '每日摘要已更新',
    residentName: '王奶奶',
    timestamp: new Date('2026-08-01T20:00:00'),
    read: false,
  },
];

// 通知類型圖示
const notificationTypeIcons: Record<string, React.ReactNode> = {
  alert: <WarningIcon color="error" />,
  reminder: <EventIcon color="warning" />,
  event: <MedicationIcon color="info" />,
  info: <DashboardIcon color="success" />,
};

export default function FamilyDashboard() {
  const router = useRouter();
  const [authorizedResidents] = useState<AuthorizedResidentSummary[]>(mockAuthorizedResidents);
  const [notifications] = useState<NotificationSummary[]>(mockNotifications);

  const unreadCount = notifications.filter((n) => !n.read).length;

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
    <Container maxWidth="lg" sx={{ py: 2 }}>
      <Typography variant="h4" gutterBottom sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
        <DashboardIcon color="primary" />
        家屬儀表板
      </Typography>
      <Typography variant="body2" color="text.secondary" gutterBottom>
        查看您授權的住民近期照護狀況
      </Typography>

      {/* 快速入口 */}
      <Paper sx={{ p: 2, mb: 3, bgcolor: 'primary.light' }}>
        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: 2 }}>
          <Box>
            <Typography variant="h6" color="primary.contrastText">
              歡迎回來
            </Typography>
            <Typography variant="body2" color="primary.contrastText">
              您目前有 {authorizedResidents.length} 位住民的查看權限
            </Typography>
          </Box>
          <Box sx={{ display: 'flex', gap: 1 }}>
            <Badge badgeContent={unreadCount} color="error">
              <Button
                variant="contained"
                color="inherit"
                startIcon={<NotificationsIcon />}
                onClick={() => router.push('/family/Notifications')}
              >
                通知中心
              </Button>
            </Badge>
            <Button
              variant="outlined"
              color="inherit"
              onClick={() => router.push('/family/Authorizations')}
            >
              授權管理
            </Button>
          </Box>
        </Box>
      </Paper>

      <Grid container spacing={{ xs: 2, sm: 3 }}>
        {/* 住民摘要卡片 */}
        <Grid item xs={12} md={8}>
          <Typography variant="h6" gutterBottom>
            住民狀況
          </Typography>
          {authorizedResidents.length === 0 ? (
            <Alert severity="info">
              您目前沒有被授權查看的住民。請聯繫照護機構進行授權設定。
            </Alert>
          ) : (
            authorizedResidents.map((resident) => (
              <Card key={resident.id} sx={{ mb: 2 }}>
                <CardContent>
                  {/* 住民標題 */}
                  <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', mb: 2 }}>
                    <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
                      <Avatar sx={{ width: 56, height: 56, bgcolor: 'primary.main' }}>
                        {resident.name[0]}
                      </Avatar>
                      <Box>
                        <Typography variant="h5">{resident.name}</Typography>
                        <Typography variant="body2" color="text.secondary">
                          <AccessTimeIcon sx={{ fontSize: 14, mr: 0.5, verticalAlign: 'middle' }} />
                          更新於 {formatTime(resident.lastUpdate)}
                        </Typography>
                      </Box>
                    </Box>
                    <Box sx={{ display: 'flex', gap: 1 }}>
                      <Chip
                        label={moodTrendConfig[resident.moodTrend].label}
                        color={moodTrendConfig[resident.moodTrend].color}
                        icon={<MoodIcon />}
                      />
                      {resident.recentAlerts > 0 && (
                        <Chip label={`${resident.recentAlerts} 個警示`} color="error" />
                      )}
                    </Box>
                  </Box>

                  {/* 今日摘要 */}
                  <Paper sx={{ p: { xs: 1.5, sm: 2 }, bgcolor: 'grey.50', mb: { xs: 1.5, sm: 2 } }}>
                    <Typography variant="subtitle2" color="text.secondary" gutterBottom>
                      今日摘要
                    </Typography>
                    <Typography variant="body1">{resident.todaySummary}</Typography>
                  </Paper>

                  {/* 快速資訊 */}
                  <Grid container spacing={2}>
                    <Grid item xs={6} sm={3}>
                      <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                        <MedicationIcon color="error" />
                        <Box>
                          <Typography variant="caption" color="text.secondary">
                            最近用藥
                          </Typography>
                          <Typography variant="body2">
                            {resident.lastMedication || '無紀錄'}
                          </Typography>
                        </Box>
                      </Box>
                    </Grid>
                    <Grid item xs={6} sm={3}>
                      <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                        <DirectionsWalkIcon color="success" />
                        <Box>
                          <Typography variant="caption" color="text.secondary">
                            最近活動
                          </Typography>
                          <Typography variant="body2">
                            {resident.lastActivity || '無紀錄'}
                          </Typography>
                        </Box>
                      </Box>
                    </Grid>
                    <Grid item xs={6} sm={3}>
                      <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                        <EventIcon color="warning" />
                        <Box>
                          <Typography variant="caption" color="text.secondary">
                            待處理提醒
                          </Typography>
                          <Typography variant="body2">{resident.pendingReminders} 個</Typography>
                        </Box>
                      </Box>
                    </Grid>
                    <Grid item xs={6} sm={3}>
                      <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                        <WarningIcon color={resident.recentAlerts > 0 ? 'error' : 'disabled'} />
                        <Box>
                          <Typography variant="caption" color="text.secondary">
                            近期警示
                          </Typography>
                          <Typography variant="body2">{resident.recentAlerts} 個</Typography>
                        </Box>
                      </Box>
                    </Grid>
                  </Grid>
                </CardContent>
                <Divider />
                <CardActions>
                  <Button size="small" onClick={() => router.push('/family/Notifications')}>
                    查看詳細紀錄
                  </Button>
                </CardActions>
              </Card>
            ))
          )}
        </Grid>

        {/* 通知側欄 */}
        <Grid item xs={12} md={4}>
          <Paper sx={{ p: { xs: 1.5, sm: 2 } }}>
            <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
              <Typography variant="h6">
                <Badge badgeContent={unreadCount} color="error" sx={{ mr: 1 }}>
                  <NotificationsIcon />
                </Badge>
                最新通知
              </Typography>
              <Button
                size="small"
                endIcon={<ArrowForwardIcon />}
                onClick={() => router.push('/family/Notifications')}
              >
                全部
              </Button>
            </Box>

            <List dense>
              {notifications.slice(0, 5).map((notification, index) => (
                <React.Fragment key={notification.id}>
                  <ListItem
                    sx={{
                      bgcolor: notification.read ? 'inherit' : 'action.hover',
                      borderRadius: 1,
                    }}
                  >
                    <ListItemIcon sx={{ minWidth: 36 }}>
                      {notificationTypeIcons[notification.type]}
                    </ListItemIcon>
                    <ListItemText
                      primary={
                        <Typography
                          variant="body2"
                          fontWeight={notification.read ? 'normal' : 'bold'}
                        >
                          {notification.title}
                        </Typography>
                      }
                      secondary={
                        <Typography variant="caption" color="text.secondary">
                          {notification.residentName} · {formatTime(notification.timestamp)}
                        </Typography>
                      }
                    />
                  </ListItem>
                  {index < Math.min(notifications.length, 5) - 1 && <Divider />}
                </React.Fragment>
              ))}
            </List>

            {notifications.length === 0 && (
              <Typography variant="body2" color="text.secondary" align="center" sx={{ py: 2 }}>
                沒有通知
              </Typography>
            )}
          </Paper>

          {/* 快速功能 */}
          <Paper sx={{ p: { xs: 1.5, sm: 2 }, mt: 2 }}>
            <Typography variant="h6" gutterBottom>
              快速功能
            </Typography>
            <List dense>
              <ListItem
                component="button"
                sx={{ cursor: 'pointer', '&:hover': { bgcolor: 'action.hover' } }}
                onClick={() => router.push('/family/Authorizations')}
              >
                <ListItemIcon>
                  <PersonIcon />
                </ListItemIcon>
                <ListItemText primary="管理授權" secondary="新增或調整授權對象" />
              </ListItem>
              <ListItem
                component="button"
                sx={{ cursor: 'pointer', '&:hover': { bgcolor: 'action.hover' } }}
                onClick={() => router.push('/family/Notifications')}
              >
                <ListItemIcon>
                  <NotificationsIcon />
                </ListItemIcon>
                <ListItemText primary="通知設定" secondary="調整通知偏好" />
              </ListItem>
            </List>
          </Paper>

          {/* 隱私提示 */}
          <Alert severity="info" sx={{ mt: 2 }}>
            您僅能查看被授權的住民資訊。如需查看其他住民，請聯繫照護機構。
          </Alert>
        </Grid>
      </Grid>
    </Container>
  );
}
