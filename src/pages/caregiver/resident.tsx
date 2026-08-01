'use client';
import React, { useState } from 'react';
import {
  Container,
  Typography,
  Box,
  Paper,
  Grid,
  Card,
  CardContent,
  Avatar,
  Chip,
  Tabs,
  Tab,
  List,
  ListItem,
  ListItemIcon,
  ListItemText,
  Divider,
  Button,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Alert,
} from '@mui/material';
import PersonIcon from '@mui/icons-material/Person';
import MedicationIcon from '@mui/icons-material/Medication';
import DirectionsWalkIcon from '@mui/icons-material/DirectionsWalk';
import RestaurantIcon from '@mui/icons-material/Restaurant';
import FavoriteIcon from '@mui/icons-material/Favorite';
import EventIcon from '@mui/icons-material/Event';
import NotificationsActiveIcon from '@mui/icons-material/NotificationsActive';
import HistoryIcon from '@mui/icons-material/History';
import SwapHorizIcon from '@mui/icons-material/SwapHoriz';

// Persona 類型
interface Persona {
  id: string;
  displayName: string;
  avatar?: string;
  preferredLanguage: string;
  responseStyle: 'formal' | 'casual' | 'caring';
  interests: string[];
  routine: string[];
  memoryNamespace: string;
  status: 'active' | 'inactive';
  createdAt: Date;
  lastInteractionAt?: Date;
}

// 統計資料
interface ResidentStats {
  totalEvents: number;
  todayEvents: number;
  pendingReminders: number;
  lastMedication?: string;
  lastActivity?: string;
  moodTrend: 'positive' | 'neutral' | 'negative';
}

// 模擬 Persona 資料
const mockPersonas: Persona[] = [
  {
    id: 'p1',
    displayName: '王奶奶',
    preferredLanguage: 'zh-TW',
    responseStyle: 'caring',
    interests: ['園藝', '看電視劇', '與孫子聊天'],
    routine: ['早上 6:30 起床', '早上 8:00 服藥', '下午 3:00 散步', '晚上 9:00 就寢'],
    memoryNamespace: 'persona_p1',
    status: 'active',
    createdAt: new Date('2026-01-15'),
    lastInteractionAt: new Date('2026-08-01T14:30:00'),
  },
  {
    id: 'p2',
    displayName: '李爺爺',
    preferredLanguage: 'zh-TW',
    responseStyle: 'formal',
    interests: ['下棋', '看報紙', '聽廣播'],
    routine: ['早上 7:00 起床', '早上 8:30 服藥', '下午 2:00 午休', '晚上 10:00 就寢'],
    memoryNamespace: 'persona_p2',
    status: 'active',
    createdAt: new Date('2026-02-20'),
    lastInteractionAt: new Date('2026-08-01T10:15:00'),
  },
];

// 模擬統計資料
const mockStats: Record<string, ResidentStats> = {
  p1: {
    totalEvents: 156,
    todayEvents: 5,
    pendingReminders: 2,
    lastMedication: '今天 08:00 降血壓藥',
    lastActivity: '今天 10:00 散步 30 分鐘',
    moodTrend: 'positive',
  },
  p2: {
    totalEvents: 98,
    todayEvents: 3,
    pendingReminders: 1,
    lastMedication: '今天 08:30 心臟藥物',
    lastActivity: '今天 09:00 室內活動',
    moodTrend: 'neutral',
  },
};

// 回應風格配置
const responseStyleConfig: Record<string, string> = {
  formal: '正式',
  casual: '輕鬆',
  caring: '關懷',
};

// 情緒趨勢配置
const moodTrendConfig: Record<string, { label: string; color: 'success' | 'warning' | 'error' }> = {
  positive: { label: '正向', color: 'success' },
  neutral: { label: '平穩', color: 'warning' },
  negative: { label: '低落', color: 'error' },
};

export default function ResidentDetail() {
  const [selectedPersona, setSelectedPersona] = useState<string>(mockPersonas[0].id);
  const [tabValue, setTabValue] = useState(0);
  const [switchDialogOpen, setSwitchDialogOpen] = useState(false);

  const currentPersona = mockPersonas.find((p) => p.id === selectedPersona);
  const currentStats = mockStats[selectedPersona];

  // 切換 Persona
  const handleSwitchPersona = (personaId: string) => {
    setSelectedPersona(personaId);
    setSwitchDialogOpen(false);
  };

  if (!currentPersona || !currentStats) {
    return (
      <Container>
        <Alert severity="error">找不到住民資料</Alert>
      </Container>
    );
  }

  return (
    <Container maxWidth="lg" sx={{ py: 2 }}>
      {/* 標題與切換按鈕 */}
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
        <Typography variant="h4" sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
          <PersonIcon color="primary" />
          住民詳情
        </Typography>
        <Button
          variant="outlined"
          startIcon={<SwapHorizIcon />}
          onClick={() => setSwitchDialogOpen(true)}
        >
          切換住民
        </Button>
      </Box>

      {/* 住民基本資訊卡片 */}
      <Paper sx={{ p: 3, mb: 3 }}>
        <Grid container spacing={3}>
          <Grid item xs={12} md={4}>
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
              <Avatar sx={{ width: 80, height: 80, fontSize: 32 }}>
                {currentPersona.displayName[0]}
              </Avatar>
              <Box>
                <Typography variant="h5">{currentPersona.displayName}</Typography>
                <Chip
                  size="small"
                  label={currentPersona.status === 'active' ? '活躍' : '非活躍'}
                  color={currentPersona.status === 'active' ? 'success' : 'default'}
                  sx={{ mt: 0.5 }}
                />
              </Box>
            </Box>
          </Grid>
          <Grid item xs={12} md={8}>
            <Grid container spacing={2}>
              <Grid item xs={6} sm={3}>
                <Typography variant="body2" color="text.secondary">
                  總事件數
                </Typography>
                <Typography variant="h5">{currentStats.totalEvents}</Typography>
              </Grid>
              <Grid item xs={6} sm={3}>
                <Typography variant="body2" color="text.secondary">
                  今日事件
                </Typography>
                <Typography variant="h5">{currentStats.todayEvents}</Typography>
              </Grid>
              <Grid item xs={6} sm={3}>
                <Typography variant="body2" color="text.secondary">
                  待處理提醒
                </Typography>
                <Typography variant="h5">{currentStats.pendingReminders}</Typography>
              </Grid>
              <Grid item xs={6} sm={3}>
                <Typography variant="body2" color="text.secondary">
                  情緒趨勢
                </Typography>
                <Chip
                  label={moodTrendConfig[currentStats.moodTrend].label}
                  color={moodTrendConfig[currentStats.moodTrend].color}
                />
              </Grid>
            </Grid>
          </Grid>
        </Grid>
      </Paper>

      {/* 分頁內容 */}
      <Paper sx={{ mb: 2 }}>
        <Tabs value={tabValue} onChange={(_, v) => setTabValue(v)}>
          <Tab label="個人資料" />
          <Tab label="日常作息" />
          <Tab label="最近動態" />
          <Tab label="Persona 設定" />
        </Tabs>
      </Paper>

      {/* 個人資料 */}
      {tabValue === 0 && (
        <Grid container spacing={3}>
          <Grid item xs={12} md={6}>
            <Card>
              <CardContent>
                <Typography variant="h6" gutterBottom>
                  <FavoriteIcon sx={{ mr: 1, verticalAlign: 'middle' }} />
                  興趣愛好
                </Typography>
                <Box sx={{ display: 'flex', gap: 1, flexWrap: 'wrap' }}>
                  {currentPersona.interests.map((interest, idx) => (
                    <Chip key={idx} label={interest} variant="outlined" />
                  ))}
                </Box>
              </CardContent>
            </Card>
          </Grid>
          <Grid item xs={12} md={6}>
            <Card>
              <CardContent>
                <Typography variant="h6" gutterBottom>
                  <EventIcon sx={{ mr: 1, verticalAlign: 'middle' }} />
                  重要資訊
                </Typography>
                <List dense>
                  <ListItem>
                    <ListItemText primary="語言偏好" secondary={currentPersona.preferredLanguage} />
                  </ListItem>
                  <ListItem>
                    <ListItemText primary="回應風格" secondary={responseStyleConfig[currentPersona.responseStyle]} />
                  </ListItem>
                  <ListItem>
                    <ListItemText
                      primary="最後互動"
                      secondary={
                        currentPersona.lastInteractionAt
                          ? currentPersona.lastInteractionAt.toLocaleString('zh-TW')
                          : '尚無紀錄'
                      }
                    />
                  </ListItem>
                </List>
              </CardContent>
            </Card>
          </Grid>
        </Grid>
      )}

      {/* 日常作息 */}
      {tabValue === 1 && (
        <Card>
          <CardContent>
            <Typography variant="h6" gutterBottom>
              <HistoryIcon sx={{ mr: 1, verticalAlign: 'middle' }} />
              日常作息
            </Typography>
            <List>
              {currentPersona.routine.map((item, idx) => (
                <React.Fragment key={idx}>
                  <ListItem>
                    <ListItemIcon>
                      {item.includes('服藥') ? (
                        <MedicationIcon color="error" />
                      ) : item.includes('散步') ? (
                        <DirectionsWalkIcon color="success" />
                      ) : (
                        <EventIcon color="action" />
                      )}
                    </ListItemIcon>
                    <ListItemText primary={item} />
                  </ListItem>
                  {idx < currentPersona.routine.length - 1 && <Divider />}
                </React.Fragment>
              ))}
            </List>
          </CardContent>
        </Card>
      )}

      {/* 最近動態 */}
      {tabValue === 2 && (
        <Grid container spacing={3}>
          <Grid item xs={12} md={6}>
            <Card>
              <CardContent>
                <Typography variant="h6" gutterBottom>
                  <MedicationIcon sx={{ mr: 1, verticalAlign: 'middle' }} color="error" />
                  最近用藥
                </Typography>
                <Typography variant="body1">{currentStats.lastMedication || '無紀錄'}</Typography>
              </CardContent>
            </Card>
          </Grid>
          <Grid item xs={12} md={6}>
            <Card>
              <CardContent>
                <Typography variant="h6" gutterBottom>
                  <DirectionsWalkIcon sx={{ mr: 1, verticalAlign: 'middle' }} color="success" />
                  最近活動
                </Typography>
                <Typography variant="body1">{currentStats.lastActivity || '無紀錄'}</Typography>
              </CardContent>
            </Card>
          </Grid>
          <Grid item xs={12}>
            <Card>
              <CardContent>
                <Typography variant="h6" gutterBottom>
                  <NotificationsActiveIcon sx={{ mr: 1, verticalAlign: 'middle' }} color="warning" />
                  待處理提醒
                </Typography>
                {currentStats.pendingReminders > 0 ? (
                  <Alert severity="info">有 {currentStats.pendingReminders} 個提醒待處理</Alert>
                ) : (
                  <Typography color="text.secondary">沒有待處理的提醒</Typography>
                )}
              </CardContent>
            </Card>
          </Grid>
        </Grid>
      )}

      {/* Persona 設定 */}
      {tabValue === 3 && (
        <Card>
          <CardContent>
            <Typography variant="h6" gutterBottom>
              Persona 技術資訊
            </Typography>
            <Alert severity="info" sx={{ mb: 2 }}>
              Persona 切換會同步切換系統提示詞、可用工具、記憶命名空間與資料範圍。
            </Alert>
            <List>
              <ListItem>
                <ListItemText primary="Persona ID" secondary={currentPersona.id} />
              </ListItem>
              <ListItem>
                <ListItemText primary="記憶命名空間" secondary={currentPersona.memoryNamespace} />
              </ListItem>
              <ListItem>
                <ListItemText
                  primary="建立時間"
                  secondary={currentPersona.createdAt.toLocaleDateString('zh-TW')}
                />
              </ListItem>
            </List>
          </CardContent>
        </Card>
      )}

      {/* Persona 切換對話框 */}
      <Dialog open={switchDialogOpen} onClose={() => setSwitchDialogOpen(false)}>
        <DialogTitle>切換住民 (Persona)</DialogTitle>
        <DialogContent>
          <Alert severity="warning" sx={{ mb: 2 }}>
            切換住民將結束目前的對話 Session，並清除前一位住民的上下文，避免資訊殘留。
          </Alert>
          <FormControl fullWidth sx={{ mt: 1 }}>
            <InputLabel>選擇住民</InputLabel>
            <Select
              value={selectedPersona}
              label="選擇住民"
              onChange={(e) => handleSwitchPersona(e.target.value)}
            >
              {mockPersonas.map((persona) => (
                <MenuItem key={persona.id} value={persona.id}>
                  {persona.displayName}
                  {persona.status === 'active' && (
                    <Chip size="small" label="活躍" color="success" sx={{ ml: 1 }} />
                  )}
                </MenuItem>
              ))}
            </Select>
          </FormControl>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setSwitchDialogOpen(false)}>取消</Button>
        </DialogActions>
      </Dialog>
    </Container>
  );
}
