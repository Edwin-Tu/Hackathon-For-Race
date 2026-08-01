const screen = document.getElementById('screen');
const voiceBtn = document.getElementById('voiceBtn');

const views = {
  home: `
    <div class="home-view">
      <h2>今天想做什麼？</h2>
      <div class="grid-actions">
        <button class="action big" data-target="health">🩺 健康</button>
        <button class="action big" data-target="companion">💬 陪伴聊天</button>
        <button class="action big" data-target="medication">💊 吃藥提醒</button>
        <button class="action big emergency" data-target="emergency">📞 緊急求助</button>
      </div>
      <button class="secondary-btn" data-target="family">👨‍👩‍👧 家屬功能</button>
    </div>
  `,
  health: `
    <div class="screen-card">
      <h2>🩺 健康</h2>
      <div class="info-row"><span>今日步數</span><strong>8,420 步</strong></div>
      <div class="info-row"><span>心率</span><strong>76 次/分</strong></div>
      <div class="info-row"><span>血壓</span><strong>118/76</strong></div>
      <div class="info-row"><span>睡眠</span><strong>7.2 小時</strong></div>
      <div class="quick-item">
        <strong>今日健康建議</strong>
        <p>多喝水，下午可以散步 10 分鐘。</p>
      </div>
      <button class="med-btn" data-target="home">量測紀錄</button>
      <button class="back-btn" data-target="home">返回首頁</button>
    </div>
  `,
  companion: `
    <div class="screen-card">
      <h2>💬 AI 陪伴</h2>
      <button class="med-btn">🎤 一鍵語音聊天</button>
      <div class="info-row"><span>今日心情</span><strong>開心</strong></div>
      <div class="quick-item"><strong>📖 說故事</strong><p>陪您聽一個溫暖的小故事。</p></div>
      <div class="quick-item"><strong>🎵 聽音樂</strong><p>播放輕柔的古典音樂。</p></div>
      <div class="quick-item"><strong>🧠 小遊戲</strong><p>記憶力小測驗，試試看。</p></div>
      <button class="back-btn" data-target="home">返回首頁</button>
    </div>
  `,
  medication: `
    <div class="screen-card">
      <h2>💊 吃藥提醒</h2>
      <div class="med-item"><strong>上午 8:00</strong><p>阿司匹靈 1 顆</p></div>
      <div class="med-item"><strong>中午 12:00</strong><p>降血壓藥 1 顆</p></div>
      <div class="med-item"><strong>晚上 6:00</strong><p>維他命 1 顆</p></div>
      <button class="med-btn">✅ 已服藥</button>
      <button class="back-btn" data-target="home">返回首頁</button>
    </div>
  `,
  emergency: `
    <div class="screen-card">
      <h2>📞 緊急求助</h2>
      <button class="emergency-btn">🆘 SOS 求救</button>
      <div class="list-item"><strong>撥打家屬</strong><p>立即聯絡家人確認狀況。</p></div>
      <div class="list-item"><strong>撥打照護員</strong><p>安排即時支援。</p></div>
      <div class="list-item"><strong>撥打 119</strong><p>若情況危急，請立即求助。</p></div>
      <button class="back-btn" data-target="home">返回首頁</button>
    </div>
  `,
  family: `
    <div class="screen-card">
      <h2>👨‍👩‍👧 家屬功能</h2>
      <div class="list-item"><strong>查看長者位置</strong><p>目前位於家中客廳。</p></div>
      <div class="list-item"><strong>今日是否吃藥</strong><p>上午已服藥，下午待提醒。</p></div>
      <div class="list-item"><strong>健康數據</strong><p>步數與睡眠皆維持穩定。</p></div>
      <div class="list-item"><strong>AI聊天紀錄摘要</strong><p>已與長者聊過心情與故事。</p></div>
      <div class="list-item"><strong>異常通知</strong><p>心率略高，建議關注。</p></div>
      <button class="back-btn" data-target="home">返回首頁</button>
    </div>
  `
};

function render(view) {
  screen.innerHTML = views[view] || views.home;
  screen.querySelectorAll('[data-target]').forEach((btn) => {
    btn.addEventListener('click', () => render(btn.dataset.target));
  });
}

voiceBtn.addEventListener('click', () => {
  const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
  if (!SpeechRecognition) {
    alert('此瀏覽器不支援語音辨識，請使用 Chrome。');
    return;
  }

  const recognition = new SpeechRecognition();
  recognition.lang = 'zh-TW';
  recognition.start();
  voiceBtn.textContent = '🎤 辨識中...';

  recognition.onresult = (event) => {
    const result = event.results[0][0].transcript;
    voiceBtn.textContent = '🎤 語音操作';
    if (result.includes('健康')) {
      render('health');
    } else if (result.includes('陪伴') || result.includes('聊天')) {
      render('companion');
    } else if (result.includes('藥')) {
      render('medication');
    } else if (result.includes('緊急') || result.includes('求救')) {
      render('emergency');
    } else if (result.includes('家屬')) {
      render('family');
    } else {
      render('home');
    }
  };

  recognition.onerror = () => {
    voiceBtn.textContent = '🎤 語音操作';
  };
});

render('home');
