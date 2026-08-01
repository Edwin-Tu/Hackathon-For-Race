import React, { useEffect, useState } from 'react';
import { Table, TableHead, TableBody, TableRow, TableCell, IconButton, Dialog, DialogTitle, DialogContent, DialogActions, TextField, Button } from '@mui/material';
import { Edit, Delete } from '@mui/icons-material';

// Placeholder API 呼叫，實際會使用 RTK Query 或 fetch
const fetchUsers = async () => {
  const res = await fetch('/api/admin/users');
  return res.json();
};
const createUser = async (user) => {
  await fetch('/api/admin/users', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(user) });
};
const updateUser = async (user) => {
  await fetch(`/api/admin/users/${user.id}`, { method: 'PUT', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(user) });
};
const deleteUser = async (id) => {
  await fetch(`/api/admin/users/${id}`, { method: 'DELETE' });
};

export default function Users() {
  const [users, setUsers] = useState([]);
  const [open, setOpen] = useState(false);
  const [editUser, setEditUser] = useState({});

  const load = async () => { setUsers(await fetchUsers()); };
  useEffect(() => { load(); }, []);

  const handleSave = async () => {
    if (editUser.id) await updateUser(editUser);
    else await createUser(editUser);
    setOpen(false);
    load();
  };

  return (
    <>
      <Button variant="contained" onClick={() => { setEditUser({}); setOpen(true); }}>新增使用者</Button>
      <Table>
        <TableHead>
          <TableRow>
            <TableCell>帳號</TableCell><TableCell>角色</TableCell><TableCell>操作</TableCell>
          </TableRow>
        </TableHead>
        <TableBody>
          {users.map(u => (
            <TableRow key={u.id}>
              <TableCell>{u.username}</TableCell>
              <TableCell>{u.role}</TableCell>
              <TableCell>
                <IconButton onClick={() => { setEditUser(u); setOpen(true); }}><Edit /></IconButton>
                <IconButton onClick={() => { deleteUser(u.id).then(load); }}><Delete /></IconButton>
              </TableCell>
            </TableRow>
          ))}
        </TableBody>
      </Table>
      <Dialog open={open} onClose={() => setOpen(false)}>
        <DialogTitle>{editUser?.id ? '編輯使用者' : '新增使用者'}</DialogTitle>
        <DialogContent>
          <TextField label="帳號" fullWidth value={editUser.username || ''} onChange={e => setEditUser({ ...editUser, username: e.target.value })} />
          <TextField label="角色" fullWidth value={editUser.role || ''} onChange={e => setEditUser({ ...editUser, role: e.target.value })} sx={{ mt: 2 }} />
        </DialogContent>
        <DialogActions>
          <Button onClick={handleSave}>儲存</Button>
          <Button onClick={() => setOpen(false)}>取消</Button>
        </DialogActions>
      </Dialog>
    </>
  );
}
