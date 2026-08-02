'use client';
import React, { useState, useRef, useCallback, useEffect } from 'react';
import {
  Container,
  Typography,
  Box,
  Paper,
  IconButton,
  CircularProgress,
  Chip,
  Avatar,
  Divider,
  Alert,
  Fade,
  Grow,
  LinearProgress,
  Skeleton,
} from '@mui/material';
import { useTheme, alpha, keyframes } from '@mui/material/styles';
import MicIcon from '@mui/icons-material/Mic';
import MicOffIcon from '@mui/icons-material/MicOff';
import StopIcon from '@mui/icons-material/Stop';
import VolumeUpIcon from '@mui/icons-material/VolumeUp';
import PersonIcon from '@mui/icons-material/Person';
import SmartToyIcon from '@mui/icons-material/SmartToy';
import GraphicEqIcon from '@mui/icons-material/GraphicEq';
import CheckCircleIcon from '@mui/icons-material/CheckCircle';
import ErrorIcon from '@mui/icons-material/Error';
import AutoAwesomeIcon from '@mui/icons-material/AutoAwesome';
import { useGetLatestVideoQuery } from '@/store/videoApi';

// 動畫定義
const ripple = keyframes`
  0% { transform: scale(1); opacity: 0.8; }
  100% { transform: scale(2.5); opacity: 0; }
`;

const pulse = keyframes`
  0%, 100% { transform: scale(1); }
  50% { transform: scale(1.05); }
`;

const wave = keyframes`
  0%, 100% { height: 8px; }
  50% { height: 24px; }
`;

// 對話訊息類型
interface Message {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  timestamp: Date;
  transcriptConfidence?: number;
  toolCalls?: ToolCall[];
}

// 工具呼叫類型
interface ToolCall {
  name: string;
  status: 'proposed' | 'executing' | 'succeeded' | 'failed';
  result?: string;
}

// 工具圖示
const toolIcons: Record<string, React.ReactElement> = {
  create_care_event: <CheckCircleIcon />,
  create_reminder: <AutoAwesomeIcon />,
  get_user_schedule: <GraphicEqIcon />,
  create_care_alert: <ErrorIcon />,
};

export default function VoiceInteraction() {
  const theme = useTheme();
  
  // 取得住民 ID（從 JWT 或 URL 參數）
  const residentId = 'resident-001'; // TODO: 從 auth context 取得
  
  // 取得最新動圖
  const { data: latestVideo, isLoading: videoLoading } = useGetLatestVideoQuery(residentId);
  
  // 影片播放 ref
  const videoRef = useRef<HTMLVideoElement>(null);
  
  // 錄音狀態
  const [isRecording, setIsRecording] = useState(false);
  const [isProcessing, setIsProcessing] = useState(false);
  const [isSpeaking, setIsSpeaking] = useState(false);

  // 對話歷史
  const [messages, setMessages] = useState<Message[]>([
    {
      id: '1',
      role: 'assistant',
      content: '您好！我是您的照護助理。您可以告訴我今天的狀況，或者需要我幫您記錄什麼事情。',
      timestamp: new Date(),
    },
  ]);

  // 目前的轉錄文字
  const [transcript, setTranscript] = useState('');
  const [error, setError] = useState<string | null>(null);

  // 音訊相關 refs
  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const audioChunksRef = useRef<Blob[]>([]);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  // 滾動到最新訊息
  const scrollToBottom = useCallback(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, []);

  // 開始錄音
  const startRecording = async () => {
    try {
      setError(null);
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      const mediaRecorder = new MediaRecorder(stream);
      mediaRecorderRef.current = mediaRecorder;
      audioChunksRef.current = [];

      mediaRecorder.ondataavailable = (event) => {
        if (event.data.size > 0) {
          audioChunksRef.current.push(event.data);
        }
      };

      mediaRecorder.onstop = async () => {
        const audioBlob = new Blob(audioChunksRef.current, { type: 'audio/webm' });
        stream.getTracks().forEach((track) => track.stop());
        await processAudio(audioBlob);
      };

      mediaRecorder.start();
      setIsRecording(true);
    } catch (err) {
      setError('無法存取麥克風，請確認已授權麥克風權限。');
      console.error('錄音錯誤:', err);
    }
  };

  // 停止錄音
  const stopRecording = () => {
    if (mediaRecorderRef.current && isRecording) {
      mediaRecorderRef.current.stop();
      setIsRecording(false);
    }
  };

  // 處理音訊（送至 Whisper 轉錄）
  const processAudio = async (audioBlob: Blob) => {
    setIsProcessing(true);
    setTranscript('正在辨識語音...');

    try {
      // 模擬 Whisper 轉錄結果
      await new Promise((resolve) => setTimeout(resolve, 1500));
      const mockTranscripts = [
        '我今天早上八點吃過藥了',
        '下午有出去散步半小時',
        '明天下午三點要回診，幫我記得',
        '今天有什麼事情？',
        '我有點不舒服，想通知照護人員',
      ];
      const mockText = mockTranscripts[Math.floor(Math.random() * mockTranscripts.length)] ?? '';

      setTranscript(mockText);

      // 新增使用者訊息
      const userMessage: Message = {
        id: Date.now().toString(),
        role: 'user',
        content: mockText,
        timestamp: new Date(),
        transcriptConfidence: 0.95,
      };
      setMessages((prev) => [...prev, userMessage]);

      // 處理 Agent 回應
      await processAgentResponse(mockText);
    } catch (err) {
      setError('語音辨識失敗，請重試。');
      console.error('處理音訊錯誤:', err);
    } finally {
      setIsProcessing(false);
      setTranscript('');
    }
  };

  // 處理 Agent 回應
  const processAgentResponse = async (userInput: string) => {
    await new Promise((resolve) => setTimeout(resolve, 1000));

    let responseContent = '';
    let toolCalls: ToolCall[] = [];

    if (userInput.includes('吃過藥') || userInput.includes('服藥')) {
      toolCalls = [{ name: 'create_care_event', status: 'succeeded', result: '已記錄用藥事件' }];
      responseContent = '好的，已經幫您記錄今天早上八點的用藥紀錄。';
    } else if (userInput.includes('散步') || userInput.includes('運動')) {
      toolCalls = [{ name: 'create_care_event', status: 'succeeded', result: '已記錄活動事件' }];
      responseContent = '好的，已記錄您今天下午散步半小時的活動紀錄。保持運動很棒！';
    } else if (userInput.includes('回診') || userInput.includes('提醒')) {
      toolCalls = [{ name: 'create_reminder', status: 'succeeded', result: '已建立提醒' }];
      responseContent = '好的，已經幫您設定明天下午三點的回診提醒。需要我在出發前半小時再提醒您嗎？';
    } else if (userInput.includes('什麼事') || userInput.includes('行程')) {
      toolCalls = [{ name: 'get_user_schedule', status: 'succeeded', result: '查詢成功' }];
      responseContent = '讓我查看一下...今天下午兩點有復健課程，晚上六點記得服用降血壓藥。';
    } else if (userInput.includes('不舒服') || userInput.includes('通知照護')) {
      toolCalls = [{ name: 'create_care_alert', status: 'succeeded', result: '已發送警示' }];
      responseContent = '我已經通知照護人員您的狀況。請您先坐下休息，照護人員很快會過來。請問是哪裡不舒服？';
    } else {
      responseContent = '好的，我明白了。還有什麼需要我幫忙的嗎？';
    }

    const assistantMessage: Message = {
      id: (Date.now() + 1).toString(),
      role: 'assistant',
      content: responseContent,
      timestamp: new Date(),
      toolCalls,
    };

    setMessages((prev) => [...prev, assistantMessage]);
    scrollToBottom();

    // 播放 TTS
    await speakText(responseContent);
  };

  // TTS 語音播放
  const speakText = async (text: string) => {
    if ('speechSynthesis' in window) {
      setIsSpeaking(true);
      const utterance = new SpeechSynthesisUtterance(text);
      utterance.lang = 'zh-TW';
      utterance.rate = 0.9;
      utterance.onend = () => setIsSpeaking(false);
      utterance.onerror = () => setIsSpeaking(false);
      window.speechSynthesis.speak(utterance);
    }
  };

  // 停止 TTS
  const stopSpeaking = () => {
    if ('speechSynthesis' in window) {
      window.speechSynthesis.cancel();
      setIsSpeaking(false);
    }
  };

  // 音波動畫元件
  const SoundWave = () => (
    <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5, height: 24 }}>
      {[0, 1, 2, 3, 4].map((i) => (
        <Box
          key={i}
          sx={{
            width: 4,
            bgcolor: 'primary.main',
            borderRadius: 2,
            animation: `${wave} 0.8s ease-in-out infinite`,
            animationDelay: `${i * 0.1}s`,
          }}
        />
      ))}
    </Box>
  );

  return (
    <Container maxWidth="md" sx={{ py: 3 }}>
      {/* 動圖顯示區域 */}
      <Fade in timeout={300}>
        <Box 
          sx={{ 
            mb: 3, 
            display: 'flex', 
            justifyContent: 'center',
            position: 'relative',
          }}
        >
          {videoLoading ? (
            <Skeleton 
              variant="rounded" 
              width={280} 
              height={280} 
              sx={{ borderRadius: '50%' }}
            />
          ) : latestVideo?.videoUrl ? (
            <Box
              sx={{
                position: 'relative',
                width: 280,
                height: 280,
                borderRadius: '50%',
                overflow: 'hidden',
                boxShadow: isSpeaking 
                  ? `0 0 40px ${alpha(theme.palette.primary.main, 0.5)}`
                  : `0 8px 32px ${alpha(theme.palette.common.black, 0.15)}`,
                border: `4px solid ${isSpeaking ? theme.palette.primary.main : theme.palette.divider}`,
                transition: 'all 0.3s ease',
              }}
            >
              <video
                ref={videoRef}
                src={latestVideo.videoUrl}
                autoPlay
                loop
                muted
                playsInline
                style={{
                  width: '100%',
                  height: '100%',
                  objectFit: 'cover',
                }}
              />
              {/* 說話時的動畫光環 */}
              {isSpeaking && (
                <Box
                  sx={{
                    position: 'absolute',
                    top: -4,
                    left: -4,
                    right: -4,
                    bottom: -4,
                    borderRadius: '50%',
                    border: `3px solid ${theme.palette.primary.main}`,
                    animation: `${pulse} 1s ease-in-out infinite`,
                  }}
                />
              )}
            </Box>
          ) : (
            <Avatar
              sx={{
                width: 280,
                height: 280,
                bgcolor: alpha(theme.palette.primary.main, 0.1),
                color: theme.palette.primary.main,
                fontSize: 120,
                boxShadow: `0 8px 32px ${alpha(theme.palette.common.black, 0.1)}`,
              }}
            >
              <SmartToyIcon sx={{ fontSize: 120 }} />
            </Avatar>
          )}
        </Box>
      </Fade>

      {/* 頁面標題 */}
      <Fade in timeout={300}>
        <Box sx={{ mb: 3, textAlign: 'center' }}>
          <Typography variant="h4" sx={{ fontWeight: 700 }}>
            語音互動
          </Typography>
          <Typography variant="body2" color="text.secondary">
            按下麥克風按鈕開始說話，系統會記錄您的生活事件並回覆
          </Typography>
        </Box>
      </Fade>

      {/* 錯誤提示 */}
      <Fade in={!!error}>
        <Box>
          {error && (
            <Alert 
              severity="error" 
              sx={{ mb: 2 }} 
              onClose={() => setError(null)}
              variant="filled"
            >
              {error}
            </Alert>
          )}
        </Box>
      </Fade>

      {/* 對話歷史 */}
      <Grow in timeout={400}>
        <Paper
          sx={{
            height: '35vh',
            overflow: 'auto',
            p: 3,
            mb: 3,
            bgcolor: alpha(theme.palette.background.default, 0.5),
            border: `1px solid ${theme.palette.divider}`,
          }}
        >
          {messages.map((msg, index) => (
            <Fade in timeout={300} key={msg.id}>
              <Box
                sx={{
                  display: 'flex',
                  flexDirection: msg.role === 'user' ? 'row-reverse' : 'row',
                  mb: 3,
                  gap: 1.5,
                }}
              >
                <Avatar
                  sx={{
                    bgcolor: msg.role === 'user' ? 'primary.main' : 'secondary.main',
                    width: 40,
                    height: 40,
                  }}
                >
                  {msg.role === 'user' ? <PersonIcon /> : <SmartToyIcon />}
                </Avatar>
                <Box sx={{ maxWidth: '75%' }}>
                  <Paper
                    elevation={0}
                    sx={{
                      p: 2,
                      bgcolor: msg.role === 'user' 
                        ? theme.palette.primary.main
                        : theme.palette.background.paper,
                      color: msg.role === 'user' 
                        ? theme.palette.primary.contrastText 
                        : theme.palette.text.primary,
                      borderRadius: 3,
                      borderTopRightRadius: msg.role === 'user' ? 4 : 24,
                      borderTopLeftRadius: msg.role === 'user' ? 24 : 4,
                      boxShadow: msg.role === 'user'
                        ? `0 4px 12px ${alpha(theme.palette.primary.main, 0.3)}`
                        : '0 2px 8px rgba(0,0,0,0.08)',
                    }}
                  >
                    <Typography variant="body1" color="text.primary" sx={{ lineHeight: 1.7 }}>
                      {msg.content}
                    </Typography>

                    {/* 顯示工具呼叫狀態 */}
                    {msg.toolCalls && msg.toolCalls.length > 0 && (
                      <Box sx={{ mt: 1.5, pt: 1.5, borderTop: `1px solid ${alpha(theme.palette.divider, 0.3)}` }}>
                        {msg.toolCalls.map((tool, idx) => (
                          <Chip
                            key={idx}
                            size="small"
                            icon={toolIcons[tool.name] || <AutoAwesomeIcon />}
                            label={tool.result || tool.name}
                            color={tool.status === 'succeeded' ? 'success' : 'default'}
                            variant="outlined"
                            sx={{ 
                              mr: 0.5, 
                              mt: 0.5,
                              bgcolor: alpha(theme.palette.success.main, 0.1),
                            }}
                          />
                        ))}
                      </Box>
                    )}
                  </Paper>
                  <Typography 
                    variant="caption" 
                    color="text.secondary" 
                    sx={{ 
                      ml: msg.role === 'user' ? 0 : 1.5,
                      mr: msg.role === 'user' ? 1.5 : 0,
                      mt: 0.5,
                      display: 'block',
                      textAlign: msg.role === 'user' ? 'right' : 'left',
                    }}
                  >
                    {msg.timestamp.toLocaleTimeString('zh-TW', { hour: '2-digit', minute: '2-digit' })}
                    {msg.transcriptConfidence && (
                      <span> · 辨識度 {Math.round(msg.transcriptConfidence * 100)}%</span>
                    )}
                  </Typography>
                </Box>
              </Box>
            </Fade>
          ))}
          <div ref={messagesEndRef} />
        </Paper>
      </Grow>

      {/* 轉錄狀態顯示 */}
      <Fade in={isProcessing || !!transcript}>
        <Box>
          {(isProcessing || transcript) && (
            <Paper 
              sx={{ 
                p: 2, 
                mb: 3, 
                bgcolor: alpha(theme.palette.info.main, 0.08),
                border: `1px solid ${alpha(theme.palette.info.main, 0.2)}`,
              }}
            >
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 1.5 }}>
                {isProcessing && <CircularProgress size={20} color="info" />}
                <Typography variant="body2" color="info.main" sx={{ fontWeight: 500 }}>
                  {transcript || '處理中...'}
                </Typography>
              </Box>
              {isProcessing && (
                <LinearProgress 
                  sx={{ mt: 1.5, borderRadius: 1 }} 
                  color="info"
                />
              )}
            </Paper>
          )}
        </Box>
      </Fade>

      {/* 控制按鈕 */}
      <Box sx={{ display: 'flex', justifyContent: 'center', gap: 3, alignItems: 'center' }}>
        {/* 錄音按鈕 */}
        <Box sx={{ position: 'relative' }}>
          {/* 錄音中的漣漪效果 */}
          {isRecording && (
            <>
              <Box
                sx={{
                  position: 'absolute',
                  top: '50%',
                  left: '50%',
                  width: 88,
                  height: 88,
                  borderRadius: '50%',
                  bgcolor: alpha(theme.palette.error.main, 0.3),
                  transform: 'translate(-50%, -50%)',
                  animation: `${ripple} 1.5s ease-out infinite`,
                }}
              />
              <Box
                sx={{
                  position: 'absolute',
                  top: '50%',
                  left: '50%',
                  width: 88,
                  height: 88,
                  borderRadius: '50%',
                  bgcolor: alpha(theme.palette.error.main, 0.3),
                  transform: 'translate(-50%, -50%)',
                  animation: `${ripple} 1.5s ease-out infinite 0.5s`,
                }}
              />
            </>
          )}
          
          <IconButton
            onClick={isRecording ? stopRecording : startRecording}
            disabled={isProcessing || isSpeaking}
            sx={{
              width: 88,
              height: 88,
              bgcolor: isRecording ? 'error.main' : 'primary.main',
              color: 'white',
              boxShadow: isRecording 
                ? `0 8px 24px ${alpha(theme.palette.error.main, 0.5)}`
                : `0 8px 24px ${alpha(theme.palette.primary.main, 0.4)}`,
              transition: 'all 0.3s ease',
              animation: isRecording ? `${pulse} 1s ease-in-out infinite` : 'none',
              '&:hover': {
                bgcolor: isRecording ? 'error.dark' : 'primary.dark',
                transform: 'scale(1.05)',
              },
              '&:disabled': {
                bgcolor: 'grey.400',
                boxShadow: 'none',
              },
            }}
          >
            {isRecording ? (
              <StopIcon sx={{ fontSize: 40 }} />
            ) : (
              <MicIcon sx={{ fontSize: 40 }} />
            )}
          </IconButton>
        </Box>

        {/* TTS 控制按鈕 */}
        <Fade in={isSpeaking}>
          <Box>
            {isSpeaking && (
              <IconButton
                onClick={stopSpeaking}
                sx={{
                  width: 64,
                  height: 64,
                  bgcolor: 'warning.main',
                  color: 'white',
                  boxShadow: `0 6px 20px ${alpha(theme.palette.warning.main, 0.4)}`,
                  animation: `${pulse} 1s ease-in-out infinite`,
                  '&:hover': { 
                    bgcolor: 'warning.dark',
                  },
                }}
              >
                <VolumeUpIcon sx={{ fontSize: 30 }} />
              </IconButton>
            )}
          </Box>
        </Fade>
      </Box>

      {/* 狀態提示 */}
      <Box sx={{ textAlign: 'center', mt: 3 }}>
        <Chip
          icon={
            isRecording ? <GraphicEqIcon /> : 
            isProcessing ? <CircularProgress size={16} color="inherit" /> :
            isSpeaking ? <VolumeUpIcon /> :
            <MicIcon />
          }
          label={
            isRecording
              ? '錄音中...說完後按停止'
              : isProcessing
                ? '正在處理...'
                : isSpeaking
                  ? '播放回覆中...'
                  : '按下麥克風按鈕開始說話'
          }
          color={
            isRecording ? 'error' : 
            isProcessing ? 'info' : 
            isSpeaking ? 'warning' : 
            'default'
          }
          variant={isRecording || isProcessing || isSpeaking ? 'filled' : 'outlined'}
          sx={{ 
            px: 2, 
            py: 2.5,
            fontSize: '0.9rem',
            fontWeight: 500,
          }}
        />
      </Box>
    </Container>
  );
}
