'use client';
import React, { useState } from 'react';
import {
  Container,
  Typography,
  Box,
  Paper,
  Table,
  TableHead,
  TableBody,
  TableRow,
  TableCell,
  Chip,
  IconButton,
  Button,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Tabs,
  Tab,
  useMediaQuery,
} from '@mui/material';
import { useTheme } from '@mui/material/styles';
import ReminderCard from '../../components/ReminderCard';
import NotificationsActiveIcon from '@mui/icons-material/NotificationsActive';
import EditIcon from '@mui/icons-material/Edit';
import DeleteIcon from '@mui/icons-material/Delete';
import CheckCircleIcon from '@mui/icons-material/CheckCircle';
import AddIcon from '@mui/icons-material/Add';
import MedicationIcon from '@mui/icons-material/Medication';
import FavoriteIcon from '@mui/icons-material/Favorite';
import EventIcon from '@mui/icons-material/Event';
import MoreHorizIcon from '@mui/icons-material/MoreHoriz';

// 提醒狀態類型
type ReminderStatus = 'pending' | 'completed' | 'missed' | 'cancelled';

// 重要程度
type Importance = 'high' | 'medium' | 'low';

// 提醒類別
type ReminderCategory = 'medication' | 'health' | 'appointment' | 'other';

const categoryConfig: Record<ReminderCategory, { label: string; icon: React.ReactElement; color: 'error' | 'success' | 'info' | 'default' }> = {
  medication: { label: '用藥', icon: <MedicationIcon />, color: 'error' },
  health: { label: '健康狀況', icon: <FavoriteIcon />, color: 'success' },
  appointment: { label: '回診', icon: <EventIcon />, color: 'info' },
  other: { label: '其他', icon: <MoreHorizIcon />, color: 'default' },
};

interface Reminder {
  id: string;
  residentId: string;
  residentName: string;
  title: string;
  scheduledAt: Date;
  status: ReminderStatus;
  importance: Importance;
  category: ReminderCategory;
  idempotencyKey: string;
  createdBy: string;
  completedAt?: Date;
}

// 狀態配置
const statusConfig: Record<ReminderStatus, { label: string; color: 'default' | 'success' | 'error' | 'warning' }> = {
  pending: { label: '待執行', color: 'warning' },
  completed: { label: '已完成', color: 'success' },
  missed: { label: '已錯過', color: 'error' },
  cancelled: { label: '已取消', color: 'default' },
};

const importanceConfig: Record<Importance, { label: string; color: 'error' | 'warning' | 'info' }> = {
  high: { label: '高', color: 'error' },
  medium: { label: '中', color: 'warning' },
  low: { label: '低', color: 'info' },
};

// 模擬提醒資料
const mockReminders: Reminder[] = [
  {
    id: '1',
    residentId: 'r1',
    residentName: '王奶奶',
    title: '下午三點回診',
    scheduledAt: new Date('2026-08-02T15:00:00'),
    status: 'pending',
    importance: 'high',
    category: 'appointment',
    idempotencyKey: 'rem-r1-20260802-1500',
    createdBy: 'voice_agent',
  },
  {
    id: '2',
    residentId: 'r1',
    residentName: '王奶奶',
    title: '晚上六點服用降血壓藥',
    scheduledAt: new Date('2026-08-01T18:00:00'),
    status: 'completed',
    importance: 'high',
    category: 'medication',
    idempotencyKey: 'rem-r1-20260801-1800',
    createdBy: 'voice_agent',
    completedAt: new Date('2026-08-01T18:05:00'),
  },
  {
    id: '3',
    residentId: 'r1',
    residentName: '王奶奶',
    title: '下午兩點復健課程',
    scheduledAt: new Date('2026-08-01T14:00:00'),
    status: 'completed',
    importance: 'medium',
    category: 'health',
    idempotencyKey: 'rem-r1-20260801-1400',
    createdBy: 'caregiver',
    completedAt: new Date('2026-08-01T14:00:00'),
  },
  {
    id: '4',
    residentId: 'r2',
    residentName: '李爺爺',
    title: '早上八點半服用心臟藥物',
    scheduledAt: new Date('2026-08-01T08:30:00'),
    status: 'completed',
    importance: 'high',
    category: 'medication',
    idempotencyKey: 'rem-r2-20260801-0830',
    createdBy: 'voice_agent',
    completedAt: new Date('2026-08-01T08:35:00'),
  },
  {
    id: '5',
    residentId: 'r2',
    residentName: '李爺爺',
    title: '下午四點家屬探訪',
    scheduledAt: new Date('2026-08-01T16:00:00'),
    status: 'missed',
    importance: 'medium',
    category: 'other',
    idempotencyKey: 'rem-r2-20260801-1600',
    createdBy: 'family',
  },
];

export default function Reminders() {
  const theme = useTheme();
  const isMobile = useMediaQuery(theme.breakpoints.down('sm'));
  const [tabValue, setTabValue] = useState(0);
  const [reminders, setReminders] = useState<Reminder[]>(mockReminders);
  const [editDialogOpen, setEditDialogOpen] = useState(false);
  const [editReminder, setEditReminder] = useState<Partial<Reminder>>({});
  const [categoryFilter, setCategoryFilter] = useState<ReminderCategory | 'all'>('all');

  // 依狀態分類
  const pendingReminders = reminders.filter((r) => r.status === 'pending');
  const completedReminders = reminders.filter((r) => r.status === 'completed');
  const missedReminders = reminders.filter((r) => r.status === 'missed');

  // 計算各分頁的類別統計
  const getCategoryStats = (data: Reminder[]) => {
    const stats: Record<ReminderCategory, number> = {
      medication: 0,
      health: 0,
      appointment: 0,
      other: 0,
    };
    data.forEach((r) => {
      stats[r.category]++;
    });
    return stats;
  };

  // 取得當前分頁的資料
  const getCurrentTabData = () => {
    switch (tabValue) {
      case 0: return pendingReminders;
      case 1: return completedReminders;
      case 2: return missedReminders;
      default: return [];
    }
  };

  // 套用類別篩選
  const getFilteredData = (data: Reminder[]) => {
    if (categoryFilter === 'all') return data;
    return data.filter((r) => r.category === categoryFilter);
  };

  const currentTabData = getCurrentTabData();
  const categoryStats = getCategoryStats(currentTabData);
  const filteredPendingReminders = getFilteredData(pendingReminders);
  const filteredCompletedReminders = getFilteredData(completedReminders);
  const filteredMissedReminders = getFilteredData(missedReminders);

  // 標記完成
  const handleComplete = (id: string) => {
    setReminders((prev) =>
      prev.map((r) =>
        r.id === id ? { ...r, status: 'completed' as ReminderStatus, completedAt: new Date() } : r
      )
    );
  };

  // 刪除提醒
  const handleDelete = (id: string) => {
    setReminders((prev) => prev.filter((r) => r.id !== id));
  };

  // 開啟編輯對話框
  const handleEdit = (reminder: Reminder) => {
    setEditReminder(reminder);
    setEditDialogOpen(true);
  };

  // 開啟新增對話框
  const handleAdd = () => {
    setEditReminder({
      importance: 'medium',
      category: 'other',
      status: 'pending',
    });
    setEditDialogOpen(true);
  };

  // 儲存提醒
  const handleSave = () => {
    if (editReminder.id) {
      // 更新
      setReminders((prev) =>
        prev.map((r) => (r.id === editReminder.id ? { ...r, ...editReminder } as Reminder : r))
      );
    } else {
      // 新增
      const newReminder: Reminder = {
        id: Date.now().toString(),
        residentId: editReminder.residentId || 'r1',
        residentName: editReminder.residentName || '王奶奶',
        title: editReminder.title || '',
        scheduledAt: editReminder.scheduledAt || new Date(),
        status: 'pending',
        importance: editReminder.importance || 'medium',
        category: editReminder.category || 'other',
        idempotencyKey: `rem-${Date.now()}`,
        createdBy: 'caregiver',
      };
      setReminders((prev) => [...prev, newReminder]);
    }
    setEditDialogOpen(false);
  };

  // 渲染提醒表格
  const renderTable = (data: Reminder[]) => (
    <Table>
      <TableHead>
        <TableRow>
          <TableCell>住民</TableCell>
          <TableCell>提醒內容</TableCell>
          <TableCell>類別</TableCell>
          <TableCell>排程時間</TableCell>
          <TableCell>重要性</TableCell>
          <TableCell>狀態</TableCell>
          <TableCell>來源</TableCell>
          <TableCell>操作</TableCell>
        </TableRow>
      </TableHead>
      <TableBody>
        {data.length === 0 ? (
          <TableRow>
            <TableCell colSpan={8} align="center">
              <Typography color="text.secondary">沒有提醒</Typography>
            </TableCell>
          </TableRow>
        ) : (
          data.map((reminder) => (
            <TableRow key={reminder.id}>
              <TableCell>{reminder.residentName}</TableCell>
              <TableCell>{reminder.title}</TableCell>
              <TableCell>
                <Chip
                  size="small"
                  icon={categoryConfig[reminder.category].icon}
                  label={categoryConfig[reminder.category].label}
                  color={categoryConfig[reminder.category].color}
                />
              </TableCell>
              <TableCell>
                {reminder.scheduledAt.toLocaleString('zh-TW', {
                  month: 'numeric',
                  day: 'numeric',
                  hour: '2-digit',
                  minute: '2-digit',
                })}
              </TableCell>
              <TableCell>
                <Chip
                  size="small"
                  label={importanceConfig[reminder.importance].label}
                  color={importanceConfig[reminder.importance].color}
                />
              </TableCell>
              <TableCell>
                <Chip
                  size="small"
                  label={statusConfig[reminder.status].label}
                  color={statusConfig[reminder.status].color}
                />
              </TableCell>
              <TableCell>
                <Typography variant="caption">{reminder.createdBy}</Typography>
              </TableCell>
              <TableCell>
                {reminder.status === 'pending' && (
                  <IconButton size="small" color="success" onClick={() => handleComplete(reminder.id)}>
                    <CheckCircleIcon />
                  </IconButton>
                )}
                <IconButton size="small" onClick={() => handleEdit(reminder)}>
                  <EditIcon />
                </IconButton>
                <IconButton size="small" color="error" onClick={() => handleDelete(reminder.id)}>
                  <DeleteIcon />
                </IconButton>
              </TableCell>
            </TableRow>
          ))
        )}
      </TableBody>
    </Table>
  );

  // 渲染手機版卡片列表
  const renderCardList = (data: Reminder[]) => (
    <Box sx={{ px: 1 }}>
      {data.length === 0 ? (
        <Typography color="text.secondary" align="center" sx={{ py: 4 }}>
          沒有提醒
        </Typography>
      ) : (
        data.map((reminder) => (
          <ReminderCard
            key={reminder.id}
            reminder={reminder}
            onComplete={handleComplete}
            onEdit={handleEdit}
            onDelete={handleDelete}
          />
        ))
      )}
    </Box>
  );

  return (
    <Container maxWidth="lg" sx={{ py: 2 }}>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
        <Typography variant="h4" sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
          <NotificationsActiveIcon color="primary" />
          提醒管理
        </Typography>
        <Button variant="contained" startIcon={<AddIcon />} onClick={handleAdd}>
          新增提醒
        </Button>
      </Box>

      {/* 分頁標籤 */}
      <Paper sx={{ mb: 2 }}>
        <Tabs value={tabValue} onChange={(_, v) => { setTabValue(v); setCategoryFilter('all'); }}>
          <Tab label={`待執行 (${pendingReminders.length})`} />
          <Tab label={`已完成 (${completedReminders.length})`} />
          <Tab label={`已錯過 (${missedReminders.length})`} />
        </Tabs>
      </Paper>

      {/* 類別統計與篩選 */}
      <Paper sx={{ p: { xs: 1.5, sm: 2 }, mb: 2 }}>
        <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1, alignItems: 'center', justifyContent: 'space-between' }}>
          {/* 類別統計 */}
          <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1 }}>
            {Object.entries(categoryConfig).map(([key, config]) => {
              const count = categoryStats[key as ReminderCategory];
              if (count === 0) return null;
              return (
                <Chip
                  key={key}
                  size="small"
                  icon={config.icon}
                  label={`${config.label} ${count}`}
                  color={config.color}
                  variant={categoryFilter === key ? 'filled' : 'outlined'}
                  onClick={() => setCategoryFilter(categoryFilter === key ? 'all' : key as ReminderCategory)}
                  sx={{ cursor: 'pointer' }}
                />
              );
            })}
          </Box>
          {/* 篩選下拉選單 */}
          <FormControl size="small" sx={{ minWidth: 100 }}>
            <InputLabel>篩選類別</InputLabel>
            <Select
              value={categoryFilter}
              label="篩選類別"
              onChange={(e) => setCategoryFilter(e.target.value as ReminderCategory | 'all')}
            >
              <MenuItem value="all">全部</MenuItem>
              {Object.entries(categoryConfig).map(([key, config]) => (
                <MenuItem key={key} value={key}>
                  <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                    {config.icon}
                    {config.label}
                  </Box>
                </MenuItem>
              ))}
            </Select>
          </FormControl>
        </Box>
      </Paper>

      {/* 提醒列表 */}
      <Paper sx={{ overflow: 'hidden' }}>
        {isMobile ? (
          <>
            {tabValue === 0 && renderCardList(filteredPendingReminders)}
            {tabValue === 1 && renderCardList(filteredCompletedReminders)}
            {tabValue === 2 && renderCardList(filteredMissedReminders)}
          </>
        ) : (
          <>
            {tabValue === 0 && renderTable(filteredPendingReminders)}
            {tabValue === 1 && renderTable(filteredCompletedReminders)}
            {tabValue === 2 && renderTable(filteredMissedReminders)}
          </>
        )}
      </Paper>

      {/* 編輯/新增對話框 */}
      <Dialog open={editDialogOpen} onClose={() => setEditDialogOpen(false)} maxWidth="sm" fullWidth>
        <DialogTitle>{editReminder.id ? '編輯提醒' : '新增提醒'}</DialogTitle>
        <DialogContent>
          <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2, mt: 1 }}>
            <TextField
              label="提醒內容"
              fullWidth
              value={editReminder.title || ''}
              onChange={(e) => setEditReminder({ ...editReminder, title: e.target.value })}
            />
            <FormControl fullWidth>
              <InputLabel>類別</InputLabel>
              <Select
                value={editReminder.category || 'other'}
                label="類別"
                onChange={(e) =>
                  setEditReminder({ ...editReminder, category: e.target.value as ReminderCategory })
                }
              >
                {Object.entries(categoryConfig).map(([key, config]) => (
                  <MenuItem key={key} value={key}>
                    <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                      {config.icon}
                      {config.label}
                    </Box>
                  </MenuItem>
                ))}
              </Select>
            </FormControl>
            <TextField
              label="排程時間"
              type="datetime-local"
              fullWidth
              slotProps={{ inputLabel: { shrink: true } }}
              value={
                editReminder.scheduledAt
                  ? new Date(editReminder.scheduledAt).toISOString().slice(0, 16)
                  : ''
              }
              onChange={(e) =>
                setEditReminder({ ...editReminder, scheduledAt: new Date(e.target.value) })
              }
            />
            <FormControl fullWidth>
              <InputLabel>重要性</InputLabel>
              <Select
                value={editReminder.importance || 'medium'}
                label="重要性"
                onChange={(e) =>
                  setEditReminder({ ...editReminder, importance: e.target.value as Importance })
                }
              >
                <MenuItem value="high">高</MenuItem>
                <MenuItem value="medium">中</MenuItem>
                <MenuItem value="low">低</MenuItem>
              </Select>
            </FormControl>
          </Box>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setEditDialogOpen(false)}>取消</Button>
          <Button variant="contained" onClick={handleSave}>
            儲存
          </Button>
        </DialogActions>
      </Dialog>
    </Container>
  );
}
