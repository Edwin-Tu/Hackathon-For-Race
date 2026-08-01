'use client';
import React, { useState } from 'react';
import {
  Container,
  Typography,
  Box,
  Paper,
  Tabs,
  Tab,
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
  Slider,
  Switch,
  FormControlLabel,
  Alert,
  Accordion,
  AccordionSummary,
  AccordionDetails,
} from '@mui/material';
import PolicyIcon from '@mui/icons-material/Policy';
import EditIcon from '@mui/icons-material/Edit';
import DeleteIcon from '@mui/icons-material/Delete';
import AddIcon from '@mui/icons-material/Add';
import ExpandMoreIcon from '@mui/icons-material/ExpandMore';
import SaveIcon from '@mui/icons-material/Save';
import RestoreIcon from '@mui/icons-material/Restore';

// 政策動作
type PolicyAction = 'ALLOW' | 'WARN' | 'RESTRICT' | 'AUTHORIZE' | 'BLOCK' | 'ESCALATE';

// 攻擊類別
type AttackCategory =
  | 'prompt_injection'
  | 'instruction_override'
  | 'role_impersonation'
  | 'secret_extraction'
  | 'cross_resident_access'
  | 'encoding_obfuscation'
  | 'tool_abuse';

// 政策規則
interface PolicyRule {
  id: string;
  name: string;
  description: string;
  enabled: boolean;
  attackCategories: AttackCategory[];
  riskThreshold: number;
  action: PolicyAction;
  requiresAuth: boolean;
  notifyAdmin: boolean;
}

// 風險閾值設定
interface RiskThresholds {
  low: number;
  medium: number;
  high: number;
  critical: number;
}

// 攻擊類別配置
const attackCategoryLabels: Record<AttackCategory, string> = {
  prompt_injection: '提示詞注入',
  instruction_override: '指令覆寫',
  role_impersonation: '角色偽裝',
  secret_extraction: '機密提取',
  cross_resident_access: '跨住民存取',
  encoding_obfuscation: '編碼混淆',
  tool_abuse: '工具濫用',
};

// 政策動作配置
const policyActionConfig: Record<PolicyAction, { label: string; color: 'success' | 'warning' | 'error' | 'info' | 'default'; description: string }> = {
  ALLOW: { label: '允許', color: 'success', description: '正常處理請求' },
  WARN: { label: '警告', color: 'warning', description: '允許但記錄警告' },
  RESTRICT: { label: '限制', color: 'warning', description: '限制回答或工具範圍' },
  AUTHORIZE: { label: '要求驗證', color: 'info', description: '要求額外身分驗證' },
  BLOCK: { label: '阻擋', color: 'error', description: '直接阻擋請求' },
  ESCALATE: { label: '升級', color: 'error', description: '升級人工處理' },
};

// 模擬政策規則
const mockRules: PolicyRule[] = [
  {
    id: '1',
    name: '提示詞注入防護',
    description: '偵測並阻擋試圖覆寫系統指令的輸入',
    enabled: true,
    attackCategories: ['prompt_injection', 'instruction_override'],
    riskThreshold: 70,
    action: 'BLOCK',
    requiresAuth: false,
    notifyAdmin: true,
  },
  {
    id: '2',
    name: '跨住民存取防護',
    description: '阻擋嘗試存取其他住民資料的請求',
    enabled: true,
    attackCategories: ['cross_resident_access'],
    riskThreshold: 50,
    action: 'BLOCK',
    requiresAuth: false,
    notifyAdmin: true,
  },
  {
    id: '3',
    name: '機密提取防護',
    description: '阻擋嘗試取得系統機密的請求',
    enabled: true,
    attackCategories: ['secret_extraction'],
    riskThreshold: 60,
    action: 'BLOCK',
    requiresAuth: false,
    notifyAdmin: true,
  },
  {
    id: '4',
    name: '編碼混淆偵測',
    description: '偵測使用編碼方式規避檢查的輸入',
    enabled: true,
    attackCategories: ['encoding_obfuscation'],
    riskThreshold: 65,
    action: 'BLOCK',
    requiresAuth: false,
    notifyAdmin: false,
  },
  {
    id: '5',
    name: '角色偽裝防護',
    description: '偵測試圖假冒其他角色的行為',
    enabled: true,
    attackCategories: ['role_impersonation'],
    riskThreshold: 75,
    action: 'AUTHORIZE',
    requiresAuth: true,
    notifyAdmin: true,
  },
  {
    id: '6',
    name: '工具濫用監控',
    description: '監控異常的工具呼叫模式',
    enabled: true,
    attackCategories: ['tool_abuse'],
    riskThreshold: 80,
    action: 'WARN',
    requiresAuth: false,
    notifyAdmin: false,
  },
];

// 預設風險閾值
const defaultThresholds: RiskThresholds = {
  low: 30,
  medium: 50,
  high: 70,
  critical: 90,
};

export default function PolicyEditor() {
  const [tabValue, setTabValue] = useState(0);
  const [rules, setRules] = useState<PolicyRule[]>(mockRules);
  const [thresholds, setThresholds] = useState<RiskThresholds>(defaultThresholds);
  const [editDialogOpen, setEditDialogOpen] = useState(false);
  const [editRule, setEditRule] = useState<Partial<PolicyRule>>({});
  const [hasChanges, setHasChanges] = useState(false);

  // 切換規則啟用狀態
  const toggleRuleEnabled = (id: string) => {
    setRules((prev) => prev.map((r) => (r.id === id ? { ...r, enabled: !r.enabled } : r)));
    setHasChanges(true);
  };

  // 開啟編輯對話框
  const handleEdit = (rule: PolicyRule) => {
    setEditRule({ ...rule });
    setEditDialogOpen(true);
  };

  // 開啟新增對話框
  const handleAdd = () => {
    setEditRule({
      name: '',
      description: '',
      enabled: true,
      attackCategories: [],
      riskThreshold: 70,
      action: 'BLOCK',
      requiresAuth: false,
      notifyAdmin: false,
    });
    setEditDialogOpen(true);
  };

  // 切換攻擊類別
  const toggleAttackCategory = (category: AttackCategory) => {
    const current = editRule.attackCategories || [];
    if (current.includes(category)) {
      setEditRule({ ...editRule, attackCategories: current.filter((c) => c !== category) });
    } else {
      setEditRule({ ...editRule, attackCategories: [...current, category] });
    }
  };

  // 儲存規則
  const handleSaveRule = () => {
    if (editRule.id) {
      setRules((prev) => prev.map((r) => (r.id === editRule.id ? ({ ...r, ...editRule } as PolicyRule) : r)));
    } else {
      const newRule: PolicyRule = {
        id: Date.now().toString(),
        name: editRule.name || '',
        description: editRule.description || '',
        enabled: editRule.enabled ?? true,
        attackCategories: editRule.attackCategories || [],
        riskThreshold: editRule.riskThreshold || 70,
        action: editRule.action || 'BLOCK',
        requiresAuth: editRule.requiresAuth ?? false,
        notifyAdmin: editRule.notifyAdmin ?? false,
      };
      setRules((prev) => [...prev, newRule]);
    }
    setEditDialogOpen(false);
    setHasChanges(true);
  };

  // 刪除規則
  const handleDelete = (id: string) => {
    setRules((prev) => prev.filter((r) => r.id !== id));
    setHasChanges(true);
  };

  // 儲存所有變更
  const handleSaveAll = () => {
    // TODO: 呼叫 API 儲存
    console.log('Saving rules:', rules);
    console.log('Saving thresholds:', thresholds);
    setHasChanges(false);
    alert('政策已儲存');
  };

  // 重置為預設
  const handleReset = () => {
    setRules(mockRules);
    setThresholds(defaultThresholds);
    setHasChanges(false);
  };

  return (
    <Container maxWidth="lg" sx={{ py: 2 }}>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
        <Typography variant="h4" sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
          <PolicyIcon color="primary" />
          政策編輯器
        </Typography>
        <Box sx={{ display: 'flex', gap: 1 }}>
          <Button variant="outlined" startIcon={<RestoreIcon />} onClick={handleReset}>
            重置
          </Button>
          <Button
            variant="contained"
            startIcon={<SaveIcon />}
            onClick={handleSaveAll}
            disabled={!hasChanges}
          >
            儲存變更
          </Button>
        </Box>
      </Box>

      {hasChanges && (
        <Alert severity="warning" sx={{ mb: 2 }}>
          有未儲存的變更
        </Alert>
      )}

      <Paper sx={{ mb: 2 }}>
        <Tabs value={tabValue} onChange={(_, v) => setTabValue(v)}>
          <Tab label="政策規則" />
          <Tab label="風險閾值" />
          <Tab label="全域設定" />
        </Tabs>
      </Paper>

      {/* 政策規則 */}
      {tabValue === 0 && (
        <>
          <Box sx={{ mb: 2 }}>
            <Button variant="contained" startIcon={<AddIcon />} onClick={handleAdd}>
              新增規則
            </Button>
          </Box>
          <Paper>
            <Table>
              <TableHead>
                <TableRow>
                  <TableCell>啟用</TableCell>
                  <TableCell>規則名稱</TableCell>
                  <TableCell>攻擊類別</TableCell>
                  <TableCell>風險閾值</TableCell>
                  <TableCell>動作</TableCell>
                  <TableCell>選項</TableCell>
                  <TableCell>操作</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {rules.map((rule) => (
                  <TableRow key={rule.id} sx={{ opacity: rule.enabled ? 1 : 0.5 }}>
                    <TableCell>
                      <Switch checked={rule.enabled} onChange={() => toggleRuleEnabled(rule.id)} />
                    </TableCell>
                    <TableCell>
                      <Typography fontWeight="bold">{rule.name}</Typography>
                      <Typography variant="caption" color="text.secondary">
                        {rule.description}
                      </Typography>
                    </TableCell>
                    <TableCell>
                      <Box sx={{ display: 'flex', gap: 0.5, flexWrap: 'wrap' }}>
                        {rule.attackCategories.map((cat) => (
                          <Chip key={cat} size="small" label={attackCategoryLabels[cat]} />
                        ))}
                      </Box>
                    </TableCell>
                    <TableCell>
                      <Chip
                        size="small"
                        label={`≥ ${rule.riskThreshold}`}
                        color={rule.riskThreshold >= 70 ? 'error' : rule.riskThreshold >= 50 ? 'warning' : 'success'}
                      />
                    </TableCell>
                    <TableCell>
                      <Chip
                        size="small"
                        label={policyActionConfig[rule.action].label}
                        color={policyActionConfig[rule.action].color}
                      />
                    </TableCell>
                    <TableCell>
                      <Box sx={{ display: 'flex', gap: 0.5 }}>
                        {rule.requiresAuth && <Chip size="small" label="驗證" variant="outlined" />}
                        {rule.notifyAdmin && <Chip size="small" label="通知" variant="outlined" />}
                      </Box>
                    </TableCell>
                    <TableCell>
                      <IconButton size="small" onClick={() => handleEdit(rule)}>
                        <EditIcon />
                      </IconButton>
                      <IconButton size="small" color="error" onClick={() => handleDelete(rule.id)}>
                        <DeleteIcon />
                      </IconButton>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </Paper>
        </>
      )}

      {/* 風險閾值 */}
      {tabValue === 1 && (
        <Paper sx={{ p: 3 }}>
          <Typography variant="h6" gutterBottom>
            風險分數閾值設定
          </Typography>
          <Typography variant="body2" color="text.secondary" sx={{ mb: 3 }}>
            設定不同風險等級的分數門檻。風險分數由攻擊分類、資產風險、角色權限等因素計算得出。
          </Typography>

          <Box sx={{ display: 'flex', flexDirection: 'column', gap: 4 }}>
            <Box>
              <Typography gutterBottom>低風險閾值: {thresholds.low}</Typography>
              <Slider
                value={thresholds.low}
                onChange={(_, v) => {
                  setThresholds({ ...thresholds, low: v as number });
                  setHasChanges(true);
                }}
                min={0}
                max={100}
                marks={[{ value: 0, label: '0' }, { value: 50, label: '50' }, { value: 100, label: '100' }]}
                color="success"
              />
            </Box>
            <Box>
              <Typography gutterBottom>中風險閾值: {thresholds.medium}</Typography>
              <Slider
                value={thresholds.medium}
                onChange={(_, v) => {
                  setThresholds({ ...thresholds, medium: v as number });
                  setHasChanges(true);
                }}
                min={0}
                max={100}
                color="warning"
              />
            </Box>
            <Box>
              <Typography gutterBottom>高風險閾值: {thresholds.high}</Typography>
              <Slider
                value={thresholds.high}
                onChange={(_, v) => {
                  setThresholds({ ...thresholds, high: v as number });
                  setHasChanges(true);
                }}
                min={0}
                max={100}
                color="error"
              />
            </Box>
            <Box>
              <Typography gutterBottom>嚴重風險閾值: {thresholds.critical}</Typography>
              <Slider
                value={thresholds.critical}
                onChange={(_, v) => {
                  setThresholds({ ...thresholds, critical: v as number });
                  setHasChanges(true);
                }}
                min={0}
                max={100}
                sx={{ color: '#d32f2f' }}
              />
            </Box>
          </Box>
        </Paper>
      )}

      {/* 全域設定 */}
      {tabValue === 2 && (
        <Paper sx={{ p: 3 }}>
          <Typography variant="h6" gutterBottom>
            全域安全設定
          </Typography>

          <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
            <FormControlLabel control={<Switch defaultChecked />} label="啟用輸入守衛" />
            <FormControlLabel control={<Switch defaultChecked />} label="啟用輸出守衛" />
            <FormControlLabel control={<Switch defaultChecked />} label="啟用串流監控" />
            <FormControlLabel control={<Switch defaultChecked />} label="啟用 Token 守衛" />
            <FormControlLabel control={<Switch defaultChecked />} label="啟用工具白名單" />
            <FormControlLabel control={<Switch />} label="嚴格模式（所有可疑請求都阻擋）" />
            <FormControlLabel control={<Switch defaultChecked />} label="記錄所有安全事件" />
            <FormControlLabel control={<Switch />} label="高風險事件即時通知管理者" />
          </Box>
        </Paper>
      )}

      {/* 編輯對話框 */}
      <Dialog open={editDialogOpen} onClose={() => setEditDialogOpen(false)} maxWidth="sm" fullWidth>
        <DialogTitle>{editRule.id ? '編輯規則' : '新增規則'}</DialogTitle>
        <DialogContent>
          <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2, mt: 1 }}>
            <TextField
              label="規則名稱"
              fullWidth
              value={editRule.name || ''}
              onChange={(e) => setEditRule({ ...editRule, name: e.target.value })}
            />
            <TextField
              label="說明"
              fullWidth
              multiline
              rows={2}
              value={editRule.description || ''}
              onChange={(e) => setEditRule({ ...editRule, description: e.target.value })}
            />

            <Typography variant="subtitle2">攻擊類別</Typography>
            <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1 }}>
              {Object.entries(attackCategoryLabels).map(([cat, label]) => (
                <Chip
                  key={cat}
                  label={label}
                  onClick={() => toggleAttackCategory(cat as AttackCategory)}
                  color={editRule.attackCategories?.includes(cat as AttackCategory) ? 'primary' : 'default'}
                  variant={editRule.attackCategories?.includes(cat as AttackCategory) ? 'filled' : 'outlined'}
                />
              ))}
            </Box>

            <Typography variant="subtitle2">風險閾值: {editRule.riskThreshold || 70}</Typography>
            <Slider
              value={editRule.riskThreshold || 70}
              onChange={(_, v) => setEditRule({ ...editRule, riskThreshold: v as number })}
              min={0}
              max={100}
              marks={[{ value: 30, label: '低' }, { value: 50, label: '中' }, { value: 70, label: '高' }, { value: 90, label: '嚴重' }]}
            />

            <FormControl fullWidth>
              <InputLabel>政策動作</InputLabel>
              <Select
                value={editRule.action || 'BLOCK'}
                label="政策動作"
                onChange={(e) => setEditRule({ ...editRule, action: e.target.value as PolicyAction })}
              >
                {Object.entries(policyActionConfig).map(([key, config]) => (
                  <MenuItem key={key} value={key}>
                    {config.label} - {config.description}
                  </MenuItem>
                ))}
              </Select>
            </FormControl>

            <FormControlLabel
              control={
                <Switch
                  checked={editRule.requiresAuth || false}
                  onChange={(e) => setEditRule({ ...editRule, requiresAuth: e.target.checked })}
                />
              }
              label="要求額外身分驗證"
            />
            <FormControlLabel
              control={
                <Switch
                  checked={editRule.notifyAdmin || false}
                  onChange={(e) => setEditRule({ ...editRule, notifyAdmin: e.target.checked })}
                />
              }
              label="通知管理者"
            />
          </Box>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setEditDialogOpen(false)}>取消</Button>
          <Button variant="contained" onClick={handleSaveRule}>
            儲存
          </Button>
        </DialogActions>
      </Dialog>
    </Container>
  );
}
