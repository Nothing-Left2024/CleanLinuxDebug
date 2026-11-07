# CleanLinux 路线规划

> 定位：为「写代码 + llama.cpp 推理」而生的轻量 Arch 发行版
> 核心哲学：每一 MB 内存都要花在刀刃上

---

## 设计原则

### 1. 工具自举原则
系统自带工具**禁止依赖 Python**——因为功能编辑器的用途之一就是关闭 Python 释放内存，
工具不能用自己可能关掉的东西来构建。

| 组件 | 技术选型 | 原因 |
|------|----------|------|
| 功能编辑器 | Shell + yad (GTK) | yad 体积 ~1MB，纯 C，不依赖 Python |
| 任务管理器 | lxtask + Shell + yad | lxtask ~1MB，轻量 GTK 进程管理器 |
| GPU 监控 | nvidia-smi + nvtop | nvidia-smi 随 nvidia-utils 已内置 |
| 配置存储 | /etc/cleanlinux/*.conf | 纯文本，shell 直接 source |

### 2. 内存预算哲学

```
┌─────────────────────────────────────────────┐
│ 纯 CLI 模式          ~100 MB                │
│ GUI 基础 (X+openbox+tint2)   ~180 MB        │
│ + 动态壁纸 (mpv)      +40 MB                │
│ + 毛玻璃 (picom)      +30 MB (部分占显存)   │
│ 仪表盘/编辑器运行时    各 ~15 MB (按需)      │
├─────────────────────────────────────────────┤
│ 8GB 机器可用给 llama:  ~7 GB → 4.5GB 模型  │
└─────────────────────────────────────────────┘
```

### 3. 显存一等公民
任务管理器中 VRAM 与 RAM 同级展示。RTX 2060 只有 6GB 显存，
显存占用 = 能加载多大模型，比 CPU 内存更关键。

---

## 阶段一：GUI 功能编辑器（cleanlinux-features）

**目标**：图形化开关系统功能，实时显示内存收益。

### 新增依赖（packages.x86_64）
```
yad          # GTK 对话框工具，~1MB
```

### 界面设计（yad notebook 四标签页）

```
┌─ CleanLinux 功能编辑器 ──────────────────────────┐
│ [系统服务] [桌面组件] [AI 性能] [内存总览]         │
│ ┌─────────────────────────────────────────────┐ │
│ │ ☑ NetworkManager      ~20 MB   [开关]       │ │
│ │ ☐ sshd                ~10 MB   [开关]       │ │
│ │ ☐ systemd-resolved    ~8 MB    [开关]       │ │
│ │ ☑ getty@tty2-6 (多余终端)  [开关]             │ │
│ │ ☐ cups (打印)          ~15 MB   [开关]       │ │
│ │ ☐ Python 解释器       释放~30 MB [卸载⚠️]    │ │
│ └─────────────────────────────────────────────┘ │
│           当前内存: 1.2 GB / 16 GB                │
└──────────────────────────────────────────────────┘
```

### 四个标签页

| 标签页 | 功能 | 实现 |
|--------|------|------|
| 系统服务 | NetworkManager/sshd/cups/resolved/多余getty 开关 | `systemctl disable --now` |
| 桌面组件 | 动态壁纸、毛玻璃强度(0-20)、任务栏、X 会话本身 | 杀进程 + 改 /etc/cleanlinux/desktop.conf |
| AI 性能 | llama 自动加载、NVIDIA 持久模式、zram 开关 | nvidia-smi -pm 1, modprobe zram |
| 内存总览 | 实时显示各组件占用 + 一键「极致模式」 | 读取 /proc + 汇总 |

### 关键功能：极致模式（Performance Mode）
一键关闭 GUI 全家桶（壁纸+毛玻璃+任务栏，保留 X + 终端），
预计释放 ~70 MB 内存 + ~50 MB 显存给 llama.cpp。

### 配置文件设计
```bash
# /etc/cleanlinux/features.conf  (由编辑器读写，.xinitrc 读取)
WALLPAPER=on          # 动态壁纸
BLUR_STRENGTH=12      # 毛玻璃强度 0=关闭
TASKBAR=on
LLAMA_SERVICE=off
ZRAM=on
```

**验证标准**：关闭壁纸+毛玻璃后 `free -m` 显示节省 ≥60 MB。

---

## 阶段二：任务管理器（cleanlinux-monitor）

**目标**：美观轻量，显存占用与 RAM 同级展示。

### 新增依赖
```
lxtask        # 轻量 GUI 进程管理器，~1MB，支持杀进程
```

### 双层设计

**第一层：仪表盘（cleanlinux-monitor，yad 实现）**

```
┌─ CleanLinux 监控 ────────────────────────────────┐
│  CPU ▓▓▓▓▓░░░░░  42%     RAM ▓▓▓░░░░░ 3.2/16 GB  │
│                                                  │
│  ┌─ GPU: RTX 2060 ──────────────────────────┐   │
│  │ 显存  ▓▓▓▓▓▓▓░░░  4.1 / 6.0 GB  (68%)    │   │
│  │ 利用率 ▓▓▓▓░░░░░  38%   温度 62°C  85W   │   │
│  └───────────────────────────────────────────┘   │
│                                                  │
│  TOP 进程:                                       │
│   llama.cpp     4.1 GB VRAM  12% CPU            │
│   mpv            40 MB RAM                        │
│                                                  │
│  [进程管理] [GPU详情] [刷新]   5秒自动刷新       │
└──────────────────────────────────────────────────┘
```

- 数据源：`nvidia-smi --query-gpu=memory.used,memory.total,utilization.gpu,temperature.gpu,power.draw --format=csv,noheader`
- 每 5 秒轮询刷新（yad --watch 模式）

**第二层：深度工具（按钮调起）**
| 按钮 | 工具 | 用途 |
|------|------|------|
| 进程管理 | lxtask | 杀进程、看树状关系 |
| GPU 详情 | nvtop | 每进程显存、GPU 曲线图 |

### 进程级显存占用（差异化能力）
nvtop 能显示「哪个进程占了多少显存」——这对 llama 调参至关重要
（比如发现 Xorg 偷占了 300MB 显存，就可以针对性优化）。

---

## 阶段三：集成与液态玻璃主题

### 3.1 GTK 主题统一（液态玻璃风格）
```
新增: matcha-gtk-theme 或自定义 CSS
yad/lxtask 窗口半透明背景 + 圆角，
与 picom dual_kawase 毛玻璃叠加 = 完整液态玻璃体验
```

### 3.2 入口集成
| 入口 | 方式 |
|------|------|
| tint2 任务栏 | 固定启动器图标 (编辑器+监控) |
| dmenu | 快捷键 Win+F = features, Win+M = monitor |
| openbox 右键菜单 | 加入菜单项 |
| 文本菜单 cleanlinux-menu | 新增选项 6=功能编辑器(CLI版), 7=监控(CLI版) |
| CLI 模式 | whiptail 实现无 GUI 版本，功能一致 |

### 3.3 CLI 版本（重要）
功能编辑器和监控必须有 **whiptail TUI 版本**——
CLI 模式（~100MB）是本系统卖点，编辑器不能反过来要求先开 GUI。

---

## 阶段四：llama.cpp 服务化（远期）

```bash
# cleanlinux-llama.service
systemctl start llama          # 启动 llama-server (OpenAI 兼容 API)
cleanlinux-llama load qwen2.5-coder-3b   # 一键换模型
cleanlinux-llama status        # 查看模型 + 显存占用
```

- llama-server 提供 OpenAI 兼容 API → VSCode/vim 的 AI 插件可直接连
- 配合功能编辑器：开启 llama 服务前自动建议开启极致模式

---

## 实施顺序与工作量

| 优先级 | 任务 | 依赖 | 预估 |
|--------|------|------|------|
| P0 | yad/lxtask 加入包列表 | 无 | 10 分钟 |
| P0 | cleanlinux-features (GUI+TUI) | yad | 2-3 小时 |
| P0 | cleanlinux-monitor 仪表盘 | yad+nvidia-smi | 1-2 小时 |
| P1 | features.conf 接入 .xinitrc | 阶段一 | 30 分钟 |
| P1 | 极致模式 + 快捷键绑定 | 阶段一 | 30 分钟 |
| P2 | GTK 液态玻璃主题 | 阶段一二 | 1-2 小时 |
| P2 | ISO 重新构建验证 | 全部 | GitHub Actions |
| P3 | llama 服务化 | 远期 | 待定 |

---

## 风险与对策

| 风险 | 对策 |
|------|------|
| 卸载 Python 破坏 archinstall | 卸载前弹窗警告，提供恢复命令 |
| yad 轮询导致 CPU 占用 | 5 秒间隔 + 空闲时降频到 30 秒 |
| 远程机器仍未恢复 | 全部开发在本地 + GitHub Actions 验证 |
| 显存读数需要 nvidia 驱动已加载 | 检测 nvidia-smi 可用性，无驱动时优雅降级 |
