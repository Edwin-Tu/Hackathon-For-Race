import React, { useState, useRef, useCallback } from 'react';
import { ChevronLeft, Volume2, Mic, MicOff, Heart, Home, MessageCircle, Pill } from 'lucide-react';

// ── 語音輸入 hook ────────────────────────────────────────────
function useSpeechInput({ onYes, onNo, onTranscript }) {
  const [listening, setListening] = useState(false);
  const [transcript, setTranscript] = useState('');
  const recognitionRef = useRef(null);

  const YES_WORDS = ['是', '有', '對', '好', '要', '需要', '吃了', '喝了', '做了', '睡了', '吃', '喝', '好的', '正確', '沒錯'];
  const NO_WORDS  = ['否', '沒有', '不', '不要', '沒', '不用', '沒吃', '沒喝', '沒做', '沒睡', '不需要'];

  const start = useCallback(() => {
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (!SpeechRecognition) return;

    const rec = new SpeechRecognition();
    rec.lang = 'zh-TW';
    rec.continuous = false;
    rec.interimResults = false;
    recognitionRef.current = rec;

    rec.onstart = () => setListening(true);
    rec.onend   = () => setListening(false);
    rec.onerror = () => setListening(false);

    rec.onresult = (e) => {
      const text = e.results[0][0].transcript.trim();
      setTranscript(text);
      if (onTranscript) onTranscript(text);

      const isYes = YES_WORDS.some((w) => text.includes(w));
      const isNo  = NO_WORDS.some((w) => text.includes(w));

      if (isYes && !isNo) {
        onYes(text);
      } else if (isNo) {
        onNo(text);
      }
    };

    rec.start();
  }, [onYes, onNo, onTranscript]);

  const stop = useCallback(() => {
    recognitionRef.current?.stop();
    setListening(false);
  }, []);

  return { listening, transcript, start, stop };
}

// ── 單題卡 ────────────────────────────────────────────────────
function QuestionCard({ emoji, question, onYes, onNo }) {
  const [voiceText, setVoiceText] = useState('');
  const [voiceStatus, setVoiceStatus] = useState('idle');
  const [pressed, setPressed] = useState(null);

  const { listening, start, stop } = useSpeechInput({
    onYes: (text) => {
      setVoiceText(`「${text}」→ 是`);
      setVoiceStatus('done');
      setPressed('yes');
      setTimeout(() => { setVoiceText(''); setVoiceStatus('idle'); setPressed(null); onYes(); }, 800);
    },
    onNo: (text) => {
      setVoiceText(`「${text}」→ 否`);
      setVoiceStatus('done');
      setPressed('no');
      setTimeout(() => { setVoiceText(''); setVoiceStatus('idle'); setPressed(null); onNo(); }, 800);
    },
    onTranscript: (text) => {
      setVoiceText(`聽到：「${text}」`);
    },
  });

  const handleMic = () => {
    if (listening) { stop(); setVoiceStatus('idle'); }
    else { setVoiceText(''); setVoiceStatus('listening'); start(); }
  };

  const handleYes = () => {
    setPressed('yes');
    setTimeout(() => { setPressed(null); onYes(); }, 600);
  };

  const handleNo = () => {
    setPressed('no');
    setTimeout(() => { setPressed(null); onNo(); }, 600);
  };

  return (
    <div style={{
      background: 'linear-gradient(145deg, #ffffff, #f8faff)',
      borderRadius: '28px',
      boxShadow: '0 8px 32px rgba(0,0,0,0.10), 0 2px 8px rgba(0,0,0,0.06)',
      padding: '2rem',
      display: 'flex',
      flexDirection: 'column',
      alignItems: 'center',
      gap: '1.5rem',
      border: '2px solid rgba(255,255,255,0.8)',
    }}>
      {/* emoji */}
      <div style={{
        background: 'linear-gradient(135deg, #e0f2fe, #dbeafe)',
        borderRadius: '50%',
        width: '130px',
        height: '130px',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        fontSize: '4rem',
        boxShadow: '0 4px 16px rgba(59,130,246,0.15)',
      }}>
        {emoji}
      </div>

      {/* 問題 */}
      <p style={{
        fontSize: '2rem',
        fontWeight: '900',
        color: '#1e293b',
        textAlign: 'center',
        lineHeight: '1.4',
        whiteSpace: 'pre-line',
      }}>{question}</p>

      {/* 是 / 否 按鈕 */}
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem', width: '100%' }}>
        <button
          onClick={handleYes}
          style={{
            borderRadius: '20px',
            padding: '1.5rem 0',
            fontSize: '2rem',
            fontWeight: '900',
            color: 'white',
            border: 'none',
            cursor: 'pointer',
            transition: 'all 0.15s ease',
            background: pressed === 'yes'
              ? 'linear-gradient(135deg, #6ee7b7, #34d399)'
              : 'linear-gradient(135deg, #10b981, #059669)',
            boxShadow: pressed === 'yes'
              ? '0 0 0 6px rgba(16,185,129,0.3), 0 8px 24px rgba(16,185,129,0.4)'
              : '0 4px 16px rgba(16,185,129,0.35)',
            transform: pressed === 'yes' ? 'scale(1.06)' : 'scale(1)',
          }}
        >
          ✅ 是
        </button>
        <button
          onClick={handleNo}
          style={{
            borderRadius: '20px',
            padding: '1.5rem 0',
            fontSize: '2rem',
            fontWeight: '900',
            color: 'white',
            border: 'none',
            cursor: 'pointer',
            transition: 'all 0.15s ease',
            background: pressed === 'no'
              ? 'linear-gradient(135deg, #fca5a5, #f87171)'
              : 'linear-gradient(135deg, #ef4444, #dc2626)',
            boxShadow: pressed === 'no'
              ? '0 0 0 6px rgba(239,68,68,0.3), 0 8px 24px rgba(239,68,68,0.4)'
              : '0 4px 16px rgba(239,68,68,0.35)',
            transform: pressed === 'no' ? 'scale(1.06)' : 'scale(1)',
          }}
        >
          ❌ 否
        </button>
      </div>

      {/* 按下後大型提示 */}
      {pressed !== null && (
        <div style={{
          width: '100%',
          borderRadius: '18px',
          padding: '1.2rem',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          gap: '1rem',
          background: pressed === 'yes'
            ? 'linear-gradient(135deg, #d1fae5, #a7f3d0)'
            : 'linear-gradient(135deg, #fee2e2, #fecaca)',
          boxShadow: pressed === 'yes'
            ? '0 4px 16px rgba(16,185,129,0.2)'
            : '0 4px 16px rgba(239,68,68,0.2)',
        }}>
          <span style={{ fontSize: '2.5rem' }}>{pressed === 'yes' ? '✅' : '❌'}</span>
          <span style={{
            fontSize: '2rem',
            fontWeight: '900',
            color: pressed === 'yes' ? '#065f46' : '#991b1b',
          }}>
            {pressed === 'yes' ? '已選擇：是' : '已選擇：否'}
          </span>
        </div>
      )}

      {/* 語音按鈕 */}
      <button
        onClick={handleMic}
        style={{
          width: '100%',
          borderRadius: '18px',
          padding: '1.2rem',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          gap: '0.8rem',
          border: 'none',
          cursor: 'pointer',
          fontSize: '1.6rem',
          fontWeight: '900',
          transition: 'all 0.2s ease',
          background: listening
            ? 'linear-gradient(135deg, #ef4444, #dc2626)'
            : voiceStatus === 'done'
            ? 'linear-gradient(135deg, #d1fae5, #a7f3d0)'
            : 'linear-gradient(135deg, #f1f5f9, #e2e8f0)',
          color: listening ? 'white' : voiceStatus === 'done' ? '#065f46' : '#475569',
          boxShadow: listening
            ? '0 4px 16px rgba(239,68,68,0.4)'
            : '0 2px 8px rgba(0,0,0,0.08)',
          animation: listening ? 'pulse 1.5s infinite' : 'none',
        }}
      >
        {listening
          ? <><MicOff size={32} /><span>聆聽中…</span></>
          : <><Mic size={32} /><span>說話回答</span></>
        }
      </button>

      {voiceText !== '' && (
        <div style={{
          width: '100%',
          borderRadius: '14px',
          padding: '0.8rem 1rem',
          textAlign: 'center',
          background: voiceStatus === 'done' ? '#ecfdf5' : '#eff6ff',
          border: voiceStatus === 'done' ? '2px solid #6ee7b7' : '2px solid #bfdbfe',
          color: voiceStatus === 'done' ? '#065f46' : '#1e40af',
        }}>
          <p style={{ fontSize: '1.3rem', fontWeight: '700' }}>{voiceText}</p>
        </div>
      )}
    </div>
  );
}

// ── 完成畫面 ────────────────────────────────────────────────
function DoneCard({ emoji, message, onReset, resetLabel = '🔄 重新開始' }) {
  return (
    <div style={{
      background: 'linear-gradient(145deg, #f0fdf4, #dcfce7)',
      borderRadius: '28px',
      boxShadow: '0 8px 32px rgba(16,185,129,0.15)',
      padding: '2.5rem 2rem',
      display: 'flex',
      flexDirection: 'column',
      alignItems: 'center',
      gap: '1.5rem',
      border: '2px solid #86efac',
    }}>
      <div style={{
        background: 'linear-gradient(135deg, #bbf7d0, #86efac)',
        borderRadius: '50%',
        width: '120px',
        height: '120px',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        fontSize: '3.5rem',
        boxShadow: '0 4px 16px rgba(16,185,129,0.25)',
      }}>
        {emoji}
      </div>
      <p style={{ fontSize: '2rem', fontWeight: '900', color: '#14532d', textAlign: 'center', lineHeight: '1.4' }}>{message}</p>
      <button
        onClick={onReset}
        style={{
          width: '100%',
          borderRadius: '18px',
          padding: '1.2rem',
          background: 'linear-gradient(135deg, #f8faff, #f1f5f9)',
          border: '2px solid #cbd5e1',
          fontSize: '1.5rem',
          fontWeight: '900',
          color: '#475569',
          cursor: 'pointer',
          boxShadow: '0 2px 8px rgba(0,0,0,0.06)',
          transition: 'all 0.15s ease',
        }}
      >
        {resetLabel}
      </button>
    </div>
  );
}

// ── 設定頁 ────────────────────────────────────────────────────
function SettingsPage({ userName, userTitle, onSave }) {
  const [name, setName] = useState(userName);
  const [title, setTitle] = useState(userTitle);

  const titleOptions = ['👴 爺爺', '👵 奶奶', '🧑 先生', '👩 女士', '🙂 其他'];

  return (
    <div style={{
      minHeight: '100vh',
      background: 'linear-gradient(160deg, #eff6ff 0%, #f0f9ff 50%, #ecfdf5 100%)',
      padding: '1.5rem',
      fontFamily: 'system-ui, sans-serif',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
    }}>
      <div style={{ maxWidth: '420px', width: '100%', display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>

        {/* 標題 */}
        <div style={{
          background: 'linear-gradient(135deg, #3b82f6, #2563eb)',
          borderRadius: '28px',
          padding: '1.8rem',
          textAlign: 'center',
          boxShadow: '0 8px 32px rgba(59,130,246,0.3)',
        }}>
          <p style={{ fontSize: '3rem', margin: 0 }}>👤</p>
          <p style={{ fontSize: '2rem', fontWeight: '900', color: 'white', margin: '0.5rem 0 0' }}>使用者設定</p>
          <p style={{ fontSize: '1.1rem', color: 'rgba(255,255,255,0.8)', margin: '0.3rem 0 0' }}>請輸入您的姓名與稱謂</p>
        </div>

        {/* 姓名輸入 */}
        <div style={{
          background: 'white',
          borderRadius: '24px',
          padding: '1.5rem',
          boxShadow: '0 4px 20px rgba(0,0,0,0.08)',
          display: 'flex',
          flexDirection: 'column',
          gap: '1rem',
        }}>
          <p style={{ fontSize: '1.4rem', fontWeight: '900', color: '#1e293b', margin: 0 }}>姓名</p>
          <input
            type="text"
            value={name}
            onChange={(e) => setName(e.target.value)}
            placeholder="請輸入姓名（例：王小明）"
            style={{
              borderRadius: '16px',
              border: '3px solid #bfdbfe',
              padding: '1rem 1.2rem',
              fontSize: '1.6rem',
              fontWeight: '700',
              color: '#1e293b',
              outline: 'none',
              width: '100%',
              boxSizing: 'border-box',
              background: '#f8faff',
            }}
          />

          <p style={{ fontSize: '1.4rem', fontWeight: '900', color: '#1e293b', margin: '0.5rem 0 0' }}>稱謂</p>
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '0.7rem' }}>
            {titleOptions.map((t) => (
              <button
                key={t}
                onClick={() => setTitle(t)}
                style={{
                  borderRadius: '14px',
                  padding: '0.9rem',
                  fontSize: '1.3rem',
                  fontWeight: '900',
                  border: '3px solid',
                  cursor: 'pointer',
                  transition: 'all 0.15s ease',
                  background: title === t
                    ? 'linear-gradient(135deg, #3b82f6, #2563eb)'
                    : '#f8faff',
                  borderColor: title === t ? '#2563eb' : '#bfdbfe',
                  color: title === t ? 'white' : '#475569',
                  boxShadow: title === t ? '0 4px 12px rgba(59,130,246,0.3)' : 'none',
                }}
              >
                {t}
              </button>
            ))}
          </div>
        </div>

        {/* 預覽 */}
        {name.trim() !== '' && (
          <div style={{
            background: 'linear-gradient(135deg, #f0fdf4, #dcfce7)',
            borderRadius: '20px',
            border: '2px solid #86efac',
            padding: '1.2rem 1.5rem',
            textAlign: 'center',
          }}>
            <p style={{ fontSize: '1.2rem', color: '#14532d', margin: 0 }}>顯示效果預覽</p>
            <p style={{ fontSize: '1.8rem', fontWeight: '900', color: '#065f46', margin: '0.4rem 0 0' }}>
              {name}{title ? ' ' + title : ''} 早安！
            </p>
          </div>
        )}

        {/* 儲存按鈕 */}
        <button
          onClick={() => {
            if (name.trim() === '') return;
            onSave(name.trim(), title);
          }}
          style={{
            borderRadius: '22px',
            padding: '1.4rem',
            background: name.trim() === ''
              ? 'linear-gradient(135deg, #cbd5e1, #94a3b8)'
              : 'linear-gradient(135deg, #10b981, #059669)',
            border: 'none',
            fontSize: '1.8rem',
            fontWeight: '900',
            color: 'white',
            cursor: name.trim() === '' ? 'not-allowed' : 'pointer',
            boxShadow: name.trim() === '' ? 'none' : '0 8px 24px rgba(16,185,129,0.35)',
            transition: 'all 0.15s ease',
          }}
        >
          ✅ 儲存設定
        </button>
      </div>
    </div>
  );
}

export default function ElderApp() {
  // 從 localStorage 讀取使用者資料，若無則為空
  const [userName, setUserName] = useState(() => localStorage.getItem('elderUserName') || '');
  const [userTitle, setUserTitle] = useState(() => localStorage.getItem('elderUserTitle') || '👵 奶奶');
  const [currentPage, setCurrentPage] = useState(() => {
    const saved = localStorage.getItem('elderUserName');
    return saved ? 'home' : 'setup';
  });

  const speakText = (text) => {
    if (typeof window !== 'undefined' && 'speechSynthesis' in window) {
      window.speechSynthesis.cancel();
      const utterance = new SpeechSynthesisUtterance(text);
      utterance.lang = 'zh-TW';
      utterance.rate = 0.85;
      window.speechSynthesis.speak(utterance);
    }
  };

  const go = (page) => setCurrentPage(page);

  const handleSaveUser = (name, title) => {
    setUserName(name);
    setUserTitle(title);
    localStorage.setItem('elderUserName', name);
    localStorage.setItem('elderUserTitle', title);
    go('home');
  };

  // ── 首頁問卷
  const homeQuestions = [
    { key: 'sleep',    emoji: '😴', question: '昨晚睡得好嗎？',   yes: '很好，繼續保持！',         no: '沒關係，今天多休息。' },
    { key: 'meal',     emoji: '🍚', question: '早餐吃了嗎？',     yes: '太好了！',                 no: '記得去吃點東西喔！' },
    { key: 'medicine', emoji: '💊', question: '早上的藥吃了嗎？', yes: '很棒，繼續保持！',         no: '記得補吃藥，不要忘記！' },
    { key: 'pain',     emoji: '🤕', question: '身體有不舒服嗎？', yes: '辛苦了，要通知家人嗎？',   no: '太好了，今天狀況不錯！' },
  ];
  const [homeIdx, setHomeIdx] = useState(0);
  const [homeDone, setHomeDone] = useState(false);
  const [homeMsg, setHomeMsg] = useState('');

  // ── 記事問卷
  const noteQuestions = [
    { key: 'doctor',   emoji: '🏥', question: '今天需要回診掛號嗎？',   label: '回診掛號' },
    { key: 'medicine', emoji: '💊', question: '藥快吃完，需要買藥嗎？', label: '買藥補充' },
    { key: 'family',   emoji: '📞', question: '今天要聯絡家人嗎？',     label: '聯絡家人' },
    { key: 'food',     emoji: '🛒', question: '今天需要買食物嗎？',     label: '購買食物' },
    { key: 'exercise', emoji: '🚶', question: '今天要記得散步嗎？',     label: '記得散步' },
    { key: 'water',    emoji: '💧', question: '需要提醒自己多喝水嗎？', label: '多喝水'   },
    { key: 'rest',     emoji: '😴', question: '今天要特別注意休息嗎？', label: '注意休息' },
  ];
  const [noteIdx, setNoteIdx] = useState(0);
  const [noteDone, setNoteDone] = useState(false);
  const [noteRecords, setNoteRecords] = useState([]);

  // ── 健康問卷
  const healthQuestions = [
    { key: 'walk',  emoji: '🚶', question: '今天有散步嗎？',       yes: '很好，繼續保持！',   no: '沒關係，明天試試看。' },
    { key: 'water', emoji: '💧', question: '今天有喝足夠的水嗎？', yes: '棒！身體需要水分。', no: '記得多喝點水喔！' },
    { key: 'rest',  emoji: '😴', question: '今天有好好休息嗎？',   yes: '很好，繼續保持！',   no: '記得多休息一下。' },
  ];
  const [healthIdx, setHealthIdx] = useState(0);
  const [healthDone, setHealthDone] = useState(false);
  const [healthMsg, setHealthMsg] = useState('');

  // ── 服藥問卷
  const medQuestions = [
    { key: 'morning', emoji: '🌅', question: '早上 8 點的降血壓藥\n吃了嗎？', yes: '太棒了！', no: '記得補吃喔！' },
    { key: 'noon',    emoji: '☀️', question: '中午 12 點的胃藥\n吃了嗎？',   yes: '太棒了！', no: '記得補吃喔！' },
    { key: 'evening', emoji: '🌙', question: '晚上 6 點的鈣片\n吃了嗎？',    yes: '太棒了！', no: '記得補吃喔！' },
  ];
  const [medIdx, setMedIdx] = useState(0);
  const [medDone, setMedDone] = useState(false);
  const [medCount, setMedCount] = useState(0);

  // ── 聊天問卷
  const chatQuestions = [
    { key: 'talk',  emoji: '🗣️', question: '想要陪伴聊天嗎？', yes: '好的！我們來聊聊天吧！',     no: '好的，沒問題！' },
    { key: 'story', emoji: '📖', question: '想聽故事嗎？',     yes: '好的！我來說故事給您聽！',   no: '好的，沒問題！' },
    { key: 'music', emoji: '🎵', question: '想聽音樂嗎？',     yes: '好的！現在為您播放音樂！',   no: '好的，沒問題！' },
  ];
  const [chatIdx, setChatIdx] = useState(0);
  const [chatDone, setChatDone] = useState(false);
  const [chatMsg, setChatMsg] = useState('');

  // ── SOS 問卷
  const sosQuestions = [
    { key: 'family',    emoji: '👨‍👩‍👧', question: '要聯絡家人嗎？',   yes: '正在聯絡家人，請稍候！',       no: '' },
    { key: 'caregiver', emoji: '👩‍⚕️', question: '要聯絡照護員嗎？', yes: '正在聯絡照護員，請稍候！',     no: '' },
    { key: 'ambulance', emoji: '🚑',    question: '需要叫救護車嗎？', yes: '正在叫救護車，請保持冷靜！',   no: '' },
  ];
  const [sosIdx, setSosIdx] = useState(0);
  const [sosDone, setSosDone] = useState(false);
  const [sosMsg, setSosMsg] = useState('');

  // ── 頂部返回列
  const TopBar = ({ title, gradient, icon }) => (
    <div style={{
      display: 'flex',
      alignItems: 'center',
      gap: '1rem',
      marginBottom: '1.5rem',
    }}>
      <button
        onClick={() => go('home')}
        style={{
          display: 'flex',
          alignItems: 'center',
          gap: '0.4rem',
          borderRadius: '16px',
          background: 'white',
          border: '2px solid #e2e8f0',
          padding: '0.8rem 1.2rem',
          fontSize: '1.3rem',
          fontWeight: '900',
          color: '#475569',
          cursor: 'pointer',
          boxShadow: '0 2px 8px rgba(0,0,0,0.08)',
          transition: 'all 0.15s ease',
        }}
      >
        <ChevronLeft size={24} /> 返回
      </button>
      <div style={{
        display: 'flex',
        alignItems: 'center',
        gap: '0.6rem',
        background: gradient,
        borderRadius: '14px',
        padding: '0.6rem 1.2rem',
        boxShadow: '0 2px 8px rgba(0,0,0,0.10)',
      }}>
        {icon}
        <h1 style={{ fontSize: '1.8rem', fontWeight: '900', color: 'white', margin: 0 }}>{title}</h1>
      </div>
    </div>
  );

  // ── 底部導航
  const BottomNav = () => (
    <div style={{
      position: 'sticky',
      bottom: 0,
      marginTop: '1.5rem',
      display: 'grid',
      gridTemplateColumns: 'repeat(4, 1fr)',
      gap: '0.5rem',
      background: 'rgba(255,255,255,0.95)',
      backdropFilter: 'blur(12px)',
      borderRadius: '24px',
      border: '2px solid #e2e8f0',
      padding: '0.6rem',
      boxShadow: '0 -4px 24px rgba(0,0,0,0.08)',
    }}>
      {[
        { key: 'home',       label: '首頁', icon: <Home size={28} /> },
        { key: 'health',     label: '健康', icon: <Heart size={28} /> },
        { key: 'chat',       label: '聊天', icon: <MessageCircle size={28} /> },
        { key: 'medication', label: '服藥', icon: <Pill size={28} /> },
      ].map((item) => (
        <button
          key={item.key}
          onClick={() => go(item.key)}
          style={{
            borderRadius: '18px',
            padding: '0.8rem 0',
            display: 'flex',
            flexDirection: 'column',
            alignItems: 'center',
            gap: '0.3rem',
            border: 'none',
            cursor: 'pointer',
            transition: 'all 0.2s ease',
            background: currentPage === item.key
              ? 'linear-gradient(135deg, #3b82f6, #2563eb)'
              : 'transparent',
            color: currentPage === item.key ? 'white' : '#64748b',
            boxShadow: currentPage === item.key ? '0 4px 12px rgba(59,130,246,0.35)' : 'none',
            fontWeight: '900',
            fontSize: '1rem',
          }}
        >
          {item.icon}
          <span>{item.label}</span>
        </button>
      ))}
    </div>
  );

  // ── 進度條
  const ProgressDots = ({ total, current, activeColor }) => (
    <div style={{ display: 'flex', justifyContent: 'center', gap: '0.6rem', margin: '0.5rem 0' }}>
      {Array.from({ length: total }).map((_, i) => (
        <div key={i} style={{
          width: i === current ? '32px' : '12px',
          height: '12px',
          borderRadius: '6px',
          background: i < current ? activeColor : i === current ? activeColor : '#cbd5e1',
          opacity: i < current ? 0.5 : 1,
          transition: 'all 0.3s ease',
        }} />
      ))}
    </div>
  );

  // ════════════════════════════════════════════════════════
  // 首頁
  // ════════════════════════════════════════════════════════
  // ── 設定頁
  if (currentPage === 'setup') {
    return (
      <SettingsPage
        userName={userName}
        userTitle={userTitle}
        onSave={handleSaveUser}
      />
    );
  }

  if (currentPage === 'home') {
    const q = homeQuestions[homeIdx];

    return (
      <div style={{
        minHeight: '100vh',
        background: 'linear-gradient(160deg, #eff6ff 0%, #f0f9ff 50%, #ecfdf5 100%)',
        padding: '1.2rem',
        fontFamily: 'system-ui, sans-serif',
      }}>
        <div style={{ maxWidth: '460px', margin: '0 auto', display: 'flex', flexDirection: 'column', gap: '1.2rem' }}>

          {/* 問候列 */}
          <div style={{
            background: 'linear-gradient(135deg, #3b82f6, #2563eb)',
            borderRadius: '28px',
            padding: '1.5rem 1.8rem',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            boxShadow: '0 8px 32px rgba(59,130,246,0.3)',
          }}>
            <div>
              <p style={{ fontSize: '2rem', fontWeight: '900', color: 'white', margin: 0 }}>{userName} {userTitle}</p>
              <p style={{ fontSize: '1.3rem', color: 'rgba(255,255,255,0.85)', margin: '0.3rem 0 0' }}>早安！今天也要加油喔！</p>
            </div>
            <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
              <button
                onClick={() => speakText(homeDone ? homeMsg : q.question)}
                style={{
                  display: 'flex',
                  flexDirection: 'column',
                  alignItems: 'center',
                  gap: '0.3rem',
                  background: 'rgba(255,255,255,0.2)',
                  border: '2px solid rgba(255,255,255,0.4)',
                  borderRadius: '16px',
                  padding: '0.6rem 0.8rem',
                  color: 'white',
                  cursor: 'pointer',
                  backdropFilter: 'blur(8px)',
                  transition: 'all 0.15s ease',
                }}
              >
                <Volume2 size={24} />
                <span style={{ fontSize: '0.9rem', fontWeight: '900' }}>朗讀</span>
              </button>
              <button
                onClick={() => go('setup')}
                style={{
                  display: 'flex',
                  flexDirection: 'column',
                  alignItems: 'center',
                  gap: '0.3rem',
                  background: 'rgba(255,255,255,0.15)',
                  border: '2px solid rgba(255,255,255,0.3)',
                  borderRadius: '16px',
                  padding: '0.6rem 0.8rem',
                  color: 'rgba(255,255,255,0.85)',
                  cursor: 'pointer',
                  backdropFilter: 'blur(8px)',
                  transition: 'all 0.15s ease',
                }}
              >
                <span style={{ fontSize: '1.2rem' }}>⚙️</span>
                <span style={{ fontSize: '0.9rem', fontWeight: '900' }}>設定</span>
              </button>
            </div>
          </div>

          {/* 緊急求助按鈕 */}
          <button
            onClick={() => { speakText('緊急求助'); go('sos'); }}
            style={{
              width: '100%',
              borderRadius: '24px',
              padding: '1.4rem',
              background: 'linear-gradient(135deg, #ef4444, #b91c1c)',
              border: '4px solid #fca5a5',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              gap: '1rem',
              cursor: 'pointer',
              boxShadow: '0 8px 28px rgba(239,68,68,0.5)',
              transition: 'all 0.15s ease',
              animation: 'sosPulse 2s infinite',
            }}
          >
            <span style={{ fontSize: '2.5rem' }}>🆘</span>
            <span style={{ fontSize: '2.2rem', fontWeight: '900', color: 'white', letterSpacing: '0.05em' }}>緊急求助</span>
            <span style={{ fontSize: '2.5rem' }}>🆘</span>
          </button>

          {/* 區塊標題 */}
          <div style={{
            display: 'flex',
            alignItems: 'center',
            gap: '0.8rem',
            padding: '0 0.5rem',
          }}>
            <div style={{
              width: '6px', height: '32px',
              background: 'linear-gradient(180deg, #3b82f6, #2563eb)',
              borderRadius: '3px',
            }} />
            <p style={{ fontSize: '1.5rem', fontWeight: '900', color: '#1e293b', margin: 0 }}>今日晨間確認</p>
          </div>

          {/* 今日確認 */}
          {!homeDone ? (
            <>
              <ProgressDots total={homeQuestions.length} current={homeIdx} activeColor="#3b82f6" />
              <QuestionCard
                emoji={q.emoji}
                question={q.question}
                onYes={() => {
                  speakText(q.yes);
                  if (homeIdx + 1 < homeQuestions.length) {
                    setHomeIdx(homeIdx + 1);
                  } else {
                    setHomeDone(true);
                    setHomeMsg('今天的確認完成了！');
                    speakText('今天的確認完成了！');
                  }
                }}
                onNo={() => {
                  speakText(q.no);
                  if (homeIdx + 1 < homeQuestions.length) {
                    setHomeIdx(homeIdx + 1);
                  } else {
                    setHomeDone(true);
                    setHomeMsg('今天的確認完成了！');
                    speakText('今天的確認完成了！');
                  }
                }}
              />
            </>
          ) : (
            <DoneCard
              emoji="🎉"
              message="今天的確認完成了！"
              onReset={() => { setHomeIdx(0); setHomeDone(false); setHomeMsg(''); }}
              resetLabel="🔄 再確認一次"
            />
          )}

          {/* 記事區塊 */}
          <div style={{
            background: 'linear-gradient(145deg, #fffbeb, #fef3c7)',
            borderRadius: '28px',
            border: '2px solid #fcd34d',
            boxShadow: '0 4px 20px rgba(251,191,36,0.2)',
            padding: '1.5rem',
            display: 'flex',
            flexDirection: 'column',
            gap: '1rem',
          }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.8rem' }}>
              <div style={{
                background: 'linear-gradient(135deg, #fbbf24, #f59e0b)',
                borderRadius: '14px',
                width: '52px', height: '52px',
                display: 'flex', alignItems: 'center', justifyContent: 'center',
                fontSize: '1.8rem',
                boxShadow: '0 4px 12px rgba(245,158,11,0.3)',
              }}>📓</div>
              <p style={{ fontSize: '1.5rem', fontWeight: '900', color: '#78350f', margin: 0 }}>今天要記的事</p>
            </div>

            {!noteDone ? (
              <>
                <ProgressDots total={noteQuestions.length} current={noteIdx} activeColor="#f59e0b" />
                <QuestionCard
                  emoji={noteQuestions[noteIdx].emoji}
                  question={noteQuestions[noteIdx].question}
                  onYes={() => {
                    const newRecords = [...noteRecords, noteQuestions[noteIdx].label];
                    setNoteRecords(newRecords);
                    speakText('好的，已記下！');
                    if (noteIdx + 1 < noteQuestions.length) {
                      setNoteIdx(noteIdx + 1);
                    } else {
                      setNoteDone(true);
                      speakText(newRecords.length > 0 ? `已記下：${newRecords.join('、')}` : '今天沒有要記的事。');
                    }
                  }}
                  onNo={() => {
                    if (noteIdx + 1 < noteQuestions.length) {
                      setNoteIdx(noteIdx + 1);
                    } else {
                      setNoteDone(true);
                      speakText(noteRecords.length > 0 ? `已記下：${noteRecords.join('、')}` : '今天沒有要記的事。');
                    }
                  }}
                />
              </>
            ) : (
              <>
                {noteRecords.length > 0 ? (
                  <div style={{ display: 'flex', flexDirection: 'column', gap: '0.6rem' }}>
                    {noteRecords.map((label, i) => {
                      const item = noteQuestions.find((n) => n.label === label);
                      return (
                        <div key={i} style={{
                          background: 'linear-gradient(135deg, #fef9c3, #fef08a)',
                          borderRadius: '16px',
                          border: '2px solid #fcd34d',
                          padding: '1rem 1.2rem',
                          display: 'flex',
                          alignItems: 'center',
                          gap: '0.8rem',
                          boxShadow: '0 2px 8px rgba(251,191,36,0.15)',
                        }}>
                          <span style={{ fontSize: '2rem' }}>{item?.emoji}</span>
                          <span style={{ fontSize: '1.5rem', fontWeight: '900', color: '#78350f' }}>{label}</span>
                          <span style={{ marginLeft: 'auto', fontSize: '1.5rem' }}>📌</span>
                        </div>
                      );
                    })}
                  </div>
                ) : (
                  <div style={{
                    background: 'rgba(255,255,255,0.6)',
                    borderRadius: '16px',
                    padding: '1.5rem',
                    textAlign: 'center',
                    border: '2px solid #fde68a',
                  }}>
                    <span style={{ fontSize: '2.5rem' }}>😊</span>
                    <p style={{ fontSize: '1.3rem', fontWeight: '900', color: '#92400e', marginTop: '0.5rem' }}>今天沒有要記的事</p>
                  </div>
                )}
                <button
                  onClick={() => { setNoteIdx(0); setNoteDone(false); setNoteRecords([]); }}
                  style={{
                    borderRadius: '16px',
                    padding: '1rem',
                    background: 'rgba(255,255,255,0.7)',
                    border: '2px solid #fcd34d',
                    fontSize: '1.3rem',
                    fontWeight: '900',
                    color: '#92400e',
                    cursor: 'pointer',
                    boxShadow: '0 2px 8px rgba(251,191,36,0.15)',
                  }}
                >
                  🔄 重新記事
                </button>
              </>
            )}
          </div>

        </div>
      </div>
    );
  }

  // ════════════════════════════════════════════════════════
  // 健康頁
  // ════════════════════════════════════════════════════════
  if (currentPage === 'health') {
    const q = healthQuestions[healthIdx];
    return (
      <div style={{
        minHeight: '100vh',
        background: 'linear-gradient(160deg, #f0fdf4, #dcfce7, #ecfdf5)',
        padding: '1.2rem',
        fontFamily: 'system-ui, sans-serif',
      }}>
        <div style={{ maxWidth: '460px', margin: '0 auto', display: 'flex', flexDirection: 'column', gap: '1.2rem' }}>
          <TopBar
            title="健康狀況"
            gradient="linear-gradient(135deg, #10b981, #059669)"
            icon={<Heart size={22} color="white" />}
          />
          {!healthDone ? (
            <>
              <ProgressDots total={healthQuestions.length} current={healthIdx} activeColor="#10b981" />
              <QuestionCard
                emoji={q.emoji}
                question={q.question}
                onYes={() => {
                  speakText(q.yes);
                  setHealthMsg(q.yes);
                  if (healthIdx + 1 < healthQuestions.length) {
                    setHealthIdx(healthIdx + 1);
                  } else {
                    setHealthDone(true);
                    speakText('健康確認完成了！');
                    setHealthMsg('健康確認完成了！');
                  }
                }}
                onNo={() => {
                  speakText(q.no);
                  setHealthMsg(q.no);
                  if (healthIdx + 1 < healthQuestions.length) {
                    setHealthIdx(healthIdx + 1);
                  } else {
                    setHealthDone(true);
                    speakText('健康確認完成了！');
                    setHealthMsg('健康確認完成了！');
                  }
                }}
              />
              {healthMsg !== '' && (
                <div style={{
                  background: 'linear-gradient(135deg, #f0fdf4, #dcfce7)',
                  borderRadius: '20px',
                  border: '2px solid #86efac',
                  padding: '1.2rem 1.5rem',
                  display: 'flex',
                  alignItems: 'center',
                  gap: '1rem',
                  boxShadow: '0 4px 16px rgba(16,185,129,0.12)',
                }}>
                  <span style={{ fontSize: '2rem' }}>🤖</span>
                  <p style={{ fontSize: '1.4rem', fontWeight: '700', color: '#14532d', margin: 0 }}>{healthMsg}</p>
                </div>
              )}
            </>
          ) : (
            <DoneCard
              emoji="💪"
              message="健康確認完成！今天很棒！"
              onReset={() => { setHealthIdx(0); setHealthDone(false); setHealthMsg(''); }}
              resetLabel="🔄 再確認一次"
            />
          )}
          <BottomNav />
        </div>
      </div>
    );
  }

  // ════════════════════════════════════════════════════════
  // 聊天頁
  // ════════════════════════════════════════════════════════
  if (currentPage === 'chat') {
    const q = chatQuestions[chatIdx];
    return (
      <div style={{
        minHeight: '100vh',
        background: 'linear-gradient(160deg, #eff6ff, #dbeafe, #e0f2fe)',
        padding: '1.2rem',
        fontFamily: 'system-ui, sans-serif',
      }}>
        <div style={{ maxWidth: '460px', margin: '0 auto', display: 'flex', flexDirection: 'column', gap: '1.2rem' }}>
          <TopBar
            title="陪伴聊天"
            gradient="linear-gradient(135deg, #3b82f6, #2563eb)"
            icon={<MessageCircle size={22} color="white" />}
          />
          {!chatDone ? (
            <>
              <ProgressDots total={chatQuestions.length} current={chatIdx} activeColor="#3b82f6" />
              <QuestionCard
                emoji={q.emoji}
                question={q.question}
                onYes={() => {
                  speakText(q.yes);
                  setChatMsg(q.yes);
                  if (chatIdx + 1 < chatQuestions.length) {
                    setChatIdx(chatIdx + 1);
                  } else {
                    setChatDone(true);
                  }
                }}
                onNo={() => {
                  if (chatIdx + 1 < chatQuestions.length) {
                    setChatIdx(chatIdx + 1);
                  } else {
                    setChatDone(true);
                  }
                }}
              />
              {chatMsg !== '' && (
                <div style={{
                  background: 'linear-gradient(135deg, #eff6ff, #dbeafe)',
                  borderRadius: '20px',
                  border: '2px solid #93c5fd',
                  padding: '1.2rem 1.5rem',
                  display: 'flex',
                  alignItems: 'center',
                  gap: '1rem',
                  boxShadow: '0 4px 16px rgba(59,130,246,0.12)',
                }}>
                  <span style={{ fontSize: '2rem' }}>🤖</span>
                  <p style={{ fontSize: '1.4rem', fontWeight: '700', color: '#1e40af', margin: 0 }}>{chatMsg}</p>
                </div>
              )}
            </>
          ) : (
            <>
              <DoneCard
                emoji="🤗"
                message="好的！今天的陪伴安排好了！"
                onReset={() => { setChatIdx(0); setChatDone(false); setChatMsg(''); }}
                resetLabel="🔄 重新選擇"
              />
              <button
                onClick={() => speakText('您好，我在這裡陪著您，請放心。')}
                style={{
                  borderRadius: '22px',
                  background: 'linear-gradient(135deg, #3b82f6, #2563eb)',
                  border: 'none',
                  padding: '1.5rem',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  gap: '1rem',
                  cursor: 'pointer',
                  boxShadow: '0 8px 24px rgba(59,130,246,0.35)',
                  transition: 'all 0.15s ease',
                }}
              >
                <Volume2 size={36} color="white" />
                <span style={{ fontSize: '1.8rem', fontWeight: '900', color: 'white' }}>聽語音陪伴</span>
              </button>
            </>
          )}
          <BottomNav />
        </div>
      </div>
    );
  }

  // ════════════════════════════════════════════════════════
  // 服藥頁
  // ════════════════════════════════════════════════════════
  if (currentPage === 'medication') {
    const q = medQuestions[medIdx];
    return (
      <div style={{
        minHeight: '100vh',
        background: 'linear-gradient(160deg, #fffbeb, #fef3c7, #fef9c3)',
        padding: '1.2rem',
        fontFamily: 'system-ui, sans-serif',
      }}>
        <div style={{ maxWidth: '460px', margin: '0 auto', display: 'flex', flexDirection: 'column', gap: '1.2rem' }}>
          <TopBar
            title="服藥提醒"
            gradient="linear-gradient(135deg, #f59e0b, #d97706)"
            icon={<Pill size={22} color="white" />}
          />
          {!medDone ? (
            <>
              <ProgressDots total={medQuestions.length} current={medIdx} activeColor="#f59e0b" />
              <QuestionCard
                emoji={q.emoji}
                question={q.question}
                onYes={() => {
                  speakText(q.yes);
                  const next = medCount + 1;
                  setMedCount(next);
                  if (medIdx + 1 < medQuestions.length) {
                    setMedIdx(medIdx + 1);
                  } else {
                    setMedDone(true);
                    speakText(`今天吃了 ${next} 次藥，做得很棒！`);
                  }
                }}
                onNo={() => {
                  speakText(q.no);
                  if (medIdx + 1 < medQuestions.length) {
                    setMedIdx(medIdx + 1);
                  } else {
                    setMedDone(true);
                    speakText('服藥確認完成了，記得補吃喔！');
                  }
                }}
              />
            </>
          ) : (
            <DoneCard
              emoji={medCount === 3 ? '🎉' : '💊'}
              message={`今天服藥 ${medCount} / 3 次完成！`}
              onReset={() => { setMedIdx(0); setMedDone(false); setMedCount(0); }}
              resetLabel="🔄 重新確認"
            />
          )}
          <BottomNav />
        </div>
      </div>
    );
  }

  // ════════════════════════════════════════════════════════
  // SOS 頁
  // ════════════════════════════════════════════════════════
  if (currentPage === 'sos') {
    const q = sosQuestions[sosIdx];
    return (
      <div style={{
        minHeight: '100vh',
        background: 'linear-gradient(160deg, #fff1f2, #ffe4e6, #fecdd3)',
        padding: '1.2rem',
        fontFamily: 'system-ui, sans-serif',
      }}>
        <div style={{ maxWidth: '460px', margin: '0 auto', display: 'flex', flexDirection: 'column', gap: '1.2rem' }}>
          <TopBar
            title="緊急求助"
            gradient="linear-gradient(135deg, #ef4444, #dc2626)"
            icon={<span style={{ fontSize: '1.2rem' }}>🆘</span>}
          />
          {!sosDone ? (
            <>
              <ProgressDots total={sosQuestions.length} current={sosIdx} activeColor="#ef4444" />
              <QuestionCard
                emoji={q.emoji}
                question={q.question}
                onYes={() => {
                  speakText(q.yes);
                  setSosMsg(q.yes);
                  if (sosIdx + 1 < sosQuestions.length) {
                    setSosIdx(sosIdx + 1);
                  } else {
                    setSosDone(true);
                  }
                }}
                onNo={() => {
                  if (sosIdx + 1 < sosQuestions.length) {
                    setSosIdx(sosIdx + 1);
                  } else {
                    setSosDone(true);
                    speakText('好的，有需要再按求助。');
                    setSosMsg('好的，有需要再按求助。');
                  }
                }}
              />
              {sosMsg !== '' && (
                <div style={{
                  background: 'linear-gradient(135deg, #fff1f2, #ffe4e6)',
                  borderRadius: '20px',
                  border: '2px solid #fca5a5',
                  padding: '1.2rem 1.5rem',
                  display: 'flex',
                  alignItems: 'center',
                  gap: '1rem',
                  boxShadow: '0 4px 16px rgba(239,68,68,0.12)',
                }}>
                  <span style={{ fontSize: '2rem' }}>🤖</span>
                  <p style={{ fontSize: '1.4rem', fontWeight: '700', color: '#991b1b', margin: 0 }}>{sosMsg}</p>
                </div>
              )}
            </>
          ) : (
            <DoneCard
              emoji="🆘"
              message={sosMsg || '已完成，請保持冷靜。'}
              onReset={() => { setSosIdx(0); setSosDone(false); setSosMsg(''); }}
              resetLabel="🔄 重新求助"
            />
          )}
        </div>
      </div>
    );
  }

  return null;
}
