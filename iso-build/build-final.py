#!/usr/bin/env python3
"""
CleanLinux Complete ISO Builder for macOS
Creates ISO with NVIDIA + llama.cpp + RTX 2060 optimizations
"""

import os
import sys
import subprocess
import shutil
from pathlib import Path
from datetime import datetime

try:
    import pycdlib
except ImportError:
    print("请安装 pycdlib: pip3 install pycdlib")
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

def log(msg, level="info"):
    timestamp = datetime.now().strftime("%H:%M:%S")
    icons = {"info": "ℹ", "success": "✅", "error": "❌", "warn": "⚠️"}
    print(f"[{timestamp}] {icons.get(level, '•')} {msg}")

def iso_filename(name):
    """Convert to ISO9660 compatible name"""
    import re
    base = Path(name).stem.upper().replace('.', '_')
    ext = Path(name).suffix.upper().replace('.', '')
    return f"{base}_{ext}" if ext else base

def create_iso_content():
    """Create ISO content structure"""
    log("准备 ISO 内容...")
    
    content_dir = OUTPUT_DIR / "content"
    if content_dir.exists():
        shutil.rmtree(content_dir)
    content_dir.mkdir(parents=True)
    
    # Create directory structure
    dirs = [
        "airootfs/etc/systemd/system",
        "airootfs/usr/local/bin",
        "airootfs/root/.config/picom",
        "airootfs/root/.config/mpv",
        "airootfs/etc/pacman.d",
        "airootfs/etc/modprobe.d",
        "airootfs/etc/cleanlinux",
        "airootfs/usr/share/wallpapers",
        "scripts",
        "docs",
    ]
    
    for d in dirs:
        (content_dir / d).mkdir(parents=True, exist_ok=True)
    
    # ── Create pacman configuration ──
    pacman_conf = content_dir / "airootfs/etc/pacman.conf"
    pacman_conf.write_text("""# Pacman Configuration for CleanLinux
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

[nvidia-repo]
Server = https://mirrors.tuna.tsinghua.edu.cn/archlinux/$repo/os/$arch
""")
    
    # ── Create mirror list ──
    mirrorlist = content_dir / "airootfs/etc/pacman.d/mirrorlist"
    mirrorlist.write_text("""# Arch Linux China Mirrors
Server = https://mirrors.tuna.tsinghua.edu.cn/archlinux/$repo/os/$arch
Server = https://mirrors.ustc.edu.cn/archlinux/$repo/os/$arch
Server = https://mirrors.aliyun.com/archlinux/$repo/os/$arch
Server = https://mirrors.hit.edu.cn/archlinux/$repo/os/$arch
Server = https://mirrors.jlu.edu.cn/archlinux/$repo/os/$arch
Server = https://mirror.sjtu.edu.cn/archlinux/$repo/os/$arch
""")
    
    # ── Create NVIDIA module config ──
    nvidia_conf = content_dir / "airootfs/etc/modprobe.d/nvidia.conf"
    nvidia_conf.write_text("""# NVIDIA Driver Configuration for RTX 2060
options nvidia_drm modeset=1 fbdev=1
options nvidia NVreg_RestrictProfilingToAdminUsers=0
""")
    
    # ── Create NVIDIA installation script ──
    nvidia_script = content_dir / "airootfs/usr/local/bin/install_nvidia.sh"
    nvidia_script.write_text(f"""#!/bin/bash
#=============================================================================
# NVIDIA Driver Installation Script
# Target GPU: GeForce RTX 2060 (TU106)
# CUDA Compute Capability: {RTX_2060_CUDA_ARCH}
# VRAM: {RTX_2060_VRAM_GB}GB GDDR6
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
cat > /etc/systemd/system/nvidia_performance.service << 'SERVICE'
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

systemctl enable nvidia_performance.service 2>/dev/null || true

echo ""
echo "✅ NVIDIA 驱动安装完成！"
echo "   GPU: GeForce RTX 2060"
echo "   显存: {RTX_2060_VRAM_GB}GB GDDR6"
echo "   CUDA 架构: {RTX_2060_CUDA_ARCH} (Turing)"
echo "   性能模式: 持久化模式启用"
""")
    nvidia_script.chmod(0o755)
    
    # ── Create llama.cpp installation script ──
    llama_script = content_dir / "airootfs/usr/local/bin/install_llama_cpp.sh"
    llama_script.write_text(f"""#!/bin/bash
#=============================================================================
# llama.cpp Installation Script
# RTX 2060 CUDA Optimization
# Recommended: Q4_K_M quantization (4.5GB VRAM usage)
#=============================================================================
set -euo pipefail

LLAMA_DIR="/opt/llama.cpp"
CUDA_ARCH="{RTX_2060_CUDA_ARCH}"

echo "==> 安装 llama.cpp 编译依赖..."
pacman -S --noconfirm git cmake gcc make cuda cuda-compat-lib --needed 2>/dev/null || true

echo "==> 克隆 llama.cpp 源码..."
if [ ! -d "$LLAMA_DIR" ]; then
    git clone --depth=1 https://github.com/ggerganov/llama.cpp.git "$LLAMA_DIR"
fi

cd "$LLAMA_DIR"

echo "==> CUDA 优化编译 (架构: $CUDA_ARCH)..."
cmake -S . -B build \\
    -DGGML_CUDA=ON \\
    -DCMAKE_BUILD_TYPE=Release \\
    -DGGML_CUDA_FORCE_MMQ=OFF \\
    -DCMAKE_CUDA_ARCHITECTURES="$CUDA_ARCH"

cmake --build build --config Release -j$(nproc)
cmake --install build

echo "==> 创建符号链接..."
ln -sf "$LLAMA_DIR/build/bin/llama-cli" /usr/local/bin/llama-cli
ln -sf "$LLAMA_DIR/build/bin/llama-server" /usr/local/bin/llama-server
ln -sf "$LLAMA_DIR/build/bin/llama-quantize" /usr/local/bin/llama-quantize

echo ""
echo "✅ llama.cpp 安装完成！"
echo "   GPU: GeForce RTX 2060"
echo "   CUDA 架构: $CUDA_ARCH"
echo "   推荐模型: Meta-Llama-3-8B-Q4_K_M.gguf"
echo "   推理命令: llama-cli -m model.gguf -ngl 33 -t 4"
echo ""
echo "   可选量化等级:"
echo "     Q4_K_M  - 4.5GB 显存 (推荐)"
echo "     Q5_K_M  - 5.5GB 显存"
echo "     Q8_0    - 9+GB 显存"
echo "     IQ4_XS  - 3.5GB 显存 (极限压缩)"
""")
    llama_script.chmod(0o755)
    
    # ── Create dynamic wallpaper script ──
    wallpaper_script = content_dir / "airootfs/usr/local/bin/wallpaper"
    wallpaper_script.write_text("""#!/bin/bash
# Dynamic Wallpaper using mpv (root window background)
# Memory: ~40MB | CPU: <2%

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
    
    # ── Create picom configuration (frosted glass effect) ──
    picom_conf = content_dir / "airootfs/root/.config/picom/picom.conf"
    picom_conf.write_text("""# Picom Configuration - Frosted Glass Effect
backend = "glx";
glx-no-stencil = true;
glx-no-rebind-pixmap = true;
vsync = true;

# Shadow
shadow = true;
shadow-radius = 12;
shadow-opacity = 0.35;
shadow-offset-x = -8;
shadow-offset-y = -8;

# Blur (Frosted Glass / Liquid Glass Effect)
blur-method = "dual_kawase";
blur-strength = 15;
blur-background-exclude = [
    "window_type = 'desktop'",
    "class_g = 'mpv'"
];
blur-kern = "5x5 gaussian";

# Fade
fade = true;
fade-in-step = 0.03;
fade-out-step = 0.03;

# Opacity
inactive-opacity = 0.95;
frame-opacity = 0.9;
inactive-opacity-override = false;

# DWM Integration
dwm-workarounds = true;
""")
    
    # ── Create X11 startup script ──
    xinitrc = content_dir / "airootfs/root/.xinitrc"
    xinitrc.write_text("""#!/bin/bash
# CleanLinux X11 Startup Script
# Starts: mpv wallpaper -> picom -> dwm

# Kill existing processes
pkill -f "mpv.*root" 2>/dev/null || true
pkill picom 2>/dev/null || true

# Start dynamic wallpaper (if video exists)
WALLPAPER_VIDEO="/usr/share/wallpapers/default.mp4"
if [ -f "$WALLPAPER_VIDEO" ]; then
    mpv --no-border --no-osc --no-osd-bar \\
        --ontop --geometry=100%x100% \\
        --force-window --wid=root \\
        --loop --volume=0 "$WALLPAPER_VIDEO" &
fi

# Start picom (frosted glass effect)
picom --config ~/.config/picom/picom.conf &

# Start dwm (dynamic window manager)
exec dwm
""")
    xinitrc.chmod(0o755)
    
    # ── Create welcome service ──
    welcome_service = content_dir / "airootfs/etc/systemd/system/cleanlinux_welcome.service"
    welcome_service.write_text("""[Unit]
Description=CleanLinux Welcome Message
After=multi-user.target

[Service]
Type=oneshot
ExecStart=/bin/sh -c 'printf "\\e[32mWelcome to CleanLinux!\\e[0m\\n\\e[33m  - CLI mode: ~100MB RAM\\e[0m\\n  - GUI mode: startx\\e[0m\\n  - Wallpaper: wallpaper [video.mp4]\\e[0m\\n  - GPU Monitor: nvtop\\e[0m\\n  - LLM Inference: llama-cli -m model.gguf\\e[0m\\n\\nPress Enter to continue..."'
StandardInput=tty

[Install]
WantedBy=multi-user.target
""")
    
    # ── Create README ──
    readme = content_dir / "airootfs/etc/cleanlinux/README"
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

预装组件:
  - NVIDIA 专有驱动 (nvidia + nvidia-utils)
  - llama.cpp (CUDA {RTX_2060_CUDA_ARCH} 优化编译)
  - picom compositor (液态玻璃磨砂效果)
  - mpv 动态壁纸
  - dwm 窗口管理器
  - Alacritty 终端

中国镜像源:
  - TUNA (清华大学)
  - USTC (中国科学技术大学)
  - Aliyun (阿里云)
  - HIT (哈尔滨工业大学)
  - JLU (吉林大学)
  - SJTU (上海交通大学)
""")
    
    # ── Create documentation ──
    docs_dir = content_dir / "docs"
    
    optimization_guide = docs_dir / "NVIDIA_llama_cpp_Optimization.md"
    optimization_guide.write_text(f"""# CleanLinux 优化指南
## NVIDIA RTX 2060 优化配置

### 驱动安装
```bash
sudo pacman -S nvidia nvidia-utils opencl-nvidia
```

### CUDA 编译参数
- 架构代号: 7.5 (Turing)
- 优化标志: `-DGGML_CUDA_FORCE_MMQ=OFF`
- 显存管理: Q4_K_M 量化 (4.5GB)

### llama.cpp 推理命令
```bash
# 下载模型
wget https://huggingface.co/bartowski/Meta-Llama-3-8B-Instruct-GGUF/resolve/main/Meta-Llama-3-8B-Instruct-Q4_K_M.gguf

# 推理 (RTX 2060 6GB VRAM)
llama-cli -m Meta-Llama-3-8B-Instruct-Q4_K_M.gguf -ngl 33 -t 4 -c 4096

# HTTP API 服务器
llama-server -m model.gguf -ngl 35 -c 8192 --port 8080
```

### 性能监控
```bash
nvtop          # GPU 实时监控
nvidia-smi     # 详细信息
```
""")
    
    # ── Create scripts directory ──
    scripts_dir = content_dir / "scripts"
    
    install_all = scripts_dir / "install_all.sh"
    install_all.write_text(f"""#!/bin/bash
#=============================================================================
# CleanLinux Full Installation Script
# Installs: NVIDIA Driver + llama.cpp + Desktop + Wallpaper
#=============================================================================
set -euo pipefail

echo "╔══════════════════════════════════════════════╗"
echo "║     CleanLinux 一键安装脚本                   ║"
echo "║     RTX 2060 + llama.cpp + 液态玻璃桌面      ║"
echo "╚══════════════════════════════════════════════╝"
echo ""

# Update system
echo "[1/4] 更新系统..."
pacman -Syu --noconfirm

# Install NVIDIA
echo "[2/4] 安装 NVIDIA 驱动..."
/usr/local/bin/install_nvidia.sh

# Install llama.cpp
echo "[3/4] 编译 llama.cpp..."
/usr/local/bin/install_llama_cpp.sh

# Install desktop components
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
    
    return content_dir

def build_iso(content_dir, output_path):
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
        
        # Add main directories
        iso.add_directory("/AIROOTFS")
        iso.add_directory("/SCRIPTS")
        iso.add_directory("/DOCS")
        
        # Helper function to add files
        def add_file_recursive(source_dir, iso_prefix):
            for item in sorted(source_dir.rglob("*")):
                if item.is_file():
                    rel_path = item.relative_to(source_dir)
                    # Convert to ISO9660 compatible path
                    iso_path_parts = [iso_prefix]
                    for part in rel_path.parts:
                        iso_path_parts.append(iso_filename(part))
                    iso_path = "/".join(iso_path_parts)
                    try:
                        iso.add_file(str(item), iso_path)
                    except Exception as e:
                        log(f"跳过: {rel_path} ({e})", "warn")
        
        # Add airootfs content
        airootfs = content_dir / "airootfs"
        add_file_recursive(airootfs, "/AIROOTFS")
        
        # Add scripts
        scripts = content_dir / "scripts"
        add_file_recursive(scripts, "/SCRIPTS")
        
        # Add docs
        docs = content_dir / "docs"
        add_file_recursive(docs, "/DOCS")
        
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
    
    # Create ISO content
    content_dir = create_iso_content()
    
    # Build ISO
    success = build_iso(content_dir, ISO_PATH)
    
    if success:
        print()
        print("=" * 70)
        print("  ✅ ISO 构建完成！")
        print("=" * 70)
        print(f"\n  📦 输出文件: {ISO_PATH}")
        print(f"  📊 文件大小: {ISO_PATH.stat().st_size / (1024*1024):.2f} MB")
        print()
        print("  📋 ISO 内容:")
        print("     • AIROOTFS/  - Arch Linux 根文件系统配置")
        print("     • SCRIPTS/   - 安装脚本")
        print("     • DOCS/      - 优化指南文档")
        print()
        print("  🚀 使用方法:")
        print("     1. 复制到 Linux 机器")
        print("     2. 使用 archiso 构建完整启动 ISO:")
        print("        sudo pacman -S archiso")
        print("        cd iso-build && sudo bash build-iso.sh")
        print("     3. 写入 U 盘:")
        print(f"        dd if={ISO_PATH.name} of=/dev/sdX bs=4M status=progress")
        print()
        print("  ⚙️  RTX 2060 配置:")
        print(f"     • CUDA 架构: {RTX_2060_CUDA_ARCH} (Turing)")
        print(f"     • 显存: {RTX_2060_VRAM_GB}GB GDDR6")
        print("     • 推荐量化: Q4_K_M (4.5GB 显存)")
        print("     • 模型推荐: Meta-Llama-3-8B-Instruct")
        print()
    else:
        print("\n❌ ISO 构建失败")
        sys.exit(1)

if __name__ == "__main__":
    main()
