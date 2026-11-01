# Linux 构建环境要求

## 最小系统要求

### 推荐发行版
| 发行版 | 版本要求 | 说明 |
|--------|---------|------|
| **Arch Linux** | 任意最新 | 首选，原生支持 archiso |
| **Ubuntu** | 20.04 LTS 或更新 | 需要额外安装 archiso |
| **Fedora** | 38+ | 需要额外安装 archiso |
| **Debian** | 12 (Bookworm) | 需要额外安装 archiso |

### 最低配置
```
CPU:    x86_64 (64位)
内存:   2 GB RAM
磁盘:   10 GB 可用空间
网络:   需要下载约 1.5 GB 数据包
```

### 推荐配置
```
CPU:    4 核以上（编译 llama.cpp 需要）
内存:   8 GB RAM
磁盘:   20 GB 可用空间
GPU:    可选（用于测试 NVIDIA 驱动）
```

## 必须安装的软件包

### Arch Linux（最简单）
```bash
sudo pacman -S archiso base-devel
```

### Ubuntu/Debian
```bash
sudo apt update
sudo apt install archiso genisoimage xorriso mkisofs

# 或者从源码编译 archiso
git clone https://github.com/archlinux/archiso.git
cd archiso
makepkg -si
```

### Fedora/RHEL
```bash
sudo dnf install archiso genisoimage xorriso
```

## 构建步骤

### 1. 复制项目到 Linux 机器
```bash
# 从 Mac 传输
scp -r /path/to/CleanLinux user@linux-host:~/
```

### 2. 安装依赖
```bash
# Arch Linux
sudo pacman -S archiso base-devel git

# Ubuntu/Debian
sudo apt install archiso genisoimage xorriso git

# Fedora
sudo dnf install archiso genisoimage xorriso git
```

### 3. 构建 ISO
```bash
cd ~/CleanLinux/iso-build
sudo bash build-iso.sh
```

### 4. 写入 U 盘
```bash
# 查看 U 盘设备
lsblk

# 写入（替换 sdX 为你的 U 盘设备）
sudo dd if=output/CleanLinux_RTX2060_x86_64.iso of=/dev/sdX bs=4M status=progress
sync
```

## 云服务器方案（推荐）

如果暂时没有 Linux 机器，可以使用免费云服务器：

### 方案 A：GitHub Actions（免费，无需服务器）
```yaml
# .github/workflows/build-iso.yml
name: Build CleanLinux ISO
on: [push]
jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - run: |
          sudo pacman -Syu archiso --noconfirm || sudo apt install archiso -y
          cd iso-build && sudo bash build-iso.sh
      - uses: actions/upload-artifact@v3
        with:
          name: CleanLinux-ISO
          path: iso-build/output/*.iso
```

### 方案 B：Oracle Cloud Free Tier（免费 VPS）
```bash
# 1. 注册 Oracle Cloud Free Tier
# https://www.oracle.com/cloud/free/

# 2. 创建 Ubuntu VM
# 3. SSH 连接并构建
ssh oracle@your-server-ip
git clone https://github.com/your-repo/CleanLinux.git
cd CleanLinux/iso-build
sudo apt install archiso genisoimage
sudo bash build-iso.sh
```

### 方案 C：Google Cloud Shell（免费，临时）
```bash
# 1. 打开 https://console.cloud.google.com/cloudshell
# 2. 克隆项目
git clone <your-repo>
cd CleanLinux/iso-build
# 3. 由于 GCP Shell 限制，可能需要使用其他方案
```

## 虚拟机方案

### 使用 UTM（macOS）
```bash
# 1. 安装 UTM
# https://mac.getutm.app

# 2. 下载 Arch Linux ISO
wget https://mirrors.tuna.tsinghua.edu.cn/archlinux/iso/latest/archlinux-x86_64.iso

# 3. 创建虚拟机并安装 Arch Linux

# 4. 在虚拟机内构建
sudo pacman -S archiso
cd /path/to/CleanLinux/iso-build
sudo bash build-iso.sh
```

### 使用 VirtualBox
```bash
# 类似 UTM，安装 Arch Linux 虚拟机后构建
```

## 快速验证脚本

在 Linux 机器上运行以下脚本验证环境：
```bash
#!/bin/bash
echo "=== 检查构建环境 ==="
echo ""
echo "1. archiso:"
which mkarchiso && echo "   ✅ mkarchiso 已安装" || echo "   ❌ 需要安装 archiso"
echo ""
echo "2. genisoimage:"
which genisoimage && echo "   ✅ genisoimage 已安装" || echo "   ❌ 需要安装"
echo ""
echo "3. xorriso:"
which xorriso && echo "   ✅ xorriso 已安装" || echo "   ⚠️  可选"
echo ""
echo "4. 磁盘空间:"
avail=$(df -BG . | tail -1 | awk '{print $4}' | tr -d 'G')
if [ "$avail" -gt 10 ]; then
    echo "   ✅ 可用空间: ${avail}GB"
else
    echo "   ❌ 空间不足，需要至少 10GB"
fi
echo ""
echo "5. 内存:"
mem=$(free -g | awk '/^Mem:/{print $7}')
if [ "$mem" -gt 2 ]; then
    echo "   ✅ 可用内存: ${mem}GB"
else
    echo "   ⚠️  内存可能不足，建议 8GB+"
fi
```

## 常见问题

### Q: 没有 Linux 机器怎么办？
A: 使用 GitHub Actions（免费）或 Oracle Cloud Free Tier（永久免费 VPS）

### Q: 需要多久构建？
A: 
- 仅配置文件：~1 分钟
- 完整编译 llama.cpp：~10-30 分钟（取决于 CPU）

### Q: 可以在 Docker 中构建吗？
A: 可以，但需要挂载目录并安装 archiso：
```bash
docker run --rm -it -v "$(pwd)":/workspace archlinux:latest bash
# 然后在容器内执行构建
```

### Q: 需要 NVIDIA GPU 吗？
A: 不需要。NVIDIA 驱动和 CUDA 工具链是在 ISO 内配置，构建时只需要 x86_64 CPU。

## 推荐方案总结

| 方案 | 难度 | 时间 | 成本 | 推荐度 |
|------|------|------|------|--------|
| GitHub Actions | ⭐ | 5 分钟 | 免费 | ⭐⭐⭐⭐⭐ |
| Oracle Cloud | ⭐⭐ | 15 分钟 | 免费 | ⭐⭐⭐⭐ |
| 朋友的 Linux 电脑 | ⭐ | 5 分钟 | 免费 | ⭐⭐⭐⭐ |
| UTM 虚拟机 | ⭐⭐⭐ | 30 分钟 | 免费 | ⭐⭐⭐ |
| 本地安装 archiso | ⭐⭐⭐⭐ | 20 分钟 | 免费 | ⭐⭐ |
