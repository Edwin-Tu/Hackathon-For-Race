import React from 'react';
import { useGetResidentsQuery } from '../../store/apiSlice';
import { Container, Typography, List, ListItem, ListItemText } from '@mui/material';

const ResidentList: React.FC = () => {
  const { data: residents, isLoading, error } = useGetResidentsQuery();

  if (isLoading) return <Typography>載入中…</Typography>;
  if (error) return <Typography>取得住民失敗</Typography>;

  return (
    <Container>
      <Typography variant="h4" gutterBottom>
        住民列表
      </Typography>
      <List>
        {residents?.map((r) => (
          <ListItem key={r.id} button>
            <ListItemText primary={r.name} secondary={`ID: ${r.id}`} />
          </ListItem>
        ))}
      </List>
    </Container>
  );
};

export default ResidentList;
