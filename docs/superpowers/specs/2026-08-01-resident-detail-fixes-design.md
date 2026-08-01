# 住民詳情頁修復設計

**日期**: 2026-08-01  
**範圍**: 前端 Bug 修復 + 功能擴充

---

## 問題摘要

| # | 問題 | 現象 | 根因 |
|---|------|------|------|
| 1 | 滑動條無法滑動 | 住民詳情頁的分頁內容區無法滾動 | Tab Panel 沒有設定 `overflow: auto` |
| 2 | 缺少席系資料 | 需要 Vitals、病史/用藥、生活方式、緊急聯絡等健康資料 | 目前只有 Persona 資料，缺乏健康面向 |
| 3 | 整頁不定期刷新 | 無規律整頁 reload | `isTokenExpired` 誤判 (秒/毫秒單位錯誤) |

---

## 修復設計

### 1. 分頁內容滾動修復

**修改檔案**: `src/pages/caregiver/resident.tsx`

**修改方式**: 在 Tab Panel 內容外層加入帶有 `maxHeight` 和 `overflow: auto` 的容器。

```tsx
{/* 分頁內容容器 */}
<Box sx={{ 
  maxHeight: 'calc(100vh - 350px)',
  overflow: 'auto',
  mt: 2 
}}>
  {tabValue === 0 && ( /* 個人資料 */ )}
  {tabValue === 1 && ( /* 健康資訊 */ )}
  {tabValue === 2 && ( /* 日常作息 */ )}
  {tabValue === 3 && ( /* 最近動態 */ )}
  {tabValue === 4 && ( /* Persona 設定 */ )}
</Box>
```

**預期效果**: 內容超出容器時出現捲軸，使用者可上下滾動。

---

### 2. 新增「健康資訊」Tab

**修改檔案**: `src/pages/caregiver/resident.tsx`

#### Tab 結構

現有: `個人資料` | `日常作息` | `最近動態` | `Persona 設定`

新增後: `個人資料` | `健康資訊` | `日常作息` | `最近動態` | `Persona 設定`

#### 資料模型

```typescript
interface HealthInfo {
  // 生理監測
  vitals: {
    bloodPressure?: string;    // 血壓
    bloodSugar?: number;       // 血糖 mg/dL
    temperature?: number;      // 體溫
    pulse?: number;            // 脈搏
    lastMeasuredAt?: Date;     // 最後量測時間
  };
  // 病史與用藥
  medicalHistory: {
    chronicConditions: string[];  // 慢性病
    allergies: string[];          // 過敏史
    currentMedications: string[]; // 目前用藥
  };
  // 生活方式
  lifestyle: {
    dietPreference?: string;      // 飲食偏好
    exerciseRoutine?: string;     // 運動習慣
    sleepPattern?: string;        // 睡眠模式
    specialNotes?: string;        // 特殊備註
  };
  // 緊急聯絡
  emergency: {
    contactName?: string;         // 緊急聯絡人
    contactPhone?: string;        // 聯絡電話
    insurance?: string;           // 保險資訊
    careNotes?: string;           // 照護注意事項
  };
}
```

#### UI 佈局

```
┌─────────────────────────────────────────────────────────────┐
│  健康資訊                                                    │
├─────────────────────────────────────────────────────────────┤
│  ┌─────────────────────┐  ┌─────────────────────┐           │
│  │ 💓 生理監測 (Vitals) │  │ 📋 病史與用藥       │           │
│  │  血壓: 125/80 mmHg  │  │  慢性病: 高血壓     │           │
│  │  血糖: 98 mg/dL     │  │  過敏史: 青黴素     │           │
│  │  體溫: 36.5°C       │  │  用藥: 降血壓藥     │           │
│  │  脈搏: 72 bpm       │  │                     │           │
│  └─────────────────────┘  └─────────────────────┘           │
│                                                              │
│  ┌─────────────────────┐  ┌─────────────────────┐           │
│  │ 🏃 生活方式         │  │ 🚨 緊急/行政資料    │           │
│  │  飲食: 低鈉飲食     │  │  緊急聯絡人: 王小明 │           │
│  │  運動: 每日散步30分 │  │  電話: 0912-345-678│           │
│  │  睡眠: 平均7小時    │  │  保險: 全民健保     │           │
│  └─────────────────────┘  └─────────────────────┘           │
└─────────────────────────────────────────────────────────────┘
```

#### Mock 資料

```typescript
const mockHealthInfo: Record<string, HealthInfo> = {
  p1: {
    vitals: {
      bloodPressure: '125/80 mmHg',
      bloodSugar: 98,
      temperature: 36.5,
      pulse: 72,
      lastMeasuredAt: new Date('2026-08-01T08:00:00'),
    },
    medicalHistory: {
      chronicConditions: ['高血壓', '輕度糖尿病'],
      allergies: ['青黴素'],
      currentMedications: ['降血壓藥 (每日早上)', '血糖控制藥 (每餐前)'],
    },
    lifestyle: {
      dietPreference: '低鈉、低糖飲食',
      exerciseRoutine: '每日散步 30 分鐘',
      sleepPattern: '平均 7 小時，偶有失眠',
      specialNotes: '喜歡溫熱的食物',
    },
    emergency: {
      contactName: '王小明 (兒子)',
      contactPhone: '0912-345-678',
      insurance: '全民健保 + 商業醫療險',
      careNotes: '行動需扶助，使用助行器',
    },
  },
  p2: {
    vitals: {
      bloodPressure: '130/85 mmHg',
      bloodSugar: 105,
      temperature: 36.3,
      pulse: 68,
      lastMeasuredAt: new Date('2026-08-01T08:30:00'),
    },
    medicalHistory: {
      chronicConditions: ['心臟病', '高血壓'],
      allergies: [],
      currentMedications: ['心臟藥物 (每日早晚)', '降血壓藥 (每日早上)'],
    },
    lifestyle: {
      dietPreference: '低脂飲食',
      exerciseRoutine: '室內輕度活動',
      sleepPattern: '平均 6 小時，午休 1 小時',
      specialNotes: '避免劇烈運動',
    },
    emergency: {
      contactName: '李小華 (女兒)',
      contactPhone: '0923-456-789',
      insurance: '全民健保',
      careNotes: '心臟病患者，需定期監測',
    },
  },
};
```

---

### 3. Session 過期誤判修復

**修改檔案**: `src/layout/Layout.tsx`

**問題根因**: JWT 的 `exp` 是秒級 Unix timestamp，但 `Date.now()` 回傳毫秒級。

**修復前**:
```typescript
function isTokenExpired(token: string | null): boolean {
  // ...
  return payload.exp < Date.now();  // 錯誤：單位不一致
}
```

**修復後**:
```typescript
function isTokenExpired(token: string | null): boolean {
  if (!token) return true;
  try {
    const tokenPart = token.split('.')[1];
    if (!tokenPart) return true;
    const payload = JSON.parse(atob(tokenPart));
    // 修正：將 Date.now() 轉為秒級
    return payload.exp < Math.floor(Date.now() / 1000);
  } catch {
    return true;
  }
}
```

**預期效果**: Token 過期判斷正確，不再誤導至登入頁。

---

## 影響範圍

| 檔案 | 變更類型 |
|------|----------|
| `src/pages/caregiver/resident.tsx` | 新增健康資訊 Tab、修復滾動 |
| `src/layout/Layout.tsx` | 修復 token 過期判斷 |

---

## 測試驗收標準

1. **滾動測試**: 在各分頁填入超出畫面的內容，確認可正常滾動
2. **健康資訊 Tab**: 切換至「健康資訊」Tab，確認四個區塊正確顯示
3. **Session 測試**: 登入後停留超過 1 分鐘，確認不再被誤導登出
