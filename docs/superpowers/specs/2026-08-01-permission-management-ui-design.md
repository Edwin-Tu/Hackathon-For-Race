# 權限管理前端 UI 調整設計文件

**版本**：v1.0  
**日期**：2026-08-01  
**範圍**：僅前端 UI 調整（保留 mock 資料）  
**驗收標準**：展示可用

---

## 一、設計概述

本設計針對「智護聲盾」系統的權限管理相關前端頁面進行調整，對齊規劃書中 F07（身分驗證與角色授權）的定義，並優化使用者體驗。

### 調整範圍

1. **權限項目管理**（Roles.tsx）— 對齊 F07 規劃的權限分類
2. **政策編輯器**（PolicyEditor.tsx）— 整合權限與政策的關聯
3. **家屬授權流程**（Authorizations.tsx）— 新增授權模板
4. **登入介面**（login.tsx）— 移除員工/住民切換，住民入口移至 Demo 區

---

## 二、權限項目管理

### 2.1 調整後的權限清單

從原本的 6 大類 21 項權限，調整為 8 大類 25 項權限：

#### 住民資料

| 權限 key | 說明 |
|---------|------|
| `resident:read` | 查看住民基本資訊 |
| `resident:write` | 編輯住民資訊 |
| `resident:delete` | 刪除住民紀錄 |

#### 生活事件

| 權限 key | 說明 |
|---------|------|
| `event:read` | 查看生活事件 |
| `event:write` | 建立生活事件 |
| `event:correct` | 修正事件紀錄 |
| `event:delete` | 刪除事件紀錄 |

#### 提醒管理

| 權限 key | 說明 |
|---------|------|
| `reminder:read` | 查看提醒 |
| `reminder:write` | 建立提醒 |
| `reminder:delete` | 刪除提醒 |

#### 記憶管理

| 權限 key | 說明 |
|---------|------|
| `memory:read` | 查看 AI 記憶 |
| `memory:correct` | 修正錯誤記憶 |
| `memory:delete` | 刪除記憶 |

#### 語音互動

| 權限 key | 說明 |
|---------|------|
| `voice:interact` | 使用語音互動功能 |
| `voice:session` | 管理語音 Session |

#### 住民隔離（新增）

| 權限 key | 說明 |
|---------|------|
| `privacy:cross_resident` | 跨住民資料存取 |
| `privacy:sensitive` | 存取敏感個資 |

#### 安全管理（新增）

| 權限 key | 說明 |
|---------|------|
| `security:assets` | 管理受保護資產 |
| `security:policy` | 編輯安全政策 |
| `security:audit` | 查看稽核日誌 |
| `security:benchmark` | 執行安全測試 |

#### 系統管理

| 權限 key | 說明 |
|---------|------|
| `admin:users` | 管理使用者帳號 |
| `admin:roles` | 管理角色權限 |
| `admin:settings` | 系統設定 |
| `admin:escalate` | 接收升級處理 |

### 2.2 預設角色權限對照

| 角色 | 權限範圍 |
|-----|---------|
| ADMIN | 全部 25 項權限 |
| CAREGIVER | resident:read, event:*, reminder:*, memory:read, memory:correct |
| FAMILY | resident:read, event:read, reminder:read |
| RESIDENT | voice:interact, event:read, reminder:read |

### 2.3 UI 調整

- 更新 `allPermissions` 陣列，採用新的 8 大類分組
- 更新 `mockRoles` 中各角色的預設權限
- Accordion 分類名稱對應新的類別

---

## 三、政策編輯器

### 3.1 規則表格新增欄位

在政策規則表格中新增「受影響範圍」欄位，顯示該規則觸發時會限制的權限。

表格欄位順序：
1. 啟用
2. 規則名稱
3. 攻擊類別
4. 風險閾值
5. 動作
6. **受影響範圍**（新增）
7. 選項
8. 操作

### 3.2 編輯對話框新增欄位

在「攻擊類別」下方新增：
- **受影響權限**：多選欄位，可選擇權限 key
- **受影響角色**：多選欄位，可選擇角色

### 3.3 預設規則與權限對應

| 規則 | 受影響權限 |
|-----|-----------|
| 提示詞注入防護 | `*`（全部） |
| 跨住民存取防護 | `privacy:cross_resident` |
| 機密提取防護 | `security:assets`, `memory:read` |
| 編碼混淆偵測 | `*`（全部） |
| 角色偽裝防護 | `admin:*`, `privacy:*` |
| 工具濫用監控 | `event:write`, `reminder:write`, `memory:correct` |

### 3.4 資料結構調整

```typescript
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

---

## 四、家屬授權流程

### 4.1 授權模板

新增三個預設模板：

| 模板 | 預設勾選 | 說明 |
|-----|---------|------|
| 基本 | viewSummary, receiveNotifications | 僅看重點摘要 |
| 標準 | viewSummary, viewReminders, viewAlerts, receiveNotifications | 一般家屬使用 |
| 完整 | 全部勾選 | 需要詳細追蹤的家屬 |

### 4.2 UI 呈現

在編輯對話框的「授權範圍」區塊：
1. 標題下方新增 ToggleButtonGroup，包含「基本」「標準」「完整」三個選項
2. 預設選中「標準」
3. 選擇模板後自動套用勾選狀態
4. 使用者仍可手動調整個別權限

### 4.3 列表顯示優化

「授權範圍」欄位改為：
- 符合模板時顯示模板名稱（如「標準授權」）
- 自訂時顯示「自訂 (N/5)」

### 4.4 資料結構調整

```typescript
// 授權模板定義
const authTemplates = {
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
```

---

## 五、登入介面簡化

### 5.1 移除項目

- `loginMode` state 變數
- ToggleButtonGroup（員工登入/住民登入切換）
- 獨立的住民登入表單區塊

### 5.2 Demo 快速登入卡片

調整為 4 個卡片：

| 順序 | 帳號 | 角色 | 說明 | 顏色 |
|-----|------|------|------|------|
| 1 | admin | 系統管理者 | 管理使用者、角色與系統設定 | error |
| 2 | caregiver | 照護人員 | 照護住民、查看摘要與警示 | info |
| 3 | family | 家屬 | 查看住民狀況與通知 | success |
| 4 | resident | 住民（語音互動） | 直接進入語音互動介面 | warning |

### 5.3 住民卡片行為

點擊「住民」卡片後：
1. 展開 Collapse 區塊顯示 Persona 選擇
2. 顯示現有的 mockPersonas（王奶奶、李爺爺）
3. 點選後執行 `performResidentLogin(personaId)`

### 5.4 頁面結構

```
┌──────────────────────────────────────┐
│           🛡️ 智護聲盾                │
│   Smart Care Voice Agent ...        │
│                                     │
│   [帳號輸入框]                       │
│   [密碼輸入框]                       │
│   [登入按鈕]                         │
│                                     │
│   ─────── Demo 快速登入 ───────      │
│                                     │
│   [系統管理者] admin                 │
│   [照護人員] caregiver               │
│   [家屬] family                      │
│   [住民（語音互動）] resident        │
│      └→ 展開：[王奶奶] [李爺爺]      │
│                                     │
└──────────────────────────────────────┘
```

---

## 六、實作檔案清單

| 檔案 | 調整內容 |
|-----|---------|
| `src/pages/admin/Roles.tsx` | 更新權限清單與分類 |
| `src/pages/admin/PolicyEditor.tsx` | 新增受影響範圍欄位 |
| `src/pages/family/Authorizations.tsx` | 新增授權模板 |
| `src/pages/login.tsx` | 移除模式切換，整合住民入口 |

---

## 七、限制與備註

1. 本次調整僅涉及前端 UI，所有資料仍使用 mock
2. 後端 API 對接需另行規劃
3. 權限清單與 F07 規劃保持一致，如規劃有變動需同步更新
4. 住民登入仍為 Demo 模式，正式環境需連接機構帳號系統
