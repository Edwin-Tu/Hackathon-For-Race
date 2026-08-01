# AI 圖生影片功能實作計畫

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 實作家屬上傳照片自動生成 5 秒循環動圖的完整功能

**Architecture:** AWS Serverless 架構，前端直傳 S3，Lambda 透過 S3 Event 觸發呼叫 Bedrock Luma Ray 生成影片，DynamoDB 儲存任務狀態，前端輪詢查詢進度。

**Tech Stack:** Next.js 16, React 19, MUI 9, RTK Query, AWS SDK v3, Lambda (Node.js 20), DynamoDB, S3, Bedrock

## Global Constraints

- Node.js 20.x（Lambda Runtime）
- Next.js 16.x（現有專案）
- AWS Region: `us-west-2`
- S3 Buckets: `my-app-images-prod-us-west-2`, `my-app-videos-prod-us-west-2`
- DynamoDB Table: `VideoTasks`
- Bedrock Model: `luma.ray-v2:0`
- 語言：繁體中文（UI 文字、程式碼註解）

---

## File Structure

### 新增檔案

| 路徑 | 職責 |
|------|------|
| `src/types/video.ts` | VideoTask 型別定義 |
| `src/store/videoApi.ts` | RTK Query video endpoints |
| `src/pages/api/v1/video/presigned-url.ts` | 取得 S3 預簽名 URL |
| `src/pages/api/v1/video/tasks/[taskId].ts` | 查詢任務狀態 |
| `src/pages/api/v1/video/residents/[residentId]/latest.ts` | 取得住民最新動圖 |
| `src/pages/family/VideoUpload.tsx` | 家屬上傳頁面 |
| `src/utils/aws.ts` | AWS SDK 初始化（S3、DynamoDB） |
| `lambda/generate-video/index.mjs` | Lambda 函式主程式 |
| `lambda/generate-video/package.json` | Lambda 依賴 |

### 修改檔案

| 路徑 | 修改內容 |
|------|----------|
| `src/store/index.ts` | 註冊 videoApi reducer |
| `src/types.ts` | 匯出 video types |
| `package.json` | 新增 @aws-sdk 依賴 |

---

## Task 1: 型別定義與 AWS SDK 設定

**Files:**
- Create: `src/types/video.ts`
- Create: `src/utils/aws.ts`
- Modify: `src/types.ts`
- Modify: `package.json`

**Interfaces:**
- Produces: `VideoTask`, `VideoTaskStatus` 型別供後續 API 和前端使用
- Produces: `s3Client`, `dynamoClient` 供 API Routes 使用

- [ ] **Step 1: 安裝 AWS SDK 依賴**

執行：
```bash
npm install @aws-sdk/client-s3 @aws-sdk/s3-request-presigner @aws-sdk/client-dynamodb @aws-sdk/lib-dynamodb
```

- [ ] **Step 2: 建立 VideoTask 型別定義**

建立 `src/types/video.ts`：
```ts
// 影片生成任務狀態
export type VideoTaskStatus = 'PENDING' | 'PROCESSING' | 'COMPLETED' | 'FAILED';

// DynamoDB VideoTask 記錄
export interface VideoTask {
  taskId: string;
  residentId: string;
  familyMemberId: string;
  imageKey: string;
  videoKey?: string;
  videoUrl?: string;
  status: VideoTaskStatus;
  prompt?: string;
  errorMessage?: string;
  createdAt: number;
  updatedAt: number;
}

// API 回應型別
export interface PresignedUrlResponse {
  uploadUrl: string;
  imageKey: string;
  taskId: string;
}

export interface TaskStatusResponse {
  taskId: string;
  status: VideoTaskStatus;
  videoUrl?: string;
  errorMessage?: string;
}

export interface LatestVideoResponse {
  videoUrl: string;
  createdAt: number;
}
```

- [ ] **Step 3: 匯出型別到主 types.ts**

修改 `src/types.ts`，在檔案末尾加入：
```ts
// Video 相關型別
export * from './types/video';
```

- [ ] **Step 4: 建立 AWS SDK 初始化**

建立 `src/utils/aws.ts`：
```ts
import { S3Client } from '@aws-sdk/client-s3';
import { DynamoDBClient } from '@aws-sdk/client-dynamodb';
import { DynamoDBDocumentClient } from '@aws-sdk/lib-dynamodb';

// S3 Client
export const s3Client = new S3Client({
  region: process.env.AWS_REGION,
  credentials: {
    accessKeyId: process.env.AWS_ACCESS_KEY_ID!,
    secretAccessKey: process.env.AWS_SECRET_ACCESS_KEY!,
  },
});

// DynamoDB Client
const dynamoClient = new DynamoDBClient({
  region: process.env.AWS_REGION,
  credentials: {
    accessKeyId: process.env.AWS_ACCESS_KEY_ID!,
    secretAccessKey: process.env.AWS_SECRET_ACCESS_KEY!,
  },
});

export const docClient = DynamoDBDocumentClient.from(dynamoClient);

// 環境變數
export const AWS_CONFIG = {
  imagesBucket: process.env.AWS_S3_IMAGES_BUCKET!,
  videosBucket: process.env.AWS_S3_VIDEOS_BUCKET!,
  videoTasksTable: process.env.AWS_DYNAMODB_TABLE_VIDEO_TASKS!,
  bedrockModelId: process.env.AWS_BEDROCK_MODEL_ID!,
  region: process.env.AWS_REGION!,
};
```

- [ ] **Step 5: 驗證型別編譯通過**

執行：
```bash
npx tsc --noEmit src/types/video.ts src/utils/aws.ts
```
預期：無錯誤輸出

- [ ] **Step 6: Commit**

```bash
git add src/types/video.ts src/utils/aws.ts src/types.ts package.json package-lock.json
git commit -m "feat(video): add VideoTask types and AWS SDK setup"
```

---

## Task 2: Presigned URL API

**Files:**
- Create: `src/pages/api/v1/video/presigned-url.ts`

**Interfaces:**
- Consumes: `s3Client`, `docClient`, `AWS_CONFIG` from `src/utils/aws.ts`
- Consumes: `VideoTask`, `PresignedUrlResponse` from `src/types/video.ts`
- Produces: `POST /api/v1/video/presigned-url` API endpoint

- [ ] **Step 1: 建立 presigned-url API Route**

建立 `src/pages/api/v1/video/presigned-url.ts`：
```ts
import type { NextApiRequest, NextApiResponse } from 'next';
import { PutObjectCommand } from '@aws-sdk/client-s3';
import { getSignedUrl } from '@aws-sdk/s3-request-presigner';
import { PutCommand } from '@aws-sdk/lib-dynamodb';
import { v4 as uuidv4 } from 'uuid';
import { s3Client, docClient, AWS_CONFIG } from '@/utils/aws';
import type { PresignedUrlResponse, VideoTask } from '@/types/video';

export default async function handler(
  req: NextApiRequest,
  res: NextApiResponse<PresignedUrlResponse | { error: string }>
) {
  if (req.method !== 'POST') {
    return res.status(405).json({ error: 'Method not allowed' });
  }

  try {
    const { residentId, filename } = req.body;

    if (!residentId || !filename) {
      return res.status(400).json({ error: '缺少必要參數' });
    }

    // 從 token 取得 familyMemberId（暫時用固定值，待整合驗證）
    const familyMemberId = 'family-001'; // TODO: 從 auth token 取得

    const taskId = uuidv4();
    const timestamp = Date.now();
    const imageKey = `images/${residentId}/${familyMemberId}/${timestamp}_${filename}`;

    // 產生 presigned URL
    const command = new PutObjectCommand({
      Bucket: AWS_CONFIG.imagesBucket,
      Key: imageKey,
      ContentType: 'image/jpeg',
    });
    const uploadUrl = await getSignedUrl(s3Client, command, { expiresIn: 300 });

    // 建立 DynamoDB 任務記錄（PENDING 狀態）
    const task: VideoTask = {
      taskId,
      residentId,
      familyMemberId,
      imageKey,
      status: 'PENDING',
      createdAt: timestamp,
      updatedAt: timestamp,
    };

    await docClient.send(new PutCommand({
      TableName: AWS_CONFIG.videoTasksTable,
      Item: task,
    }));

    return res.status(200).json({
      uploadUrl,
      imageKey,
      taskId,
    });
  } catch (error) {
    console.error('Presigned URL error:', error);
    return res.status(500).json({ error: '產生上傳連結失敗' });
  }
}
```

- [ ] **Step 2: 安裝 uuid 依賴**

執行：
```bash
npm install uuid
npm install -D @types/uuid
```

- [ ] **Step 3: 驗證編譯通過**

執行：
```bash
npx tsc --noEmit src/pages/api/v1/video/presigned-url.ts
```
預期：無錯誤

- [ ] **Step 4: Commit**

```bash
git add src/pages/api/v1/video/presigned-url.ts package.json package-lock.json
git commit -m "feat(video): add presigned-url API endpoint"
```

---

## Task 3: Task Status API

**Files:**
- Create: `src/pages/api/v1/video/tasks/[taskId].ts`

**Interfaces:**
- Consumes: `docClient`, `AWS_CONFIG` from `src/utils/aws.ts`
- Consumes: `VideoTask`, `TaskStatusResponse` from `src/types/video.ts`
- Produces: `GET /api/v1/video/tasks/{taskId}` API endpoint

- [ ] **Step 1: 建立 task status API Route**

建立 `src/pages/api/v1/video/tasks/[taskId].ts`：
```ts
import type { NextApiRequest, NextApiResponse } from 'next';
import { GetCommand } from '@aws-sdk/lib-dynamodb';
import { docClient, AWS_CONFIG } from '@/utils/aws';
import type { VideoTask, TaskStatusResponse } from '@/types/video';

export default async function handler(
  req: NextApiRequest,
  res: NextApiResponse<TaskStatusResponse | { error: string }>
) {
  if (req.method !== 'GET') {
    return res.status(405).json({ error: 'Method not allowed' });
  }

  try {
    const { taskId } = req.query;

    if (!taskId || typeof taskId !== 'string') {
      return res.status(400).json({ error: '缺少 taskId' });
    }

    const result = await docClient.send(new GetCommand({
      TableName: AWS_CONFIG.videoTasksTable,
      Key: { taskId },
    }));

    if (!result.Item) {
      return res.status(404).json({ error: '找不到任務' });
    }

    const task = result.Item as VideoTask;

    return res.status(200).json({
      taskId: task.taskId,
      status: task.status,
      videoUrl: task.videoUrl,
      errorMessage: task.errorMessage,
    });
  } catch (error) {
    console.error('Get task status error:', error);
    return res.status(500).json({ error: '查詢任務狀態失敗' });
  }
}
```

- [ ] **Step 2: 驗證編譯通過**

執行：
```bash
npx tsc --noEmit src/pages/api/v1/video/tasks/[taskId].ts
```
預期：無錯誤

- [ ] **Step 3: Commit**

```bash
git add src/pages/api/v1/video/tasks/[taskId].ts
git commit -m "feat(video): add task status API endpoint"
```

---

## Task 4: Latest Video API

**Files:**
- Create: `src/pages/api/v1/video/residents/[residentId]/latest.ts`

**Interfaces:**
- Consumes: `docClient`, `AWS_CONFIG` from `src/utils/aws.ts`
- Consumes: `VideoTask`, `LatestVideoResponse` from `src/types/video.ts`
- Produces: `GET /api/v1/video/residents/{residentId}/latest` API endpoint

- [ ] **Step 1: 建立 latest video API Route**

建立 `src/pages/api/v1/video/residents/[residentId]/latest.ts`：
```ts
import type { NextApiRequest, NextApiResponse } from 'next';
import { QueryCommand } from '@aws-sdk/lib-dynamodb';
import { docClient, AWS_CONFIG } from '@/utils/aws';
import type { VideoTask, LatestVideoResponse } from '@/types/video';

export default async function handler(
  req: NextApiRequest,
  res: NextApiResponse<LatestVideoResponse | null | { error: string }>
) {
  if (req.method !== 'GET') {
    return res.status(405).json({ error: 'Method not allowed' });
  }

  try {
    const { residentId } = req.query;

    if (!residentId || typeof residentId !== 'string') {
      return res.status(400).json({ error: '缺少 residentId' });
    }

    // 使用 GSI 查詢該住民最新的已完成任務
    const result = await docClient.send(new QueryCommand({
      TableName: AWS_CONFIG.videoTasksTable,
      IndexName: 'residentId-createdAt-index',
      KeyConditionExpression: 'residentId = :rid',
      FilterExpression: '#status = :status',
      ExpressionAttributeNames: {
        '#status': 'status',
      },
      ExpressionAttributeValues: {
        ':rid': residentId,
        ':status': 'COMPLETED',
      },
      ScanIndexForward: false, // 降序排列，最新的在前
      Limit: 1,
    }));

    if (!result.Items || result.Items.length === 0) {
      return res.status(200).json(null);
    }

    const task = result.Items[0] as VideoTask;

    return res.status(200).json({
      videoUrl: task.videoUrl!,
      createdAt: task.createdAt,
    });
  } catch (error) {
    console.error('Get latest video error:', error);
    return res.status(500).json({ error: '查詢最新影片失敗' });
  }
}
```

- [ ] **Step 2: 驗證編譯通過**

執行：
```bash
npx tsc --noEmit src/pages/api/v1/video/residents/[residentId]/latest.ts
```
預期：無錯誤

- [ ] **Step 3: Commit**

```bash
git add src/pages/api/v1/video/residents/[residentId]/latest.ts
git commit -m "feat(video): add latest video API endpoint"
```

---

## Task 5: RTK Query Video Endpoints

**Files:**
- Create: `src/store/videoApi.ts`
- Modify: `src/store/index.ts`

**Interfaces:**
- Consumes: `PresignedUrlResponse`, `TaskStatusResponse`, `LatestVideoResponse` from `src/types/video.ts`
- Produces: `useGetPresignedUrlMutation`, `useGetTaskStatusQuery`, `useGetLatestVideoQuery` hooks

- [ ] **Step 1: 建立 videoApi slice**

建立 `src/store/videoApi.ts`：
```ts
import { createApi, fetchBaseQuery } from '@reduxjs/toolkit/query/react';
import type {
  PresignedUrlResponse,
  TaskStatusResponse,
  LatestVideoResponse,
} from '@/types/video';

export const videoApi = createApi({
  reducerPath: 'videoApi',
  baseQuery: fetchBaseQuery({
    baseUrl: '/api/v1/video',
    prepareHeaders: (headers, { getState }) => {
      const token = (getState() as any).auth?.token;
      if (token) headers.set('authorization', `Bearer ${token}`);
      return headers;
    },
  }),
  tagTypes: ['VideoTask'],
  endpoints: (builder) => ({
    // 取得 S3 預簽名 URL
    getPresignedUrl: builder.mutation<
      PresignedUrlResponse,
      { residentId: string; filename: string }
    >({
      query: (body) => ({
        url: '/presigned-url',
        method: 'POST',
        body,
      }),
    }),

    // 查詢任務狀態
    getTaskStatus: builder.query<TaskStatusResponse, string>({
      query: (taskId) => `/tasks/${taskId}`,
      providesTags: (result, error, taskId) => [{ type: 'VideoTask', id: taskId }],
    }),

    // 取得住民最新影片
    getLatestVideo: builder.query<LatestVideoResponse | null, string>({
      query: (residentId) => `/residents/${residentId}/latest`,
    }),
  }),
});

export const {
  useGetPresignedUrlMutation,
  useGetTaskStatusQuery,
  useGetLatestVideoQuery,
} = videoApi;
```

- [ ] **Step 2: 註冊 videoApi 到 store**

讀取並修改 `src/store/index.ts`，加入 videoApi：

在 import 區加入：
```ts
import { videoApi } from './videoApi';
```

在 store 配置的 reducer 中加入：
```ts
[videoApi.reducerPath]: videoApi.reducer,
```

在 middleware 中加入：
```ts
.concat(videoApi.middleware)
```

- [ ] **Step 3: 驗證編譯通過**

執行：
```bash
npx tsc --noEmit src/store/videoApi.ts src/store/index.ts
```
預期：無錯誤

- [ ] **Step 4: Commit**

```bash
git add src/store/videoApi.ts src/store/index.ts
git commit -m "feat(video): add RTK Query video endpoints"
```

---

## Task 6: 家屬上傳頁面

**Files:**
- Create: `src/pages/family/VideoUpload.tsx`

**Interfaces:**
- Consumes: `useGetPresignedUrlMutation`, `useGetTaskStatusQuery` from `src/store/videoApi.ts`
- Produces: 家屬端影片上傳頁面 UI

- [ ] **Step 1: 建立 VideoUpload 頁面**

建立 `src/pages/family/VideoUpload.tsx`：
```tsx
import React, { useState, useCallback, useEffect } from 'react';
import {
  Box,
  Button,
  Card,
  CardContent,
  Typography,
  LinearProgress,
  Alert,
  Skeleton,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
} from '@mui/material';
import CloudUploadIcon from '@mui/icons-material/CloudUpload';
import ReplayIcon from '@mui/icons-material/Replay';
import {
  useGetPresignedUrlMutation,
  useGetTaskStatusQuery,
} from '@/store/videoApi';

type UploadStatus = 'idle' | 'uploading' | 'processing' | 'completed' | 'failed';

// 模擬住民列表（實際應從 API 取得）
const mockResidents = [
  { id: 'resident-001', name: '王爺爺' },
  { id: 'resident-002', name: '李奶奶' },
];

export default function VideoUpload() {
  const [file, setFile] = useState<File | null>(null);
  const [residentId, setResidentId] = useState('');
  const [status, setStatus] = useState<UploadStatus>('idle');
  const [taskId, setTaskId] = useState<string | null>(null);
  const [videoUrl, setVideoUrl] = useState<string | null>(null);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  const [getPresignedUrl] = useGetPresignedUrlMutation();
  
  // 輪詢任務狀態
  const { data: taskStatus, refetch } = useGetTaskStatusQuery(taskId!, {
    skip: !taskId || status !== 'processing',
    pollingInterval: 5000, // 每 5 秒輪詢
  });

  // 監聽任務狀態變化
  useEffect(() => {
    if (!taskStatus) return;

    if (taskStatus.status === 'COMPLETED' && taskStatus.videoUrl) {
      setStatus('completed');
      setVideoUrl(taskStatus.videoUrl);
    } else if (taskStatus.status === 'FAILED') {
      setStatus('failed');
      setErrorMessage(taskStatus.errorMessage || '影片生成失敗');
    }
  }, [taskStatus]);

  // 處理檔案選擇
  const handleFileChange = useCallback((e: React.ChangeEvent<HTMLInputElement>) => {
    const selectedFile = e.target.files?.[0];
    if (!selectedFile) return;

    // 驗證檔案格式
    if (!['image/jpeg', 'image/png'].includes(selectedFile.type)) {
      setErrorMessage('不支援的檔案格式，請上傳 JPG 或 PNG');
      return;
    }

    // 驗證檔案大小（10MB）
    if (selectedFile.size > 10 * 1024 * 1024) {
      setErrorMessage('檔案過大，請上傳 10MB 以下的圖片');
      return;
    }

    setFile(selectedFile);
    setErrorMessage(null);
  }, []);

  // 上傳並開始生成
  const handleUpload = async () => {
    if (!file || !residentId) return;

    setStatus('uploading');
    setErrorMessage(null);

    try {
      // 1. 取得預簽名 URL
      const result = await getPresignedUrl({
        residentId,
        filename: file.name,
      }).unwrap();

      // 2. 直傳 S3
      const uploadResponse = await fetch(result.uploadUrl, {
        method: 'PUT',
        body: file,
        headers: {
          'Content-Type': file.type,
        },
      });

      if (!uploadResponse.ok) {
        throw new Error('上傳失敗');
      }

      // 3. 設定 taskId 並開始輪詢
      setTaskId(result.taskId);
      setStatus('processing');
    } catch (error) {
      console.error('Upload error:', error);
      setStatus('failed');
      setErrorMessage('上傳失敗，請檢查網路後重試');
    }
  };

  // 重試
  const handleRetry = () => {
    setStatus('idle');
    setTaskId(null);
    setVideoUrl(null);
    setErrorMessage(null);
    setFile(null);
  };

  return (
    <Box sx={{ maxWidth: 600, mx: 'auto', p: 3 }}>
      <Typography variant="h5" gutterBottom>
        上傳照片生成動態影像
      </Typography>
      <Typography variant="body2" color="text.secondary" sx={{ mb: 3 }}>
        上傳一張您的照片，AI 將自動生成 5 秒的動態影像，供長者端播放語音時顯示。
      </Typography>

      <Card>
        <CardContent>
          {/* 選擇住民 */}
          <FormControl fullWidth sx={{ mb: 2 }}>
            <InputLabel>選擇長者</InputLabel>
            <Select
              value={residentId}
              label="選擇長者"
              onChange={(e) => setResidentId(e.target.value)}
              disabled={status !== 'idle'}
            >
              {mockResidents.map((r) => (
                <MenuItem key={r.id} value={r.id}>
                  {r.name}
                </MenuItem>
              ))}
            </Select>
          </FormControl>

          {/* 上傳區域 */}
          {status === 'idle' && (
            <>
              <Button
                component="label"
                variant="outlined"
                fullWidth
                startIcon={<CloudUploadIcon />}
                sx={{ py: 3, mb: 2 }}
              >
                {file ? file.name : '選擇照片'}
                <input
                  type="file"
                  accept="image/jpeg,image/png"
                  hidden
                  onChange={handleFileChange}
                />
              </Button>

              <Button
                variant="contained"
                fullWidth
                onClick={handleUpload}
                disabled={!file || !residentId}
              >
                開始生成
              </Button>
            </>
          )}

          {/* 上傳中 */}
          {status === 'uploading' && (
            <Box sx={{ textAlign: 'center', py: 3 }}>
              <Typography gutterBottom>上傳中...</Typography>
              <LinearProgress />
            </Box>
          )}

          {/* 處理中 */}
          {status === 'processing' && (
            <Box sx={{ textAlign: 'center', py: 3 }}>
              <Skeleton variant="rectangular" height={200} sx={{ mb: 2 }} />
              <Typography>AI 生成中，約需 30 秒...</Typography>
              <LinearProgress sx={{ mt: 2 }} />
            </Box>
          )}

          {/* 完成 */}
          {status === 'completed' && videoUrl && (
            <Box sx={{ textAlign: 'center' }}>
              <Typography gutterBottom color="success.main">
                生成完成！
              </Typography>
              <video
                src={videoUrl}
                autoPlay
                loop
                muted
                playsInline
                style={{ width: '100%', maxWidth: 400, borderRadius: 8 }}
              />
              <Box sx={{ mt: 2 }}>
                <Button
                  variant="outlined"
                  startIcon={<ReplayIcon />}
                  onClick={handleRetry}
                >
                  重新上傳
                </Button>
              </Box>
            </Box>
          )}

          {/* 錯誤 */}
          {status === 'failed' && (
            <Box sx={{ textAlign: 'center', py: 3 }}>
              <Alert severity="error" sx={{ mb: 2 }}>
                {errorMessage || '發生錯誤'}
              </Alert>
              <Button
                variant="outlined"
                startIcon={<ReplayIcon />}
                onClick={handleRetry}
              >
                重試
              </Button>
            </Box>
          )}

          {/* 格式錯誤提示 */}
          {errorMessage && status === 'idle' && (
            <Alert severity="error" sx={{ mt: 2 }}>
              {errorMessage}
            </Alert>
          )}
        </CardContent>
      </Card>
    </Box>
  );
}
```

- [ ] **Step 2: 驗證編譯通過**

執行：
```bash
npx tsc --noEmit src/pages/family/VideoUpload.tsx
```
預期：無錯誤

- [ ] **Step 3: Commit**

```bash
git add src/pages/family/VideoUpload.tsx
git commit -m "feat(video): add family video upload page"
```

---

## Task 7: Lambda 函式

**Files:**
- Create: `lambda/generate-video/index.mjs`
- Create: `lambda/generate-video/package.json`

**Interfaces:**
- Consumes: S3 Event（觸發）
- Consumes: DynamoDB VideoTasks table
- Consumes: Bedrock Luma Ray API
- Produces: 更新 DynamoDB 任務狀態，將生成的 MP4 存入 S3

- [ ] **Step 1: 建立 Lambda 目錄與 package.json**

建立 `lambda/generate-video/package.json`：
```json
{
  "name": "generate-video-lambda",
  "version": "1.0.0",
  "type": "module",
  "dependencies": {
    "@aws-sdk/client-bedrock-runtime": "^3.700.0",
    "@aws-sdk/client-dynamodb": "^3.700.0",
    "@aws-sdk/client-s3": "^3.700.0",
    "@aws-sdk/lib-dynamodb": "^3.700.0"
  }
}
```

- [ ] **Step 2: 建立 Lambda 主程式**

建立 `lambda/generate-video/index.mjs`：
```js
import { S3Client, GetObjectCommand, PutObjectCommand } from '@aws-sdk/client-s3';
import { DynamoDBClient } from '@aws-sdk/client-dynamodb';
import { DynamoDBDocumentClient, UpdateCommand, QueryCommand } from '@aws-sdk/lib-dynamodb';
import { BedrockRuntimeClient, InvokeModelCommand, GetAsyncInvokeCommand, StartAsyncInvokeCommand } from '@aws-sdk/client-bedrock-runtime';

const s3Client = new S3Client();
const dynamoClient = DynamoDBDocumentClient.from(new DynamoDBClient());
const bedrockClient = new BedrockRuntimeClient({ region: process.env.AWS_REGION });

const IMAGES_BUCKET = process.env.AWS_S3_IMAGES_BUCKET;
const VIDEOS_BUCKET = process.env.AWS_S3_VIDEOS_BUCKET;
const TABLE_NAME = process.env.AWS_DYNAMODB_TABLE_VIDEO_TASKS;
const MODEL_ID = process.env.AWS_BEDROCK_MODEL_ID;

export const handler = async (event) => {
  console.log('Received event:', JSON.stringify(event, null, 2));

  for (const record of event.Records) {
    const bucket = record.s3.bucket.name;
    const key = decodeURIComponent(record.s3.object.key.replace(/\+/g, ' '));

    console.log(`Processing: ${bucket}/${key}`);

    // 解析 key 取得 residentId 和 familyMemberId
    // 格式: images/{residentId}/{familyMemberId}/{timestamp}_{filename}
    const keyParts = key.split('/');
    if (keyParts.length < 4 || keyParts[0] !== 'images') {
      console.log('Invalid key format, skipping');
      continue;
    }

    const residentId = keyParts[1];
    const familyMemberId = keyParts[2];

    // 查找對應的 PENDING 任務
    const queryResult = await dynamoClient.send(new QueryCommand({
      TableName: TABLE_NAME,
      IndexName: 'residentId-createdAt-index',
      KeyConditionExpression: 'residentId = :rid',
      FilterExpression: 'imageKey = :imageKey AND #status = :status',
      ExpressionAttributeNames: { '#status': 'status' },
      ExpressionAttributeValues: {
        ':rid': residentId,
        ':imageKey': key,
        ':status': 'PENDING',
      },
      Limit: 1,
    }));

    if (!queryResult.Items || queryResult.Items.length === 0) {
      console.log('No pending task found for this image');
      continue;
    }

    const task = queryResult.Items[0];
    const taskId = task.taskId;

    try {
      // 更新狀態為 PROCESSING
      await updateTaskStatus(taskId, 'PROCESSING');

      // 呼叫 Bedrock 生成影片
      const videoKey = `videos/${residentId}/${familyMemberId}/${taskId}.mp4`;
      
      // Bedrock Luma Ray 非同步呼叫
      const invokeResult = await bedrockClient.send(new StartAsyncInvokeCommand({
        modelId: MODEL_ID,
        modelInput: {
          taskType: 'IMAGE_TO_VIDEO',
          imageToVideoParams: {
            images: [{
              format: 'jpeg',
              source: {
                s3Location: {
                  uri: `s3://${IMAGES_BUCKET}/${key}`,
                },
              },
            }],
            text: 'gentle natural movement, soft breathing motion, warm family atmosphere, subtle eye blinks, slight head movement',
          },
          videoGenerationConfig: {
            durationSeconds: 5,
            fps: 24,
            dimension: '1280x720',
          },
        },
        outputDataConfig: {
          s3OutputDataConfig: {
            s3Uri: `s3://${VIDEOS_BUCKET}/${videoKey}`,
          },
        },
      }));

      const invocationArn = invokeResult.invocationArn;
      console.log('Started async invoke:', invocationArn);

      // 輪詢等待完成（Lambda 有 5 分鐘 timeout）
      let completed = false;
      let attempts = 0;
      const maxAttempts = 60; // 最多等待 5 分鐘

      while (!completed && attempts < maxAttempts) {
        await sleep(5000); // 等待 5 秒
        attempts++;

        const statusResult = await bedrockClient.send(new GetAsyncInvokeCommand({
          invocationArn,
        }));

        console.log(`Attempt ${attempts}: Status = ${statusResult.status}`);

        if (statusResult.status === 'Completed') {
          completed = true;
          
          // 建立影片 URL
          const videoUrl = `https://${VIDEOS_BUCKET}.s3.${process.env.AWS_REGION}.amazonaws.com/${videoKey}`;
          
          // 更新任務為完成
          await updateTaskStatus(taskId, 'COMPLETED', {
            videoKey,
            videoUrl,
          });
          
          console.log('Video generation completed:', videoUrl);
        } else if (statusResult.status === 'Failed') {
          throw new Error(statusResult.failureMessage || 'Bedrock generation failed');
        }
      }

      if (!completed) {
        throw new Error('Timeout waiting for video generation');
      }

    } catch (error) {
      console.error('Error processing:', error);
      
      await updateTaskStatus(taskId, 'FAILED', {
        errorMessage: error.message || '影片生成失敗',
      });
    }
  }

  return { statusCode: 200, body: 'OK' };
};

async function updateTaskStatus(taskId, status, extraFields = {}) {
  const updateExpression = ['#status = :status', 'updatedAt = :updatedAt'];
  const expressionAttributeValues = {
    ':status': status,
    ':updatedAt': Date.now(),
  };

  for (const [key, value] of Object.entries(extraFields)) {
    updateExpression.push(`${key} = :${key}`);
    expressionAttributeValues[`:${key}`] = value;
  }

  await dynamoClient.send(new UpdateCommand({
    TableName: TABLE_NAME,
    Key: { taskId },
    UpdateExpression: `SET ${updateExpression.join(', ')}`,
    ExpressionAttributeNames: { '#status': 'status' },
    ExpressionAttributeValues: expressionAttributeValues,
  }));
}

function sleep(ms) {
  return new Promise(resolve => setTimeout(resolve, ms));
}
```

- [ ] **Step 3: Commit**

```bash
git add lambda/generate-video/
git commit -m "feat(video): add Lambda function for video generation"
```

---

## Task 8: 整合測試與最終驗證

**Files:**
- 無新增檔案

**Interfaces:**
- 整合測試所有元件

- [ ] **Step 1: 驗證前端編譯**

執行：
```bash
npm run build
```
預期：編譯成功

- [ ] **Step 2: 啟動開發伺服器測試 API**

執行：
```bash
npm run dev
```

測試 API（使用 curl 或 Postman）：
```bash
curl -X POST http://localhost:3000/api/v1/video/presigned-url \
  -H "Content-Type: application/json" \
  -d '{"residentId": "resident-001", "filename": "test.jpg"}'
```
預期：回傳 `{ uploadUrl, imageKey, taskId }`

- [ ] **Step 3: 驗證頁面可存取**

開啟瀏覽器存取：`http://localhost:3000/family/VideoUpload`
預期：顯示上傳頁面 UI

- [ ] **Step 4: Final Commit**

```bash
git add .
git commit -m "feat(video): complete AI video generator integration"
```

---

## 部署檢查清單

完成開發後，部署前需確認：

- [ ] AWS DynamoDB `VideoTasks` table 已建立，含 GSI `residentId-createdAt-index`
- [ ] AWS S3 `my-app-images-prod-us-west-2` bucket 已建立並設定 CORS
- [ ] AWS S3 `my-app-videos-prod-us-west-2` bucket 已建立並設定公開讀取（或使用 presigned URL）
- [ ] Lambda `generate-video` 已部署並設定 S3 Event 觸發
- [ ] Lambda IAM Role 有 S3、DynamoDB、Bedrock 權限
- [ ] Bedrock `luma.ray-v2:0` 模型已在 us-west-2 啟用
