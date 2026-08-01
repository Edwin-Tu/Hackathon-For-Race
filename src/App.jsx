import React, { useState, useRef, useEffect } from 'react';
import { Home, Pill, Heart, MessageCircle, Menu, X, Settings, User, LogOut } from 'lucide-react';

// ══════════════════════════════════════════════
// 常數
// ══════════════════════════════════════════════
const DEFAULT_FAMILY = [
  { id: 1, name: '女兒小美', url: 'https://media.giphy.com/media/l0HlBO7eyXzSZkJri/giphy.gif', scene: '服藥提醒', greeting: '媽媽！記得吃藥喔，女兒愛您！❤️' },
  { id: 2, name: '孫子小志', url: 'https://media.giphy.com/media/3o7abKhOpu0NwenH3O/giphy.gif', scene: '健康關懷', greeting: '奶奶！今天有好好照顧自己嗎？😊' },
  { id: 3, name: '兒子大明', url: 'https://media.giphy.com/media/xT9IgG50Lg7russbDa/giphy.gif', scene: '日常陪伴', greeting: '媽！有空記得多休息，我很想您！' },
];

const TODAY_REMINDERS = [
  { question: '今天早上的藥\n吃了嗎？', yes: '太好了，繼續保持！',   no: '記得待會補吃喔！'     },
  { question: '今天有喝水嗎？',         yes: '很棒，繼續補充水分！', no: '記得去倒杯水喔！'     },
  { question: '今天有好好休息嗎？',     yes: '很好，繼續保持！',     no: '記得讓自己休息一下！' },
];

const TITLE_OPTIONS = ['👴 爺爺', '👵 奶奶', '🧑 先生', '👩 女士', '🙂 其他'];

function getGreeting() {
  const h = new Date().getHours();
  if (h >= 5  && h < 12) return { icon: '🌅', text: '早安' };
  if (h >= 12 && h < 18) return { icon: '☀️', text: '午安' };
  return { icon: '🌙', text: '晚安' };
}

// ══════════════════════════════════════════════
// 雙選智慧互動卡（是⭕ / 否❌）
// ══════════════════════════════════════════════
function DualChoiceCard({ question, familyMember, onYes, onNo, accentYes = '#16a34a', accentNo = '#dc2626' }) {
  const [pressed, setPressed] = useState(null);

  const pressedRef = useRef(null);
  const onYesRef   = useRef(onYes);
  const onNoRef    = useRef(onNo);
  useEffect(() => { onYesRef.current = onYes; onNoRef.current = onNo; });

  const triggerYes = () => {
    if (pressedRef.current) return;
    pressedRef.current = 'yes';
    setPressed('yes');
    setTimeout(() => { pressedRef.current = null; setPressed(null); onYesRef.current(); }, 900);
  };

  const triggerNo = () => {
    if (pressedRef.current) return;
    pressedRef.current = 'no';
    setPressed('no');
    setTimeout(() => { pressedRef.current = null; setPressed(null); onNoRef.current(); }, 900);
  };

  const gif  = familyMember?.url  || '';
  const name = familyMember?.name || 'AI';

  return (
    <div style={{ display: 'flex', flexDirection: 'column', borderRadius: '24px', overflow: 'hidden', border: '2px solid #e2e8f0', boxShadow: '0 6px 28px rgba(0,0,0,0.10)' }}>

      {/* 家人 GIF 全寬 */}
      <div style={{ position: 'relative', background: '#0f172a', height: '200px', overflow: 'hidden' }}>
        <img src={gif} alt={name} style={{
          width: '100%', height: '100%', objectFit: 'cover', opacity: 0.85,
        }} onError={e => { e.target.style.display = 'none'; }} />
        <div style={{
          position: 'absolute', bottom: 0, left: 0, right: 0,
          background: 'linear-gradient(transparent, rgba(0,0,0,0.75))',
          padding: '1.2rem 1.4rem 0.8rem',
        }}>
          <p style={{ fontSize: '1.5rem', fontWeight: '900', color: '#fbbf24', margin: 0 }}>{name}</p>
          <p style={{ fontSize: '1rem', color: 'rgba(255,255,255,0.7)', margin: '0.1rem 0 0' }}>想問您：</p>
        </div>
      </div>

      {/* 問題文字 */}
      <div style={{ background: '#1e293b', padding: '1.2rem 1.6rem' }}>
        <p style={{ fontSize: '1.9rem', fontWeight: '900', color: '#fff', margin: 0, lineHeight: 1.4, whiteSpace: 'pre-line', textAlign: 'center' }}>
          {question}
        </p>
      </div>

      {/* 左是 / 右否 */}
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', minHeight: '150px' }}>
        <button onClick={triggerYes} style={{
          background: pressed === 'yes' ? '#bbf7d0' : accentYes,
          border: 'none', cursor: 'pointer',
          display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', gap: '0.5rem',
          padding: '1.4rem',
          transform: pressed === 'yes' ? 'scale(0.96)' : 'scale(1)',
          transition: 'all 0.15s ease',
        }}>
          <span style={{ fontSize: '3.5rem', lineHeight: 1 }}>⭕</span>
          <span style={{ fontSize: '2.2rem', fontWeight: '900', color: '#fff' }}>是</span>
        </button>
        <button onClick={triggerNo} style={{
          background: pressed === 'no' ? '#fecaca' : accentNo,
          border: 'none', borderLeft: '3px solid rgba(255,255,255,0.3)', cursor: 'pointer',
          display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', gap: '0.5rem',
          padding: '1.4rem',
          transform: pressed === 'no' ? 'scale(0.96)' : 'scale(1)',
          transition: 'all 0.15s ease',
        }}>
          <span style={{ fontSize: '3.5rem', lineHeight: 1 }}>❌</span>
          <span style={{ fontSize: '2.2rem', fontWeight: '900', color: '#fff' }}>否</span>
        </button>
      </div>

      {/* 已選回饋 */}
      {pressed && (
        <div style={{ background: pressed === 'yes' ? '#dcfce7' : '#fee2e2', padding: '1rem', textAlign: 'center' }}>
          <span style={{ fontSize: '1.8rem', fontWeight: '900', color: pressed === 'yes' ? '#15803d' : '#dc2626' }}>
            {pressed === 'yes' ? '⭕ 已選擇：是' : '❌ 已選擇：否'}
          </span>
        </div>
      )}

    </div>
  );
}

// ══════════════════════════════════════════════
// 側邊欄
// ══════════════════════════════════════════════
function Sidebar({ open, onClose, onNavigate, currentPage, userName, userTitle, onLogout }) {
  const items = [
    { icon: <Home size={28} />,          label: '首頁',     key: 'home'       },
    { icon: <Pill size={28} />,          label: '服藥提醒', key: 'medication' },
    { icon: <Heart size={28} />,         label: '健康狀況', key: 'health'     },
    { icon: <MessageCircle size={28} />, label: 'AI 陪伴',  key: 'companion'  },
    { icon: <Settings size={28} />,      label: '系統設定', key: 'settings'   },
  ];
  return (
    <>
      <div onClick={onClose} style={{
        position: 'fixed', inset: 0, zIndex: 200,
        background: 'rgba(0,0,0,0.5)',
        opacity: open ? 1 : 0, pointerEvents: open ? 'auto' : 'none',
        transition: 'opacity 0.3s ease',
      }} />
      <div style={{
        position: 'fixed', top: 0, left: 0, bottom: 0, zIndex: 300,
        width: '300px', background: '#0f172a',
        transform: open ? 'translateX(0)' : 'translateX(-100%)',
        transition: 'transform 0.32s cubic-bezier(0.4,0,0.2,1)',
        display: 'flex', flexDirection: 'column',
        boxShadow: '6px 0 40px rgba(0,0,0,0.4)', overflowY: 'auto',
      }}>
        {/* 頭部：帳號資訊 */}
        <div style={{
          padding: '3rem 1.5rem 1.5rem', borderBottom: '1px solid rgba(255,255,255,0.08)',
          background: 'linear-gradient(180deg, #1d4ed8 0%, #1e293b 100%)',
        }}>
          <div style={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.8rem' }}>
              <div style={{
                width: '52px', height: '52px', borderRadius: '50%',
                background: 'rgba(255,255,255,0.2)', border: '2px solid rgba(255,255,255,0.4)',
                display: 'flex', alignItems: 'center', justifyContent: 'center',
                fontSize: '1.6rem', flexShrink: 0,
              }}>
                {userTitle?.split(' ')[0] || '👤'}
              </div>
              <div>
                <p style={{ fontSize: '1.6rem', fontWeight: '900', color: '#fff', margin: 0 }}>
                  {userName || '使用者'}
                </p>
                <p style={{ fontSize: '1rem', color: 'rgba(255,255,255,0.6)', margin: '0.2rem 0 0' }}>
                  {userTitle}
                </p>
              </div>
            </div>
            <button onClick={onClose} style={{
              background: 'rgba(255,255,255,0.12)', border: 'none', borderRadius: '12px',
              padding: '0.7rem', cursor: 'pointer', color: '#fff', display: 'flex', alignItems: 'center',
            }}><X size={26} /></button>
          </div>
          <button onClick={() => { onNavigate('account'); onClose(); }} style={{
            marginTop: '1rem', width: '100%', display: 'flex', alignItems: 'center', gap: '0.6rem',
            background: 'rgba(255,255,255,0.1)', border: '1px solid rgba(255,255,255,0.2)',
            borderRadius: '10px', padding: '0.7rem 1rem', cursor: 'pointer',
            color: '#e2e8f0', fontSize: '1.1rem', fontWeight: '700',
          }}>
            <User size={18} /> 帳號管理
          </button>
        </div>

        {/* 選單 */}
        <div style={{ flex: 1, padding: '1.2rem 0.8rem', display: 'flex', flexDirection: 'column', gap: '0.3rem' }}>
          {items.map(it => {
            const isActive = currentPage === it.key;
            return (
              <button key={it.key} onClick={() => { onNavigate(it.key); onClose(); }} style={{
                display: 'flex', alignItems: 'center', gap: '1rem',
                borderRadius: '14px', padding: '1.1rem 1.3rem',
                background: isActive ? 'rgba(59,130,246,0.25)' : 'transparent',
                border: `1px solid ${isActive ? 'rgba(59,130,246,0.5)' : 'transparent'}`,
                color: isActive ? '#93c5fd' : '#cbd5e1',
                fontSize: '1.5rem', fontWeight: '800', cursor: 'pointer', textAlign: 'left',
                transition: 'all 0.15s ease',
              }}>
                <span style={{ color: isActive ? '#60a5fa' : '#64748b', display: 'flex' }}>{it.icon}</span>
                {it.label}
                {isActive && <span style={{ marginLeft: 'auto', width: '8px', height: '8px', borderRadius: '50%', background: '#3b82f6' }} />}
              </button>
            );
          })}
        </div>

        {/* 登出 */}
        <div style={{ padding: '0.8rem 0.8rem 2.5rem', borderTop: '1px solid rgba(255,255,255,0.08)' }}>
          <button onClick={() => { onLogout(); onClose(); }} style={{
            width: '100%', display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '0.8rem',
            borderRadius: '14px', padding: '1.1rem',
            background: 'rgba(239,68,68,0.12)', border: '1px solid rgba(239,68,68,0.3)',
            color: '#fca5a5', fontSize: '1.4rem', fontWeight: '800', cursor: 'pointer',
          }}>
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

  if (mode === 'choice') return (
    <div style={{
      minHeight: '100vh',
      background: 'linear-gradient(160deg, #1e3a8a 0%, #1d4ed8 60%, #2563eb 100%)',
      display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center',
      gap: '2rem', padding: '2rem', fontFamily: '"Microsoft JhengHei", system-ui',
    }}>
      <div style={{ textAlign: 'center' }}>
        <p style={{ fontSize: '5rem', margin: 0, lineHeight: 1 }}>🛡️</p>
        <h1 style={{ fontSize: '2.8rem', fontWeight: '900', color: '#fff', margin: '0.8rem 0 0' }}>智護聲盾</h1>
        <p style={{ fontSize: '1.4rem', color: 'rgba(255,255,255,0.6)', margin: '0.4rem 0 0' }}>請選擇登入方式</p>
      </div>
      <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem', width: '100%', maxWidth: '340px' }}>
        <button onClick={() => setMode('sms')} style={{
          borderRadius: '20px', padding: '1.6rem 1.4rem', background: '#2563eb', border: 'none',
          display: 'flex', alignItems: 'center', gap: '1.2rem', cursor: 'pointer', textAlign: 'left',
        }}>
          <span style={{ fontSize: '2.5rem' }}>📱</span>
          <div>
            <p style={{ fontSize: '1.6rem', fontWeight: '900', color: '#fff', margin: 0 }}>簡訊驗證碼</p>
            <p style={{ fontSize: '1rem', color: 'rgba(255,255,255,0.75)', margin: '0.2rem 0 0' }}>收簡訊輸入 6 位數字</p>
          </div>
        </button>
        <button onClick={() => setMode('qr')} style={{
          borderRadius: '20px', padding: '1.6rem 1.4rem', background: '#7c3aed', border: 'none',
          display: 'flex', alignItems: 'center', gap: '1.2rem', cursor: 'pointer', textAlign: 'left',
        }}>
          <span style={{ fontSize: '2.5rem' }}>📷</span>
          <div>
            <p style={{ fontSize: '1.6rem', fontWeight: '900', color: '#fff', margin: 0 }}>QR Code 掃描</p>
            <p style={{ fontSize: '1rem', color: 'rgba(255,255,255,0.75)', margin: '0.2rem 0 0' }}>家屬幫忙掃描即可登入</p>
          </div>
        </button>
      </div>
    </div>
  );

  if (mode === 'sms') return (
    <div style={{
      minHeight: '100vh', background: '#0f172a',
      display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center',
      gap: '1.5rem', padding: '2rem', fontFamily: '"Microsoft JhengHei", system-ui',
    }}>
      <p style={{ fontSize: '3rem', margin: 0 }}>📱</p>
      <h2 style={{ fontSize: '2rem', fontWeight: '900', color: '#fff', margin: 0 }}>輸入驗證碼</h2>
      <p style={{ fontSize: '1.3rem', color: 'rgba(255,255,255,0.5)', margin: 0, textAlign: 'center' }}>
        簡訊已傳送至您的手機<br />
        <span style={{ color: '#fbbf24', fontWeight: '700' }}>示範碼：123456</span>
      </p>
      <div style={{ display: 'flex', gap: '0.6rem' }}>
        {Array.from({ length: 6 }).map((_, i) => (
          <div key={i} style={{
            width: '48px', height: '60px', borderRadius: '12px',
            background: code[i] ? 'rgba(255,255,255,0.2)' : 'rgba(255,255,255,0.06)',
            border: `2px solid ${code[i] ? 'rgba(255,255,255,0.5)' : 'rgba(255,255,255,0.15)'}`,
            display: 'flex', alignItems: 'center', justifyContent: 'center',
            fontSize: '2.2rem', fontWeight: '900', color: '#fff',
          }}>{code[i] || ''}</div>
        ))}
      </div>
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3,1fr)', gap: '0.7rem', width: '100%', maxWidth: '300px' }}>
        {[1,2,3,4,5,6,7,8,9,'←',0,'✓'].map((k, i) => (
          <button key={i} onClick={() => {
            if (k === '←') setCode(c => c.slice(0, -1));
            else if (k === '✓') { if (code === DEMO_CODE) onLogin(); else alert('驗證碼錯誤，請再試一次'); }
            else if (code.length < 6) setCode(c => c + k);
          }} style={{
            borderRadius: '14px', padding: '1.2rem 0',
            background: k === '✓' ? '#2563eb' : k === '←' ? '#475569' : 'rgba(255,255,255,0.1)',
            border: '1px solid rgba(255,255,255,0.12)',
            fontSize: k === '✓' ? '1.6rem' : '2rem', fontWeight: '900',
            color: '#fff', cursor: 'pointer',
          }}>{k}</button>
        ))}
      </div>
      <button onClick={() => { setCode(''); setMode('choice'); }} style={{
        background: 'none', border: 'none', color: 'rgba(255,255,255,0.35)', fontSize: '1.2rem', cursor: 'pointer',
      }}>← 返回</button>
    </div>
  );

  if (mode === 'qr') return (
    <div style={{
      minHeight: '100vh', background: '#0f172a',
      display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center',
      gap: '1.8rem', padding: '2rem', fontFamily: '"Microsoft JhengHei", system-ui',
    }}>
      <p style={{ fontSize: '1.6rem', fontWeight: '800', color: '#fff', margin: 0, textAlign: 'center' }}>
        請讓家屬掃描下方 QR Code
      </p>
      <div style={{ width: '200px', height: '200px', borderRadius: '20px', background: '#fff', padding: '12px', display: 'flex', alignItems: 'center', justifyContent: 'center', boxShadow: '0 8px 32px rgba(0,0,0,0.4)' }}>
        <img src="https://api.qrserver.com/v1/create-qr-code/?size=176x176&data=zhihu-shield-login-demo" alt="QR Code"
          style={{ width: '176px', height: '176px', borderRadius: '8px' }}
          onError={e => { e.target.style.display = 'none'; }}
        />
      </div>
      <button onClick={() => onLogin()} style={{
        borderRadius: '16px', padding: '1.2rem 2rem', background: '#7c3aed', border: 'none',
        fontSize: '1.4rem', fontWeight: '800', color: '#fff', cursor: 'pointer',
      }}>✅ 模擬掃描成功</button>
      <button onClick={() => setMode('choice')} style={{
        background: 'none', border: 'none', color: 'rgba(255,255,255,0.35)', fontSize: '1.2rem', cursor: 'pointer',
      }}>← 返回</button>
    </div>
  );
}

// ══════════════════════════════════════════════
// SOS 固定按鈕
// ══════════════════════════════════════════════
function SOSBtn({ onPress }) {
  return (
    <button onClick={onPress} style={{
      position: 'fixed', bottom: '88px', right: '14px', zIndex: 500,
      width: '68px', height: '68px', borderRadius: '50%',
      background: '#dc2626', border: '4px solid #fca5a5',
      display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center',
      cursor: 'pointer', animation: 'sosPulse 2s infinite',
      boxShadow: '0 4px 20px rgba(220,38,38,0.55)',
    }}>
      <span style={{ fontSize: '1.6rem', lineHeight: 1 }}>🆘</span>
      <span style={{ fontSize: '0.6rem', color: '#fff', fontWeight: '900', marginTop: '1px' }}>SOS</span>
    </button>
  );
}

// ══════════════════════════════════════════════
// 主程式
// ══════════════════════════════════════════════
export default function ElderApp() {
  const [loggedIn,    setLoggedIn]    = useState(false);
  const [page,        setPage]        = useState('home');
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [sosActive,   setSosActive]   = useState(false);
  const [sosTrigger,  setSosTrigger]  = useState({});

  // 帳號
  const [userName,  setUserName]  = useState(() => localStorage.getItem('userName')  || '王');
  const [userTitle, setUserTitle] = useState(() => localStorage.getItem('userTitle') || '👵 奶奶');

  // 家人 GIF（固定，可由後台替換 DEFAULT_FAMILY 常數）
  const family = DEFAULT_FAMILY;

  // 服藥
  const [meds, setMeds] = useState([
    { id: 1, time: '08:00', name: '降血壓藥', taken: false },
    { id: 2, time: '12:00', name: '維他命',   taken: false },
    { id: 3, time: '18:00', name: '心臟藥',   taken: false },
  ]);

  // 服藥「否」提示
  const [medNoMsg,    setMedNoMsg]    = useState('');
  // 健康頁回饋
  const [healthMsg,   setHealthMsg]   = useState('');

  // 陪伴
  const [companionMsg, setCompanionMsg] = useState('');

  // 首頁輪播
  const [reminderIdx, setReminderIdx] = useState(0);

  // 系統設定
  const [fontSize,   setFontSize]   = useState(() => localStorage.getItem('fontSize')   || 'medium');
  const fontScale = fontSize === 'small' ? 0.85 : fontSize === 'large' ? 1.18 : 1;

  // 把縮放比例直接套到 html 根元素，這樣所有 rem 單位都會縮放
  useEffect(() => {
    document.documentElement.style.fontSize = `${fontScale * 16}px`;
    return () => { document.documentElement.style.fontSize = ''; };
  }, [fontScale]);

  const medFamily    = family[0];
  const healthFamily = family[1];
  const companionFam = family[2];

  const takeMed = (id) => {
    setMeds(prev => prev.map(m => m.id === id ? { ...m, taken: true } : m));
  };

  const handleNavigate = (key) => {
    const pages = ['home','medication','health','companion','settings','account'];
    if (pages.includes(key)) setPage(key);
  };

  const handleLogout = () => {
    setLoggedIn(false);
    setPage('home');
  };

  // 登入
  if (!loggedIn) return <LoginPage onLogin={() => setLoggedIn(true)} />;

  // SOS 頁
  if (sosActive) {
    const ACTIONS = [
      { label: '📞 通知家屬 — 女兒小美', msg: '正在撥打給女兒小美，請稍候！'    },
      { label: '👩‍⚕️ 通知照護員',         msg: '正在通知照護員，請稍候！'        },
      { label: '🚑 撥打緊急聯絡人',       msg: '正在撥打緊急聯絡人，請保持冷靜！'},
    ];
    return (
      <div style={{
        minHeight: '100vh', background: '#dc2626',
        display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center',
        gap: '1.5rem', padding: '2rem', fontFamily: '"Microsoft JhengHei", system-ui',
      }}>
        <span style={{ fontSize: '5rem', animation: 'sosPulse 1s infinite' }}>🆘</span>
        <h1 style={{ fontSize: '2.8rem', fontWeight: '900', color: '#fff', margin: 0, textAlign: 'center' }}>緊急求助中</h1>
        <p style={{ fontSize: '1.5rem', color: 'rgba(255,255,255,0.85)', margin: 0, textAlign: 'center' }}>
          請點下方按鈕通知相關人員<br />請保持冷靜
        </p>
        <div style={{ display: 'flex', flexDirection: 'column', gap: '0.8rem', width: '100%', maxWidth: '360px' }}>
          {ACTIONS.map((a, i) => {
            const done = !!sosTrigger[i];
            return (
              <button key={i} onClick={() => { if (done) return; setSosTrigger(p => ({ ...p, [i]: true })); }} style={{
                borderRadius: '16px', padding: '1.3rem 1.5rem',
                background: done ? 'rgba(255,255,255,0.35)' : 'rgba(255,255,255,0.15)',
                border: `2px solid ${done ? 'rgba(255,255,255,0.7)' : 'rgba(255,255,255,0.3)'}`,
                display: 'flex', alignItems: 'center', gap: '1rem',
                cursor: done ? 'default' : 'pointer', width: '100%', textAlign: 'left',
              }}>
                <span style={{ fontSize: '1.6rem', color: '#fff', fontWeight: '900', flex: 1 }}>{a.label}</span>
                <span style={{ fontSize: '1.8rem' }}>{done ? '✅' : '▶'}</span>
              </button>
            );
          })}
        </div>
        {Object.keys(sosTrigger).length > 0 && (
          <div style={{ background: 'rgba(255,255,255,0.2)', borderRadius: '14px', padding: '1rem 1.5rem', width: '100%', maxWidth: '360px', textAlign: 'center' }}>
            <p style={{ fontSize: '1.4rem', fontWeight: '800', color: '#fff', margin: 0 }}>
              ✅ 已通知 {Object.keys(sosTrigger).length} 位 — 幫助正在趕來！
            </p>
          </div>
        )}
        <button onClick={() => { setSosActive(false); setSosTrigger({}); }} style={{
          borderRadius: '14px', padding: '1.2rem 2.5rem',
          background: 'rgba(255,255,255,0.2)', border: '2px solid rgba(255,255,255,0.4)',
          fontSize: '1.5rem', fontWeight: '800', color: '#fff', cursor: 'pointer', marginTop: '0.5rem',
        }}>取消 / 我沒事了</button>
      </div>
    );
  }

  // 共用元件
  const TopBar = () => (
    <div style={{
      position: 'sticky', top: 0, zIndex: 100, background: '#fff', borderBottom: '1px solid #e2e8f0',
      padding: '0.8rem 1rem', display: 'flex', alignItems: 'center', justifyContent: 'space-between',
      maxWidth: '640px', margin: '0 auto', boxSizing: 'border-box', width: '100%',
    }}>
      <button onClick={() => setSidebarOpen(true)} style={{
        display: 'flex', alignItems: 'center', justifyContent: 'center',
        background: '#f1f5f9', border: '1px solid #e2e8f0', borderRadius: '12px',
        padding: '0.6rem', cursor: 'pointer', color: '#374151',
      }}><Menu size={28} /></button>
      <p style={{ fontSize: '1.4rem', fontWeight: '900', color: '#1e293b', margin: 0 }}>
        {getGreeting().icon} {userName} {userTitle}
      </p>
      <button onClick={() => setSosActive(true)} style={{
        background: '#fee2e2', border: '2px solid #fca5a5', borderRadius: '12px',
        padding: '0.5rem 0.8rem', cursor: 'pointer', fontSize: '1.2rem', fontWeight: '800', color: '#dc2626',
      }}>🆘</button>
    </div>
  );

  const NAV = [
    { key: 'home',       label: '首頁', icon: <Home size={24} /> },
    { key: 'medication', label: '服藥', icon: <Pill size={24} /> },
    { key: 'health',     label: '健康', icon: <Heart size={24} /> },
    { key: 'companion',  label: '陪伴', icon: <MessageCircle size={24} /> },
  ];
  const BottomNav = () => (
    <div style={{
      position: 'fixed', bottom: 0, left: 0, right: 0, zIndex: 100,
      display: 'flex', justifyContent: 'center', background: '#fff', borderTop: '2px solid #e2e8f0', padding: '0.4rem 0 0.6rem',
    }}>
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4,1fr)', width: '100%', maxWidth: '640px', gap: '0.2rem', padding: '0 0.4rem' }}>
        {NAV.map(n => (
          <button key={n.key} onClick={() => setPage(n.key)} style={{
            display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '0.15rem',
            border: 'none', cursor: 'pointer', borderRadius: '12px', padding: '0.5rem 0',
            background: page === n.key ? '#eff6ff' : 'transparent',
            color: page === n.key ? '#2563eb' : '#94a3b8',
            fontWeight: '800', fontSize: '0.85rem',
          }}>
            {n.icon}<span>{n.label}</span>
          </button>
        ))}
      </div>
    </div>
  );

  const PageWrap = ({ children, bg = '#f0f7ff' }) => (
    <div style={{ minHeight: '100vh', background: bg, fontFamily: '"Microsoft JhengHei", system-ui, sans-serif', paddingBottom: '80px' }}>
      <Sidebar open={sidebarOpen} onClose={() => setSidebarOpen(false)} currentPage={page} onNavigate={handleNavigate} userName={userName} userTitle={userTitle} onLogout={handleLogout} />
      <TopBar />
      <div style={{ maxWidth: '640px', margin: '0 auto', padding: '1rem', display: 'flex', flexDirection: 'column', gap: '1rem' }}>
        {children}
      </div>
    </div>
  );

  // ════════════════════════════════════════════
  // 首頁
  // ════════════════════════════════════════════
  if (page === 'home') {
    const cur = TODAY_REMINDERS[reminderIdx % TODAY_REMINDERS.length];
    return (
      <PageWrap>
        <DualChoiceCard
          question={cur.question}
          familyMember={family[0]}
          accentYes="#16a34a" accentNo="#dc2626"
          onYes={() => { setReminderIdx(i => i + 1); }}
          onNo={()  => { setReminderIdx(i => i + 1); }}
        />
        <SOSBtn onPress={() => setSosActive(true)} />
        <BottomNav />
      </PageWrap>
    );
  }

  // ════════════════════════════════════════════
  // 服藥頁
  // ════════════════════════════════════════════
  if (page === 'medication') {
    const unfinished = meds.filter(m => !m.taken);
    const allDone    = unfinished.length === 0;
    const cur        = unfinished[0];
    return (
      <PageWrap bg="#fffbeb">
        <div style={{ display: 'flex', alignItems: 'center' }}>
          <h1 style={{ fontSize: '1.8rem', fontWeight: '900', color: '#92400e', margin: 0 }}>💊 服藥確認</h1>
          <span style={{ fontSize: '1.2rem', color: '#b45309', fontWeight: '700', marginLeft: 'auto' }}>
            {meds.filter(m => m.taken).length} / {meds.length} 完成
          </span>
        </div>
        <div style={{ display: 'flex', gap: '0.6rem', justifyContent: 'center' }}>
          {meds.map(m => (
            <div key={m.id} style={{ width: '32px', height: '32px', borderRadius: '50%', background: m.taken ? '#22c55e' : '#e2e8f0', display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: '1rem' }}>
              {m.taken ? '✓' : ''}
            </div>
          ))}
        </div>
        {allDone ? (
          <div style={{ background: '#f0fdf4', borderRadius: '20px', padding: '2.5rem', textAlign: 'center', border: '2px solid #86efac' }}>
            <p style={{ fontSize: '3rem', margin: 0 }}>🎉</p>
            <p style={{ fontSize: '2rem', fontWeight: '900', color: '#15803d', margin: '0.8rem 0 0' }}>今日服藥全部完成！</p>
            <button onClick={() => setMeds(p => p.map(m => ({ ...m, taken: false })))} style={{
              marginTop: '1.2rem', borderRadius: '12px', padding: '0.9rem 1.5rem',
              background: '#f1f5f9', border: '1px solid #e2e8f0', fontSize: '1.2rem', fontWeight: '700', color: '#475569', cursor: 'pointer',
            }}>🔄 重置（測試用）</button>
          </div>
        ) : (
          <>
            <DualChoiceCard
              question={`${cur.time} 的 ${cur.name}\n吃了嗎？`}
              familyMember={medFamily}
              accentYes="#16a34a" accentNo="#dc2626"
              onYes={() => { takeMed(cur.id); setMedNoMsg(''); }}
              onNo={() => setMedNoMsg(`${cur.name} 還沒吃，記得待會補吃喔！`)}
            />
            {medNoMsg && (
              <div style={{ background: '#fffbeb', borderRadius: '12px', padding: '1rem', border: '1px solid #fcd34d', textAlign: 'center' }}>
                <p style={{ fontSize: '1.3rem', fontWeight: '700', color: '#92400e', margin: 0 }}>⚠️ {medNoMsg}</p>
              </div>
            )}
          </>
        )}
        <SOSBtn onPress={() => setSosActive(true)} />
        <BottomNav />
      </PageWrap>
    );
  }

  // ════════════════════════════════════════════
  // 健康頁
  // ════════════════════════════════════════════
  if (page === 'health') {
    return (
      <PageWrap bg="#f0fdf4">
        <h1 style={{ fontSize: '1.8rem', fontWeight: '900', color: '#065f46', margin: 0 }}>❤️ 今日健康</h1>
        <DualChoiceCard
          question="今天有量血壓嗎？"
          familyMember={healthFamily}
          accentYes="#2563eb" accentNo="#64748b"
          onYes={() => setHealthMsg('很好！持續記錄對健康很有幫助！')}
          onNo={() => setHealthMsg('記得找個時間量一下，對健康很重要喔！')}
        />
        {healthMsg && (
          <div style={{ background: '#f0fdf4', borderRadius: '12px', padding: '1rem', border: '1px solid #86efac', textAlign: 'center' }}>
            <p style={{ fontSize: '1.3rem', fontWeight: '700', color: '#065f46', margin: 0 }}>✅ {healthMsg}</p>
          </div>
        )}
        <SOSBtn onPress={() => setSosActive(true)} />
        <BottomNav />
      </PageWrap>
    );
  }

  // ════════════════════════════════════════════
  // 陪伴頁
  // ════════════════════════════════════════════
  if (page === 'companion') {
    return (
      <PageWrap bg="#eff6ff">
        <h1 style={{ fontSize: '1.8rem', fontWeight: '900', color: '#1e40af', margin: 0 }}>💬 AI 陪伴</h1>
        {companionMsg && (
          <div style={{ background: '#fff', borderRadius: '16px', padding: '1.2rem', border: '2px solid #bfdbfe', display: 'flex', gap: '0.8rem' }}>
            <span style={{ fontSize: '2rem' }}>🤖</span>
            <div style={{ flex: 1 }}>
              <p style={{ fontSize: '1.5rem', fontWeight: '700', color: '#1e40af', margin: 0, lineHeight: 1.5 }}>{companionMsg}</p>
            </div>
          </div>
        )}
        <DualChoiceCard
          question="今天心情還好嗎？"
          familyMember={companionFam}
          accentYes="#7c3aed" accentNo="#0891b2"
          onYes={() => setCompanionMsg('太好了！保持好心情，我們隨時陪著您！')}
          onNo={()  => setCompanionMsg('沒關係，我在這裡陪著您，有什麼心事都可以說喔！')}
        />
        <SOSBtn onPress={() => setSosActive(true)} />
        <BottomNav />
      </PageWrap>
    );
  }

  // ════════════════════════════════════════════
  // 帳號管理頁
  // ════════════════════════════════════════════
  if (page === 'account') {
    const saveAccount = () => {
      localStorage.setItem('userName',  userName);
      localStorage.setItem('userTitle', userTitle);
      setPage('home');
    };
    return (
      <PageWrap bg="#f0f7ff">
        <h1 style={{ fontSize: '1.8rem', fontWeight: '900', color: '#1e293b', margin: 0 }}>👤 帳號管理</h1>

        <div style={{ background: 'linear-gradient(135deg, #1d4ed8, #2563eb)', borderRadius: '20px', padding: '1.8rem', display: 'flex', alignItems: 'center', gap: '1.2rem' }}>
          <div style={{ width: '72px', height: '72px', borderRadius: '50%', background: 'rgba(255,255,255,0.2)', border: '3px solid rgba(255,255,255,0.5)', display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: '2.2rem', flexShrink: 0 }}>
            {userTitle?.split(' ')[0] || '👤'}
          </div>
          <div>
            <p style={{ fontSize: '2rem', fontWeight: '900', color: '#fff', margin: 0 }}>{userName || '未設定'}</p>
            <p style={{ fontSize: '1.2rem', color: 'rgba(255,255,255,0.7)', margin: '0.2rem 0 0' }}>{userTitle}</p>
          </div>
        </div>

        <div style={{ background: '#fff', borderRadius: '16px', padding: '1.4rem', border: '1px solid #e2e8f0', display: 'flex', flexDirection: 'column', gap: '0.8rem' }}>
          <label style={{ fontSize: '1.2rem', fontWeight: '800', color: '#374151' }}>姓（例：王、李、陳）</label>
          <input value={userName} onChange={e => setUserName(e.target.value.slice(0,1))} placeholder="請輸入一個字的姓"
            style={{ width: '100%', boxSizing: 'border-box', borderRadius: '12px', border: '2px solid #e2e8f0', padding: '1rem', fontSize: '1.6rem', fontWeight: '700', color: '#1e293b', outline: 'none' }}
            onFocus={e => e.target.style.borderColor = '#2563eb'}
            onBlur={e  => e.target.style.borderColor = '#e2e8f0'}
          />
        </div>

        <div style={{ background: '#fff', borderRadius: '16px', padding: '1.4rem', border: '1px solid #e2e8f0', display: 'flex', flexDirection: 'column', gap: '0.8rem' }}>
          <label style={{ fontSize: '1.2rem', fontWeight: '800', color: '#374151' }}>稱謂</label>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3,1fr)', gap: '0.6rem' }}>
            {TITLE_OPTIONS.map(t => (
              <button key={t} onClick={() => setUserTitle(t)} style={{
                borderRadius: '12px', padding: '0.9rem 0.4rem',
                border: `2px solid ${userTitle === t ? '#2563eb' : '#e2e8f0'}`,
                background: userTitle === t ? '#eff6ff' : '#fff',
                fontSize: '1.1rem', fontWeight: '800',
                color: userTitle === t ? '#1d4ed8' : '#64748b', cursor: 'pointer',
              }}>{t}</button>
            ))}
          </div>
        </div>

        <div style={{ background: '#fff', borderRadius: '16px', padding: '1.4rem', border: '1px solid #fca5a5' }}>
          <p style={{ fontSize: '1.2rem', fontWeight: '800', color: '#374151', margin: '0 0 0.8rem' }}>帳號操作</p>
          <button onClick={handleLogout} style={{
            width: '100%', display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '0.8rem',
            borderRadius: '14px', padding: '1.2rem', background: '#fee2e2', border: '2px solid #fca5a5',
            fontSize: '1.5rem', fontWeight: '800', color: '#dc2626', cursor: 'pointer',
          }}>
            <LogOut size={24} /> 登出帳號
          </button>
          <p style={{ fontSize: '1rem', color: '#94a3b8', margin: '0.6rem 0 0', textAlign: 'center' }}>登出後需重新登入才能使用</p>
        </div>

        <button onClick={saveAccount} style={{
          width: '100%', borderRadius: '14px', padding: '1.3rem', background: '#10b981', border: 'none',
          fontSize: '1.6rem', fontWeight: '900', color: '#fff', cursor: 'pointer',
        }}>✅ 儲存並返回</button>
      </PageWrap>
    );
  }

  // ════════════════════════════════════════════
  // 系統設定頁
  // ════════════════════════════════════════════
  if (page === 'settings') {
    const FONT_OPT = [{ key:'small', label:'小' },{ key:'medium', label:'中' },{ key:'large', label:'大' }];

    const saveAndBack = () => {
      localStorage.setItem('fontSize', fontSize);
      setPage('home');
    };

    return (
      <PageWrap bg="#f8fafc">
        <h1 style={{ fontSize: '1.8rem', fontWeight: '900', color: '#1e293b', margin: 0 }}>⚙️ 系統設定</h1>

        {/* 字體大小 */}
        <div style={{ background: '#fff', borderRadius: '16px', padding: '1.4rem', border: '1px solid #e2e8f0' }}>
          <p style={{ fontSize: '1.3rem', fontWeight: '800', color: '#374151', margin: '0 0 1rem' }}>🔡 字體大小</p>
          <div style={{ display: 'flex', gap: '0.8rem' }}>
            {FONT_OPT.map(f => (
              <button key={f.key} onClick={() => setFontSize(f.key)} style={{
                flex: 1, borderRadius: '14px', padding: '1.1rem 0',
                border: `3px solid ${fontSize === f.key ? '#2563eb' : '#e2e8f0'}`,
                background: fontSize === f.key ? '#eff6ff' : '#fff',
                fontSize: f.key === 'small' ? '1rem' : f.key === 'large' ? '1.5rem' : '1.2rem',
                fontWeight: '900', color: fontSize === f.key ? '#1d4ed8' : '#64748b', cursor: 'pointer',
              }}>{f.label}</button>
            ))}
          </div>
        </div>

        {/* 服藥時間管理 */}
        <div style={{ background: '#fff', borderRadius: '16px', padding: '1.4rem', border: '1px solid #e2e8f0' }}>
          <p style={{ fontSize: '1.3rem', fontWeight: '800', color: '#374151', margin: '0 0 1rem' }}>💊 服藥時間管理</p>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '0.7rem' }}>
            {meds.map((m, i) => (
              <div key={m.id} style={{ display: 'flex', alignItems: 'center', gap: '0.8rem' }}>
                <input type="time" value={m.time}
                  onChange={e => setMeds(p => p.map((x, xi) => xi === i ? { ...x, time: e.target.value } : x))}
                  style={{ borderRadius: '10px', border: '1px solid #e2e8f0', padding: '0.7rem', fontSize: '1.4rem', fontWeight: '700', color: '#1e293b', background: '#f8fafc', outline: 'none', width: '130px' }}
                />
                <input type="text" value={m.name}
                  onChange={e => setMeds(p => p.map((x, xi) => xi === i ? { ...x, name: e.target.value } : x))}
                  style={{ flex: 1, borderRadius: '10px', border: '1px solid #e2e8f0', padding: '0.7rem', fontSize: '1.3rem', fontWeight: '700', color: '#1e293b', background: '#f8fafc', outline: 'none' }}
                />
                <button onClick={() => setMeds(p => p.filter((_, xi) => xi !== i))} style={{
                  background: '#fee2e2', border: '1px solid #fca5a5', borderRadius: '8px',
                  padding: '0.5rem 0.8rem', cursor: 'pointer', fontSize: '1.2rem', color: '#dc2626',
                }}>✕</button>
              </div>
            ))}
          </div>
          <button onClick={() => setMeds(p => [...p, { id: Date.now(), time: '09:00', name: '新藥物', taken: false }])} style={{
            marginTop: '0.8rem', width: '100%', borderRadius: '12px', padding: '0.9rem',
            background: '#eff6ff', border: '1px solid #bfdbfe',
            fontSize: '1.2rem', fontWeight: '700', color: '#2563eb', cursor: 'pointer',
          }}>＋ 新增藥物</button>
        </div>

        <button onClick={saveAndBack} style={{
          width: '100%', borderRadius: '14px', padding: '1.3rem',
          background: '#10b981', border: 'none',
          fontSize: '1.6rem', fontWeight: '900', color: '#fff', cursor: 'pointer',
        }}>✅ 儲存並返回</button>
      </PageWrap>
    );
  }

  return null;
}
