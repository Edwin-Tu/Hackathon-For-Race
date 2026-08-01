'use client';
import React, { useState } from 'react';
import {
  Container,
  Typography,
  Box,
  Paper,
  Card,
  CardContent,
  Chip,
  IconButton,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  TextField,
  Collapse,
  Divider,
  List,
  ListItem,
  ListItemIcon,
  ListItemText,
  Button,
} from '@mui/material';
import Grid from '@mui/material/Grid';
import SummarizeIcon from '@mui/icons-material/Summarize';
import ExpandMoreIcon from '@mui/icons-material/ExpandMore';
import ExpandLessIcon from '@mui/icons-material/ExpandLess';
import SourceIcon from '@mui/icons-material/Source';
import MedicationIcon from '@mui/icons-material/Medication';
import DirectionsWalkIcon from '@mui/icons-material/DirectionsWalk';
import RestaurantIcon from '@mui/icons-material/Restaurant';
import MoodIcon from '@mui/icons-material/Mood';
import BedtimeIcon from '@mui/icons-material/Bedtime';
import EventIcon from '@mui/icons-material/Event';
import RefreshIcon from '@mui/icons-material/Refresh';

// 事件類型圖示
const eventTypeIcons: Record<string, React.ReactNode> = {
  meal: <RestaurantIcon fontSize="small" />,
  activity: <DirectionsWalkIcon fontSize="small" />,
  medication: <MedicationIcon fontSize="small" />,
  sleep: <BedtimeIcon fontSize="small" />,
  mood: <MoodIcon fontSize="small" />,
  schedule: <EventIcon fontSize="small" />,
};

// 來源事件
interface SourceEvent {
  id: string;
  type: string;
  content: string;
  time: string;
  confidence: number;
}

// 摘要資料
interface DailySummary {
  id: string;
  residentId: string;
  residentName: string;
  date: string;
  summary: string;
  version: number;
  reviewStatus: 'pending' | 'reviewed' | 'flagged';
  sourceEvents: SourceEvent[];
  generatedAt: Date;
}

// 模擬摘要資料
const mockSummaries: DailySummary[] = [
  {
    id: '1',
    residentId: 'r1',
    residentName: '王奶奶',
    date: '2026-08-01',
    summary:
      '今日用藥正常，早上八點已服用降血壓藥。活動量適中，上午散步 30 分鐘。飲食正常，早餐吃了稀飯、豆漿、饅頭。情緒良好，下午與女兒通電話後心情愉快。明日下午三點有心臟科回診。',
    version: 1,
    reviewStatus: 'reviewed',
    sourceEvents: [
      { id: 'e1', type: 'medication', content: '服用降血壓藥', time: '08:00', confidence: 0.95 },
      { id: 'e2', type: 'meal', content: '早餐：稀飯、豆漿、饅頭', time: '07:30', confidence: 0.88 },
      { id: 'e3', type: 'activity', content: '戶外散步 30 分鐘', time: '10:00', confidence: 0.92 },
      { id: 'e4', type: 'mood', content: '與女兒通話後心情愉快', time: '14:00', confidence: 0.78 },
      { id: 'e5', type: 'schedule', content: '明日下午三點心臟科回診', time: '15:00', confidence: 0.97 },
    ],
    generatedAt: new Date('2026-08-01T20:00:00'),
  },
  {
    id: '2',
    residentId: 'r2',
    residentName: '李爺爺',
    date: '2026-08-01',
    summary:
      '今日血壓偏高，收縮壓達 160mmHg，已通知護理人員追蹤。早上八點半服用心臟藥物。中午午睡一小時。家屬探訪因故未能如期進行。',
    version: 2,
    reviewStatus: 'flagged',
    sourceEvents: [
      { id: 'e6', type: 'medication', content: '服用心臟藥物', time: '08:30', confidence: 0.97 },
      { id: 'e7', type: 'sleep', content: '午睡 1 小時', time: '13:00', confidence: 0.85 },
      { id: 'e8', type: 'schedule', content: '家屬探訪（已錯過）', time: '16:00', confidence: 0.9 },
    ],
    generatedAt: new Date('2026-08-01T20:00:00'),
  },
];

// 審核狀態配置
const reviewStatusConfig: Record<string, { label: string; color: 'success' | 'warning' | 'error' }> = {
  pending: { label: '待審核', color: 'warning' },
  reviewed: { label: '已審核', color: 'success' },
  flagged: { label: '需關注', color: 'error' },
};

export default function Summary() {
  const [selectedResident, setSelectedResident] = useState<string>('all');
  const [selectedDate, setSelectedDate] = useState<string>('2026-08-01');
  const [expandedId, setExpandedId] = useState<string | null>(null);

  // 篩選摘要
  const filteredSummaries = mockSummaries
    .filter((s) => selectedResident === 'all' || s.residentId === selectedResident)
    .filter((s) => s.date === selectedDate);

  // 取得住民列表
  const residents = Array.from(new Set(mockSummaries.map((s) => s.residentId))).map((id) => ({
    id,
    name: mockSummaries.find((s) => s.residentId === id)?.residentName || '',
  }));

  // 切換展開
  const toggleExpand = (id: string) => {
    setExpandedId(expandedId === id ? null : id);
  };

  return (
    <Container maxWidth="lg" sx={{ py: 2 }}>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
        <Typography variant="h4" sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
          <SummarizeIcon color="primary" />
          每日摘要
        </Typography>
        <Button variant="outlined" startIcon={<RefreshIcon />}>
          重新生成
        </Button>
      </Box>

      {/* 篩選器 */}
      <Paper sx={{ p: 2, mb: 3 }}>
        <Box sx={{ display: 'flex', gap: 2, flexWrap: 'wrap' }}>
          <FormControl size="small" sx={{ minWidth: 150 }}>
            <InputLabel>住民</InputLabel>
            <Select
              value={selectedResident}
              label="住民"
              onChange={(e) => setSelectedResident(e.target.value)}
            >
              <MenuItem value="all">全部</MenuItem>
              {residents.map((r) => (
                <MenuItem key={r.id} value={r.id}>
                  {r.name}
                </MenuItem>
              ))}
            </Select>
          </FormControl>
          <TextField
            type="date"
            size="small"
            label="日期"
            value={selectedDate}
            onChange={(e) => setSelectedDate(e.target.value)}
            slotProps={{ inputLabel: { shrink: true } }}
          />
        </Box>
      </Paper>

      {/* 摘要卡片 */}
      <Grid container spacing={3}>
        {filteredSummaries.length === 0 ? (
          <Grid item xs={12}>
            <Paper sx={{ p: 4, textAlign: 'center' }}>
              <Typography color="text.secondary">沒有符合條件的摘要</Typography>
            </Paper>
          </Grid>
        ) : (
          filteredSummaries.map((summary) => (
            <Grid item xs={12} key={summary.id}>
              <Card>
                <CardContent>
                  {/* 標題列 */}
                  <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', mb: 2 }}>
                    <Box>
                      <Typography variant="h5" component="div">
                        {summary.residentName}
                      </Typography>
                      <Typography variant="body2" color="text.secondary">
                        {summary.date} · 版本 {summary.version} · 生成於{' '}
                        {summary.generatedAt.toLocaleTimeString('zh-TW', { hour: '2-digit', minute: '2-digit' })}
                      </Typography>
                    </Box>
                    <Box sx={{ display: 'flex', gap: 1, alignItems: 'center' }}>
                      <Chip
                        size="small"
                        label={reviewStatusConfig[summary.reviewStatus].label}
                        color={reviewStatusConfig[summary.reviewStatus].color}
                      />
                      <Chip size="small" label={`${summary.sourceEvents.length} 個來源事件`} variant="outlined" />
                    </Box>
                  </Box>

                  {/* 摘要內容 */}
                  <Paper sx={{ p: 2, bgcolor: 'grey.50', mb: 2 }}>
                    <Typography variant="body1">{summary.summary}</Typography>
                  </Paper>

                  {/* 來源事件展開按鈕 */}
                  <Box
                    sx={{
                      display: 'flex',
                      alignItems: 'center',
                      cursor: 'pointer',
                      '&:hover': { bgcolor: 'action.hover' },
                      p: 1,
                      borderRadius: 1,
                    }}
                    onClick={() => toggleExpand(summary.id)}
                  >
                    <SourceIcon sx={{ mr: 1 }} color="action" />
                    <Typography variant="body2" color="text.secondary" sx={{ flex: 1 }}>
                      來源事件追溯 (source_event_ids)
                    </Typography>
                    <IconButton size="small">
                      {expandedId === summary.id ? <ExpandLessIcon /> : <ExpandMoreIcon />}
                    </IconButton>
                  </Box>

                  {/* 來源事件列表 */}
                  <Collapse in={expandedId === summary.id}>
                    <Divider sx={{ my: 1 }} />
                    <List dense>
                      {summary.sourceEvents.map((event) => (
                        <ListItem key={event.id}>
                          <ListItemIcon sx={{ minWidth: 36 }}>
                            {eventTypeIcons[event.type] || <EventIcon fontSize="small" />}
                          </ListItemIcon>
                          <ListItemText
                            primary={event.content}
                            secondary={
                              <Box component="span" sx={{ display: 'flex', gap: 1, alignItems: 'center' }}>
                                <Typography component="span" variant="caption">{event.time}</Typography>
                                <Chip
                                  size="small"
                                  label={`${Math.round(event.confidence * 100)}%`}
                                  color={event.confidence >= 0.9 ? 'success' : event.confidence >= 0.7 ? 'warning' : 'error'}
                                  sx={{ height: 18, fontSize: '0.7rem' }}
                                />
                                <Typography component="span" variant="caption" color="text.secondary">
                                  ID: {event.id}
                                </Typography>
                              </Box>
                            }
                            secondaryTypographyProps={{ component: 'div' }}
                          />
                        </ListItem>
                      ))}
                    </List>
                    <Box sx={{ mt: 1, p: 1, bgcolor: 'info.light', borderRadius: 1 }}>
                      <Typography variant="caption" color="info.contrastText">
                        💡 此摘要僅根據上方的結構化事件生成，照護者可追溯每段內容的來源。若有錯誤可前往「記憶修正」頁面修正。
                      </Typography>
                    </Box>
                  </Collapse>
                </CardContent>
              </Card>
            </Grid>
          ))
        )}
      </Grid>
    </Container>
  );
}
