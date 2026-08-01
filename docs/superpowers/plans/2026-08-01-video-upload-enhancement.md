# 影片上傳功能增強 實作計畫

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 增強影片上傳頁面，新增歷史紀錄顯示與跨頁面進度追蹤功能

**Architecture:** 使用 Redux Slice 儲存進行中的任務狀態（activeTask），搭配 RTK Query 輪詢機制。新增歷史 API endpoint 查詢 DynamoDB，前端顯示歷史影片卡片列表。

**Tech Stack:** React, Redux Toolkit, RTK Query, MUI, Next.js API Routes, AWS DynamoDB

## Global Constraints

- 遵循現有 Redux store 架構（`src/store/index.ts`）
- API 路徑遵循現有格式 `/api/v1/video/...`
- 使用 TypeScript 嚴格型別
- 使用 MUI 元件庫
- 程式碼註解使用繁體中文

---

## File Structure

| 動作 | 路徑 | 職責 |
|------|------|------|
| Create | `src/store/videoSlice.ts` | Redux slice 管理 activeTask 狀態 |
| Modify | `src/store/index.ts` | 整合 videoSlice |
| Modify | `src/store/videoApi.ts` | 新增 getVideoHistory endpoint |
| Modify | `src/types/video.ts` | 新增 VideoHistoryResponse 型別 |
| Create | `src/pages/api/v1/video/residents/[residentId]/history.ts` | 後端歷史 API |
| Create | `src/components/VideoHistoryList.tsx` | 歷史列表容器元件 |
| Create | `src/components/VideoHistoryCard.tsx` | 歷史卡片元件 |
| Modify | `src/pages/family/VideoUpload.tsx` | 整合 activeTask 邏輯與歷史列表 |

---

### Task 1: 建立 videoSlice — Redux 狀態管理

**Files:**
- Create: `src/store/videoSlice.ts`
- Modify: `src/store/index.ts`

**Interfaces:**
- Produces: 
  - `setActiveTask(payload: { residentId: string; taskId: string }): void`
  - `clearActiveTask(): void`
  - `selectActiveTask(state: RootState): ActiveTask | null`

- [ ] **Step 1: 建立 videoSlice.ts**

```ts
// src/store/videoSlice.ts
import { createSlice, PayloadAction } from '@reduxjs/toolkit';

export interface ActiveTask {
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

// Selector
export const selectActiveTask = (state: { video: VideoState }) => state.video.activeTask;

export default videoSlice.reducer;
```

- [ ] **Step 2: 整合至 store/index.ts**

修改 `src/store/index.ts`，在 reducer 中加入 videoSlice：

```ts
import { configureStore } from '@reduxjs/toolkit';
import { api } from './apiSlice';
import { videoApi } from './videoApi';
import videoReducer from './videoSlice';

export const store = configureStore({
  reducer: {
    [api.reducerPath]: api.reducer,
    [videoApi.reducerPath]: videoApi.reducer,
    video: videoReducer,
  },
  middleware: (getDefaultMiddleware) =>
    getDefaultMiddleware().concat(api.middleware).concat(videoApi.middleware),
});

type RootState = ReturnType<typeof store.getState>;
export type { RootState };
```

- [ ] **Step 3: 驗證 TypeScript 編譯**

Run: `npx tsc --noEmit`
Expected: 無型別錯誤

- [ ] **Step 4: Commit**

```bash
git add src/store/videoSlice.ts src/store/index.ts
git commit -m "feat(store): 新增 videoSlice 管理進行中任務狀態"
```

---

### Task 2: 擴充型別定義與 RTK Query API

**Files:**
- Modify: `src/types/video.ts`
- Modify: `src/store/videoApi.ts`

**Interfaces:**
- Produces:
  - `VideoHistoryResponse { tasks: VideoTask[] }`
  - `useGetVideoHistoryQuery(residentId: string): { data, isLoading, refetch }`

- [ ] **Step 1: 擴充 video.ts 型別**

在 `src/types/video.ts` 末尾新增：

```ts
// 歷史影片列表回應
export interface VideoHistoryResponse {
  tasks: VideoTask[];
}
```

- [ ] **Step 2: 擴充 videoApi.ts 新增 getVideoHistory**

在 `src/store/videoApi.ts` 的 endpoints 區塊內新增：

```ts
// 取得住民歷史影片列表
getVideoHistory: builder.query<VideoHistoryResponse, string>({
  query: (residentId) => `/residents/${residentId}/history`,
  providesTags: (result, error, residentId) => [
    { type: 'VideoTask', id: `history-${residentId}` },
  ],
}),
```

並在 export 中加入：

```ts
export const {
  useGetPresignedUrlMutation,
  useGetTaskStatusQuery,
  useGetLatestVideoQuery,
  useGetVideoHistoryQuery, // 新增
} = videoApi;
```

- [ ] **Step 3: 在 types/video.ts 引入 VideoHistoryResponse**

確認 `src/store/videoApi.ts` 開頭的 import 包含 `VideoHistoryResponse`：

```ts
import type {
  PresignedUrlResponse,
  TaskStatusResponse,
  LatestVideoResponse,
  VideoHistoryResponse, // 新增
} from '@/types/video';
```

- [ ] **Step 4: 驗證 TypeScript 編譯**

Run: `npx tsc --noEmit`
Expected: 無型別錯誤

- [ ] **Step 5: Commit**

```bash
git add src/types/video.ts src/store/videoApi.ts
git commit -m "feat(api): 新增 getVideoHistory RTK Query endpoint"
```

---

### Task 3: 建立後端歷史 API

**Files:**
- Create: `src/pages/api/v1/video/residents/[residentId]/history.ts`

**Interfaces:**
- Produces: `GET /api/v1/video/residents/{residentId}/history` → `VideoHistoryResponse`

- [ ] **Step 1: 建立 history.ts API Route**

```ts
// src/pages/api/v1/video/residents/[residentId]/history.ts
import type { NextApiRequest, NextApiResponse } from 'next';
import { QueryCommand } from '@aws-sdk/lib-dynamodb';
import { docClient, AWS_CONFIG } from '@/utils/aws';
import type { VideoTask, VideoHistoryResponse } from '@/types/video';

export default async function handler(
  req: NextApiRequest,
  res: NextApiResponse<VideoHistoryResponse | { error: string }>
) {
  if (req.method !== 'GET') {
    return res.status(405).json({ error: 'Method not allowed' });
  }

  try {
    const { residentId } = req.query;

    if (!residentId || typeof residentId !== 'string') {
      return res.status(400).json({ error: '缺少 residentId' });
    }

    // 使用 GSI 查詢該住民所有任務，按時間降序
    const result = await docClient.send(new QueryCommand({
      TableName: AWS_CONFIG.videoTasksTable,
      IndexName: 'residentId-createdAt-index',
      KeyConditionExpression: 'residentId = :rid',
      ExpressionAttributeValues: {
        ':rid': residentId,
      },
      ScanIndexForward: false, // 降序（最新在前）
      Limit: 20,
    }));

    const tasks = (result.Items || []) as VideoTask[];

    return res.status(200).json({ tasks });
  } catch (error) {
    console.error('Get video history error:', error);
    return res.status(500).json({ error: '查詢歷史影片失敗' });
  }
}
```

- [ ] **Step 2: 驗證 TypeScript 編譯**

Run: `npx tsc --noEmit`
Expected: 無型別錯誤

- [ ] **Step 3: Commit**

```bash
git add src/pages/api/v1/video/residents/\[residentId\]/history.ts
git commit -m "feat(api): 新增 GET /video/residents/:residentId/history 歷史 API"
```

---

### Task 4: 建立 VideoHistoryCard 元件

**Files:**
- Create: `src/components/VideoHistoryCard.tsx`

**Interfaces:**
- Consumes: `VideoTask` from `@/types/video`
- Produces: `<VideoHistoryCard task={task} />`

- [ ] **Step 1: 建立 VideoHistoryCard.tsx**

```tsx
// src/components/VideoHistoryCard.tsx
import React from 'react';
import {
  Card,
  CardContent,
  Skeleton,
  Chip,
  Typography,
  Box,
} from '@mui/material';
import type { VideoTask, VideoTaskStatus } from '@/types/video';

interface VideoHistoryCardProps {
  task: VideoTask;
}

// 狀態標籤文字
function getStatusLabel(status: VideoTaskStatus): string {
  switch (status) {
    case 'COMPLETED':
      return '已完成';
    case 'PROCESSING':
      return '生成中';
    case 'PENDING':
      return '等待中';
    case 'FAILED':
      return '失敗';
    default:
      return status;
  }
}

// 狀態顏色
function getStatusColor(status: VideoTaskStatus): 'success' | 'warning' | 'error' | 'default' {
  switch (status) {
    case 'COMPLETED':
      return 'success';
    case 'PROCESSING':
    case 'PENDING':
      return 'warning';
    case 'FAILED':
      return 'error';
    default:
      return 'default';
  }
}

// 格式化日期
function formatDate(timestamp: number): string {
  return new Date(timestamp).toLocaleDateString('zh-TW', {
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  });
}

export function VideoHistoryCard({ task }: VideoHistoryCardProps) {
  const isCompleted = task.status === 'COMPLETED';
  const isProcessing = task.status === 'PROCESSING' || task.status === 'PENDING';

  return (
    <Card sx={{ height: '100%' }}>
      <Box sx={{ height: 120, position: 'relative', bgcolor: 'grey.100' }}>
        {isCompleted && task.videoUrl ? (
          <video
            src={task.videoUrl}
            style={{ width: '100%', height: '100%', objectFit: 'cover' }}
            muted
            playsInline
          />
        ) : (
          <Skeleton
            variant="rectangular"
            height={120}
            animation={isProcessing ? 'wave' : false}
          />
        )}

        {/* 狀態 Badge */}
        <Chip
          label={getStatusLabel(task.status)}
          color={getStatusColor(task.status)}
          size="small"
          sx={{ position: 'absolute', top: 8, right: 8 }}
        />
      </Box>
      <CardContent sx={{ py: 1, '&:last-child': { pb: 1 } }}>
        <Typography variant="caption" color="text.secondary">
          {formatDate(task.createdAt)}
        </Typography>
        {task.status === 'FAILED' && task.errorMessage && (
          <Typography variant="caption" color="error" display="block">
            {task.errorMessage}
          </Typography>
        )}
      </CardContent>
    </Card>
  );
}
```

- [ ] **Step 2: 驗證 TypeScript 編譯**

Run: `npx tsc --noEmit`
Expected: 無型別錯誤

- [ ] **Step 3: Commit**

```bash
git add src/components/VideoHistoryCard.tsx
git commit -m "feat(ui): 新增 VideoHistoryCard 元件"
```

---

### Task 5: 建立 VideoHistoryList 元件

**Files:**
- Create: `src/components/VideoHistoryList.tsx`

**Interfaces:**
- Consumes: `useGetVideoHistoryQuery` from `@/store/videoApi`
- Produces: `<VideoHistoryList residentId={residentId} />`

- [ ] **Step 1: 建立 VideoHistoryList.tsx**

```tsx
// src/components/VideoHistoryList.tsx
import React from 'react';
import { Box, Typography, Skeleton, Grid } from '@mui/material';
import { useGetVideoHistoryQuery } from '@/store/videoApi';
import { VideoHistoryCard } from './VideoHistoryCard';

interface VideoHistoryListProps {
  residentId: string;
}

export function VideoHistoryList({ residentId }: VideoHistoryListProps) {
  const { data, isLoading, isError } = useGetVideoHistoryQuery(residentId, {
    skip: !residentId,
  });

  if (!residentId) return null;

  if (isLoading) {
    return (
      <Box sx={{ mt: 3 }}>
        <Typography variant="h6" gutterBottom>
          歷史影片
        </Typography>
        <Grid container spacing={2}>
          {[1, 2, 3].map((i) => (
            <Grid item xs={6} sm={4} key={i}>
              <Skeleton variant="rectangular" height={160} />
            </Grid>
          ))}
        </Grid>
      </Box>
    );
  }

  if (isError) {
    return (
      <Box sx={{ mt: 3 }}>
        <Typography color="error">載入歷史紀錄失敗</Typography>
      </Box>
    );
  }

  if (!data?.tasks?.length) {
    return (
      <Box sx={{ mt: 3 }}>
        <Typography variant="h6" gutterBottom>
          歷史影片
        </Typography>
        <Typography color="text.secondary">尚無歷史紀錄</Typography>
      </Box>
    );
  }

  return (
    <Box sx={{ mt: 3 }}>
      <Typography variant="h6" gutterBottom>
        歷史影片
      </Typography>
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

- [ ] **Step 2: 驗證 TypeScript 編譯**

Run: `npx tsc --noEmit`
Expected: 無型別錯誤

- [ ] **Step 3: Commit**

```bash
git add src/components/VideoHistoryList.tsx
git commit -m "feat(ui): 新增 VideoHistoryList 元件"
```

---

### Task 6: 整合 VideoUpload.tsx — 跨頁面狀態與歷史列表

**Files:**
- Modify: `src/pages/family/VideoUpload.tsx`

**Interfaces:**
- Consumes: 
  - `setActiveTask`, `clearActiveTask`, `selectActiveTask` from `@/store/videoSlice`
  - `VideoHistoryList` from `@/components/VideoHistoryList`
  - `useGetVideoHistoryQuery` from `@/store/videoApi`

- [ ] **Step 1: 新增 import**

在 `src/pages/family/VideoUpload.tsx` 開頭新增：

```tsx
import { useDispatch, useSelector } from 'react-redux';
import { setActiveTask, clearActiveTask, selectActiveTask } from '@/store/videoSlice';
import { VideoHistoryList } from '@/components/VideoHistoryList';
import { videoApi } from '@/store/videoApi';
```

- [ ] **Step 2: 在元件內新增 dispatch 與 selector**

在 `VideoUpload` 元件函式開頭新增：

```tsx
const dispatch = useDispatch();
const activeTask = useSelector(selectActiveTask);
```

- [ ] **Step 3: 新增頁面載入時恢復 activeTask 的 useEffect**

在現有的 `useEffect` 後面新增：

```tsx
// 頁面載入時，若有 activeTask 則恢復狀態
useEffect(() => {
  if (activeTask && status === 'idle') {
    setResidentId(activeTask.residentId);
    setTaskId(activeTask.taskId);
    setStatus('processing');
  }
  // eslint-disable-next-line react-hooks/exhaustive-deps
}, []);
```

- [ ] **Step 4: 修改 handleUpload — 上傳成功後 dispatch setActiveTask**

在 `handleUpload` 函式內，原本設定 `setTaskId(result.taskId)` 之後，新增：

```tsx
// 3. 設定 taskId 並開始輪詢
setTaskId(result.taskId);
dispatch(setActiveTask({ residentId, taskId: result.taskId }));
setStatus('processing');
```

- [ ] **Step 5: 修改監聽 taskStatus 的 useEffect — 完成/失敗時 clearActiveTask 並刷新歷史**

修改現有的 `useEffect(() => { if (!taskStatus) return; ... }, [taskStatus])` 為：

```tsx
// 監聽任務狀態變化
useEffect(() => {
  if (!taskStatus) return;

  if (taskStatus.status === 'COMPLETED' && taskStatus.videoUrl) {
    setStatus('completed');
    setVideoUrl(taskStatus.videoUrl);
    dispatch(clearActiveTask());
    // 刷新歷史列表
    dispatch(videoApi.util.invalidateTags([{ type: 'VideoTask', id: `history-${residentId}` }]));
  } else if (taskStatus.status === 'FAILED') {
    setStatus('failed');
    setErrorMessage(taskStatus.errorMessage || '影片生成失敗');
    dispatch(clearActiveTask());
    // 刷新歷史列表
    dispatch(videoApi.util.invalidateTags([{ type: 'VideoTask', id: `history-${residentId}` }]));
  }
}, [taskStatus, dispatch, residentId]);
```

- [ ] **Step 6: 在 return JSX 中加入 VideoHistoryList**

在 `</Card>` 之後、`</Box>` 之前加入：

```tsx
{/* 歷史影片列表 */}
<VideoHistoryList residentId={residentId} />
```

- [ ] **Step 7: 驗證 TypeScript 編譯**

Run: `npx tsc --noEmit`
Expected: 無型別錯誤

- [ ] **Step 8: 本地測試**

Run: `npm run dev`
手動測試：
1. 開啟 `/family/video-upload` 頁面
2. 選擇住民，確認下方顯示歷史列表
3. 上傳圖片，確認進度顯示
4. 切換到其他頁面再切回來，確認進度仍在顯示

- [ ] **Step 9: Commit**

```bash
git add src/pages/family/VideoUpload.tsx
git commit -m "feat(VideoUpload): 整合跨頁面狀態追蹤與歷史列表"
```

---

## 驗收檢查清單

- [ ] 選擇住民後，下方顯示該住民的歷史影片列表
- [ ] COMPLETED 狀態顯示影片縮圖
- [ ] PROCESSING/PENDING 狀態顯示骨架屏動畫
- [ ] FAILED 狀態顯示錯誤訊息
- [ ] 上傳開始後切換頁面再切回來，自動恢復顯示進行中狀態
- [ ] 任務完成/失敗後，歷史列表自動刷新
