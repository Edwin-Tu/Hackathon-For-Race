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
  Alert,
  Snackbar,
} from '@mui/material';
import MemoryIcon from '@mui/icons-material/Memory';
import EditIcon from '@mui/icons-material/Edit';
import DeleteIcon from '@mui/icons-material/Delete';
import HistoryIcon from '@mui/icons-material/History';
import WarningIcon from '@mui/icons-material/Warning';

// 記憶類型
type MemoryType = 'life_event' | 'preference' | 'candidate';
type MemoryStatus = 'active' | 'corrected' | 'deleted';
type EventType = 'meal' | 'activity' | 'medication' | 'sleep' | 'mood' | 'schedule';

interface Memory {
  id: string;
  residentId: string;
  residentName: string;
  memoryType: MemoryType;
  eventType?: EventType;
  content: string;
  originalContent: string;
  sourceText: string;
  confidence: number;
  status: MemoryStatus;
  createdAt: Date;
  correctedAt?: Date;
  correctedBy?: string;
  correctionReason?: string;
}

// 類型配置
const memoryTypeConfig: Record<MemoryType, { label: string; color: 'primary' | 'secondary' | 'warning' }> = {
  life_event: { label: '生活事件', color: 'primary' },
  preference: { label: '偏好記憶', color: 'secondary' },
  candidate: { label: '候選記憶', color: 'warning' },
};

const eventTypeLabels: Record<EventType, string> = {
  meal: '飲食',
  activity: '活動',
  medication: '用藥',
  sleep: '睡眠',
  mood: '情緒',
  schedule: '行程',
};

// 模擬記憶資料
const mockMemories: Memory[] = [
  {
    id: '1',
    residentId: 'r1',
    residentName: '王奶奶',
    memoryType: 'life_event',
    eventType: 'medication',
    content: '服用降血壓藥',
    originalContent: '服用降血壓藥',
    sourceText: '我早上八點吃過藥了',
    confidence: 0.95,
    status: 'active',
    createdAt: new Date('2026-08-01T08:05:00'),
  },
  {
    id: '2',
    residentId: 'r1',
    residentName: '王奶奶',
    memoryType: 'life_event',
    eventType: 'meal',
    content: '早餐：稀飯、豆漿、饅頭',
    originalContent: '早餐：稀飯、饅頭',
    sourceText: '早上吃了稀飯和饅頭',
    confidence: 0.88,
    status: 'corrected',
    createdAt: new Date('2026-08-01T07:35:00'),
    correctedAt: new Date('2026-08-01T09:00:00'),
    correctedBy: 'caregiver_zhang',
    correctionReason: '補充豆漿',
  },
  {
    id: '3',
    residentId: 'r1',
    residentName: '王奶奶',
    memoryType: 'preference',
    content: '喜歡被稱呼「王奶奶」',
    originalContent: '喜歡被稱呼「王奶奶」',
    sourceText: '你可以叫我王奶奶',
    confidence: 0.92,
    status: 'active',
    createdAt: new Date('2026-07-28T10:00:00'),
  },
  {
    id: '4',
    residentId: 'r1',
    residentName: '王奶奶',
    memoryType: 'candidate',
    eventType: 'mood',
    content: '今天心情很好',
    originalContent: '今天心情很好',
    sourceText: '今天心情很好，跟女兒講電話了',
    confidence: 0.65,
    status: 'active',
    createdAt: new Date('2026-08-01T14:10:00'),
  },
  {
    id: '5',
    residentId: 'r2',
    residentName: '李爺爺',
    memoryType: 'life_event',
    eventType: 'activity',
    content: '早上散步 20 分鐘',
    originalContent: '早上散步 30 分鐘',
    sourceText: '早上去公園走了一下',
    confidence: 0.7,
    status: 'deleted',
    createdAt: new Date('2026-08-01T09:00:00'),
    correctedAt: new Date('2026-08-01T10:00:00'),
    correctedBy: 'caregiver_li',
    correctionReason: '時間錯誤，實際是在室內活動',
  },
];

export default function MemoryCorrection() {
  const [memories, setMemories] = useState<Memory[]>(mockMemories);
  const [selectedResident, setSelectedResident] = useState<string>('all');
  const [selectedType, setSelectedType] = useState<string>('all');
  const [showDeleted, setShowDeleted] = useState(false);

  const [editDialogOpen, setEditDialogOpen] = useState(false);
  const [deleteDialogOpen, setDeleteDialogOpen] = useState(false);
  const [selectedMemory, setSelectedMemory] = useState<Memory | null>(null);
  const [editContent, setEditContent] = useState('');
  const [editReason, setEditReason] = useState('');
  const [snackbar, setSnackbar] = useState({ open: false, message: '' });

  // 篩選記憶
  const filteredMemories = memories
    .filter((m) => selectedResident === 'all' || m.residentId === selectedResident)
    .filter((m) => selectedType === 'all' || m.memoryType === selectedType)
    .filter((m) => showDeleted || m.status !== 'deleted')
    .sort((a, b) => b.createdAt.getTime() - a.createdAt.getTime());

  // 取得所有住民
  const residents = Array.from(new Set(memories.map((m) => m.residentId))).map((id) => ({
    id,
    name: memories.find((m) => m.residentId === id)?.residentName || '',
  }));

  // 開啟編輯對話框
  const handleEdit = (memory: Memory) => {
    setSelectedMemory(memory);
    setEditContent(memory.content);
    setEditReason('');
    setEditDialogOpen(true);
  };

  // 開啟刪除確認對話框
  const handleDeleteClick = (memory: Memory) => {
    setSelectedMemory(memory);
    setEditReason('');
    setDeleteDialogOpen(true);
  };

  // 儲存修正
  const handleSaveCorrection = () => {
    if (!selectedMemory || !editReason.trim()) return;

    setMemories((prev) =>
      prev.map((m) =>
        m.id === selectedMemory.id
          ? {
              ...m,
              content: editContent,
              status: 'corrected' as MemoryStatus,
              correctedAt: new Date(),
              correctedBy: 'current_user',
              correctionReason: editReason,
            }
          : m
      )
    );

    setEditDialogOpen(false);
    setSnackbar({ open: true, message: '記憶已修正' });
  };

  // 確認刪除
  const handleConfirmDelete = () => {
    if (!selectedMemory || !editReason.trim()) return;

    setMemories((prev) =>
      prev.map((m) =>
        m.id === selectedMemory.id
          ? {
              ...m,
              status: 'deleted' as MemoryStatus,
              correctedAt: new Date(),
              correctedBy: 'current_user',
              correctionReason: editReason,
            }
          : m
      )
    );

    setDeleteDialogOpen(false);
    setSnackbar({ open: true, message: '記憶已標記為刪除' });
  };

  return (
    <Container maxWidth="lg" sx={{ py: 2 }}>
      <Typography variant="h4" gutterBottom sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
        <MemoryIcon color="primary" />
        記憶修正
      </Typography>
      <Typography variant="body2" color="text.secondary" gutterBottom>
        查看並修正 AI 記錄的生活事件或記憶。所有修正都會保留原始內容與修正原因，供追溯。
      </Typography>

      {/* 篩選器 */}
      <Paper sx={{ p: 2, mb: 3 }}>
        <Box sx={{ display: 'flex', gap: 2, flexWrap: 'wrap', alignItems: 'center' }}>
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

          <FormControl size="small" sx={{ minWidth: 150 }}>
            <InputLabel>記憶類型</InputLabel>
            <Select
              value={selectedType}
              label="記憶類型"
              onChange={(e) => setSelectedType(e.target.value)}
            >
              <MenuItem value="all">全部</MenuItem>
              {Object.entries(memoryTypeConfig).map(([key, config]) => (
                <MenuItem key={key} value={key}>
                  {config.label}
                </MenuItem>
              ))}
            </Select>
          </FormControl>

          <Button
            variant={showDeleted ? 'contained' : 'outlined'}
            size="small"
            onClick={() => setShowDeleted(!showDeleted)}
          >
            {showDeleted ? '隱藏已刪除' : '顯示已刪除'}
          </Button>
        </Box>
      </Paper>

      {/* 記憶列表 */}
      <Paper>
        <Table>
          <TableHead>
            <TableRow>
              <TableCell>住民</TableCell>
              <TableCell>類型</TableCell>
              <TableCell>內容</TableCell>
              <TableCell>原始語句</TableCell>
              <TableCell>信心度</TableCell>
              <TableCell>狀態</TableCell>
              <TableCell>操作</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {filteredMemories.length === 0 ? (
              <TableRow>
                <TableCell colSpan={7} align="center">
                  <Typography color="text.secondary">沒有記憶紀錄</Typography>
                </TableCell>
              </TableRow>
            ) : (
              filteredMemories.map((memory) => (
                <TableRow
                  key={memory.id}
                  sx={{ opacity: memory.status === 'deleted' ? 0.5 : 1 }}
                >
                  <TableCell>{memory.residentName}</TableCell>
                  <TableCell>
                    <Box sx={{ display: 'flex', flexDirection: 'column', gap: 0.5 }}>
                      <Chip
                        size="small"
                        label={memoryTypeConfig[memory.memoryType].label}
                        color={memoryTypeConfig[memory.memoryType].color}
                      />
                      {memory.eventType && (
                        <Typography variant="caption" color="text.secondary">
                          {eventTypeLabels[memory.eventType]}
                        </Typography>
                      )}
                    </Box>
                  </TableCell>
                  <TableCell>
                    <Typography variant="body2" color="text.primary">{memory.content}</Typography>
                    {memory.status === 'corrected' && memory.originalContent !== memory.content && (
                      <Typography variant="caption" color="text.secondary" sx={{ display: 'block', mt: 0.5 }}>
                        <s>原始：{memory.originalContent}</s>
                      </Typography>
                    )}
                  </TableCell>
                  <TableCell>
                    <Typography variant="body2" color="text.primary" sx={{ fontStyle: 'italic' }}>
                      「{memory.sourceText}」
                    </Typography>
                  </TableCell>
                  <TableCell>
                    <Chip
                      size="small"
                      label={`${Math.round(memory.confidence * 100)}%`}
                      color={memory.confidence >= 0.8 ? 'success' : memory.confidence >= 0.6 ? 'warning' : 'error'}
                      variant="outlined"
                    />
                  </TableCell>
                  <TableCell>
                    <Box>
                      <Chip
                        size="small"
                        label={memory.status === 'active' ? '有效' : memory.status === 'corrected' ? '已修正' : '已刪除'}
                        color={memory.status === 'active' ? 'success' : memory.status === 'corrected' ? 'info' : 'error'}
                      />
                      {memory.correctedBy && (
                        <Typography variant="caption" color="text.secondary" sx={{ display: 'block' }}>
                          {memory.correctedBy}
                        </Typography>
                      )}
                    </Box>
                  </TableCell>
                  <TableCell>
                    {memory.status !== 'deleted' && (
                      <>
                        <IconButton size="small" onClick={() => handleEdit(memory)}>
                          <EditIcon />
                        </IconButton>
                        <IconButton size="small" color="error" onClick={() => handleDeleteClick(memory)}>
                          <DeleteIcon />
                        </IconButton>
                      </>
                    )}
                    {memory.correctionReason && (
                      <IconButton size="small" title={`修正原因：${memory.correctionReason}`}>
                        <HistoryIcon />
                      </IconButton>
                    )}
                  </TableCell>
                </TableRow>
              ))
            )}
          </TableBody>
        </Table>
      </Paper>

      {/* 編輯對話框 */}
      <Dialog open={editDialogOpen} onClose={() => setEditDialogOpen(false)} maxWidth="sm" fullWidth>
        <DialogTitle>修正記憶</DialogTitle>
        <DialogContent>
          <Alert severity="info" sx={{ mb: 2 }}>
            修正後原始內容會保留，供日後追溯。
          </Alert>
          <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2, mt: 1 }}>
            <TextField
              label="原始語句"
              fullWidth
              value={selectedMemory?.sourceText || ''}
              disabled
              multiline
            />
            <TextField
              label="修正後內容"
              fullWidth
              value={editContent}
              onChange={(e) => setEditContent(e.target.value)}
              multiline
              rows={2}
            />
            <TextField
              label="修正原因"
              fullWidth
              value={editReason}
              onChange={(e) => setEditReason(e.target.value)}
              required
              helperText="請說明修正原因"
            />
          </Box>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setEditDialogOpen(false)}>取消</Button>
          <Button variant="contained" onClick={handleSaveCorrection} disabled={!editReason.trim()}>
            儲存修正
          </Button>
        </DialogActions>
      </Dialog>

      {/* 刪除確認對話框 */}
      <Dialog open={deleteDialogOpen} onClose={() => setDeleteDialogOpen(false)}>
        <DialogTitle sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
          <WarningIcon color="error" />
          刪除記憶
        </DialogTitle>
        <DialogContent>
          <Alert severity="warning" sx={{ mb: 2 }}>
            刪除後此記憶將不再使用，但會保留紀錄供追溯。
          </Alert>
          <Typography variant="body2" gutterBottom>
            即將刪除：{selectedMemory?.content}
          </Typography>
          <TextField
            label="刪除原因"
            fullWidth
            value={editReason}
            onChange={(e) => setEditReason(e.target.value)}
            required
            sx={{ mt: 2 }}
          />
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setDeleteDialogOpen(false)}>取消</Button>
          <Button variant="contained" color="error" onClick={handleConfirmDelete} disabled={!editReason.trim()}>
            確認刪除
          </Button>
        </DialogActions>
      </Dialog>

      {/* Snackbar */}
      <Snackbar
        open={snackbar.open}
        autoHideDuration={3000}
        onClose={() => setSnackbar({ ...snackbar, open: false })}
        message={snackbar.message}
      />
    </Container>
  );
}
