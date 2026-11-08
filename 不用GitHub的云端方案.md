# Railway 直接部署方案（不需要 GitHub）

## 方法 1：Railway CLI（最快，5 分钟）

### 第 1 步：安装 Railway CLI

打开 PowerShell（Win+X → Windows PowerShell），复制粘贴这行：

```powershell
iwr https://railway.app/install.ps1 -useb | iex
```

按回车，等它装完。

### 第 2 步：登录 Railway

```powershell
railway login
```

会自动打开浏览器，用 GitHub 或 Google 登录（随便哪个都行，30 秒）。

### 第 3 步：一键部署

```powershell
cd E:\hammless\3
railway init
railway up
```

Railway 会自动：
- 检测到 Dockerfile
- 上传代码
- 部署到云端
- 给你一个公网地址

### 第 4 步：填环境变量

```powershell
railway variables set DEEPSEEK_API_KEY=sk-f961f2ab7a294ad5b4a7fc1322923b33
railway variables set QQ_BOT_QQ=2500694598
railway variables set PORT=8080
```

完成！你的地址在 Railway 控制台显示。

---

## 方法 2：Zeabur（网页操作，不用命令行）

1. 打开 https://zeabur.com
2. 用 GitHub 登录
3. 点 **New Project**
4. 选 **Upload from local**
5. 把 `大肥鱼-云端免费版.zip` 拖进去
6. 等部署完成
7. 点 **Variables** 填环境变量（key 和 QQ 号）

---

## 方法 3：Hugging Face Spaces（完全免费，永久）

我帮你生成配置文件，你只需要：
1. 去 huggingface.co 注册（用 Google 账号秒登）
2. 创建一个 Space
3. 上传文件
4. 搞定

---

**哪个方案？**

- **想要最快**：方法 1（Railway CLI，3 条命令）
- **不想装东西**：方法 2（Zeabur 网页拖文件）
- **完全免费**：方法 3（Hugging Face，但我要先改点配置）

告诉我选哪个，我立刻给你详细步骤或者帮你准备文件。
