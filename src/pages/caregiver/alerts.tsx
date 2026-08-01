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
  Chip,
  Button,
  IconButton,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Tabs,
  Tab,
  Avatar,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField,
  Alert,
  Tooltip,
  Badge,
} from '@mui/material';
import Grid from '@mui/material/Grid';
import WarningIcon from '@mui/icons-material/Warning';
import ErrorIcon from '@mui/icons-material/Error';
import CheckCircleIcon from '@mui/icons-material/CheckCircle';
import AccessTimeIcon from '@mui/icons-material/AccessTime';
import PersonIcon from '@mui/icons-material/Person';
import NotificationsActiveIcon from '@mui/icons-material/NotificationsActive';
import VisibilityIcon from '@mui/icons-material/Visibility';
import DoneIcon from '@mui/icons-material/Done';
import CloseIcon from '@mui/icons-material/Close';
import CommentIcon from '@mui/icons-material/Comment';
import RefreshIcon from '@mui/icons-material/Refresh';
import { useRouter } from 'next/router';

// 警示類型
type AlertSeverity = 'critical' | 'high' | 'medium' | 'low';
type AlertStatus = 'active' | 'acknowledged' | 'resolved' | 'dismissed';
type AlertType = 'fall_risk' | 'vital_abnormal' | 'missed_medication' | 'behavior_change' | 'emergency' | 'other';

// 警示資料
interface CareAlert {
  id: string;
  residentId: string;
  residentName: string;
  type: AlertType;
  severity: AlertSeverity;
  status: AlertStatus;
  title: string;
  message: string;
  sourceText?: string;
  createdAt: Date;
  acknowledgedAt?: Date;
  acknowledgedBy?: string;
  resolvedAt?: Date;
  resolvedBy?: string;
  resolution?: string;
}

// 嚴重度配置
const severityConfig: Record<AlertSeverity, { label: string; color: 'error' | 'warning' | 'info' | 'success'; bgcolor: string }> = {
  critical: { label: '緊急', color: 'error', bgcolor: 'error.main' },
  high: { label: '高', color: 'error', bgcolor: 'error.light' },
  medium: { label: '中', color: 'warning', bgcolor: 'warning.light' },
  low: { label: '低', color: 'info', bgcolor: 'info.light' },
};

// 狀態配置
const statusConfig: Record<AlertStatus, { label: string; color: 'error' | 'warning' | 'success' | 'default' }> = {
  active: { label: '待處理', color: 'error' },
  acknowledged: { label: '已確認', color: 'warning' },
  resolved: { label: '已解決', color: 'success' },
  dismissed: { label: '已忽略', color: 'default' },
};

// 類型配置
const typeConfig: Record<AlertType, { label: string; icon: React.ReactNode }> = {
  fall_risk: { label: '跌倒風險', icon: <WarningIcon /> },
  vital_abnormal: { label: '生命徵象異常', icon: <ErrorIcon /> },
  missed_medication: { label: '漏服藥物', icon: <NotificationsActiveIcon /> },
  behavior_change: { label: '行為改變', icon: <PersonIcon /> },
  emergency: { label: '緊急求助', icon: <ErrorIcon /> },
  other: { label: '其他', icon: <WarningIcon /> },
};

// 模擬警示資料
const mockAlerts: CareAlert[] = [
  {
    id: '1',
    residentId: 'r1',
    residentName: '王奶奶',
    type: 'fall_risk',
    severity: 'high',
    status: 'active',
    title: '跌倒風險警示',
    message: '住民表示頭暈不適，需要立即關注',
    sourceText: '我有點頭暈，站不太穩',
    createdAt: new Date('2026-08-01T09:30:00'),
  },
  {
    id: '2',
    residentId: 'r2',
    residentName: '李爺爺',
    type: 'vital_abnormal',
    severity: 'medium',
    status: 'acknowledged',
    title: '血壓異常',
    message: '收縮壓 160mmHg，高於正常範圍',
    createdAt: new Date('2026-08-01T11:15:00'),
    acknowledgedAt: new Date('2026-08-01T11:20:00'),
    acknowledgedBy: '張護理師',
  },
  {
    id: '3',
    residentId: 'r3',
    residentName: '張奶奶',
    type: 'missed_medication',
    severity: 'medium',
    status: 'resolved',
    title: '漏服藥物提醒',
    message: '早上血糖藥未在預定時間服用',
    createdAt: new Date('2026-08-01T08:30:00'),
    resolvedAt: new Date('2026-08-01T09:00:00'),
    resolvedBy: '李照服員',
    resolution: '已補服藥物，住民狀況正常',
  },
  {
    id: '4',
    residentId: 'r2',
    residentName: '李爺爺',
    type: 'behavior_change',
    severity: 'low',
    status: 'dismissed',
    title: '情緒變化',
    message: '住民今日較為沉默，與平時不同',
    createdAt: new Date('2026-08-01T10:00:00'),
  },
  {
    id: '5',
    residentId: 'r1',
    residentName: '王奶奶',
    type: 'emergency',
    severity: 'critical',
    status: 'resolved',
    title: '緊急求助',
    message: '住民按下緊急呼叫按鈕',
    sourceText: '我跌倒了，站不起來',
    createdAt: new Date('2026-07-31T15:30:00'),
    resolvedAt: new Date('2026-07-31T15:45:00'),
    resolvedBy: '張護理師',
    resolution: '已協助住民起身，檢查無明顯外傷，持續觀察中',
  },
];

export default function Alerts() {
  const router = useRouter();
  const [alerts, setAlerts] = useState<CareAlert[]>(mockAlerts);
  const [tabValue, setTabValue] = useState(0);
  const [filterSeverity, setFilterSeverity] = useState<string>('all');
  const [filterType, setFilterType] = useState<string>('all');
  const [selectedAlert, setSelectedAlert] = useState<CareAlert | null>(null);
  const [actionDialogOpen, setActionDialogOpen] = useState(false);
  const [actionType, setActionType] = useState<'acknowledge' | 'resolve' | 'dismiss'>('acknowledge');
  const [resolution, setResolution] = useState('');

  // 依狀態分類
  const activeAlerts = alerts.filter((a) => a.status === 'active');
  const acknowledgedAlerts = alerts.filter((a) => a.status === 'acknowledged');
  const resolvedAlerts = alerts.filter((a) => a.status === 'resolved' || a.status === 'dismissed');

  // 依分頁篩選
  const getFilteredAlerts = () => {
    let filtered = tabValue === 0 ? activeAlerts : tabValue === 1 ? acknowledgedAlerts : resolvedAlerts;
    if (filterSeverity !== 'all') {
      filtered = filtered.filter((a) => a.severity === filterSeverity);
    }
    if (filterType !== 'all') {
      filtered = filtered.filter((a) => a.type === filterType);
    }
    return filtered.sort((a, b) => {
      // 按嚴重度排序
      const severityOrder = { critical: 0, high: 1, medium: 2, low: 3 };
      return severityOrder[a.severity] - severityOrder[b.severity];
    });
  };

  // 格式化時間
  const formatTime = (date: Date) => {
    const now = new Date();
    const diff = now.getTime() - date.getTime();
    const minutes = Math.floor(diff / (1000 * 60));
    if (minutes < 60) return `${minutes} 分鐘前`;
    const hours = Math.floor(minutes / 60);
    if (hours < 24) return `${hours} 小時前`;
    return date.toLocaleString('zh-TW', { month: 'numeric', day: 'numeric', hour: '2-digit', minute: '2-digit' });
  };

  // 開啟操作對話框
  const handleAction = (alert: CareAlert, action: 'acknowledge' | 'resolve' | 'dismiss') => {
    setSelectedAlert(alert);
    setActionType(action);
    setResolution('');
    setActionDialogOpen(true);
  };

  // 執行操作
  const confirmAction = () => {
    if (!selectedAlert) return;

    const now = new Date();
    const updatedAlerts = alerts.map((a) => {
      if (a.id !== selectedAlert.id) return a;

      if (actionType === 'acknowledge') {
        return { ...a, status: 'acknowledged' as AlertStatus, acknowledgedAt: now, acknowledgedBy: '目前使用者' };
      } else if (actionType === 'resolve') {
        return { ...a, status: 'resolved' as AlertStatus, resolvedAt: now, resolvedBy: '目前使用者', resolution };
      } else {
        return { ...a, status: 'dismissed' as AlertStatus };
      }
    });

    setAlerts(updatedAlerts);
    setActionDialogOpen(false);
  };

  const filteredAlerts = getFilteredAlerts();

  return (
    <Container maxWidth="lg" sx={{ py: 2 }}>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
        <Typography variant="h4" sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
          <Badge badgeContent={activeAlerts.length} color="error">
            <WarningIcon color="error" />
          </Badge>
          高風險警示
        </Typography>
        <Button variant="outlined" startIcon={<RefreshIcon />}>
          重新整理
        </Button>
      </Box>

      {/* 統計卡片 */}
      <Grid container spacing={2} sx={{ mb: 3 }}>
        <Grid size={{ xs: 6, sm: 3 }}>
          <Paper sx={{ p: 2, textAlign: 'center', bgcolor: (theme) => theme.palette.mode === 'dark' ? 'rgba(248, 113, 113, 0.15)' : 'error.light' }}>
            <Typography variant="h3" sx={{ color: (theme) => theme.palette.mode === 'dark' ? '#F87171' : 'error.dark' }}>
              {activeAlerts.length}
            </Typography>
            <Typography variant="body2">待處理</Typography>
          </Paper>
        </Grid>
        <Grid size={{ xs: 6, sm: 3 }}>
          <Paper sx={{ p: 2, textAlign: 'center', bgcolor: (theme) => theme.palette.mode === 'dark' ? 'rgba(251, 191, 36, 0.15)' : 'warning.light' }}>
            <Typography variant="h3" sx={{ color: (theme) => theme.palette.mode === 'dark' ? '#FBBF24' : 'warning.dark' }}>
              {acknowledgedAlerts.length}
            </Typography>
            <Typography variant="body2">處理中</Typography>
          </Paper>
        </Grid>
        <Grid size={{ xs: 6, sm: 3 }}>
          <Paper sx={{ p: 2, textAlign: 'center', bgcolor: (theme) => theme.palette.mode === 'dark' ? 'rgba(74, 222, 128, 0.15)' : 'success.light' }}>
            <Typography variant="h3" sx={{ color: (theme) => theme.palette.mode === 'dark' ? '#4ADE80' : 'success.dark' }}>
              {resolvedAlerts.length}
            </Typography>
            <Typography variant="body2">已解決</Typography>
          </Paper>
        </Grid>
        <Grid size={{ xs: 6, sm: 3 }}>
          <Paper sx={{ p: 2, textAlign: 'center' }}>
            <Typography variant="h3" color="error.main">
              {alerts.filter((a) => a.severity === 'critical' && a.status === 'active').length}
            </Typography>
            <Typography variant="body2">緊急事件</Typography>
          </Paper>
        </Grid>
      </Grid>

      {/* 分頁與篩選 */}
      <Paper sx={{ mb: 2 }}>
        <Box sx={{ borderBottom: 1, borderColor: 'divider' }}>
          <Tabs value={tabValue} onChange={(_, v) => setTabValue(v)}>
            <Tab
              label={
                <Badge badgeContent={activeAlerts.length} color="error" sx={{ pr: 2 }}>
                  待處理
                </Badge>
              }
            />
            <Tab label={`處理中 (${acknowledgedAlerts.length})`} />
            <Tab label={`已完成 (${resolvedAlerts.length})`} />
          </Tabs>
        </Box>
        <Box sx={{ p: 2, display: 'flex', gap: 2, flexWrap: 'wrap' }}>
          <FormControl size="small" sx={{ minWidth: 120 }}>
            <InputLabel>嚴重度</InputLabel>
            <Select value={filterSeverity} label="嚴重度" onChange={(e) => setFilterSeverity(e.target.value)}>
              <MenuItem value="all">全部</MenuItem>
              {Object.entries(severityConfig).map(([key, config]) => (
                <MenuItem key={key} value={key}>
                  {config.label}
                </MenuItem>
              ))}
            </Select>
          </FormControl>
          <FormControl size="small" sx={{ minWidth: 150 }}>
            <InputLabel>類型</InputLabel>
            <Select value={filterType} label="類型" onChange={(e) => setFilterType(e.target.value)}>
              <MenuItem value="all">全部</MenuItem>
              {Object.entries(typeConfig).map(([key, config]) => (
                <MenuItem key={key} value={key}>
                  {config.label}
                </MenuItem>
              ))}
            </Select>
          </FormControl>
        </Box>
      </Paper>

      {/* 警示列表 */}
      {filteredAlerts.length === 0 ? (
        <Paper sx={{ p: 4, textAlign: 'center' }}>
          <CheckCircleIcon sx={{ fontSize: 48, color: 'success.main', mb: 2 }} />
          <Typography color="text.secondary">沒有符合條件的警示</Typography>
        </Paper>
      ) : (
        <Grid container spacing={2}>
          {filteredAlerts.map((alert) => (
            <Grid size={{ xs: 12 }} key={alert.id}>
              <Card
                sx={{
                  borderLeft: 6,
                  borderColor: severityConfig[alert.severity].bgcolor,
                }}
              >
                <CardContent>
                  <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', mb: 2 }}>
                    <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
                      <Avatar sx={{ bgcolor: severityConfig[alert.severity].bgcolor }}>
                        {typeConfig[alert.type].icon}
                      </Avatar>
                      <Box>
                        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 0.5 }}>
                          <Typography variant="h6">{alert.title}</Typography>
                          <Chip
                            size="small"
                            label={severityConfig[alert.severity].label}
                            color={severityConfig[alert.severity].color}
                          />
                          <Chip
                            size="small"
                            label={statusConfig[alert.status].label}
                            color={statusConfig[alert.status].color}
                            variant="outlined"
                          />
                        </Box>
                        <Typography variant="body2" color="text.secondary">
                          {alert.residentName} · {typeConfig[alert.type].label} · {formatTime(alert.createdAt)}
                        </Typography>
                      </Box>
                    </Box>
                  </Box>

                  <Typography variant="body1" sx={{ mb: 2 }}>
                    {alert.message}
                  </Typography>

                  {alert.sourceText && (
                    <Paper sx={{ p: 1.5, bgcolor: (theme) => theme.palette.mode === 'dark' ? 'rgba(30, 41, 59, 0.8)' : 'grey.100', mb: 2 }}>
                      <Typography variant="caption" color="text.secondary">
                        原始語句：
                      </Typography>
                      <Typography variant="body2" sx={{ fontStyle: 'italic' }}>
                        「{alert.sourceText}」
                      </Typography>
                    </Paper>
                  )}

                  {alert.resolution && (
                    <Alert severity="success" sx={{ mb: 2 }}>
                      <Typography variant="body2">
                        <strong>處理結果：</strong>
                        {alert.resolution}
                      </Typography>
                      <Typography variant="caption" color="text.secondary">
                        由 {alert.resolvedBy} 於 {alert.resolvedAt?.toLocaleString('zh-TW')} 處理
                      </Typography>
                    </Alert>
                  )}
                </CardContent>

                <CardActions sx={{ justifyContent: 'space-between', px: 2, pb: 2 }}>
                  <Button
                    size="small"
                    startIcon={<VisibilityIcon />}
                    onClick={() => router.push(`/caregiver/resident?id=${alert.residentId}`)}
                  >
                    查看住民
                  </Button>
                  <Box sx={{ display: 'flex', gap: 1 }}>
                    {alert.status === 'active' && (
                      <>
                        <Button
                          size="small"
                          variant="outlined"
                          color="warning"
                          startIcon={<DoneIcon />}
                          onClick={() => handleAction(alert, 'acknowledge')}
                        >
                          確認
                        </Button>
                        <Button
                          size="small"
                          variant="contained"
                          color="success"
                          startIcon={<CheckCircleIcon />}
                          onClick={() => handleAction(alert, 'resolve')}
                        >
                          解決
                        </Button>
                        <Tooltip title="忽略">
                          <IconButton size="small" onClick={() => handleAction(alert, 'dismiss')}>
                            <CloseIcon />
                          </IconButton>
                        </Tooltip>
                      </>
                    )}
                    {alert.status === 'acknowledged' && (
                      <Button
                        size="small"
                        variant="contained"
                        color="success"
                        startIcon={<CheckCircleIcon />}
                        onClick={() => handleAction(alert, 'resolve')}
                      >
                        標記解決
                      </Button>
                    )}
                  </Box>
                </CardActions>
              </Card>
            </Grid>
          ))}
        </Grid>
      )}

      {/* 操作對話框 */}
      <Dialog open={actionDialogOpen} onClose={() => setActionDialogOpen(false)} maxWidth="sm" fullWidth>
        <DialogTitle>
          {actionType === 'acknowledge' && '確認警示'}
          {actionType === 'resolve' && '解決警示'}
          {actionType === 'dismiss' && '忽略警示'}
        </DialogTitle>
        <DialogContent>
          {selectedAlert && (
            <Box sx={{ mb: 2 }}>
              <Typography variant="subtitle1" sx={{ fontWeight: 'bold' }}>
                {selectedAlert.title}
              </Typography>
              <Typography variant="body2" color="text.secondary">
                {selectedAlert.residentName} · {selectedAlert.message}
              </Typography>
            </Box>
          )}

          {actionType === 'resolve' && (
            <TextField
              label="處理結果說明"
              fullWidth
              multiline
              rows={3}
              value={resolution}
              onChange={(e) => setResolution(e.target.value)}
              placeholder="請描述處理過程與結果..."
              sx={{ mt: 2 }}
            />
          )}

          {actionType === 'dismiss' && (
            <Alert severity="warning">
              忽略此警示後，將不會再顯示於待處理列表。請確認此警示不需要進一步處理。
            </Alert>
          )}
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setActionDialogOpen(false)}>取消</Button>
          <Button
            variant="contained"
            color={actionType === 'dismiss' ? 'warning' : actionType === 'resolve' ? 'success' : 'primary'}
            onClick={confirmAction}
            disabled={actionType === 'resolve' && !resolution.trim()}
          >
            確認
          </Button>
        </DialogActions>
      </Dialog>
    </Container>
  );
}
