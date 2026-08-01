import React from 'react';
import { List, ListItem, ListItemText, Typography } from '@mui/material';
import { useFamilyNotifications } from '../../hooks/useFamilyNotifications';

export default function Notifications() {
  const { data: notes, loading, error } = useFamilyNotifications();
  if (loading) return <Typography>載入中…</Typography>;
  if (error) return <Typography 顏色="error">取得通知失敗</Typography>;

  return (
    <List>
      {notes.map((n) => (
        <ListItem key={n.id} divider>
          <ListItemText primary={n.title} secondary={n.time} />
        </ListItem>
      ))}
    </List>
  );
}
