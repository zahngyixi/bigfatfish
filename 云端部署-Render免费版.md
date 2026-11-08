# Render 免费部署教程（保姆级）

> **不花钱，每月 750 小时免费额度，够一个月 24 小时挂着。**
> 
> 需要：GitHub 账号（没有的话 5 分钟注册一个）

---

## 第 1 步：把项目传到 GitHub（5 分钟）

### 1.1 创建 GitHub 仓库
1. 打开 https://github.com/new
2. Repository name 填：`bigfatfish`
3. 选 **Private**（私有，不让别人看到你的配置）
4. 点 **Create repository**

### 1.2 上传代码
把 `大肥鱼-交付包.zip` 解压到一个文件夹，然后：

**方式 A：用 GitHub 网页上传（最简单）**
1. 在刚创建的仓库页面，点 **uploading an existing file**
2. 把解压后的**所有文件和文件夹**拖进去
3. 拉到最下面，点 **Commit changes**

**方式 B：用命令行（如果你会 Git）**
```bash
cd 你的文件夹
git init
git add .
git commit -m "初始提交"
git branch -M main
git remote add origin https://github.com/你的用户名/bigfatfish.git
git push -u origin main
```

---

## 第 2 步：部署到 Render（3 分钟）

### 2.1 注册 Render
1. 打开 https://render.com
2. 点右上角 **Sign Up**
3. 选 **Sign up with GitHub**（用 GitHub 账号登录，不用再注册）

### 2.2 创建 Web Service
1. 登录后点 **New +** → **Web Service**
2. 点 **Connect a repository** → 选你刚才的 `bigfatfish`（如果看不到，点 **Configure account** 授权）
3. 填写配置：
   - **Name**: `bigfatfish`（随便起，这会是你的网址前缀）
   - **Region**: Singapore 或 Oregon（新加坡快一点）
   - **Branch**: `main`
   - **Runtime**: **Docker**
   - **Instance Type**: **Free**
   
4. 点 **Create Web Service**

### 2.3 添加环境变量
部署会开始但会失败（因为还没填 key）。在页面左侧点 **Environment**：

| Key | Value |
|-----|-------|
| `DEEPSEEK_API_KEY` | `sk-你的真实key` |
| `QQ_BOT_QQ` | `2500694598` |
| `PORT` | `8080` |

点 **Save Changes**，Render 会自动重新部署。

### 2.4 等部署完成
看到 **Deploy succeeded** + 绿色的 **Live** 标志就成功了。

你的后端地址是：`https://bigfatfish-xxxx.onrender.com`（xxxx 是随机字符）

---

## 第 3 步：改 APK 连接地址（2 分钟）

### 3.1 修改代码
打开 `android-webview/app/src/main/java/com/bigfatfish/app/MainActivity.java`，第 24 行改成：

```java
private static final String BACKEND_URL = "https://bigfatfish-xxxx.onrender.com";
```

（把 `xxxx` 换成你刚才 Render 给的真实网址）

### 3.2 push 触发 APK 构建
把修改后的 `MainActivity.java` 提交到 GitHub：

```bash
git add android-webview/app/src/main/java/com/bigfatfish/app/MainActivity.java
git commit -m "改成 Render 地址"
git push
```

或者在 GitHub 网页上直接编辑那个文件，点 **Commit changes**。

### 3.3 下载 APK
1. GitHub 仓库页面点 **Actions**
2. 等最新的 workflow 跑完（约 3 分钟）
3. 点进去 → **Artifacts** → 下载 `bigfatfish-release`
4. 解压得到 `app-release.apk`，传到手机装上

---

## 第 4 步：挂 QQ（3 分钟）

你的后端现在在 Render 上跑着，地址是 `https://bigfatfish-xxxx.onrender.com`。

**NapCat 可以在任意设备上装**（你的电脑、朋友的电脑、另一台手机的 Termux）：

1. 装 NapCatQQ（Windows / Linux / Termux 都行）
2. 配置 `onebot11.json` 的反向 WebSocket：
   ```json
   {
     "reverse": {
       "enable": true,
       "ws": {
         "enable": true,
         "urls": ["wss://bigfatfish-xxxx.onrender.com:3001"]
       }
     }
   }
   ```
   注意是 `wss://`（有 s，因为 Render 强制 HTTPS）

3. 用 QQ `2500694598` 扫码登录
4. **先确认 Render 上的大肥鱼在运行，再启动 NapCat**

---

## 常见问题

### Q1: 部署失败，日志显示 `ModuleNotFoundError`
**A:** `requirements-lite.txt` 没传上去，检查 GitHub 仓库里文件是否齐全。

### Q2: APK 装上后白屏
**A:** 
1. 检查 `MainActivity.java` 里的网址是否正确
2. 打开手机浏览器访问那个网址，看是否能打开（如果浏览器也打不开，说明 Render 部署有问题）

### Q3: Render 显示服务已停止
**A:** 免费版闲置 15 分钟会自动休眠，有请求时会自动唤醒（首次访问可能慢 10-20 秒）。

### Q4: 每月 750 小时不够用
**A:** 
- 一个月 = 720 小时，刚好够
- 如果超了，注册多个 Render 账号（用不同邮箱），或者换 Railway（也有免费额度）

### Q5: NapCat 连不上 Render
**A:** 
1. Render 的 3001 端口需要单独暴露。在 `render.yaml` 里加：
   ```yaml
   ports:
     - port: 3001
       protocol: tcp
   ```
   然后重新部署。
2. 或者改用 HTTP 长轮询模式（不推荐，实时性差）

---

## 完成！

- **手机 APP**：`app-release.apk` 装上就能用
- **QQ 机器人**：给 `2500694598` 发私聊，它会自动回
- **管理后台**：浏览器打开 `https://bigfatfish-xxxx.onrender.com` 看界面

所有东西都在云上跑，手机不用一直开着，也不花钱（除非超 750 小时）。

---

*需要我帮你写 Railway 版本的配置吗？或者遇到哪一步卡住了告诉我。*
