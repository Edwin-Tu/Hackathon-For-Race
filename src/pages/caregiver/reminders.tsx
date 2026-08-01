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
} from '@mui/material';
import NotificationsActiveIcon from '@mui/icons-material/NotificationsActive';
import EditIcon from '@mui/icons-material/Edit';
import DeleteIcon from '@mui/icons-material/Delete';
import CheckCircleIcon from '@mui/icons-material/CheckCircle';
import AddIcon from '@mui/icons-material/Add';

// 提醒狀態類型
type ReminderStatus = 'pending' | 'completed' | 'missed' | 'cancelled';

// 重要程度
type Importance = 'high' | 'medium' | 'low';

interface Reminder {
  id: string;
  residentId: string;
  residentName: string;
  title: string;
  scheduledAt: Date;
  status: ReminderStatus;
  importance: Importance;
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
    idempotencyKey: 'rem-r2-20260801-1600',
    createdBy: 'family',
  },
];

export default function Reminders() {
  const [tabValue, setTabValue] = useState(0);
  const [reminders, setReminders] = useState<Reminder[]>(mockReminders);
  const [editDialogOpen, setEditDialogOpen] = useState(false);
  const [editReminder, setEditReminder] = useState<Partial<Reminder>>({});

  // 依狀態分類
  const pendingReminders = reminders.filter((r) => r.status === 'pending');
  const completedReminders = reminders.filter((r) => r.status === 'completed');
  const missedReminders = reminders.filter((r) => r.status === 'missed');

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
            <TableCell colSpan={7} align="center">
              <Typography color="text.secondary">沒有提醒</Typography>
            </TableCell>
          </TableRow>
        ) : (
          data.map((reminder) => (
            <TableRow key={reminder.id}>
              <TableCell>{reminder.residentName}</TableCell>
              <TableCell>{reminder.title}</TableCell>
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
        <Tabs value={tabValue} onChange={(_, v) => setTabValue(v)}>
          <Tab label={`待執行 (${pendingReminders.length})`} />
          <Tab label={`已完成 (${completedReminders.length})`} />
          <Tab label={`已錯過 (${missedReminders.length})`} />
        </Tabs>
      </Paper>

      {/* 提醒列表 */}
      <Paper>
        {tabValue === 0 && renderTable(pendingReminders)}
        {tabValue === 1 && renderTable(completedReminders)}
        {tabValue === 2 && renderTable(missedReminders)}
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
