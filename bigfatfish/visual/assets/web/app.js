/* ==========================================================
   大肥鱼 AI 伴侣 · 前端逻辑
   - WebSocket 流式对话 + HTTP 兜底
   - 情绪驱动主题 / Live2D 表情
   - TTS 播放 + Web Audio 振幅驱动口型同步
   - PWA 注册、设置持久化
   ========================================================== */
(function () {
  'use strict';

  // ---------------- 配置 ----------------
  const DEFAULT_SERVER = (location.protocol === 'file:')
    ? 'http://127.0.0.1:8080'
    : location.origin;

  const DEFAULTS = {
    serverUrl: DEFAULT_SERVER,
    userId: 'me',
    tts: true,
    wallpaper: '',
    model: ''
  };

  let CFG = loadCfg();
  function loadCfg() {
    try { return Object.assign({}, DEFAULTS, JSON.parse(localStorage.getItem('bff_cfg') || '{}')); }
    catch (e) { return Object.assign({}, DEFAULTS); }
  }
  function saveCfg() { localStorage.setItem('bff_cfg', JSON.stringify(CFG)); }

  const $ = (id) => document.getElementById(id);
  const body = document.body;

  // ---------------- 状态 ----------------
  let ws = null;
  let wsRetry = 0;
  let streaming = false;
  let currentBubble = null;
  let audioCtx = null;
  let analyser = null;
  let live2dModel = null;
  let rafId = null;

  const EMOTION_LABEL = {
    happy: '开心', sad: '难过', angry: '生气',
    cute: '可爱', anxious: '担心', neutral: '平静'
  };

  // ---------------- 开机动画 ----------------
  function boot() {
    const canvas = $('boot-canvas');
    const ctx = canvas.getContext('2d');
    let W, H;
    function resize() {
      W = canvas.width = window.innerWidth * devicePixelRatio;
      H = canvas.height = window.innerHeight * devicePixelRatio;
    }
    resize();
    window.addEventListener('resize', resize);

    const dots = Array.from({ length: 46 }, () => ({
      x: Math.random() * W, y: Math.random() * H,
      r: (Math.random() * 2 + .6) * devicePixelRatio,
      v: (Math.random() * .35 + .12) * devicePixelRatio
    }));

    function draw() {
      ctx.clearRect(0, 0, W, H);
      ctx.fillStyle = 'rgba(160,205,255,.55)';
      dots.forEach(d => {
        d.y -= d.v;
        if (d.y < -10) { d.y = H + 10; d.x = Math.random() * W; }
        ctx.beginPath(); ctx.arc(d.x, d.y, d.r, 0, Math.PI * 2); ctx.fill();
      });
      if (!$('boot').classList.contains('done')) requestAnimationFrame(draw);
    }
    draw();

    const tips = ['唤醒记忆中', '整理情绪中', '游向你…'];
    let p = 0;
    const timer = setInterval(() => {
      p = Math.min(100, p + Math.random() * 22 + 8);
      $('boot-progress').style.width = p + '%';
      $('boot-tip').textContent = tips[Math.min(tips.length - 1, Math.floor(p / 34))];
      if (p >= 100) {
        clearInterval(timer);
        setTimeout(() => $('boot').classList.add('done'), 260);
      }
    }, 260);
  }

  // ---------------- 壁纸 ----------------
  function applyWallpaper() {
    const wp = $('wallpaper');
    if (CFG.wallpaper) {
      wp.style.backgroundImage = `linear-gradient(rgba(6,10,26,.35),rgba(6,10,26,.55)), url("${CFG.wallpaper.replace(/"/g, '')}")`;
    } else {
      wp.style.backgroundImage = '';
    }
  }

  // ---------------- 连接 ----------------
  function wsUrl() {
    try {
      const u = new URL(CFG.serverUrl);
      return (u.protocol === 'https:' ? 'wss:' : 'ws:') + '//' + u.host + '/ws';
    } catch (e) { return 'ws://127.0.0.1:8080/ws'; }
  }
  function apiUrl(path) { return CFG.serverUrl.replace(/\/$/, '') + path; }

  function setStatus(state, text) {
    const dot = $('status-dot');
    dot.className = 'dot ' + (state || '');
    $('status-text').textContent = text;
  }

  function connect() {
    if (ws && (ws.readyState === 0 || ws.readyState === 1)) return;
    setStatus('', '连接中…');
    try { ws = new WebSocket(wsUrl()); }
    catch (e) { onDisconnected(); return; }

    ws.onopen = () => {
      wsRetry = 0;
      setStatus('online', '已连接');
      say('我在这儿~ 想聊点什么？');
    };
    ws.onmessage = (ev) => {
      let data;
      try { data = JSON.parse(ev.data); } catch (e) { return; }
      if (data.type === 'stream_start') startStream();
      else if (data.type === 'stream_chunk') appendStream(data.text || '');
      else if (data.type === 'stream_end') endStream(data.full_text || '', data.emotion || 'neutral');
      else if (data.type === 'emotion') setEmotion(data.emotion);
    };
    ws.onclose = onDisconnected;
    ws.onerror = () => { try { ws.close(); } catch (e) {} };
  }

  function onDisconnected() {
    setStatus('offline', '离线 · 将用 HTTP 兜底');
    ws = null;
    wsRetry = Math.min(wsRetry + 1, 6);
    setTimeout(connect, 1500 * wsRetry);   // 指数退避重连
  }

  // ---------------- 聊天 ----------------
  function addMsg(role, text) {
    const row = document.createElement('div');
    row.className = 'msg ' + role;
    const bubble = document.createElement('div');
    bubble.className = 'bubble';
    bubble.textContent = text;
    row.appendChild(bubble);
    $('chat-body').appendChild(row);
    $('chat-body').scrollTop = $('chat-body').scrollHeight;
    return bubble;
  }

  function startStream() {
    streaming = true;
    $('btn-send').disabled = true;
    currentBubble = addMsg('ai', '');
    currentBubble.parentElement.classList.add('typing');
  }
  function appendStream(text) {
    if (!currentBubble) startStream();
    currentBubble.textContent += text;
    $('chat-body').scrollTop = $('chat-body').scrollHeight;
  }
  function endStream(fullText, emotion) {
    streaming = false;
    $('btn-send').disabled = false;
    if (currentBubble) {
      currentBubble.textContent = fullText || currentBubble.textContent;
      currentBubble.parentElement.classList.remove('typing');
      currentBubble = null;
    }
    setEmotion(emotion);
    say(fullText);
    if (CFG.tts && fullText) speak(fullText);
  }

  async function send(text) {
    if (!text || streaming) return;
    addMsg('user', text);
    $('chat-input').value = '';

    // 优先 WebSocket 流式
    if (ws && ws.readyState === 1) {
      ws.send(JSON.stringify({ type: 'chat', text: text, user_id: CFG.userId }));
      return;
    }

    // HTTP 兜底（非流式）
    startStream();
    try {
      const resp = await fetch(apiUrl('/api/chat'), {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ text: text, user_id: CFG.userId })
      });
      const data = await resp.json();
      endStream(data.text || data.error || '（无回复）', data.emotion || 'neutral');
    } catch (e) {
      endStream('连不上后端啦… 检查一下大肥鱼是不是没启动？', 'sad');
    }
  }

  // ---------------- 语音 & 口型同步 ----------------
  async function speak(text) {
    try {
      const resp = await fetch(apiUrl('/api/tts'), {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ text: text })
      });
      if (!resp.ok) return;
      const data = await resp.json();
      if (!data.url) return;                       // 后端未启用 TTS

      const audio = $('tts-audio');
      audio.src = apiUrl(data.url);
      initAudioGraph(audio);
      await audio.play();
      startLipSync();
      audio.onended = stopLipSync;
    } catch (e) { /* 语音不可用不影响文字 */ }
  }

  function initAudioGraph(audio) {
    if (audioCtx) return;                        // MediaElementSource 只能创建一次
    const AC = window.AudioContext || window.webkitAudioContext;
    if (!AC) return;
    try {
      audioCtx = new AC();
      const src = audioCtx.createMediaElementSource(audio);
      analyser = audioCtx.createAnalyser();
      analyser.fftSize = 256;
      src.connect(analyser);
      analyser.connect(audioCtx.destination);
    } catch (e) { analyser = null; }
  }

  function startLipSync() {
    if (rafId) cancelAnimationFrame(rafId);
    if (!analyser) { // 无 Web Audio 时用轻微随机张合作兜底
      let t = 0;
      const tick = () => {
        t += .12;
        setMouth((Math.sin(t * 3) * .5 + .5) * .45);
        rafId = requestAnimationFrame(tick);
      };
      tick();
      return;
    }
    const buf = new Uint8Array(analyser.frequencyBinCount);
    const tick = () => {
      analyser.getByteFrequencyData(buf);
      let sum = 0;
      for (let i = 0; i < buf.length; i++) sum += buf[i];
      const rms = sum / buf.length / 255;
      setMouth(Math.min(1, rms * 2.2));
      rafId = requestAnimationFrame(tick);
    };
    tick();
  }
  function stopLipSync() {
    if (rafId) cancelAnimationFrame(rafId);
    rafId = null;
    setMouth(0);
  }
  function setMouth(v) {
    document.documentElement.style.setProperty('--mouth', v.toFixed(3));
    if (live2dModel && live2dModel.internalModel) {
      try { live2dModel.internalModel.coreModel.setParameterValueById('ParamMouthOpenY', v); }
      catch (e) { /* 模型无此参数 */ }
    }
  }

  // ---------------- 情绪 ----------------
  function setEmotion(emotion) {
    const e = EMOTION_LABEL[emotion] ? emotion : 'neutral';
    body.dataset.emotion = e;
    $('emotion-badge').textContent = EMOTION_LABEL[e];
  }

  function say(text) {
    if (!text) return;
    $('speech-text').textContent = text.length > 60 ? text.slice(0, 60) + '…' : text;
  }

  // ---------------- Live2D（可选，失败自动降级） ----------------
  async function tryLoadLive2D() {
    if (!CFG.model) return;                      // 未配置模型 → 使用内置 CSS 形象
    const base = apiUrl('/live2d/') + CFG.model.replace(/^\/+|\/+$/g, '') + '/';
    const modelJson = base + CFG.model + '.model3.json';

    // 先确认模型文件存在，避免白屏
    try {
      const head = await fetch(modelJson, { method: 'GET' });
      if (!head.ok) return;
    } catch (e) { return; }

    await loadScript('https://cdn.jsdelivr.net/npm/pixi.js@6.5.8/dist/browser/pixi.min.js');
    await loadScript('https://cdn.jsdelivr.net/npm/pixi-live2d-display@0.4.0/dist/cubism4.min.js');
    if (!window.PIXI || !window.PIXI.live2d) return;

    try {
      const app = new PIXI.Application({
        view: $('live2d-canvas'),
        autoStart: true, transparent: true,
        resizeTo: $('avatar-wrap'), backgroundAlpha: 0
      });
      const model = await PIXI.live2d.Live2DModel.from(modelJson);
      app.stage.addChild(model);
      model.scale.set(Math.min($('avatar-wrap').clientWidth / model.width, 1.4));
      model.anchor.set(0.5, 0.5);
      model.x = $('avatar-wrap').clientWidth / 2;
      model.y = $('avatar-wrap').clientHeight / 2;
      live2dModel = model;
      $('live2d-canvas').classList.add('ready');
      $('fallback-avatar').style.display = 'none';
    } catch (e) {
      console.warn('[Live2D] 加载失败，使用内置形象', e);
    }
  }

  function loadScript(src) {
    return new Promise((resolve) => {
      const s = document.createElement('script');
      s.src = src; s.onload = resolve; s.onerror = resolve;
      document.head.appendChild(s);
    });
  }

  // ---------------- 语音输入（浏览器能力） ----------------
  function toggleVoice() {
    const SR = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (!SR) { say('这个环境不支持语音输入，用文字打给我吧~'); return; }
    if (window.__rec) { window.__rec.stop(); window.__rec = null; $('btn-voice').classList.remove('rec'); return; }
    const rec = new SR();
    rec.lang = 'zh-CN'; rec.interimResults = false;
    rec.onresult = (ev) => send(ev.results[0][0].transcript);
    rec.onend = () => { window.__rec = null; $('btn-voice').classList.remove('rec'); };
    rec.onerror = () => { window.__rec = null; $('btn-voice').classList.remove('rec'); say('没听清…再试一次？'); };
    rec.start();
    window.__rec = rec;
    $('btn-voice').classList.add('rec');
    say('在听啦…');
  }

  // ---------------- 设置面板 ----------------
  function openSettings() {
    $('cfg-server').value = CFG.serverUrl;
    $('cfg-user').value = CFG.userId;
    $('cfg-tts').checked = CFG.tts;
    $('cfg-wallpaper').value = CFG.wallpaper;
    $('cfg-model').value = CFG.model;
    $('settings-note').textContent = '';
    $('settings-mask').hidden = false;
  }

  function bindUI() {
    $('btn-send').addEventListener('click', () => send($('chat-input').value.trim()));
    $('chat-input').addEventListener('keydown', (e) => {
      if (e.key === 'Enter') send($('chat-input').value.trim());
    });
    $('btn-voice').addEventListener('click', toggleVoice);
    $('btn-collapse').addEventListener('click', () => $('chat-panel').classList.toggle('collapsed'));
    $('chat-head').addEventListener('click', (e) => {
      if (e.target.id !== 'btn-collapse') $('chat-panel').classList.toggle('collapsed');
    });
    $('btn-settings').addEventListener('click', openSettings);
    $('settings-mask').addEventListener('click', (e) => {
      if (e.target.id === 'settings-mask') $('settings-mask').hidden = true;
    });
    $('btn-save').addEventListener('click', () => {
      CFG.serverUrl = $('cfg-server').value.trim().replace(/\/$/, '') || DEFAULT_SERVER;
      CFG.userId = $('cfg-user').value.trim() || 'me';
      CFG.tts = $('cfg-tts').checked;
      CFG.wallpaper = $('cfg-wallpaper').value.trim();
      CFG.model = $('cfg-model').value.trim();
      saveCfg();
      applyWallpaper();
      $('settings-mask').hidden = true;
      if (ws) { ws.close(); ws = null; }
      connect();
      tryLoadLive2D();
    });
    $('btn-clear-chat').addEventListener('click', () => {
      $('chat-body').innerHTML = '<div class="msg ai"><div class="bubble">聊点新的吧~ 🐟</div></div>';
    });
  }

  // ---------------- PWA ----------------
  function registerSW() {
    if ('serviceWorker' in navigator && location.protocol !== 'file:') {
      navigator.serviceWorker.register('/sw.js', { scope: '/' }).catch(() => {});
    }
  }

  // ---------------- 启动 ----------------
  document.addEventListener('DOMContentLoaded', () => {
    boot();
    bindUI();
    applyWallpaper();
    setEmotion('neutral');
    registerSW();
    connect();
    setTimeout(tryLoadLive2D, 1200);
  });
})();
