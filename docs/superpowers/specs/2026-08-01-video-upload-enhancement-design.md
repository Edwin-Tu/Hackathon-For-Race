# 影片上傳功能增強設計規格

> 建立日期：2026-08-01  
> 狀態：已確認

## 1. 概述

### 1.1 功能目標
增強現有影片上傳功能，新增兩項核心需求：
1. **歷史紀錄顯示**：在上傳頁面下方顯示該住民的歷史影片列表
2. **跨頁面進度追蹤**：切換頁面再切回來時，持續顯示上傳/生成進度，不中斷

### 1.2 現有實作基礎
- `src/pages/family/VideoUpload.tsx` — 現有上傳頁面
- `src/store/videoApi.ts` — RTK Query API endpoints
- `src/types/video.ts` — 型別定義
- Lambda `generate-video` — 後端影片生成

---

## 2. 系統設計

### 2.1 架構變更

```
┌─────────────────────────────────────────────────────────────┐
│                      VideoUpload.tsx                         │
├─────────────────────────────────────────────────────────────┤
│  [選擇長者 Dropdown]                                         │
│                                                              │
│  ┌─ 上傳區 ─────────────────────────────────────────────┐   │
│  │  (idle/uploading/processing/completed/failed)        │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                              │
│  ┌─ 歷史影片列表 ─────────────────────────────────────────┐ │
│  │  • 影片縮圖 1 (COMPLETED) [日期]                       │ │
│  │  • 影片縮圖 2 (PROCESSING) 生成中...                   │ │
│  │  • 影片縮圖 3 (COMPLETED) [日期]                       │ │
│  └─────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
```

### 2.2 資料流

```
[使用者選擇長者]
       │
       ├─→ dispatch setActiveResident(residentId)
       │
       └─→ 呼叫 getHistory(residentId) 取得歷史列表

[使用者上傳圖片]
       │
       ├─→ 呼叫 getPresignedUrl → 上傳 S3
       │
       └─→ dispatch setActiveTask({ residentId, taskId })
              │
              └─→ 開始輪詢 getTaskStatus(taskId)

[切換頁面再回來]
       │
       └─→ 從 Redux 讀取 activeTask
              │
              ├─→ 若有 activeTask，自動恢復輪詢
              │
              └─→ 頁面顯示進行中狀態

[任務完成/失敗]
       │
       ├─→ dispatch clearActiveTask()
       │
       └─→ invalidate 歷史列表快取，觸發重新載入
```

---

## 3. Redux Store 設計

### 3.1 新增 videoSlice.ts

```ts
// src/store/videoSlice.ts
import { createSlice, PayloadAction } from '@reduxjs/toolkit';

interface ActiveTask {
  residentId: string;
  taskId: string;
}

interface VideoState {
  activeTask: ActiveTask | null;
}

const initialState: VideoState = {
  activeTask: null,
};

export const videoSlice = createSlice({
  name: 'video',
  initialState,
  reducers: {
    setActiveTask: (state, action: PayloadAction<ActiveTask>) => {
      state.activeTask = action.payload;
    },
    clearActiveTask: (state) => {
      state.activeTask = null;
    },
  },
});

export const { setActiveTask, clearActiveTask } = videoSlice.actions;
export default videoSlice.reducer;
```

### 3.2 Store 整合

在 `store/index.ts` 加入 videoSlice：

```ts
import videoReducer from './videoSlice';

export const store = configureStore({
  reducer: {
    // ...existing reducers
    video: videoReducer,
    [videoApi.reducerPath]: videoApi.reducer,
  },
});
```

---

## 4. API 設計

### 4.1 新增 API Endpoint

**GET /api/v1/video/residents/{residentId}/history**

取得指定住民的所有影片任務歷史。

**Request**:
```
GET /api/v1/video/residents/resident-001/history
Authorization: Bearer {token}
```

**Response**:
```json
{
  "tasks": [
    {
      "taskId": "task-uuid-1",
      "status": "COMPLETED",
      "videoUrl": "https://s3.../videos/.../output.mp4",
      "createdAt": 1722470400000
    },
    {
      "taskId": "task-uuid-2",
      "status": "PROCESSING",
      "videoUrl": null,
      "createdAt": 1722470500000
    },
    {
      "taskId": "task-uuid-3",
      "status": "FAILED",
      "videoUrl": null,
      "errorMessage": "影片生成失敗",
      "createdAt": 1722470600000
    }
  ]
}
```

### 4.2 RTK Query 擴充

```ts
// src/store/videoApi.ts 新增

// 取得住民歷史影片列表
getVideoHistory: builder.query<VideoHistoryResponse, string>({
  query: (residentId) => `/residents/${residentId}/history`,
  providesTags: (result, error, residentId) => [
    { type: 'VideoTask', id: `history-${residentId}` },
  ],
}),
```

---

## 5. 前端實作

### 5.1 VideoUpload.tsx 變更

**新增邏輯**：

1. **初始化時檢查 activeTask**：
   ```ts
   const activeTask = useSelector(selectActiveTask);
   
   useEffect(() => {
     if (activeTask) {
       // 恢復輪詢
       setResidentId(activeTask.residentId);
       setTaskId(activeTask.taskId);
       setStatus('processing');
     }
   }, []);
   ```

2. **上傳成功時設定 activeTask**：
   ```ts
   // 上傳成功後
   setTaskId(result.taskId);
   dispatch(setActiveTask({ residentId, taskId: result.taskId }));
   setStatus('processing');
   ```

3. **任務完成/失敗時清除**：
   ```ts
   useEffect(() => {
     if (taskStatus?.status === 'COMPLETED' || taskStatus?.status === 'FAILED') {
       dispatch(clearActiveTask());
     }
   }, [taskStatus]);
   ```

### 5.2 歷史列表元件

**新增 VideoHistoryList 元件**：

```tsx
// src/components/VideoHistoryList.tsx

interface VideoHistoryListProps {
  residentId: string;
}

export function VideoHistoryList({ residentId }: VideoHistoryListProps) {
  const { data, isLoading } = useGetVideoHistoryQuery(residentId, {
    skip: !residentId,
  });

  if (!residentId) return null;
  if (isLoading) return <Skeleton variant="rectangular" height={200} />;
  if (!data?.tasks?.length) return <Typography>尚無歷史紀錄</Typography>;

  return (
    <Box sx={{ mt: 3 }}>
      <Typography variant="h6" gutterBottom>歷史影片</Typography>
      <Grid container spacing={2}>
        {data.tasks.map((task) => (
          <Grid item xs={6} sm={4} key={task.taskId}>
            <VideoHistoryCard task={task} />
          </Grid>
        ))}
      </Grid>
    </Box>
  );
}
```

### 5.3 歷史卡片元件

```tsx
// src/components/VideoHistoryCard.tsx

function VideoHistoryCard({ task }: { task: VideoTask }) {
  const isCompleted = task.status === 'COMPLETED';
  const isProcessing = task.status === 'PROCESSING';
  const isFailed = task.status === 'FAILED';

  return (
    <Card>
      <CardMedia
        sx={{ height: 120, position: 'relative' }}
      >
        {isCompleted && task.videoUrl ? (
          <video
            src={task.videoUrl}
            style={{ width: '100%', height: '100%', objectFit: 'cover' }}
            muted
          />
        ) : (
          <Skeleton variant="rectangular" height={120} animation={isProcessing ? 'wave' : false} />
        )}
        
        {/* 狀態 Badge */}
        <Chip
          label={getStatusLabel(task.status)}
          color={getStatusColor(task.status)}
          size="small"
          sx={{ position: 'absolute', top: 8, right: 8 }}
        />
      </CardMedia>
      <CardContent sx={{ py: 1 }}>
        <Typography variant="caption" color="text.secondary">
          {formatDate(task.createdAt)}
        </Typography>
      </CardContent>
    </Card>
  );
}
```

---

## 6. 型別定義擴充

```ts
// src/types/video.ts 新增

export interface VideoHistoryResponse {
  tasks: VideoTask[];
}
```

---

## 7. 後端 API 實作

### 7.1 Next.js API Route

**檔案**：`src/pages/api/v1/video/residents/[residentId]/history.ts`

```ts
export default async function handler(req: NextApiRequest, res: NextApiResponse) {
  if (req.method !== 'GET') {
    return res.status(405).json({ error: 'Method not allowed' });
  }

  const { residentId } = req.query;

  // 查詢 DynamoDB，使用 GSI residentId-createdAt-index
  const result = await dynamoClient.send(new QueryCommand({
    TableName: TABLE_NAME,
    IndexName: 'residentId-createdAt-index',
    KeyConditionExpression: 'residentId = :rid',
    ExpressionAttributeValues: {
      ':rid': residentId,
    },
    ScanIndexForward: false, // 降序（最新在前）
    Limit: 20, // 限制筆數
  }));

  return res.json({
    tasks: result.Items || [],
  });
}
```

---

## 8. 實作清單

### 8.1 前端變更
- [ ] 新增 `src/store/videoSlice.ts`
- [ ] 整合 videoSlice 至 store
- [ ] 擴充 `src/store/videoApi.ts` — 新增 getVideoHistory
- [ ] 擴充 `src/types/video.ts` — 新增 VideoHistoryResponse
- [ ] 新增 `src/components/VideoHistoryList.tsx`
- [ ] 新增 `src/components/VideoHistoryCard.tsx`
- [ ] 修改 `src/pages/family/VideoUpload.tsx` — 整合 activeTask 邏輯與歷史列表

### 8.2 後端變更
- [ ] 新增 `src/pages/api/v1/video/residents/[residentId]/history.ts`

---

## 9. 驗收標準

1. **歷史紀錄顯示**：
   - 選擇住民後，下方顯示該住民的歷史影片
   - COMPLETED 狀態顯示影片縮圖
   - PROCESSING 狀態顯示骨架屏動畫
   - FAILED 狀態顯示錯誤標示

2. **跨頁面進度追蹤**：
   - 上傳開始後切換到其他頁面
   - 再切回上傳頁面，自動恢復顯示處理中狀態
   - 輪詢持續進行直到完成/失敗

---

## 附錄：技術決策

| 決策項目 | 選擇 | 理由 |
|----------|------|------|
| 狀態管理 | Redux Slice | 符合現有架構，全局狀態跨頁面共享 |
| 歷史列表位置 | 同一頁面下方 | 減少頁面切換，操作流暢 |
| 歷史範圍 | 只顯示該住民 | 符合使用情境，減少資料量 |
