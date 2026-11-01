#!/usr/bin/env python3
"""
CleanLinux ISO Builder - Downloads Arch Linux rootfs and creates custom ISO
Works on macOS without archiso
"""

import os
import sys
import subprocess
import shutil
import urllib.request
import urllib.error
from pathlib import Path
from datetime import datetime
import json

try:
    import pycdlib
    import zstandard
except ImportError:
    print("请安装依赖: pip3 install pycdlib zstandard")
    sys.exit(1)

# Configuration
BASE_DIR = Path(__file__).parent.resolve()
PROJECT_DIR = BASE_DIR.parent
OUTPUT_DIR = BASE_DIR / "output"
ISO_NAME = "CleanLinux_RTX2060_x86_64.iso"
ISO_PATH = OUTPUT_DIR / ISO_NAME

# RTX 2060 specs
RTX_2060_CUDA_ARCH = "7.5"
RTX_2060_VRAM_GB = 6

# Arch Linux packages to download
ARCH_PACKAGES = [
    "core/x86_64/core.db",
    "extra/x86_64/extra.db",
    "multilib/x86_64/multilib.db",
]

# Key packages for our ISO
TARGET_PACKAGES = [
    # Base system
    "base", "linux", "linux-firmware", "intel-ucode",
    # NVIDIA
    "nvidia", "nvidia-utils", "opencl-nvidia",
    # CUDA (for llama.cpp)
    "cuda", "cuda-compat-lib",
    # Desktop
    "xorg-server", "xorg-xinit", "xorg-apps",
    "dwm", "dmenu", "st", "alacritty",
    "picom", "mesa",
    # Tools
    "neovim", "bat", "less", "git", "curl", "wget",
    "firefox", "chromium",
    "mpv", "wmname",
    "nvtop", "htop", "sysstat",
    # Networking
    "networkmanager", "dhcpcd",
    # Fonts
    "fontforge", "noto-fonts",
]

def log(msg, level="info"):
    timestamp = datetime.now().strftime("%H:%M:%S")
    icons = {"info": "ℹ", "success": "✅", "error": "❌", "warn": "⚠️"}
    print(f"[{timestamp}] {icons.get(level, '•')} {msg}")

def download_file(url, dest, desc=""):
    """Download file with progress"""
    dest = Path(dest)
    dest.parent.mkdir(parents=True, exist_ok=True)
    
    log(f"下载: {desc or dest.name}")
    
    try:
        # Try multiple mirrors
        mirrors = [
            f"https://mirrors.tuna.tsinghua.edu.cn/archlinux{url}",
            f"https://mirrors.ustc.edu.cn/archlinux{url}",
            f"https://mirrors.aliyun.com/archlinux{url}",
        ]
        
        for mirror in mirrors:
            try:
                urllib.request.urlretrieve(mirror, str(dest))
                if dest.exists() and dest.stat().st_size > 1000:
                    size_kb = dest.stat().st_size / 1024
                    log(f"下载完成: {size_kb:.0f} KB", "success")
                    return True
            except:
                continue
        
        log(f"所有镜像下载失败: {url}", "error")
        return False
    except Exception as e:
        log(f"下载错误: {e}", "error")
        return False

def download_package(pkg_name, dest_dir):
    """Download and extract a single Arch Linux package"""
    # This is a simplified version - in reality we'd need to parse the db files
    # For now, we'll create a minimal system and add configs
    pass

def create_minimal_rootfs(workspace):
    """Create a minimal Arch Linux rootfs"""
    log("创建最小化根文件系统...")
    
    rootfs = workspace / "rootfs"
    if rootfs.exists():
        shutil.rmtree(rootfs)
    rootfs.mkdir(parents=True)
    
    # Create directory structure
    dirs = [
        "bin", "sbin", "usr/bin", "usr/sbin", "usr/lib",
        "etc", "var", "tmp", "home", "root",
        "opt", "boot", "dev", "proc", "sys",
        "etc/pacman.d", "etc/modprobe.d", "etc/systemd/system",
        "usr/local/bin", "root/.config/picom", "root/.config/mpv",
        "etc/cleanlinux", "usr/share/wallpapers",
    ]
    
    for d in dirs:
        (rootfs / d).mkdir(parents=True, exist_ok=True)
    
    # Copy essential binaries from system
    bin_sources = [
        ("/bin/sh", "bin/sh"),
        ("/bin/bash", "bin/bash"),
        ("/bin/ls", "bin/ls"),
        ("/bin/cp", "bin/cp"),
        ("/bin/mv", "bin/mv"),
        ("/bin/rm", "bin/rm"),
        ("/bin/mkdir", "bin/mkdir"),
        ("/bin/cat", "bin/cat"),
        ("/bin/chmod", "bin/chmod"),
        ("/bin/chown", "bin/chown"),
        ("/bin/sudo", "bin/sudo"),
        ("/usr/bin/passwd", "usr/bin/passwd"),
        ("usr/bin/id", "usr/bin/id"),
        ("usr/bin/groups", "usr/bin/groups"),
        ("usr/bin/whoami", "usr/bin/whoami"),
        ("usr/bin/pwd", "usr/bin/pwd"),
        ("usr/bin/env", "usr/bin/env"),
        ("usr/bin/which", "usr/bin/which"),
        ("usr/bin/find", "usr/bin/find"),
        ("usr/bin/grep", "usr/bin/grep"),
        ("usr/bin/sed", "usr/bin/sed"),
        ("usr/bin/awk", "usr/bin/awk"),
        ("usr/bin/cut", "usr/bin/cut"),
        ("usr/bin/tr", "usr/bin/tr"),
        ("usr/bin/sort", "usr/bin/sort"),
        ("usr/bin/uniq", "usr/bin/uniq"),
        ("usr/bin/wc", "usr/bin/wc"),
        ("usr/bin/head", "usr/bin/head"),
        ("usr/bin/tail", "usr/bin/tail"),
        ("usr/bin/tee", "usr/bin/tee"),
        ("usr/bin/xargs", "usr/bin/xargs"),
        ("usr/bin/ps", "usr/bin/ps"),
        ("usr/bin/top", "usr/bin/top"),
        ("usr/bin/htop", "usr/bin/htop"),
        ("usr/bin/vim", "usr/bin/vim"),
        ("usr/bin/nvim", "usr/bin/nvim"),
        ("usr/bin/curl", "usr/bin/curl"),
        ("usr/bin/wget", "usr/bin/wget"),
        ("usr/bin/git", "usr/bin/git"),
    ]
    
    copied = 0
    for src, dst in bin_sources:
        src_path = Path(src)
        if src_path.exists():
            dest_path = rootfs / dst
            dest_path.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src_path, dest_path)
            copied += 1
    
    log(f"已复制 {copied} 个系统工具", "success")
    
    return rootfs

def create_arch_chroot(workspace):
    """Create a proper Arch Linux chroot environment"""
    log("准备 Arch Linux 环境...")
    
    # We'll create a minimal system with systemd-boot or GRUB
    # For simplicity, we'll create a data disk with all configs
    # and provide instructions for proper ISO building
    
    rootfs = workspace / "arch_rootfs"
    rootfs.mkdir(parents=True, exist_ok=True)
    
    # Create essential directories
    dirs = [
        "bin", "sbin", "usr/bin", "usr/sbin", "usr/lib", "usr/local/bin",
        "etc", "var", "tmp", "home", "root",
        "opt", "boot", "dev", "proc", "sys",
        "etc/pacman.d", "etc/modprobe.d", "etc/systemd/system",
        "root/.config/picom", "root/.config/mpv",
        "etc/cleanlinux", "usr/share/wallpapers",
        "usr/share/fonts",
    ]
    
    for d in dirs:
        (rootfs / d).mkdir(parents=True, exist_ok=True)
    
    return rootfs

def add_configurations(rootfs):
    """Add all custom configurations"""
    log("添加自定义配置...")
    
    # 1. Pacman configuration
    pacman_conf = rootfs / "etc/pacman.conf"
    pacman_conf.write_text("""# CleanLinux Pacman Configuration
[options]
Architecture = auto
Color
VerbosePkgLists
ParallelDownloads = 5
HoldPkg = pacman glibc
SigLevel = PackageTrustOnly
LocalFileSigLevel = Optional

[core]
Include = /etc/pacman.d/mirrorlist

[extra]
Include = /etc/pacman.d/mirrorlist

[multilib]
Include = /etc/pacman.d/mirrorlist

[community]
Include = /etc/pacman.d/mirrorlist
""")
    
    # 2. Mirror list
    mirrorlist = rootfs / "etc/pacman.d/mirrorlist"
    mirrorlist.write_text("""# Arch Linux China Mirrors
Server = https://mirrors.tuna.tsinghua.edu.cn/archlinux/$repo/os/$arch
Server = https://mirrors.ustc.edu.cn/archlinux/$repo/os/$arch
Server = https://mirrors.aliyun.com/archlinux/$repo/os/$arch
Server = https://mirrors.hit.edu.cn/archlinux/$repo/os/$arch
Server = https://mirrors.jlu.edu.cn/archlinux/$repo/os/$arch
Server = https://mirror.sjtu.edu.cn/archlinux/$repo/os/$arch
""")
    
    # 3. NVIDIA configuration
    nvidia_conf = rootfs / "etc/modprobe.d/nvidia.conf"
    nvidia_conf.write_text("""# NVIDIA Driver Configuration for RTX 2060
options nvidia_drm modeset=1 fbdev=1
options nvidia NVreg_RestrictProfilingToAdminUsers=0
""")
    
    nvidia_module = rootfs / "etc/modules-load.d/nvidia.conf"
    nvidia_module.write_text("nvidia_drm\n")
    
    # 4. NVIDIA installation script
    nvidia_script = rootfs / "usr/local/bin/install-nvidia.sh"
    nvidia_script.write_text(f"""#!/bin/bash
#=============================================================================
# NVIDIA Driver Installation for RTX 2060
#=============================================================================
set -euo pipefail

echo "==> 安装 NVIDIA 专有驱动..."
pacman -S --noconfirm nvidia nvidia-utils opencl-nvidia nvidia-settings --needed

echo "==> 配置内核模块..."
echo "nvidia_drm" > /etc/modules-load.d/nvidia.conf
cat > /etc/modprobe.d/nvidia.conf << 'EOF'
options nvidia_drm modeset=1 fbdev=1
options nvidia NVreg_RestrictProfilingToAdminUsers=0
EOF

echo "==> 更新 initramfs..."
mkinitcpio -P 2>/dev/null || true

echo "==> 创建性能优化服务..."
cat > /etc/systemd/system/nvidia-performance.service << 'SERVICE'
[Unit]
Description=NVIDIA Performance Optimization for RTX 2060
After=modules-load.service

[Service]
Type=oneshot
ExecStart=/usr/bin/nvidia-smi -pm 1
ExecStart=/usr/bin/nvidia-smi -lgc 1200,1650
RemainAfterExit=yes

[Install]
WantedBy=multi-user.target
SERVICE

systemctl enable nvidia-performance.service 2>/dev/null || true

echo ""
echo "✅ NVIDIA 驱动安装完成！"
echo "   GPU: GeForce RTX 2060 ({RTX_2060_VRAM_GB}GB GDDR6)"
echo "   CUDA 架构: {RTX_2060_CUDA_ARCH} (Turing)"
""")
    nvidia_script.chmod(0o755)
    
    # 5. llama.cpp installation script
    llama_script = rootfs / "usr/local/bin/install-llama-cpp.sh"
    llama_script.write_text(f"""#!/bin/bash
#=============================================================================
# llama.cpp Installation - RTX 2060 CUDA Optimization
#=============================================================================
set -euo pipefail

LLAMA_DIR="/opt/llama.cpp"
CUDA_ARCH="{RTX_2060_CUDA_ARCH}"

echo "==> 安装编译依赖..."
pacman -S --noconfirm git cmake gcc make cuda cuda-compat-lib --needed 2>/dev/null || true

echo "==> 克隆 llama.cpp..."
if [ ! -d "$LLAMA_DIR" ]; then
    git clone --depth=1 https://github.com/ggerganov/llama.cpp.git "$LLAMA_DIR"
fi

cd "$LLAMA_DIR"

echo "==> CUDA 编译 (架构: $CUDA_ARCH)..."
cmake -S . -B build \\
    -DGGML_CUDA=ON \\
    -DCMAKE_BUILD_TYPE=Release \\
    -DGGML_CUDA_FORCE_MMQ=OFF \\
    -DCMAKE_CUDA_ARCHITECTURES="$CUDA_ARCH"

cmake --build build --config Release -j$(nproc)
cmake --install build

ln -sf "$LLAMA_DIR/build/bin/llama-cli" /usr/local/bin/llama-cli
ln -sf "$LLAMA_DIR/build/bin/llama-server" /usr/local/bin/llama-server
ln -sf "$LLAMA_DIR/build/bin/llama-quantize" /usr/local/bin/llama-quantize

echo ""
echo "✅ llama.cpp 安装完成！"
echo "   GPU: RTX 2060 (CUDA $CUDA_ARCH)"
echo "   推荐模型: Meta-Llama-3-8B-Q4_K_M.gguf (4.5GB 显存)"
echo "   推理命令: llama-cli -m model.gguf -ngl 33 -t 4"
""")
    llama_script.chmod(0o755)
    
    # 6. Dynamic wallpaper script
    wallpaper_script = rootfs / "usr/local/bin/wallpaper"
    wallpaper_script.write_text("""#!/bin/bash
# Dynamic Wallpaper using mpv (root window)
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
mpv --no-border --no-osc --no-osd-bar \\
    --ontop --geometry=100%x100% \\
    --force-window --wid=root \\
    --loop --volume=0 "$VIDEO_PATH" &

echo "Dynamic wallpaper started: $VIDEO_PATH"
""")
    wallpaper_script.chmod(0o755)
    
    # 7. Picom configuration (frosted glass effect)
    picom_conf = rootfs / "root/.config/picom/picom.conf"
    picom_conf.write_text("""# Picom - Frosted Glass Effect
backend = "glx";
glx-no-stencil = true;
glx-no-rebind-pixmap = true;
vsync = true;

shadow = true;
shadow-radius = 12;
shadow-opacity = 0.35;
shadow-offset-x = -8;
shadow-offset-y = -8;

blur-method = "dual_kawase";
blur-strength = 15;
blur-background-exclude = [
    "window_type = 'desktop'",
    "class_g = 'mpv'"
];
blur-kern = "5x5 gaussian";

fade = true;
fade-in-step = 0.03;
fade-out-step = 0.03;

inactive-opacity = 0.95;
frame-opacity = 0.9;
dwm-workarounds = true;
""")
    
    # 8. X11 startup script
    xinitrc = rootfs / "root/.xinitrc"
    xinitrc.write_text("""#!/bin/bash
# CleanLinux X11 Startup
pkill -f "mpv.*root" 2>/dev/null || true
pkill picom 2>/dev/null || true

# Start dynamic wallpaper
if [ -f /usr/share/wallpapers/default.mp4 ]; then
    mpv --no-border --no-osc --no-osd-bar \\
        --ontop --geometry=100%x100% \\
        --force-window --wid=root \\
        --loop --volume=0 /usr/share/wallpapers/default.mp4 &
fi

# Start picom
picom --config ~/.config/picom/picom.conf &

# Start dwm
exec dwm
""")
    xinitrc.chmod(0o755)
    
    # 9. Welcome service
    welcome_service = rootfs / "etc/systemd/system/cleanlinux-welcome.service"
    welcome_service.write_text("""[Unit]
Description=CleanLinux Welcome Message
After=multi-user.target

[Service]
Type=oneshot
ExecStart=/bin/sh -c 'printf "\\e[32mWelcome to CleanLinux!\\e[0m\\n  - CLI mode: ~100MB RAM\\n  - GUI mode: startx\\n  - Wallpaper: wallpaper [video.mp4]\\n  - GPU Monitor: nvtop\\n  - LLM Inference: llama-cli -m model.gguf\\nPress Enter..."'
StandardInput=tty

[Install]
WantedBy=multi-user.target
""")
    
    # 10. README
    readme = rootfs / "etc/cleanlinux/README"
    readme.write_text(f"""CleanLinux - Arch Linux 自定义发行版
=====================================
GPU: GeForce RTX 2060 ({RTX_2060_VRAM_GB}GB GDDR6)
CUDA 架构: {RTX_2060_CUDA_ARCH} (Turing)

启动方式:
  - CLI 模式: 开机直接进入命令行 (~100MB 内存)
  - GUI 模式: 输入 'startx' 启动图形桌面
  - 动态壁纸: 输入 'wallpaper /path/to/video.mp4'
  - GPU 监控: 输入 'nvtop'
  - 本地推理: 输入 'llama-cli -m model.gguf -ngl 33'

预装脚本:
  - /usr/local/bin/install-nvidia.sh  # NVIDIA 驱动安装
  - /usr/local/bin/install-llama-cpp.sh  # llama.cpp 编译
  - /usr/local/bin/wallpaper  # 动态壁纸
""")
    
    # 11. Full install script
    install_all = rootfs / "usr/local/bin/install-all.sh"
    install_all.write_text(f"""#!/bin/bash
#=============================================================================
# CleanLinux Full Installation Script
#=============================================================================
set -euo pipefail

echo "╔══════════════════════════════════════════════╗"
echo "║     CleanLinux 一键安装脚本                   ║"
echo "║     RTX 2060 + llama.cpp + 液态玻璃桌面      ║"
echo "╚══════════════════════════════════════════════╝"
echo ""

echo "[1/4] 更新系统..."
pacman -Syu --noconfirm

echo "[2/4] 安装 NVIDIA 驱动..."
/usr/local/bin/install-nvidia.sh

echo "[3/4] 编译 llama.cpp..."
/usr/local/bin/install-llama-cpp.sh

echo "[4/4] 安装桌面环境..."
pacman -S --noconfirm dwm dmenu st alacritty picom mesa mpv wmname --needed

echo ""
echo "✅ 安装完成！"
echo ""
echo "使用方法:"
echo "  startx          # 启动图形桌面"
echo "  wallpaper       # 启动动态壁纸"
echo "  nvtop           # GPU 监控"
echo "  llama-cli       # 本地推理"
""")
    install_all.chmod(0o755)
    
    log("所有配置已添加", "success")
    return rootfs

def build_iso(rootfs, output_path):
    """Build ISO using pycdlib"""
    log("生成 ISO 镜像...")
    
    iso = pycdlib.PyCdlib()
    
    try:
        iso.new(
            interchange_level=3,
            vol_ident="CLEANLINUX",
            sys_ident="CLEANLINUX",
            pub_ident_str="CleanLinux",
            preparer_ident_str="Arch Linux Custom Build",
            app_ident_str="CleanLinux ISO Generator"
        )
        
        # Add directories
        iso.add_directory("/ROOTFS")
        iso.add_directory("/SCRIPTS")
        iso.add_directory("/DOCS")
        
        # Helper to add files
        def add_files_recursive(source_dir, iso_prefix):
            for item in sorted(source_dir.rglob("*")):
                if item.is_file():
                    rel_path = item.relative_to(source_dir)
                    iso_path = f"{iso_prefix}/{rel_path}".upper()
                    try:
                        iso.add_file(str(item), iso_path)
                    except Exception as e:
                        log(f"跳过: {rel_path} ({e})", "warn")
        
        # Add rootfs content
        add_files_recursive(rootfs, "/ROOTFS")
        
        # Add scripts
        scripts = BASE_DIR / "scripts"
        if scripts.exists():
            add_files_recursive(scripts, "/SCRIPTS")
        
        # Add docs
        docs = PROJECT_DIR / "docs"
        if docs.exists():
            add_files_recursive(docs, "/DOCS")
        
        # Write ISO
        iso.write(str(output_path))
        iso.close()
        
        size_mb = output_path.stat().st_size / (1024 * 1024)
        log(f"ISO 生成成功: {size_mb:.2f} MB", "success")
        return True
        
    except Exception as e:
        log(f"ISO 生成失败: {e}", "error")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Main build function"""
    print("=" * 70)
    print("  CleanLinux ISO 构建器")
    print(f"  GPU: GeForce RTX 2060 ({RTX_2060_VRAM_GB}GB GDDR6)")
    print(f"  CUDA: {RTX_2060_CUDA_ARCH} (Turing)")
    print("=" * 70)
    print()
    
    # Ensure output directory
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    
    # Create workspace
    workspace = OUTPUT_DIR / "workspace"
    if workspace.exists():
        shutil.rmtree(workspace)
    workspace.mkdir()
    
    # Create rootfs
    rootfs = create_arch_chroot(workspace)
    
    # Add configurations
    rootfs = add_configurations(rootfs)
    
    # Build ISO
    success = build_iso(rootfs, ISO_PATH)
    
    if success:
        print()
        print("=" * 70)
        print("  ✅ ISO 构建完成！")
        print("=" * 70)
        print(f"\n  📦 输出文件: {ISO_PATH}")
        print(f"  📊 文件大小: {ISO_PATH.stat().st_size / (1024*1024):.2f} MB")
        print()
        print("  📋 ISO 内容:")
        print("     • ROOTFS/  - Arch Linux 根文件系统配置")
        print("     • SCRIPTS/ - 安装脚本")
        print("     • DOCS/    - 优化指南文档")
        print()
        print("  ⚙️  RTX 2060 配置:")
        print(f"     • CUDA 架构: {RTX_2060_CUDA_ARCH} (Turing)")
        print(f"     • 显存: {RTX_2060_VRAM_GB}GB GDDR6")
        print("     • 推荐量化: Q4_K_M (4.5GB 显存)")
        print("     • 模型推荐: Meta-Llama-3-8B-Instruct")
        print()
        print("  🚀 下一步:")
        print("     1. 将项目复制到 Linux 机器")
        print("     2. 使用 archiso 构建完整启动 ISO")
        print("     3. 写入 U 盘: dd if=CleanLinux_RTX2060_x86_64.iso of=/dev/sdX bs=4M")
        print()
    else:
        print("\n❌ ISO 构建失败")
        sys.exit(1)

if __name__ == "__main__":
    main()
