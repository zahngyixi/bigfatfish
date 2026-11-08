# 大肥鱼 AI 伴侣 - 打包方案总览

> 目标：让这套 Python 项目以「能装到手机上、点开就用」的形态运行。
>
> 先说结论：**Python 后端无法原样塞进一个纯 APK**，但我们提供了三种可立即落地的形态，
> 其中 **WebView 壳是真 APK**，**PWA 是无需编译的等价体验**，**Termux 包是本机一键部署**。

---

## 一、为什么不能直接 `pip install` 进 APK

Android 不是普通 Linux，它用 **Bionic libc**（不是 glibc），且没有标准 Python 运行时。
把 CPython 打进 APK 是可行的（Chaquopy / python-for-android），但本项目里这些依赖会卡住：

| 依赖 | 卡点 |
|------|------|
| `chromadb` | 依赖 `duckdb` + `hnswlib`，均无 Android 预编译 wheel / p4a recipe |
| `sherpa-onnx` | 官方只提供 Linux aarch64 (glibc) wheel，不提供 Android Bionic 版 |
| `faster-whisper` | 依赖 CTranslate2，同上 |
| `numpy` / `pydub` | 需交叉编译；p4a 有 numpy recipe，但组合起来仍要处理 |
| `torch` | **已主动排除**，ARM64 + Bionic 下基本不可行 |
| `redis-server` | APK 内不能跑独立 Redis 进程（代码已支持内存降级） |

因此「一个 APK 装完全部功能」需要重写记忆层与语音层，工作量约等于另起一个项目。
**当前交付选择的是工程上最稳的路线：前端进 APK、后端跑 Termux 或云端。**

---

## 二、四种形态对比

| 形态 | 产物 | 后端位置 | 真 APK | 离线可用 | 适合谁 |
|------|------|----------|--------|----------|--------|
| **① PWA** | `bigfatfish/visual/assets/web/` | Termux / 云端 | ❌ | 界面可离线 | 想马上看到效果、不想编译 |
| **② WebView 壳 APK** | `android-webview/` | Termux `127.0.0.1:8080` / 云端 | ✅ | 取决于后端 | 想要桌面图标 + 全屏 APP |
| **③ Termux 一键包** | `termux/` | 手机本机 | ❌ | ✅ | 后端就想跑在自己手机上 |
| **④ 全本地 Python APK** | 未实现（改造清单见第六节） | APK 内 | ✅ | ✅ | 有 Android NDK 经验的开发者 |

推荐组合：
- **只挂 QQ**：用 ③ Termux 包 + `QQ_SETUP_GUIDE.md`，连 WebView 都不用开
- **要 APP 图标**：③ 起后端 + ② 装 APK 壳（或 ① 添加到主屏幕）
- **不想折腾手机**：后端丢云端 + ① PWA，扫码即用

---

## 三、形态 ① PWA（零编译，立即可用）

已补齐的文件：

```
bigfatfish/visual/assets/web/
├── index.html          液态玻璃 UI + 开机动画 + Live2D 容器
├── styles.css          Glassmorphism / 手机安全区适配
├── app.js              WebSocket 流式对话 + 情绪驱动 + TTS 口型同步
├── manifest.json       standalone 全屏、桌面图标
├── sw.js               Service Worker（离线开壳）
└── icons/              icon-192 / 512 / 512-maskable
```

后端配合（`bigfatfish/visual/ui_server.py` 已实现）：
- `GET  /sw.js` —— SW 必须从**根路径**提供才能控制 `/` 作用域
- `POST /api/tts` —— 返回 `/tts/xxx.mp3`，前端用 Web Audio 分析振幅驱动嘴型
- `GET  /tts/*` —— 静态音频目录
- **CORS 中间件** —— 允许 APK 壳 / 局域网 / 云端跨域访问

使用步骤：
```bash
# 1. 起后端
python -m bigfatfish.main

# 2. 手机浏览器访问（启动时会打印二维码）
http://<手机或电脑IP>:8080

# 3. 浏览器菜单 → 「添加到主屏幕」
```
添加后就是全屏、有图标、无地址栏的 APP，体验和原生壳基本一致。

> Live2D：把模型目录放到 `bigfatfish/visual/assets/live2d_models/<模型名>/`，
> 在设置里填模型名即可；不填或加载失败会自动降级为内置会眨眼/摆尾/张嘴的 CSS 小鱼。

---

## 四、形态 ② WebView 壳 APK（真 APK）

工程在 `android-webview/`，纯 Java + WebView，APK 约 2MB。

```
android-webview/
├── settings.gradle / build.gradle / gradle.properties
├── gradle/wrapper/gradle-wrapper.properties
├── app/build.gradle                       (AGP 8.1.4, minSdk 24, targetSdk 34)
├── app/src/main/AndroidManifest.xml
├── app/src/main/java/com/bigfatfish/app/MainActivity.java
├── app/src/main/res/{values,xml,mipmap-*}
└── README.md
```

关键配置：
- `BACKEND_URL = "http://127.0.0.1:8080"` —— 打开即全屏加载本机 Termux 后端
- `network_security_config.xml` —— Android 9+ 默认禁明文 HTTP，已放行 `127.0.0.1` / 局域网段
- `setMediaPlaybackRequiresUserGesture(false)` —— 允许 TTS 自动播放
- `android:usesCleartextTraffic="true"` + `usesCleartextTrafficPermitted`

### 拿 APK 的两种方式

**A. GitHub Actions 云构建（推荐，不需要本地 Android SDK）**

`.github/workflows/build-apk.yml` 已配好：
1. push 到 GitHub（或手动 `workflow_dispatch`）
2. Actions 里跑 `./gradlew assembleRelease`
3. 在 Artifacts 下载 `bigfatfish-release.apk`

**B. 本地编译**
```bash
cd android-webview
./gradlew assembleRelease
# 输出: app/build/outputs/apk/release/app-release.apk
```
> 需要 JDK 17 + Android SDK 34。仓库里没有 `gradlew` 可执行文件（Windows 上生成不便），
> 本地编译前在 Android Studio 里打开该目录一次，或运行 `gradle wrapper` 生成即可。
> 云构建路径不受影响（workflow 里的 `chmod +x gradlew` 需要该文件存在，见下方备注）。

> ⚠ **备注**：若走云构建，请先在本地/Android Studio 生成 `gradlew` + `gradle-wrapper.jar`
> 并提交，或把 workflow 的构建步骤改成 `gradle assembleRelease`（Ubuntu runner 自带 gradle 时）。
> 这是当前工程唯一需要你补一步的地方，其余文件均已齐备。

### 使用顺序
1. Termux 里起后端：`python -m bigfatfish.main`
2. 装 APK、点开 → 自动加载 `127.0.0.1:8080`
3. 若后端在云端/局域网，改 `MainActivity.java` 的 `BACKEND_URL` 后重新编译

---

## 五、形态 ③ Termux 一键包（含 QQ 常驻）

```
termux/
├── bootstrap.sh              一键装依赖 + 拉代码 + 生成 .env + 配置快捷方式
├── widget/启动大肥鱼.sh       Termux:Widget 桌面一键启动
├── widget/停止大肥鱼.sh       Termux:Widget 桌面一键停止
├── boot/bigfatfish-boot.sh    Termux:Boot 开机自启
└── README.md
```

```bash
# Termux 里
curl -fsSL https://<你的仓库>/raw/main/termux/bootstrap.sh | bash
nano .env          # 填 DEEPSEEK_API_KEY、QQ_BOT_QQ
python -m bigfatfish.main
```

装 **Termux:Widget** 后桌面会有「启动大肥鱼 / 停止大肥鱼」两个图标；
装 **Termux:Boot** 后手机重启会自动拉起后端，QQ 机器人 7×24 在线。

### 和 QQ 怎么配合
- 大肥鱼默认 `QQ_WS_MODE=reverse`，**监听 3001**，等 NapCat/Lagrange 连过来
- NapCat 可以跑在同一台手机（Termux 里装 nodejs）或任意一台电脑/服务器
- 详细配置见 [QQ_SETUP_GUIDE.md](<QQ_SETUP_GUIDE.md>)
- 云端部署大肥鱼时，NapCat 的 `reverse.ws.urls` 填 `ws://<云端IP>:3001` 并放行端口

---

## 六、形态 ④ 全本地 Python APK（改造清单，未实现）

如果你确实要把 Python 后端也塞进 APK，两条可行路线：

### 路线 A: Chaquopy（Android Studio 插件，改动最小）
1. `app/build.gradle` 加 `com.chaquo.python` 插件，指定 `buildPython` 与 abiFilters `arm64-v8a`
2. `pip` 块只装 `requirements-lite.txt`（纯 Python 包）
3. 用 `Python.getInstance().getModule("bigfatfish.main")` 启动 asyncio 循环
4. 把 Web UI 的 aiohttp 服务绑到 `127.0.0.1:8080`，WebView 仍加载该地址

### 路线 B: python-for-android / Buildozer（Kivy 系）
1. `buildozer.spec` 里 `requirements = python3,pyjnius,android,flask,...`
2. 为 `aiohttp` / `edge-tts` / `bilibili-api-python` 写自定义 recipe
3. 用 Android `Service` 保活后台

### 必须替换的模块
| 模块 | 替换方案 |
|------|----------|
| `chromadb` 长期记忆 | `sqlite3` + 关键词/TF-IDF 检索（或用 `hnswlib` 的 NDK 编译版） |
| `redis` 短期记忆 | 已内置内存字典降级，直接关掉 Redis 即可 |
| `sherpa-onnx` ASR | 调 Android 原生 `SpeechRecognizer` 通过 Pyjnius，或改云端 ASR API |
| `faster-whisper` | 删除 |
| `pydub` + `numpy` | 用 Android `MediaCodec` 或让云端返回文本 |
| `pyttsx3` | 删除，只保留 `edge-tts`（需要网络） |
| `Pillow / qrcode` | 可留（有 recipe），或删掉二维码功能 |

### 已知代价
- APK 体积 ~40–80MB，冷启动 3–8 秒
- 后台保活受厂商省电策略限制，需要前台 Service + 常驻通知
- DeepSeek API 仍需联网，所以「全离线」本来就不成立

> 结论：因为 DeepSeek 无论如何都要联网，**把后端放云端 + 前端 PWA/壳 APK** 是性价比最高的方案。

---

## 七、常见坑速查

| 现象 | 原因 | 处理 |
|------|------|------|
| APK 打开白屏 | 后端没起 / 明文 HTTP 被拦 | 先起后端；确认 `network_security_config.xml` 生效 |
| PWA 不能「添加到主屏幕」 | SW 装在 `/static/` 作用域 | 已改为从根路径 `/sw.js` 提供 |
| 聊天能发但没语音 | `/api/tts` 返回 `tts_disabled` | `.env` 里 `TTS_ENABLED=true`，且装了 `edge-tts` |
| QQ 连不上 3001 | 正反 WS 方向配反 | 见 [QQ_SETUP_GUIDE.md](<QQ_SETUP_GUIDE.md>) 的「方向」表格 |
| `import bigfatfish` 失败 | 用了 `cd bigfatfish && python main.py` | 已统一改成 `python -m bigfatfish.main`，并在 `main.py` 加了 sys.path 兜底 |
| 图标缺失 | 没跑图标脚本 | `python tools/make_icons.py` |
| chromadb 编译失败 | Termux 缺 Rust 工具链 | `pkg install rust clang cmake`；或改用 `requirements-lite.txt` |

---

## 八、自检

```bash
python tools/check_syntax.py     # Python 语法 / JSON / 静态资源 / Android 工程完整性
python tools/make_icons.py       # 重新生成 PWA + APK 图标
```
