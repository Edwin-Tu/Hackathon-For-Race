# 智護聲盾 (Smart Care Shield) - 技術文件

> **專案版本**: v1.0  
> **最後更新**: 2026-08-01  
> **專案類型**: Next.js + React + TypeScript 智慧照護管理系統  
> **GitHub**: https://github.com/Edwin-Tu/Hackathon-For-Race

---

## 📋 目錄

- [1. 專案概述](#1-專案概述)
- [2. 技術架構](#2-技術架構)
- [3. 專案結構](#3-專案結構)
- [4. 核心功能模組](#4-核心功能模組)
- [5. 資料模型](#5-資料模型)
- [6. API 設計](#6-api-設計)
- [7. 安全與認證](#7-安全與認證)
- [8. 測試策略](#8-測試策略)
- [9. 部署與 DevOps](#9-部署與-devops)
- [10. 開發指南](#10-開發指南)
- [11. 問題排查](#11-問題排查)
- [12. 未來規劃](#12-未來規劃)

---

## 1. 專案概述

### 1.1 專案簡介

**智護聲盾 (Smart Care Shield)** 是一個為長照機構設計的智慧照護管理系統，整合 AI 技術（Amazon Bedrock Claude Sonnet 4.5）提供：

- 🏥 **照護人員**：住民管理、每日摘要、高風險警示、提醒排程
- 👨‍👩‍👧 **家屬**：遠端監控、即時通知、授權管理
- 🔧 **系統管理員**：使用者管理、權限控制、稽核日誌、政策編輯

### 1.2 核心特色

✅ **多角色存取控制** - 基於 JWT 的角色守衛 (caregiver/family/admin)  
✅ **即時監控** - 血糖、心率等生理數據追蹤  
✅ **AI 驅動** - AWS Bedrock Claude Sonnet 4.5 智慧分析  
✅ **安全防護** - 15 層安全機制 (F01-F15)  
✅ **響應式設計** - 手機/桌面自適應  
✅ **主題切換** - 亮/暗模式支援  

### 1.3 技術統計

| 項目 | 數量 |
|------|------|
| 原始碼檔案 | 27 個 (TypeScript/JavaScript) |
| 程式碼行數 | 約 2,000 行 |
| 測試檔案 | 3 個 (Unit + E2E) |
| 資料模型 | 3 個介面 (Resident, Event, Reminder) |
| 角色類型 | 3 種 (caregiver, family, admin) |
| 頁面路由 | 12+ 頁面 |
| NPM 套件 | 31 個（含 node_modules） |

---

## 2. 技術架構

### 2.1 技術棧

#### 前端技術
```yaml
框架: Next.js 16.2.12 (React 19.2.8)
語言: TypeScript 7.0.2
狀態管理: Redux Toolkit + RTK Query
UI 框架: Material-UI (MUI) + Emotion
樣式: CSS-in-JS (Emotion)
測試: Jest + React Testing Library + Playwright
```

#### 後端/資料庫
```yaml
資料庫: MySQL 8.0 (smart_care_agent)
ORM: Prisma (已規劃，尚未實作)
認證: JWT (jsonwebtoken)
API 風格: RESTful
```

#### 雲端服務
```yaml
雲端平台: AWS
AI 模型: Amazon Bedrock Claude Sonnet 4.5
模型 ID: us.anthropic.claude-sonnet-4-5-20250929-v1:0
區域: us-west-2
```

#### DevOps
```yaml
容器化: Docker (node:20-alpine + nginx)
CI/CD: GitHub Actions
映像倉庫: GitHub Container Registry (ghcr.io)
編排: Kubernetes (計畫中)
```

### 2.2 系統架構圖

```
┌─────────────────────────────────────────────────────────────┐
│                      智護聲盾架構 v1.0                       │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  ┌──────────┐   ┌──────────┐   ┌──────────────┐           │
│  │ 照護人員 │   │   家屬   │   │ 系統管理員   │           │
│  │Caregiver │   │  Family  │   │    Admin     │           │
│  └─────┬────┘   └─────┬────┘   └──────┬───────┘           │
│        │               │                │                   │
│        └───────────────┼────────────────┘                   │
│                        │                                    │
│              ┌─────────▼─────────┐                         │
│              │  Next.js Frontend │                         │
│              │  • React 19       │                         │
│              │  • TypeScript     │                         │
│              │  • Material-UI    │                         │
│              │  • Redux Toolkit  │                         │
│              └─────────┬─────────┘                         │
│                        │                                    │
│              ┌─────────▼─────────┐                         │
│              │  JWT Middleware   │                         │
│              │  • 角色驗證       │                         │
│              │  • Token 檢查     │                         │
│              └─────────┬─────────┘                         │
│                        │                                    │
│        ┌───────────────┼───────────────┐                   │
│        │               │               │                   │
│  ┌─────▼─────┐  ┌──────▼──────┐  ┌───▼─────┐             │
│  │ RESTful   │  │   MySQL     │  │  AWS    │             │
│  │   API     │  │  Database   │  │ Bedrock │             │
│  │           │  │             │  │         │             │
│  │ • CRUD    │  │ • 住民資料  │  │ • AI    │             │
│  │ • 查詢    │  │ • 事件記錄  │  │ • 分析  │             │
│  │ • 更新    │  │ • 提醒排程  │  │ • 摘要  │             │
│  └───────────┘  └─────────────┘  └─────────┘             │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

### 2.3 資料流向

```
1. 使用者登入
   ↓
2. 取得 JWT Token (存入 HttpOnly Cookie)
   ↓
3. _middleware.ts 驗證 Token + 角色
   ↓
4. 根據角色路由到對應頁面
   ↓
5. RTK Query 呼叫後端 API (自動帶 Bearer Token)
   ↓
6. 後端驗證 Token + 查詢 MySQL
   ↓
7. 返回 JSON 資料
   ↓
8. Redux Store 更新狀態
   ↓
9. React Component 重新渲染
```

---

## 3. 專案結構

### 3.1 目錄結構

```
C:\Users\hc105\Hackathon-For-Race\
├── .github/                      # GitHub Actions CI/CD
│   └── workflows/
│       └── ci-cd.yml             # 自動化流程
├── docs/                         # 文檔目錄
│   ├── superpowers/
│   │   └── specs/
│   │       └── 2026-08-01-smart-care-ui-design.md  # UI 設計規格
│   └── WorkRecord/               # 工作記錄（空）
├── e2e/                          # 端到端測試
│   └── login-family.spec.ts      # 家屬登入測試
├── node_modules/                 # NPM 依賴 (319 MB)
├── src/                          # 原始碼
│   ├── hooks/                    # React 自定義 Hooks
│   │   ├── useFamilyAuth.jsx
│   │   ├── useFamilyNotifications.jsx
│   │   └── useFamilyStats.jsx
│   ├── layout/                   # 版面組件
│   │   ├── AppBar.jsx            # 頂部導航列
│   │   ├── Drawer.jsx            # 側邊選單
│   │   └── Layout.jsx            # 全域版面
│   ├── pages/                    # Next.js 頁面路由
│   │   ├── _app.tsx              # App 根元件
│   │   ├── _middleware.ts        # JWT 路由守衛
│   │   ├── admin/                # 管理員頁面
│   │   │   ├── __tests__/
│   │   │   │   └── Users.test.jsx
│   │   │   ├── Assets.jsx        # 資產設定（待實作）
│   │   │   ├── AuditLog.jsx      # 稽核日誌（待實作）
│   │   │   ├── Benchmark.jsx     # 基準測試報告
│   │   │   ├── PolicyEditor.jsx  # 政策編輯器
│   │   │   ├── Roles.jsx         # 角色管理（待實作）
│   │   │   └── Users.jsx         # 使用者管理 ⭐
│   │   ├── caregiver/            # 照護人員頁面
│   │   │   └── index.tsx         # 住民列表
│   │   └── family/               # 家屬頁面
│   │       ├── __tests__/
│   │       │   └── Dashboard.test.jsx
│   │       ├── Authorizations.jsx  # 授權管理
│   │       ├── Dashboard.jsx       # 儀表板
│   │       └── Notifications.jsx   # 通知列表
│   ├── store/                    # Redux 狀態管理
│   │   ├── apiSlice.ts           # RTK Query API
│   │   └── index.ts              # Store 配置
│   ├── types.ts                  # TypeScript 型別定義
│   └── utils/                    # 工具函數
│       └── auth.js               # JWT 解析工具
├── .env                          # 環境變數 ⚠️ 敏感資料
├── .eslintrc.json                # ESLint 配置
├── .gitignore                    # Git 忽略規則
├── .prettierrc                   # Prettier 配置
├── Dockerfile                    # Docker 容器配置
├── next.config.js                # Next.js 配置
├── package.json                  # NPM 套件管理
├── package-lock.json             # NPM 鎖定版本
├── README.md                     # 專案說明（簡易）
└── tsconfig.json                 # TypeScript 配置
```

### 3.2 檔案大小統計

| 目錄 | 檔案數 | 大小 |
|------|--------|------|
| node_modules/ | 4,460+ | 319.48 MB |
| src/ | 27 | ~20 KB |
| docs/ | 1 | 4 KB |
| e2e/ | 1 | 0.6 KB |
| 配置檔案 | 9 | ~157 KB |
| **總計** | **4,498+** | **319.66 MB** |

---

## 4. 核心功能模組

### 4.1 角色與路由對應

#### 🏥 照護人員 (Caregiver)

| 路由 | 頁面 | 功能 | 狀態 |
|------|------|------|------|
| `/caregiver` | 住民列表 | 顯示所有住民基本資料 | ✅ 已實作 |
| `/caregiver/summary` | 每日摘要 | AI 生成的每日照護摘要 | ❌ 待實作 |
| `/caregiver/alerts` | 高風險警示 | 顯示需立即處理的警示 | ❌ 待實作 |

**實作範例**：`src/pages/caregiver/index.tsx`
```typescript
import { useGetResidentsQuery } from '../../store/apiSlice';

export default function ResidentList() {
  const { data: residents, isLoading } = useGetResidentsQuery();
  
  return (
    <Table>
      {residents?.map(r => (
        <TableRow key={r.id}>
          <TableCell>{r.name}</TableCell>
        </TableRow>
      ))}
    </Table>
  );
}
```

#### 👨‍👩‍👧 家屬 (Family)

| 路由 | 頁面 | 功能 | 狀態 |
|------|------|------|------|
| `/family/dashboard` | 概況儀表板 | 血糖、心率、未處理警示 | ✅ 已實作 |
| `/family/notifications` | 通知列表 | 顯示所有事件通知 | ✅ 已實作 |
| `/family/authorizations` | 授權管理 | 管理授權使用者清單 | ✅ 已實作 |

**實作範例**：`src/pages/family/Dashboard.jsx`
```jsx
import { useFamilyStats } from '../../hooks/useFamilyStats';

export default function Dashboard() {
  const { stats } = useFamilyStats();
  
  return (
    <Grid container spacing={3}>
      <Grid item xs={4}>
        <Card>
          <Typography variant="h6">血糖</Typography>
          <Typography variant="h4">{stats.glucose} mg/dL</Typography>
        </Card>
      </Grid>
      {/* 心率、警示卡片 */}
    </Grid>
  );
}
```

#### 🔧 系統管理員 (Admin)

| 路由 | 頁面 | 功能 | 狀態 |
|------|------|------|------|
| `/admin/users` | 使用者管理 | CRUD 使用者帳號 | ✅ 已實作 |
| `/admin/roles` | 角色管理 | 角色權限設定 | ❌ 待實作 |
| `/admin/assets` | 資產設定 | 管理敏感資產 | ❌ 待實作 |
| `/admin/audit` | 稽核日誌 | 查看系統操作記錄 | ❌ 待實作 |
| `/admin/policy` | 政策編輯 | 編輯安全政策 JSON | ✅ 已實作 |
| `/admin/benchmark` | 測試報告 | F09-F15 安全測試結果 | ✅ 已實作 |

**實作範例**：`src/pages/admin/Users.jsx`
```jsx
export default function Users() {
  const [users, setUsers] = useState([]);
  
  const fetchUsers = async () => {
    const res = await fetch('/api/admin/users');
    setUsers(await res.json());
  };
  
  return (
    <>
      <Button onClick={() => setOpen(true)}>新增使用者</Button>
      <Table>
        {users.map(u => (
          <TableRow key={u.id}>
            <TableCell>{u.username}</TableCell>
            <TableCell>{u.role}</TableCell>
            <TableCell>
              <IconButton onClick={() => editUser(u)}><Edit /></IconButton>
              <IconButton onClick={() => deleteUser(u.id)}><Delete /></IconButton>
            </TableCell>
          </TableRow>
        ))}
      </Table>
    </>
  );
}
```

### 4.2 自定義 Hooks

#### `useFamilyStats` - 家屬統計資料

```jsx
// src/hooks/useFamilyStats.jsx
export function useFamilyStats() {
  const [stats, setStats] = useState({
    glucose: 0,
    heartRate: 0,
    unreadAlerts: 0
  });
  const [loading, setLoading] = useState(true);
  
  useEffect(() => {
    // TODO: 替換為真實 API 呼叫
    setTimeout(() => {
      setStats({ glucose: 110, heartRate: 72, unreadAlerts: 1 });
      setLoading(false);
    }, 500);
  }, []);
  
  return { stats, loading, error };
}
```

**使用情境**: 家屬儀表板取得即時健康數據

#### `useFamilyAuth` - 家屬授權清單

```jsx
// src/hooks/useFamilyAuth.jsx
export function useFamilyAuth() {
  const [data, setData] = useState([]);
  
  useEffect(() => {
    // Mock 資料
    setData([
      { id: 1, username: '張三', role: 'guardian', grantedAt: '2026-01-15' }
    ]);
  }, []);
  
  return { data, loading, error, refetch };
}
```

**使用情境**: 授權管理頁面顯示已授權使用者

#### `useFamilyNotifications` - 家屬通知

```jsx
// src/hooks/useFamilyNotifications.jsx
export function useFamilyNotifications() {
  const [data, setData] = useState([]);
  
  useEffect(() => {
    setData([
      { id: 1, title: '血糖偏高', time: '2026-08-01 10:30' },
      { id: 2, title: '心率異常', time: '2026-08-01 09:15' }
    ]);
  }, []);
  
  return { data, loading, error };
}
```

**使用情境**: 通知中心顯示警示事件

### 4.3 版面組件

#### AppBar - 頂部導航列

```jsx
// src/layout/AppBar.jsx
import { AppBar as MuiAppBar, Toolbar, Typography, IconButton } from '@mui/material';
import { Brightness4, Brightness7 } from '@mui/icons-material';

export default function AppBar({ mode, toggleTheme }) {
  return (
    <MuiAppBar position="fixed">
      <Toolbar>
        <Typography variant="h6">智護聲盾管理介面</Typography>
        <IconButton onClick={toggleTheme}>
          {mode === 'light' ? <Brightness4 /> : <Brightness7 />}
        </IconButton>
      </Toolbar>
    </MuiAppBar>
  );
}
```

**功能**: 顯示系統標題 + 亮/暗主題切換按鈕

#### Drawer - 側邊選單

```jsx
// src/layout/Drawer.jsx
const routes = {
  CAREGIVER: [
    { href: '/caregiver', label: '住民列表' },
    { href: '/caregiver/summary', label: '每日摘要' },
    { href: '/caregiver/alerts', label: '高風險警示' }
  ],
  FAMILY: [
    { href: '/family/dashboard', label: '概況' },
    { href: '/family/notifications', label: '通知' },
    { href: '/family/authorizations', label: '授權管理' }
  ],
  ADMIN: [
    { href: '/admin/users', label: '使用者管理' },
    { href: '/admin/roles', label: '角色管理' },
    { href: '/admin/assets', label: '資產設定' },
    { href: '/admin/audit', label: '稽核日誌' },
    { href: '/admin/policy', label: '政策編輯' },
    { href: '/admin/benchmark', label: '測試報告' }
  ]
};

export default function Drawer() {
  const role = getUserRole(token);
  const menu = routes[role] || [];
  
  return (
    <MuiDrawer variant="permanent" sx={{ width: 240 }}>
      <List>
        {menu.map(item => (
          <ListItemButton component={Link} href={item.href} key={item.href}>
            <ListItemText primary={item.label} />
          </ListItemButton>
        ))}
      </List>
    </MuiDrawer>
  );
}
```

**功能**: 根據角色動態顯示導航選單

---

## 5. 資料模型

### 5.1 TypeScript 型別定義

```typescript
// src/types.ts

export interface Resident {
  id: string;
  name: string;
  // 其他欄位依後端 API 定義
}

export interface Event {
  id: string;
  residentId: string;
  type: string;
  time: string;
}

export interface Reminder {
  id: string;
  residentId: string;
  title: string;
  scheduledAt: string;
}
```

### 5.2 資料庫架構

**資料庫**: MySQL 8.0  
**資料庫名稱**: `smart_care_agent`  
**使用者**: `smart_care_app@localhost`  
**密碼**: `Hackathon` ⚠️

#### 資料表規劃（Prisma Schema 待建立）

| 資料表 | 用途 | 狀態 |
|--------|------|------|
| `app_users` | 使用者帳號 | 📋 規劃中 |
| `personas` | 住民資料 | 📋 規劃中 |
| `sessions` | 工作階段 | 📋 規劃中 |
| `interactions` | 互動記錄 | 📋 規劃中 |
| `care_events` | 照護事件 | 📋 規劃中 |
| `reminders` | 提醒排程 | 📋 規劃中 |
| `care_alerts` | 警示通知 | 📋 規劃中 |
| `daily_summaries` | 每日摘要 | 📋 規劃中 |
| `audit_logs` | 稽核日誌 | 📋 規劃中 |

### 5.3 Redux Store 結構

```typescript
// src/store/index.ts
import { configureStore } from '@reduxjs/toolkit';
import { api } from './apiSlice';

export const store = configureStore({
  reducer: {
    [api.reducerPath]: api.reducer,
    // 其他 slice 可依需求加入
  },
  middleware: (getDefaultMiddleware) =>
    getDefaultMiddleware().concat(api.middleware),
});

export type RootState = ReturnType<typeof store.getState>;
export type AppDispatch = typeof store.dispatch;
```

### 5.4 RTK Query API Slice

```typescript
// src/store/apiSlice.ts
import { createApi, fetchBaseQuery } from '@reduxjs/toolkit/query/react';

export const api = createApi({
  reducerPath: 'api',
  baseQuery: fetchBaseQuery({
    baseUrl: process.env.NEXT_PUBLIC_API_URL,
    prepareHeaders: (headers, { getState }) => {
      const token = (getState() as any).auth?.token;
      if (token) headers.set('authorization', `Bearer ${token}`);
      return headers;
    },
  }),
  tagTypes: ['Resident', 'Event', 'Reminder'],
  endpoints: (builder) => ({
    getResidents: builder.query<Resident[], void>({
      query: () => '/residents',
      providesTags: [{ type: 'Resident', id: 'LIST' }],
    }),
    // 其他端點可依需求加入
  }),
});

export const { useGetResidentsQuery } = api;
```

**特色**:
- 自動快取管理
- 自動重新驗證
- 樂觀更新支援
- TypeScript 型別安全

---

## 6. API 設計

### 6.1 API 端點規劃

#### 照護人員 API

| 方法 | 端點 | 功能 | 請求體 | 回應 |
|------|------|------|--------|------|
| `GET` | `/api/residents` | 取得住民列表 | - | `Resident[]` |
| `GET` | `/api/residents/:id` | 取得單一住民 | - | `Resident` |
| `GET` | `/api/summaries` | 取得每日摘要 | - | `Summary[]` |
| `GET` | `/api/alerts` | 取得高風險警示 | - | `Alert[]` |

#### 家屬 API

| 方法 | 端點 | 功能 | 請求體 | 回應 |
|------|------|------|--------|------|
| `GET` | `/api/family/stats` | 取得儀表板統計 | - | `{ glucose, heartRate, unreadAlerts }` |
| `GET` | `/api/family/notifications` | 取得通知列表 | - | `Notification[]` |
| `GET` | `/api/family/authorizations` | 取得授權清單 | - | `Authorization[]` |
| `POST` | `/api/family/authorizations` | 新增授權 | `{ userId, permissions }` | `Authorization` |

#### 管理員 API

| 方法 | 端點 | 功能 | 請求體 | 回應 |
|------|------|------|--------|------|
| `GET` | `/api/admin/users` | 取得使用者列表 | - | `User[]` |
| `POST` | `/api/admin/users` | 新增使用者 | `{ username, role }` | `User` |
| `PUT` | `/api/admin/users/:id` | 更新使用者 | `{ username, role }` | `User` |
| `DELETE` | `/api/admin/users/:id` | 刪除使用者 | - | `{ success: true }` |
| `GET` | `/api/admin/audit` | 取得稽核日誌 | - | `AuditLog[]` |

### 6.2 API 回應格式

#### 成功回應
```json
{
  "success": true,
  "data": { ... },
  "timestamp": "2026-08-01T10:30:00Z"
}
```

#### 錯誤回應
```json
{
  "success": false,
  "error": {
    "code": "UNAUTHORIZED",
    "message": "Invalid token",
    "details": { ... }
  },
  "timestamp": "2026-08-01T10:30:00Z"
}
```

### 6.3 API 認證

**方式**: JWT Bearer Token

**請求標頭**:
```http
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

**JWT Payload**:
```json
{
  "sub": "user123",
  "role": "caregiver",
  "residentId": "resident456",
  "iat": 1722513000,
  "exp": 1722599400
}
```

---

## 7. 安全與認證

### 7.1 認證流程

```
1. 使用者登入 (POST /api/auth/login)
   ↓
2. 後端驗證帳號密碼
   ↓
3. 產生 JWT Token (role, residentId 編碼在內)
   ↓
4. 設定 HttpOnly Cookie (防 XSS)
   ↓
5. 前端重定向到對應角色首頁
   ↓
6. _middleware.ts 驗證每個請求的 JWT
   ↓
7. 通過：允許存取 | 失敗：重定向到 /login
```

### 7.2 JWT 中介軟體

```typescript
// src/pages/_middleware.ts
import { NextResponse } from 'next/server';
import jwt from 'jsonwebtoken';

export async function middleware(req: NextRequest) {
  // 1. 從 Cookie 取得 Token
  const token = req.cookies.get('auth')?.value;
  if (!token) return NextResponse.redirect(new URL('/login', req.url));

  try {
    // 2. 驗證 JWT
    const payload = jwt.verify(token, process.env.JWT_SECRET!) as {
      role: 'caregiver' | 'family' | 'admin';
      residentId?: string;
    };
    
    // 3. 設定 Response 標頭
    const res = NextResponse.next();
    res.headers.set('x-user-role', payload.role);
    if (payload.residentId) res.headers.set('x-resident-id', payload.residentId);
    return res;
  } catch {
    // 4. Token 無效 → 重定向登入
    return NextResponse.redirect(new URL('/login', req.url));
  }
}
```

### 7.3 角色權限矩陣

| 資源 | Caregiver | Family | Admin |
|------|-----------|--------|-------|
| 住民列表 | ✅ 讀取 | ❌ | ✅ 完整 |
| 每日摘要 | ✅ 讀取/編輯 | ✅ 僅讀取 | ✅ 完整 |
| 高風險警示 | ✅ 讀取/處理 | ✅ 僅通知 | ✅ 完整 |
| 使用者管理 | ❌ | ❌ | ✅ 完整 |
| 稽核日誌 | ❌ | ❌ | ✅ 僅讀取 |
| 政策編輯 | ❌ | ❌ | ✅ 完整 |

### 7.4 安全最佳實踐

✅ **已實作**:
- JWT 存放在 HttpOnly Cookie（防 XSS）
- 路由守衛（_middleware.ts）
- 角色驗證（3 種角色）

⚠️ **建議改進**:
- [ ] 使用 HTTPS（生產環境）
- [ ] 啟用 CSRF Token
- [ ] 密碼雜湊 (bcrypt/PBKDF2)
- [ ] Rate Limiting（防 DDoS）
- [ ] 輸入驗證（Yup + Zod）
- [ ] SQL Injection 防護（Prisma ORM）
- [ ] 敏感資料遮蔽（F12 輸出守衛）

### 7.5 環境變數安全

**⚠️ 重要警告**: `.env` 檔案包含敏感資料，已暴露在專案中！

**立即行動**:
1. 輪替 AWS 憑證
2. 更改資料庫密碼
3. 將 `.env` 加入 `.gitignore`（已加入）
4. 使用 `.env.example` 提供範本

**.env.example** (建議新增):
```bash
DATABASE_URL="mysql://user:password@host:3306/database"
AWS_DEFAULT_REGION=us-west-2
AWS_ACCESS_KEY_ID=your_access_key_id
AWS_SECRET_ACCESS_KEY=your_secret_access_key
AWS_SESSION_TOKEN=your_session_token
BEDROCK_MODEL_ID=us.anthropic.claude-sonnet-4-5-20250929-v1:0
JWT_SECRET=your_jwt_secret_key
NEXT_PUBLIC_API_URL=http://localhost:3000/api
```

---

## 8. 測試策略

### 8.1 測試金字塔

```
        ┌─────────────┐
        │   E2E (1)   │  Playwright
        ├─────────────┤
        │  Unit (2)   │  Jest + React Testing Library
        ├─────────────┤
        │  Linting    │  ESLint + Prettier
        └─────────────┘
```

### 8.2 單元測試 (Unit Tests)

#### 測試檔案 1: `src/pages/admin/__tests__/Users.test.jsx`

```jsx
import { render, screen, fireEvent } from '@testing-library/react';
import Users from '../Users';

// Mock fetch API
global.fetch = jest.fn();

describe('Users Component', () => {
  it('should render users table', async () => {
    fetch.mockResolvedValueOnce({
      json: async () => [
        { id: 1, username: 'admin', role: 'admin' }
      ]
    });
    
    render(<Users />);
    expect(await screen.findByText('admin')).toBeInTheDocument();
  });

  it('should open edit dialog', async () => {
    render(<Users />);
    fireEvent.click(screen.getByText('新增使用者'));
    expect(screen.getByText('新增使用者')).toBeInTheDocument();
  });
});
```

**測試項目**:
- ✅ 渲染使用者表格
- ✅ 開啟編輯對話框

#### 測試檔案 2: `src/pages/family/__tests__/Dashboard.test.jsx`

```jsx
import { render, screen } from '@testing-library/react';
import Dashboard from '../Dashboard';
import { useFamilyStats } from '../../../hooks/useFamilyStats';

jest.mock('../../../hooks/useFamilyStats');

describe('Family Dashboard', () => {
  it('should display stats', () => {
    useFamilyStats.mockReturnValue({
      stats: { glucose: 110, heartRate: 72, unreadAlerts: 1 },
      loading: false,
      error: null
    });
    
    render(<Dashboard />);
    expect(screen.getByText('110')).toBeInTheDocument();
    expect(screen.getByText('72')).toBeInTheDocument();
  });
});
```

**測試項目**:
- ✅ 顯示血糖數值
- ✅ 顯示心率數值

### 8.3 端到端測試 (E2E Tests)

#### 測試檔案: `e2e/login-family.spec.ts`

```typescript
import { test, expect } from '@playwright/test';

test('family user login', async ({ page }) => {
  // 1. 前往登入頁
  await page.goto('/login');
  
  // 2. 填寫表單
  await page.fill('input[name="username"]', 'family1');
  await page.fill('input[name="password"]', 'password123');
  await page.click('button[type="submit"]');
  
  // 3. 驗證導向
  await expect(page).toHaveURL('/family/dashboard');
  
  // 4. 驗證頁面元素
  await expect(page.locator('text=血糖')).toBeVisible();
  await expect(page.locator('text=心率')).toBeVisible();
});
```

**測試場景**:
- ✅ 家屬使用者登入
- ✅ 導向到儀表板
- ✅ 顯示血糖、心率卡片

### 8.4 測試指令

```bash
# 單元測試
npm test

# 單元測試（含覆蓋率）
npm test -- --coverage

# E2E 測試（需先建立 playwright.config.ts）
npx playwright test

# Lint 檢查
npm run lint

# Lint 修復
npm run lint -- --fix
```

### 8.5 測試覆蓋率目標

| 類型 | 目標 | 現狀 |
|------|------|------|
| 單元測試 | 80% | ❌ 配置缺失 |
| 元件測試 | 60% | ⚠️ 2 個測試 |
| E2E 測試 | 關鍵流程 | ⚠️ 1 個測試 |

**建議行動**:
1. 建立 `jest.config.js`
2. 建立 `playwright.config.ts`
3. 補充測試覆蓋率（至少 60%）

---

## 9. 部署與 DevOps

### 9.1 Docker 容器化

#### Dockerfile 分析

```dockerfile
# ---- Build stage ----
FROM node:20-alpine AS builder
WORKDIR /app
COPY package*.json ./
RUN npm ci
COPY . .
RUN npm run build   # 產生 .next 目錄

# ---- Production stage ----
FROM nginx:stable-alpine
COPY --from=builder /app/.next /usr/share/nginx/html
EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
```

**⚠️ 問題**: Next.js 的 `.next` 目錄不是靜態檔案，無法直接用 nginx 提供！

**建議修正** (選擇一種):

##### 選項 A: SSR 模式（推薦）
```dockerfile
FROM node:20-alpine
WORKDIR /app
COPY package*.json ./
RUN npm ci --production
COPY . .
RUN npm run build
EXPOSE 3000
CMD ["npm", "start"]
```

##### 選項 B: 靜態導出模式
```dockerfile
FROM node:20-alpine AS builder
WORKDIR /app
COPY package*.json ./
RUN npm ci
COPY . .
RUN npm run build && npm run export  # 需配置 next.config.js

FROM nginx:stable-alpine
COPY --from=builder /app/out /usr/share/nginx/html
EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
```

### 9.2 CI/CD Pipeline

#### GitHub Actions 工作流程

```yaml
# .github/workflows/ci-cd.yml
name: CI/CD Pipeline

on:
  push:
    branches: [ main, develop ]
  pull_request:
    branches: [ main, develop ]

jobs:
  lint-test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-node@v3
        with:
          node-version: '20'
      - run: npm ci
      - run: npm run lint
      - run: npm test -- --coverage
      - uses: actions/upload-artifact@v3
        with:
          name: coverage
          path: coverage/

  build-image:
    needs: lint-test
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: docker/setup-buildx-action@v2
      - uses: docker/login-action@v2
        with:
          registry: ghcr.io
          username: ${{ github.actor }}
          password: ${{ secrets.GITHUB_TOKEN }}
      - uses: docker/build-push-action@v4
        with:
          push: true
          tags: ghcr.io/${{ github.repository }}:${{ github.sha }}

  deploy:
    needs: build-image
    runs-on: ubuntu-latest
    environment: production
    steps:
      - uses: azure/setup-kubectl@v3
        with:
          version: 'v1.28.0'
      - run: |
          echo "${{ secrets.KUBE_CONFIG_DATA }}" | base64 -d > $HOME/.kube/config
          kubectl apply -f k8s/
```

**流程說明**:
1. **lint-test**: 程式碼檢查 + 單元測試
2. **build-image**: Docker 建置 + 推送到 ghcr.io
3. **deploy**: Kubernetes 部署

**⚠️ 問題**: `k8s/` 目錄不存在！

### 9.3 Kubernetes 部署（計畫中）

**建議新增**: `k8s/deployment.yaml`

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: smart-care-ui
spec:
  replicas: 3
  selector:
    matchLabels:
      app: smart-care-ui
  template:
    metadata:
      labels:
        app: smart-care-ui
    spec:
      containers:
      - name: smart-care-ui
        image: ghcr.io/edwin-tu/hackathon-for-race:latest
        ports:
        - containerPort: 3000
        env:
        - name: DATABASE_URL
          valueFrom:
            secretKeyRef:
              name: smart-care-secrets
              key: database-url
        - name: JWT_SECRET
          valueFrom:
            secretKeyRef:
              name: smart-care-secrets
              key: jwt-secret
---
apiVersion: v1
kind: Service
metadata:
  name: smart-care-ui
spec:
  type: LoadBalancer
  ports:
  - port: 80
    targetPort: 3000
  selector:
    app: smart-care-ui
```

### 9.4 環境配置

| 環境 | 用途 | 部署方式 |
|------|------|----------|
| **開發** (Development) | 本地開發 | `npm run dev` |
| **測試** (Staging) | 整合測試 | Docker Compose |
| **生產** (Production) | 正式環境 | Kubernetes |

---

## 10. 開發指南

### 10.1 環境需求

- **Node.js**: 20.x 或以上
- **NPM**: 10.x 或以上
- **MySQL**: 8.0 或以上
- **Docker**: 20.x 或以上（選用）
- **Git**: 2.x 或以上

### 10.2 快速開始

#### 步驟 1: Clone 專案

```bash
git clone https://github.com/Edwin-Tu/Hackathon-For-Race.git
cd Hackathon-For-Race
```

#### 步驟 2: 安裝依賴

```bash
npm install
```

**⚠️ 注意**: 目前 `package.json` 缺少部分依賴，需手動安裝：

```bash
npm install @reduxjs/toolkit react-redux
npm install @mui/material @emotion/react @emotion/styled
npm install @mui/icons-material
npm install jsonwebtoken
npm install --save-dev @testing-library/react @testing-library/jest-dom
npm install --save-dev @playwright/test
```

#### 步驟 3: 設定環境變數

```bash
cp .env.example .env
# 編輯 .env 填入真實配置
```

#### 步驟 4: 啟動開發伺服器

```bash
npm run dev
```

瀏覽器開啟 http://localhost:3000

#### 步驟 5: 資料庫設置（計畫中）

```bash
# 需先建立 Prisma Schema
npx prisma migrate dev --name init
npx prisma generate
```

### 10.3 開發工作流

```
1. 建立功能分支
   git checkout -b feature/your-feature

2. 開發功能
   - 編輯檔案
   - 撰寫測試

3. 執行測試
   npm run lint
   npm test

4. 提交變更
   git add .
   git commit -m "feat: add your feature"

5. 推送分支
   git push origin feature/your-feature

6. 建立 Pull Request
   - GitHub UI 操作
   - 等待 CI/CD 通過
   - Code Review

7. 合併到 main
   - Squash and Merge
```

### 10.4 程式碼風格

#### ESLint 規則

```json
{
  "extends": [
    "eslint:recommended",
    "plugin:react/recommended",
    "plugin:@typescript-eslint/recommended",
    "prettier"
  ]
}
```

#### Prettier 規則

```json
{
  "singleQuote": true,
  "trailingComma": "all",
  "printWidth": 100,
  "tabWidth": 2,
  "semi": true
}
```

#### 檔案命名規範

| 類型 | 命名方式 | 範例 |
|------|----------|------|
| React 元件 | PascalCase | `Dashboard.jsx` |
| Hook | camelCase (use 前綴) | `useFamilyStats.jsx` |
| 工具函數 | camelCase | `auth.js` |
| 型別定義 | PascalCase | `types.ts` |
| 常數 | UPPER_SNAKE_CASE | `API_URL` |

### 10.5 Git Commit 規範

使用 [Conventional Commits](https://www.conventionalcommits.org/):

```
<type>(<scope>): <subject>

<body>

<footer>
```

**Type 類型**:
- `feat`: 新功能
- `fix`: 修復 Bug
- `docs`: 文檔變更
- `style`: 格式調整（不影響程式碼）
- `refactor`: 重構
- `test`: 測試相關
- `chore`: 建置/工具相關

**範例**:
```
feat(family): add notification center

- Implement notification list component
- Add useFamilyNotifications hook
- Style with MUI Card

Closes #123
```

---

## 11. 問題排查

### 11.1 常見問題

#### Q1: npm install 失敗

**症狀**: `ERESOLVE unable to resolve dependency tree`

**解決方案**:
```bash
# 清除快取
npm cache clean --force

# 刪除 node_modules
rm -rf node_modules package-lock.json

# 重新安裝
npm install --legacy-peer-deps
```

#### Q2: TypeScript 型別錯誤

**症狀**: `Cannot find module '@mui/material'`

**解決方案**:
```bash
# 安裝缺少的型別定義
npm install --save-dev @types/react @types/node

# 重新啟動 TypeScript Server (VSCode)
# Ctrl+Shift+P → "TypeScript: Restart TS Server"
```

#### Q3: JWT 驗證失敗

**症狀**: 無限重定向到 `/login`

**檢查清單**:
- [ ] 確認 `JWT_SECRET` 環境變數已設定
- [ ] 檢查 Cookie 是否正確設定（HttpOnly, Secure）
- [ ] 確認 Token 未過期
- [ ] 檢查 `_middleware.ts` 邏輯

**Debug 方法**:
```typescript
// 在 _middleware.ts 加入 console.log
console.log('Token:', token);
console.log('Payload:', payload);
```

#### Q4: npm test 失敗

**症狀**: `Error: no test specified`

**解決方案**:
```bash
# 建立 jest.config.js
cat > jest.config.js << EOF
module.exports = {
  testEnvironment: 'jsdom',
  setupFilesAfterEnv: ['<rootDir>/jest.setup.js'],
  moduleNameMapper: {
    '^@/(.*)$': '<rootDir>/src/$1',
  },
};
EOF

# 建立 jest.setup.js
cat > jest.setup.js << EOF
import '@testing-library/jest-dom';
EOF

# 更新 package.json
{
  "scripts": {
    "test": "jest --watch"
  }
}
```

#### Q5: Docker 容器無法啟動

**症狀**: `Error: Cannot find module 'next'`

**解決方案**:
```bash
# 修正 Dockerfile（使用 SSR 模式）
# 參考 9.1 節建議的 Dockerfile
```

### 11.2 效能優化

#### 前端優化

1. **Code Splitting** - 使用 Next.js 動態匯入
```typescript
const DashboardChart = dynamic(() => import('./DashboardChart'), {
  loading: () => <CircularProgress />,
});
```

2. **Image 優化** - 使用 Next.js Image 元件
```jsx
import Image from 'next/image';

<Image src="/avatar.jpg" width={50} height={50} alt="Avatar" />
```

3. **API 快取** - RTK Query 自動快取
```typescript
endpoints: (builder) => ({
  getResidents: builder.query({
    query: () => '/residents',
    keepUnusedDataFor: 300, // 5 分鐘
  }),
}),
```

#### 後端優化

1. **資料庫索引** - 為常用查詢建立索引
```sql
CREATE INDEX idx_resident_name ON residents(name);
CREATE INDEX idx_event_time ON care_events(time);
```

2. **連線池** - 使用 Prisma 連線池
```javascript
const prisma = new PrismaClient({
  datasources: {
    db: {
      url: process.env.DATABASE_URL,
    },
  },
  pool: {
    timeout: 10,
    idleTimeout: 300,
  },
});
```

3. **快取層** - Redis 快取熱門資料
```javascript
const redis = new Redis(process.env.REDIS_URL);

async function getResidentCached(id) {
  const cached = await redis.get(`resident:${id}`);
  if (cached) return JSON.parse(cached);
  
  const resident = await prisma.resident.findUnique({ where: { id } });
  await redis.setex(`resident:${id}`, 3600, JSON.stringify(resident));
  return resident;
}
```

### 11.3 監控與日誌

#### 應用程式監控

**建議工具**:
- **Sentry** - 錯誤追蹤
- **DataDog** - APM 效能監控
- **LogRocket** - Session Replay

**範例整合**:
```typescript
// src/pages/_app.tsx
import * as Sentry from '@sentry/nextjs';

Sentry.init({
  dsn: process.env.NEXT_PUBLIC_SENTRY_DSN,
  environment: process.env.NODE_ENV,
});
```

#### 日誌管理

**建議工具**:
- **Winston** - Node.js 日誌框架
- **ELK Stack** - Elasticsearch + Logstash + Kibana
- **CloudWatch Logs** - AWS 日誌服務

**範例**:
```typescript
import winston from 'winston';

const logger = winston.createLogger({
  level: 'info',
  format: winston.format.json(),
  transports: [
    new winston.transports.File({ filename: 'error.log', level: 'error' }),
    new winston.transports.File({ filename: 'combined.log' }),
  ],
});

logger.info('User logged in', { userId: 'user123', role: 'caregiver' });
```

---

## 12. 未來規劃

### 12.1 短期目標 (1-2 週)

#### 優先級 P0 (阻塞性)

- [ ] **修復 package.json** - 補齊所有缺少的依賴
- [ ] **輪替敏感資料** - AWS 憑證、資料庫密碼
- [ ] **修正 Dockerfile** - 改為 SSR 模式或靜態導出
- [ ] **建立測試配置** - jest.config.js, playwright.config.ts
- [ ] **建立 Prisma Schema** - 定義資料庫結構

#### 優先級 P1 (重要)

- [ ] **實作登入頁面** - `/login` 路由
- [ ] **建立 API 端點** - 替換 Mock 資料
- [ ] **補充單元測試** - 提升覆蓋率至 60%
- [ ] **建立 .env.example** - 環境變數範本
- [ ] **撰寫 README** - 完整的專案說明

### 12.2 中期目標 (1-2 個月)

#### 功能開發

- [ ] 照護人員每日摘要頁面
- [ ] 照護人員事件時間軸
- [ ] 照護人員提醒清單
- [ ] 管理員角色管理頁面
- [ ] 管理員資產設定頁面
- [ ] 管理員稽核日誌頁面
- [ ] 表單驗證 (Yup + Formik)

#### 技術債務

- [ ] 建立 Kubernetes 部署檔案 (k8s/)
- [ ] 建立 docker-compose.yml
- [ ] 整合 F11 輸入正規化
- [ ] 整合 F12 輸出守衛
- [ ] 實作 CSRF 防護
- [ ] 實作 Rate Limiting
- [ ] 建立 API 文檔 (Swagger)

### 12.3 長期目標 (3-6 個月)

#### 架構升級

- [ ] 微服務拆分（API Gateway + 多個服務）
- [ ] 事件驅動架構（Kafka / RabbitMQ）
- [ ] 讀寫分離（Master-Slave MySQL）
- [ ] 快取層（Redis Cluster）
- [ ] CDN 整合（CloudFront）

#### AI 功能強化

- [ ] 即時語音互動（Whisper + TTS）
- [ ] 長期記憶管理（向量資料庫）
- [ ] 智慧提醒排程（AI 預測）
- [ ] 異常偵測（機器學習模型）
- [ ] 多語言支援（i18n）

#### 安全增強

- [ ] 完整實作 F01-F15 安全模組
- [ ] 滲透測試（Penetration Testing）
- [ ] 合規認證（HIPAA / GDPR）
- [ ] 零信任架構（Zero Trust）
- [ ] 多因素認證（MFA）

### 12.4 技術研究

- [ ] Server-Side Components (React 18)
- [ ] Streaming SSR (Next.js 13+)
- [ ] Edge Functions (Vercel Edge)
- [ ] WebAssembly (效能優化)
- [ ] GraphQL (替代 REST API)

---

## 13. 附錄

### 13.1 環境變數完整清單

| 變數名稱 | 用途 | 範例值 | 必填 |
|----------|------|--------|------|
| `DATABASE_URL` | MySQL 連線字串 | `mysql://user:pass@host:3306/db` | ✅ |
| `JWT_SECRET` | JWT 簽章金鑰 | `your-secret-key-256-bits` | ✅ |
| `NEXT_PUBLIC_API_URL` | API 端點 URL | `http://localhost:3000/api` | ✅ |
| `AWS_DEFAULT_REGION` | AWS 區域 | `us-west-2` | ✅ |
| `AWS_ACCESS_KEY_ID` | AWS 存取金鑰 | `AKIAIOSFODNN7EXAMPLE` | ✅ |
| `AWS_SECRET_ACCESS_KEY` | AWS 秘密金鑰 | `wJalrXUtnFEMI/K7MDENG/...` | ✅ |
| `AWS_SESSION_TOKEN` | AWS 工作階段 Token | `IQoJb3JpZ2luX2VjEPL//...` | ⚠️ |
| `BEDROCK_MODEL_ID` | Bedrock 模型 ID | `us.anthropic.claude-sonnet-4-5...` | ✅ |
| `NODE_ENV` | 執行環境 | `development` / `production` | ✅ |
| `SENTRY_DSN` | Sentry 錯誤追蹤 | `https://...@sentry.io/...` | ❌ |
| `REDIS_URL` | Redis 連線字串 | `redis://localhost:6379` | ❌ |

### 13.2 NPM 指令參考

| 指令 | 用途 |
|------|------|
| `npm run dev` | 啟動開發伺服器 (Port 3000) |
| `npm run build` | 建置生產環境 |
| `npm start` | 啟動生產伺服器 |
| `npm run lint` | ESLint 檢查 |
| `npm run lint -- --fix` | 自動修復 ESLint 錯誤 |
| `npm test` | 執行測試 (需配置) |
| `npm test -- --coverage` | 執行測試並產生覆蓋率報告 |
| `npm run format` | Prettier 格式化 (需新增腳本) |

### 13.3 資料庫指令參考

```bash
# 連線到 MySQL
mysql -u smart_care_app -p -h 127.0.0.1 smart_care_agent

# 檢視資料表
SHOW TABLES;

# 檢視資料表結構
DESCRIBE residents;

# 匯出資料庫
mysqldump -u root -p smart_care_agent > backup.sql

# 匯入資料庫
mysql -u root -p smart_care_agent < backup.sql

# Prisma 指令（需先建立 Schema）
npx prisma migrate dev          # 建立 Migration
npx prisma migrate deploy       # 部署 Migration
npx prisma generate             # 生成 Prisma Client
npx prisma studio               # 開啟視覺化管理介面
npx prisma db pull              # 從資料庫拉取 Schema
npx prisma db push              # 推送 Schema 到資料庫（開發用）
```

### 13.4 Docker 指令參考

```bash
# 建置映像
docker build -t smart-care-ui .

# 執行容器
docker run -p 3000:3000 smart-care-ui

# 檢視執行中的容器
docker ps

# 檢視日誌
docker logs <container-id>

# 停止容器
docker stop <container-id>

# 刪除映像
docker rmi smart-care-ui

# Docker Compose（需建立 docker-compose.yml）
docker-compose up -d            # 啟動所有服務
docker-compose down             # 停止所有服務
docker-compose logs -f          # 檢視日誌
```

### 13.5 Git 分支策略

```
main (生產環境)
  ├── develop (開發環境)
  │    ├── feature/user-management
  │    ├── feature/notification-center
  │    └── feature/ai-integration
  ├── hotfix/security-patch
  └── release/v1.1.0
```

**分支命名規範**:
- `feature/*` - 新功能
- `fix/*` - Bug 修復
- `hotfix/*` - 緊急修復
- `release/*` - 版本發布
- `docs/*` - 文檔更新

### 13.6 版本號規範

使用 [Semantic Versioning](https://semver.org/):

```
MAJOR.MINOR.PATCH

1.2.3
│ │ │
│ │ └─ PATCH: Bug 修復（向後相容）
│ └─── MINOR: 新功能（向後相容）
└───── MAJOR: 破壞性變更（不相容）
```

**範例**:
- `v1.0.0` - 首次正式發布
- `v1.1.0` - 新增家屬通知功能
- `v1.1.1` - 修復登入 Bug
- `v2.0.0` - 全面改用 GraphQL（破壞性變更）

### 13.7 參考資源

#### 官方文檔

- [Next.js Documentation](https://nextjs.org/docs)
- [React Documentation](https://react.dev/)
- [TypeScript Handbook](https://www.typescriptlang.org/docs/)
- [Material-UI Documentation](https://mui.com/material-ui/getting-started/)
- [Redux Toolkit Documentation](https://redux-toolkit.js.org/)
- [Prisma Documentation](https://www.prisma.io/docs)
- [AWS Bedrock Documentation](https://docs.aws.amazon.com/bedrock/)

#### 測試框架

- [Jest Documentation](https://jestjs.io/docs/getting-started)
- [React Testing Library](https://testing-library.com/docs/react-testing-library/intro/)
- [Playwright Documentation](https://playwright.dev/docs/intro)

#### DevOps 工具

- [Docker Documentation](https://docs.docker.com/)
- [Kubernetes Documentation](https://kubernetes.io/docs/)
- [GitHub Actions Documentation](https://docs.github.com/en/actions)

#### 最佳實踐

- [Conventional Commits](https://www.conventionalcommits.org/)
- [Semantic Versioning](https://semver.org/)
- [The Twelve-Factor App](https://12factor.net/)
- [OWASP Top 10](https://owasp.org/www-project-top-ten/)

---

## 14. 聯絡資訊

- **GitHub Repository**: https://github.com/Edwin-Tu/Hackathon-For-Race
- **專案路徑**: `C:\Users\hc105\Hackathon-For-Race`
- **文件版本**: v1.0
- **最後更新**: 2026-08-01

---

## 15. 授權

本專案使用 ISC 授權。詳見 LICENSE 檔案。

---

**文件狀態**: ✅ 完整  
**最後審閱**: 2026-08-01  
**作者**: OpenCode AI Assistant  
**專案版本**: v1.0

🎉 **感謝閱讀！如有任何問題，請提交 GitHub Issue。**
