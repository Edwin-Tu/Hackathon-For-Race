import React, { useState, useRef, useEffect } from 'react';
import { LogOut, Settings } from 'lucide-react';

// ══════════════════════════════════════════════
// 可更換的提醒 GIF（後台 / 家屬端可在這裡替換或擴充）
// ══════════════════════════════════════════════
const REMINDER_GIFS = [
  {
    id: 1,
    name: '女兒小美',
    url: 'https://media.giphy.com/media/l0HlBO7eyXzSZkJri/giphy.gif',
    scene: '服藥提醒',
    greeting: '媽媽！記得吃藥喔，女兒愛您！❤️',
  },
  {
    id: 2,
    name: '孫子小志',
    url: 'https://media.giphy.com/media/3o7abKhOpu0NwenH3O/giphy.gif',
    scene: '健康關懷',
    greeting: '奶奶！今天有好好照顧自己嗎？😊',
  },
  {
    id: 3,
    name: '兒子大明',
    url: 'https://media.giphy.com/media/xT9IgG50Lg7russbDa/giphy.gif',
    scene: '日常陪伴',
    greeting: '媽！有空記得多休息，我很想您！',
  },
];

// ══════════════════════════════════════════════
// 後台 AI 排程（目前於前端模擬，之後可改為 API / SSE 推送）
// ══════════════════════════════════════════════
const AI_SCHEDULE = [
  { kind: 'wait', duration: 6000 },
  {
    kind: 'question',
    speaker: REMINDER_GIFS[0],
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
    speaker: REMINDER_GIFS[1],
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
    speaker: REMINDER_GIFS[2],
    question: '今天心情還不錯嗎？',
    yesFeedback: '太好了，保持好心情！',
    noFeedback: '沒關係，我在這裡陪著您！',
  },
  { kind: 'wait', duration: 4000 },
];

const TITLE_OPTIONS = ['👴 爺爺', '👵 奶奶', '🧑 先生', '👩 女士', '🙂 其他'];

function getGreeting() {
  const h = new Date().getHours();
  if (h >= 5 && h < 12) return { icon: '🌅', text: '早安' };
  if (h >= 12 && h < 18) return { icon: '☀️', text: '午安' };
  return { icon: '🌙', text: '晚安' };
}

// ══════════════════════════════════════════════
// 雙選智慧互動卡（是⭕ / 否❌）
// ══════════════════════════════════════════════
function DualChoiceCard({
  scene,
  busy,
  feedback,
  onYes,
  onNo,
  accentYes = '#16a34a',
  accentNo = '#dc2626',
}) {
  const gif = scene.speaker?.url || '';
  const name = scene.speaker?.name || 'AI';

  return (
    <div
      style={{
        display: 'flex',
        flexDirection: 'column',
        borderRadius: '24px',
        overflow: 'hidden',
        border: '2px solid #e2e8f0',
        boxShadow: '0 6px 28px rgba(0,0,0,0.10)',
      }}
    >
      {/* 家人 GIF 全寬 */}
      <div
        style={{ position: 'relative', background: '#0f172a', height: '200px', overflow: 'hidden' }}
      >
        <img
          src={gif}
          alt={name}
          style={{
            width: '100%',
            height: '100%',
            objectFit: 'cover',
            opacity: 0.85,
          }}
          onError={(e) => {
            e.target.style.display = 'none';
          }}
        />
        <div
          style={{
            position: 'absolute',
            bottom: 0,
            left: 0,
            right: 0,
            background: 'linear-gradient(transparent, rgba(0,0,0,0.75))',
            padding: '1.2rem 1.4rem 0.8rem',
          }}
        >
          <p style={{ fontSize: '1.5rem', fontWeight: '900', color: '#fbbf24', margin: 0 }}>
            {name}
          </p>
          <p style={{ fontSize: '1rem', color: 'rgba(255,255,255,0.7)', margin: '0.1rem 0 0' }}>
            想問您：
          </p>
        </div>
      </div>

      {/* 問題文字 */}
      <div style={{ background: '#1e293b', padding: '1.2rem 1.6rem' }}>
        <p
          style={{
            fontSize: '1.9rem',
            fontWeight: '900',
            color: '#fff',
            margin: 0,
            lineHeight: 1.4,
            whiteSpace: 'pre-line',
            textAlign: 'center',
          }}
        >
          {scene.question}
        </p>
      </div>

      {/* 左是 / 右否 */}
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', minHeight: '150px' }}>
        <button
          onClick={() => onYes()}
          disabled={busy}
          style={{
            background: feedback?.value === 'yes' ? '#bbf7d0' : accentYes,
            border: 'none',
            cursor: busy ? 'default' : 'pointer',
            opacity: busy ? 0.9 : 1,
            display: 'flex',
            flexDirection: 'column',
            alignItems: 'center',
            justifyContent: 'center',
            gap: '0.5rem',
            padding: '1.4rem',
          }}
        >
          <span style={{ fontSize: '3.5rem', lineHeight: 1 }}>⭕</span>
          <span style={{ fontSize: '2.2rem', fontWeight: '900', color: '#fff' }}>是</span>
        </button>
        <button
          onClick={() => onNo()}
          disabled={busy}
          style={{
            background: feedback?.value === 'no' ? '#fecaca' : accentNo,
            border: 'none',
            borderLeft: '3px solid rgba(255,255,255,0.3)',
            cursor: busy ? 'default' : 'pointer',
            opacity: busy ? 0.9 : 1,
            display: 'flex',
            flexDirection: 'column',
            alignItems: 'center',
            justifyContent: 'center',
            gap: '0.5rem',
            padding: '1.4rem',
          }}
        >
          <span style={{ fontSize: '3.5rem', lineHeight: 1 }}>❌</span>
          <span style={{ fontSize: '2.2rem', fontWeight: '900', color: '#fff' }}>否</span>
        </button>
      </div>

      {/* 已選回饋 */}
      {feedback && (
        <div
          style={{
            background: feedback.value === 'yes' ? '#dcfce7' : '#fee2e2',
            padding: '1rem',
            textAlign: 'center',
          }}
        >
          <span
            style={{
              fontSize: '1.7rem',
              fontWeight: '900',
              color: feedback.value === 'yes' ? '#15803d' : '#dc2626',
            }}
          >
            {feedback.value === 'yes' ? '⭕ 已選擇：是' : '❌ 已選擇：否'} — {feedback.text}
          </span>
        </div>
      )}
    </div>
  );
}

// ══════════════════════════════════════════════
// GIF 提醒卡（後台 AI 提醒時顯示，可更換 GIF）
// ══════════════════════════════════════════════
function ReminderCard({ scene, gifUrl, onDismiss }) {
  return (
    <div
      style={{
        display: 'flex',
        flexDirection: 'column',
        borderRadius: '24px',
        overflow: 'hidden',
        border: '2px solid #e2e8f0',
        boxShadow: '0 6px 28px rgba(0,0,0,0.10)',
      }}
    >
      <div
        style={{ position: 'relative', background: '#0f172a', height: '280px', overflow: 'hidden' }}
      >
        <img
          src={gifUrl}
          alt="提醒動畫"
          style={{ width: '100%', height: '100%', objectFit: 'cover' }}
          onError={(e) => {
            e.target.style.display = 'none';
          }}
        />
      </div>
      <div style={{ background: '#fff', padding: '1.6rem 1.6rem 2rem', textAlign: 'center' }}>
        <p style={{ fontSize: '1.7rem', fontWeight: '900', color: '#1e40af', margin: 0 }}>
          🔔 {scene.title}
        </p>
        <p
          style={{ fontSize: '1.3rem', fontWeight: '700', color: '#475569', margin: '0.5rem 0 0' }}
        >
          {scene.message}
        </p>
        <button
          onClick={onDismiss}
          style={{
            marginTop: '1.2rem',
            borderRadius: '16px',
            padding: '0.9rem 2.6rem',
            background: '#2563eb',
            border: 'none',
            color: '#fff',
            fontSize: '1.4rem',
            fontWeight: '800',
            cursor: 'pointer',
          }}
        >
          我知道了
        </button>
      </div>
    </div>
  );
}

// ══════════════════════════════════════════════
// 側邊欄（隱藏式：帳號設置、登出）
// ══════════════════════════════════════════════
function Sidebar({ open, onClose, onSettings, onLogout, userName, userTitle }) {
  return (
    <>
      <div
        onClick={onClose}
        style={{
          position: 'fixed',
          inset: 0,
          zIndex: 200,
          background: 'rgba(0,0,0,0.5)',
          opacity: open ? 1 : 0,
          pointerEvents: open ? 'auto' : 'none',
          transition: 'opacity 0.3s ease',
        }}
      />
      <div
        style={{
          position: 'fixed',
          top: 0,
          left: 0,
          bottom: 0,
          zIndex: 300,
          width: '300px',
          background: '#0f172a',
          transform: open ? 'translateX(0)' : 'translateX(-100%)',
          transition: 'transform 0.32s cubic-bezier(0.4,0,0.2,1)',
          display: 'flex',
          flexDirection: 'column',
          boxShadow: '6px 0 40px rgba(0,0,0,0.4)',
          overflowY: 'auto',
        }}
      >
        {/* 頭部：帳號資訊 */}
        <div
          style={{
            padding: '3rem 1.5rem 1.5rem',
            borderBottom: '1px solid rgba(255,255,255,0.08)',
            background: 'linear-gradient(180deg, #1d4ed8 0%, #1e293b 100%)',
          }}
        >
          <div
            style={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between' }}
          >
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.8rem' }}>
              <div
                style={{
                  width: '52px',
                  height: '52px',
                  borderRadius: '50%',
                  background: 'rgba(255,255,255,0.2)',
                  border: '2px solid rgba(255,255,255,0.4)',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  fontSize: '1.6rem',
                  flexShrink: 0,
                }}
              >
                {userTitle?.split(' ')[0] || '👤'}
              </div>
              <div>
                <p style={{ fontSize: '1.6rem', fontWeight: '900', color: '#fff', margin: 0 }}>
                  {userName || '使用者'}
                </p>
                <p
                  style={{ fontSize: '1rem', color: 'rgba(255,255,255,0.6)', margin: '0.2rem 0 0' }}
                >
                  {userTitle}
                </p>
              </div>
            </div>
            <button
              onClick={onClose}
              style={{
                background: 'rgba(255,255,255,0.12)',
                border: 'none',
                borderRadius: '12px',
                padding: '0.7rem',
                cursor: 'pointer',
                color: '#fff',
                display: 'flex',
                alignItems: 'center',
              }}
            >
              <span style={{ fontSize: '1.6rem', lineHeight: 1 }}>✕</span>
            </button>
          </div>
        </div>

        {/* 帳號設置 */}
        <div style={{ flex: 1, padding: '1.5rem 0.8rem' }}>
          <button
            onClick={() => {
              onSettings();
              onClose();
            }}
            style={{
              width: '100%',
              display: 'flex',
              alignItems: 'center',
              gap: '0.9rem',
              borderRadius: '14px',
              padding: '1.3rem 1.3rem',
              background: 'rgba(59,130,246,0.12)',
              border: '1px solid rgba(59,130,246,0.4)',
              color: '#e2e8f0',
              fontSize: '1.5rem',
              fontWeight: '800',
              cursor: 'pointer',
              textAlign: 'left',
            }}
          >
            <Settings size={26} style={{ color: '#60a5fa' }} /> 帳號設置
          </button>
        </div>

        {/* 登出 */}
        <div
          style={{ padding: '0.8rem 0.8rem 2.5rem', borderTop: '1px solid rgba(255,255,255,0.08)' }}
        >
          <button
            onClick={() => {
              onLogout();
              onClose();
            }}
            style={{
              width: '100%',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              gap: '0.8rem',
              borderRadius: '14px',
              padding: '1.1rem',
              background: 'rgba(239,68,68,0.12)',
              border: '1px solid rgba(239,68,68,0.3)',
              color: '#fca5a5',
              fontSize: '1.4rem',
              fontWeight: '800',
              cursor: 'pointer',
            }}
          >
            <LogOut size={22} /> 登出
          </button>
        </div>
      </div>
    </>
  );
}

// ══════════════════════════════════════════════
// 登入頁（簡訊 + QR Code）
// ══════════════════════════════════════════════
function LoginPage({ onLogin }) {
  const [mode, setMode] = useState('choice');
  const [code, setCode] = useState('');
  const DEMO_CODE = '123456';

  if (mode === 'choice')
    return (
      <div
        style={{
          minHeight: '100vh',
          background: 'linear-gradient(160deg, #1e3a8a 0%, #1d4ed8 60%, #2563eb 100%)',
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          justifyContent: 'center',
          gap: '2rem',
          padding: '2rem',
          fontFamily: '"Microsoft JhengHei", system-ui',
        }}
      >
        <div style={{ textAlign: 'center' }}>
          <p style={{ fontSize: '5rem', margin: 0, lineHeight: 1 }}>🛡️</p>
          <h1
            style={{ fontSize: '2.8rem', fontWeight: '900', color: '#fff', margin: '0.8rem 0 0' }}
          >
            智護聲盾
          </h1>
          <p style={{ fontSize: '1.4rem', color: 'rgba(255,255,255,0.6)', margin: '0.4rem 0 0' }}>
            請選擇登入方式
          </p>
        </div>
        <div
          style={{
            display: 'flex',
            flexDirection: 'column',
            gap: '1rem',
            width: '100%',
            maxWidth: '340px',
          }}
        >
          <button
            onClick={() => setMode('sms')}
            style={{
              borderRadius: '20px',
              padding: '1.6rem 1.4rem',
              background: '#2563eb',
              border: 'none',
              display: 'flex',
              alignItems: 'center',
              gap: '1.2rem',
              cursor: 'pointer',
              textAlign: 'left',
            }}
          >
            <span style={{ fontSize: '2.5rem' }}>📱</span>
            <div>
              <p style={{ fontSize: '1.6rem', fontWeight: '900', color: '#fff', margin: 0 }}>
                簡訊驗證碼
              </p>
              <p
                style={{ fontSize: '1rem', color: 'rgba(255,255,255,0.75)', margin: '0.2rem 0 0' }}
              >
                收簡訊輸入 6 位數字
              </p>
            </div>
          </button>
          <button
            onClick={() => setMode('qr')}
            style={{
              borderRadius: '20px',
              padding: '1.6rem 1.4rem',
              background: '#7c3aed',
              border: 'none',
              display: 'flex',
              alignItems: 'center',
              gap: '1.2rem',
              cursor: 'pointer',
              textAlign: 'left',
            }}
          >
            <span style={{ fontSize: '2.5rem' }}>📷</span>
            <div>
              <p style={{ fontSize: '1.6rem', fontWeight: '900', color: '#fff', margin: 0 }}>
                QR Code 掃描
              </p>
              <p
                style={{ fontSize: '1rem', color: 'rgba(255,255,255,0.75)', margin: '0.2rem 0 0' }}
              >
                家屬幫忙掃描即可登入
              </p>
            </div>
          </button>
        </div>
      </div>
    );

  if (mode === 'sms')
    return (
      <div
        style={{
          minHeight: '100vh',
          background: '#0f172a',
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          justifyContent: 'center',
          gap: '1.5rem',
          padding: '2rem',
          fontFamily: '"Microsoft JhengHei", system-ui',
        }}
      >
        <p style={{ fontSize: '3rem', margin: 0 }}>📱</p>
        <h2 style={{ fontSize: '2rem', fontWeight: '900', color: '#fff', margin: 0 }}>
          輸入驗證碼
        </h2>
        <p
          style={{
            fontSize: '1.3rem',
            color: 'rgba(255,255,255,0.5)',
            margin: 0,
            textAlign: 'center',
          }}
        >
          簡訊已傳送至您的手機
          <br />
          <span style={{ color: '#fbbf24', fontWeight: '700' }}>示範碼：123456</span>
        </p>
        <div style={{ display: 'flex', gap: '0.6rem' }}>
          {Array.from({ length: 6 }).map((_, i) => (
            <div
              key={i}
              style={{
                width: '48px',
                height: '60px',
                borderRadius: '12px',
                background: code[i] ? 'rgba(255,255,255,0.2)' : 'rgba(255,255,255,0.06)',
                border: `2px solid ${code[i] ? 'rgba(255,255,255,0.5)' : 'rgba(255,255,255,0.15)'}`,
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                fontSize: '2.2rem',
                fontWeight: '900',
                color: '#fff',
              }}
            >
              {code[i] || ''}
            </div>
          ))}
        </div>
        <div
          style={{
            display: 'grid',
            gridTemplateColumns: 'repeat(3,1fr)',
            gap: '0.7rem',
            width: '100%',
            maxWidth: '300px',
          }}
        >
          {[1, 2, 3, 4, 5, 6, 7, 8, 9, '←', 0, '✓'].map((k, i) => (
            <button
              key={i}
              onClick={() => {
                if (k === '←') setCode((c) => c.slice(0, -1));
                else if (k === '✓') {
                  if (code === DEMO_CODE) onLogin();
                  else alert('驗證碼錯誤，請再試一次');
                } else if (code.length < 6) setCode((c) => c + k);
              }}
              style={{
                borderRadius: '14px',
                padding: '1.2rem 0',
                background: k === '✓' ? '#2563eb' : k === '←' ? '#475569' : 'rgba(255,255,255,0.1)',
                border: '1px solid rgba(255,255,255,0.12)',
                fontSize: k === '✓' ? '1.6rem' : '2rem',
                fontWeight: '900',
                color: '#fff',
                cursor: 'pointer',
              }}
            >
              {k}
            </button>
          ))}
        </div>
        <button
          onClick={() => {
            setCode('');
            setMode('choice');
          }}
          style={{
            background: 'none',
            border: 'none',
            color: 'rgba(255,255,255,0.35)',
            fontSize: '1.2rem',
            cursor: 'pointer',
          }}
        >
          ← 返回
        </button>
      </div>
    );

  if (mode === 'qr')
    return (
      <div
        style={{
          minHeight: '100vh',
          background: '#0f172a',
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          justifyContent: 'center',
          gap: '1.8rem',
          padding: '2rem',
          fontFamily: '"Microsoft JhengHei", system-ui',
        }}
      >
        <p
          style={{
            fontSize: '1.6rem',
            fontWeight: '800',
            color: '#fff',
            margin: 0,
            textAlign: 'center',
          }}
        >
          請讓家屬掃描下方 QR Code
        </p>
        <div
          style={{
            width: '200px',
            height: '200px',
            borderRadius: '20px',
            background: '#fff',
            padding: '12px',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            boxShadow: '0 8px 32px rgba(0,0,0,0.4)',
          }}
        >
          <img
            src="https://api.qrserver.com/v1/create-qr-code/?size=176x176&data=zhihu-shield-login-demo"
            alt="QR Code"
            style={{ width: '176px', height: '176px', borderRadius: '8px' }}
            onError={(e) => {
              e.target.style.display = 'none';
            }}
          />
        </div>
        <button
          onClick={() => onLogin()}
          style={{
            borderRadius: '16px',
            padding: '1.2rem 2rem',
            background: '#7c3aed',
            border: 'none',
            fontSize: '1.4rem',
            fontWeight: '800',
            color: '#fff',
            cursor: 'pointer',
          }}
        >
          ✅ 模擬掃描成功
        </button>
        <button
          onClick={() => setMode('choice')}
          style={{
            background: 'none',
            border: 'none',
            color: 'rgba(255,255,255,0.35)',
            fontSize: '1.2rem',
            cursor: 'pointer',
          }}
        >
          ← 返回
        </button>
      </div>
    );
}

// ══════════════════════════════════════════════
// SOS 固定按鈕
// ══════════════════════════════════════════════
function SOSBtn({ onPress }) {
  return (
    <button
      onClick={onPress}
      style={{
        position: 'fixed',
        bottom: '28px',
        right: '14px',
        zIndex: 500,
        width: '68px',
        height: '68px',
        borderRadius: '50%',
        background: '#dc2626',
        border: '4px solid #fca5a5',
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        justifyContent: 'center',
        cursor: 'pointer',
        animation: 'sosPulse 2s infinite',
        boxShadow: '0 4px 20px rgba(220,38,38,0.55)',
      }}
    >
      <span style={{ fontSize: '1.6rem', lineHeight: 1 }}>🆘</span>
      <span style={{ fontSize: '0.6rem', color: '#fff', fontWeight: '900', marginTop: '1px' }}>
        SOS
      </span>
    </button>
  );
}

// ══════════════════════════════════════════════
// 主程式
// ══════════════════════════════════════════════
export default function ElderApp() {
  const [loggedIn, setLoggedIn] = useState(false);
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [settingsOpen, setSettingsOpen] = useState(false);
  const [sosActive, setSosActive] = useState(false);
  const [sosTrigger, setSosTrigger] = useState({});

  // 畫面狀態：空白 / 二選一 / GIF 提醒
  const [view, setView] = useState({ type: 'blank' });
  const [busy, setBusy] = useState(false);
  const [feedback, setFeedback] = useState(null);

  // 帳號 / 個人化設定
  const [userName, setUserName] = useState(() => localStorage.getItem('userName') || '王');
  const [userTitle, setUserTitle] = useState(() => localStorage.getItem('userTitle') || '👵 奶奶');
  const [fontSize, setFontSize] = useState(() => localStorage.getItem('fontSize') || 'medium');
  const [gifUrl, setGifUrl] = useState(
    () => localStorage.getItem('reminderGif') || REMINDER_GIFS[0].url,
  );

  // 排程器 refs
  const sceneIndexRef = useRef(0);
  const timerRef = useRef(null);

  const fontScale = fontSize === 'small' ? 0.85 : fontSize === 'large' ? 1.18 : 1;

  // 把縮放比例直接套到 html 根元素，這樣所有 rem 單位都會縮放
  useEffect(() => {
    document.documentElement.style.fontSize = `${fontScale * 16}px`;
    return () => {
      document.documentElement.style.fontSize = '';
    };
  }, [fontScale]);

  // 依序執行後台 AI 排程
  function renderScene(index) {
    const scene = AI_SCHEDULE[index % AI_SCHEDULE.length];
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
  const handleAnswer = (value) => {
    if (busy || view.type !== 'question') return;
    const scene = view.scene;
    setBusy(true);
    const text = value === 'yes' ? scene.yesFeedback : scene.noFeedback;
    setFeedback({ value, text });
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
    localStorage.setItem('reminderGif', gifUrl);
    setSettingsOpen(false);
  };

  const handleLogout = () => {
    setLoggedIn(false);
  };

  // 登入
  if (!loggedIn) return <LoginPage onLogin={() => setLoggedIn(true)} />;

  // SOS 頁
  if (sosActive) {
    const ACTIONS = [
      { label: '📞 通知家屬 — 女兒小美', msg: '正在撥打給女兒小美，請稍候！' },
      { label: '👩‍⚕️ 通知照護員', msg: '正在通知照護員，請稍候！' },
      { label: '🚑 撥打緊急聯絡人', msg: '正在撥打緊急聯絡人，請保持冷靜！' },
    ];
    return (
      <div
        style={{
          minHeight: '100vh',
          background: '#dc2626',
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          justifyContent: 'center',
          gap: '1.5rem',
          padding: '2rem',
          fontFamily: '"Microsoft JhengHei", system-ui',
        }}
      >
        <span style={{ fontSize: '5rem', animation: 'sosPulse 1s infinite' }}>🆘</span>
        <h1
          style={{
            fontSize: '2.8rem',
            fontWeight: '900',
            color: '#fff',
            margin: 0,
            textAlign: 'center',
          }}
        >
          緊急求助中
        </h1>
        <p
          style={{
            fontSize: '1.5rem',
            color: 'rgba(255,255,255,0.85)',
            margin: 0,
            textAlign: 'center',
          }}
        >
          請點下方按鈕通知相關人員
          <br />
          請保持冷靜
        </p>
        <div
          style={{
            display: 'flex',
            flexDirection: 'column',
            gap: '0.8rem',
            width: '100%',
            maxWidth: '360px',
          }}
        >
          {ACTIONS.map((a, i) => {
            const done = !!sosTrigger[i];
            return (
              <button
                key={i}
                onClick={() => {
                  if (done) return;
                  setSosTrigger((p) => ({ ...p, [i]: true }));
                }}
                style={{
                  borderRadius: '16px',
                  padding: '1.3rem 1.5rem',
                  background: done ? 'rgba(255,255,255,0.35)' : 'rgba(255,255,255,0.15)',
                  border: `2px solid ${done ? 'rgba(255,255,255,0.7)' : 'rgba(255,255,255,0.3)'}`,
                  display: 'flex',
                  alignItems: 'center',
                  gap: '1rem',
                  cursor: done ? 'default' : 'pointer',
                  width: '100%',
                  textAlign: 'left',
                }}
              >
                <span style={{ fontSize: '1.6rem', color: '#fff', fontWeight: '900', flex: 1 }}>
                  {a.label}
                </span>
                <span style={{ fontSize: '1.8rem' }}>{done ? '✅' : '▶'}</span>
              </button>
            );
          })}
        </div>
        {Object.keys(sosTrigger).length > 0 && (
          <div
            style={{
              background: 'rgba(255,255,255,0.2)',
              borderRadius: '14px',
              padding: '1rem 1.5rem',
              width: '100%',
              maxWidth: '360px',
              textAlign: 'center',
            }}
          >
            <p style={{ fontSize: '1.4rem', fontWeight: '800', color: '#fff', margin: 0 }}>
              ✅ 已通知 {Object.keys(sosTrigger).length} 位 — 幫助正在趕來！
            </p>
          </div>
        )}
        <button
          onClick={() => {
            setSosActive(false);
            setSosTrigger({});
          }}
          style={{
            borderRadius: '14px',
            padding: '1.2rem 2.5rem',
            background: 'rgba(255,255,255,0.2)',
            border: '2px solid rgba(255,255,255,0.4)',
            fontSize: '1.5rem',
            fontWeight: '800',
            color: '#fff',
            cursor: 'pointer',
            marginTop: '0.5rem',
          }}
        >
          取消 / 我沒事了
        </button>
      </div>
    );
  }

  const greeting = getGreeting();

  return (
    <div
      style={{
        minHeight: '100vh',
        background: '#f0f7ff',
        fontFamily: '"Microsoft JhengHei", system-ui, sans-serif',
      }}
    >
      <Sidebar
        open={sidebarOpen}
        onClose={() => setSidebarOpen(false)}
        onSettings={() => setSettingsOpen(true)}
        onLogout={handleLogout}
        userName={userName}
        userTitle={userTitle}
      />

      {/* 頂部列 */}
      <div
        style={{
          position: 'sticky',
          top: 0,
          zIndex: 100,
          background: '#fff',
          borderBottom: '1px solid #e2e8f0',
          padding: '0.8rem 1rem',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          maxWidth: '640px',
          margin: '0 auto',
          boxSizing: 'border-box',
          width: '100%',
        }}
      >
        <button
          onClick={() => setSidebarOpen(true)}
          style={{
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            background: '#f1f5f9',
            border: '1px solid #e2e8f0',
            borderRadius: '12px',
            padding: '0.6rem',
            cursor: 'pointer',
            color: '#374151',
            fontSize: '1.6rem',
            lineHeight: 1,
          }}
        >
          ☰
        </button>
        <p style={{ fontSize: '1.4rem', fontWeight: '900', color: '#1e293b', margin: 0 }}>
          {greeting.icon} {userName} {userTitle}
        </p>
        <button
          onClick={() => setSosActive(true)}
          style={{
            background: '#fee2e2',
            border: '2px solid #fca5a5',
            borderRadius: '12px',
            padding: '0.5rem 0.8rem',
            cursor: 'pointer',
            fontSize: '1.2rem',
            fontWeight: '800',
            color: '#dc2626',
          }}
        >
          🆘
        </button>
      </div>

      {/* 主內容：常態為空白，AI 事件時顯示卡片 */}
      <div
        style={{
          maxWidth: '640px',
          margin: '0 auto',
          padding: '1rem',
          minHeight: 'calc(100vh - 76px)',
        }}
      >
        {view.type === 'question' && (
          <DualChoiceCard
            scene={view.scene}
            busy={busy}
            feedback={feedback}
            accentYes="#16a34a"
            accentNo="#dc2626"
            onYes={() => handleAnswer('yes')}
            onNo={() => handleAnswer('no')}
          />
        )}
        {view.type === 'reminder' && (
          <ReminderCard scene={view.scene} gifUrl={gifUrl} onDismiss={dismissReminder} />
        )}
      </div>

      <SOSBtn onPress={() => setSosActive(true)} />

      {/* 帳號設置 */}
      {settingsOpen && (
        <div
          style={{
            position: 'fixed',
            inset: 0,
            zIndex: 400,
            background: 'rgba(0,0,0,0.5)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            padding: '1.2rem',
          }}
          onClick={() => setSettingsOpen(false)}
        >
          <div
            style={{
              background: '#fff',
              borderRadius: '20px',
              width: '100%',
              maxWidth: '480px',
              maxHeight: '88vh',
              overflowY: 'auto',
              padding: '1.5rem',
            }}
            onClick={(e) => e.stopPropagation()}
          >
            <h2
              style={{
                fontSize: '1.7rem',
                fontWeight: '900',
                color: '#1e293b',
                margin: '0 0 1.4rem',
              }}
            >
              👤 帳號設置
            </h2>

            {/* 姓名 */}
            <div style={{ marginBottom: '1.4rem' }}>
              <p
                style={{
                  fontSize: '1.2rem',
                  fontWeight: '800',
                  color: '#374151',
                  margin: '0 0 0.6rem',
                }}
              >
                姓名（例：王、李、陳）
              </p>
              <input
                value={userName}
                onChange={(e) => setUserName(e.target.value.slice(0, 1))}
                placeholder="請輸入一個字的姓"
                style={{
                  width: '100%',
                  boxSizing: 'border-box',
                  borderRadius: '12px',
                  border: '2px solid #e2e8f0',
                  padding: '1rem',
                  fontSize: '1.6rem',
                  fontWeight: '700',
                  color: '#1e293b',
                  outline: 'none',
                }}
                onFocus={(e) => (e.target.style.borderColor = '#2563eb')}
                onBlur={(e) => (e.target.style.borderColor = '#e2e8f0')}
              />
            </div>

            {/* 稱謂 */}
            <div style={{ marginBottom: '1.4rem' }}>
              <p
                style={{
                  fontSize: '1.2rem',
                  fontWeight: '800',
                  color: '#374151',
                  margin: '0 0 0.6rem',
                }}
              >
                稱謂
              </p>
              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3,1fr)', gap: '0.6rem' }}>
                {TITLE_OPTIONS.map((t) => (
                  <button
                    key={t}
                    onClick={() => setUserTitle(t)}
                    style={{
                      borderRadius: '12px',
                      padding: '0.9rem 0.4rem',
                      border: `2px solid ${userTitle === t ? '#2563eb' : '#e2e8f0'}`,
                      background: userTitle === t ? '#eff6ff' : '#fff',
                      fontSize: '1.1rem',
                      fontWeight: '800',
                      color: userTitle === t ? '#1d4ed8' : '#64748b',
                      cursor: 'pointer',
                    }}
                  >
                    {t}
                  </button>
                ))}
              </div>
            </div>

            {/* 字體大小 */}
            <div style={{ marginBottom: '1.4rem' }}>
              <p
                style={{
                  fontSize: '1.2rem',
                  fontWeight: '800',
                  color: '#374151',
                  margin: '0 0 0.6rem',
                }}
              >
                🔡 字體大小
              </p>
              <div style={{ display: 'flex', gap: '0.8rem' }}>
                {[
                  { key: 'small', label: '小' },
                  { key: 'medium', label: '中' },
                  { key: 'large', label: '大' },
                ].map((f) => (
                  <button
                    key={f.key}
                    onClick={() => setFontSize(f.key)}
                    style={{
                      flex: 1,
                      borderRadius: '14px',
                      padding: '1.1rem 0',
                      border: `3px solid ${fontSize === f.key ? '#2563eb' : '#e2e8f0'}`,
                      background: fontSize === f.key ? '#eff6ff' : '#fff',
                      fontSize:
                        f.key === 'small' ? '1rem' : f.key === 'large' ? '1.5rem' : '1.2rem',
                      fontWeight: '900',
                      color: fontSize === f.key ? '#1d4ed8' : '#64748b',
                      cursor: 'pointer',
                    }}
                  >
                    {f.label}
                  </button>
                ))}
              </div>
            </div>

            {/* 提醒 GIF（可更換） */}
            <div style={{ marginBottom: '1.4rem' }}>
              <p
                style={{
                  fontSize: '1.2rem',
                  fontWeight: '800',
                  color: '#374151',
                  margin: '0 0 0.6rem',
                }}
              >
                🎬 提醒動畫 GIF（後台 / 家屬可替換）
              </p>
              <div style={{ display: 'flex', gap: '0.8rem', flexWrap: 'wrap' }}>
                {REMINDER_GIFS.map((g) => (
                  <button
                    key={g.id}
                    onClick={() => setGifUrl(g.url)}
                    style={{
                      borderRadius: '12px',
                      padding: '0.5rem',
                      cursor: 'pointer',
                      border: `3px solid ${gifUrl === g.url ? '#2563eb' : '#e2e8f0'}`,
                      background: gifUrl === g.url ? '#eff6ff' : '#fff',
                    }}
                  >
                    <img
                      src={g.url}
                      alt={g.name}
                      style={{
                        width: '84px',
                        height: '84px',
                        objectFit: 'cover',
                        borderRadius: '8px',
                      }}
                      onError={(e) => {
                        e.target.style.display = 'none';
                      }}
                    />
                    <p
                      style={{
                        fontSize: '0.9rem',
                        fontWeight: '700',
                        color: '#475569',
                        margin: '0.4rem 0 0',
                      }}
                    >
                      {g.name}
                    </p>
                  </button>
                ))}
              </div>
            </div>

            <div style={{ display: 'flex', gap: '0.8rem' }}>
              <button
                onClick={() => setSettingsOpen(false)}
                style={{
                  flex: 1,
                  borderRadius: '14px',
                  padding: '1.1rem',
                  background: '#f1f5f9',
                  border: '1px solid #e2e8f0',
                  fontSize: '1.3rem',
                  fontWeight: '800',
                  color: '#475569',
                  cursor: 'pointer',
                }}
              >
                取消
              </button>
              <button
                onClick={saveSettings}
                style={{
                  flex: 1,
                  borderRadius: '14px',
                  padding: '1.1rem',
                  background: '#10b981',
                  border: 'none',
                  fontSize: '1.4rem',
                  fontWeight: '900',
                  color: '#fff',
                  cursor: 'pointer',
                }}
              >
                ✅ 儲存
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
