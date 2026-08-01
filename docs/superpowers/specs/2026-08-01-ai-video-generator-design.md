# AI 圖生影片功能設計規格

> 建立日期：2026-08-01  
> 狀態：待審閱

## 1. 概述

### 1.1 功能目標
家屬上傳自己的照片，系統自動生成 5 秒循環動圖，供住民端播放語音時顯示家屬動態影像。

### 1.2 核心場景
1. 家屬在前端選擇住民、上傳照片
2. 系統自動觸發 AI 影片生成（無需手動點擊）
3. 生成完成後，住民端播放語音時可顯示家屬動圖

### 1.3 技術選型
- **架構**：完整 AWS Serverless（S3 + Lambda + Bedrock + DynamoDB）
- **前端**：整合進現有 Next.js + React + MUI 專案
- **進度通知**：輪詢（Polling）

---

## 2. 系統架構

```
[家屬前端頁面]
      │
      ├─(1) POST /api/v1/video/presigned-url → 取得 S3 上傳 URL
      │
      ├─(2) PUT 直傳照片至 S3 (images bucket)
      │                ↓
      │         [S3 Event 觸發]
      │                ↓
      │     [Lambda: generate-video]
      │          │
      │          ├─(3) 呼叫 Bedrock Image-to-Video API
      │          ├─(4) 建立 DynamoDB 任務記錄 (status: PROCESSING)
      │          │
      │          ↓ (Bedrock 完成)
      │          │
      │          ├─(5) 將 MP4 存至 S3 (videos bucket)
      │          └─(6) 更新 DynamoDB (status: COMPLETED, videoUrl)
      │
      ├─(7) 前端輪詢 GET /api/v1/video/tasks/{taskId}
      │
      └─(8) 住民端播放語音時，載入 videoUrl 循環播放
```

### 2.1 核心 AWS 資源

| 服務 | 資源名稱 | 用途 |
|------|----------|------|
| S3 | `{project}-images` | 存放家屬上傳的原始照片 |
| S3 | `{project}-videos` | 存放生成的 5 秒 MP4 |
| Lambda | `{project}-generate-video` | S3 Event 觸發，呼叫 Bedrock |
| DynamoDB | `{project}-video-tasks` | 記錄任務狀態與結果 URL |
| IAM Role | `{project}-lambda-role` | Lambda 執行角色 |
| CloudFront | (可選) | 加速影片分發 |

---

## 3. 資料模型

### 3.1 DynamoDB Table: video-tasks

| 欄位 | 類型 | 說明 |
|------|------|------|
| `taskId` (PK) | String | UUID，任務唯一識別碼 |
| `residentId` | String | 關聯的住民 ID |
| `familyMemberId` | String | 上傳者（家屬）ID |
| `imageKey` | String | S3 原始照片路徑 |
| `videoKey` | String | S3 生成影片路徑（完成後填入） |
| `videoUrl` | String | CloudFront/S3 公開播放 URL |
| `status` | String | `PENDING` → `PROCESSING` → `COMPLETED` / `FAILED` |
| `prompt` | String | 傳給 Bedrock 的動態描述（可選） |
| `errorMessage` | String | 失敗時的錯誤訊息 |
| `createdAt` | Number | 建立時間戳 |
| `updatedAt` | Number | 最後更新時間戳 |

### 3.2 索引
- **GSI**: `residentId-createdAt-index` — 查詢某住民的所有動圖，按時間排序

### 3.3 S3 Key 命名規則

```
images/{residentId}/{familyMemberId}/{timestamp}_{filename}
videos/{residentId}/{familyMemberId}/{taskId}.mp4
```

---

## 4. API 設計

整合進現有 Next.js API Routes：

| 方法 | 路徑 | 功能 |
|------|------|------|
| `POST` | `/api/v1/video/presigned-url` | 取得 S3 上傳預簽名 URL |
| `GET` | `/api/v1/video/tasks/{taskId}` | 查詢單一任務狀態 |
| `GET` | `/api/v1/video/residents/{residentId}/latest` | 取得某住民最新的動圖 URL |

### 4.1 POST /api/v1/video/presigned-url

**Request Body**:
```json
{
  "residentId": "string",
  "filename": "string"
}
```

**Response**:
```json
{
  "uploadUrl": "https://s3.amazonaws.com/...",
  "imageKey": "images/{residentId}/{familyMemberId}/{timestamp}_{filename}",
  "taskId": "uuid"
}
```

### 4.2 GET /api/v1/video/tasks/{taskId}

**Response**:
```json
{
  "taskId": "uuid",
  "status": "PROCESSING" | "COMPLETED" | "FAILED",
  "videoUrl": "https://...",
  "errorMessage": "string (if failed)"
}
```

### 4.3 GET /api/v1/video/residents/{residentId}/latest

**Response**:
```json
{
  "videoUrl": "https://...",
  "createdAt": 1234567890
}
```
或 `null`（若無動圖）

---

## 5. Lambda 函式設計

### 5.1 Lambda: generate-video

**觸發方式**：S3 Event（`s3:ObjectCreated:*` on images bucket）

**執行流程**：
1. 從 S3 Event 取得上傳的 `imageKey`
2. 解析 metadata（`residentId`, `familyMemberId`）— 透過 S3 key 命名規則
3. 建立 DynamoDB 記錄（status: `PROCESSING`）
4. 呼叫 Bedrock Image-to-Video API
5. 等待生成完成
6. 將 MP4 存至 videos bucket
7. 更新 DynamoDB（status: `COMPLETED`, `videoUrl`）

**Lambda 設定**：

| 項目 | 值 |
|------|------|
| Runtime | Python 3.12 或 Node.js 20.x |
| Timeout | 5 分鐘 |
| Memory | 512 MB |
| IAM Policy | S3 讀寫、DynamoDB 讀寫、Bedrock InvokeModel |

### 5.2 Bedrock 呼叫參數

**Model**: Amazon Nova Reel（或其他可用的 Image-to-Video 模型）

**Input**:
```json
{
  "taskType": "IMAGE_TO_VIDEO",
  "imageToVideoParams": {
    "images": [{
      "format": "jpeg",
      "source": {
        "s3Location": {
          "uri": "s3://bucket/key"
        }
      }
    }],
    "text": "gentle natural movement, soft breathing motion, warm family atmosphere"
  },
  "videoGenerationConfig": {
    "durationSeconds": 5,
    "fps": 24,
    "dimension": "1280x720"
  }
}
```

**預設 Prompt**：生成自然的微動效果（眨眼、微笑、輕微晃動），適合搭配語音播放。

---

## 6. 前端設計

### 6.1 家屬端 — 上傳照片頁面

**新增頁面**：`src/pages/family/VideoUpload.tsx`

**功能流程**：
1. 家屬選擇要設定的住民（從已授權列表）
2. 選擇/拍攝照片
3. 前端請求 presigned URL，直傳 S3
4. 顯示「處理中」狀態，輪詢任務進度
5. 完成後預覽生成的動圖

**UI 狀態**：

| 狀態 | 顯示 |
|------|------|
| `idle` | 上傳按鈕 |
| `uploading` | 上傳進度條 |
| `processing` | 骨架屏 + 「AI 生成中，約需 30 秒...」 |
| `completed` | 影片預覽 + 循環播放 |
| `failed` | 錯誤訊息 + 重試按鈕 |

**防呆機制**：
- 上傳/生成中按鈕 disabled
- 照片格式限制：JPEG、PNG
- 檔案大小限制：10MB

### 6.2 住民端（暫不實作）

僅保留 API 介面 `GET /api/v1/video/residents/{residentId}/latest`，供日後住民端串接使用。

### 6.3 Redux Store 擴展

新增 `videoApi` endpoints 到現有 RTK Query（`src/store/apiSlice.ts`）：

```ts
getPresignedUrl: builder.mutation<
  { uploadUrl: string; imageKey: string; taskId: string },
  { residentId: string; filename: string }
>

getTaskStatus: builder.query<VideoTask, string>

getLatestVideo: builder.query<{ videoUrl: string; createdAt: number } | null, string>
```

---

## 7. 錯誤處理

### 7.1 錯誤處理策略

| 情境 | 處理方式 |
|------|----------|
| S3 上傳失敗 | 前端顯示錯誤訊息，提供重試 |
| Lambda 執行失敗 | 寫入 DynamoDB status: `FAILED`，記錄 errorMessage |
| Bedrock API 失敗 | 重試 1 次，若仍失敗則標記 `FAILED` |
| Bedrock 超時 | Lambda timeout 前檢查，未完成則標記 `FAILED` |
| 照片格式不支援 | Lambda 驗證，不支援則直接標記 `FAILED` |

### 7.2 前端錯誤提示

| 錯誤碼 | 使用者訊息 |
|--------|------------|
| `UPLOAD_FAILED` | 「上傳失敗，請檢查網路後重試」 |
| `INVALID_FORMAT` | 「不支援的檔案格式，請上傳 JPG 或 PNG」 |
| `GENERATION_FAILED` | 「影片生成失敗，請稍後重試」 |
| `TIMEOUT` | 「生成時間過長，請稍後查看」 |

---

## 8. 實作範圍

### 8.1 本次實作
- [ ] AWS 資源建立（S3、Lambda、DynamoDB、IAM）
- [ ] Lambda 函式開發（generate-video）
- [ ] Next.js API Routes（presigned-url、task status、latest video）
- [ ] 家屬端上傳頁面（VideoUpload.tsx）
- [ ] RTK Query endpoints
- [ ] 錯誤處理與 UI 狀態

### 8.2 暫不實作
- 住民端影片播放整合（待住民端開發時再加）
- CloudFront CDN（可選，視效能需求）
- 成本控制機制（配額限制、快取等）

---

## 9. 部署建議

建議使用 **AWS CDK** 或 **SAM** 管理基礎設施：
- 版本控制 IaC 程式碼
- 方便跨環境部署（dev/staging/prod）
- 自動設定 S3 Event → Lambda 觸發

---

## 附錄：技術決策記錄

| 決策項目 | 選擇 | 理由 |
|----------|------|------|
| 架構模式 | 完整 AWS Serverless | 無需管理伺服器，按使用量計費 |
| 進度通知 | 輪詢（Polling） | 實作簡單，5 秒輪詢間隔可接受 |
| 觸發方式 | S3 Event 自動觸發 | 符合「上傳即生成」需求 |
| 資料庫 | DynamoDB | Serverless、低延遲、與 Lambda 整合佳 |
