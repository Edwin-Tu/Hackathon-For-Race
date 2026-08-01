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
import { useDispatch, useSelector } from 'react-redux';
import { setActiveTask, clearActiveTask, selectActiveTask } from '@/store/videoSlice';
import { VideoHistoryList } from '@/components/VideoHistoryList';
import { videoApi } from '@/store/videoApi';

type UploadStatus = 'idle' | 'uploading' | 'processing' | 'completed' | 'failed';

// 模擬住民列表（實際應從 API 取得）
const mockResidents = [
  { id: 'resident-001', name: '王爺爺' },
  { id: 'resident-002', name: '李奶奶' },
];

export default function VideoUpload() {
  const dispatch = useDispatch();
  const activeTask = useSelector(selectActiveTask);
  const [file, setFile] = useState<File | null>(null);
  const [residentId, setResidentId] = useState('');
  const [status, setStatus] = useState<UploadStatus>('idle');
  const [taskId, setTaskId] = useState<string | null>(null);
  const [videoUrl, setVideoUrl] = useState<string | null>(null);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  const [getPresignedUrl] = useGetPresignedUrlMutation();
  
  // 輪詢任務狀態
  const { data: taskStatus } = useGetTaskStatusQuery(taskId!, {
    skip: !taskId || status !== 'processing',
    pollingInterval: 5000, // 每 5 秒輪詢
  });

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

  // 頁面載入時，若有 activeTask 則恢復狀態
  useEffect(() => {
    if (activeTask && status === 'idle') {
      setResidentId(activeTask.residentId);
      setTaskId(activeTask.taskId);
      setStatus('processing');
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

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
      dispatch(setActiveTask({ residentId, taskId: result.taskId }));
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

      {/* 歷史影片列表 */}
      <VideoHistoryList residentId={residentId} />
    </Box>
  );
}
