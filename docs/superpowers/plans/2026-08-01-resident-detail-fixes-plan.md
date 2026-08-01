# 住民詳情頁修復實作計畫

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 修復住民詳情頁的三個問題：Tab 內容無法滾動、缺少健康資訊 Tab、Session 過期誤判導致頁面刷新

**Architecture:** 修改 `resident.tsx` 新增滾動容器與健康資訊 Tab，修改 `Layout.tsx` 的 token 過期判斷邏輯（秒 vs 毫秒）

**Tech Stack:** Next.js, React 18, MUI v5, TypeScript

## Global Constraints

- 使用繁體中文進行 UI 文字與程式碼註解
- 遵循專案現有的 MUI 元件使用慣例
- 使用 mock 資料，不需要後端 API 整合

---

## File Structure

| 檔案 | 角色 | 變更類型 |
|------|------|----------|
| `src/pages/caregiver/resident.tsx` | 住民詳情頁主元件 | 修改 |
| `src/layout/Layout.tsx` | 全域 Layout，含 session 檢查 | 修改 |

---

### Task 1: 修復 Session 過期誤判

**Files:**
- Modify: `src/layout/Layout.tsx:14-24`

**Interfaces:**
- Consumes: 無
- Produces: 修正後的 `isTokenExpired(token: string | null): boolean` 函數

- [ ] **Step 1: 閱讀現有 isTokenExpired 函數**

開啟 `src/layout/Layout.tsx`，找到第 14-24 行的 `isTokenExpired` 函數：

```typescript
function isTokenExpired(token: string | null): boolean {
  if (!token) return true;
  try {
    const tokenPart = token.split('.')[1];
    if (!tokenPart) return true;
    const payload = JSON.parse(atob(tokenPart));
    return payload.exp < Date.now();  // 問題：exp 是秒，Date.now() 是毫秒
  } catch {
    return true;
  }
}
```

- [ ] **Step 2: 修正時間單位比較**

將 `return payload.exp < Date.now();` 修改為：

```typescript
// 修正：JWT exp 是秒級 Unix timestamp，Date.now() 是毫秒級
return payload.exp < Math.floor(Date.now() / 1000);
```

- [ ] **Step 3: 驗證修改**

啟動開發伺服器 (若尚未啟動)：
```bash
npm run dev
```

登入後在任一頁面停留超過 1 分鐘，確認不再被重導至登入頁。

- [ ] **Step 4: Commit**

```bash
git add src/layout/Layout.tsx
git commit -m "fix: correct JWT expiry check (seconds vs milliseconds)"
```

---

### Task 2: 新增 HealthInfo 資料模型與 Mock 資料

**Files:**
- Modify: `src/pages/caregiver/resident.tsx:42-112`

**Interfaces:**
- Consumes: 無
- Produces: 
  - `interface HealthInfo` 型別定義
  - `const mockHealthInfo: Record<string, HealthInfo>` mock 資料

- [ ] **Step 1: 新增 HealthInfo 介面定義**

在 `resident.tsx` 的 `ResidentStats` 介面定義後方（約第 65 行）新增：

```typescript
// 健康資訊類型
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

- [ ] **Step 2: 新增 Mock 健康資料**

在 `mockStats` 定義後方（約第 113 行）新增：

```typescript
// 模擬健康資訊資料
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

- [ ] **Step 3: 確認 TypeScript 編譯無錯誤**

執行：
```bash
npx tsc --noEmit
```

預期：無錯誤輸出

- [ ] **Step 4: Commit**

```bash
git add src/pages/caregiver/resident.tsx
git commit -m "feat(resident): add HealthInfo interface and mock data"
```

---

### Task 3: 新增健康資訊 Tab 與 UI 元件

**Files:**
- Modify: `src/pages/caregiver/resident.tsx:220-228` (Tabs 區域)
- Modify: `src/pages/caregiver/resident.tsx` (新增 Tab Panel)

**Interfaces:**
- Consumes: 
  - `HealthInfo` 介面
  - `mockHealthInfo` 資料
- Produces: 健康資訊 Tab UI (tabValue === 1)

- [ ] **Step 1: 新增 import 與取得健康資料**

在 imports 區域確認有以下 icon（若無則新增）：

```typescript
import ContactPhoneIcon from '@mui/icons-material/ContactPhone';
import LocalHospitalIcon from '@mui/icons-material/LocalHospital';
import MonitorHeartIcon from '@mui/icons-material/MonitorHeart';
import RestaurantMenuIcon from '@mui/icons-material/RestaurantMenu';
```

在 `ResidentDetail` 元件內，`currentStats` 下方新增：

```typescript
const currentHealthInfo = mockHealthInfo[selectedPersona];
```

- [ ] **Step 2: 修改 Tabs 加入「健康資訊」**

找到 Tabs 元件（約第 222-227 行），修改為：

```tsx
<Paper sx={{ mb: 2 }}>
  <Tabs value={tabValue} onChange={(_, v) => setTabValue(v)} variant="scrollable" scrollButtons="auto">
    <Tab label="個人資料" />
    <Tab label="健康資訊" />
    <Tab label="日常作息" />
    <Tab label="最近動態" />
    <Tab label="Persona 設定" />
  </Tabs>
</Paper>
```

- [ ] **Step 3: 調整現有 Tab Panel 的 tabValue 判斷**

由於新增了「健康資訊」在第二位，需要調整後續 Tab 的 index：
- `tabValue === 1` 改為 `tabValue === 2` (日常作息)
- `tabValue === 2` 改為 `tabValue === 3` (最近動態)
- `tabValue === 3` 改為 `tabValue === 4` (Persona 設定)

- [ ] **Step 4: 新增健康資訊 Tab Panel**

在 `{tabValue === 0 && (...)}` (個人資料) 之後，`{tabValue === 2 && (...)}` (日常作息) 之前，插入：

```tsx
{/* 健康資訊 */}
{tabValue === 1 && currentHealthInfo && (
  <Grid container spacing={3}>
    {/* 生理監測 */}
    <Grid size={{ xs: 12, md: 6 }}>
      <Card>
        <CardContent>
          <Typography variant="h6" gutterBottom>
            <MonitorHeartIcon sx={{ mr: 1, verticalAlign: 'middle' }} color="error" />
            生理監測
          </Typography>
          <List dense>
            <ListItem>
              <ListItemText primary="血壓" secondary={currentHealthInfo.vitals.bloodPressure || '無紀錄'} />
            </ListItem>
            <ListItem>
              <ListItemText primary="血糖" secondary={currentHealthInfo.vitals.bloodSugar ? `${currentHealthInfo.vitals.bloodSugar} mg/dL` : '無紀錄'} />
            </ListItem>
            <ListItem>
              <ListItemText primary="體溫" secondary={currentHealthInfo.vitals.temperature ? `${currentHealthInfo.vitals.temperature}°C` : '無紀錄'} />
            </ListItem>
            <ListItem>
              <ListItemText primary="脈搏" secondary={currentHealthInfo.vitals.pulse ? `${currentHealthInfo.vitals.pulse} bpm` : '無紀錄'} />
            </ListItem>
            <ListItem>
              <ListItemText
                primary="最後量測"
                secondary={currentHealthInfo.vitals.lastMeasuredAt?.toLocaleString('zh-TW') || '無紀錄'}
              />
            </ListItem>
          </List>
        </CardContent>
      </Card>
    </Grid>

    {/* 病史與用藥 */}
    <Grid size={{ xs: 12, md: 6 }}>
      <Card>
        <CardContent>
          <Typography variant="h6" gutterBottom>
            <LocalHospitalIcon sx={{ mr: 1, verticalAlign: 'middle' }} color="primary" />
            病史與用藥
          </Typography>
          <List dense>
            <ListItem>
              <ListItemText
                primary="慢性病"
                secondary={currentHealthInfo.medicalHistory.chronicConditions.length > 0
                  ? currentHealthInfo.medicalHistory.chronicConditions.join('、')
                  : '無'}
              />
            </ListItem>
            <ListItem>
              <ListItemText
                primary="過敏史"
                secondary={currentHealthInfo.medicalHistory.allergies.length > 0
                  ? currentHealthInfo.medicalHistory.allergies.join('、')
                  : '無'}
              />
            </ListItem>
            <ListItem>
              <ListItemText
                primary="目前用藥"
                secondary={currentHealthInfo.medicalHistory.currentMedications.length > 0
                  ? currentHealthInfo.medicalHistory.currentMedications.join('、')
                  : '無'}
              />
            </ListItem>
          </List>
        </CardContent>
      </Card>
    </Grid>

    {/* 生活方式 */}
    <Grid size={{ xs: 12, md: 6 }}>
      <Card>
        <CardContent>
          <Typography variant="h6" gutterBottom>
            <RestaurantMenuIcon sx={{ mr: 1, verticalAlign: 'middle' }} color="success" />
            生活方式
          </Typography>
          <List dense>
            <ListItem>
              <ListItemText primary="飲食偏好" secondary={currentHealthInfo.lifestyle.dietPreference || '無紀錄'} />
            </ListItem>
            <ListItem>
              <ListItemText primary="運動習慣" secondary={currentHealthInfo.lifestyle.exerciseRoutine || '無紀錄'} />
            </ListItem>
            <ListItem>
              <ListItemText primary="睡眠模式" secondary={currentHealthInfo.lifestyle.sleepPattern || '無紀錄'} />
            </ListItem>
            <ListItem>
              <ListItemText primary="特殊備註" secondary={currentHealthInfo.lifestyle.specialNotes || '無紀錄'} />
            </ListItem>
          </List>
        </CardContent>
      </Card>
    </Grid>

    {/* 緊急/行政資料 */}
    <Grid size={{ xs: 12, md: 6 }}>
      <Card>
        <CardContent>
          <Typography variant="h6" gutterBottom>
            <ContactPhoneIcon sx={{ mr: 1, verticalAlign: 'middle' }} color="warning" />
            緊急/行政資料
          </Typography>
          <List dense>
            <ListItem>
              <ListItemText primary="緊急聯絡人" secondary={currentHealthInfo.emergency.contactName || '無紀錄'} />
            </ListItem>
            <ListItem>
              <ListItemText primary="聯絡電話" secondary={currentHealthInfo.emergency.contactPhone || '無紀錄'} />
            </ListItem>
            <ListItem>
              <ListItemText primary="保險資訊" secondary={currentHealthInfo.emergency.insurance || '無紀錄'} />
            </ListItem>
            <ListItem>
              <ListItemText primary="照護注意事項" secondary={currentHealthInfo.emergency.careNotes || '無紀錄'} />
            </ListItem>
          </List>
        </CardContent>
      </Card>
    </Grid>
  </Grid>
)}
```

- [ ] **Step 5: 驗證頁面渲染**

開啟瀏覽器訪問住民詳情頁，確認：
1. Tab 列顯示五個分頁
2. 點選「健康資訊」Tab 顯示四個 Card
3. 切換住民後健康資訊隨之更新

- [ ] **Step 6: Commit**

```bash
git add src/pages/caregiver/resident.tsx
git commit -m "feat(resident): add health info tab with vitals, medical, lifestyle, emergency sections"
```

---

### Task 4: 修復 Tab Panel 滾動問題

**Files:**
- Modify: `src/pages/caregiver/resident.tsx:229-380` (Tab Panel 區域)

**Interfaces:**
- Consumes: 無
- Produces: 可滾動的 Tab Panel 容器

- [ ] **Step 1: 包裹 Tab Panel 內容**

找到 Tab Panel 開始的位置（Tabs Paper 之後），用一個 Box 包裹所有 Tab 內容：

```tsx
{/* 分頁內容容器 - 可滾動 */}
<Box sx={{ 
  maxHeight: 'calc(100vh - 350px)', 
  overflow: 'auto',
  mt: 2 
}}>
  {/* 個人資料 */}
  {tabValue === 0 && ( ... )}
  
  {/* 健康資訊 */}
  {tabValue === 1 && ( ... )}
  
  {/* 日常作息 */}
  {tabValue === 2 && ( ... )}
  
  {/* 最近動態 */}
  {tabValue === 3 && ( ... )}
  
  {/* Persona 設定 */}
  {tabValue === 4 && ( ... )}
</Box>
```

- [ ] **Step 2: 驗證滾動功能**

在瀏覽器中：
1. 縮小視窗高度
2. 切換至內容較多的分頁（如「健康資訊」）
3. 確認出現垂直捲軸且可正常滾動

- [ ] **Step 3: Commit**

```bash
git add src/pages/caregiver/resident.tsx
git commit -m "fix(resident): add scrollable container for tab panels"
```

---

### Task 5: 最終驗證與測試

**Files:**
- 無檔案變更，純驗證

**Interfaces:**
- Consumes: 所有前述 Task 的產出
- Produces: 確認三個問題皆已修復

- [ ] **Step 1: 驗證 Session 過期修復**

1. 登入系統
2. 停留在任一頁面超過 2 分鐘
3. 確認頁面不會自動刷新或重導

- [ ] **Step 2: 驗證健康資訊 Tab**

1. 進入住民詳情頁
2. 切換至「健康資訊」Tab
3. 確認四個區塊（生理監測、病史與用藥、生活方式、緊急/行政資料）正確顯示
4. 切換不同住民，確認資料隨之更新

- [ ] **Step 3: 驗證 Tab Panel 滾動**

1. 縮小瀏覽器視窗高度
2. 切換各分頁
3. 確認內容超出時可正常滾動

- [ ] **Step 4: TypeScript 編譯檢查**

```bash
npx tsc --noEmit
```

預期：無錯誤輸出

- [ ] **Step 5: 確認無 console 錯誤**

開啟瀏覽器 DevTools Console，操作住民詳情頁各功能，確認無 React 警告或錯誤。

---

## 完成標準

- [ ] Session 過期判斷正確，不再誤導登出
- [ ] 健康資訊 Tab 顯示四個區塊
- [ ] Tab Panel 內容可滾動
- [ ] TypeScript 編譯無錯誤
- [ ] 瀏覽器 Console 無錯誤
