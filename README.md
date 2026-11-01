# CleanLinux

Arch Linux 自定义发行版，专为 NVIDIA RTX 2060 和本地 AI 推理优化。

## 特性

- **极致轻量**: CLI 默认启动，内存占用 ~100MB
- **NVIDIA 优化**: 专有驱动预装，CUDA 7.5 (Turing) 支持
- **llama.cpp**: GPU 加速本地推理，支持 Q4/Q5/Q8 量化
- **动态壁纸**: mpv root window，内存仅 ~40MB
- **液态玻璃**: picom compositor，macOS 风格磨砂效果
- **中国镜像**: TUNA/USTC/阿里云等 6 个国内镜像源

## GPU 配置

| 项目 | 规格 |
|------|------|
| GPU | GeForce RTX 2060 (TU106) |
| 显存 | 6GB GDDR6 |
| CUDA 架构 | 7.5 (Turing) |
| 推荐量化 | Q4_K_M (4.5GB) |

## 快速开始

### 构建 ISO（需要 Linux 机器）
```bash
# 1. 安装 archiso
sudo pacman -S archiso

# 2. 构建 ISO
cd iso-build
sudo bash build-iso.sh

# 3. 写入 U 盘
dd if=output/CleanLinux_RTX2060_x86_64.iso of=/dev/sdX bs=4M status=progress
```

### 使用 GitHub Actions 构建
```bash
# 推送到 GitHub 后，Actions 自动构建
git push origin main
```

## 启动方式

```bash
# CLI 模式（默认）
# 开机直接进入命令行，内存 ~100MB

# GUI 模式
startx

# 动态壁纸
wallpaper /path/to/video.mp4

# GPU 监控
nvtop

# 本地推理
llama-cli -m model.gguf -ngl 33 -t 4
```

## 目录结构

```
CleanLinux/
├── docs/                    # 文档
│   └── Arch-Linux-NVIDIA-llama-cpp-Wallpaper-Optimization.docx
├── iso-build/               # ISO 构建配置
│   ├── config/              # ArchISO 配置
│   ├── rootfs-overlay/      # 根文件系统覆盖层
│   ├── build-iso.sh         # Linux 构建脚本
│   ├── build-macos.py       # macOS 构建脚本
│   └── output/              # 输出目录
└── README.md
```

## 资源占用

| 阶段 | 内存占用 |
|------|----------|
| CLI | ~100 MB |
| GUI + picom | ~250 MB |
| 动态壁纸 | +40 MB |
| llama.cpp 推理 | ~4.5 GB 显存 |

## 镜像源

- TUNA (清华大学)
- USTC (中国科学技术大学)
- Aliyun (阿里云)
- HIT (哈尔滨工业大学)
- JLU (吉林大学)
- SJTU (上海交通大学)

## 许可证

MIT License
