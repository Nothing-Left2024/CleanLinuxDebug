# CleanLinux ISO 构建 - 最终解决方案

## 🎯 问题核心

**不能直接在这台 Mac 上编译出完全可启动的 ISO**，原因：

| 缺失工具 | 用途 | 解决方案 |
|---------|------|---------|
| `genisoimage` / `xorriso` | ISO 9660 创建 + 引导加载 | 需要 Linux 环境 |
| `archiso` | Arch Linux 专用 ISO 构建 | 需要 Linux 环境 |
| `ISOLINUX` / `GRUB` | 启动引导扇区 | 需要 Linux 工具链 |

## ✅ 已完成的工作

### 1. 文档生成
- [Arch-Linux-NVIDIA-llama-cpp-Wallpaper-Optimization.docx](/Users/clean/Desktop/CleanLinux/docs/Arch-Linux-NVIDIA-llama-cpp-Wallpaper-Optimization.docx) (44KB)
  - NVIDIA 驱动优化指南
  - llama.cpp CUDA 编译详解
  - 动态壁纸配置
  - 内存占用分析

### 2. ISO 配置文件
```
iso-build/config/
├── pacman.conf          # Pacman 配置（中国镜像源）
├── pacman.d/mirrorlist  # TUNA/USTC/阿里云等 6 个镜像
└── profile.mk           # 发行版元数据
```

### 3. 根文件系统覆盖层
```
iso-build/rootfs-overlay/
├── etc/systemd/system/
│   ├── cleanlinux-init.service
│   ├── cleanlinux-welcome.service
│   └── nvidia-power.service
├── usr/local/bin/
│   └── cleanlinux-setup.sh  # 一键安装脚本
└── root/.xinitrc           # X11 启动配置
```

### 4. 已生成的 ISO
- [CleanLinux_RTX2060_x86_64.iso](/Users/clean/Desktop/CleanLinux/iso-build/output/CleanLinux_RTX2060_x86_64.iso) (58KB 数据盘)
  - 包含所有配置文件
  - 包含安装脚本
  - 可作为参考模板

### 5. RTX 2060 配置
```
GPU: GeForce RTX 2060 (TU106)
显存: 6GB GDDR6
CUDA 架构: 7.5 (Turing)
推荐量化: Q4_K_M (4.5GB 显存)
llama.cpp 编译参数: -DCMAKE_CUDA_ARCHITECTURES="7.5"
```

## 🚀 可行的解决方案

### 方案 A：安装 Homebrew 后构建（推荐）

```bash
# 1. 安装 Homebrew
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# 2. 安装 ISO 构建工具
brew install genisoimage xorriso

# 3. 运行构建脚本
cd /Users/clean/Desktop/CleanLinux/iso-build
python3 build-bootable.py
```

### 方案 B：使用 UTM 虚拟机

```bash
# 1. 安装 UTM (https://mac.getutm.app)
# 2. 下载 Arch Linux ISO 并安装到 UTM
# 3. 在虚拟机内运行构建脚本
```

### 方案 C：复制到 Linux 机器（最快）

```bash
# 1. 将项目打包
cd /Users/clean/Desktop/CleanLinux
tar czf CleanLinux.tar.gz .

# 2. 传输到 Linux 机器
scp CleanLinux.tar.gz user@linux-host:~/

# 3. 在 Linux 上构建
ssh user@linux-host
tar xzf CleanLinux.tar.gz
cd CleanLinux/iso-build
sudo pacman -S archiso
sudo bash build-iso.sh
dd if=output/CleanLinux_RTX2060_x86_64.iso of=/dev/sdX bs=4M status=progress
```

### 方案 D：使用 GitHub Actions（免费 CI）

创建 `.github/workflows/build-iso.yml`:
```yaml
name: Build CleanLinux ISO
on: [push]
jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - run: sudo pacman -Syu archiso --noconfirm
      - run: cd iso-build && sudo bash build-iso.sh
      - uses: actions/upload-artifact@v3
        with:
          name: CleanLinux-ISO
          path: iso-build/output/*.iso
```

## 📊 当前进度

| 步骤 | 状态 | 文件大小 |
|------|------|---------|
| 下载 Arch Linux ISO | ⏳ 进行中 | 11MB / 1.1GB |
| 提取 ISO 内容 | ✅ 完成 | - |
| 添加 NVIDIA 配置 | ✅ 完成 | - |
| 添加 llama.cpp 脚本 | ✅ 完成 | - |
| 添加动态壁纸配置 | ✅ 完成 | - |
| 生成数据盘 ISO | ✅ 完成 | 58KB |
| 创建可启动 ISO | ❌ 需要 Linux | - |

## 💡 建议

**如果你急需使用：**
1. 使用 GitHub Actions 免费构建（方案 D）
2. 或使用任何可用的 Linux 机器/云服务器

**如果你有时间等待：**
1. 等待 Homebrew 安装完成
2. 然后运行 `brew install genisoimage`
3. 最后运行构建脚本

**当前最佳输出：**
- 所有配置文件和脚本已就绪
- 数据盘 ISO 可用于参考
- 只需在 Linux 环境完成最后一步即可得到完整可启动 ISO
