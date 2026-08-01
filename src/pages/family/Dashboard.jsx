import React from 'react';
import { Grid, Card, Typography } from '@mui/material';
import { useFamilyStats } from '../../hooks/useFamilyStats';

export default function Dashboard() {
  const { stats, loading, error } = useFamilyStats();
  if (loading) return <Typography>載入中…</Typography>;
  if (error) return <Typography 顏色="error">資料取得失敗</Typography>;

  return (
    <Grid container spacing={3}>
      <Grid size={{ xs: 12, sm: 4 }}>
        <Card sx={{ p: 2 }}>
          <Typography variant="h6">血糖</Typography>
          <Typography variant="h4">{stats.glucose} mg/dL</Typography>
        </Card>
      </Grid>
      <Grid size={{ xs: 12, sm: 4 }}>
        <Card sx={{ p: 2 }}>
          <Typography variant="h6">心率</Typography>
          <Typography variant="h4">{stats.heartRate} bpm</Typography>
        </Card>
      </Grid>
      <Grid size={{ xs: 12, sm: 4 }}>
        <Card sx={{ p: 2 }}>
          <Typography variant="h6">未處理警示</Typography>
          <Typography variant="h4">{stats.unreadAlerts}</Typography>
        </Card>
      </Grid>
    </Grid>
  );
}
