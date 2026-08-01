# Source Code Directory

此目錄包含所有前端原始碼。

## 📁 目錄結構

```
src/
├── components/          # React 元件
├── pages/               # Next.js 頁面路由
├── hooks/               # 自定義 React Hooks
├── store/               # Redux 狀態管理
├── types/               # TypeScript 型別定義
├── utils/               # 工具函數
├── theme/               # MUI 主題配置
├── context/             # React Context
├── layout/              # 版面組件
├── middleware.ts        # Next.js 中介軟體
└── __tests__/           # 測試檔案
```

## 📦 主要模組說明

### Components (元件)

可重用的 React 元件庫。

**命名規範**:
- 元件檔案使用 PascalCase: `Button.tsx`
- 樣式檔案（如需要）: `Button.module.css`
- 測試檔案: `Button.test.tsx`

**結構建議**:
```
components/
├── common/              # 通用元件
│   ├── Button/
│   ├── Input/
│   └── Card/
├── layout/              # 版面元件
│   ├── Header/
│   ├── Footer/
│   └── Sidebar/
└── features/            # 功能特定元件
    ├── caregiver/
    ├── family/
    └── admin/
```

### Pages (頁面)

Next.js 頁面路由，對應 URL 路徑。

**路由結構**:
- `/pages/index.tsx` → `/`
- `/pages/login.tsx` → `/login`
- `/pages/caregiver/index.tsx` → `/caregiver`
- `/pages/api/health.ts` → `/api/health`

**已實現頁面** (27個):

| 路由 | 檔案 | 說明 |
|------|------|------|
| `/` | `index.tsx` | 首頁 |
| `/login` | `login.tsx` | 登入頁面 |
| `/caregiver` | `caregiver/index.tsx` | 照護人員首頁 |
| `/caregiver/summary` | `caregiver/summary.tsx` | 每日摘要 |
| `/caregiver/alerts` | `caregiver/alerts.tsx` | 高風險警示 |
| `/caregiver/reminders` | `caregiver/reminders.tsx` | 提醒排程 |
| `/family/Dashboard` | `family/Dashboard.tsx` | 家屬儀表板 |
| `/family/Notifications` | `family/Notifications.tsx` | 家屬通知 |
| `/admin/Users` | `admin/Users.tsx` | 使用者管理 |
| `/api/health` | `api/health.ts` | 健康檢查 API |

### Hooks (自定義 Hooks)

可重用的 React Hooks。

**命名規範**: 使用 `use` 前綴，例如 `useAuth.ts`

**常用 Hooks**:
```typescript
// 認證
useAuth()         // 使用者認證狀態
usePermissions()  // 權限檢查

// 資料獲取
useResidents()    // 住民資料
useEvents()       // 事件資料

// UI 狀態
useModal()        // Modal 控制
useToast()        // 通知訊息
```

### Store (狀態管理)

Redux Toolkit 狀態管理。

**結構**:
```
store/
├── slices/              # Redux Slices
│   ├── authSlice.ts
│   ├── residentsSlice.ts
│   └── uiSlice.ts
├── api/                 # RTK Query API
│   └── apiSlice.ts
└── store.ts             # Store 配置
```

### Types (型別定義)

TypeScript 型別和介面定義。

**命名規範**:
- Interface 使用 PascalCase: `User`, `Resident`
- Type Alias 使用 PascalCase: `UserRole`, `EventType`
- 檔案名稱使用 camelCase: `user.ts`, `resident.ts`

**範例**:
```typescript
// types/user.ts
export interface User {
  id: string;
  name: string;
  email: string;
  role: UserRole;
}

export type UserRole = 'admin' | 'caregiver' | 'family';
```

### Utils (工具函數)

純函數工具庫。

**分類**:
```
utils/
├── date.ts              # 日期處理
├── format.ts            # 格式化
├── validation.ts        # 驗證
├── storage.ts           # LocalStorage 操作
└── api.ts               # API 工具
```

### Theme (主題配置)

Material-UI 主題配置。

```
theme/
├── palette.ts           # 色彩配置
├── typography.ts        # 字型配置
├── components.ts        # 元件樣式覆寫
└── index.ts             # 主題導出
```

## 🎨 樣式規範

### 使用 Emotion (CSS-in-JS)

```tsx
import { styled } from '@mui/material/styles';

const StyledButton = styled('button')(({ theme }) => ({
  backgroundColor: theme.palette.primary.main,
  color: theme.palette.primary.contrastText,
}));
```

### 響應式設計

```tsx
const responsive = {
  mobile: '@media (max-width: 600px)',
  tablet: '@media (max-width: 960px)',
  desktop: '@media (min-width: 961px)',
};
```

## 📝 命名規範

### 檔案命名

- **元件**: PascalCase (`UserProfile.tsx`)
- **Hooks**: camelCase with `use` prefix (`useAuth.ts`)
- **Utils**: camelCase (`formatDate.ts`)
- **Types**: camelCase (`user.ts`)
- **常數**: UPPER_SNAKE_CASE (`API_ENDPOINTS.ts`)

### 變數命名

```typescript
// ✅ Good
const userName = 'John';
const isLoading = false;
const userList = [];

// ❌ Bad
const user_name = 'John';
const loading = false;
const users = [];  // 不明確
```

## 🧪 測試

### 單元測試

```tsx
// Button.test.tsx
import { render, screen } from '@testing-library/react';
import Button from './Button';

describe('Button', () => {
  it('renders correctly', () => {
    render(<Button>Click me</Button>);
    expect(screen.getByText('Click me')).toBeInTheDocument();
  });
});
```

### 測試位置

- 元件測試: `components/**/__tests__/`
- Hooks 測試: `hooks/**/__tests__/`
- Utils 測試: `utils/**/__tests__/`

## 📚 Import 規範

### 使用 Path Alias

```typescript
// ✅ Good
import { Button } from '@/components/Button';
import { useAuth } from '@/hooks/useAuth';
import { User } from '@/types/user';

// ❌ Bad
import { Button } from '../../../components/Button';
```

### Import 順序

```typescript
// 1. 外部套件
import React from 'react';
import { Box } from '@mui/material';

// 2. 內部模組
import { Button } from '@/components/Button';
import { useAuth } from '@/hooks/useAuth';

// 3. 型別
import type { User } from '@/types/user';

// 4. 樣式
import styles from './Component.module.css';
```

## 🔗 相關資源

- [Next.js 文檔](https://nextjs.org/docs)
- [React 文檔](https://react.dev)
- [TypeScript 文檔](https://www.typescriptlang.org/docs)
- [Material-UI 文檔](https://mui.com)
- [Redux Toolkit 文檔](https://redux-toolkit.js.org)

---

**最後更新**: 2026-08-01  
**維護者**: 開發團隊
