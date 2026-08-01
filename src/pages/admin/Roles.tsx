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
  Chip,
  IconButton,
  Button,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField,
  FormControl,
  FormGroup,
  FormControlLabel,
  Checkbox,
  Accordion,
  AccordionSummary,
  AccordionDetails,
} from '@mui/material';
import AdminPanelSettingsIcon from '@mui/icons-material/AdminPanelSettings';
import EditIcon from '@mui/icons-material/Edit';
import DeleteIcon from '@mui/icons-material/Delete';
import AddIcon from '@mui/icons-material/Add';
import ExpandMoreIcon from '@mui/icons-material/ExpandMore';

// 權限定義
interface Permission {
  key: string;
  label: string;
  description: string;
  category: string;
}

// 角色定義
interface Role {
  id: string;
  name: string;
  displayName: string;
  description: string;
  permissions: string[];
  isSystem: boolean;
  userCount: number;
}

// 權限清單（對齊 F07 規劃）
const allPermissions: Permission[] = [
  // 住民資料
  { key: 'resident:read', label: '查看住民資料', description: '查看住民基本資訊', category: '住民資料' },
  { key: 'resident:write', label: '編輯住民資料', description: '新增、修改住民資訊', category: '住民資料' },
  { key: 'resident:delete', label: '刪除住民', description: '刪除住民紀錄', category: '住民資料' },
  // 生活事件
  { key: 'event:read', label: '查看生活事件', description: '查看住民生活事件紀錄', category: '生活事件' },
  { key: 'event:write', label: '建立生活事件', description: '新增生活事件', category: '生活事件' },
  { key: 'event:correct', label: '修正生活事件', description: '修正錯誤的事件紀錄', category: '生活事件' },
  { key: 'event:delete', label: '刪除生活事件', description: '刪除事件紀錄', category: '生活事件' },
  // 提醒管理
  { key: 'reminder:read', label: '查看提醒', description: '查看提醒列表', category: '提醒管理' },
  { key: 'reminder:write', label: '建立提醒', description: '新增提醒', category: '提醒管理' },
  { key: 'reminder:delete', label: '刪除提醒', description: '刪除提醒', category: '提醒管理' },
  // 記憶管理
  { key: 'memory:read', label: '查看記憶', description: '查看 AI 記憶', category: '記憶管理' },
  { key: 'memory:correct', label: '修正記憶', description: '修正錯誤記憶', category: '記憶管理' },
  { key: 'memory:delete', label: '刪除記憶', description: '刪除記憶', category: '記憶管理' },
  // 語音互動
  { key: 'voice:interact', label: '語音互動', description: '使用語音互動功能', category: '語音互動' },
  { key: 'voice:session', label: '管理語音 Session', description: '管理語音對話工作階段', category: '語音互動' },
  // 住民隔離
  { key: 'privacy:cross_resident', label: '跨住民存取', description: '存取其他住民資料', category: '住民隔離' },
  { key: 'privacy:sensitive', label: '敏感資料存取', description: '存取敏感個人資料', category: '住民隔離' },
  // 安全管理
  { key: 'security:assets', label: '管理資產', description: '管理受保護資產', category: '安全管理' },
  { key: 'security:policy', label: '編輯政策', description: '編輯安全政策', category: '安全管理' },
  { key: 'security:audit', label: '查看稽核', description: '查看稽核日誌', category: '安全管理' },
  { key: 'security:benchmark', label: '執行測試', description: '執行安全基準測試', category: '安全管理' },
  // 系統管理
  { key: 'admin:users', label: '管理使用者', description: '管理系統使用者帳號', category: '系統管理' },
  { key: 'admin:roles', label: '管理角色', description: '管理角色與權限', category: '系統管理' },
  { key: 'admin:settings', label: '系統設定', description: '調整系統設定', category: '系統管理' },
  { key: 'admin:escalate', label: '接收升級', description: '接收升級處理通知', category: '系統管理' },
];

// 依類別分組權限
const permissionsByCategory = allPermissions.reduce<Record<string, Permission[]>>(
  (acc, perm) => {
    if (!acc[perm.category]) acc[perm.category] = [];
    acc[perm.category]!.push(perm);
    return acc;
  },
  {}
);

// 模擬角色資料
const mockRoles: Role[] = [
  {
    id: '1',
    name: 'ADMIN',
    displayName: '系統管理者',
    description: '完整系統管理權限',
    permissions: allPermissions.map((p) => p.key),
    isSystem: true,
    userCount: 2,
  },
  {
    id: '2',
    name: 'CAREGIVER',
    displayName: '照護人員',
    description: '照護住民的日常管理',
    permissions: [
      'resident:read',
      'event:read', 'event:write', 'event:correct', 'event:delete',
      'reminder:read', 'reminder:write', 'reminder:delete',
      'memory:read', 'memory:correct',
    ],
    isSystem: true,
    userCount: 15,
  },
  {
    id: '3',
    name: 'FAMILY',
    displayName: '家屬',
    description: '查看被授權住民的資訊',
    permissions: ['resident:read', 'event:read', 'reminder:read'],
    isSystem: true,
    userCount: 45,
  },
  {
    id: '4',
    name: 'RESIDENT',
    displayName: '住民',
    description: '使用語音互動功能',
    permissions: ['voice:interact', 'event:read', 'reminder:read'],
    isSystem: true,
    userCount: 30,
  },
];

export default function Roles() {
  const [roles, setRoles] = useState<Role[]>(mockRoles);
  const [editDialogOpen, setEditDialogOpen] = useState(false);
  const [editRole, setEditRole] = useState<Partial<Role>>({});

  // 開啟編輯對話框
  const handleEdit = (role: Role) => {
    setEditRole({ ...role });
    setEditDialogOpen(true);
  };

  // 開啟新增對話框
  const handleAdd = () => {
    setEditRole({
      name: '',
      displayName: '',
      description: '',
      permissions: [],
      isSystem: false,
    });
    setEditDialogOpen(true);
  };

  // 切換權限
  const togglePermission = (permKey: string) => {
    const currentPerms = editRole.permissions || [];
    if (currentPerms.includes(permKey)) {
      setEditRole({ ...editRole, permissions: currentPerms.filter((p) => p !== permKey) });
    } else {
      setEditRole({ ...editRole, permissions: [...currentPerms, permKey] });
    }
  };

  // 儲存角色
  const handleSave = () => {
    if (editRole.id) {
      setRoles((prev) => prev.map((r) => (r.id === editRole.id ? ({ ...r, ...editRole } as Role) : r)));
    } else {
      const newRole: Role = {
        id: Date.now().toString(),
        name: editRole.name || '',
        displayName: editRole.displayName || '',
        description: editRole.description || '',
        permissions: editRole.permissions || [],
        isSystem: false,
        userCount: 0,
      };
      setRoles((prev) => [...prev, newRole]);
    }
    setEditDialogOpen(false);
  };

  // 刪除角色
  const handleDelete = (id: string) => {
    const role = roles.find((r) => r.id === id);
    if (role?.isSystem) {
      alert('系統角色無法刪除');
      return;
    }
    setRoles((prev) => prev.filter((r) => r.id !== id));
  };

  return (
    <Container maxWidth="lg" sx={{ py: 2 }}>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
        <Typography variant="h4" sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
          <AdminPanelSettingsIcon color="primary" />
          角色管理
        </Typography>
        <Button variant="contained" startIcon={<AddIcon />} onClick={handleAdd}>
          新增角色
        </Button>
      </Box>

      <Paper>
        <Table>
          <TableHead>
            <TableRow>
              <TableCell>角色名稱</TableCell>
              <TableCell>代碼</TableCell>
              <TableCell>說明</TableCell>
              <TableCell>權限數</TableCell>
              <TableCell>使用者數</TableCell>
              <TableCell>類型</TableCell>
              <TableCell>操作</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {roles.map((role) => (
              <TableRow key={role.id}>
                <TableCell>
                  <Typography sx={{ fontWeight: 'bold' }}>{role.displayName}</Typography>
                </TableCell>
                <TableCell>
                  <Chip size="small" label={role.name} variant="outlined" />
                </TableCell>
                <TableCell>{role.description}</TableCell>
                <TableCell>{role.permissions.length}</TableCell>
                <TableCell>{role.userCount}</TableCell>
                <TableCell>
                  <Chip
                    size="small"
                    label={role.isSystem ? '系統' : '自訂'}
                    color={role.isSystem ? 'primary' : 'default'}
                  />
                </TableCell>
                <TableCell>
                  <IconButton size="small" onClick={() => handleEdit(role)}>
                    <EditIcon />
                  </IconButton>
                  {!role.isSystem && (
                    <IconButton size="small" color="error" onClick={() => handleDelete(role.id)}>
                      <DeleteIcon />
                    </IconButton>
                  )}
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </Paper>

      {/* 編輯對話框 */}
      <Dialog open={editDialogOpen} onClose={() => setEditDialogOpen(false)} maxWidth="md" fullWidth>
        <DialogTitle>{editRole.id ? '編輯角色' : '新增角色'}</DialogTitle>
        <DialogContent>
          <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2, mt: 1 }}>
            <TextField
              label="角色代碼"
              fullWidth
              value={editRole.name || ''}
              onChange={(e) => setEditRole({ ...editRole, name: e.target.value.toUpperCase() })}
              disabled={editRole.isSystem}
              helperText="英文大寫，如 CAREGIVER"
            />
            <TextField
              label="顯示名稱"
              fullWidth
              value={editRole.displayName || ''}
              onChange={(e) => setEditRole({ ...editRole, displayName: e.target.value })}
            />
            <TextField
              label="說明"
              fullWidth
              value={editRole.description || ''}
              onChange={(e) => setEditRole({ ...editRole, description: e.target.value })}
            />

            <Typography variant="subtitle1" sx={{ mt: 2 }}>
              權限設定
            </Typography>

            {Object.entries(permissionsByCategory).map(([category, perms]) => (
              <Accordion key={category} defaultExpanded>
                <AccordionSummary expandIcon={<ExpandMoreIcon />}>
                  <Typography>
                    {category} ({perms.filter((p) => editRole.permissions?.includes(p.key)).length}/{perms.length})
                  </Typography>
                </AccordionSummary>
                <AccordionDetails>
                  <FormControl component="fieldset">
                    <FormGroup>
                      {perms.map((perm) => (
                        <FormControlLabel
                          key={perm.key}
                          control={
                            <Checkbox
                              checked={editRole.permissions?.includes(perm.key) || false}
                              onChange={() => togglePermission(perm.key)}
                            />
                          }
                          label={
                            <Box>
                              <Typography variant="body2">{perm.label}</Typography>
                              <Typography variant="caption" color="text.secondary">
                                {perm.description}
                              </Typography>
                            </Box>
                          }
                        />
                      ))}
                    </FormGroup>
                  </FormControl>
                </AccordionDetails>
              </Accordion>
            ))}
          </Box>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setEditDialogOpen(false)}>取消</Button>
          <Button variant="contained" onClick={handleSave}>
            儲存
          </Button>
        </DialogActions>
      </Dialog>
    </Container>
  );
}
