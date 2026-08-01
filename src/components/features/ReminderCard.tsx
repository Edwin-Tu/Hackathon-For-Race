'use client';
import React from 'react';
import {
  Card,
  CardContent,
  Box,
  Typography,
  Chip,
  IconButton,
  Tooltip,
} from '@mui/material';
import { useTheme } from '@mui/material/styles';
import CheckCircleIcon from '@mui/icons-material/CheckCircle';
import EditIcon from '@mui/icons-material/Edit';
import DeleteIcon from '@mui/icons-material/Delete';
import AccessTimeIcon from '@mui/icons-material/AccessTime';
import MedicationIcon from '@mui/icons-material/Medication';
import FavoriteIcon from '@mui/icons-material/Favorite';
import EventIcon from '@mui/icons-material/Event';
import MoreHorizIcon from '@mui/icons-material/MoreHoriz';

// 類型定義
type ReminderStatus = 'pending' | 'completed' | 'missed' | 'cancelled';
type Importance = 'high' | 'medium' | 'low';
type ReminderCategory = 'medication' | 'health' | 'appointment' | 'other';

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

// 配置
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

const categoryConfig: Record<ReminderCategory, { label: string; icon: React.ReactElement; color: 'error' | 'success' | 'info' | 'default' }> = {
  medication: { label: '用藥', icon: <MedicationIcon sx={{ fontSize: 16 }} />, color: 'error' },
  health: { label: '健康狀況', icon: <FavoriteIcon sx={{ fontSize: 16 }} />, color: 'success' },
  appointment: { label: '回診', icon: <EventIcon sx={{ fontSize: 16 }} />, color: 'info' },
  other: { label: '其他', icon: <MoreHorizIcon sx={{ fontSize: 16 }} />, color: 'default' },
};

interface ReminderCardProps {
  reminder: Reminder;
  onComplete?: (id: string) => void;
  onEdit?: (reminder: Reminder) => void;
  onDelete?: (id: string) => void;
}

export default function ReminderCard({ reminder, onComplete, onEdit, onDelete }: ReminderCardProps) {
  const theme = useTheme();

  const formatDateTime = (date: Date) => {
    return date.toLocaleString('zh-TW', {
      month: 'numeric',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    });
  };

  return (
    <Card
      sx={{
        mb: 1.5,
        border: reminder.status === 'pending' && reminder.importance === 'high'
          ? `1px solid ${theme.palette.error.main}`
          : `1px solid ${theme.palette.divider}`,
      }}
    >
      <CardContent sx={{ p: 2, '&:last-child': { pb: 2 } }}>
        {/* 頂部：類別與優先級 */}
        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 1 }}>
          <Chip
            size="small"
            icon={categoryConfig[reminder.category].icon}
            label={categoryConfig[reminder.category].label}
            color={categoryConfig[reminder.category].color}
            sx={{ height: 24 }}
          />
          <Chip
            size="small"
            label={`${importanceConfig[reminder.importance].label}優先`}
            color={importanceConfig[reminder.importance].color}
            variant="outlined"
            sx={{ height: 24 }}
          />
        </Box>

        {/* 住民名稱 */}
        <Typography variant="caption" color="text.secondary">
          {reminder.residentName}
        </Typography>

        {/* 提醒內容 */}
        <Typography
          variant="body1"
          sx={{
            fontWeight: 500,
            mt: 0.5,
            mb: 1,
            display: '-webkit-box',
            WebkitLineClamp: 2,
            WebkitBoxOrient: 'vertical',
            overflow: 'hidden',
          }}
        >
          {reminder.title}
        </Typography>

        {/* 底部：時間、狀態、操作按鈕 */}
        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1.5 }}>
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
              <AccessTimeIcon sx={{ fontSize: 14, color: 'text.secondary' }} />
              <Typography variant="caption" color="text.secondary">
                {formatDateTime(reminder.scheduledAt)}
              </Typography>
            </Box>
            <Chip
              size="small"
              label={statusConfig[reminder.status].label}
              color={statusConfig[reminder.status].color}
              sx={{ height: 20, fontSize: '0.7rem' }}
            />
          </Box>

          {/* 操作按鈕 */}
          <Box sx={{ display: 'flex', gap: 0.5 }}>
            {reminder.status === 'pending' && onComplete && (
              <Tooltip title="標記完成">
                <IconButton
                  size="small"
                  color="success"
                  onClick={() => onComplete(reminder.id)}
                  sx={{ minWidth: 44, minHeight: 44 }}
                >
                  <CheckCircleIcon />
                </IconButton>
              </Tooltip>
            )}
            {onEdit && (
              <Tooltip title="編輯">
                <IconButton
                  size="small"
                  onClick={() => onEdit(reminder)}
                  sx={{ minWidth: 44, minHeight: 44 }}
                >
                  <EditIcon />
                </IconButton>
              </Tooltip>
            )}
            {onDelete && (
              <Tooltip title="刪除">
                <IconButton
                  size="small"
                  color="error"
                  onClick={() => onDelete(reminder.id)}
                  sx={{ minWidth: 44, minHeight: 44 }}
                >
                  <DeleteIcon />
                </IconButton>
              </Tooltip>
            )}
          </Box>
        </Box>
      </CardContent>
    </Card>
  );
}

export type { Reminder, ReminderStatus, Importance, ReminderCategory };
