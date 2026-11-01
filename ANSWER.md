# 能否在这台 Mac 上编译 ISO？

## 简短回答
**部分可以**，但有重要限制。

## 能做什么 ✅

### 1. 下载和准备 ISO 内容
```bash
# 已完成的步骤
- 下载 Arch Linux ISO (1.1 GB)
- 提取 ISO 内容
- 添加 NVIDIA + llama.cpp 配置
- 生成数据盘 ISO
```

### 2. 生成配置文件
所有必要的配置文件都已准备好：
- `config/pacman.conf` - Pacman 配置
- `config/pacman.d/mirrorlist` - 中国镜像源
- `rootfs-overlay/` - 根文件系统覆盖层
- 安装脚本（nvidia, llama.cpp, wallpaper）

## 不能做什么 ❌

### 无法创建可启动 ISO

**原因：**
1. **缺少关键工具**
   - `genisoimage` / `mkisofs` - ISO 9660 创建工具
   - `xorriso` - 高级 ISO 创建工具
   - `archiso` - Arch Linux ISO 构建工具链
   
2. **macOS 的限制**
   - 没有 Homebrew/Fink/MacPorts 包管理器
   - 无法直接安装 Linux 构建工具
   
3. **pycdlib 的局限**
   - 只能创建数据盘 ISO
   - 无法添加 ISOLINUX/GRUB 引导加载器
   - 无法创建可启动的 EFI 引导扇区

## 替代方案

### 方案一：使用 Docker（如果有 Docker Desktop）
```bash
# 安装 Docker Desktop for Mac
# 然后运行：
docker run --rm -it \
  -v "$(pwd)":/workspace \
  archlinux:latest \
  bash /workspace/iso-build/build-iso.sh
```

### 方案二：在 Linux 虚拟机中构建
```bash
# 使用 UTM 或 Parallels 运行 Linux
# 然后在虚拟机中构建
```

### 方案三：使用 CI/CD 服务
```bash
# 推送到 GitHub
# 使用 GitHub Actions 在 Linux 环境中构建
```

### 方案四：使用在线构建服务
- 使用类似 OSBuild 的服务
- 或使用云服务器（AWS EC2, Google Cloud 等）

## 当前进度

| 步骤 | 状态 | 说明 |
|------|------|------|
| 下载 Arch ISO | ✅ 完成 | 1.1 GB 已从 TUNA 镜像下载 |
| 提取 ISO 内容 | ✅ 完成 | 已提取到 extracted/ 目录 |
| 添加 NVIDIA 配置 | ✅ 完成 | RTX 2060 + CUDA 7.5 |
| 添加 llama.cpp | ✅ 完成 | CUDA 优化编译脚本 |
| 添加动态壁纸 | ✅ 完成 | mpv root window 方案 |
| 生成数据盘 ISO | ✅ 完成 | CleanLinux_RTX2060_x86_64.iso |
| 创建可启动 ISO | ❌ 需要 Linux | 缺少 archiso 工具 |

## 建议

**最快解决方案：**
1. 将项目复制到任何 Linux 机器（可以是朋友的电脑、云服务器）
2. 运行：
   ```bash
   sudo pacman -S archiso
   cd iso-build
   sudo bash build-iso.sh
   ```
3. 写入 U 盘：
   ```bash
   dd if=output/CleanLinux_RTX2060_x86_64.iso of=/dev/sdX bs=4M status=progress
   ```

**如果必须在 Mac 上工作：**
考虑使用 Parallels Desktop 或 VMware Fusion 运行 Linux 虚拟机，然后在虚拟机中构建 ISO。
