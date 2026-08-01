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
  Alert,
  Tooltip,
} from '@mui/material';
import VpnKeyIcon from '@mui/icons-material/VpnKey';
import EditIcon from '@mui/icons-material/Edit';
import DeleteIcon from '@mui/icons-material/Delete';
import AddIcon from '@mui/icons-material/Add';
import VisibilityOffIcon from '@mui/icons-material/VisibilityOff';
import ContentCopyIcon from '@mui/icons-material/ContentCopy';

// 資產類型
type AssetType =
  | 'api_key'
  | 'token'
  | 'password'
  | 'private_key'
  | 'system_prompt'
  | 'database_info'
  | 'resident_data'
  | 'internal_rule'
  | 'custom';

// 防護模式
type ProtectionMode = 'exact' | 'case_insensitive' | 'partial' | 'encoding' | 'semantic';

// 資產定義
interface ProtectedAsset {
  id: string;
  name: string;
  type: AssetType;
  description: string;
  protectionModes: ProtectionMode[];
  riskLevel: 'critical' | 'high' | 'medium' | 'low';
  createdAt: Date;
  lastModified: Date;
  hitCount: number;
}

// 類型配置
const assetTypeConfig: Record<AssetType, { label: string; color: 'error' | 'warning' | 'info' | 'success' | 'default' }> = {
  api_key: { label: 'API Key', color: 'error' },
  token: { label: 'Token', color: 'error' },
  password: { label: '密碼', color: 'error' },
  private_key: { label: '私鑰', color: 'error' },
  system_prompt: { label: '系統提示詞', color: 'warning' },
  database_info: { label: '資料庫資訊', color: 'warning' },
  resident_data: { label: '住民敏感資料', color: 'warning' },
  internal_rule: { label: '內部規則', color: 'info' },
  custom: { label: '自訂', color: 'default' },
};

// 防護模式配置
const protectionModeConfig: Record<ProtectionMode, { label: string; description: string }> = {
  exact: { label: '完全比對', description: '精確匹配原始值' },
  case_insensitive: { label: '不分大小寫', description: '忽略大小寫差異' },
  partial: { label: '部分比對', description: '匹配部分內容' },
  encoding: { label: '編碼比對', description: '偵測 Base64/Hex 等編碼' },
  semantic: { label: '語意比對', description: '偵測語意相似的描述' },
};

// 風險等級配置
const riskLevelConfig: Record<string, { label: string; color: 'error' | 'warning' | 'info' | 'success' }> = {
  critical: { label: '嚴重', color: 'error' },
  high: { label: '高', color: 'error' },
  medium: { label: '中', color: 'warning' },
  low: { label: '低', color: 'info' },
};

// 模擬資產資料
const mockAssets: ProtectedAsset[] = [
  {
    id: '1',
    name: 'OPENAI_API_KEY',
    type: 'api_key',
    description: 'OpenAI API 金鑰',
    protectionModes: ['exact', 'case_insensitive', 'encoding', 'partial'],
    riskLevel: 'critical',
    createdAt: new Date('2026-07-01'),
    lastModified: new Date('2026-07-15'),
    hitCount: 12,
  },
  {
    id: '2',
    name: 'SYSTEM_PROMPT',
    type: 'system_prompt',
    description: '系統提示詞內容',
    protectionModes: ['exact', 'partial', 'semantic'],
    riskLevel: 'high',
    createdAt: new Date('2026-07-01'),
    lastModified: new Date('2026-08-01'),
    hitCount: 25,
  },
  {
    id: '3',
    name: 'DATABASE_PASSWORD',
    type: 'password',
    description: '資料庫連線密碼',
    protectionModes: ['exact', 'encoding'],
    riskLevel: 'critical',
    createdAt: new Date('2026-07-01'),
    lastModified: new Date('2026-07-01'),
    hitCount: 8,
  },
  {
    id: '4',
    name: 'JWT_SECRET',
    type: 'token',
    description: 'JWT 簽章金鑰',
    protectionModes: ['exact', 'encoding'],
    riskLevel: 'critical',
    createdAt: new Date('2026-07-01'),
    lastModified: new Date('2026-07-01'),
    hitCount: 3,
  },
  {
    id: '5',
    name: 'RESIDENT_ID_PATTERN',
    type: 'resident_data',
    description: '住民身分證字號格式',
    protectionModes: ['exact', 'partial'],
    riskLevel: 'high',
    createdAt: new Date('2026-07-10'),
    lastModified: new Date('2026-07-10'),
    hitCount: 5,
  },
  {
    id: '6',
    name: 'SECURITY_RULES',
    type: 'internal_rule',
    description: '安全規則與政策內容',
    protectionModes: ['semantic'],
    riskLevel: 'medium',
    createdAt: new Date('2026-07-15'),
    lastModified: new Date('2026-07-20'),
    hitCount: 2,
  },
];

export default function Assets() {
  const [assets, setAssets] = useState<ProtectedAsset[]>(mockAssets);
  const [editDialogOpen, setEditDialogOpen] = useState(false);
  const [editAsset, setEditAsset] = useState<Partial<ProtectedAsset>>({});

  // 開啟編輯對話框
  const handleEdit = (asset: ProtectedAsset) => {
    setEditAsset({ ...asset });
    setEditDialogOpen(true);
  };

  // 開啟新增對話框
  const handleAdd = () => {
    setEditAsset({
      name: '',
      type: 'custom',
      description: '',
      protectionModes: ['exact'],
      riskLevel: 'medium',
    });
    setEditDialogOpen(true);
  };

  // 切換防護模式
  const toggleProtectionMode = (mode: ProtectionMode) => {
    const currentModes = editAsset.protectionModes || [];
    if (currentModes.includes(mode)) {
      setEditAsset({ ...editAsset, protectionModes: currentModes.filter((m) => m !== mode) });
    } else {
      setEditAsset({ ...editAsset, protectionModes: [...currentModes, mode] });
    }
  };

  // 儲存資產
  const handleSave = () => {
    if (editAsset.id) {
      setAssets((prev) =>
        prev.map((a) =>
          a.id === editAsset.id ? ({ ...a, ...editAsset, lastModified: new Date() } as ProtectedAsset) : a
        )
      );
    } else {
      const newAsset: ProtectedAsset = {
        id: Date.now().toString(),
        name: editAsset.name || '',
        type: editAsset.type || 'custom',
        description: editAsset.description || '',
        protectionModes: editAsset.protectionModes || ['exact'],
        riskLevel: editAsset.riskLevel || 'medium',
        createdAt: new Date(),
        lastModified: new Date(),
        hitCount: 0,
      };
      setAssets((prev) => [...prev, newAsset]);
    }
    setEditDialogOpen(false);
  };

  // 刪除資產
  const handleDelete = (id: string) => {
    setAssets((prev) => prev.filter((a) => a.id !== id));
  };

  return (
    <Container maxWidth="lg" sx={{ py: 2 }}>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
        <Typography variant="h4" sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
          <VpnKeyIcon color="primary" />
          受保護資產
        </Typography>
        <Button variant="contained" startIcon={<AddIcon />} onClick={handleAdd}>
          新增資產
        </Button>
      </Box>

      <Alert severity="info" sx={{ mb: 3 }}>
        受保護資產會被 Token Guard 監控。當輸入或輸出包含這些資產時，系統會根據防護模式進行偵測並阻擋洩漏。
      </Alert>

      <Paper>
        <Table>
          <TableHead>
            <TableRow>
              <TableCell>資產名稱</TableCell>
              <TableCell>類型</TableCell>
              <TableCell>說明</TableCell>
              <TableCell>防護模式</TableCell>
              <TableCell>風險等級</TableCell>
              <TableCell>命中次數</TableCell>
              <TableCell>操作</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {assets.map((asset) => (
              <TableRow key={asset.id}>
                <TableCell>
                  <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                    <VisibilityOffIcon fontSize="small" color="action" />
                    <Typography fontWeight="bold">{asset.name}</Typography>
                  </Box>
                </TableCell>
                <TableCell>
                  <Chip
                    size="small"
                    label={assetTypeConfig[asset.type].label}
                    color={assetTypeConfig[asset.type].color}
                  />
                </TableCell>
                <TableCell>{asset.description}</TableCell>
                <TableCell>
                  <Box sx={{ display: 'flex', gap: 0.5, flexWrap: 'wrap' }}>
                    {asset.protectionModes.map((mode) => (
                      <Tooltip key={mode} title={protectionModeConfig[mode].description}>
                        <Chip size="small" label={protectionModeConfig[mode].label} variant="outlined" />
                      </Tooltip>
                    ))}
                  </Box>
                </TableCell>
                <TableCell>
                  <Chip
                    size="small"
                    label={riskLevelConfig[asset.riskLevel].label}
                    color={riskLevelConfig[asset.riskLevel].color}
                  />
                </TableCell>
                <TableCell>
                  <Chip size="small" label={asset.hitCount} color={asset.hitCount > 10 ? 'error' : 'default'} />
                </TableCell>
                <TableCell>
                  <IconButton size="small" onClick={() => handleEdit(asset)}>
                    <EditIcon />
                  </IconButton>
                  <IconButton size="small" color="error" onClick={() => handleDelete(asset.id)}>
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
        <DialogTitle>{editAsset.id ? '編輯資產' : '新增資產'}</DialogTitle>
        <DialogContent>
          <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2, mt: 1 }}>
            <TextField
              label="資產名稱"
              fullWidth
              value={editAsset.name || ''}
              onChange={(e) => setEditAsset({ ...editAsset, name: e.target.value })}
              helperText="建議使用大寫英文與底線，如 API_KEY"
            />

            <FormControl fullWidth>
              <InputLabel>資產類型</InputLabel>
              <Select
                value={editAsset.type || 'custom'}
                label="資產類型"
                onChange={(e) => setEditAsset({ ...editAsset, type: e.target.value as AssetType })}
              >
                {Object.entries(assetTypeConfig).map(([key, config]) => (
                  <MenuItem key={key} value={key}>
                    {config.label}
                  </MenuItem>
                ))}
              </Select>
            </FormControl>

            <TextField
              label="說明"
              fullWidth
              value={editAsset.description || ''}
              onChange={(e) => setEditAsset({ ...editAsset, description: e.target.value })}
            />

            <FormControl fullWidth>
              <InputLabel>風險等級</InputLabel>
              <Select
                value={editAsset.riskLevel || 'medium'}
                label="風險等級"
                onChange={(e) =>
                  setEditAsset({ ...editAsset, riskLevel: e.target.value as ProtectedAsset['riskLevel'] })
                }
              >
                {Object.entries(riskLevelConfig).map(([key, config]) => (
                  <MenuItem key={key} value={key}>
                    {config.label}
                  </MenuItem>
                ))}
              </Select>
            </FormControl>

            <Typography variant="subtitle2" sx={{ mt: 1 }}>
              防護模式
            </Typography>
            <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1 }}>
              {Object.entries(protectionModeConfig).map(([mode, config]) => (
                <Tooltip key={mode} title={config.description}>
                  <Chip
                    label={config.label}
                    onClick={() => toggleProtectionMode(mode as ProtectionMode)}
                    color={editAsset.protectionModes?.includes(mode as ProtectionMode) ? 'primary' : 'default'}
                    variant={editAsset.protectionModes?.includes(mode as ProtectionMode) ? 'filled' : 'outlined'}
                  />
                </Tooltip>
              ))}
            </Box>
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
