import React, { useState } from 'react';
import { Button, Dialog, DialogTitle, DialogContent, DialogActions, TextField, List, ListItem, ListItemText } from '@mui/material';
import { useFamilyAuth } from '../../hooks/useFamilyAuth';

export default function Authorizations() {
  const { data: authList, refetch } = useFamilyAuth();
  const [open, setOpen] = useState(false);
  const [newUser, setNewUser] = useState('');

  const handleAdd = async () => {
    await fetch('/api/auth/grant', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ username: newUser }),
    });
    setOpen(false);
    setNewUser('');
    refetch();
  };

  return (
    <>
      <Button variant="contained" onClick={() => setOpen(true)}>
        新增授權
      </Button>
      <List>
        {authList?.map((a) => (
          <ListItem key={a.id} divider>
            <ListItemText primary={a.username} secondary={a.status} />
          </ListItem>
        ))}
      </List>

      <Dialog open={open} onClose={() => setOpen(false)}>
        <DialogTitle>新增授權使用者</DialogTitle>
        <DialogContent>
          <TextField
            label="使用者帳號"
            fullWidth
            value={newUser}
            onChange={(e) => setNewUser(e.target.value)}
          />
        </DialogContent>
        <DialogActions>
          <Button onClick={handleAdd}>確認</Button>
          <Button onClick={() => setOpen(false)}>取消</Button>
        </DialogActions>
      </Dialog>
    </>
  );
}
