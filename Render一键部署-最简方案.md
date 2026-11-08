# Render 一键部署（最简方案）

## 点这个链接就行：

```
https://render.com/deploy?repo=https://github.com/zahngyixi/bigfatfish
```

> ⚠️ 如果链接打不开（因为仓库还没创建），用下面的手动方案

---

## 手动 3 步（如果上面链接不行）

### 1. 登录 Render
打开：https://render.com/
点右上角 **Get Started** → 用 **Google** 或 **GitHub** 登录（30 秒）

### 2. 创建 Web Service
- 点 **New +** → **Web Service**
- 点右边 **Public Git repository**
- 粘贴：`https://github.com/zahngyixi/bigfatfish`（如果你的 GitHub 上还没这个仓库，先告诉我）
- 或者点 **Upload Docker**，把 `大肥鱼-云端免费版.zip` 解压后拖进去

### 3. 配置
- Name: `bigfatfish`
- Region: **Singapore**
- Instance Type: **Free**
- 点 **Create Web Service**

然后在左侧 **Environment** 里添加：

```
DEEPSEEK_API_KEY = sk-f961f2ab7a294ad5b4a7fc1322923b33
QQ_BOT_QQ = 2500694598
PORT = 8080
```

点 **Save Changes**，等 3 分钟部署完成。

---

## 部署完成后

你会得到一个地址：`https://bigfatfish-xxxx.onrender.com`

**测试：**
- 浏览器打开那个地址 → 看到界面
- QQ 给 2500694598 发消息 → 鲸鱼娘会回你

**这时候你电脑就可以关机了，QQ 机器人 24 小时在线。**

---

## 挂 QQ 机器人

你需要在**任意一台设备**上装 NapCat：
- 你的电脑 / 朋友的电脑 / 另一台手机的 Termux
- 配置反向 WS：`wss://bigfatfish-xxxx.onrender.com:3001`（注意是 wss，有 s）
- 用 QQ 2500694598 扫码登录

详细见 `QQ_SETUP_GUIDE.md`。

---

## 常见问题

**Q: 我 GitHub 上没有 bigfatfish 仓库怎么办？**
A: 告诉我，我用你的 token 推一次代码。或者在 Render 选「Upload Docker」，拖 zip 文件。

**Q: 免费额度够用吗？**
A: 每月 750 小时，刚好够一个月 24 小时运行。

**Q: 为什么还要我点按钮？**
A: 云平台的安全规则，必须账号主人确认部署。这是最后一步了。
