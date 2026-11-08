# 大肥鱼 AI 伴侣 - 快速安装指南

## 🚀 一键部署 (推荐)

### Termux (Android)

```bash
# 1. 打开 Termux，进入项目目录
cd ~/bigfatfish

# 2. 运行部署脚本
bash deploy.sh

# 3. 编辑配置 (必须配置 DEEPSEEK_API_KEY)
nano .env

# 4. 启动程序
bash start.sh
```

### Linux

```bash
bash deploy.sh
nano .env
bash start.sh
```

### Windows

```bash
REM 在项目目录按 Win+R，输入 cmd，然后：
deploy.bat
REM 编辑 .env 文件
start.bat
```

---

## ⚙️ 必需配置

在 `.env` 文件中配置以下项目：

```bash
# 必需：DeepSeek API Key
DEEPSEEK_API_KEY=sk-xxxxxxxxxxxxxxxxxxxxxxxx

# 可选：QQ 接入
QQ_ENABLED=true
QQ_WS_MODE=reverse
QQ_WEBSOCKET_URL=ws://0.0.0.0:3001
QQ_BOT_QQ=123456789

# 可选：Redis (如果不配置，使用内存缓存)
REDIS_HOST=localhost
REDIS_PORT=6379
```

---

## 🎯 接入平台

### QQ (NapCatQQ)

1. 安装 NapCatQQ: https://github.com/NapNeko/NapCatQQ
2. 配置反向 WebSocket: `ws://127.0.0.1:3001`（NapCat 连向大肥鱼）
3. 在 `.env` 中配置 `QQ_BOT_QQ` 和 `QQ_ADMIN_LIST`
4. **先启动大肥鱼，再启动 NapCat**（大肥鱼是服务端）
5. 详见 `QQ_SETUP_GUIDE.md`

### Web UI

程序启动后自动显示二维码，用手机扫描访问。

---

## 📱 API Key 获取

访问 https://platform.deepseek.com 申请 API Key。

---

## 🐛 常见问题

**Q: pip 安装慢怎么办？**
```bash
pip config set global.index-url https://mirrors.aliyun.com/pypi/simple/
```

**Q: chromadb 编译失败？**
```bash
# Termux 需要先安装编译工具
pkg install rust clang cmake
pip install --no-cache-dir chromadb==0.4.24
```

**Q: 如何看日志？**
```bash
tail -f bigfatfish/logs/bigfatfish.log
```

---

更多详情见 `README.md`
