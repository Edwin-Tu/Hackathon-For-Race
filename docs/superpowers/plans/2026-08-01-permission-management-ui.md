# 權限管理前端 UI 調整實作計畫

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 調整權限管理相關前端頁面，對齊 F07 規劃並優化使用者體驗

**Architecture:** 漸進式調整現有 4 個 React 組件，保留 mock 資料模式，更新權限定義、政策規則結構、授權模板及登入流程

**Tech Stack:** React 18, TypeScript, MUI v6, Next.js

## Global Constraints

- 僅調整前端 UI，所有資料維持 mock
- 保留現有 TypeScript 類型安全
- 保留現有 MUI 組件風格
- 不新增任何 npm 依賴

---

## File Structure

| 檔案 | 職責 |
|-----|------|
| `src/pages/admin/Roles.tsx` | 角色管理頁面 — 更新權限清單為 8 大類 25 項 |
| `src/pages/admin/PolicyEditor.tsx` | 政策編輯器 — 新增受影響範圍欄位與編輯功能 |
| `src/pages/family/Authorizations.tsx` | 家屬授權管理 — 新增授權模板功能 |
| `src/pages/login.tsx` | 登入頁面 — 移除模式切換，住民入口整合至 Demo 區 |

---

### Task 1: 更新權限清單（Roles.tsx）

**Files:**
- Modify: `src/pages/admin/Roles.tsx:35-92` (allPermissions 與 mockRoles)

**Interfaces:**
- Produces: 更新後的 `allPermissions` 陣列（8 大類 25 項），更新後的 `mockRoles` 角色預設權限

- [ ] **Step 1: 更新 allPermissions 陣列**

將 `allPermissions` 陣列替換為新的 8 大類 25 項權限：

```typescript
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
```

- [ ] **Step 2: 更新 mockRoles 角色預設權限**

更新各角色的 permissions 陣列：

```typescript
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
```

- [ ] **Step 3: 手動驗證頁面顯示**

執行開發伺服器，導航至 `/admin/Roles`：
- 確認新增的 8 大類權限分組正確顯示
- 確認各角色的預設權限正確
- 確認編輯對話框的 Accordion 分類正確

Run: `npm run dev`
驗證: 瀏覽器開啟 http://localhost:3000/admin/Roles

- [ ] **Step 4: Commit**

```bash
git add src/pages/admin/Roles.tsx
git commit -m "feat(roles): update permissions to align with F07 spec (8 categories, 25 items)"
```

---

### Task 2: 政策編輯器新增受影響範圍（PolicyEditor.tsx）

**Files:**
- Modify: `src/pages/admin/PolicyEditor.tsx`

**Interfaces:**
- Consumes: 無（獨立頁面）
- Produces: 更新後的 `PolicyRule` interface，包含 `affectedPermissions` 與 `affectedRoles`

- [ ] **Step 1: 更新 PolicyRule interface**

在 `PolicyRule` interface 中新增兩個欄位：

```typescript
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
  // 新增
  affectedPermissions: string[];
  affectedRoles: string[];
}
```

- [ ] **Step 2: 新增權限與角色選項定義**

在檔案頂部新增權限清單與角色清單供選擇使用：

```typescript
// 權限選項（簡化版，供政策編輯器選擇）
const permissionOptions = [
  { key: '*', label: '全部權限' },
  { key: 'resident:*', label: '住民資料（全部）' },
  { key: 'event:*', label: '生活事件（全部）' },
  { key: 'event:write', label: '建立生活事件' },
  { key: 'reminder:*', label: '提醒管理（全部）' },
  { key: 'reminder:write', label: '建立提醒' },
  { key: 'memory:*', label: '記憶管理（全部）' },
  { key: 'memory:read', label: '查看記憶' },
  { key: 'memory:correct', label: '修正記憶' },
  { key: 'privacy:cross_resident', label: '跨住民存取' },
  { key: 'privacy:*', label: '住民隔離（全部）' },
  { key: 'security:assets', label: '管理資產' },
  { key: 'security:*', label: '安全管理（全部）' },
  { key: 'admin:*', label: '系統管理（全部）' },
];

// 角色選項
const roleOptions = [
  { key: 'ADMIN', label: '系統管理者' },
  { key: 'CAREGIVER', label: '照護人員' },
  { key: 'FAMILY', label: '家屬' },
  { key: 'RESIDENT', label: '住民' },
];
```

- [ ] **Step 3: 更新 mockRules 加入預設受影響範圍**

更新 mockRules 陣列，為每條規則加入 `affectedPermissions` 與 `affectedRoles`：

```typescript
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
    affectedPermissions: ['*'],
    affectedRoles: ['ADMIN', 'CAREGIVER', 'FAMILY', 'RESIDENT'],
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
    affectedPermissions: ['privacy:cross_resident'],
    affectedRoles: ['CAREGIVER', 'FAMILY', 'RESIDENT'],
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
    affectedPermissions: ['security:assets', 'memory:read'],
    affectedRoles: ['ADMIN', 'CAREGIVER', 'FAMILY', 'RESIDENT'],
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
    affectedPermissions: ['*'],
    affectedRoles: ['ADMIN', 'CAREGIVER', 'FAMILY', 'RESIDENT'],
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
    affectedPermissions: ['admin:*', 'privacy:*'],
    affectedRoles: ['CAREGIVER', 'FAMILY', 'RESIDENT'],
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
    affectedPermissions: ['event:write', 'reminder:write', 'memory:correct'],
    affectedRoles: ['CAREGIVER'],
  },
];
```

- [ ] **Step 4: 在表格中新增「受影響範圍」欄位**

在 TableHead 和 TableBody 中新增欄位：

```tsx
// TableHead 中，在「動作」欄後新增
<TableCell>受影響範圍</TableCell>

// TableBody 中，在動作 Chip 後新增
<TableCell>
  <Box sx={{ display: 'flex', flexDirection: 'column', gap: 0.5 }}>
    <Box sx={{ display: 'flex', gap: 0.5, flexWrap: 'wrap' }}>
      {rule.affectedPermissions.slice(0, 2).map((perm) => (
        <Chip
          key={perm}
          size="small"
          label={permissionOptions.find((p) => p.key === perm)?.label || perm}
          variant="outlined"
          color="primary"
        />
      ))}
      {rule.affectedPermissions.length > 2 && (
        <Chip size="small" label={`+${rule.affectedPermissions.length - 2}`} variant="outlined" />
      )}
    </Box>
    <Typography variant="caption" color="text.secondary">
      {rule.affectedRoles.map((r) => roleOptions.find((ro) => ro.key === r)?.label || r).join('、')}
    </Typography>
  </Box>
</TableCell>
```

- [ ] **Step 5: 在編輯對話框新增受影響權限與角色選擇**

在編輯對話框的「風險閾值」下方，新增兩個 Autocomplete 欄位：

```tsx
// 在 Slider 下方新增
<Typography variant="subtitle2" sx={{ mt: 2 }}>受影響權限</Typography>
<Autocomplete
  multiple
  options={permissionOptions}
  getOptionLabel={(option) => option.label}
  value={permissionOptions.filter((p) => editRule.affectedPermissions?.includes(p.key))}
  onChange={(_, newValue) =>
    setEditRule({ ...editRule, affectedPermissions: newValue.map((v) => v.key) })
  }
  renderInput={(params) => (
    <TextField {...params} placeholder="選擇權限" size="small" />
  )}
  renderTags={(value, getTagProps) =>
    value.map((option, index) => (
      <Chip
        variant="outlined"
        label={option.label}
        size="small"
        {...getTagProps({ index })}
        key={option.key}
      />
    ))
  }
/>

<Typography variant="subtitle2" sx={{ mt: 2 }}>受影響角色</Typography>
<Autocomplete
  multiple
  options={roleOptions}
  getOptionLabel={(option) => option.label}
  value={roleOptions.filter((r) => editRule.affectedRoles?.includes(r.key))}
  onChange={(_, newValue) =>
    setEditRule({ ...editRule, affectedRoles: newValue.map((v) => v.key) })
  }
  renderInput={(params) => (
    <TextField {...params} placeholder="選擇角色" size="small" />
  )}
  renderTags={(value, getTagProps) =>
    value.map((option, index) => (
      <Chip
        variant="outlined"
        label={option.label}
        size="small"
        {...getTagProps({ index })}
        key={option.key}
      />
    ))
  }
/>
```

- [ ] **Step 6: 更新 handleAdd 初始值**

在 `handleAdd` 函式中加入新欄位的初始值：

```typescript
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
    affectedPermissions: [],
    affectedRoles: [],
  });
  setEditDialogOpen(true);
};
```

- [ ] **Step 7: 更新 handleSaveRule 新增欄位**

在 `handleSaveRule` 函式中處理新欄位：

```typescript
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
      affectedPermissions: editRule.affectedPermissions || [],
      affectedRoles: editRule.affectedRoles || [],
    };
    setRules((prev) => [...prev, newRule]);
  }
  setEditDialogOpen(false);
  setHasChanges(true);
};
```

- [ ] **Step 8: 新增 Autocomplete import**

在檔案頂部的 import 中新增 Autocomplete：

```typescript
import {
  // ... 現有 imports
  Autocomplete,
} from '@mui/material';
```

- [ ] **Step 9: 手動驗證頁面顯示**

執行開發伺服器，導航至 `/admin/PolicyEditor`：
- 確認表格新增「受影響範圍」欄位
- 確認編輯對話框可選擇受影響權限與角色
- 確認新增規則時可正確儲存

Run: `npm run dev`
驗證: 瀏覽器開啟 http://localhost:3000/admin/PolicyEditor

- [ ] **Step 10: Commit**

```bash
git add src/pages/admin/PolicyEditor.tsx
git commit -m "feat(policy): add affected permissions and roles to policy rules"
```

---

### Task 3: 家屬授權模板（Authorizations.tsx）

**Files:**
- Modify: `src/pages/family/Authorizations.tsx`

**Interfaces:**
- Consumes: 無（獨立頁面）
- Produces: 新增 `authTemplates` 定義與模板選擇 UI

- [ ] **Step 1: 新增授權模板定義**

在檔案頂部（scopeLabels 之後）新增授權模板定義：

```typescript
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
```

- [ ] **Step 2: 新增 selectedTemplate state**

在 component 內新增 state：

```typescript
const [selectedTemplate, setSelectedTemplate] = useState<AuthTemplate>('standard');
```

- [ ] **Step 3: 新增 import ToggleButtonGroup**

在 import 中新增 ToggleButtonGroup 和 ToggleButton：

```typescript
import {
  // ... 現有 imports
  ToggleButtonGroup,
  ToggleButton,
} from '@mui/material';
```

- [ ] **Step 4: 更新列表中的授權範圍顯示**

在 TableBody 中，將原本的多個 Chip 改為簡化顯示：

```tsx
<TableCell>
  <Chip
    size="small"
    label={getTemplateLabelFromScope(auth.scope)}
    color={getTemplateFromScope(auth.scope) === 'custom' ? 'default' : 'primary'}
    variant={getTemplateFromScope(auth.scope) === 'custom' ? 'outlined' : 'filled'}
  />
</TableCell>
```

- [ ] **Step 5: 更新 handleAdd 設定預設模板**

更新 handleAdd，設定預設選擇「標準」模板：

```typescript
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
```

- [ ] **Step 6: 更新 handleEdit 設定當前模板**

更新 handleEdit，偵測當前模板：

```typescript
const handleEdit = (auth: Authorization) => {
  setSelectedTemplate(getTemplateFromScope(auth.scope));
  setEditAuth({ ...auth });
  setEditDialogOpen(true);
};
```

- [ ] **Step 7: 新增模板選擇處理函式**

新增處理模板切換的函式：

```typescript
const handleTemplateChange = (newTemplate: AuthTemplate) => {
  if (newTemplate && newTemplate !== 'custom') {
    setSelectedTemplate(newTemplate);
    setEditAuth({
      ...editAuth,
      scope: { ...authTemplates[newTemplate].scope },
    });
  }
};
```

- [ ] **Step 8: 更新 toggleScope 函式**

更新 toggleScope，切換後重新偵測模板：

```typescript
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
```

- [ ] **Step 9: 在編輯對話框新增模板選擇 UI**

在「授權範圍」標題下方新增 ToggleButtonGroup：

```tsx
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
  {/* ... 原有的 Checkbox 列表 ... */}
</FormGroup>
```

- [ ] **Step 10: 手動驗證頁面顯示**

執行開發伺服器，導航至 `/family/Authorizations`：
- 確認列表顯示模板名稱（標準授權、完整授權等）
- 確認編輯對話框有模板選擇按鈕
- 確認選擇模板後自動套用勾選
- 確認手動調整後顯示「自訂」

Run: `npm run dev`
驗證: 瀏覽器開啟 http://localhost:3000/family/Authorizations

- [ ] **Step 11: Commit**

```bash
git add src/pages/family/Authorizations.tsx
git commit -m "feat(auth): add authorization templates (basic/standard/full)"
```

---

### Task 4: 登入介面簡化（login.tsx）

**Files:**
- Modify: `src/pages/login.tsx`

**Interfaces:**
- Consumes: 無（獨立頁面）
- Produces: 簡化後的登入頁面，住民入口整合至 Demo 區

- [ ] **Step 1: 移除 loginMode state 與相關邏輯**

刪除以下程式碼：
- `const [loginMode, setLoginMode] = useState<LoginMode>('staff');`
- `type LoginMode = 'staff' | 'resident';`

- [ ] **Step 2: 新增 expandedResident state**

新增用於控制住民卡片展開的 state：

```typescript
const [expandedResident, setExpandedResident] = useState(false);
```

- [ ] **Step 3: 新增 Collapse import**

在 import 中新增 Collapse：

```typescript
import {
  // ... 現有 imports
  Collapse,
} from '@mui/material';
```

- [ ] **Step 4: 更新 demoAccounts 加入住民選項**

更新 demoAccounts 陣列，加入住民：

```typescript
const demoAccounts: DemoAccount[] = [
  { 
    username: 'admin', 
    role: 'ADMIN', 
    displayName: '系統管理者', 
    icon: <AdminPanelSettingsIcon />, 
    color: 'error',
    description: '管理使用者、角色與系統設定',
  },
  { 
    username: 'caregiver', 
    role: 'CAREGIVER', 
    displayName: '照護人員', 
    icon: <LocalHospitalIcon />, 
    color: 'info',
    description: '照護住民、查看摘要與警示',
  },
  { 
    username: 'family', 
    role: 'FAMILY', 
    displayName: '家屬', 
    icon: <FamilyRestroomIcon />, 
    color: 'success',
    description: '查看住民狀況與通知',
  },
  { 
    username: 'resident', 
    role: 'RESIDENT', 
    displayName: '住民（語音互動）', 
    icon: <RecordVoiceOverIcon />, 
    color: 'warning',
    description: '直接進入語音互動介面',
  },
];
```

- [ ] **Step 5: 更新 handleSubmit 移除 loginMode 判斷**

簡化 handleSubmit：

```typescript
const handleSubmit = async (e: React.FormEvent) => {
  e.preventDefault();
  setError('');
  
  if (!username || !password) {
    setError('請輸入帳號與密碼');
    return;
  }
  await performLogin(username);
};
```

- [ ] **Step 6: 更新 handleQuickLogin 處理住民卡片**

更新 handleQuickLogin 處理住民卡片的展開邏輯：

```typescript
const handleQuickLogin = (account: DemoAccount) => {
  if (account.role === 'RESIDENT') {
    setExpandedResident(!expandedResident);
    return;
  }
  setUsername(account.username);
  performLogin(account.username);
};
```

- [ ] **Step 7: 移除 ToggleButtonGroup 切換區塊**

刪除以下區塊（約在第 338-372 行）：

```tsx
{/* 登入模式切換 */}
<Box sx={{ display: 'flex', justifyContent: 'center', mb: 4 }}>
  <ToggleButtonGroup
    value={loginMode}
    ...
  </ToggleButtonGroup>
</Box>
```

- [ ] **Step 8: 移除住民登入獨立區塊**

刪除以下區塊（約在第 526-598 行）：

```tsx
{/* 住民登入（Persona 選擇） */}
{loginMode === 'resident' && (
  <Fade in timeout={300}>
    ...
  </Fade>
)}
```

- [ ] **Step 9: 移除 loginMode 條件判斷**

將原本的 `{loginMode === 'staff' && (...)}` 改為直接顯示（移除條件判斷）。

- [ ] **Step 10: 在住民卡片下方新增 Collapse 展開區**

在 Demo 卡片的 map 迴圈中，為住民卡片加入 Collapse：

```tsx
{demoAccounts.map((account, index) => (
  <React.Fragment key={account.username}>
    <Grow in timeout={400 + index * 100}>
      <Paper
        variant="outlined"
        sx={{
          p: 2,
          cursor: loading ? 'not-allowed' : 'pointer',
          transition: 'all 0.2s ease',
          opacity: loading ? 0.6 : 1,
          '&:hover': loading ? {} : {
            borderColor: theme.palette[account.color].main,
            bgcolor: alpha(theme.palette[account.color].main, 0.04),
            transform: 'translateX(4px)',
          },
        }}
        onClick={() => !loading && handleQuickLogin(account)}
      >
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
          <Avatar 
            sx={{ 
              bgcolor: alpha(theme.palette[account.color].main, 0.15),
              color: theme.palette[account.color].main,
            }}
          >
            {account.icon}
          </Avatar>
          <Box sx={{ flex: 1 }}>
            <Typography variant="subtitle1" fontWeight={600}>
              {account.displayName}
            </Typography>
            <Typography variant="caption" color="text.secondary">
              {account.description}
            </Typography>
          </Box>
          <Chip
            size="small"
            label={account.username}
            color={account.color}
            variant="outlined"
          />
        </Box>
      </Paper>
    </Grow>
    
    {/* 住民 Persona 選擇展開區 */}
    {account.role === 'RESIDENT' && (
      <Collapse in={expandedResident}>
        <Box sx={{ pl: 4, pt: 1, display: 'flex', gap: 1, flexWrap: 'wrap' }}>
          {mockPersonas.map((persona) => (
            <Chip
              key={persona.id}
              label={persona.displayName}
              onClick={() => !loading && performResidentLogin(persona.id)}
              color="warning"
              variant="outlined"
              sx={{ 
                cursor: loading ? 'not-allowed' : 'pointer',
                '&:hover': { bgcolor: alpha(theme.palette.warning.main, 0.1) },
              }}
            />
          ))}
        </Box>
      </Collapse>
    )}
  </React.Fragment>
))}
```

- [ ] **Step 11: 清理未使用的程式碼**

移除以下不再使用的項目：
- `selectedPersona` state
- `setSelectedPersona` 相關邏輯
- 不再使用的 FormControl、Select、MenuItem（如果沒有其他地方使用）

- [ ] **Step 12: 手動驗證頁面顯示**

執行開發伺服器，導航至 `/login`：
- 確認沒有員工/住民切換按鈕
- 確認 Demo 區有 4 個卡片
- 確認點擊「住民」卡片會展開 Persona 選擇
- 確認點擊 Persona 可正確登入

Run: `npm run dev`
驗證: 瀏覽器開啟 http://localhost:3000/login

- [ ] **Step 13: Commit**

```bash
git add src/pages/login.tsx
git commit -m "feat(login): simplify login page, integrate resident entry into demo section"
```

---

### Task 5: 最終驗證與整合 Commit

**Files:**
- 無新增修改，僅驗證

- [ ] **Step 1: 完整流程驗證**

依序驗證以下頁面：

1. `/login` — 確認登入流程正常
2. `/admin/Roles` — 確認權限清單正確
3. `/admin/PolicyEditor` — 確認政策規則含受影響範圍
4. `/family/Authorizations` — 確認授權模板功能

- [ ] **Step 2: 確認無 TypeScript 錯誤**

Run: `npm run build`
Expected: Build 成功，無 TypeScript 錯誤

- [ ] **Step 3: 最終整合 Commit（可選）**

如有需要額外調整，進行整合 commit：

```bash
git add .
git commit -m "chore: permission management UI adjustments complete"
```
