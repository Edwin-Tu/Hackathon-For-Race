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

// 歷史影片列表回應
export interface VideoHistoryResponse {
  tasks: VideoTask[];
}
