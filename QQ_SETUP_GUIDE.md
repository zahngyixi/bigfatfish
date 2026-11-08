# QQ 机器人接入指南

## 📱 方案选择

大肥鱼通过 **OneBot v11 协议** 接入 QQ，需要先在手机/PC 上运行一个 QQ 客户端 + OneBot 适配器。推荐两个方案：

| 方案 | 优势 | 适用场景 |
|------|------|----------|
| **NapCatQQ** | 官方 QQ（NT 架构），稳定性好，支持语音/图片/表情包 | 推荐，功能最全 |
| **Lagrange** | 纯 C# 实现，轻量级，支持 Linux 无头运行 | 服务器端，不需要图形界面 |

> **重要：WebSocket 方向要对得上。**
> 大肥鱼支持两种模式，由 `.env` 的 `QQ_WS_MODE` 决定：
>
> | 模式 | 谁监听端口 | 谁主动连接 | NapCat 侧配置 |
> |------|-----------|-----------|--------------|
> | `reverse`（默认，推荐） | **大肥鱼** 监听 3001 | NapCat 连过来 | `reverse.ws.urls` 填 `ws://<大肥鱼IP>:3001` |
> | `forward` | **NapCat** 监听 3001 | 大肥鱼连过去 | `ws` 段开启服务端并监听 3001 |
>
> 本指南下面的 NapCat / Lagrange 示例都是 **reverse 模式**，与默认配置匹配。

---

## 🚀 方案一：NapCatQQ（推荐）

### 1. 安装 NapCatQQ

#### Windows / macOS

1. 下载官方 QQ：https://im.qq.com/pcqq
2. 下载 NapCatQQ：https://github.com/NapNeko/NapCatQQ/releases
3. 解压 NapCatQQ，双击 `napcat.exe`（Windows）或 `napcat`（macOS）
4. 首次启动会弹出登录窗口，扫码登录你的机器人 QQ 号

#### Android Termux（和大肥鱼在同一台手机）

```bash
# 1. 安装 Node.js
pkg install nodejs-lts

# 2. 下载 NapCatQQ (Android 版本)
cd ~
git clone https://github.com/NapNeko/NapCatQQ.git
cd NapCatQQ
npm install

# 3. 启动（首次会生成配置文件）
npm start
# 按提示扫码登录
```

### 2. 配置反向 WebSocket

编辑 NapCatQQ 的配置文件（位置：`NapCatQQ/config/onebot11.json`）：

```json
{
  "http": {
    "enable": false
  },
  "ws": {
    "enable": false
  },
  "reverse": {
    "enable": true,
    "ws": {
      "enable": true,
      "urls": [
        "ws://127.0.0.1:3001"
      ]
    }
  }
}
```

**关键点：**
- `reverse.ws.urls` 填 `ws://127.0.0.1:3001`（大肥鱼会监听这个地址）
- 如果大肥鱼在**另一台机器**上，改成 `ws://<大肥鱼IP>:3001`

### 3. 启动 NapCatQQ

```bash
# Windows
napcat.exe

# macOS / Linux
./napcat

# Termux
cd ~/NapCatQQ && npm start
```

看到日志输出 `[NapCat] 连接到 ws://127.0.0.1:3001` 说明成功。

---

## 🚀 方案二：Lagrange（轻量级）

### 1. 安装 Lagrange

#### Windows / Linux

1. 下载 Lagrange：https://github.com/LagrangeDev/Lagrange.Core/releases
2. 解压到任意目录，例如 `~/lagrange/`

#### 配置文件

编辑 `appsettings.json`：

```json
{
  "Logging": {
    "LogLevel": {
      "Default": "Information"
    }
  },
  "SignServerUrl": "",
  "Account": {
    "Uin": 0,
    "Password": "",
    "Protocol": "Linux"
  },
  "Message": {
    "IgnoreSelf": true
  },
  "Implementations": [
    {
      "Type": "ReverseWebSocket",
      "Host": "127.0.0.1",
      "Port": 3001,
      "Suffix": "/",
      "ReconnectInterval": 5000,
      "HeartBeatInterval": 5000,
      "AccessToken": ""
    }
  ]
}
```

**关键点：**
- `Type` 改为 `ReverseWebSocket`
- `Host` 填大肥鱼的 IP（本机就是 `127.0.0.1`）
- `Port` 填 `3001`

> 如果用 `forward` 模式，把 `Type` 改成 `ForwardWebSocket`，并让 Lagrange 监听 3001。

### 2. 启动 Lagrange

```bash
# Windows
Lagrange.OneBot.exe

# Linux
./Lagrange.OneBot
```

首次启动会提示扫码登录，用手机 QQ 扫码即可。

---

## 🐟 大肥鱼端配置

编辑项目根目录的 `.env` 文件：

```bash
# ========== QQ 接入配置 ==========
QQ_ENABLED=true

# reverse = 大肥鱼监听 3001，NapCat 反向连过来（默认，推荐）
# forward = 大肥鱼主动连接 NapCat 的 WS 服务
QQ_WS_MODE=reverse

# reverse 模式下这是「监听地址」，填 0.0.0.0 才能被局域网设备连上
# forward 模式下这是「要连接的地址」，填 NapCat 的 ws://地址
QQ_WEBSOCKET_URL=ws://0.0.0.0:3001
QQ_BOT_QQ=123456789                    # 你的机器人 QQ 号
QQ_ADMIN_LIST=987654321,111222333      # 管理员 QQ 号（逗号分隔，可多个）

# 群聊触发关键词（可选，默认 @机器人 触发）
QQ_GROUP_KEYWORDS=大肥鱼,小鱼,AI

# 群聊白名单/黑名单（留空则不限制，逗号分隔群号）
QQ_GROUP_WHITELIST=
QQ_GROUP_BLACKLIST=

# 私聊自动回复（默认开启）
QQ_PRIVATE_AUTO_REPLY=true
```

**参数说明：**
- `QQ_WS_MODE`：`reverse`（大肥鱼当服务端，默认）或 `forward`（大肥鱼当客户端）
- `QQ_WEBSOCKET_URL`：reverse 下是监听地址，保持 `ws://0.0.0.0:3001` 即可
- `QQ_BOT_QQ`：机器人的 QQ 号（NapCat/Lagrange 登录的那个号）
- `QQ_ADMIN_LIST`：管理员 QQ 号列表，只有管理员可以使用某些敏感指令（如清空记忆）
- `QQ_GROUP_KEYWORDS`：群聊里不 @ 机器人也能触发的关键词（已在 `qq_adapter.py` 实现）
- `QQ_GROUP_WHITELIST` / `QQ_GROUP_BLACKLIST`：群号白/黑名单
- `QQ_PRIVATE_AUTO_REPLY`：私聊是否自动回复

---

## 🎯 启动顺序

1. **先启动 NapCat/Lagrange**，确保 QQ 登录成功
2. **再启动大肥鱼后端**：
   ```bash
   cd ~/bigfatfish
   python -m bigfatfish.main
   ```
3. 看到日志 `✓ QQ 适配器已连接` 说明成功

---

## 💬 使用示例

### 私聊对话
```
用户: 今天天气怎么样？
大肥鱼: 我帮你查一下~ [查询天气]
        今天多云，最高温度 22°C 哦~ 🌤️
```

### 群聊 @触发
```
用户: @大肥鱼 讲个笑话
大肥鱼: 好哒~ 有一天……[讲笑话]
```

### 群聊关键词触发（需配置 `QQ_GROUP_KEYWORDS`）
```
用户: 大肥鱼在吗？
大肥鱼: 在的在的~ 有什么想聊的吗？ 🐟
```

### 语音消息（需启用 ASR）
```
用户: [发送语音："明天提醒我交作业"]
大肥鱼: 好哒，已经记下啦~ 明天会提醒你交作业的 📝
```

---

## 🔧 常见问题

### Q1: NapCat 连接失败，显示 `ECONNREFUSED`
**A:** 这是**方向配反了**，按顺序检查：

1. 确认 `.env` 里 `QQ_WS_MODE=reverse`（默认），此时**大肥鱼是服务端、NapCat 是客户端**
2. 确认大肥鱼**先启动**，并看到日志 `🚀 QQ 反向 WS 已监听 ws://0.0.0.0:3001`
3. 确认 NapCat 的 `onebot11.json` 里配的是 `reverse.ws.urls`，不是 `ws` 段
4. 如果大肥鱼在云端，NapCat 里填 `ws://<云端IP>:3001`，并放行 3001 端口
5. 想让 NapCat 当服务端？把 `QQ_WS_MODE=forward`，并在 NapCat 里开启 `ws` 服务端监听 3001
6. 用 `netstat -tlnp | grep 3001` 确认 3001 端口确实在监听

### Q2: 群聊里 @机器人 没反应
**A:** 
1. 确认 `.env` 里的 `QQ_BOT_QQ` 填的是机器人自己的 QQ 号
2. 检查 NapCat/Lagrange 日志，看是否收到消息
3. 查看大肥鱼日志 `bigfatfish/logs/bigfatfish.log`，搜索 `[QQ]` 相关日志

### Q3: 私聊机器人没反应
**A:** 
1. 确认 `.env` 里 `QQ_PRIVATE_AUTO_REPLY=true`
2. 检查 QQ 号是否在 `QQ_ADMIN_LIST` 里（如果设置了白名单模式）
3. 私聊频率过高可能被限流，等待 3 秒后重试

### Q4: 语音消息识别不出来
**A:** 
1. 确认 `.env` 里 `ASR_ENABLED=true`
2. 检查 sherpa-onnx 模型是否下载完整（`models/sherpa-onnx/`）
3. 查看日志是否有 ASR 错误

### Q5: 发送的图片/表情包显示不出来
**A:** 
1. NapCat 对图片支持较好，Lagrange 可能不支持某些格式
2. 检查图片 URL 是否可访问（可以在浏览器里打开试试）
3. 大肥鱼发送的表情包路径：`bigfatfish/visual/assets/emoticon_packs/`

### Q6: 想在云端运行 NapCat，但没有图形界面
**A:** 
用 Lagrange 更合适（纯命令行），或者用 NapCat 的 Docker 版本：
```bash
docker run -d \
  --name napcat \
  -p 3001:3001 \
  -v ~/napcat-config:/app/config \
  napneko/napcat:latest
```

---

## 🎨 进阶配置

### 1. 表情包自动发送

大肥鱼会根据情绪标签自动发送表情包，表情包存放路径：
```
bigfatfish/visual/assets/emoticon_packs/
├── happy/      # 开心
├── sad/        # 难过
├── angry/      # 生气
├── cute/       # 可爱
└── neutral/    # 平静
```

把你喜欢的表情包图片（.jpg/.png/.gif）放进对应目录，大肥鱼会随机选一张发送。

### 2. 群聊白名单/黑名单

编辑 `.env`：
```bash
# 只在这些群里响应（留空则所有群都响应）
QQ_GROUP_WHITELIST=123456789,987654321

# 不在这些群里响应
QQ_GROUP_BLACKLIST=111222333
```

### 3. 自定义触发前缀

编辑 `bigfatfish/gateway/qq_adapter.py`，找到：
```python
if message.startswith("/"):
    # 处理命令
```

可以改成你喜欢的前缀，比如 `!` 或 `#`。

### 4. 定时群发消息

编辑 `.env`：
```bash
ACTIVE_INTERACTION_ENABLED=true
ACTIVE_INTERVAL_HOURS=24
```

大肥鱼会每 24 小时在群里主动发一条消息（比如"早安~ 今天也要开心呀 🌸"）。

---

## 📚 相关文档

- NapCatQQ 官方文档：https://napneko.github.io
- Lagrange 官方文档：https://lagrangedev.github.io/Lagrange.Doc
- OneBot v11 协议：https://11.onebot.dev

---

**配置完成后，试着给机器人发条消息吧~ 🐟**
