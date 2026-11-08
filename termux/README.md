# Termux 一键安装包

这个目录包含 Termux 环境的一键安装脚本和桌面快捷方式。

## 📦 文件说明

| 文件 | 用途 |
|------|------|
| `bootstrap.sh` | 一键安装脚本（安装依赖 + 克隆项目 + 配置环境） |
| `widget/启动大肥鱼.sh` | Termux:Widget 桌面快捷方式（一键启动） |
| `widget/停止大肥鱼.sh` | Termux:Widget 桌面快捷方式（一键停止） |
| `boot/bigfatfish-boot.sh` | Termux:Boot 开机自启脚本 |

## 🚀 使用方法

### 方案一：curl 一键安装（推荐）

在 Termux 里执行：

```bash
curl -fsSL https://你的仓库地址/raw/main/termux/bootstrap.sh | bash
```

### 方案二：手动下载安装

```bash
# 1. 克隆项目
cd ~
git clone https://github.com/你的用户名/bigfatfish.git
cd bigfatfish

# 2. 运行安装脚本
bash termux/bootstrap.sh
```

## 📱 桌面快捷方式（Termux:Widget）

1. 安装 Termux:Widget：https://f-droid.org/packages/com.termux.widget/
2. 运行 `bootstrap.sh` 后，快捷方式会自动创建到 `~/.shortcuts/`
3. 在手机桌面：长按 → 小部件 → Termux:Widget → 选择「启动大肥鱼」或「停止大肥鱼」

## 🔄 开机自启（Termux:Boot）

1. 安装 Termux:Boot：https://f-droid.org/packages/com.termux.boot/
2. 打开 Termux:Boot APP 一次（授予自启权限）
3. 运行 `bootstrap.sh` 后，自启脚本会自动配置到 `~/.termux/boot/`
4. 重启手机后，大肥鱼会在 10 秒后自动启动

## ⚠️ 注意事项

- Termux:Widget 和 Termux:Boot 需要单独安装，不是 Termux 自带的
- 开机自启会在后台运行，日志输出到 `~/bigfatfish-boot.log`
- 如果需要停止后台进程：`pkill -f bigfatfish.main`
- 桌面快捷方式的脚本必须放在 `~/.shortcuts/` 目录下才能被 Termux:Widget 识别

## 🔧 手动配置

如果 `bootstrap.sh` 未自动创建快捷方式，可以手动复制：

```bash
mkdir -p ~/.shortcuts
cp termux/widget/*.sh ~/.shortcuts/
chmod +x ~/.shortcuts/*.sh

mkdir -p ~/.termux/boot
cp termux/boot/bigfatfish-boot.sh ~/.termux/boot/
chmod +x ~/.termux/boot/bigfatfish-boot.sh
```

---

**安装完成后，记得编辑 `.env` 文件配置 DeepSeek API Key！**
