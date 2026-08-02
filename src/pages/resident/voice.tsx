'use client';
import { useEffect, useRef, useState } from 'react';
import {
  Alert,
  Box,
  Button,
  Dialog,
  DialogActions,
  DialogContent,
  DialogTitle,
  Drawer,
  IconButton,
  List,
  ListItemButton,
  ListItemIcon,
  ListItemText,
  Snackbar,
  TextField,
  Typography,
} from '@mui/material';
import { keyframes } from '@mui/material/styles';
import { useRouter } from 'next/router';
import CloseIcon from '@mui/icons-material/Close';
import LogoutIcon from '@mui/icons-material/Logout';
import MenuIcon from '@mui/icons-material/Menu';
import SettingsIcon from '@mui/icons-material/Settings';
import { getUserInfo } from '../../utils/auth';

// ══════════════════════════════════════════════
// 可更換的提醒 GIF（後台 / 家屬端可在這裡替換或擴充）
// ══════════════════════════════════════════════
const REMINDER_GIFS = [
  { url: 'https://media.giphy.com/media/l0HlBO7eyXzSZkJri/giphy.gif', label: '貼心小美' },
  { url: 'https://media.giphy.com/media/3o7abKhOpu0NwenH3O/giphy.gif', label: '活力小志' },
  { url: 'https://media.giphy.com/media/xT9IgG50Lg7russbDa/giphy.gif', label: '溫暖大明' },
];

// ══════════════════════════════════════════════
// 後台 AI 排程（目前於前端模擬，之後可改為 API / SSE 推送）
// ══════════════════════════════════════════════
interface QuestionScene {
  kind: 'question';
  speaker?: { name: string; gifUrl: string };
  question: string;
  yesFeedback: string;
  noFeedback: string;
}

interface ReminderScene {
  kind: 'reminder';
  title: string;
  message: string;
  duration: number;
}

interface WaitScene {
  kind: 'wait';
  duration: number;
}

type Scene = QuestionScene | ReminderScene | WaitScene;

const AI_SCHEDULE: Scene[] = [
  { kind: 'wait', duration: 6000 },
  {
    kind: 'question',
    speaker: { name: '女兒小美', gifUrl: REMINDER_GIFS[0]!.url },
    question: '今天早上的藥\n吃了嗎？',
    yesFeedback: '太好了，繼續保持！',
    noFeedback: '記得待會補吃喔！',
  },
  { kind: 'wait', duration: 4000 },
  {
    kind: 'reminder',
    title: '服藥提醒',
    message: '記得喝口水，準備吃下一餐的藥喔！',
    duration: 8000,
  },
  { kind: 'wait', duration: 6000 },
  {
    kind: 'question',
    speaker: { name: '孫子小志', gifUrl: REMINDER_GIFS[1]!.url },
    question: '今天有好好喝水嗎？',
    yesFeedback: '很棒，繼續補充水分！',
    noFeedback: '記得去倒杯水喔！',
  },
  { kind: 'wait', duration: 4000 },
  {
    kind: 'reminder',
    title: '健康提醒',
    message: '下午三點記得散步，活動筋骨喔！',
    duration: 8000,
  },
  { kind: 'wait', duration: 6000 },
  {
    kind: 'question',
    speaker: { name: '兒子大明', gifUrl: REMINDER_GIFS[2]!.url },
    question: '今天心情還不錯嗎？',
    yesFeedback: '太好了，保持好心情！',
    noFeedback: '沒關係，我在這裡陪著您！',
  },
  { kind: 'wait', duration: 4000 },
];

type View =
  | { type: 'blank' }
  | { type: 'question'; scene: QuestionScene }
  | { type: 'reminder'; scene: ReminderScene };

const TITLE_OPTIONS = ['👴 爺爺', '👵 奶奶', '🧑 先生', '👩 女士', '🙂 其他'];
const FONT_OPTIONS = [
  { key: 'small', label: '小' },
  { key: 'medium', label: '中' },
  { key: 'large', label: '大' },
];

function getGreeting() {
  const h = new Date().getHours();
  if (h >= 5 && h < 12) return { icon: '🌅', text: '早安' };
  if (h >= 12 && h < 18) return { icon: '☀️', text: '午安' };
  return { icon: '🌙', text: '晚安' };
}

const sosPulse = keyframes`
  0%, 100% { transform: scale(1); box-shadow: 0 4px 20px rgba(220,38,38,0.6); }
  50% { transform: scale(1.08); box-shadow: 0 4px 32px rgba(220,38,38,0.9); }
`;

// ══════════════════════════════════════════════
// 二選一互動卡（是 / 否 大按鈕）
// ══════════════════════════════════════════════
function DualChoiceCard({
  scene,
  busy,
  feedback,
  onAnswer,
}: {
  scene: QuestionScene;
  busy: boolean;
  feedback: { value: 'yes' | 'no'; text: string } | null;
  onAnswer: (value: 'yes' | 'no') => void;
}) {
  return (
    <Box
      sx={{
        borderRadius: '24px',
        overflow: 'hidden',
        border: '2px solid',
        borderColor: 'divider',
        boxShadow: '0 6px 28px rgba(0,0,0,0.10)',
        bgcolor: '#fff',
      }}
    >
      {scene.speaker && (
        <Box sx={{ position: 'relative', bgcolor: '#0f172a', height: 200, overflow: 'hidden' }}>
          <img
            src={scene.speaker.gifUrl}
            alt={scene.speaker.name}
            style={{ width: '100%', height: '100%', objectFit: 'cover', opacity: 0.85 }}
            onError={(e) => {
              e.currentTarget.style.display = 'none';
            }}
          />
          <Box
            sx={{
              position: 'absolute',
              bottom: 0,
              left: 0,
              right: 0,
              background: 'linear-gradient(transparent, rgba(0,0,0,0.75))',
              p: '1.2rem 1.4rem 0.8rem',
            }}
          >
            <Typography sx={{ fontSize: '1.5rem', fontWeight: 900, color: '#fbbf24' }}>
              {scene.speaker.name}
            </Typography>
            <Typography sx={{ fontSize: '1rem', color: 'rgba(255,255,255,0.7)' }}>
              想問您：
            </Typography>
          </Box>
        </Box>
      )}

      <Box sx={{ bgcolor: '#1e293b', px: 3, py: 2.5 }}>
        <Typography
          sx={{
            fontSize: '1.9rem',
            fontWeight: 900,
            color: '#fff',
            lineHeight: 1.4,
            whiteSpace: 'pre-line',
            textAlign: 'center',
          }}
        >
          {scene.question}
        </Typography>
      </Box>

      <Box sx={{ display: 'grid', gridTemplateColumns: '1fr 1fr', minHeight: 150 }}>
        <Button
          onClick={() => onAnswer('yes')}
          disabled={busy}
          sx={{
            height: 150,
            borderRadius: 0,
            flexDirection: 'column',
            gap: 0.5,
            bgcolor: '#16a34a',
            color: '#fff',
            '&:hover': { bgcolor: '#15803d' },
            '&.Mui-disabled': { bgcolor: '#4ade80', color: '#fff', opacity: 0.9 },
          }}
        >
          <Box component="span" sx={{ fontSize: '3.5rem', lineHeight: 1 }}>
            ⭕
          </Box>
          <Box component="span" sx={{ fontSize: '2.2rem', fontWeight: 900, lineHeight: 1.2 }}>
            是
          </Box>
        </Button>
        <Button
          onClick={() => onAnswer('no')}
          disabled={busy}
          sx={{
            height: 150,
            borderRadius: 0,
            borderLeft: '3px solid rgba(255,255,255,0.3)',
            flexDirection: 'column',
            gap: 0.5,
            bgcolor: '#dc2626',
            color: '#fff',
            '&:hover': { bgcolor: '#b91c1c' },
            '&.Mui-disabled': { bgcolor: '#f87171', color: '#fff', opacity: 0.9 },
          }}
        >
          <Box component="span" sx={{ fontSize: '3.5rem', lineHeight: 1 }}>
            ❌
          </Box>
          <Box component="span" sx={{ fontSize: '2.2rem', fontWeight: 900, lineHeight: 1.2 }}>
            否
          </Box>
        </Button>
      </Box>

      {feedback && (
        <Box
          sx={{
            bgcolor: feedback.value === 'yes' ? '#dcfce7' : '#fee2e2',
            p: 2,
            textAlign: 'center',
          }}
        >
          <Typography
            sx={{
              fontSize: '1.7rem',
              fontWeight: 900,
              color: feedback.value === 'yes' ? '#15803d' : '#dc2626',
            }}
          >
            {feedback.value === 'yes' ? '⭕ 已選擇：是' : '❌ 已選擇：否'} — {feedback.text}
          </Typography>
        </Box>
      )}
    </Box>
  );
}

// ══════════════════════════════════════════════
// GIF 提醒卡（後台 AI 提醒時顯示，可更換 GIF）
// ══════════════════════════════════════════════
function ReminderCard({
  scene,
  gifUrl,
  onDismiss,
}: {
  scene: ReminderScene;
  gifUrl: string;
  onDismiss: () => void;
}) {
  return (
    <Box
      sx={{
        borderRadius: '24px',
        overflow: 'hidden',
        border: '2px solid',
        borderColor: 'divider',
        boxShadow: '0 6px 28px rgba(0,0,0,0.10)',
        bgcolor: '#fff',
      }}
    >
      <Box sx={{ position: 'relative', bgcolor: '#0f172a', height: 280, overflow: 'hidden' }}>
        <img
          src={gifUrl}
          alt="提醒動畫"
          style={{ width: '100%', height: '100%', objectFit: 'cover' }}
          onError={(e) => {
            e.currentTarget.style.display = 'none';
          }}
        />
      </Box>
      <Box sx={{ p: 3, textAlign: 'center' }}>
        <Typography sx={{ fontSize: '1.7rem', fontWeight: 900, color: '#1e40af' }}>
          🔔 {scene.title}
        </Typography>
        <Typography sx={{ fontSize: '1.3rem', fontWeight: 700, color: 'text.secondary', mt: 1 }}>
          {scene.message}
        </Typography>
        <Button
          variant="contained"
          color="primary"
          onClick={onDismiss}
          sx={{ mt: 2.5, px: 5, py: 1.5, fontSize: '1.4rem', fontWeight: 800, borderRadius: 3 }}
        >
          我知道了
        </Button>
      </Box>
    </Box>
  );
}

// ══════════════════════════════════════════════
// SOS 全螢幕畫面
// ══════════════════════════════════════════════
function SOSScreen({ onCancel }: { onCancel: () => void }) {
  const [triggered, setTriggered] = useState<Record<number, boolean>>({});
  const ACTIONS = [
    { label: '📞 通知家屬 — 女兒小美' },
    { label: '👩‍⚕️ 通知照護員' },
    { label: '🚑 撥打緊急聯絡人' },
  ];
  return (
    <Box
      sx={{
        position: 'fixed',
        inset: 0,
        zIndex: 1300,
        bgcolor: '#dc2626',
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        justifyContent: 'center',
        gap: 2,
        p: 3,
      }}
    >
      <Box sx={{ fontSize: '5rem', animation: `${sosPulse} 1s infinite` }}>🆘</Box>
      <Typography sx={{ fontSize: '2.6rem', fontWeight: 900, color: '#fff', textAlign: 'center' }}>
        緊急求助中
      </Typography>
      <Typography sx={{ fontSize: '1.5rem', color: 'rgba(255,255,255,0.85)', textAlign: 'center' }}>
        請點下方按鈕通知相關人員
        <br />
        請保持冷靜
      </Typography>
      <Box
        sx={{ display: 'flex', flexDirection: 'column', gap: 1.5, width: '100%', maxWidth: 380 }}
      >
        {ACTIONS.map((a, i) => {
          const done = !!triggered[i];
          return (
            <Button
              key={i}
              onClick={() => !done && setTriggered((p) => ({ ...p, [i]: true }))}
              disabled={done}
              sx={{
                width: '100%',
                borderRadius: 3,
                py: 2,
                px: 3,
                justifyContent: 'space-between',
                bgcolor: done ? 'rgba(255,255,255,0.35)' : 'rgba(255,255,255,0.15)',
                border: `2px solid ${done ? 'rgba(255,255,255,0.7)' : 'rgba(255,255,255,0.3)'}`,
                color: '#fff',
                fontSize: '1.5rem',
                fontWeight: 900,
                textTransform: 'none',
                '&.Mui-disabled': { color: '#fff', opacity: 1 },
              }}
            >
              <span>{a.label}</span>
              <span style={{ fontSize: '1.8rem' }}>{done ? '✅' : '▶'}</span>
            </Button>
          );
        })}
      </Box>
      {Object.keys(triggered).length > 0 && (
        <Box
          sx={{
            bgcolor: 'rgba(255,255,255,0.2)',
            borderRadius: 3,
            p: 2,
            px: 3,
            textAlign: 'center',
          }}
        >
          <Typography sx={{ fontSize: '1.4rem', fontWeight: 800, color: '#fff' }}>
            ✅ 已通知 {Object.keys(triggered).length} 位 — 幫助正在趕來！
          </Typography>
        </Box>
      )}
      <Button
        variant="contained"
        onClick={onCancel}
        sx={{
          mt: 1,
          px: 5,
          py: 1.5,
          fontSize: '1.5rem',
          fontWeight: 800,
          borderRadius: 3,
          bgcolor: 'rgba(255,255,255,0.2)',
          color: '#fff',
          '&:hover': { bgcolor: 'rgba(255,255,255,0.3)' },
        }}
      >
        取消 / 我沒事了
      </Button>
    </Box>
  );
}

export default function ElderVoice() {
  const router = useRouter();

  // 畫面狀態：空白 / 二選一 / GIF 提醒
  const [view, setView] = useState<View>({ type: 'blank' });
  const [busy, setBusy] = useState(false);
  const [feedback, setFeedback] = useState<{ value: 'yes' | 'no'; text: string } | null>(null);

  // 側邊欄 / 對話框
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [settingsOpen, setSettingsOpen] = useState(false);
  const [logoutOpen, setLogoutOpen] = useState(false);
  const [sosActive, setSosActive] = useState(false);
  const [toast, setToast] = useState('');

  // 帳號 / 個人化設定
  const [userName, setUserName] = useState('王');
  const [userTitle, setUserTitle] = useState('👵 奶奶');
  const [fontSize, setFontSize] = useState('medium');
  const [gifKey, setGifKey] = useState(REMINDER_GIFS[0]!.url);

  // 排程器 refs
  const sceneIndexRef = useRef(0);
  const timerRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  const fontScale = fontSize === 'small' ? 0.85 : fontSize === 'large' ? 1.18 : 1;

  // 讀取個人化設定
  useEffect(() => {
    const info = getUserInfo(localStorage.getItem('auth'));
    setUserName(localStorage.getItem('userName') || info?.displayName || '王');
    setUserTitle(localStorage.getItem('userTitle') || '👵 奶奶');
    setFontSize(localStorage.getItem('fontSize') || 'medium');
    setGifKey(localStorage.getItem('reminderGif') || REMINDER_GIFS[0]!.url);
  }, []);

  // 字體縮放套用到根元素
  useEffect(() => {
    document.documentElement.style.fontSize = `${fontScale * 16}px`;
    return () => {
      document.documentElement.style.fontSize = '';
    };
  }, [fontScale]);

  // 依序執行後台 AI 排程
  function renderScene(index: number) {
    const scene = AI_SCHEDULE[index % AI_SCHEDULE.length]!;
    sceneIndexRef.current = index;
    setBusy(false);
    setFeedback(null);
    if (scene.kind === 'wait') {
      setView({ type: 'blank' });
      timerRef.current = setTimeout(() => renderScene(index + 1), scene.duration);
    } else if (scene.kind === 'question') {
      setView({ type: 'question', scene });
    } else {
      setView({ type: 'reminder', scene });
      timerRef.current = setTimeout(() => renderScene(index + 1), scene.duration);
    }
  }

  useEffect(() => {
    renderScene(0);
    return () => {
      if (timerRef.current) clearTimeout(timerRef.current);
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  // 回答是 / 否（模擬回傳後台 AI）
  const handleAnswer = (value: 'yes' | 'no') => {
    if (busy || view.type !== 'question') return;
    const scene = view.scene;
    setBusy(true);
    const text = value === 'yes' ? scene.yesFeedback : scene.noFeedback;
    setFeedback({ value, text });
    setToast(
      value === 'yes' ? '已選擇「是」，回覆已傳送給照護人員' : '已選擇「否」，回覆已傳送給照護人員',
    );
    if (timerRef.current) clearTimeout(timerRef.current);
    timerRef.current = setTimeout(() => renderScene(sceneIndexRef.current + 1), 2200);
  };

  const dismissReminder = () => {
    if (timerRef.current) clearTimeout(timerRef.current);
    renderScene(sceneIndexRef.current + 1);
  };

  const saveSettings = () => {
    localStorage.setItem('userName', userName);
    localStorage.setItem('userTitle', userTitle);
    localStorage.setItem('fontSize', fontSize);
    localStorage.setItem('reminderGif', gifKey);
    setSettingsOpen(false);
    setToast('設定已儲存');
  };

  const handleLogout = () => {
    localStorage.removeItem('auth');
    document.cookie = 'auth=; path=/; expires=Thu, 01 Jan 1970 00:00:00 GMT';
    router.push('/login');
  };

  if (sosActive) {
    return <SOSScreen onCancel={() => setSosActive(false)} />;
  }

  const greeting = getGreeting();

  return (
    <Box
      sx={{ minHeight: '100vh', bgcolor: '#f0f7ff', fontFamily: '"Microsoft JhengHei", system-ui' }}
    >
      {/* 頂部列 */}
      <Box
        sx={{
          position: 'sticky',
          top: 0,
          zIndex: 100,
          bgcolor: '#ffffff',
          borderBottom: '1px solid #e2e8f0',
          px: 2,
          py: 1.2,
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          maxWidth: 640,
          mx: 'auto',
          width: '100%',
          boxSizing: 'border-box',
        }}
      >
        <IconButton
          onClick={() => setSidebarOpen(true)}
          sx={{ bgcolor: '#f1f5f9', borderRadius: 2, p: 1.5, '&:hover': { bgcolor: '#e2e8f0' } }}
        >
          <MenuIcon sx={{ fontSize: 32 }} />
        </IconButton>
        <Typography sx={{ fontSize: '1.4rem', fontWeight: 900, color: '#1e293b' }}>
          {greeting.icon} {userName} {userTitle}
        </Typography>
        <Button
          onClick={() => setSosActive(true)}
          sx={{
            bgcolor: '#fee2e2',
            border: '2px solid #fca5a5',
            borderRadius: 2,
            px: 1.6,
            py: 0.8,
            fontSize: '1.2rem',
            fontWeight: 800,
            color: '#dc2626',
            minWidth: 0,
            '&:hover': { bgcolor: '#fecaca' },
          }}
        >
          🆘
        </Button>
      </Box>

      {/* 主內容：常態為空白，AI 事件時顯示卡片 */}
      <Box
        sx={{
          maxWidth: 640,
          mx: 'auto',
          px: 2,
          py: 2,
          minHeight: 'calc(100vh - 76px)',
          display: 'flex',
          flexDirection: 'column',
        }}
      >
        {view.type === 'question' && (
          <DualChoiceCard
            scene={view.scene}
            busy={busy}
            feedback={feedback}
            onAnswer={handleAnswer}
          />
        )}
        {view.type === 'reminder' && (
          <ReminderCard scene={view.scene} gifUrl={gifKey} onDismiss={dismissReminder} />
        )}
      </Box>

      {/* 隱藏側邊欄：帳號設置、登出 */}
      <Drawer
        anchor="left"
        open={sidebarOpen}
        onClose={() => setSidebarOpen(false)}
        slotProps={{ paper: { sx: { width: 300, bgcolor: '#0f172a' } } }}
      >
        <Box sx={{ display: 'flex', flexDirection: 'column', height: '100%' }}>
          {/* 帳號資訊 */}
          <Box
            sx={{
              p: '2.5rem 1.5rem 1.5rem',
              borderBottom: '1px solid rgba(255,255,255,0.08)',
              background: 'linear-gradient(180deg, #1d4ed8 0%, #1e293b 100%)',
            }}
          >
            <Box
              sx={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between' }}
            >
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 1.5 }}>
                <Box
                  sx={{
                    width: 52,
                    height: 52,
                    borderRadius: '50%',
                    bgcolor: 'rgba(255,255,255,0.2)',
                    border: '2px solid rgba(255,255,255,0.4)',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    fontSize: '1.6rem',
                  }}
                >
                  {userTitle?.split(' ')[0] || '👤'}
                </Box>
                <Box>
                  <Typography sx={{ fontSize: '1.5rem', fontWeight: 900, color: '#fff' }}>
                    {userName || '使用者'}
                  </Typography>
                  <Typography sx={{ fontSize: '1rem', color: 'rgba(255,255,255,0.6)' }}>
                    {userTitle}
                  </Typography>
                </Box>
              </Box>
              <IconButton
                onClick={() => setSidebarOpen(false)}
                sx={{ bgcolor: 'rgba(255,255,255,0.12)', color: '#fff', borderRadius: 2 }}
              >
                <CloseIcon />
              </IconButton>
            </Box>
          </Box>

          {/* 選單 */}
          <List sx={{ flex: 1, p: 1.5, display: 'flex', flexDirection: 'column', gap: 0.5 }}>
            <ListItemButton
              onClick={() => {
                setSidebarOpen(false);
                setSettingsOpen(true);
              }}
              sx={{
                borderRadius: 3,
                py: 1.8,
                px: 2,
                bgcolor: 'rgba(59,130,246,0.12)',
                border: '1px solid rgba(59,130,246,0.4)',
              }}
            >
              <ListItemIcon sx={{ minWidth: 44 }}>
                <SettingsIcon sx={{ color: '#60a5fa', fontSize: 30 }} />
              </ListItemIcon>
              <ListItemText
                primary="帳號設置"
                slotProps={{
                  primary: { sx: { color: '#e2e8f0', fontSize: '1.4rem', fontWeight: 800 } },
                }}
              />
            </ListItemButton>
          </List>

          {/* 登出 */}
          <Box sx={{ p: '0.8rem 1.5rem 2.5rem', borderTop: '1px solid rgba(255,255,255,0.08)' }}>
            <Button
              fullWidth
              onClick={() => {
                setSidebarOpen(false);
                setLogoutOpen(true);
              }}
              sx={{
                py: 1.6,
                borderRadius: 3,
                bgcolor: 'rgba(239,68,68,0.12)',
                border: '1px solid rgba(239,68,68,0.3)',
                color: '#fca5a5',
                fontSize: '1.4rem',
                fontWeight: 800,
                '&:hover': { bgcolor: 'rgba(239,68,68,0.2)' },
              }}
            >
              <LogoutIcon sx={{ mr: 1 }} /> 登出
            </Button>
          </Box>
        </Box>
      </Drawer>

      {/* 帳號設置對話框 */}
      <Dialog open={settingsOpen} onClose={() => setSettingsOpen(false)} maxWidth="sm" fullWidth>
        <DialogTitle sx={{ fontSize: '1.5rem', fontWeight: 900 }}>👤 帳號設置</DialogTitle>
        <DialogContent dividers sx={{ display: 'flex', flexDirection: 'column', gap: 3, py: 3 }}>
          {/* 姓 */}
          <Box>
            <Typography sx={{ fontSize: '1.15rem', fontWeight: 800, mb: 1 }}>
              姓名（例：王、李、陳）
            </Typography>
            <TextField
              value={userName}
              onChange={(e) => setUserName(e.target.value.slice(0, 1))}
              slotProps={{ htmlInput: { maxLength: 1 } }}
              fullWidth
            />
          </Box>

          {/* 稱謂 */}
          <Box>
            <Typography sx={{ fontSize: '1.15rem', fontWeight: 800, mb: 1 }}>稱謂</Typography>
            <Box sx={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: 1 }}>
              {TITLE_OPTIONS.map((t) => (
                <Button
                  key={t}
                  onClick={() => setUserTitle(t)}
                  sx={{
                    borderRadius: 2,
                    py: 1.4,
                    border: `2px solid ${userTitle === t ? '#2563eb' : '#e2e8f0'}`,
                    bgcolor: userTitle === t ? '#eff6ff' : '#fff',
                    color: userTitle === t ? '#1d4ed8' : '#64748b',
                    fontSize: '1.1rem',
                    fontWeight: 800,
                  }}
                >
                  {t}
                </Button>
              ))}
            </Box>
          </Box>

          {/* 字體大小 */}
          <Box>
            <Typography sx={{ fontSize: '1.15rem', fontWeight: 800, mb: 1 }}>
              🔡 字體大小
            </Typography>
            <Box sx={{ display: 'flex', gap: 1 }}>
              {FONT_OPTIONS.map((f) => (
                <Button
                  key={f.key}
                  onClick={() => setFontSize(f.key)}
                  sx={{
                    flex: 1,
                    borderRadius: 2,
                    py: 1.4,
                    border: `3px solid ${fontSize === f.key ? '#2563eb' : '#e2e8f0'}`,
                    bgcolor: fontSize === f.key ? '#eff6ff' : '#fff',
                    fontSize: f.key === 'small' ? '1rem' : f.key === 'large' ? '1.5rem' : '1.2rem',
                    fontWeight: 900,
                    color: fontSize === f.key ? '#1d4ed8' : '#64748b',
                  }}
                >
                  {f.label}
                </Button>
              ))}
            </Box>
          </Box>

          {/* 提醒 GIF（可更換） */}
          <Box>
            <Typography sx={{ fontSize: '1.15rem', fontWeight: 800, mb: 1 }}>
              🎬 提醒動畫 GIF（後台 / 家屬可替換）
            </Typography>
            <Box sx={{ display: 'flex', gap: 1.5, flexWrap: 'wrap' }}>
              {REMINDER_GIFS.map((g) => (
                <Box
                  key={g.url}
                  onClick={() => setGifKey(g.url)}
                  sx={{
                    borderRadius: 2,
                    overflow: 'hidden',
                    p: 1,
                    cursor: 'pointer',
                    border: `3px solid ${gifKey === g.url ? '#2563eb' : '#e2e8f0'}`,
                    bgcolor: gifKey === g.url ? '#eff6ff' : '#fff',
                  }}
                >
                  <img
                    src={g.url}
                    alt={g.label}
                    style={{ width: 84, height: 84, objectFit: 'cover', borderRadius: 8 }}
                    onError={(e) => {
                      e.currentTarget.style.display = 'none';
                    }}
                  />
                  <Typography
                    sx={{ fontSize: '0.9rem', fontWeight: 700, textAlign: 'center', mt: 0.5 }}
                  >
                    {g.label}
                  </Typography>
                </Box>
              ))}
            </Box>
          </Box>
        </DialogContent>
        <DialogActions sx={{ px: 3, pb: 2.5 }}>
          <Button onClick={() => setSettingsOpen(false)} sx={{ fontSize: '1.1rem' }}>
            取消
          </Button>
          <Button
            variant="contained"
            color="success"
            onClick={saveSettings}
            sx={{ fontSize: '1.2rem', fontWeight: 800, px: 4, py: 1 }}
          >
            ✅ 儲存
          </Button>
        </DialogActions>
      </Dialog>

      {/* 登出確認 */}
      <Dialog open={logoutOpen} onClose={() => setLogoutOpen(false)} maxWidth="xs" fullWidth>
        <DialogTitle sx={{ fontSize: '1.4rem', fontWeight: 900 }}>確認登出</DialogTitle>
        <DialogContent>
          <Typography sx={{ fontSize: '1.2rem', color: 'text.secondary' }}>
            確定要登出嗎？登出後需重新登入才能使用。
          </Typography>
        </DialogContent>
        <DialogActions sx={{ px: 3, pb: 2.5 }}>
          <Button onClick={() => setLogoutOpen(false)} sx={{ fontSize: '1.1rem' }}>
            取消
          </Button>
          <Button
            variant="contained"
            color="error"
            onClick={() => {
              setLogoutOpen(false);
              handleLogout();
            }}
            sx={{ fontSize: '1.2rem', fontWeight: 800, px: 4 }}
          >
            登出
          </Button>
        </DialogActions>
      </Dialog>

      {/* 提示訊息 */}
      <Snackbar
        open={!!toast}
        autoHideDuration={2000}
        onClose={() => setToast('')}
        anchorOrigin={{ vertical: 'top', horizontal: 'center' }}
      >
        <Alert severity="success" variant="filled" onClose={() => setToast('')}>
          {toast}
        </Alert>
      </Snackbar>
    </Box>
  );
}
