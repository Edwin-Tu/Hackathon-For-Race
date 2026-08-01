# 響應式 UI 設計規格 — 手機端與電腦端優化

> 建立日期：2026-08-01  
> 狀態：待審閱

## 1. 概述

### 1.1 目標
針對「智護聲盾」系統進行手機端與電腦端的 UI 優化，採用 Mobile-First 策略，確保所有角色（住民、照護者、家屬、管理員）都能在手機上順暢操作。

### 1.2 範圍
1. **新增底部導航（Bottom Navigation）**：手機版取代側邊 Drawer
2. **提醒管理類別標籤**：新增用藥、健康狀況、回診等分類
3. **手機版排版修正**：修正卡片寬度、文字截斷、按鈕尺寸、間距等問題

### 1.3 技術基礎
- 框架：Next.js + React + MUI v9
- 斷點：沿用 MUI 預設（xs:0, sm:600, md:960, lg:1200, xl:1536）
- 策略：Mobile-First（手機為主、電腦為輔）

---

## 2. 底部導航（Bottom Navigation）

### 2.1 元件規格

**檔案位置**：`src/components/BottomNav.tsx`

**顯示條件**：
- 僅在 `xs` ~ `sm` 斷點（< 600px）顯示
- 登入頁面不顯示

**樣式**：
- 位置：`position: fixed, bottom: 0, left: 0, right: 0`
- 高度：56px
- z-index：高於內容，低於 Dialog
- 背景：使用 theme paper 背景色，帶輕微陰影

### 2.2 導航項目配置

| 角色 | 項目 1 | 項目 2 | 項目 3 | 項目 4 |
|------|--------|--------|--------|--------|
| RESIDENT | 語音互動 | — | — | — |
| CAREGIVER | 住民列表 | 每日摘要 | 提醒 | 更多 |
| FAMILY | 概況 | 通知 | 授權 | — |
| ADMIN | 用戶 | 角色 | 稽核 | 更多 |

**「更多」按鈕行為**：
- 點擊後展開 BottomSheet（使用 MUI Drawer anchor="bottom"）
- 顯示該角色其餘的導航項目

**徽章（Badge）**：
- 提醒項目：顯示待執行提醒數量
- 通知項目：顯示未讀通知數量
- 警示項目：顯示待處理警示數量

### 2.3 Layout 調整

**手機版**：
- 隱藏 permanent Drawer
- 隱藏 AppBar 漢堡選單按鈕
- Content 區域增加 `paddingBottom: 56px`（BottomNav 高度）

**桌面版**：
- 維持原有 Layout（Drawer + AppBar）
- 不顯示 BottomNav

### 2.4 資料結構

```typescript
interface BottomNavItem {
  key: string;
  label: string;
  icon: React.ReactNode;
  href: string;
  badge?: number;
}

interface BottomNavConfig {
  items: BottomNavItem[];      // 最多 4 個（含「更多」）
  moreItems?: BottomNavItem[]; // 「更多」展開後的項目
}
```

---

## 3. 提醒管理類別標籤

### 3.1 資料模型

**新增類別欄位**：

```typescript
type ReminderCategory = 'medication' | 'health' | 'appointment' | 'other';

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

### 3.2 類別配置

```typescript
const categoryConfig: Record<ReminderCategory, {
  label: string;
  icon: React.ComponentType;
  color: 'error' | 'success' | 'info' | 'default';
}> = {
  medication: { label: '用藥', icon: MedicationIcon, color: 'error' },
  health: { label: '健康狀況', icon: FavoriteIcon, color: 'success' },
  appointment: { label: '回診', icon: EventIcon, color: 'info' },
  other: { label: '其他', icon: MoreHorizIcon, color: 'default' },
};
```

### 3.3 UI 變更

**列表顯示**：
- 桌面版：Table 新增「類別」欄位
- 手機版：改用卡片列表，類別 Chip 顯示在標題旁

**新增/編輯對話框**：
- 新增類別下拉選單（Select）
- 位置：「提醒內容」之後、「重要性」之前
- 預設值：`other`

**篩選功能**：
- 在篩選區新增類別篩選下拉選單
- 支援「全部」選項

### 3.4 手機版卡片設計

```
┌─────────────────────────────┐
│ 💊 用藥        🔴 高優先     │
│ ─────────────────────────── │
│ 王奶奶                       │
│ 晚上六點服用降血壓藥          │
│ 📅 08/01 18:00   ✅ 已完成   │
│                 [✓] [✏️] [🗑️]│
└─────────────────────────────┘
```

- 類別與優先級在頂部顯示
- 住民名稱作為副標題
- 提醒內容為主要文字
- 時間與狀態在底部
- 操作按鈕靠右對齊

---

## 4. 手機版排版修正規範

### 4.1 全域間距規範

| 元素 | 桌面版 (md+) | 手機版 (xs) |
|------|--------------|-------------|
| Container padding-y | 24px (`py: 3`) | 16px (`py: 2`) |
| Container padding-x | 24px (`px: 3`) | 16px (`px: 2`) |
| Card Grid spacing | 24px (`spacing={3}`) | 16px (`spacing={2}`) |
| Paper 內距 | 20px (`p: 2.5`) | 16px (`p: 2`) |
| 頁面標題 margin-bottom | 32px (`mb: 4`) | 16px (`mb: 2`) |
| Section 間距 | 24px (`mb: 3`) | 16px (`mb: 2`) |

### 4.2 卡片寬度與內距

```tsx
// Grid 配置
<Grid container spacing={{ xs: 2, md: 3 }}>
  <Grid item xs={12} sm={6} md={4}>
    <Card>
      <CardContent sx={{ p: { xs: 2, sm: 2.5 }, pb: { xs: 1, sm: 1 } }}>
        {/* 內容 */}
      </CardContent>
    </Card>
  </Grid>
</Grid>
```

### 4.3 文字截斷處理

**單行截斷**：
```tsx
<Typography 
  noWrap
  sx={{ 
    overflow: 'hidden',
    textOverflow: 'ellipsis',
    maxWidth: { xs: '180px', sm: '100%' }
  }}
>
```

**多行截斷**：
```tsx
<Typography sx={{
  display: '-webkit-box',
  WebkitLineClamp: { xs: 2, sm: 3 },
  WebkitBoxOrient: 'vertical',
  overflow: 'hidden',
}}>
```

### 4.4 按鈕尺寸規範

**最小觸控區域**：44px × 44px（符合 WCAG 2.1 Level AA）

```tsx
// IconButton
<IconButton 
  size="small"
  sx={{ 
    minWidth: { xs: 44, sm: 'auto' },
    minHeight: { xs: 44, sm: 'auto' },
  }}
>

// Button
<Button 
  size="medium"  // 手機版避免使用 size="small"
  sx={{ 
    minHeight: { xs: 44, sm: 36 },
    px: { xs: 2, sm: 2.5 },
  }}
>
```

### 4.5 表格響應式處理

對於資料表格（如提醒列表、用戶列表），採用以下策略：

**方案 A：卡片化（推薦用於提醒、住民列表）**
- 手機版將 Table 改為卡片列表
- 使用 `useMediaQuery` 判斷顯示模式

**方案 B：水平捲動（用於複雜表格如稽核日誌）**
- 使用 `<Box sx={{ overflowX: 'auto' }}>`
- 固定關鍵欄位（如名稱）

**方案 C：隱藏次要欄位（用於簡單表格）**
- 使用 `display: { xs: 'none', sm: 'table-cell' }`

---

## 5. 需調整頁面清單

| 頁面路徑 | 主要問題 | 優先級 | 預計調整 |
|----------|----------|--------|----------|
| `src/layout/Layout.tsx` | 整合 BottomNav | 高 | 新增 BottomNav 元件引用 |
| `src/pages/caregiver/reminders.tsx` | Table 改卡片、新增類別 | 高 | 重構列表顯示、新增欄位 |
| `src/pages/caregiver/index.tsx` | 卡片內距、統計區塊擠壓 | 高 | 調整 Grid/CardContent 間距 |
| `src/pages/family/Dashboard.tsx` | Grid 間距、通知列表 | 高 | 調整響應式間距 |
| `src/pages/caregiver/alerts.tsx` | 同 index | 中 | 調整響應式間距 |
| `src/pages/caregiver/timeline.tsx` | 時間軸顯示 | 中 | 評估是否需重構 |
| `src/pages/admin/Users.tsx` | Table 響應式 | 低 | 加入水平捲動 |

---

## 6. 新增檔案清單

| 檔案路徑 | 用途 |
|----------|------|
| `src/components/BottomNav.tsx` | 底部導航元件 |
| `src/components/BottomNavSheet.tsx` | 「更多」展開的 BottomSheet |
| `src/components/ReminderCard.tsx` | 手機版提醒卡片元件（可選，抽取共用） |

---

## 7. 驗收標準

### 7.1 功能驗收
- [ ] 手機版顯示底部導航，桌面版顯示側邊 Drawer
- [ ] 底部導航依角色顯示對應項目
- [ ] 「更多」按鈕可展開額外選項
- [ ] 提醒管理可選擇/顯示/篩選類別
- [ ] 新增提醒時可指定類別

### 7.2 體驗驗收
- [ ] 手機版卡片內容不溢出、文字有適當截斷
- [ ] 所有可點擊元素觸控區域 ≥ 44px
- [ ] 頁面間距在手機上不顯得過於稀疏
- [ ] 切換頁面時底部導航正確高亮當前項目

### 7.3 相容性
- [ ] iOS Safari 正常顯示
- [ ] Android Chrome 正常顯示
- [ ] 桌面版功能不受影響

---

## 附錄：技術決策記錄

| 決策項目 | 選擇 | 理由 |
|----------|------|------|
| 導航方案 | Bottom Navigation | 符合手機操作習慣，單手可及 |
| 斷點策略 | MUI 預設斷點 | 減少自訂配置，與現有程式碼一致 |
| 提醒類別 | 固定選單 | 簡化實作，避免標籤混亂 |
| 表格響應式 | 卡片化 | 手機上卡片比表格更易閱讀 |
| 觸控尺寸 | 44px | 符合 WCAG 2.1 Level AA 標準 |
