# CleanLinux ISO 构建说明

## 快速开始

### 在 macOS 上（当前环境）
```bash
cd iso-build
python3 build-macos.py
```
生成数据盘 ISO：`output/CleanLinux-x86_64.iso`

### 在 Linux 上（完整可启动 ISO）
```bash
# 1. 安装 archiso
sudo pacman -S archiso

# 2. 构建完整 ISO
sudo bash build-iso.sh

# 3. 写入 U 盘
dd if=output/CleanLinux-x86_64.iso of=/dev/sdX bs=4M status=progress
```

## 目录说明

```
iso-build/
├── config/                  # ArchISO 配置文件
│   ├── pacman.conf          # Pacman 配置（中国镜像）
│   ├── pacman.d/
│   │   └── mirrorlist       # 中国镜像源列表
│   └── profile.mk           # 发行版配置
├── rootfs-overlay/          # 根文件系统覆盖层
│   ├── etc/systemd/system/  # 自定义 systemd 服务
│   ├── usr/local/bin/       # 自定义脚本
│   ├── root/.xinitrc        # X11 启动脚本
│   └── root/.config/picom/  # picom 配置
├── build-macos.py           # macOS ISO 构建脚本
├── build-iso.sh             # Linux ISO 构建脚本
└── output/                  # 输出目录
    └── CleanLinux-x86_64.iso
```

## 发行版特性

- **基础**: Arch Linux rolling
- **窗口管理器**: dwm（极简高效）
- **Compositor**: picom（液态玻璃磨砂效果）
- **动态壁纸**: mpv root window（~40MB 内存）
- **NVIDIA**: 专有驱动预装，CUDA 就绪
- **llama.cpp**: CUDA 加速编译，GPU 推理
- **启动模式**: CLI 默认（~100MB 内存）

## 资源占用

| 阶段 | 内存占用 |
|------|----------|
| CLI | ~100 MB |
| GUI + picom | ~250 MB |
| 动态壁纸 | +40 MB |
| llama.cpp 推理 | ~4.5 GB 显存 |
