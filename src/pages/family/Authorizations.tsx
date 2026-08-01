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
  InputLabel,
  Select,
  MenuItem,
  FormGroup,
  FormControlLabel,
  Checkbox,
  Alert,
  Avatar,
  ToggleButtonGroup,
  ToggleButton,
} from '@mui/material';
import GroupIcon from '@mui/icons-material/Group';
import AddIcon from '@mui/icons-material/Add';
import EditIcon from '@mui/icons-material/Edit';
import DeleteIcon from '@mui/icons-material/Delete';
import PersonIcon from '@mui/icons-material/Person';

// 授權狀態
type AuthStatus = 'active' | 'pending' | 'expired' | 'revoked';

// 授權範圍
interface AuthScope {
  viewSummary: boolean;
  viewEvents: boolean;
  viewReminders: boolean;
  viewAlerts: boolean;
  receiveNotifications: boolean;
}

// 授權紀錄
interface Authorization {
  id: string;
  residentId: string;
  residentName: string;
  authorizedUserId: string;
  authorizedUserName: string;
  authorizedUserEmail: string;
  relation: string;
  scope: AuthScope;
  status: AuthStatus;
  grantedAt: Date;
  expiresAt?: Date;
  lastAccessAt?: Date;
}

// 狀態配置
const statusConfig: Record<AuthStatus, { label: string; color: 'success' | 'warning' | 'error' | 'default' }> = {
  active: { label: '有效', color: 'success' },
  pending: { label: '待確認', color: 'warning' },
  expired: { label: '已過期', color: 'error' },
  revoked: { label: '已撤銷', color: 'default' },
};

// 範圍標籤
const scopeLabels: Record<keyof AuthScope, string> = {
  viewSummary: '查看每日摘要',
  viewEvents: '查看生活事件',
  viewReminders: '查看提醒',
  viewAlerts: '查看警示',
  receiveNotifications: '接收通知',
};

// 授權模板類型
type AuthTemplate = 'basic' | 'standard' | 'full' | 'custom';

// 授權模板定義
const authTemplates: Record<Exclude<AuthTemplate, 'custom'>, { label: string; scope: AuthScope }> = {
  basic: {
    label: '基本',
    scope: {
      viewSummary: true,
      viewEvents: false,
      viewReminders: false,
      viewAlerts: false,
      receiveNotifications: true,
    },
  },
  standard: {
    label: '標準',
    scope: {
      viewSummary: true,
      viewEvents: false,
      viewReminders: true,
      viewAlerts: true,
      receiveNotifications: true,
    },
  },
  full: {
    label: '完整',
    scope: {
      viewSummary: true,
      viewEvents: true,
      viewReminders: true,
      viewAlerts: true,
      receiveNotifications: true,
    },
  },
};

// 判斷 scope 符合哪個模板
const getTemplateFromScope = (scope: AuthScope): AuthTemplate => {
  for (const [key, template] of Object.entries(authTemplates)) {
    const isMatch = Object.entries(template.scope).every(
      ([k, v]) => scope[k as keyof AuthScope] === v
    );
    if (isMatch) return key as AuthTemplate;
  }
  return 'custom';
};

// 取得模板顯示文字
const getTemplateLabelFromScope = (scope: AuthScope): string => {
  const template = getTemplateFromScope(scope);
  if (template === 'custom') {
    const count = Object.values(scope).filter(Boolean).length;
    return `自訂 (${count}/5)`;
  }
  return `${authTemplates[template].label}授權`;
};

// 模擬授權資料
const mockAuthorizations: Authorization[] = [
  {
    id: '1',
    residentId: 'r1',
    residentName: '王奶奶',
    authorizedUserId: 'u1',
    authorizedUserName: '王小明',
    authorizedUserEmail: 'ming@example.com',
    relation: '兒子',
    scope: {
      viewSummary: true,
      viewEvents: true,
      viewReminders: true,
      viewAlerts: true,
      receiveNotifications: true,
    },
    status: 'active',
    grantedAt: new Date('2026-07-01'),
    lastAccessAt: new Date('2026-08-01T10:00:00'),
  },
  {
    id: '2',
    residentId: 'r1',
    residentName: '王奶奶',
    authorizedUserId: 'u2',
    authorizedUserName: '王小華',
    authorizedUserEmail: 'hua@example.com',
    relation: '女兒',
    scope: {
      viewSummary: true,
      viewEvents: false,
      viewReminders: true,
      viewAlerts: true,
      receiveNotifications: true,
    },
    status: 'active',
    grantedAt: new Date('2026-07-15'),
    lastAccessAt: new Date('2026-07-30T14:00:00'),
  },
  {
    id: '3',
    residentId: 'r1',
    residentName: '王奶奶',
    authorizedUserId: 'u3',
    authorizedUserName: '張大成',
    authorizedUserEmail: 'zhang@example.com',
    relation: '看護',
    scope: {
      viewSummary: true,
      viewEvents: true,
      viewReminders: true,
      viewAlerts: true,
      receiveNotifications: false,
    },
    status: 'pending',
    grantedAt: new Date('2026-08-01'),
  },
];

export default function Authorizations() {
  const [authorizations, setAuthorizations] = useState<Authorization[]>(mockAuthorizations);
  const [editDialogOpen, setEditDialogOpen] = useState(false);
  const [editAuth, setEditAuth] = useState<Partial<Authorization>>({});
  const [selectedTemplate, setSelectedTemplate] = useState<AuthTemplate>('standard');

  // 開啟新增對話框
  const handleAdd = () => {
    setSelectedTemplate('standard');
    setEditAuth({
      authorizedUserName: '',
      authorizedUserEmail: '',
      relation: '',
      scope: { ...authTemplates.standard.scope },
      status: 'pending',
    });
    setEditDialogOpen(true);
  };

  // 開啟編輯對話框
  const handleEdit = (auth: Authorization) => {
    setSelectedTemplate(getTemplateFromScope(auth.scope));
    setEditAuth({ ...auth });
    setEditDialogOpen(true);
  };

  // 處理模板變更
  const handleTemplateChange = (newTemplate: AuthTemplate) => {
    if (newTemplate && newTemplate !== 'custom') {
      setSelectedTemplate(newTemplate);
      setEditAuth({
        ...editAuth,
        scope: { ...authTemplates[newTemplate].scope },
      });
    }
  };

  // 切換範圍
  const toggleScope = (key: keyof AuthScope) => {
    const currentScope = editAuth.scope || {
      viewSummary: false,
      viewEvents: false,
      viewReminders: false,
      viewAlerts: false,
      receiveNotifications: false,
    };
    const newScope = { ...currentScope, [key]: !currentScope[key] };
    setEditAuth({ ...editAuth, scope: newScope });
    setSelectedTemplate(getTemplateFromScope(newScope));
  };

  // 儲存授權
  const handleSave = () => {
    if (editAuth.id) {
      setAuthorizations((prev) =>
        prev.map((a) => (a.id === editAuth.id ? ({ ...a, ...editAuth } as Authorization) : a))
      );
    } else {
      const newAuth: Authorization = {
        id: Date.now().toString(),
        residentId: 'r1',
        residentName: '王奶奶',
        authorizedUserId: `u${Date.now()}`,
        authorizedUserName: editAuth.authorizedUserName || '',
        authorizedUserEmail: editAuth.authorizedUserEmail || '',
        relation: editAuth.relation || '',
        scope: editAuth.scope || {
          viewSummary: true,
          viewEvents: false,
          viewReminders: true,
          viewAlerts: true,
          receiveNotifications: true,
        },
        status: 'pending',
        grantedAt: new Date(),
      };
      setAuthorizations((prev) => [...prev, newAuth]);
    }
    setEditDialogOpen(false);
  };

  // 撤銷授權
  const handleRevoke = (id: string) => {
    setAuthorizations((prev) =>
      prev.map((a) => (a.id === id ? { ...a, status: 'revoked' as AuthStatus } : a))
    );
  };

  // 刪除授權
  const handleDelete = (id: string) => {
    setAuthorizations((prev) => prev.filter((a) => a.id !== id));
  };

  return (
    <Container maxWidth="lg" sx={{ py: 2 }}>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
        <Typography variant="h4" sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
          <GroupIcon color="primary" />
          授權管理
        </Typography>
        <Button variant="contained" startIcon={<AddIcon />} onClick={handleAdd}>
          新增授權
        </Button>
      </Box>

      <Alert severity="info" sx={{ mb: 3 }}>
        您可以授權其他家屬查看住民的照護資訊。被授權者將收到邀請通知，確認後即可開始使用。
      </Alert>

      <Paper>
        <Table>
          <TableHead>
            <TableRow>
              <TableCell>被授權者</TableCell>
              <TableCell>關係</TableCell>
              <TableCell>授權範圍</TableCell>
              <TableCell>狀態</TableCell>
              <TableCell>授權時間</TableCell>
              <TableCell>最後存取</TableCell>
              <TableCell>操作</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {authorizations.map((auth) => (
              <TableRow
                key={auth.id}
                sx={{ opacity: auth.status === 'revoked' ? 0.5 : 1 }}
              >
                <TableCell>
                  <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                    <Avatar sx={{ width: 32, height: 32 }}>
                      <PersonIcon />
                    </Avatar>
                    <Box>
                      <Typography fontWeight="bold">{auth.authorizedUserName}</Typography>
                      <Typography variant="caption" color="text.secondary">
                        {auth.authorizedUserEmail}
                      </Typography>
                    </Box>
                  </Box>
                </TableCell>
                <TableCell>
                  <Chip size="small" label={auth.relation} variant="outlined" />
                </TableCell>
                <TableCell>
                  <Chip
                    size="small"
                    label={getTemplateLabelFromScope(auth.scope)}
                    color={getTemplateFromScope(auth.scope) === 'custom' ? 'default' : 'primary'}
                    variant={getTemplateFromScope(auth.scope) === 'custom' ? 'outlined' : 'filled'}
                  />
                </TableCell>
                <TableCell>
                  <Chip
                    size="small"
                    label={statusConfig[auth.status].label}
                    color={statusConfig[auth.status].color}
                  />
                </TableCell>
                <TableCell>
                  <Typography variant="caption">
                    {auth.grantedAt.toLocaleDateString('zh-TW')}
                  </Typography>
                </TableCell>
                <TableCell>
                  <Typography variant="caption">
                    {auth.lastAccessAt
                      ? auth.lastAccessAt.toLocaleDateString('zh-TW')
                      : '尚未存取'}
                  </Typography>
                </TableCell>
                <TableCell>
                  {auth.status !== 'revoked' && (
                    <>
                      <IconButton size="small" onClick={() => handleEdit(auth)}>
                        <EditIcon />
                      </IconButton>
                      <Button
                        size="small"
                        color="warning"
                        onClick={() => handleRevoke(auth.id)}
                      >
                        撤銷
                      </Button>
                    </>
                  )}
                  <IconButton
                    size="small"
                    color="error"
                    onClick={() => handleDelete(auth.id)}
                  >
                    <DeleteIcon />
                  </IconButton>
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </Paper>

      {/* 編輯對話框 */}
      <Dialog open={editDialogOpen} onClose={() => setEditDialogOpen(false)} maxWidth="sm" fullWidth>
        <DialogTitle>{editAuth.id ? '編輯授權' : '新增授權'}</DialogTitle>
        <DialogContent>
          <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2, mt: 1 }}>
            <TextField
              label="被授權者姓名"
              fullWidth
              value={editAuth.authorizedUserName || ''}
              onChange={(e) => setEditAuth({ ...editAuth, authorizedUserName: e.target.value })}
            />
            <TextField
              label="Email"
              fullWidth
              type="email"
              value={editAuth.authorizedUserEmail || ''}
              onChange={(e) => setEditAuth({ ...editAuth, authorizedUserEmail: e.target.value })}
              helperText="系統會發送邀請通知至此信箱"
            />
            <TextField
              label="關係"
              fullWidth
              value={editAuth.relation || ''}
              onChange={(e) => setEditAuth({ ...editAuth, relation: e.target.value })}
              placeholder="如：兒子、女兒、看護"
            />

            <Typography variant="subtitle2" sx={{ mt: 1 }}>
              授權範圍
            </Typography>

            <ToggleButtonGroup
              value={selectedTemplate}
              exclusive
              onChange={(_, newValue) => newValue && handleTemplateChange(newValue)}
              size="small"
              sx={{ mb: 2 }}
            >
              <ToggleButton value="basic">基本</ToggleButton>
              <ToggleButton value="standard">標準</ToggleButton>
              <ToggleButton value="full">完整</ToggleButton>
            </ToggleButtonGroup>

            {selectedTemplate === 'custom' && (
              <Alert severity="info" sx={{ mb: 1 }}>
                已自訂授權範圍
              </Alert>
            )}

            <FormGroup>
              {Object.entries(scopeLabels).map(([key, label]) => (
                <FormControlLabel
                  key={key}
                  control={
                    <Checkbox
                      checked={editAuth.scope?.[key as keyof AuthScope] || false}
                      onChange={() => toggleScope(key as keyof AuthScope)}
                    />
                  }
                  label={label}
                />
              ))}
            </FormGroup>
          </Box>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setEditDialogOpen(false)}>取消</Button>
          <Button variant="contained" onClick={handleSave}>
            {editAuth.id ? '儲存' : '發送邀請'}
          </Button>
        </DialogActions>
      </Dialog>
    </Container>
  );
}
