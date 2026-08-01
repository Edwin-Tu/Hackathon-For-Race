// src/components/VideoHistoryCard.tsx
import React from 'react';
import {
  Card,
  CardContent,
  Skeleton,
  Chip,
  Typography,
  Box,
} from '@mui/material';
import type { VideoTask, VideoTaskStatus } from '@/types/video';

interface VideoHistoryCardProps {
  task: VideoTask;
}

// 狀態標籤文字
function getStatusLabel(status: VideoTaskStatus): string {
  switch (status) {
    case 'COMPLETED':
      return '已完成';
    case 'PROCESSING':
      return '生成中';
    case 'PENDING':
      return '等待中';
    case 'FAILED':
      return '失敗';
    default:
      return status;
  }
}

// 狀態顏色
function getStatusColor(status: VideoTaskStatus): 'success' | 'warning' | 'error' | 'default' {
  switch (status) {
    case 'COMPLETED':
      return 'success';
    case 'PROCESSING':
    case 'PENDING':
      return 'warning';
    case 'FAILED':
      return 'error';
    default:
      return 'default';
  }
}

// 格式化日期
function formatDate(timestamp: number): string {
  return new Date(timestamp).toLocaleDateString('zh-TW', {
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  });
}

export function VideoHistoryCard({ task }: VideoHistoryCardProps) {
  const isCompleted = task.status === 'COMPLETED';
  const isProcessing = task.status === 'PROCESSING' || task.status === 'PENDING';

  return (
    <Card sx={{ height: '100%' }}>
      <Box sx={{ height: 120, position: 'relative', bgcolor: 'grey.100' }}>
        {isCompleted && task.videoUrl ? (
          <video
            src={task.videoUrl}
            style={{ width: '100%', height: '100%', objectFit: 'cover' }}
            muted
            playsInline
          />
        ) : (
          <Skeleton
            variant="rectangular"
            height={120}
            animation={isProcessing ? 'wave' : false}
          />
        )}

        {/* 狀態 Badge */}
        <Chip
          label={getStatusLabel(task.status)}
          color={getStatusColor(task.status)}
          size="small"
          sx={{ position: 'absolute', top: 8, right: 8 }}
        />
      </Box>
      <CardContent sx={{ py: 1, '&:last-child': { pb: 1 } }}>
        <Typography variant="caption" color="text.secondary">
          {formatDate(task.createdAt)}
        </Typography>
        {task.status === 'FAILED' && task.errorMessage && (
          <Typography variant="caption" color="error" sx={{ display: 'block' }}>
            {task.errorMessage}
          </Typography>
        )}
      </CardContent>
    </Card>
  );
}
