#!/usr/bin/env python3
"""
CleanLinux Bootable ISO Builder
Downloads Arch Linux ISO, extracts, modifies, and rebuilds
"""

import os
import sys
import subprocess
import shutil
import urllib.request
from pathlib import Path
from datetime import datetime

try:
    import pycdlib
except ImportError:
    print("请安装 pycdlib: pip3 install pycdlib")
    sys.exit(1)

# Configuration
BASE_DIR = Path(__file__).parent.resolve()
ARCH_ISO_URL = "https://archive.archlinux.org/iso/2024.10.01/archlinux-2024.10.01-x86_64.iso"
ARCH_ISO_NAME = "archlinux-2024.10.01-x86_64.iso"
CLEANLINUX_ISO_NAME = "CleanLinux_RTX2060_x86_64.iso"

# RTX 2060 specs
RTX_2060_CUDA_ARCH = "7.5"
RTX_2060_VRAM_GB = 6

def log(msg, level="info"):
    timestamp = datetime.now().strftime("%H:%M:%S")
    icons = {"info": "ℹ", "success": "✅", "error": "❌", "warn": "⚠️"}
    print(f"[{timestamp}] {icons.get(level, '•')} {msg}")

def run_cmd(cmd, capture=False):
    """Run command"""
    try:
        result = subprocess.run(cmd, capture_output=capture, text=True, check=True)
        return result.stdout if capture else True
    except subprocess.CalledProcessError as e:
        log(f"命令失败: {' '.join(cmd)}", "error")
        if capture:
            print(f"错误: {e.stderr}")
        return False

def download_iso(dest):
    """Download Arch Linux ISO"""
    dest = Path(dest)
    if dest.exists() and dest.stat().st_size > 1000000:
        log(f"ISO 已存在: {dest.name}", "info")
        return True
    
    log("下载 Arch Linux ISO...")
    try:
        # Download in chunks
        urllib.request.urlretrieve(ARCH_ISO_URL, str(dest))
        size_mb = dest.stat().st_size / (1024 * 1024)
        log(f"下载完成: {size_mb:.1f} MB", "success")
        return True
    except Exception as e:
        log(f"下载失败: {e}", "error")
        return False

def extract_iso(iso_path, dest_dir):
    """Extract ISO using bsdtar"""
    dest_dir = Path(dest_dir)
    dest_dir.mkdir(parents=True, exist_ok=True)
    
    log("提取 ISO 内容...")
    
    # Try bsdtar
    if run_cmd(["bsdtar", "-xf", str(iso_path), "-C", str(dest_dir)]):
        log("ISO 提取完成", "success")
        return True
    
    # Try 7z
    if shutil.which("7z"):
        if run_cmd(["7z", "x", str(iso_path), f"-o{dest_dir}"]):
            log("ISO 提取完成 (7z)", "success")
            return True
    
    log("ISO 提取失败", "error")
    return False

def modify_rootfs(rootfs_dir):
    """Modify the root filesystem"""
    rootfs = Path(rootfs_dir)
    
    log("修改根文件系统...")
    
    # Find airootfs or rootfs
    airootfs = None
    for name in ["airootfs", "root", "rootfs"]:
        candidate = rootfs / name
        if candidate.exists():
            airootfs = candidate
            break
    
    if not airootfs:
        log("未找到根文件系统目录", "error")
        return False
    
    log(f"找到根文件系统: {airootfs}")
    
    # Create directories
    dirs = [
        airootfs / "etc/pacman.d",
        airootfs / "etc/modprobe.d",
        airootfs / "etc/systemd/system",
        airootfs / "etc/cleanlinux",
        airootfs / "usr/local/bin",
        airootfs / "root/.config/picom",
        airootfs / "root/.config/mpv",
        airootfs / "usr/share/wallpapers",
    ]
    
    for d in dirs:
        d.mkdir(parents=True, exist_ok=True)
    
    # Add pacman config
    pacman_conf = airootfs / "etc/pacman.conf"
    if pacman_conf.exists():
        # Append our repo
        with open(pacman_conf, "a") as f:
            f.write("""
[nvidia-repo]
Server = https://mirrors.tuna.tsinghua.edu.cn/archlinux/$repo/os/$arch
""")
    
    # Add mirror list
    mirrorlist = airootfs / "etc/pacman.d/mirrorlist"
    mirrorlist.write_text("""# CleanLinux Mirror List
Server = https://mirrors.tuna.tsinghua.edu.cn/archlinux/$repo/os/$arch
Server = https://mirrors.ustc.edu.cn/archlinux/$repo/os/$arch
Server = https://mirrors.aliyun.com/archlinux/$repo/os/$arch
Server = https://mirrors.hit.edu.cn/archlinux/$repo/os/$arch
Server = https://mirrors.jlu.edu.cn/archlinux/$repo/os/$arch
Server = https://mirror.sjtu.edu.cn/archlinux/$repo/os/$arch
""")
    
    # Add NVIDIA config
    nvidia_conf = airootfs / "etc/modprobe.d/nvidia.conf"
    nvidia_conf.write_text("""# NVIDIA Driver Configuration for RTX 2060
options nvidia_drm modeset=1 fbdev=1
options nvidia NVreg_RestrictProfilingToAdminUsers=0
""")
    
    # Add NVIDIA module load
    (airootfs / "etc/modules-load.d/nvidia.conf").write_text("nvidia_drm\n")
    
    # Add installation scripts
    scripts = airootfs / "usr/local/bin"
    
    (scripts / "install-nvidia.sh").write_text(f"""#!/bin/bash
set -euo pipefail
echo "==> 安装 NVIDIA 驱动 (RTX 2060, CUDA {RTX_2060_CUDA_ARCH})..."
pacman -S --noconfirm nvidia nvidia-utils opencl-nvidia nvidia-settings --needed
echo "==> 配置内核模块..."
echo "nvidia_drm" > /etc/modules-load.d/nvidia.conf
cat > /etc/modprobe.d/nvidia.conf << 'EOF'
options nvidia_drm modeset=1 fbdev=1
options nvidia NVreg_RestrictProfilingToAdminUsers=0
EOF
echo "==> 更新 initramfs..."
mkinitcpio -P 2>/dev/null || true
echo "✅ NVIDIA 驱动安装完成！"
""")
    (scripts / "install-nvidia.sh").chmod(0o755)
    
    (scripts / "install-llama-cpp.sh").write_text(f"""#!/bin/bash
set -euo pipefail
LLAMA_DIR="/opt/llama.cpp"
CUDA_ARCH="{RTX_2060_CUDA_ARCH}"
echo "==> 安装 llama.cpp (CUDA {RTX_2060_CUDA_ARCH} 优化)..."
pacman -S --noconfirm git cmake gcc make cuda cuda-compat-lib --needed 2>/dev/null || true
if [ ! -d "$LLAMA_DIR" ]; then
    git clone --depth=1 https://github.com/ggerganov/llama.cpp.git "$LLAMA_DIR"
fi
cd "$LLAMA_DIR"
cmake -S . -B build -DGGML_CUDA=ON -DCMAKE_BUILD_TYPE=Release -DGGML_CUDA_FORCE_MMQ=OFF -DCMAKE_CUDA_ARCHITECTURES="$CUDA_ARCH"
cmake --build build --config Release -j$(nproc)
cmake --install build
ln -sf "$LLAMA_DIR/build/bin/llama-cli" /usr/local/bin/llama-cli
ln -sf "$LLAMA_DIR/build/bin/llama-server" /usr/local/bin/llama-server
echo "✅ llama.cpp 安装完成！GPU: RTX 2060 (CUDA $CUDA_ARCH)"
""")
    (scripts / "install-llama-cpp.sh").chmod(0o755)
    
    (scripts / "wallpaper").write_text("""#!/bin/bash
VIDEO_PATH="${1:-/usr/share/wallpapers/default.mp4}"
MPV_CONF="$HOME/.config/mpv/mpv.conf"
mkdir -p "$HOME/.config/mpv"
cat > "$MPV_CONF" << 'EOF'
no-border
no-osc
no-osd-bar
ontop
geometry=100%x100%
force-window
wid=root
loop
volume=0
EOF
pkill -f "mpv.*root" 2>/dev/null || true
mpv --no-border --no-osc --no-osd-bar --ontop --geometry=100%x100% --force-window --wid=root --loop --volume=0 "$VIDEO_PATH" &
echo "Dynamic wallpaper started"
""")
    (scripts / "wallpaper").chmod(0o755)
    
    # Add picom config
    (airootfs / "root/.config/picom/picom.conf").write_text("""backend = "glx";
glx-no-stencil = true;
vsync = true;
shadow = true;
shadow-radius = 12;
shadow-opacity = 0.35;
blur-method = "dual_kawase";
blur-strength = 15;
blur-background-exclude = ["window_type = 'desktop'", "class_g = 'mpv'"];
fade = true;
fade-in-step = 0.03;
fade-out-step = 0.03;
inactive-opacity = 0.95;
""")
    
    # Add X11 startup
    (airootfs / "root/.xinitrc").write_text("""#!/bin/bash
pkill -f "mpv.*root" 2>/dev/null || true
pkill picom 2>/dev/null || true
if [ -f /usr/share/wallpapers/default.mp4 ]; then
    mpv --no-border --no-osc --no-osd-bar --ontop --geometry=100%x100% --force-window --wid=root --loop --volume=0 /usr/share/wallpapers/default.mp4 &
fi
picom --config ~/.config/picom/picom.conf &
exec dwm
""")
    (airootfs / "root/.xinitrc").chmod(0o755)
    
    # Add README
    (airootfs / "etc/cleanlinux/README").write_text(f"""CleanLinux - Arch Linux 自定义发行版
=====================================
GPU: GeForce RTX 2060 ({RTX_2060_VRAM_GB}GB GDDR6)
CUDA 架构: {RTX_2060_CUDA_ARCH} (Turing)

启动方式:
  - CLI: 开机直接进入命令行 (~100MB 内存)
  - GUI: 输入 'startx'
  - 壁纸: 输入 'wallpaper [video.mp4]'
  - GPU: 输入 'nvtop'
  - LLM: 输入 'llama-cli -m model.gguf -ngl 33'

安装脚本:
  - /usr/local/bin/install-nvidia.sh
  - /usr/local/bin/install-llama-cpp.sh
  - /usr/local/bin/wallpaper
""")
    
    log("根文件系统修改完成", "success")
    return airootfs

def rebuild_iso(extracted_dir, output_path):
    """Rebuild ISO with modifications"""
    output_path = Path(output_path)
    
    log("重建 ISO...")
    
    # Find boot files
    boot_dir = Path(extracted_dir) / "boot"
    if not boot_dir.exists():
        # Try other locations
        for d in ["isolinux", "efi", "syslinux"]:
            candidate = Path(extracted_dir) / d
            if candidate.exists():
                boot_dir = candidate
                break
    
    # Use pycdlib to create ISO
    iso = pycdlib.PyCdlib()
    
    try:
        # Create new ISO
        iso.new(
            interchange_level=3,
            vol_ident="CLEANLINUX",
            sys_ident="CLEANLINUX"
        )
        
        # Copy existing structure
        def add_dir_recursive(source, iso_path):
            iso.add_directory(iso_path)
            for item in source.iterdir():
                if item.is_dir():
                    add_dir_recursive(item, f"{iso_path}/{item.name}")
                else:
                    try:
                        iso.add_file(str(item), f"{iso_path}/{item.name}")
                    except:
                        pass
        
        # Add boot directory if exists
        if boot_dir.exists():
            add_dir_recursive(boot_dir, "/boot")
        
        # Add modified rootfs
        extracted = Path(extracted_dir)
        for item in extracted.iterdir():
            if item.is_dir() and item.name in ["airootfs", "root", "rootfs"]:
                add_dir_recursive(item, f"/{item.name.upper()}")
        
        # Write ISO
        iso.write(str(output_path))
        iso.close()
        
        size_mb = output_path.stat().st_size / (1024 * 1024)
        log(f"ISO 重建完成: {size_mb:.1f} MB", "success")
        return True
        
    except Exception as e:
        log(f"ISO 重建失败: {e}", "error")
        return False

def main():
    """Main build function"""
    print("=" * 70)
    print("  CleanLinux Bootable ISO Builder")
    print(f"  GPU: GeForce RTX 2060 ({RTX_2060_VRAM_GB}GB GDDR6)")
    print(f"  CUDA: {RTX_2060_CUDA_ARCH} (Turing)")
    print("=" * 70)
    print()
    
    # Setup directories
    workspace = BASE_DIR / "workspace"
    output_dir = BASE_DIR / "output"
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Step 1: Download ISO
    iso_path = workspace / ARCH_ISO_NAME
    if not download_iso(iso_path):
        sys.exit(1)
    
    # Step 2: Extract ISO
    extracted_dir = workspace / "extracted"
    if not extract_iso(iso_path, extracted_dir):
        sys.exit(1)
    
    # Step 3: Modify rootfs
    rootfs = modify_rootfs(extracted_dir)
    if not rootfs:
        sys.exit(1)
    
    # Step 4: Rebuild ISO
    output_path = output_dir / CLEANLINUX_ISO_NAME
    if not rebuild_iso(extracted_dir, output_path):
        sys.exit(1)
    
    print()
    print("=" * 70)
    print("  ✅ ISO 构建完成！")
    print("=" * 70)
    print(f"\n  📦 输出文件: {output_path}")
    print(f"  📊 文件大小: {output_path.stat().st_size / (1024*1024):.1f} MB")
    print()
    print("  ⚠️  注意: 此 ISO 可能不是完全可启动的")
    print("     需要在 Linux 机器上使用 archiso 进行最终构建")
    print()

if __name__ == "__main__":
    main()
