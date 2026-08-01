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
import ContactPhoneIcon from '@mui/icons-material/ContactPhone';
import LocalHospitalIcon from '@mui/icons-material/LocalHospital';
import MonitorHeartIcon from '@mui/icons-material/MonitorHeart';
import RestaurantMenuIcon from '@mui/icons-material/RestaurantMenu';

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

// 健康資訊類型
interface HealthInfo {
  // 生理監測
  vitals: {
    bloodPressure?: string;    // 血壓
    bloodSugar?: number;       // 血糖 mg/dL
    temperature?: number;      // 體溫
    pulse?: number;            // 脈搏
    lastMeasuredAt?: Date;     // 最後量測時間
  };
  // 病史與用藥
  medicalHistory: {
    chronicConditions: string[];  // 慢性病
    allergies: string[];          // 過敏史
    currentMedications: string[]; // 目前用藥
  };
  // 生活方式
  lifestyle: {
    dietPreference?: string;      // 飲食偏好
    exerciseRoutine?: string;     // 運動習慣
    sleepPattern?: string;        // 睡眠模式
    specialNotes?: string;        // 特殊備註
  };
  // 緊急聯絡
  emergency: {
    contactName?: string;         // 緊急聯絡人
    contactPhone?: string;        // 聯絡電話
    insurance?: string;           // 保險資訊
    careNotes?: string;           // 照護注意事項
  };
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

// 模擬健康資訊資料
const mockHealthInfo: Record<string, HealthInfo> = {
  p1: {
    vitals: {
      bloodPressure: '125/80 mmHg',
      bloodSugar: 98,
      temperature: 36.5,
      pulse: 72,
      lastMeasuredAt: new Date('2026-08-01T08:00:00'),
    },
    medicalHistory: {
      chronicConditions: ['高血壓', '輕度糖尿病'],
      allergies: ['青黴素'],
      currentMedications: ['降血壓藥 (每日早上)', '血糖控制藥 (每餐前)'],
    },
    lifestyle: {
      dietPreference: '低鈉、低糖飲食',
      exerciseRoutine: '每日散步 30 分鐘',
      sleepPattern: '平均 7 小時，偶有失眠',
      specialNotes: '喜歡溫熱的食物',
    },
    emergency: {
      contactName: '王小明 (兒子)',
      contactPhone: '0912-345-678',
      insurance: '全民健保 + 商業醫療險',
      careNotes: '行動需扶助，使用助行器',
    },
  },
  p2: {
    vitals: {
      bloodPressure: '130/85 mmHg',
      bloodSugar: 105,
      temperature: 36.3,
      pulse: 68,
      lastMeasuredAt: new Date('2026-08-01T08:30:00'),
    },
    medicalHistory: {
      chronicConditions: ['心臟病', '高血壓'],
      allergies: [],
      currentMedications: ['心臟藥物 (每日早晚)', '降血壓藥 (每日早上)'],
    },
    lifestyle: {
      dietPreference: '低脂飲食',
      exerciseRoutine: '室內輕度活動',
      sleepPattern: '平均 6 小時，午休 1 小時',
      specialNotes: '避免劇烈運動',
    },
    emergency: {
      contactName: '李小華 (女兒)',
      contactPhone: '0923-456-789',
      insurance: '全民健保',
      careNotes: '心臟病患者，需定期監測',
    },
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
  const [selectedPersona, setSelectedPersona] = useState<string>(mockPersonas[0]?.id ?? '');
  const [tabValue, setTabValue] = useState(0);
  const [switchDialogOpen, setSwitchDialogOpen] = useState(false);

  const currentPersona = mockPersonas.find((p) => p.id === selectedPersona);
  const currentStats = mockStats[selectedPersona];
  const currentHealthInfo = mockHealthInfo[selectedPersona];

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
          <Grid size={{ xs: 12, md: 4 }}>
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
          <Grid size={{ xs: 12, md: 8 }}>
            <Grid container spacing={2}>
              <Grid size={{ xs: 6, sm: 3 }}>
                <Typography variant="body2" color="text.secondary">
                  總事件數
                </Typography>
                <Typography variant="h5">{currentStats.totalEvents}</Typography>
              </Grid>
              <Grid size={{ xs: 6, sm: 3 }}>
                <Typography variant="body2" color="text.secondary">
                  今日事件
                </Typography>
                <Typography variant="h5">{currentStats.todayEvents}</Typography>
              </Grid>
              <Grid size={{ xs: 6, sm: 3 }}>
                <Typography variant="body2" color="text.secondary">
                  待處理提醒
                </Typography>
                <Typography variant="h5">{currentStats.pendingReminders}</Typography>
              </Grid>
              <Grid size={{ xs: 6, sm: 3 }}>
                <Typography variant="body2" color="text.secondary">
                  情緒趨勢
                </Typography>
                <Chip
                  label={moodTrendConfig[currentStats.moodTrend]?.label ?? currentStats.moodTrend}
                  color={moodTrendConfig[currentStats.moodTrend]?.color ?? 'default'}
                />
              </Grid>
            </Grid>
          </Grid>
        </Grid>
      </Paper>

      {/* 分頁內容 */}
      <Paper sx={{ mb: 2 }}>
        <Tabs value={tabValue} onChange={(_, v) => setTabValue(v)} variant="scrollable" scrollButtons="auto">
          <Tab label="個人資料" />
          <Tab label="健康資訊" />
          <Tab label="日常作息" />
          <Tab label="最近動態" />
          <Tab label="Persona 設定" />
        </Tabs>
      </Paper>

      {/* 個人資料 */}
      {tabValue === 0 && (
        <Grid container spacing={3}>
          <Grid size={{ xs: 12, md: 6 }}>
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
          <Grid size={{ xs: 12, md: 6 }}>
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

      {/* 健康資訊 */}
      {tabValue === 1 && currentHealthInfo && (
        <Grid container spacing={3}>
          {/* 生理監測 */}
          <Grid size={{ xs: 12, md: 6 }}>
            <Card>
              <CardContent>
                <Typography variant="h6" gutterBottom>
                  <MonitorHeartIcon sx={{ mr: 1, verticalAlign: 'middle' }} color="error" />
                  生理監測
                </Typography>
                <List dense>
                  <ListItem>
                    <ListItemText primary="血壓" secondary={currentHealthInfo.vitals.bloodPressure || '無紀錄'} />
                  </ListItem>
                  <ListItem>
                    <ListItemText primary="血糖" secondary={currentHealthInfo.vitals.bloodSugar ? `${currentHealthInfo.vitals.bloodSugar} mg/dL` : '無紀錄'} />
                  </ListItem>
                  <ListItem>
                    <ListItemText primary="體溫" secondary={currentHealthInfo.vitals.temperature ? `${currentHealthInfo.vitals.temperature}°C` : '無紀錄'} />
                  </ListItem>
                  <ListItem>
                    <ListItemText primary="脈搏" secondary={currentHealthInfo.vitals.pulse ? `${currentHealthInfo.vitals.pulse} bpm` : '無紀錄'} />
                  </ListItem>
                  <ListItem>
                    <ListItemText
                      primary="最後量測"
                      secondary={currentHealthInfo.vitals.lastMeasuredAt?.toLocaleString('zh-TW') || '無紀錄'}
                    />
                  </ListItem>
                </List>
              </CardContent>
            </Card>
          </Grid>

          {/* 病史與用藥 */}
          <Grid size={{ xs: 12, md: 6 }}>
            <Card>
              <CardContent>
                <Typography variant="h6" gutterBottom>
                  <LocalHospitalIcon sx={{ mr: 1, verticalAlign: 'middle' }} color="primary" />
                  病史與用藥
                </Typography>
                <List dense>
                  <ListItem>
                    <ListItemText
                      primary="慢性病"
                      secondary={currentHealthInfo.medicalHistory.chronicConditions.length > 0
                        ? currentHealthInfo.medicalHistory.chronicConditions.join('、')
                        : '無'}
                    />
                  </ListItem>
                  <ListItem>
                    <ListItemText
                      primary="過敏史"
                      secondary={currentHealthInfo.medicalHistory.allergies.length > 0
                        ? currentHealthInfo.medicalHistory.allergies.join('、')
                        : '無'}
                    />
                  </ListItem>
                  <ListItem>
                    <ListItemText
                      primary="目前用藥"
                      secondary={currentHealthInfo.medicalHistory.currentMedications.length > 0
                        ? currentHealthInfo.medicalHistory.currentMedications.join('、')
                        : '無'}
                    />
                  </ListItem>
                </List>
              </CardContent>
            </Card>
          </Grid>

          {/* 生活方式 */}
          <Grid size={{ xs: 12, md: 6 }}>
            <Card>
              <CardContent>
                <Typography variant="h6" gutterBottom>
                  <RestaurantMenuIcon sx={{ mr: 1, verticalAlign: 'middle' }} color="success" />
                  生活方式
                </Typography>
                <List dense>
                  <ListItem>
                    <ListItemText primary="飲食偏好" secondary={currentHealthInfo.lifestyle.dietPreference || '無紀錄'} />
                  </ListItem>
                  <ListItem>
                    <ListItemText primary="運動習慣" secondary={currentHealthInfo.lifestyle.exerciseRoutine || '無紀錄'} />
                  </ListItem>
                  <ListItem>
                    <ListItemText primary="睡眠模式" secondary={currentHealthInfo.lifestyle.sleepPattern || '無紀錄'} />
                  </ListItem>
                  <ListItem>
                    <ListItemText primary="特殊備註" secondary={currentHealthInfo.lifestyle.specialNotes || '無紀錄'} />
                  </ListItem>
                </List>
              </CardContent>
            </Card>
          </Grid>

          {/* 緊急/行政資料 */}
          <Grid size={{ xs: 12, md: 6 }}>
            <Card>
              <CardContent>
                <Typography variant="h6" gutterBottom>
                  <ContactPhoneIcon sx={{ mr: 1, verticalAlign: 'middle' }} color="warning" />
                  緊急/行政資料
                </Typography>
                <List dense>
                  <ListItem>
                    <ListItemText primary="緊急聯絡人" secondary={currentHealthInfo.emergency.contactName || '無紀錄'} />
                  </ListItem>
                  <ListItem>
                    <ListItemText primary="聯絡電話" secondary={currentHealthInfo.emergency.contactPhone || '無紀錄'} />
                  </ListItem>
                  <ListItem>
                    <ListItemText primary="保險資訊" secondary={currentHealthInfo.emergency.insurance || '無紀錄'} />
                  </ListItem>
                  <ListItem>
                    <ListItemText primary="照護注意事項" secondary={currentHealthInfo.emergency.careNotes || '無紀錄'} />
                  </ListItem>
                </List>
              </CardContent>
            </Card>
          </Grid>
        </Grid>
      )}

      {/* 日常作息 */}
      {tabValue === 2 && (
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
      {tabValue === 3 && (
        <Grid container spacing={3}>
          <Grid size={{ xs: 12, md: 6 }}>
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
          <Grid size={{ xs: 12, md: 6 }}>
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
          <Grid size={{ xs: 12 }}>
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
      {tabValue === 4 && (
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
