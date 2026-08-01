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
  Avatar,
  Chip,
  Button,
  TextField,
  InputAdornment,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  IconButton,
  Tooltip,
  Badge,
  Fade,
  Grow,
  Skeleton,
  LinearProgress,
} from '@mui/material';
import Grid from '@mui/material/Grid';
import { useTheme, alpha } from '@mui/material/styles';
import PeopleIcon from '@mui/icons-material/People';
import SearchIcon from '@mui/icons-material/Search';
import PersonIcon from '@mui/icons-material/Person';
import MoodIcon from '@mui/icons-material/Mood';
import MedicationIcon from '@mui/icons-material/Medication';
import DirectionsWalkIcon from '@mui/icons-material/DirectionsWalk';
import NotificationsActiveIcon from '@mui/icons-material/NotificationsActive';
import WarningIcon from '@mui/icons-material/Warning';
import AccessTimeIcon from '@mui/icons-material/AccessTime';
import VisibilityIcon from '@mui/icons-material/Visibility';
import RecordVoiceOverIcon from '@mui/icons-material/RecordVoiceOver';
import TrendingUpIcon from '@mui/icons-material/TrendingUp';
import TrendingDownIcon from '@mui/icons-material/TrendingDown';
import TrendingFlatIcon from '@mui/icons-material/TrendingFlat';
import { useRouter } from 'next/router';

// 住民狀態類型
type ResidentStatus = 'active' | 'inactive' | 'alert';
type MoodTrend = 'positive' | 'neutral' | 'negative';

// 住民資料
interface Resident {
  id: string;
  name: string;
  avatar?: string;
  status: ResidentStatus;
  moodTrend: MoodTrend;
  lastInteraction?: Date;
  todayEvents: number;
  pendingReminders: number;
  hasAlert: boolean;
  lastMedication?: string;
  lastActivity?: string;
}

// 狀態配置
const statusConfig: Record<ResidentStatus, { label: string; color: 'success' | 'default' | 'error' }> = {
  active: { label: '活躍', color: 'success' },
  inactive: { label: '非活躍', color: 'default' },
  alert: { label: '需關注', color: 'error' },
};

const moodConfig: Record<MoodTrend, { label: string; color: 'success' | 'warning' | 'error'; icon: React.ReactNode }> = {
  positive: { label: '良好', color: 'success', icon: <TrendingUpIcon /> },
  neutral: { label: '平穩', color: 'warning', icon: <TrendingFlatIcon /> },
  negative: { label: '低落', color: 'error', icon: <TrendingDownIcon /> },
};

// 模擬住民資料
const mockResidents: Resident[] = [
  {
    id: 'r1',
    name: '王奶奶',
    status: 'active',
    moodTrend: 'positive',
    lastInteraction: new Date('2026-08-01T14:30:00'),
    todayEvents: 5,
    pendingReminders: 2,
    hasAlert: false,
    lastMedication: '08:00 降血壓藥',
    lastActivity: '10:00 散步 30 分鐘',
  },
  {
    id: 'r2',
    name: '李爺爺',
    status: 'alert',
    moodTrend: 'neutral',
    lastInteraction: new Date('2026-08-01T10:15:00'),
    todayEvents: 3,
    pendingReminders: 1,
    hasAlert: true,
    lastMedication: '08:30 心臟藥物',
    lastActivity: '09:00 室內活動',
  },
  {
    id: 'r3',
    name: '張奶奶',
    status: 'active',
    moodTrend: 'positive',
    lastInteraction: new Date('2026-08-01T12:00:00'),
    todayEvents: 4,
    pendingReminders: 0,
    hasAlert: false,
    lastMedication: '07:30 血糖藥',
    lastActivity: '11:00 園藝活動',
  },
  {
    id: 'r4',
    name: '陳爺爺',
    status: 'inactive',
    moodTrend: 'negative',
    lastInteraction: new Date('2026-07-31T16:00:00'),
    todayEvents: 1,
    pendingReminders: 3,
    hasAlert: false,
    lastMedication: '昨日 18:00',
    lastActivity: '昨日 15:00',
  },
];

export default function ResidentList() {
  const theme = useTheme();
  const router = useRouter();
  const [searchText, setSearchText] = useState('');
  const [filterStatus, setFilterStatus] = useState<string>('all');
  const [filterMood, setFilterMood] = useState<string>('all');
  const [hoveredCard, setHoveredCard] = useState<string | null>(null);

  // 篩選住民
  const filteredResidents = mockResidents
    .filter((r) => filterStatus === 'all' || r.status === filterStatus)
    .filter((r) => filterMood === 'all' || r.moodTrend === filterMood)
    .filter((r) => !searchText || r.name.toLowerCase().includes(searchText.toLowerCase()));

  // 統計
  const stats = {
    total: mockResidents.length,
    active: mockResidents.filter((r) => r.status === 'active').length,
    alerts: mockResidents.filter((r) => r.hasAlert).length,
    pendingReminders: mockResidents.reduce((sum, r) => sum + r.pendingReminders, 0),
  };

  // 格式化時間
  const formatTime = (date?: Date) => {
    if (!date) return '無紀錄';
    const now = new Date();
    const diff = now.getTime() - date.getTime();
    const hours = Math.floor(diff / (1000 * 60 * 60));
    if (hours < 1) return '剛剛';
    if (hours < 24) return `${hours} 小時前`;
    return date.toLocaleDateString('zh-TW');
  };

  // 統計卡片元件
  const StatCard = ({ 
    value, 
    label, 
    color, 
    icon,
    delay 
  }: { 
    value: number; 
    label: string; 
    color: string; 
    icon: React.ReactNode;
    delay: number;
  }) => (
    <Grow in timeout={400 + delay}>
      <Paper 
        sx={{ 
          p: 2.5, 
          textAlign: 'center',
          background: `linear-gradient(135deg, ${alpha(color, 0.1)} 0%, ${alpha(color, 0.05)} 100%)`,
          border: `1px solid ${alpha(color, 0.2)}`,
          transition: 'all 0.3s ease',
          cursor: 'default',
          '&:hover': {
            transform: 'translateY(-4px)',
            boxShadow: `0 8px 24px ${alpha(color, 0.2)}`,
          },
        }}
      >
        <Box sx={{ 
          display: 'flex', 
          alignItems: 'center', 
          justifyContent: 'center',
          mb: 1,
          color: color,
        }}>
          {icon}
        </Box>
        <Typography 
          variant="h3" 
          sx={{ 
            fontWeight: 700,
            color: color,
            lineHeight: 1,
          }}
        >
          {value}
        </Typography>
        <Typography variant="body2" color="text.secondary" sx={{ mt: 0.5 }}>
          {label}
        </Typography>
      </Paper>
    </Grow>
  );

  return (
    <Container maxWidth="lg" sx={{ py: 3 }}>
      {/* 頁面標題 */}
      <Fade in timeout={300}>
        <Box sx={{ mb: 4 }}>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, mb: 1 }}>
            <Avatar 
              sx={{ 
                bgcolor: theme.palette.primary.main,
                width: 48,
                height: 48,
              }}
            >
              <PeopleIcon sx={{ fontSize: 28 }} />
            </Avatar>
            <Box>
              <Typography variant="h4" fontWeight={700}>
                住民列表
              </Typography>
              <Typography variant="body2" color="text.secondary">
                管理與追蹤所有住民的照護狀況
              </Typography>
            </Box>
          </Box>
        </Box>
      </Fade>

      {/* 統計卡片 */}
      <Grid container spacing={2} sx={{ mb: 4 }}>
        <Grid item xs={6} sm={3}>
          <StatCard 
            value={stats.total} 
            label="總住民數" 
            color={theme.palette.primary.main}
            icon={<PeopleIcon />}
            delay={0}
          />
        </Grid>
        <Grid item xs={6} sm={3}>
          <StatCard 
            value={stats.active} 
            label="今日活躍" 
            color={theme.palette.success.main}
            icon={<TrendingUpIcon />}
            delay={100}
          />
        </Grid>
        <Grid item xs={6} sm={3}>
          <StatCard 
            value={stats.alerts} 
            label="待處理警示" 
            color={theme.palette.error.main}
            icon={<WarningIcon />}
            delay={200}
          />
        </Grid>
        <Grid item xs={6} sm={3}>
          <StatCard 
            value={stats.pendingReminders} 
            label="待執行提醒" 
            color={theme.palette.warning.main}
            icon={<NotificationsActiveIcon />}
            delay={300}
          />
        </Grid>
      </Grid>

      {/* 搜尋與篩選 */}
      <Fade in timeout={500}>
        <Paper sx={{ p: { xs: 2, sm: 2.5 }, mb: { xs: 2, sm: 3 } }}>
          <Box sx={{ display: 'flex', gap: 2, flexWrap: 'wrap', alignItems: 'center' }}>
            <TextField
              size="small"
              placeholder="搜尋住民姓名"
              value={searchText}
              onChange={(e) => setSearchText(e.target.value)}
              sx={{ minWidth: 220, flex: { xs: '1 1 100%', sm: '0 1 auto' } }}
              slotProps={{
                input: {
                  startAdornment: (
                    <InputAdornment position="start">
                      <SearchIcon color="action" />
                    </InputAdornment>
                  ),
                },
              }}
            />
            <FormControl size="small" sx={{ minWidth: 120 }}>
              <InputLabel>狀態</InputLabel>
              <Select value={filterStatus} label="狀態" onChange={(e) => setFilterStatus(e.target.value)}>
                <MenuItem value="all">全部</MenuItem>
                {Object.entries(statusConfig).map(([key, config]) => (
                  <MenuItem key={key} value={key}>
                    <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                      <Box 
                        sx={{ 
                          width: 8, 
                          height: 8, 
                          borderRadius: '50%',
                          bgcolor: `${config.color}.main`,
                        }} 
                      />
                      {config.label}
                    </Box>
                  </MenuItem>
                ))}
              </Select>
            </FormControl>
            <FormControl size="small" sx={{ minWidth: 120 }}>
              <InputLabel>情緒</InputLabel>
              <Select value={filterMood} label="情緒" onChange={(e) => setFilterMood(e.target.value)}>
                <MenuItem value="all">全部</MenuItem>
                {Object.entries(moodConfig).map(([key, config]) => (
                  <MenuItem key={key} value={key}>
                    <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                      {config.icon}
                      {config.label}
                    </Box>
                  </MenuItem>
                ))}
              </Select>
            </FormControl>
            <Typography variant="body2" color="text.secondary" sx={{ ml: 'auto' }}>
              顯示 <strong>{filteredResidents.length}</strong> / {mockResidents.length} 位住民
            </Typography>
          </Box>
        </Paper>
      </Fade>

      {/* 住民卡片 */}
      <Grid container spacing={3}>
        {filteredResidents.length === 0 ? (
          <Grid item xs={12}>
            <Fade in>
              <Paper sx={{ p: 6, textAlign: 'center' }}>
                <Avatar 
                  sx={{ 
                    width: 64, 
                    height: 64, 
                    mx: 'auto', 
                    mb: 2,
                    bgcolor: alpha(theme.palette.text.secondary, 0.1),
                  }}
                >
                  <SearchIcon sx={{ fontSize: 32, color: 'text.secondary' }} />
                </Avatar>
                <Typography variant="h6" color="text.secondary">
                  沒有符合條件的住民
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  請嘗試調整搜尋條件
                </Typography>
              </Paper>
            </Fade>
          </Grid>
        ) : (
          filteredResidents.map((resident, index) => (
            <Grid item xs={12} sm={6} md={4} key={resident.id}>
              <Grow in timeout={300 + index * 100}>
                <Card
                  onMouseEnter={() => setHoveredCard(resident.id)}
                  onMouseLeave={() => setHoveredCard(null)}
                  sx={{
                    height: '100%',
                    display: 'flex',
                    flexDirection: 'column',
                    position: 'relative',
                    overflow: 'visible',
                    border: resident.hasAlert 
                      ? `2px solid ${theme.palette.error.main}` 
                      : `1px solid ${theme.palette.divider}`,
                    '&::before': resident.hasAlert ? {
                      content: '""',
                      position: 'absolute',
                      top: -8,
                      right: -8,
                      width: 20,
                      height: 20,
                      borderRadius: '50%',
                      bgcolor: theme.palette.error.main,
                      animation: 'pulse 2s infinite',
                      '@keyframes pulse': {
                        '0%, 100%': { transform: 'scale(1)', opacity: 1 },
                        '50%': { transform: 'scale(1.2)', opacity: 0.7 },
                      },
                    } : {},
                  }}
                >
                  {/* 警示標籤 */}
                  {resident.hasAlert && (
                    <Box 
                      sx={{ 
                        position: 'absolute', 
                        top: 12, 
                        right: 12,
                        zIndex: 1,
                      }}
                    >
                      <Chip
                        size="small"
                        icon={<WarningIcon />}
                        label="需關注"
                        color="error"
                        sx={{ fontWeight: 600 }}
                      />
                    </Box>
                  )}

                  <CardContent sx={{ flex: 1, pb: 1, p: { xs: 2, sm: 2 } }}>
                    {/* 頭像與基本資訊 */}
                    <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, mb: 2.5 }}>
                      <Badge
                        overlap="circular"
                        anchorOrigin={{ vertical: 'bottom', horizontal: 'right' }}
                        badgeContent={
                          <Box
                            sx={{
                              width: 14,
                              height: 14,
                              borderRadius: '50%',
                              bgcolor: statusConfig[resident.status].color === 'default' 
                                ? 'grey.400' 
                                : `${statusConfig[resident.status].color}.main`,
                              border: `2px solid ${theme.palette.background.paper}`,
                            }}
                          />
                        }
                      >
                        <Avatar 
                          sx={{ 
                            width: 60, 
                            height: 60, 
                            bgcolor: theme.palette.primary.main,
                            fontSize: 26,
                            fontWeight: 600,
                            transition: 'transform 0.3s ease',
                            transform: hoveredCard === resident.id ? 'scale(1.08)' : 'scale(1)',
                          }}
                        >
                          {resident.name[0]}
                        </Avatar>
                      </Badge>
                      <Box sx={{ flex: 1, minWidth: 0 }}>
                        <Typography variant="h6" noWrap sx={{ fontWeight: 600 }}>
                          {resident.name}
                        </Typography>
                        <Box sx={{ display: 'flex', gap: 0.5, flexWrap: 'wrap', mt: 0.5 }}>
                          <Chip
                            size="small"
                            icon={moodConfig[resident.moodTrend].icon}
                            label={moodConfig[resident.moodTrend].label}
                            color={moodConfig[resident.moodTrend].color}
                            variant="outlined"
                            sx={{ 
                              height: 24,
                              '& .MuiChip-icon': { fontSize: 16 },
                            }}
                          />
                        </Box>
                      </Box>
                    </Box>

                    {/* 快速資訊 */}
                    <Box sx={{ display: 'flex', flexDirection: 'column', gap: 1.5 }}>
                      <Box sx={{ display: 'flex', alignItems: 'center', gap: 1.5 }}>
                        <Avatar 
                          sx={{ 
                            width: 28, 
                            height: 28, 
                            bgcolor: alpha(theme.palette.text.secondary, 0.1),
                          }}
                        >
                          <AccessTimeIcon sx={{ fontSize: 16, color: 'text.secondary' }} />
                        </Avatar>
                        <Typography variant="body2" color="text.secondary">
                          最後互動：{formatTime(resident.lastInteraction)}
                        </Typography>
                      </Box>
                      <Box sx={{ display: 'flex', alignItems: 'center', gap: 1.5 }}>
                        <Avatar 
                          sx={{ 
                            width: 28, 
                            height: 28, 
                            bgcolor: alpha(theme.palette.error.main, 0.1),
                          }}
                        >
                          <MedicationIcon sx={{ fontSize: 16, color: 'error.main' }} />
                        </Avatar>
                        <Typography variant="body2" color="text.secondary" noWrap>
                          用藥：{resident.lastMedication || '無紀錄'}
                        </Typography>
                      </Box>
                      <Box sx={{ display: 'flex', alignItems: 'center', gap: 1.5 }}>
                        <Avatar 
                          sx={{ 
                            width: 28, 
                            height: 28, 
                            bgcolor: alpha(theme.palette.success.main, 0.1),
                          }}
                        >
                          <DirectionsWalkIcon sx={{ fontSize: 16, color: 'success.main' }} />
                        </Avatar>
                        <Typography variant="body2" color="text.secondary" noWrap>
                          活動：{resident.lastActivity || '無紀錄'}
                        </Typography>
                      </Box>
                    </Box>

                    {/* 統計數字 */}
                    <Box 
                      sx={{ 
                        display: 'flex', 
                        justifyContent: 'space-around', 
                        mt: 2.5, 
                        pt: 2, 
                        borderTop: 1, 
                        borderColor: 'divider',
                      }}
                    >
                      <Tooltip title="今日事件" arrow>
                        <Box sx={{ textAlign: 'center', cursor: 'default' }}>
                          <Typography variant="h5" sx={{ fontWeight: 600 }}>
                            {resident.todayEvents}
                          </Typography>
                          <Typography variant="caption" color="text.secondary">
                            事件
                          </Typography>
                        </Box>
                      </Tooltip>
                      <Tooltip title="待處理提醒" arrow>
                        <Box sx={{ textAlign: 'center', cursor: 'default' }}>
                          <Typography 
                            variant="h5" 
                            color={resident.pendingReminders > 0 ? 'warning.main' : 'inherit'}
                            sx={{ fontWeight: 600 }}
                          >
                            {resident.pendingReminders}
                          </Typography>
                          <Typography variant="caption" color="text.secondary">
                            提醒
                          </Typography>
                        </Box>
                      </Tooltip>
                    </Box>
                  </CardContent>

                  <CardActions sx={{ justifyContent: 'space-between', px: 2, pb: 2 }}>
                    <Button
                      size="small"
                      startIcon={<VisibilityIcon />}
                      onClick={() => router.push(`/caregiver/resident?id=${resident.id}`)}
                      sx={{ fontWeight: 500 }}
                    >
                      查看詳情
                    </Button>
                    <Tooltip title="語音互動" arrow>
                      <IconButton
                        size="small"
                        color="primary"
                        onClick={() => router.push(`/resident/voice?persona=${resident.id}`)}
                        sx={{
                          bgcolor: alpha(theme.palette.primary.main, 0.1),
                          '&:hover': {
                            bgcolor: alpha(theme.palette.primary.main, 0.2),
                          },
                        }}
                      >
                        <RecordVoiceOverIcon />
                      </IconButton>
                    </Tooltip>
                  </CardActions>
                </Card>
              </Grow>
            </Grid>
          ))
        )}
      </Grid>
    </Container>
  );
}
