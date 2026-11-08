# 给 zahngyixi 的傻瓜式部署指南

你的后端已经在本机跑起来了，现在只需要 3 步把它弄到云上。

---

## 第 1 步：创建 GitHub 仓库（30 秒）

1. 打开 Edge，访问：https://github.com/new
2. Repository name 填：`bigfatfish`
3. 选 **Private**（私有）
4. 点 **Create repository**（绿色按钮）

---

## 第 2 步：上传代码（1 分钟）

双击 `一键上传GitHub.bat`，等它跑完。

**如果弹窗要求登录：**
- 点「Sign in with your browser」
- 浏览器会打开 GitHub 授权页面
- 点「Authorize」（授权）
- 回到命令行窗口，按回车继续

看到 `[成功]` 就说明上传好了。

---

## 第 3 步：部署到 Render（2 分钟）

### 3.1 登录 Render
1. 打开：https://render.com
2. 点右上角 **Sign Up**
3. 选 **Sign up with GitHub**（用 GitHub 登录，不用再注册）

### 3.2 创建 Web Service
1. 点 **New +** → **Web Service**
2. 点右边的 **Connect a repository**
3. 找到 `zahngyixi/bigfatfish`，点 **Connect**
   - 如果看不到，点 **Configure account** 授权
4. 配置页面：
   - Name: `bigfatfish`（随便起）
   - Region: **Singapore**（新加坡快）
   - Branch: `main`
   - Runtime: **Docker**（会自动识别）
   - Instance Type: **Free**
5. 点 **Create Web Service**（绿色按钮）

### 3.3 添加环境变量
部署会开始但会失败（因为还没填 key）。

在页面左侧点 **Environment**，添加：

| Key | Value |
|-----|-------|
| `DEEPSEEK_API_KEY` | `sk-f961f2ab7a294ad5b4a7fc1322923b33` |
| `PORT` | `8080` |

点 **Save Changes**，Render 会自动重新部署。

### 3.4 等部署完成（约 3 分钟）
看到 **Deploy succeeded** + 绿色的 **Live** 就成功了。

你的公网地址是：`https://bigfatfish-xxxx.onrender.com`（xxxx 是随机字符，在页面顶部显示）

---

## 第 4 步：测试（10 秒）

浏览器打开你的 Render 地址（`https://bigfatfish-xxxx.onrender.com`），应该能看到界面。

**测试 QQ 机器人：**
- 用任意 QQ 给 `2500694598` 发私聊
- 它会用鲸鱼娘人格回复你（嘴硬傲娇那套）

---

## 做成 APK（可选）

有了 Render 地址后，我可以帮你：
1. 把地址写进 APK 代码
2. push 到 GitHub
3. GitHub Actions 自动编译
4. 你下载 APK 装到手机

要的话告诉我你的 Render 地址（`https://bigfatfish-xxxx.onrender.com`），我 5 分钟搞定。

---

## 卡住了怎么办

**Git 推送失败：**
- 检查仓库名是否是 `bigfatfish`
- 检查是否 Private（不是 Public）
- 重新运行 `一键上传GitHub.bat`

**Render 部署失败：**
- 检查 Environment 里的 key 是否填对
- 看部署日志（Logs 标签页）截图给我

**QQ 机器人不回消息：**
- 检查 Render 服务是否 Live（绿色）
- 给机器人发"认真点"试试（可能在摸鱼）

---

开始吧，第 1 步：https://github.com/new 创建仓库 `bigfatfish`（Private）
