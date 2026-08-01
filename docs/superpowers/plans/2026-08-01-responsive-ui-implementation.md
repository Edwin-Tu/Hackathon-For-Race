# 響應式 UI 實作計畫

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 實作手機端底部導航、提醒管理類別標籤、及全站響應式排版修正。

**Architecture:** 新增 BottomNav 元件於手機版顯示，修改 Layout 整合導航邏輯。提醒管理新增 category 欄位並支援卡片式顯示。各頁面套用統一的響應式間距規範。

**Tech Stack:** Next.js 16, React 19, MUI v9, TypeScript

## Global Constraints

- 斷點策略：MUI 預設（xs:0, sm:600, md:960）
- 手機版定義：< 600px (sm 斷點以下)
- 最小觸控區域：44px × 44px
- 語言：繁體中文
- 程式碼註解：繁體中文

---

## File Structure

### 新增檔案
| 檔案路徑 | 職責 |
|----------|------|
| `src/components/BottomNav.tsx` | 手機版底部導航元件 |
| `src/components/BottomNavSheet.tsx` | 「更多」展開的 BottomSheet |
| `src/components/ReminderCard.tsx` | 手機版提醒卡片元件 |

### 修改檔案
| 檔案路徑 | 修改內容 |
|----------|----------|
| `src/layout/Layout.tsx` | 整合 BottomNav，調整手機版 padding |
| `src/layout/Drawer.tsx` | 匯出 routes 配置供 BottomNav 使用 |
| `src/pages/caregiver/reminders.tsx` | 新增 category 欄位、手機版卡片顯示 |
| `src/pages/caregiver/index.tsx` | 響應式間距調整 |
| `src/pages/family/Dashboard.tsx` | 響應式間距調整 |

---

### Task 1: 建立 BottomNav 元件

**Files:**
- Create: `src/components/BottomNav.tsx`
- Reference: `src/layout/Drawer.tsx` (routes 配置)

**Interfaces:**
- Consumes: `getUserRole()` from `src/utils/auth`
- Produces: `<BottomNav />` 元件，props: 無

- [ ] **Step 1: 建立 BottomNav 基礎結構**

```tsx
// src/components/BottomNav.tsx
'use client';
import React, { useState, useEffect } from 'react';
import {
  BottomNavigation,
  BottomNavigationAction,
  Paper,
  Badge,
  useMediaQuery,
} from '@mui/material';
import { useTheme } from '@mui/material/styles';
import { useRouter } from 'next/router';
import { getUserRole } from '../utils/auth';

// 圖示
import PeopleIcon from '@mui/icons-material/People';
import SummarizeIcon from '@mui/icons-material/Summarize';
import NotificationsActiveIcon from '@mui/icons-material/NotificationsActive';
import MoreHorizIcon from '@mui/icons-material/MoreHoriz';
import DashboardIcon from '@mui/icons-material/Dashboard';
import NotificationsIcon from '@mui/icons-material/Notifications';
import GroupIcon from '@mui/icons-material/Group';
import AdminPanelSettingsIcon from '@mui/icons-material/AdminPanelSettings';
import SecurityIcon from '@mui/icons-material/Security';
import RecordVoiceOverIcon from '@mui/icons-material/RecordVoiceOver';

// 底部導航項目介面
interface BottomNavItem {
  key: string;
  label: string;
  icon: React.ReactNode;
  href: string;
  badge?: number;
}

// 各角色的底部導航配置
const bottomNavRoutes: Record<string, { items: BottomNavItem[]; moreItems?: BottomNavItem[] }> = {
  RESIDENT: {
    items: [
      { key: 'voice', label: '語音互動', icon: <RecordVoiceOverIcon />, href: '/resident/voice' },
    ],
  },
  CAREGIVER: {
    items: [
      { key: 'residents', label: '住民列表', icon: <PeopleIcon />, href: '/caregiver' },
      { key: 'summary', label: '每日摘要', icon: <SummarizeIcon />, href: '/caregiver/summary' },
      { key: 'reminders', label: '提醒', icon: <NotificationsActiveIcon />, href: '/caregiver/reminders', badge: 5 },
      { key: 'more', label: '更多', icon: <MoreHorizIcon />, href: '' },
    ],
    moreItems: [
      { key: 'alerts', label: '高風險警示', icon: <NotificationsActiveIcon />, href: '/caregiver/alerts' },
      { key: 'timeline', label: '事件時間軸', icon: <SummarizeIcon />, href: '/caregiver/timeline' },
      { key: 'memory', label: '記憶修正', icon: <SummarizeIcon />, href: '/caregiver/memory' },
    ],
  },
  FAMILY: {
    items: [
      { key: 'dashboard', label: '概況', icon: <DashboardIcon />, href: '/family/Dashboard' },
      { key: 'notifications', label: '通知', icon: <NotificationsIcon />, href: '/family/Notifications', badge: 3 },
      { key: 'authorizations', label: '授權', icon: <GroupIcon />, href: '/family/Authorizations' },
    ],
  },
  ADMIN: {
    items: [
      { key: 'users', label: '用戶', icon: <PeopleIcon />, href: '/admin/Users' },
      { key: 'roles', label: '角色', icon: <AdminPanelSettingsIcon />, href: '/admin/Roles' },
      { key: 'audit', label: '稽核', icon: <SecurityIcon />, href: '/admin/AuditLog' },
      { key: 'more', label: '更多', icon: <MoreHorizIcon />, href: '' },
    ],
    moreItems: [
      { key: 'assets', label: '資產設定', icon: <AdminPanelSettingsIcon />, href: '/admin/Assets' },
      { key: 'policy', label: '政策編輯', icon: <AdminPanelSettingsIcon />, href: '/admin/PolicyEditor' },
      { key: 'security', label: '安全風險', icon: <SecurityIcon />, href: '/admin/Security' },
      { key: 'benchmark', label: '測試報告', icon: <SecurityIcon />, href: '/admin/Benchmark' },
    ],
  },
};

interface BottomNavProps {
  onMoreClick?: () => void;
}

export default function BottomNav({ onMoreClick }: BottomNavProps) {
  const theme = useTheme();
  const router = useRouter();
  const isMobile = useMediaQuery(theme.breakpoints.down('sm'));
  
  const [role, setRole] = useState<string | null>(null);
  const [mounted, setMounted] = useState(false);

  useEffect(() => {
    setMounted(true);
    const token = localStorage.getItem('auth');
    const userRole = getUserRole(token);
    setRole(userRole);
  }, []);

  // 登入頁面或非手機版不顯示
  if (router.pathname === '/login' || !isMobile || !mounted || !role) {
    return null;
  }

  const config = bottomNavRoutes[role];
  if (!config) return null;

  // 找出當前選中的導航項目
  const currentValue = config.items.findIndex(
    (item) => item.href && router.pathname.startsWith(item.href)
  );

  const handleChange = (_event: React.SyntheticEvent, newValue: number) => {
    const item = config.items[newValue];
    if (item.key === 'more') {
      onMoreClick?.();
    } else if (item.href) {
      router.push(item.href);
    }
  };

  return (
    <Paper
      sx={{
        position: 'fixed',
        bottom: 0,
        left: 0,
        right: 0,
        zIndex: theme.zIndex.appBar,
        borderTop: `1px solid ${theme.palette.divider}`,
      }}
      elevation={3}
    >
      <BottomNavigation
        value={currentValue >= 0 ? currentValue : false}
        onChange={handleChange}
        showLabels
        sx={{
          height: 56,
          '& .MuiBottomNavigationAction-root': {
            minWidth: 'auto',
            padding: '6px 12px',
            '&.Mui-selected': {
              color: theme.palette.primary.main,
            },
          },
          '& .MuiBottomNavigationAction-label': {
            fontSize: '0.7rem',
            '&.Mui-selected': {
              fontSize: '0.75rem',
            },
          },
        }}
      >
        {config.items.map((item) => (
          <BottomNavigationAction
            key={item.key}
            label={item.label}
            icon={
              item.badge ? (
                <Badge badgeContent={item.badge} color="error" max={99}>
                  {item.icon}
                </Badge>
              ) : (
                item.icon
              )
            }
          />
        ))}
      </BottomNavigation>
    </Paper>
  );
}

// 匯出配置供 BottomNavSheet 使用
export { bottomNavRoutes };
export type { BottomNavItem };
```

- [ ] **Step 2: 確認檔案建立成功**

執行：在 IDE 中確認 `src/components/BottomNav.tsx` 已建立

- [ ] **Step 3: Commit**

```bash
git add src/components/BottomNav.tsx
git commit -m "feat(ui): add BottomNav component for mobile navigation"
```

---

### Task 2: 建立 BottomNavSheet 元件

**Files:**
- Create: `src/components/BottomNavSheet.tsx`

**Interfaces:**
- Consumes: `bottomNavRoutes`, `BottomNavItem` from `src/components/BottomNav.tsx`
- Produces: `<BottomNavSheet open={boolean} onClose={fn} />` 元件

- [ ] **Step 1: 建立 BottomNavSheet 元件**

```tsx
// src/components/BottomNavSheet.tsx
'use client';
import React, { useState, useEffect } from 'react';
import {
  Drawer,
  List,
  ListItemButton,
  ListItemIcon,
  ListItemText,
  Typography,
  Box,
  Divider,
} from '@mui/material';
import { useTheme, alpha } from '@mui/material/styles';
import { useRouter } from 'next/router';
import { getUserRole } from '../utils/auth';
import { bottomNavRoutes, BottomNavItem } from './BottomNav';

interface BottomNavSheetProps {
  open: boolean;
  onClose: () => void;
}

export default function BottomNavSheet({ open, onClose }: BottomNavSheetProps) {
  const theme = useTheme();
  const router = useRouter();
  const [role, setRole] = useState<string | null>(null);

  useEffect(() => {
    const token = localStorage.getItem('auth');
    const userRole = getUserRole(token);
    setRole(userRole);
  }, []);

  if (!role) return null;

  const config = bottomNavRoutes[role];
  const moreItems = config?.moreItems || [];

  const handleItemClick = (item: BottomNavItem) => {
    router.push(item.href);
    onClose();
  };

  return (
    <Drawer
      anchor="bottom"
      open={open}
      onClose={onClose}
      PaperProps={{
        sx: {
          borderTopLeftRadius: 16,
          borderTopRightRadius: 16,
          maxHeight: '60vh',
        },
      }}
    >
      {/* 拖曳指示條 */}
      <Box sx={{ display: 'flex', justifyContent: 'center', py: 1.5 }}>
        <Box
          sx={{
            width: 40,
            height: 4,
            borderRadius: 2,
            bgcolor: alpha(theme.palette.text.primary, 0.2),
          }}
        />
      </Box>

      {/* 標題 */}
      <Box sx={{ px: 2, pb: 1 }}>
        <Typography variant="subtitle1" fontWeight={600}>
          更多功能
        </Typography>
      </Box>

      <Divider />

      {/* 選單項目 */}
      <List sx={{ px: 1, py: 1 }}>
        {moreItems.map((item) => {
          const isActive = router.pathname === item.href;
          return (
            <ListItemButton
              key={item.key}
              onClick={() => handleItemClick(item)}
              sx={{
                borderRadius: 2,
                mb: 0.5,
                minHeight: 48,
                '&:hover': {
                  bgcolor: alpha(theme.palette.primary.main, 0.08),
                },
                ...(isActive && {
                  bgcolor: alpha(theme.palette.primary.main, 0.12),
                }),
              }}
            >
              <ListItemIcon
                sx={{
                  minWidth: 40,
                  color: isActive ? 'primary.main' : 'text.secondary',
                }}
              >
                {item.icon}
              </ListItemIcon>
              <ListItemText
                primary={item.label}
                primaryTypographyProps={{
                  fontWeight: isActive ? 600 : 400,
                  color: isActive ? 'primary.main' : 'text.primary',
                }}
              />
            </ListItemButton>
          );
        })}
      </List>

      {/* 底部安全區域 */}
      <Box sx={{ height: 'env(safe-area-inset-bottom, 0px)' }} />
    </Drawer>
  );
}
```

- [ ] **Step 2: Commit**

```bash
git add src/components/BottomNavSheet.tsx
git commit -m "feat(ui): add BottomNavSheet for mobile more menu"
```

---

### Task 3: 整合 BottomNav 至 Layout

**Files:**
- Modify: `src/layout/Layout.tsx`

**Interfaces:**
- Consumes: `<BottomNav />`, `<BottomNavSheet />`
- Produces: 更新後的 Layout 元件

- [ ] **Step 1: 修改 Layout.tsx 引入 BottomNav**

在 `src/layout/Layout.tsx` 頂部新增 import：

```tsx
import BottomNav from '../components/BottomNav';
import BottomNavSheet from '../components/BottomNavSheet';
```

- [ ] **Step 2: 新增 BottomNavSheet 狀態**

在 `Layout` 元件內部，`mobileOpen` state 之後新增：

```tsx
const [moreSheetOpen, setMoreSheetOpen] = useState(false);
```

- [ ] **Step 3: 調整 Content 區域的 paddingBottom**

修改 main Box 的 sx，在手機版增加底部 padding：

```tsx
<Box 
  component="main" 
  sx={{ 
    flexGrow: 1, 
    p: { xs: 2, sm: 3 },
    pt: { xs: 2, sm: 3 },
    pb: { xs: 9, sm: 3 },  // 手機版增加底部空間給 BottomNav (56px + 16px)
    mt: 8,
    // ... 其餘保持不變
  }}
>
```

- [ ] **Step 4: 在 Layout return 中加入 BottomNav 與 BottomNavSheet**

在 `</Box>` (最外層) 前面加入：

```tsx
{/* 手機版底部導航 */}
<BottomNav onMoreClick={() => setMoreSheetOpen(true)} />
<BottomNavSheet 
  open={moreSheetOpen} 
  onClose={() => setMoreSheetOpen(false)} 
/>
```

- [ ] **Step 5: 執行開發伺服器確認**

執行：`npm run dev`
確認：手機版（< 600px）顯示底部導航，桌面版顯示側邊欄

- [ ] **Step 6: Commit**

```bash
git add src/layout/Layout.tsx
git commit -m "feat(layout): integrate BottomNav for mobile navigation"
```

---

### Task 4: 提醒管理新增類別欄位

**Files:**
- Modify: `src/pages/caregiver/reminders.tsx`

**Interfaces:**
- Consumes: 無外部依賴
- Produces: 更新後的 Reminders 頁面，含 category 欄位

- [ ] **Step 1: 新增類別類型與配置**

在 `reminders.tsx` 檔案頂部（`Importance` 定義之後）新增：

```tsx
// 提醒類別
type ReminderCategory = 'medication' | 'health' | 'appointment' | 'other';

const categoryConfig: Record<ReminderCategory, { label: string; icon: React.ReactNode; color: 'error' | 'success' | 'info' | 'default' }> = {
  medication: { label: '用藥', icon: <MedicationIcon />, color: 'error' },
  health: { label: '健康狀況', icon: <FavoriteIcon />, color: 'success' },
  appointment: { label: '回診', icon: <EventIcon />, color: 'info' },
  other: { label: '其他', icon: <MoreHorizIcon />, color: 'default' },
};
```

- [ ] **Step 2: 新增 import 圖示**

在 import 區塊新增：

```tsx
import MedicationIcon from '@mui/icons-material/Medication';
import FavoriteIcon from '@mui/icons-material/Favorite';
import EventIcon from '@mui/icons-material/Event';
import MoreHorizIcon from '@mui/icons-material/MoreHoriz';
```

- [ ] **Step 3: 更新 Reminder interface**

```tsx
interface Reminder {
  id: string;
  residentId: string;
  residentName: string;
  title: string;
  scheduledAt: Date;
  status: ReminderStatus;
  importance: Importance;
  category: ReminderCategory;  // 新增
  idempotencyKey: string;
  createdBy: string;
  completedAt?: Date;
}
```

- [ ] **Step 4: 更新 mockReminders 資料**

為每筆 mock 資料加入 `category` 欄位：

```tsx
const mockReminders: Reminder[] = [
  {
    id: '1',
    // ...其他欄位保持不變
    category: 'appointment',
  },
  {
    id: '2',
    // ...
    category: 'medication',
  },
  {
    id: '3',
    // ...
    category: 'health',
  },
  {
    id: '4',
    // ...
    category: 'medication',
  },
  {
    id: '5',
    // ...
    category: 'other',
  },
];
```

- [ ] **Step 5: 在 Table 新增類別欄位**

在 `renderTable` 函式的 TableHead 中，「提醒內容」之後新增：

```tsx
<TableCell>類別</TableCell>
```

在 TableBody 的 map 中，對應位置新增：

```tsx
<TableCell>
  <Chip
    size="small"
    icon={categoryConfig[reminder.category].icon}
    label={categoryConfig[reminder.category].label}
    color={categoryConfig[reminder.category].color}
  />
</TableCell>
```

- [ ] **Step 6: 在編輯對話框新增類別選擇**

在 DialogContent 的 TextField（提醒內容）之後、FormControl（重要性）之前新增：

```tsx
<FormControl fullWidth>
  <InputLabel>類別</InputLabel>
  <Select
    value={editReminder.category || 'other'}
    label="類別"
    onChange={(e) =>
      setEditReminder({ ...editReminder, category: e.target.value as ReminderCategory })
    }
  >
    {Object.entries(categoryConfig).map(([key, config]) => (
      <MenuItem key={key} value={key}>
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
          {config.icon}
          {config.label}
        </Box>
      </MenuItem>
    ))}
  </Select>
</FormControl>
```

- [ ] **Step 7: 更新 handleAdd 預設值**

```tsx
const handleAdd = () => {
  setEditReminder({
    importance: 'medium',
    category: 'other',  // 新增
    status: 'pending',
  });
  setEditDialogOpen(true);
};
```

- [ ] **Step 8: 更新 handleSave 新增邏輯**

在新增 Reminder 物件時加入 category：

```tsx
const newReminder: Reminder = {
  // ...其他欄位
  category: editReminder.category || 'other',
  // ...
};
```

- [ ] **Step 9: 執行開發伺服器確認**

確認：提醒列表顯示類別欄位，新增/編輯可選擇類別

- [ ] **Step 10: Commit**

```bash
git add src/pages/caregiver/reminders.tsx
git commit -m "feat(reminders): add category field (medication/health/appointment/other)"
```

---

### Task 5: 提醒管理手機版卡片顯示

**Files:**
- Create: `src/components/ReminderCard.tsx`
- Modify: `src/pages/caregiver/reminders.tsx`

**Interfaces:**
- Consumes: `Reminder`, `categoryConfig`, `statusConfig`, `importanceConfig`
- Produces: `<ReminderCard reminder={Reminder} onComplete={fn} onEdit={fn} onDelete={fn} />`

- [ ] **Step 1: 建立 ReminderCard 元件**

```tsx
// src/components/ReminderCard.tsx
'use client';
import React from 'react';
import {
  Card,
  CardContent,
  Box,
  Typography,
  Chip,
  IconButton,
  Tooltip,
} from '@mui/material';
import { useTheme, alpha } from '@mui/material/styles';
import CheckCircleIcon from '@mui/icons-material/CheckCircle';
import EditIcon from '@mui/icons-material/Edit';
import DeleteIcon from '@mui/icons-material/Delete';
import AccessTimeIcon from '@mui/icons-material/AccessTime';
import MedicationIcon from '@mui/icons-material/Medication';
import FavoriteIcon from '@mui/icons-material/Favorite';
import EventIcon from '@mui/icons-material/Event';
import MoreHorizIcon from '@mui/icons-material/MoreHoriz';

// 類型定義
type ReminderStatus = 'pending' | 'completed' | 'missed' | 'cancelled';
type Importance = 'high' | 'medium' | 'low';
type ReminderCategory = 'medication' | 'health' | 'appointment' | 'other';

interface Reminder {
  id: string;
  residentId: string;
  residentName: string;
  title: string;
  scheduledAt: Date;
  status: ReminderStatus;
  importance: Importance;
  category: ReminderCategory;
  idempotencyKey: string;
  createdBy: string;
  completedAt?: Date;
}

// 配置
const statusConfig: Record<ReminderStatus, { label: string; color: 'default' | 'success' | 'error' | 'warning' }> = {
  pending: { label: '待執行', color: 'warning' },
  completed: { label: '已完成', color: 'success' },
  missed: { label: '已錯過', color: 'error' },
  cancelled: { label: '已取消', color: 'default' },
};

const importanceConfig: Record<Importance, { label: string; color: 'error' | 'warning' | 'info' }> = {
  high: { label: '高', color: 'error' },
  medium: { label: '中', color: 'warning' },
  low: { label: '低', color: 'info' },
};

const categoryConfig: Record<ReminderCategory, { label: string; icon: React.ReactNode; color: 'error' | 'success' | 'info' | 'default' }> = {
  medication: { label: '用藥', icon: <MedicationIcon sx={{ fontSize: 16 }} />, color: 'error' },
  health: { label: '健康狀況', icon: <FavoriteIcon sx={{ fontSize: 16 }} />, color: 'success' },
  appointment: { label: '回診', icon: <EventIcon sx={{ fontSize: 16 }} />, color: 'info' },
  other: { label: '其他', icon: <MoreHorizIcon sx={{ fontSize: 16 }} />, color: 'default' },
};

interface ReminderCardProps {
  reminder: Reminder;
  onComplete?: (id: string) => void;
  onEdit?: (reminder: Reminder) => void;
  onDelete?: (id: string) => void;
}

export default function ReminderCard({ reminder, onComplete, onEdit, onDelete }: ReminderCardProps) {
  const theme = useTheme();

  const formatDateTime = (date: Date) => {
    return date.toLocaleString('zh-TW', {
      month: 'numeric',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    });
  };

  return (
    <Card
      sx={{
        mb: 1.5,
        border: reminder.status === 'pending' && reminder.importance === 'high'
          ? `1px solid ${theme.palette.error.main}`
          : `1px solid ${theme.palette.divider}`,
      }}
    >
      <CardContent sx={{ p: 2, '&:last-child': { pb: 2 } }}>
        {/* 頂部：類別與優先級 */}
        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 1 }}>
          <Chip
            size="small"
            icon={categoryConfig[reminder.category].icon}
            label={categoryConfig[reminder.category].label}
            color={categoryConfig[reminder.category].color}
            sx={{ height: 24 }}
          />
          <Chip
            size="small"
            label={`${importanceConfig[reminder.importance].label}優先`}
            color={importanceConfig[reminder.importance].color}
            variant="outlined"
            sx={{ height: 24 }}
          />
        </Box>

        {/* 住民名稱 */}
        <Typography variant="caption" color="text.secondary">
          {reminder.residentName}
        </Typography>

        {/* 提醒內容 */}
        <Typography
          variant="body1"
          fontWeight={500}
          sx={{
            mt: 0.5,
            mb: 1,
            display: '-webkit-box',
            WebkitLineClamp: 2,
            WebkitBoxOrient: 'vertical',
            overflow: 'hidden',
          }}
        >
          {reminder.title}
        </Typography>

        {/* 底部：時間、狀態、操作按鈕 */}
        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1.5 }}>
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
              <AccessTimeIcon sx={{ fontSize: 14, color: 'text.secondary' }} />
              <Typography variant="caption" color="text.secondary">
                {formatDateTime(reminder.scheduledAt)}
              </Typography>
            </Box>
            <Chip
              size="small"
              label={statusConfig[reminder.status].label}
              color={statusConfig[reminder.status].color}
              sx={{ height: 20, fontSize: '0.7rem' }}
            />
          </Box>

          {/* 操作按鈕 */}
          <Box sx={{ display: 'flex', gap: 0.5 }}>
            {reminder.status === 'pending' && onComplete && (
              <Tooltip title="標記完成">
                <IconButton
                  size="small"
                  color="success"
                  onClick={() => onComplete(reminder.id)}
                  sx={{ minWidth: 44, minHeight: 44 }}
                >
                  <CheckCircleIcon />
                </IconButton>
              </Tooltip>
            )}
            {onEdit && (
              <Tooltip title="編輯">
                <IconButton
                  size="small"
                  onClick={() => onEdit(reminder)}
                  sx={{ minWidth: 44, minHeight: 44 }}
                >
                  <EditIcon />
                </IconButton>
              </Tooltip>
            )}
            {onDelete && (
              <Tooltip title="刪除">
                <IconButton
                  size="small"
                  color="error"
                  onClick={() => onDelete(reminder.id)}
                  sx={{ minWidth: 44, minHeight: 44 }}
                >
                  <DeleteIcon />
                </IconButton>
              </Tooltip>
            )}
          </Box>
        </Box>
      </CardContent>
    </Card>
  );
}

export type { Reminder, ReminderStatus, Importance, ReminderCategory };
```

- [ ] **Step 2: 在 reminders.tsx 引入 ReminderCard 與 useMediaQuery**

```tsx
import { useMediaQuery } from '@mui/material';
import { useTheme } from '@mui/material/styles';
import ReminderCard from '../../components/ReminderCard';
```

- [ ] **Step 3: 在 Reminders 元件內新增 hooks**

```tsx
const theme = useTheme();
const isMobile = useMediaQuery(theme.breakpoints.down('sm'));
```

- [ ] **Step 4: 建立卡片列表渲染函式**

在 `renderTable` 函式之後新增：

```tsx
// 渲染手機版卡片列表
const renderCardList = (data: Reminder[]) => (
  <Box sx={{ px: 1 }}>
    {data.length === 0 ? (
      <Typography color="text.secondary" align="center" sx={{ py: 4 }}>
        沒有提醒
      </Typography>
    ) : (
      data.map((reminder) => (
        <ReminderCard
          key={reminder.id}
          reminder={reminder}
          onComplete={handleComplete}
          onEdit={handleEdit}
          onDelete={handleDelete}
        />
      ))
    )}
  </Box>
);
```

- [ ] **Step 5: 修改提醒列表區塊的渲染邏輯**

將原本的：

```tsx
<Paper>
  {tabValue === 0 && renderTable(pendingReminders)}
  {tabValue === 1 && renderTable(completedReminders)}
  {tabValue === 2 && renderTable(missedReminders)}
</Paper>
```

改為：

```tsx
<Paper sx={{ overflow: 'hidden' }}>
  {isMobile ? (
    <>
      {tabValue === 0 && renderCardList(pendingReminders)}
      {tabValue === 1 && renderCardList(completedReminders)}
      {tabValue === 2 && renderCardList(missedReminders)}
    </>
  ) : (
    <>
      {tabValue === 0 && renderTable(pendingReminders)}
      {tabValue === 1 && renderTable(completedReminders)}
      {tabValue === 2 && renderTable(missedReminders)}
    </>
  )}
</Paper>
```

- [ ] **Step 6: 執行開發伺服器確認**

確認：手機版（< 600px）顯示卡片列表，桌面版顯示表格

- [ ] **Step 7: Commit**

```bash
git add src/components/ReminderCard.tsx src/pages/caregiver/reminders.tsx
git commit -m "feat(reminders): add mobile card view with ReminderCard component"
```

---

### Task 6: 照護者住民列表響應式調整

**Files:**
- Modify: `src/pages/caregiver/index.tsx`

**Interfaces:**
- Consumes: 無
- Produces: 更新後的住民列表頁面，含響應式間距

- [ ] **Step 1: 調整 Container 間距**

將：
```tsx
<Container maxWidth="lg" sx={{ py: 3 }}>
```

改為：
```tsx
<Container maxWidth="lg" sx={{ py: { xs: 2, sm: 3 } }}>
```

- [ ] **Step 2: 調整頁面標題區塊 margin**

將頁面標題的 `mb: 4` 改為響應式：

```tsx
<Box sx={{ mb: { xs: 2, sm: 4 } }}>
```

- [ ] **Step 3: 調整統計卡片 Grid spacing**

將：
```tsx
<Grid container spacing={2} sx={{ mb: 4 }}>
```

改為：
```tsx
<Grid container spacing={{ xs: 1.5, sm: 2 }} sx={{ mb: { xs: 2, sm: 4 } }}>
```

- [ ] **Step 4: 調整搜尋/篩選區塊 padding**

將 Paper 的 `p: 2.5` 改為：
```tsx
<Paper sx={{ p: { xs: 2, sm: 2.5 }, mb: { xs: 2, sm: 3 } }}>
```

- [ ] **Step 5: 調整住民卡片 Grid spacing**

將：
```tsx
<Grid container spacing={3}>
```

改為：
```tsx
<Grid container spacing={{ xs: 2, sm: 3 }}>
```

- [ ] **Step 6: 調整 CardContent 內距**

在住民卡片的 CardContent 加入響應式內距：
```tsx
<CardContent sx={{ flex: 1, pb: 1, p: { xs: 2, sm: 2 } }}>
```

- [ ] **Step 7: 執行開發伺服器確認**

確認：手機版間距縮小，內容更緊湊

- [ ] **Step 8: Commit**

```bash
git add src/pages/caregiver/index.tsx
git commit -m "fix(caregiver): improve responsive spacing for resident list"
```

---

### Task 7: 家屬儀表板響應式調整

**Files:**
- Modify: `src/pages/family/Dashboard.tsx`

**Interfaces:**
- Consumes: 無
- Produces: 更新後的家屬儀表板，含響應式間距

- [ ] **Step 1: 調整 Container 間距**

將：
```tsx
<Container maxWidth="lg" sx={{ py: 2 }}>
```

改為：
```tsx
<Container maxWidth="lg" sx={{ py: { xs: 1.5, sm: 2 } }}>
```

- [ ] **Step 2: 調整快速入口區塊**

將 Paper 的 `p: 2, mb: 3` 改為：
```tsx
<Paper sx={{ p: { xs: 1.5, sm: 2 }, mb: { xs: 2, sm: 3 }, bgcolor: 'primary.light' }}>
```

- [ ] **Step 3: 調整主要 Grid spacing**

將：
```tsx
<Grid container spacing={3}>
```

改為：
```tsx
<Grid container spacing={{ xs: 2, sm: 3 }}>
```

- [ ] **Step 4: 調整住民摘要卡片間距**

將 Card 的 `mb: 2` 改為：
```tsx
<Card key={resident.id} sx={{ mb: { xs: 1.5, sm: 2 } }}>
```

- [ ] **Step 5: 調整今日摘要 Paper 間距**

將：
```tsx
<Paper sx={{ p: 2, bgcolor: 'grey.50', mb: 2 }}>
```

改為：
```tsx
<Paper sx={{ p: { xs: 1.5, sm: 2 }, bgcolor: 'grey.50', mb: { xs: 1.5, sm: 2 } }}>
```

- [ ] **Step 6: 調整通知側欄 Paper 間距**

將：
```tsx
<Paper sx={{ p: 2 }}>
```

改為：
```tsx
<Paper sx={{ p: { xs: 1.5, sm: 2 } }}>
```

- [ ] **Step 7: 執行開發伺服器確認**

確認：手機版間距縮小，內容更緊湊

- [ ] **Step 8: Commit**

```bash
git add src/pages/family/Dashboard.tsx
git commit -m "fix(family): improve responsive spacing for dashboard"
```

---

### Task 8: 最終測試與清理

**Files:**
- 無新增/修改

**Interfaces:**
- 驗收所有功能

- [ ] **Step 1: 執行開發伺服器**

```bash
npm run dev
```

- [ ] **Step 2: 測試手機版 (使用瀏覽器開發者工具)**

- 設定螢幕寬度為 375px（iPhone SE）
- 確認底部導航顯示
- 確認「更多」按鈕展開 BottomSheet
- 確認提醒頁面顯示卡片列表
- 確認各頁面間距適當

- [ ] **Step 3: 測試桌面版**

- 設定螢幕寬度為 1200px
- 確認側邊 Drawer 顯示
- 確認底部導航隱藏
- 確認提醒頁面顯示表格
- 確認各頁面間距適當

- [ ] **Step 4: 測試切換角色**

- 登入不同角色（CAREGIVER, FAMILY, ADMIN）
- 確認底部導航項目正確切換

- [ ] **Step 5: 執行 lint 檢查**

```bash
npm run lint
```

修復任何 lint 錯誤

- [ ] **Step 6: 最終 Commit**

```bash
git add -A
git commit -m "test: verify responsive UI implementation across all viewports"
```

---

## 驗收 Checklist

- [ ] 手機版顯示底部導航，桌面版顯示側邊 Drawer
- [ ] 底部導航依角色顯示對應項目
- [ ] 「更多」按鈕可展開額外選項
- [ ] 提醒管理可選擇/顯示類別
- [ ] 手機版提醒顯示卡片列表
- [ ] 手機版卡片內容不溢出、文字有適當截斷
- [ ] 所有可點擊元素觸控區域 ≥ 44px
- [ ] 頁面間距在手機上適當
