// src/components/VideoHistoryCard.tsx
import React, { useState } from 'react';
import {
  Card,
  CardContent,
  Skeleton,
  Chip,
  Typography,
  Box,
  Dialog,
  DialogContent,
  IconButton,
  CardActionArea,
} from '@mui/material';
import CloseIcon from '@mui/icons-material/Close';
import PlayArrowIcon from '@mui/icons-material/PlayArrow';
import DeleteIcon from '@mui/icons-material/Delete';
import type { VideoTask, VideoTaskStatus } from '@/types/video';

interface VideoHistoryCardProps {
  task: VideoTask;
  onDelete?: (taskId: string) => void;
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

export function VideoHistoryCard({ task, onDelete }: VideoHistoryCardProps) {
  const [open, setOpen] = useState(false);
  const isCompleted = task.status === 'COMPLETED';
  const isProcessing = task.status === 'PROCESSING' || task.status === 'PENDING';

  const handleOpen = () => {
    if (isCompleted && task.videoUrl) {
      setOpen(true);
    }
  };

  const handleClose = () => {
    setOpen(false);
  };

  const handleDelete = (e: React.MouseEvent) => {
    e.stopPropagation();
    if (onDelete) {
      onDelete(task.taskId);
    }
  };

  return (
    <>
      <Card sx={{ height: '100%', position: 'relative' }}>
        {/* 刪除按鈕 */}
        {onDelete && (
          <IconButton
            size="small"
            onClick={handleDelete}
            sx={{
              position: 'absolute',
              top: 4,
              left: 4,
              zIndex: 2,
              bgcolor: 'rgba(0,0,0,0.5)',
              color: 'white',
              '&:hover': { bgcolor: 'rgba(244,67,54,0.8)' },
            }}
          >
            <DeleteIcon fontSize="small" />
          </IconButton>
        )}
        <CardActionArea onClick={handleOpen} disabled={!isCompleted || !task.videoUrl}>
          <Box sx={{ height: 120, position: 'relative', bgcolor: 'grey.100' }}>
            {isCompleted && task.videoUrl ? (
              <>
                <video
                  src={task.videoUrl}
                  style={{ width: '100%', height: '100%', objectFit: 'cover' }}
                  muted
                  playsInline
                />
                {/* 播放圖示 */}
                <PlayArrowIcon
                  sx={{
                    position: 'absolute',
                    top: '50%',
                    left: '50%',
                    transform: 'translate(-50%, -50%)',
                    fontSize: 48,
                    color: 'white',
                    opacity: 0.8,
                    pointerEvents: 'none',
                  }}
                />
              </>
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
        </CardActionArea>
      </Card>

      {/* 影片預覽 Dialog */}
      <Dialog
        open={open}
        onClose={handleClose}
        maxWidth="md"
        fullWidth
        slotProps={{
          paper: { sx: { bgcolor: 'black' } },
        }}
      >
        <IconButton
          onClick={handleClose}
          sx={{
            position: 'absolute',
            top: 8,
            right: 8,
            color: 'white',
            zIndex: 1,
          }}
        >
          <CloseIcon />
        </IconButton>
        <DialogContent sx={{ p: 0, display: 'flex', justifyContent: 'center' }}>
          {task.videoUrl && (
            <video
              src={task.videoUrl}
              autoPlay
              loop
              controls
              playsInline
              style={{ maxWidth: '100%', maxHeight: '80vh' }}
            />
          )}
        </DialogContent>
      </Dialog>
    </>
  );
}
