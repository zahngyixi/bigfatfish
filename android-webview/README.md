# 大肥鱼 AI 伴侣 - Android WebView 壳

这是一个**纯壳 APK 工程**，打开后全屏加载 `http://127.0.0.1:8080`（Termux 本机后端）。

## 📦 APK 获取方式

### 方案一：GitHub Actions 云构建（推荐，无需本地 Android SDK）

1. 把整个项目 push 到 GitHub
2. GitHub Actions 会自动编译 APK
3. 在 Actions 页面下载 `bigfatfish-release.apk`

### 方案二：本地编译（需要 Android Studio / Android SDK）

```bash
cd android-webview
./gradlew assembleRelease
# 输出: app/build/outputs/apk/release/app-release.apk
```

## 🔧 使用步骤

1. **在 Termux 里启动后端**
   ```bash
   cd ~/bigfatfish
   python -m bigfatfish.main
   # 确保后端运行在 http://127.0.0.1:8080
   ```

2. **安装 APK 并打开**
   - APK 会自动全屏加载本机后端
   - 所有功能（聊天、语音、Live2D）都在 WebView 里运行

3. **如果后端在云端/局域网**
   - 修改 `MainActivity.java` 里的 `BACKEND_URL`
   - 重新编译 APK

## 📱 技术说明

- **纯 WebView 壳**：APK 本身只有 2MB 左右，不包含 Python 后端
- **后端要求**：必须在 Termux 或云端先启动 `bigfatfish` Python 后端
- **网络权限**：允许明文 HTTP 访问 `127.0.0.1` 和局域网段
- **自动播放**：`setMediaPlaybackRequiresUserGesture(false)` 支持 TTS 自动播放
- **PWA 互补**：APK 是"原生壳"体验，PWA 是"添加到主屏幕"体验，功能完全一致

## 🎨 图标

图标由 `tools/make_icons.py` 自动生成到 `app/src/main/res/mipmap-*/`，无需手动设计。

## ⚠️ 注意事项

- Android 9+ 默认禁止明文 HTTP，已通过 `network_security_config.xml` 允许 `127.0.0.1`
- 如果后端未启动，APK 会白屏/加载失败，属于正常现象
- 返回键会触发 WebView 历史回退，而不是直接退出 APP

---

**如果需要把 Python 后端也打包进 APK（全本地，不依赖 Termux）**，请参考 `PACKAGING.md` 的 Chaquopy / python-for-android 方案，但工作量巨大且需要重写依赖（chromadb/sherpa-onnx 无现成 Android recipe）。
