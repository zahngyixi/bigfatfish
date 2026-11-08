# 大肥鱼 AI 伴侣 🐟

<div align="center">

**基于 DeepSeek 的手机端 AI 虚拟伴侣系统**

[![Python](https://img.shields.io/badge/Python-3.10+-blue.svg)](https://www.python.org/)
[![Platform](https://img.shields.io/badge/Platform-Android%20Termux%20%7C%20Linux%20%7C%20Windows-green.svg)]()
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)]()

*轻量化 · 模块化 · 跨平台 · 长期记忆 · 多模态交互*

</div>

---

## 📌 项目简介

**大肥鱼** 是一个运行在手机端（Android Termux）或轻量化云端的 AI 虚拟伴侣系统，核心大脑使用 **DeepSeek API**。系统支持：

- ✅ **多平台接入**: QQ (NapCat/Lagrange) + Bilibili + Web UI
- ✅ **完整记忆系统**: 短期记忆 (Redis) + 长期记忆 (ChromaDB) + Prompt 人设锁定
- ✅ **多模态交互**: 语音识别 (sherpa-onnx/faster-whisper) + 语音合成 (edge-tts)
- ✅ **拟人化情感**: 主动问候 + 表情包系统 + 文生图 (HuggingFace/Pollinations.AI)
- ✅ **Web 前端**: Live2D 视觉呈现 + 液态玻璃 UI + 手机扫码即用

---

## 🎯 核心特性

### 1. 全平台消息网关
- **QQ 接入**: 基于 NapCatQQ / Lagrange (OneBot v11)，支持群聊 @触发 和 私聊自动回复
- **Bilibili 接入**: 监听私信消息和动态评论区
- **Web UI**: 手机浏览器访问，扫码即用，实时对话

### 2. 长短期记忆系统
- **短期记忆**: Redis 缓存最近 N 轮对话，自动压缩上下文
- **长期记忆**: ChromaDB 向量检索，自动提取关键事实（用户偏好、重要事件等）
- **完全体记忆**: 强制注入系统级 Persona，防止 AI 遗忘人设

### 3. 拟人化情感交互
- **主动问候**: 定时检测用户离线时长，超过 N 小时主动发起对话
- **表情包系统**: AI 回复附带情绪标签（happy/sad/angry/cute），自动匹配表情包
- **文生图**: 集成 HuggingFace / Pollinations.AI 免费 API，支持"画个图"指令

### 4. 多模态语音通讯
- **语音识别 (ASR)**: sherpa-onnx (ARM64 官方支持) / faster-whisper 备用
- **语音合成 (TTS)**: edge-tts 在线合成，支持温柔女声（zh-CN-XiaoxiaoNeural）

### 5. 视觉呈现 (Web UI)
- **Live2D 渲染**: 模型随 TTS 口型同步（Lip-sync）
- **液态玻璃风格**: Glassmorphism 动态壁纸 + 开机动画
- **手机适配**: 响应式设计，二维码扫码访问

---

## 🚀 快速开始

### 环境要求

| 环境 | 要求 |
|------|------|
| **操作系统** | Android Termux (ARM64) / Linux / Windows |
| **Python** | 3.10+ (推荐 3.11) |
| **Redis** | 可选（短期记忆，Termux 可用 `pkg install redis`） |
| **DeepSeek API Key** | 必需（申请: https://platform.deepseek.com） |

---

### 一键部署 (Termux / Linux)

```bash
# 1. 克隆项目
git clone https://github.com/your-repo/bigfatfish.git
cd bigfatfish

# 2. 运行部署脚本
bash deploy.sh

# 3. 编辑配置文件
nano .env
# 必须配置: DEEPSEEK_API_KEY=your_api_key_here

# 4. 启动程序
./start.sh
# 或: python -m bigfatfish.main
```

**部署脚本会自动完成：**
- ✅ 安装系统依赖 (Python, Redis, ffmpeg, espeak 等)
- ✅ 安装 ARM64 兼容的 Python 依赖
- ✅ 下载 sherpa-onnx 中文语音识别模型
- ✅ 创建启动脚本

---

### Windows 部署

```powershell
# 1. 克隆项目
git clone https://github.com/your-repo/bigfatfish.git
cd bigfatfish

# 2. 双击运行 deploy.bat

# 3. 编辑 .env 文件，配置 DEEPSEEK_API_KEY

# 4. 双击 start.bat 启动
```

---

## ⚙️ 配置说明

编辑 `.env` 文件（参考 `bigfatfish/config/example.env`）：

```bash
# ========== DeepSeek API 配置 ==========
DEEPSEEK_API_KEY=your_deepseek_api_key_here

# ========== QQ 接入配置 ==========
QQ_ENABLED=true
QQ_WS_MODE=reverse
QQ_WEBSOCKET_URL=ws://0.0.0.0:3001
QQ_BOT_QQ=123456789
QQ_GROUP_KEYWORDS=大肥鱼,小鱼

# ========== Redis 配置 ==========
REDIS_HOST=localhost
REDIS_PORT=6379

# ========== 语音配置 ==========
TTS_ENABLED=true
TTS_VOICE=zh-CN-XiaoxiaoNeural
ASR_ENABLED=false  # 语音识别需要下载模型

# ========== Web UI 配置 ==========
WEB_UI_HOST=0.0.0.0
WEB_UI_PORT=8080

# ========== 主动交互配置 ==========
ACTIVE_INTERACTION_ENABLED=true
ACTIVE_INTERVAL_HOURS=6
```

---

## 📱 接入平台配置

### QQ (NapCatQQ / Lagrange)

**方案一: NapCatQQ (推荐)**
1. 在手机/PC 上安装 [NapCatQQ](https://github.com/NapNeko/NapCatQQ)
2. 配置反向 WebSocket: `ws://<大肥鱼IP>:3001`（同机填 `ws://127.0.0.1:3001`）
3. 在 `.env` 中设置 `QQ_WS_MODE=reverse`、`QQ_WEBSOCKET_URL=ws://0.0.0.0:3001`
4. **先启动大肥鱼**（它是服务端），再启动 NapCat

详细步骤见 [QQ_SETUP_GUIDE.md](<QQ_SETUP_GUIDE.md>)。

**方案二: Lagrange**
1. 安装 [Lagrange.OneBot](https://github.com/LagrangeDev/Lagrange.Core)
2. 配置 OneBot v11 反向 WebSocket
3. 同上设置 `.env`

### Bilibili

1. 登录 B 站，获取 Cookie:
   - `SESSDATA`
   - `bili_jct`
   - `buvid3`
2. 在 `.env` 中配置:
   ```bash
   BILIBILI_ENABLED=true
   BILIBILI_SESSDATA=your_sessdata
   BILIBILI_BILI_JCT=your_bili_jct
   BILIBILI_BUVID3=your_buvid3
   ```

### Web UI

程序启动后会自动显示二维码，用手机浏览器扫描即可访问。

---

## 📂 项目结构

```
bigfatfish/
├── core/                          # 核心大脑
│   ├── deepseek_agent.py          # DeepSeek API 交互 + 流式处理
│   ├── memory_manager.py          # 长短期记忆管理
│   ├── persona_engine.py          # 人设系统 + 情感逻辑
│   └── context_compressor.py      # 上下文压缩
│
├── gateway/                       # 全平台消息网关
│   ├── router.py                  # 消息路由与分发
│   ├── qq_adapter.py              # QQ (NapCat/Lagrange)
│   ├── bilibili_adapter.py        # B站接入
│   └── frequency_control.py       # 频控防风控
│
├── memory/                        # 记忆存储层
│   ├── redis_cache.py             # 短期记忆 (Redis)
│   ├── chromadb_store.py          # 长期记忆 (ChromaDB)
│   └── memory_extractor.py        # 自动提取关键事实
│
├── multimodal/                    # 多模态交互
│   ├── asr_engine.py              # 语音识别 (sherpa-onnx)
│   ├── tts_engine.py              # 语音合成 (edge-tts)
│   ├── emotion_system.py          # 表情包系统
│   └── image_gen.py               # 文生图 (HF/Pollinations)
│
├── visual/                        # 视觉呈现
│   ├── ui_server.py               # Web UI 服务器
│   └── assets/                    # 资源目录
│       ├── live2d_models/         # Live2D 模型
│       ├── emoticon_packs/        # 表情包库
│       └── web/                   # Web 前端
│
├── scheduler/                     # 定时任务引擎
│   └── active_interaction.py      # 主动发起对话
│
├── config/                        # 配置文件
│   ├── settings.py                # 全局配置
│   ├── prompts.py                 # Prompt 模板库
│   └── example.env                # 环境变量示例
│
├── main.py                        # 主程序入口
├── requirements.txt               # ARM64 兼容依赖
├── deploy.sh                      # Termux/Linux 部署脚本
└── deploy.bat                     # Windows 部署脚本
```

---

## 🛠️ ARM64 兼容性说明

本项目**完全兼容 Android Termux ARM64 环境**，所有依赖均经过验证：

| 模块 | 方案 | ARM64 支持 |
|------|------|-----------|
| **语音合成** | edge-tts | ✅ 纯 Python，无 C 扩展 |
| **语音识别** | sherpa-onnx | ✅ 官方提供 aarch64 wheel |
| **语音识别 (备用)** | faster-whisper | ✅ CTranslate2 ARM64 支持 |
| **向量数据库** | ChromaDB | ✅ 0.4.x 版本支持 ARM64 |
| **文生图** | HuggingFace API | ✅ 纯 HTTP 调用，无本地 GPU 依赖 |
| **Live2D** | Web 渲染 | ✅ 浏览器原生支持 |

**不兼容方案已排除：**
- ❌ openai-whisper (依赖 torch，ARM64 安装困难)
- ❌ 本地 Stable Diffusion (需要 CUDA，手机无法运行)

---

## 📝 使用示例

### 1. 私聊对话 (QQ)
```
用户: 今天好累啊
AI: 辛苦啦~ 要不要休息一下，我陪你聊聊天呢 😊 [emotion: cute]
[附带表情包: cute_01.jpg]
```

### 2. 群聊 @触发 (QQ)
```
用户: @大肥鱼 帮我画个夕阳下的海滩
AI: 好哒，正在生成图片... 🎨
[几秒后发送生成的图片]
```

### 3. 主动问候
```
[用户 6 小时未互动]
AI: 好久不见啦~ 最近工作还好吗？记得要好好休息哦 💕 [emotion: cute]
```

### 4. 语音对话
```
用户: [发送语音消息]
AI: [识别] "明天天气怎么样"
AI: [回复文本 + 语音] "我帮你查一下~ ..."
```

---

## 🎨 自定义

### 1. 修改人设 (Persona)

编辑 `bigfatfish/config/prompts.py` 中的 `SYSTEM_PERSONA`：

```python
SYSTEM_PERSONA = f"""你是"{settings.PERSONA_NAME}"，一个温柔可爱、善解人意的 AI 伴侣。

【核心人设】
- 性别：{settings.PERSONA_GENDER}
- 年龄：{settings.PERSONA_AGE}
- 性格特点：温柔体贴、活泼可爱、善于倾听...
"""
```

### 2. 添加表情包

将图片放到 `bigfatfish/visual/assets/emoticon_packs/` 对应分类目录：
- `happy/` - 开心
- `sad/` - 难过
- `angry/` - 生气
- `cute/` - 可爱/撒娇

### 3. 更换 TTS 声线

编辑 `.env`，可选声线：
```bash
TTS_VOICE=zh-CN-XiaoxiaoNeural  # 小晓（温柔）
TTS_VOICE=zh-CN-XiaoYiNeural    # 小依（活泼）
TTS_VOICE=zh-CN-XiaochenNeural  # 晓辰（甜美）
```

查看所有中文声线：
```python
from bigfatfish.multimodal import TTSEngine
import asyncio

async def list_voices():
    tts = TTSEngine()
    voices = await tts.list_voices()
    for v in voices:
        print(f"{v['name']} - {v['gender']} - {v['friendly_name']}")

asyncio.run(list_voices())
```

---

## 🐛 故障排查

### 1. ChromaDB 安装失败 (Termux)
```bash
# 安装 Rust 编译器
pkg install rust clang cmake

# 重新安装
pip install chromadb==0.4.24
```

### 2. Redis 连接失败
```bash
# 启动 Redis
redis-server --daemonize yes --dir ./data/redis

# 或禁用 Redis（程序会自动切换到内存缓存）
# 编辑 .env: REDIS_HOST=
```

### 3. sherpa-onnx 模型下载失败
手动下载模型：
```bash
cd models
wget https://github.com/k2-fsa/sherpa-onnx/releases/download/asr-models/sherpa-onnx-streaming-zipformer-zh-14M-2023-02-23.tar.bz2
tar -xjf sherpa-onnx-streaming-zipformer-zh-14M-2023-02-23.tar.bz2
mv sherpa-onnx-streaming-zipformer-zh-14M-2023-02-23/* sherpa-onnx/
```

### 4. Web UI 无法访问
检查防火墙，确保端口 8080 开放：
```bash
# Termux (需要 root)
iptables -I INPUT -p tcp --dport 8080 -j ACCEPT

# 或使用其他端口，编辑 .env
WEB_UI_PORT=8888
```

---

## 🤝 贡献

欢迎提交 Issue 和 Pull Request！

### 开发路线图
- [ ] 微信接入（基于 WeChaty）
- [ ] 更多 TTS 引擎（如豆包、GPT-SoVITS）
- [ ] Live2D 口型同步优化
- [ ] Docker 一键部署
- [ ] 多用户权限管理

---

## 📄 许可证

MIT License

---

## 💬 交流群

- QQ 群: (待建)
- Telegram: (待建)

---

## 🙏 致谢

- [DeepSeek](https://www.deepseek.com/) - AI 核心引擎
- [NapCatQQ](https://github.com/NapNeko/NapCatQQ) - QQ 接入方案
- [sherpa-onnx](https://github.com/k2-fsa/sherpa-onnx) - ARM64 语音识别
- [edge-tts](https://github.com/rany2/edge-tts) - 免费 TTS 方案
- [ChromaDB](https://www.trychroma.com/) - 向量数据库

---

<div align="center">

**如果这个项目对你有帮助，请给个 ⭐️ Star 吧！**

Made with ❤️ by [Your Name]

</div>
