'use client';
import React, { useState } from 'react';
import {
  Container,
  Typography,
  Box,
  Paper,
  Chip,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  TextField,
  ToggleButton,
  ToggleButtonGroup,
} from '@mui/material';
import TimelineIcon from '@mui/icons-material/Timeline';
import RestaurantIcon from '@mui/icons-material/Restaurant';
import DirectionsWalkIcon from '@mui/icons-material/DirectionsWalk';
import MedicationIcon from '@mui/icons-material/Medication';
import BedtimeIcon from '@mui/icons-material/Bedtime';
import MoodIcon from '@mui/icons-material/Mood';
import EventIcon from '@mui/icons-material/Event';

// 事件類型定義
type EventType = 'meal' | 'activity' | 'medication' | 'sleep' | 'mood' | 'schedule';

interface LifeEvent {
  id: string;
  residentId: string;
  residentName: string;
  type: EventType;
  content: string;
  eventTime: Date;
  confidence: number;
  sourceText: string;
  createdBy: string;
  status: 'confirmed' | 'pending' | 'corrected';
}

// 事件類型配置
const eventTypeConfig: Record<EventType, { label: string; color: string; icon: React.ReactNode }> = {
  meal: { label: '飲食', color: '#ff9800', icon: <RestaurantIcon /> },
  activity: { label: '活動', color: '#4caf50', icon: <DirectionsWalkIcon /> },
  medication: { label: '用藥', color: '#f44336', icon: <MedicationIcon /> },
  sleep: { label: '睡眠', color: '#9c27b0', icon: <BedtimeIcon /> },
  mood: { label: '情緒', color: '#2196f3', icon: <MoodIcon /> },
  schedule: { label: '行程', color: '#607d8b', icon: <EventIcon /> },
};

// 模擬事件資料
const mockEvents: LifeEvent[] = [
  {
    id: '1',
    residentId: 'r1',
    residentName: '王奶奶',
    type: 'medication',
    content: '服用降血壓藥',
    eventTime: new Date('2026-08-01T08:00:00'),
    confidence: 0.95,
    sourceText: '我早上八點吃過藥了',
    createdBy: 'voice_agent',
    status: 'confirmed',
  },
  {
    id: '2',
    residentId: 'r1',
    residentName: '王奶奶',
    type: 'meal',
    content: '早餐：稀飯、豆漿、饅頭',
    eventTime: new Date('2026-08-01T07:30:00'),
    confidence: 0.88,
    sourceText: '早上吃了稀飯和饅頭',
    createdBy: 'voice_agent',
    status: 'confirmed',
  },
  {
    id: '3',
    residentId: 'r1',
    residentName: '王奶奶',
    type: 'activity',
    content: '戶外散步 30 分鐘',
    eventTime: new Date('2026-08-01T10:00:00'),
    confidence: 0.92,
    sourceText: '下午有出去散步半小時',
    createdBy: 'voice_agent',
    status: 'confirmed',
  },
  {
    id: '4',
    residentId: 'r1',
    residentName: '王奶奶',
    type: 'mood',
    content: '情緒良好，與家人通話後心情愉快',
    eventTime: new Date('2026-08-01T14:00:00'),
    confidence: 0.78,
    sourceText: '今天心情很好，跟女兒講電話了',
    createdBy: 'voice_agent',
    status: 'pending',
  },
  {
    id: '5',
    residentId: 'r2',
    residentName: '李爺爺',
    type: 'medication',
    content: '服用心臟藥物',
    eventTime: new Date('2026-08-01T08:30:00'),
    confidence: 0.97,
    sourceText: '八點半吃了心臟的藥',
    createdBy: 'voice_agent',
    status: 'confirmed',
  },
  {
    id: '6',
    residentId: 'r2',
    residentName: '李爺爺',
    type: 'sleep',
    content: '午睡 1 小時',
    eventTime: new Date('2026-08-01T13:00:00'),
    confidence: 0.85,
    sourceText: '中午睡了一個小時',
    createdBy: 'voice_agent',
    status: 'confirmed',
  },
];

export default function Timeline() {
  const [selectedResident, setSelectedResident] = useState<string>('all');
  const [selectedTypes, setSelectedTypes] = useState<EventType[]>([]);
  const [dateFilter, setDateFilter] = useState<string>('2026-08-01');

  // 篩選事件
  const filteredEvents = mockEvents
    .filter((e) => selectedResident === 'all' || e.residentId === selectedResident)
    .filter((e) => selectedTypes.length === 0 || selectedTypes.includes(e.type))
    .filter((e) => e.eventTime.toISOString().startsWith(dateFilter))
    .sort((a, b) => b.eventTime.getTime() - a.eventTime.getTime());

  // 取得所有住民
  const residents = Array.from(new Set(mockEvents.map((e) => e.residentId))).map((id) => ({
    id,
    name: mockEvents.find((e) => e.residentId === id)?.residentName || '',
  }));

  const handleTypeChange = (_: React.MouseEvent<HTMLElement>, newTypes: EventType[]) => {
    setSelectedTypes(newTypes);
  };

  return (
    <Container maxWidth="lg" sx={{ py: 2 }}>
      <Typography variant="h4" gutterBottom sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
        <TimelineIcon color="primary" />
        事件時間軸
      </Typography>

      {/* 篩選器 */}
      <Paper sx={{ p: 2, mb: 3 }}>
        <Box sx={{ display: 'flex', gap: 2, flexWrap: 'wrap', alignItems: 'center' }}>
          {/* 住民篩選 */}
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

          {/* 日期篩選 */}
          <TextField
            type="date"
            size="small"
            label="日期"
            value={dateFilter}
            onChange={(e) => setDateFilter(e.target.value)}
            slotProps={{ inputLabel: { shrink: true } }}
          />

          {/* 事件類型篩選 */}
          <ToggleButtonGroup
            value={selectedTypes}
            onChange={handleTypeChange}
            size="small"
            sx={{ flexWrap: 'wrap' }}
          >
            {Object.entries(eventTypeConfig).map(([type, config]) => (
              <ToggleButton key={type} value={type}>
                {config.icon}
                <Typography variant="caption" sx={{ ml: 0.5 }}>
                  {config.label}
                </Typography>
              </ToggleButton>
            ))}
          </ToggleButtonGroup>
        </Box>
      </Paper>

      {/* 時間軸 */}
      <Box sx={{ position: 'relative', pl: 4 }}>
        {/* 時間軸線 */}
        <Box
          sx={{
            position: 'absolute',
            left: 15,
            top: 0,
            bottom: 0,
            width: 2,
            bgcolor: 'divider',
          }}
        />

        {filteredEvents.length === 0 ? (
          <Typography color="text.secondary" sx={{ py: 4, textAlign: 'center' }}>
            沒有符合條件的事件
          </Typography>
        ) : (
          filteredEvents.map((event) => {
            const config = eventTypeConfig[event.type];
            return (
              <Box key={event.id} sx={{ position: 'relative', mb: 3 }}>
                {/* 時間軸節點 */}
                <Box
                  sx={{
                    position: 'absolute',
                    left: -25,
                    width: 32,
                    height: 32,
                    borderRadius: '50%',
                    bgcolor: config.color,
                    color: 'white',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    fontSize: 16,
                  }}
                >
                  {config.icon}
                </Box>

                {/* 事件卡片 */}
                <Paper sx={{ p: 2, ml: 2 }}>
                  <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', mb: 1 }}>
                    <Box>
                      <Typography variant="subtitle1" fontWeight="bold">
                        {event.content}
                      </Typography>
                      <Typography variant="caption" color="text.secondary">
                        {event.residentName} ·{' '}
                        {event.eventTime.toLocaleTimeString('zh-TW', { hour: '2-digit', minute: '2-digit' })}
                      </Typography>
                    </Box>
                    <Box sx={{ display: 'flex', gap: 0.5 }}>
                      <Chip
                        size="small"
                        label={config.label}
                        sx={{ bgcolor: config.color, color: 'white' }}
                      />
                      <Chip
                        size="small"
                        label={event.status === 'confirmed' ? '已確認' : event.status === 'pending' ? '待確認' : '已修正'}
                        color={event.status === 'confirmed' ? 'success' : event.status === 'pending' ? 'warning' : 'info'}
                        variant="outlined"
                      />
                    </Box>
                  </Box>

                  {/* 來源文字 */}
                  <Box sx={{ bgcolor: 'grey.100', p: 1, borderRadius: 1, mt: 1 }}>
                    <Typography variant="caption" color="text.secondary">
                      原始語句：
                    </Typography>
                    <Typography variant="body2" fontStyle="italic">
                      「{event.sourceText}」
                    </Typography>
                    <Typography variant="caption" color="text.secondary">
                      信心度：{Math.round(event.confidence * 100)}% · 來源：{event.createdBy}
                    </Typography>
                  </Box>
                </Paper>
              </Box>
            );
          })
        )}
      </Box>
    </Container>
  );
}
