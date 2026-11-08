/* 大肥鱼 AI 伴侣 · Service Worker
   - 只缓存静态壳资源，保证离线也能打开 APP 界面
   - /api/ /tts/ /ws /live2d/ 一律走网络，绝不缓存动态内容
   注意：此文件由后端从根路径 /sw.js 提供（scope=/）
*/
const CACHE = 'bff-shell-v1';

const ASSETS = [
  '/',
  '/static/index.html',
  '/static/styles.css',
  '/static/app.js',
  '/static/manifest.json',
  '/static/icons/icon-192.png',
  '/static/icons/icon-512.png'
];

self.addEventListener('install', (event) => {
  event.waitUntil(
    caches.open(CACHE).then(async (cache) => {
      // 逐个添加，单个资源缺失不影响整体安装
      for (const url of ASSETS) {
        try { await cache.add(url); } catch (e) { /* ignore */ }
      }
      await self.skipWaiting();
    })
  );
});

self.addEventListener('activate', (event) => {
  event.waitUntil(
    caches.keys()
      .then((keys) => Promise.all(
        keys.filter((k) => k !== CACHE).map((k) => caches.delete(k))
      ))
      .then(() => self.clients.claim())
  );
});

const DYNAMIC = /^\/(api|tts|ws|live2d)(\/|$)/;

self.addEventListener('fetch', (event) => {
  const req = event.request;
  if (req.method !== 'GET') return;

  let url;
  try { url = new URL(req.url); } catch (e) { return; }
  if (url.origin !== self.location.origin) return;      // 不碰跨域（CDN / 云端 API）
  if (DYNAMIC.test(url.pathname)) return;                // 动态内容交给网络

  event.respondWith(
    caches.match(req).then((hit) => {
      if (hit) return hit;
      return fetch(req).then((resp) => {
        if (resp && resp.ok && resp.type === 'basic') {
          const copy = resp.clone();
          caches.open(CACHE).then((c) => c.put(req, copy)).catch(() => {});
        }
        return resp;
      }).catch(() => caches.match('/'));                 // 断网时回退到壳
    })
  );
});
