// src/components/VideoHistoryList.tsx
import React from 'react';
import { Box, Typography, Skeleton } from '@mui/material';
import Grid from '@mui/material/Grid';
import { useGetVideoHistoryQuery, useDeleteVideoTaskMutation, videoApi } from '@/store/videoApi';
import { useDispatch } from 'react-redux';
import { VideoHistoryCard } from './VideoHistoryCard';

interface VideoHistoryListProps {
  residentId: string;
}

export function VideoHistoryList({ residentId }: VideoHistoryListProps) {
  const dispatch = useDispatch();
  const { data, isLoading, isError } = useGetVideoHistoryQuery(residentId, {
    skip: !residentId,
  });
  const [deleteTask] = useDeleteVideoTaskMutation();

  const handleDelete = async (taskId: string) => {
    if (!confirm('確定要刪除這個影片嗎？')) return;
    
    try {
      await deleteTask(taskId).unwrap();
      // 刷新歷史列表
      dispatch(videoApi.util.invalidateTags([{ type: 'VideoTask', id: `history-${residentId}` }]));
    } catch (error) {
      console.error('Delete failed:', error);
      alert('刪除失敗');
    }
  };

  if (!residentId) return null;

  if (isLoading) {
    return (
      <Box sx={{ mt: 3 }}>
        <Typography variant="h6" gutterBottom>
          歷史影片
        </Typography>
        <Grid container spacing={2}>
          {[1, 2, 3].map((i) => (
            <Grid size={{ xs: 6, sm: 4 }} key={i}>
              <Skeleton variant="rectangular" height={160} />
            </Grid>
          ))}
        </Grid>
      </Box>
    );
  }

  if (isError) {
    return (
      <Box sx={{ mt: 3 }}>
        <Typography color="error">載入歷史紀錄失敗</Typography>
      </Box>
    );
  }

  if (!data?.tasks?.length) {
    return (
      <Box sx={{ mt: 3 }}>
        <Typography variant="h6" gutterBottom>
          歷史影片
        </Typography>
        <Typography color="text.secondary">尚無歷史紀錄</Typography>
      </Box>
    );
  }

  return (
    <Box sx={{ mt: 3 }}>
      <Typography variant="h6" gutterBottom>
        歷史影片
      </Typography>
      <Grid container spacing={2}>
        {data.tasks.map((task) => (
          <Grid size={{ xs: 6, sm: 4 }} key={task.taskId}>
            <VideoHistoryCard task={task} onDelete={handleDelete} />
          </Grid>
        ))}
      </Grid>
    </Box>
  );
}
