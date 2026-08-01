import { createApi, fetchBaseQuery } from '@reduxjs/toolkit/query/react';
import type {
  PresignedUrlResponse,
  TaskStatusResponse,
  LatestVideoResponse,
  VideoHistoryResponse,
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

    // 取得住民歷史影片列表
    getVideoHistory: builder.query<VideoHistoryResponse, string>({
      query: (residentId) => `/residents/${residentId}/history`,
      providesTags: (result, error, residentId) => [
        { type: 'VideoTask', id: `history-${residentId}` },
      ],
    }),
  }),
});

export const {
  useGetPresignedUrlMutation,
  useGetTaskStatusQuery,
  useGetLatestVideoQuery,
  useGetVideoHistoryQuery,
} = videoApi;
