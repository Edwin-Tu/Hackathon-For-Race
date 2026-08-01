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
  TableContainer,
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
  Avatar,
  Alert,
  InputAdornment,
  Tooltip,
  Autocomplete,
  Fade,
  Grow,
  CircularProgress,
  Backdrop,
  Zoom,
} from '@mui/material';
import { useTheme, alpha } from '@mui/material/styles';
import PeopleIcon from '@mui/icons-material/People';
import AddIcon from '@mui/icons-material/Add';
import EditIcon from '@mui/icons-material/Edit';
import DeleteIcon from '@mui/icons-material/Delete';
import SearchIcon from '@mui/icons-material/Search';
import BlockIcon from '@mui/icons-material/Block';
import CheckCircleIcon from '@mui/icons-material/CheckCircle';
import PersonIcon from '@mui/icons-material/Person';
import LockResetIcon from '@mui/icons-material/LockReset';
import WarningAmberIcon from '@mui/icons-material/WarningAmber';

// 使用者角色
type UserRole = 'ADMIN' | 'CAREGIVER' | 'FAMILY' | 'RESIDENT';

// 帳號狀態
type UserStatus = 'active' | 'inactive' | 'suspended';

// 使用者定義
interface User {
  id: string;
  username: string;
  displayName: string;
  email: string;
  role: UserRole;
  status: UserStatus;
  assignedResidents: string[]; // 指派的住民 ID
  createdAt: Date;
  lastLoginAt?: Date;
}

// 角色配置
const roleConfig: Record<UserRole, { label: string; color: 'error' | 'warning' | 'info' | 'success' }> = {
  ADMIN: { label: '系統管理者', color: 'error' },
  CAREGIVER: { label: '照護人員', color: 'info' },
  FAMILY: { label: '家屬', color: 'success' },
  RESIDENT: { label: '住民', color: 'warning' },
};

// 狀態配置
const statusConfig: Record<UserStatus, { label: string; color: 'success' | 'default' | 'error' }> = {
  active: { label: '啟用', color: 'success' },
  inactive: { label: '停用', color: 'default' },
  suspended: { label: '凍結', color: 'error' },
};

// 模擬住民列表
const mockResidents = [
  { id: 'r1', name: '王奶奶' },
  { id: 'r2', name: '李爺爺' },
  { id: 'r3', name: '張奶奶' },
  { id: 'r4', name: '陳爺爺' },
];

// 模擬使用者資料
const mockUsers: User[] = [
  {
    id: 'u1',
    username: 'admin',
    displayName: '系統管理員',
    email: 'admin@example.com',
    role: 'ADMIN',
    status: 'active',
    assignedResidents: [],
    createdAt: new Date('2026-01-01'),
    lastLoginAt: new Date('2026-08-01T09:00:00'),
  },
  {
    id: 'u2',
    username: 'caregiver_zhang',
    displayName: '張護理師',
    email: 'zhang@example.com',
    role: 'CAREGIVER',
    status: 'active',
    assignedResidents: ['r1', 'r2'],
    createdAt: new Date('2026-02-15'),
    lastLoginAt: new Date('2026-08-01T08:30:00'),
  },
  {
    id: 'u3',
    username: 'caregiver_li',
    displayName: '李照服員',
    email: 'li@example.com',
    role: 'CAREGIVER',
    status: 'active',
    assignedResidents: ['r3', 'r4'],
    createdAt: new Date('2026-03-01'),
    lastLoginAt: new Date('2026-07-31T17:00:00'),
  },
  {
    id: 'u4',
    username: 'family_wang',
    displayName: '王小明',
    email: 'wang.ming@example.com',
    role: 'FAMILY',
    status: 'active',
    assignedResidents: ['r1'],
    createdAt: new Date('2026-04-10'),
    lastLoginAt: new Date('2026-08-01T10:15:00'),
  },
  {
    id: 'u5',
    username: 'family_wang2',
    displayName: '王小華',
    email: 'wang.hua@example.com',
    role: 'FAMILY',
    status: 'active',
    assignedResidents: ['r1'],
    createdAt: new Date('2026-04-15'),
    lastLoginAt: new Date('2026-07-30T14:00:00'),
  },
  {
    id: 'u6',
    username: 'resident_wang',
    displayName: '王奶奶',
    email: '',
    role: 'RESIDENT',
    status: 'active',
    assignedResidents: ['r1'],
    createdAt: new Date('2026-01-15'),
    lastLoginAt: new Date('2026-08-01T14:30:00'),
  },
  {
    id: 'u7',
    username: 'test_user',
    displayName: '測試帳號',
    email: 'test@example.com',
    role: 'CAREGIVER',
    status: 'inactive',
    assignedResidents: [],
    createdAt: new Date('2026-05-01'),
  },
];

export default function Users() {
  const theme = useTheme();
  const [users, setUsers] = useState<User[]>(mockUsers);
  const [searchText, setSearchText] = useState('');
  const [filterRole, setFilterRole] = useState<string>('all');
  const [filterStatus, setFilterStatus] = useState<string>('all');
  const [editDialogOpen, setEditDialogOpen] = useState(false);
  const [deleteDialogOpen, setDeleteDialogOpen] = useState(false);
  const [editUser, setEditUser] = useState<Partial<User>>({});
  const [selectedUserId, setSelectedUserId] = useState<string | null>(null);
  const [saving, setSaving] = useState(false);
  const [hoveredRow, setHoveredRow] = useState<string | null>(null);

  // 篩選使用者
  const filteredUsers = users
    .filter((u) => filterRole === 'all' || u.role === filterRole)
    .filter((u) => filterStatus === 'all' || u.status === filterStatus)
    .filter(
      (u) =>
        !searchText ||
        u.username.toLowerCase().includes(searchText.toLowerCase()) ||
        u.displayName.toLowerCase().includes(searchText.toLowerCase()) ||
        u.email.toLowerCase().includes(searchText.toLowerCase())
    );

  // 開啟新增對話框
  const handleAdd = () => {
    setEditUser({
      username: '',
      displayName: '',
      email: '',
      role: 'CAREGIVER',
      status: 'active',
      assignedResidents: [],
    });
    setEditDialogOpen(true);
  };

  // 開啟編輯對話框
  const handleEdit = (user: User) => {
    setEditUser({ ...user });
    setEditDialogOpen(true);
  };

  // 開啟刪除確認對話框
  const handleDeleteClick = (userId: string) => {
    setSelectedUserId(userId);
    setDeleteDialogOpen(true);
  };

  // 切換帳號狀態
  const toggleStatus = (userId: string) => {
    setUsers((prev) =>
      prev.map((u) =>
        u.id === userId
          ? { ...u, status: u.status === 'active' ? ('inactive' as UserStatus) : ('active' as UserStatus) }
          : u
      )
    );
  };

  // 儲存使用者
  const handleSave = async () => {
    setSaving(true);
    // 模擬 API 延遲
    await new Promise((resolve) => setTimeout(resolve, 800));
    
    if (editUser.id) {
      // 更新
      setUsers((prev) => prev.map((u) => (u.id === editUser.id ? ({ ...u, ...editUser } as User) : u)));
    } else {
      // 新增
      const newUser: User = {
        id: `u${Date.now()}`,
        username: editUser.username || '',
        displayName: editUser.displayName || '',
        email: editUser.email || '',
        role: editUser.role || 'CAREGIVER',
        status: editUser.status || 'active',
        assignedResidents: editUser.assignedResidents || [],
        createdAt: new Date(),
      };
      setUsers((prev) => [...prev, newUser]);
    }
    setSaving(false);
    setEditDialogOpen(false);
  };

  // 確認刪除
  const handleConfirmDelete = () => {
    if (selectedUserId) {
      setUsers((prev) => prev.filter((u) => u.id !== selectedUserId));
    }
    setDeleteDialogOpen(false);
    setSelectedUserId(null);
  };

  // 取得住民名稱
  const getResidentNames = (residentIds: string[]) => {
    return residentIds
      .map((id) => mockResidents.find((r) => r.id === id)?.name || id)
      .join('、');
  };

  return (
    <Container maxWidth="lg" sx={{ py: 3 }}>
      {/* 頁面標題 */}
      <Fade in timeout={300}>
        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 4 }}>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
            <Avatar 
              sx={{ 
                bgcolor: theme.palette.primary.main,
                width: 48,
                height: 48,
              }}
            >
              <PeopleIcon sx={{ fontSize: 28 }} />
            </Avatar>
            <Box>
              <Typography variant="h4" fontWeight={700}>
                使用者管理
              </Typography>
              <Typography variant="body2" color="text.secondary">
                管理系統中所有使用者帳號與權限
              </Typography>
            </Box>
          </Box>
          <Button 
            variant="contained" 
            startIcon={<AddIcon />} 
            onClick={handleAdd}
            sx={{
              px: 3,
              boxShadow: `0 4px 14px ${alpha(theme.palette.primary.main, 0.4)}`,
            }}
          >
            新增使用者
          </Button>
        </Box>
      </Fade>

      {/* 篩選器 */}
      <Fade in timeout={400}>
        <Paper sx={{ p: 2.5, mb: 3 }}>
          <Box sx={{ display: 'flex', gap: 2, flexWrap: 'wrap', alignItems: 'center' }}>
            <TextField
              size="small"
              placeholder="搜尋帳號、姓名或 Email"
              value={searchText}
              onChange={(e) => setSearchText(e.target.value)}
              sx={{ minWidth: 280, flex: { xs: '1 1 100%', sm: '0 1 auto' } }}
              slotProps={{
                input: {
                  startAdornment: (
                    <InputAdornment position="start">
                      <SearchIcon color="action" />
                    </InputAdornment>
                  ),
                },
              }}
            />
            <FormControl size="small" sx={{ minWidth: 150 }}>
              <InputLabel>角色</InputLabel>
              <Select value={filterRole} label="角色" onChange={(e) => setFilterRole(e.target.value)}>
                <MenuItem value="all">全部角色</MenuItem>
                {Object.entries(roleConfig).map(([key, config]) => (
                  <MenuItem key={key} value={key}>
                    <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                      <Box 
                        sx={{ 
                          width: 8, 
                          height: 8, 
                          borderRadius: '50%',
                          bgcolor: `${config.color}.main`,
                        }} 
                      />
                      {config.label}
                    </Box>
                  </MenuItem>
                ))}
              </Select>
            </FormControl>
            <FormControl size="small" sx={{ minWidth: 120 }}>
              <InputLabel>狀態</InputLabel>
              <Select value={filterStatus} label="狀態" onChange={(e) => setFilterStatus(e.target.value)}>
                <MenuItem value="all">全部狀態</MenuItem>
                {Object.entries(statusConfig).map(([key, config]) => (
                  <MenuItem key={key} value={key}>
                    {config.label}
                  </MenuItem>
                ))}
              </Select>
            </FormControl>
            <Typography variant="body2" color="text.secondary" sx={{ ml: 'auto' }}>
              共 <strong>{filteredUsers.length}</strong> 位使用者
            </Typography>
          </Box>
        </Paper>
      </Fade>

      {/* 使用者列表 */}
      <Grow in timeout={500}>
        <TableContainer component={Paper}>
          <Table>
            <TableHead>
              <TableRow sx={{ bgcolor: alpha(theme.palette.primary.main, 0.04) }}>
                <TableCell sx={{ fontWeight: 600 }}>使用者</TableCell>
                <TableCell sx={{ fontWeight: 600 }}>帳號</TableCell>
                <TableCell sx={{ fontWeight: 600 }}>角色</TableCell>
                <TableCell sx={{ fontWeight: 600 }}>指派住民</TableCell>
                <TableCell sx={{ fontWeight: 600 }}>狀態</TableCell>
                <TableCell sx={{ fontWeight: 600 }}>最後登入</TableCell>
                <TableCell sx={{ fontWeight: 600 }}>操作</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {filteredUsers.length === 0 ? (
                <TableRow>
                  <TableCell colSpan={7} align="center" sx={{ py: 6 }}>
                    <Avatar 
                      sx={{ 
                        width: 56, 
                        height: 56, 
                        mx: 'auto', 
                        mb: 2,
                        bgcolor: alpha(theme.palette.text.secondary, 0.1),
                      }}
                    >
                      <SearchIcon sx={{ fontSize: 28, color: 'text.secondary' }} />
                    </Avatar>
                    <Typography color="text.secondary" fontWeight={500}>
                      沒有符合條件的使用者
                    </Typography>
                    <Typography variant="body2" color="text.secondary">
                      請嘗試調整搜尋條件
                    </Typography>
                  </TableCell>
                </TableRow>
              ) : (
                filteredUsers.map((user, index) => (
                  <TableRow 
                    key={user.id}
                    onMouseEnter={() => setHoveredRow(user.id)}
                    onMouseLeave={() => setHoveredRow(null)}
                    sx={{ 
                      opacity: user.status !== 'active' ? 0.6 : 1,
                      transition: 'all 0.2s ease',
                      bgcolor: hoveredRow === user.id ? alpha(theme.palette.primary.main, 0.04) : 'transparent',
                    }}
                  >
                    <TableCell>
                      <Box sx={{ display: 'flex', alignItems: 'center', gap: 1.5 }}>
                        <Avatar 
                          sx={{ 
                            width: 40, 
                            height: 40,
                            bgcolor: theme.palette.primary.main,
                            fontWeight: 600,
                          }}
                        >
                          {user.displayName[0] || <PersonIcon />}
                        </Avatar>
                        <Box>
                          <Typography fontWeight={600}>{user.displayName}</Typography>
                          <Typography variant="caption" color="text.secondary">
                            {user.email || '無 Email'}
                          </Typography>
                        </Box>
                      </Box>
                    </TableCell>
                    <TableCell>
                      <Chip
                        size="small"
                        label={user.username}
                        variant="outlined"
                        sx={{ 
                          fontFamily: 'monospace',
                          bgcolor: alpha(theme.palette.text.primary, 0.04),
                        }}
                      />
                    </TableCell>
                    <TableCell>
                      <Chip
                        size="small"
                        label={roleConfig[user.role].label}
                        color={roleConfig[user.role].color}
                      />
                    </TableCell>
                    <TableCell>
                      {user.assignedResidents.length > 0 ? (
                        <Typography variant="body2">{getResidentNames(user.assignedResidents)}</Typography>
                      ) : (
                        <Typography variant="body2" color="text.secondary">
                          {user.role === 'ADMIN' ? '全部' : '未指派'}
                        </Typography>
                      )}
                    </TableCell>
                    <TableCell>
                      <Chip
                        size="small"
                        label={statusConfig[user.status].label}
                        color={statusConfig[user.status].color}
                        sx={{
                          '& .MuiChip-label': { fontWeight: 500 },
                        }}
                      />
                    </TableCell>
                    <TableCell>
                      <Typography variant="body2" color="text.secondary">
                        {user.lastLoginAt
                          ? user.lastLoginAt.toLocaleString('zh-TW', {
                              month: 'numeric',
                              day: 'numeric',
                              hour: '2-digit',
                              minute: '2-digit',
                            })
                          : '從未登入'}
                      </Typography>
                    </TableCell>
                    <TableCell>
                      <Box sx={{ display: 'flex', gap: 0.5 }}>
                        <Tooltip title="編輯" arrow>
                          <IconButton 
                            size="small" 
                            onClick={() => handleEdit(user)}
                            sx={{
                              bgcolor: alpha(theme.palette.primary.main, 0.08),
                              '&:hover': {
                                bgcolor: alpha(theme.palette.primary.main, 0.16),
                              },
                            }}
                          >
                            <EditIcon fontSize="small" />
                          </IconButton>
                        </Tooltip>
                        <Tooltip title={user.status === 'active' ? '停用' : '啟用'} arrow>
                          <IconButton
                            size="small"
                            onClick={() => toggleStatus(user.id)}
                            sx={{
                              bgcolor: user.status === 'active' 
                                ? alpha(theme.palette.warning.main, 0.08)
                                : alpha(theme.palette.success.main, 0.08),
                              color: user.status === 'active' ? 'warning.main' : 'success.main',
                              '&:hover': {
                                bgcolor: user.status === 'active' 
                                  ? alpha(theme.palette.warning.main, 0.16)
                                  : alpha(theme.palette.success.main, 0.16),
                              },
                            }}
                          >
                            {user.status === 'active' ? <BlockIcon fontSize="small" /> : <CheckCircleIcon fontSize="small" />}
                          </IconButton>
                        </Tooltip>
                        <Tooltip title="重設密碼" arrow>
                          <IconButton 
                            size="small"
                            sx={{
                              bgcolor: alpha(theme.palette.info.main, 0.08),
                              color: 'info.main',
                              '&:hover': {
                                bgcolor: alpha(theme.palette.info.main, 0.16),
                              },
                            }}
                          >
                            <LockResetIcon fontSize="small" />
                          </IconButton>
                        </Tooltip>
                        <Tooltip title="刪除" arrow>
                          <IconButton 
                            size="small" 
                            onClick={() => handleDeleteClick(user.id)}
                            sx={{
                              bgcolor: alpha(theme.palette.error.main, 0.08),
                              color: 'error.main',
                              '&:hover': {
                                bgcolor: alpha(theme.palette.error.main, 0.16),
                              },
                            }}
                          >
                            <DeleteIcon fontSize="small" />
                          </IconButton>
                        </Tooltip>
                      </Box>
                    </TableCell>
                  </TableRow>
                ))
              )}
            </TableBody>
          </Table>
        </TableContainer>
      </Grow>

      {/* 編輯對話框 */}
      <Dialog 
        open={editDialogOpen} 
        onClose={() => !saving && setEditDialogOpen(false)} 
        maxWidth="sm" 
        fullWidth
        TransitionComponent={Zoom}
      >
        <DialogTitle sx={{ pb: 1 }}>
          {editUser.id ? '編輯使用者' : '新增使用者'}
        </DialogTitle>
        <DialogContent>
          <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2.5, mt: 2 }}>
            <TextField
              label="帳號"
              fullWidth
              value={editUser.username || ''}
              onChange={(e) => setEditUser({ ...editUser, username: e.target.value })}
              disabled={!!editUser.id || saving}
              helperText={editUser.id ? '帳號建立後無法修改' : '英文字母與數字'}
            />
            <TextField
              label="顯示名稱"
              fullWidth
              value={editUser.displayName || ''}
              onChange={(e) => setEditUser({ ...editUser, displayName: e.target.value })}
              disabled={saving}
            />
            <TextField
              label="Email"
              type="email"
              fullWidth
              value={editUser.email || ''}
              onChange={(e) => setEditUser({ ...editUser, email: e.target.value })}
              disabled={saving}
            />
            <FormControl fullWidth disabled={saving}>
              <InputLabel>角色</InputLabel>
              <Select
                value={editUser.role || 'CAREGIVER'}
                label="角色"
                onChange={(e) => setEditUser({ ...editUser, role: e.target.value as UserRole })}
              >
                {Object.entries(roleConfig).map(([key, config]) => (
                  <MenuItem key={key} value={key}>
                    <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                      <Box 
                        sx={{ 
                          width: 8, 
                          height: 8, 
                          borderRadius: '50%',
                          bgcolor: `${config.color}.main`,
                        }} 
                      />
                      {config.label}
                    </Box>
                  </MenuItem>
                ))}
              </Select>
            </FormControl>

            {(editUser.role === 'CAREGIVER' || editUser.role === 'FAMILY') && (
              <Autocomplete
                multiple
                options={mockResidents}
                getOptionLabel={(option) => option.name}
                value={mockResidents.filter((r) => editUser.assignedResidents?.includes(r.id))}
                onChange={(_, newValue) =>
                  setEditUser({ ...editUser, assignedResidents: newValue.map((v) => v.id) })
                }
                disabled={saving}
                renderInput={(params) => (
                  <TextField {...params} label="指派住民" placeholder="選擇住民" />
                )}
                renderTags={(value, getTagProps) =>
                  value.map((option, index) => (
                    <Chip
                      variant="outlined"
                      label={option.name}
                      size="small"
                      {...getTagProps({ index })}
                      key={option.id}
                    />
                  ))
                }
              />
            )}

            <FormControl fullWidth disabled={saving}>
              <InputLabel>狀態</InputLabel>
              <Select
                value={editUser.status || 'active'}
                label="狀態"
                onChange={(e) => setEditUser({ ...editUser, status: e.target.value as UserStatus })}
              >
                {Object.entries(statusConfig).map(([key, config]) => (
                  <MenuItem key={key} value={key}>
                    {config.label}
                  </MenuItem>
                ))}
              </Select>
            </FormControl>

            {!editUser.id && (
              <Alert severity="info" icon={false}>
                新使用者的初始密碼將發送至其 Email，首次登入需修改密碼。
              </Alert>
            )}
          </Box>
        </DialogContent>
        <DialogActions sx={{ px: 3, pb: 2.5 }}>
          <Button onClick={() => setEditDialogOpen(false)} disabled={saving}>
            取消
          </Button>
          <Button 
            variant="contained" 
            onClick={handleSave}
            disabled={saving}
            startIcon={saving ? <CircularProgress size={18} color="inherit" /> : null}
          >
            {saving ? '儲存中...' : '儲存'}
          </Button>
        </DialogActions>
      </Dialog>

      {/* 刪除確認對話框 */}
      <Dialog 
        open={deleteDialogOpen} 
        onClose={() => setDeleteDialogOpen(false)}
        TransitionComponent={Zoom}
        PaperProps={{
          sx: { minWidth: 380 }
        }}
      >
        <DialogTitle sx={{ display: 'flex', alignItems: 'center', gap: 1, pb: 1 }}>
          <WarningAmberIcon color="error" />
          確認刪除
        </DialogTitle>
        <DialogContent>
          <Alert severity="error" sx={{ mb: 2 }} icon={false}>
            此操作無法復原。刪除使用者後，相關的操作紀錄仍會保留供稽核。
          </Alert>
          <Typography>
            確定要刪除使用者「<strong>{users.find((u) => u.id === selectedUserId)?.displayName}</strong>」嗎？
          </Typography>
        </DialogContent>
        <DialogActions sx={{ px: 3, pb: 2.5 }}>
          <Button onClick={() => setDeleteDialogOpen(false)}>取消</Button>
          <Button variant="contained" color="error" onClick={handleConfirmDelete}>
            確認刪除
          </Button>
        </DialogActions>
      </Dialog>
    </Container>
  );
}
