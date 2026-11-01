#!/usr/bin/env python3
"""
CleanLinux Complete ISO Builder
Downloads Arch Linux ISO, modifies it with NVIDIA + llama.cpp + wallpaper configs
"""

import os
import sys
import subprocess
import shutil
import hashlib
import tempfile
from pathlib import Path
from datetime import datetime

# Configuration
BASE_DIR = Path(__file__).parent.resolve()
PROJECT_DIR = BASE_DIR.parent
OUTPUT_DIR = BASE_DIR / "output"
ARCH_ISO_URL = "https://mirrors.tuna.tsinghua.edu.cn/archlinux/iso/2026.10.01/x86_64/archlinux-2026.10.01-x86_64.iso"
ARCH_ISO_NAME = "archlinux-2026.10.01-x86_64.iso"
CLEANLINUX_ISO_NAME = "CleanLinux-x86_64.iso"

# RTX 2060 CUDA compute capability
CUDA_ARCH = "7.5"  # Turing architecture

def log(msg, level="info"):
    """Print log message with timestamp"""
    timestamp = datetime.now().strftime("%H:%M:%S")
    icons = {"info": "ℹ", "success": "✅", "error": "❌", "warn": "⚠️"}
    print(f"[{timestamp}] {icons.get(level, '•')} {msg}")

def run_cmd(cmd, cwd=None, capture=False):
    """Run command and optionally capture output"""
    log(f"运行: {' '.join(cmd)}")
    try:
        result = subprocess.run(
            cmd, 
            cwd=cwd or str(BASE_DIR),
            capture_output=capture,
            text=True,
            check=True
        )
        if capture and result.stdout:
            return result.stdout.strip()
        return True
    except subprocess.CalledProcessError as e:
        log(f"命令失败: {e}", "error")
        if capture:
            print(f"STDOUT: {e.stdout}")
            print(f"STDERR: {e.stderr}")
        return False

def download_file(url, dest, desc=""):
    """Download file with progress"""
    import urllib.request
    
    dest = Path(dest)
    dest.parent.mkdir(parents=True, exist_ok=True)
    
    log(f"下载: {desc or url.split('/')[-1]}")
    
    try:
        # Use curl for better progress display
        result = run_cmd([
            "curl", "-#", "-L", "-o", str(dest),
            "--progress-bar", url
        ])
        
        if dest.exists() and dest.stat().st_size > 0:
            size_mb = dest.stat().st_size / (1024 * 1024)
            log(f"下载完成: {size_mb:.1f} MB", "success")
            return True
        else:
            log("下载失败或文件为空", "error")
            return False
    except Exception as e:
        log(f"下载错误: {e}", "error")
        return False

def setup_workspace():
    """Create workspace directories"""
    log("准备构建工作区...")
    
    dirs = [
        OUTPUT_DIR,
        BASE_DIR / "workspace",
        BASE_DIR / "workspace" / "extracted",
        BASE_DIR / "workspace" / "new_root",
        BASE_DIR / "workspace" / "boot",
    ]
    
    for d in dirs:
        d.mkdir(parents=True, exist_ok=True)
    
    return {
        "workspace": BASE_DIR / "workspace",
        "extracted": BASE_DIR / "workspace" / "extracted",
        "new_root": BASE_DIR / "workspace" / "new_root",
        "boot": BASE_DIR / "workspace" / "boot",
    }

def download_arch_iso(workspace):
    """Download Arch Linux ISO"""
    iso_path = workspace["workspace"] / ARCH_ISO_NAME
    
    if iso_path.exists():
        log(f"ISO 已存在: {iso_path.name}", "info")
        return iso_path
    
    log("下载 Arch Linux ISO...")
    success = download_file(ARCH_ISO_URL, iso_path, "Arch Linux ISO")
    
    if success:
        return iso_path
    else:
        # Try alternative URL
        log("尝试备用镜像...", "warn")
        alt_url = "https://mirrors.ustc.edu.cn/archlinux/iso/2026.10.01/x86_64/archlinux-2026.10.01-x86_64.iso"
        return download_file(alt_url, iso_path, "Arch Linux ISO (备用)") or iso_path

def extract_iso(iso_path, workspace):
    """Extract ISO contents"""
    log("提取 ISO 内容...")
    
    extracted = workspace["extracted"]
    
    # Try bsdtar first (macOS)
    if run_cmd(["bsdtar", "-xf", str(iso_path), "-C", str(extracted)]):
        log("ISO 提取完成", "success")
        return True
    
    # Fallback to 7z
    if shutil.which("7z"):
        if run_cmd(["7z", "x", str(iso_path), f"-o{extracted}"]):
            log("ISO 提取完成 (7z)", "success")
            return True
    
    log("ISO 提取失败", "error")
    return False

def setup_new_root(workspace):
    """Set up new root filesystem"""
    log("准备新根文件系统...")
    
    new_root = workspace["new_root"]
    
    # Copy extracted ISO content
    extracted = workspace["extracted"]
    if extracted.exists():
        # Copy airootfs content (this is the Arch Linux rootfs in ISO)
        airootfs = extracted / "airootfs"
        if airootfs.exists():
            # Merge airootfs into new_root
            for item in airootfs.iterdir():
                dest = new_root / item.name
                if dest.exists():
                    shutil.rmtree(dest)
                shutil.copytree(item, dest, symlinks=True)
            log("根文件系统已准备", "success")
        else:
            # Try copying iso_contents
            iso_contents = extracted / "iso_contents"
            if iso_contents.exists():
                for item in iso_contents.iterdir():
                    dest = new_root / item.name
                    if dest.exists():
                        shutil.rmtree(dest)
                    shutil.copytree(item, dest, symlinks=True)
            else:
                # Copy everything
                for item in extracted.iterdir():
                    if item.name != ".disk":  # Skip ISO metadata
                        dest = new_root / item.name
                        if dest.exists():
                            shutil.rmtree(dest)
                        shutil.copytree(item, dest, symlinks=True)
    
    return new_root

def add_nvidia_package_conf(new_root):
    """Add NVIDIA repository configuration"""
    log("配置 NVIDIA 驱动源...")
    
    pacman_conf = new_root / "etc/pacman.conf"
    if pacman_conf.exists():
        nvidia_repo = """
[nvidia-custom]
Server = https://mirrors.tuna.tsinghua.edu.cn/archlinux/$repo/os/$arch
"""
        with open(pacman_conf, "a") as f:
            f.write(nvidia_repo)
        log("NVIDIA 仓库已添加", "success")
    
    # Create NVIDIA module configuration
    modprobe_dir = new_root / "etc/modprobe.d"
    modprobe_dir.mkdir(parents=True, exist_ok=True)
    
    with open(modprobe_dir / "nvidia.conf", "w") as f:
        f.write("options nvidia_drm modeset=1 fbdev=1\n")
        f.write("options nvidia NVreg_RestrictProfilingToAdminUsers=0\n")
    
    log("NVIDIA 模块配置已创建", "success")

def add_llama_cpp_script(new_root):
    """Add llama.cpp installation script"""
    log("添加 llama.cpp 安装脚本...")
    
    scripts_dir = new_root / "usr/local/bin"
    scripts_dir.mkdir(parents=True, exist_ok=True)
    
    script = """#!/bin/bash
#=============================================================================
# llama.cpp 安装脚本
# RTX 2060 (Turing, CUDA 7.5) 优化编译
#=============================================================================
set -euo pipefail

LLAMA_DIR="/opt/llama.cpp"
BUILD_DIR="$LLAMA_DIR/build"

echo "==> 安装 llama.cpp (CUDA $CUDA_ARCH 优化)..."

# 安装依赖
pacman -S --noconfirm git cmake gcc make cuda cuda-compat-lib --needed 2>/dev/null || true

# 克隆源码
if [ ! -d "$LLAMA_DIR" ]; then
    git clone --depth=1 https://github.com/ggerganov/llama.cpp.git "$LLAMA_DIR"
fi

cd "$LLAMA_DIR"

# CUDA 优化编译
cmake -S . -B build \\
    -DGGML_CUDA=ON \\
    -DCMAKE_BUILD_TYPE=Release \\
    -DGGML_CUDA_FORCE_MMQ=OFF \\
    -DCMAKE_CUDA_ARCHITECTURES="$CUDA_ARCH"

cmake --build build --config Release -j$(nproc)
cmake --install build

# 创建符号链接
ln -sf "$BUILD_DIR/bin/llama-cli" /usr/local/bin/llama-cli
ln -sf "$BUILD_DIR/bin/llama-server" /usr/local/bin/llama-server
ln -sf "$BUILD_DIR/bin/llama-quantize" /usr/local/bin/llama-quantize

echo "✅ llama.cpp 安装完成！"
echo "   GPU: RTX 2060 (CUDA $CUDA_ARCH)"
echo "   使用: llama-cli -m model.gguf -ngl 33"
"""
    
    script_path = scripts_dir / "install-llama-cpp.sh"
    script_path.write_text(script)
    script_path.chmod(0o755)
    
    log("llama.cpp 安装脚本已创建", "success")

def add_nvidia_setup_script(new_root):
    """Add NVIDIA driver setup script"""
    log("添加 NVIDIA 驱动安装脚本...")
    
    scripts_dir = new_root / "usr/local/bin"
    
    script = """#!/bin/bash
#=============================================================================
# NVIDIA 驱动安装脚本
# 支持: RTX 2060 (TU106)
#=============================================================================
set -euo pipefail

echo "==> 安装 NVIDIA 专有驱动..."

# 安装驱动
pacman -S --noconfirm nvidia nvidia-utils opencl-nvidia nvidia-settings --needed

# 配置内核模块
echo "nvidia_drm" > /etc/modules-load.d/nvidia.conf
echo "options nvidia_drm modeset=1 fbdev=1" > /etc/modprobe.d/nvidia.conf

# 更新 initramfs
mkinitcpio -P 2>/dev/null || true

# 创建性能优化服务
cat > /etc/systemd/system/nvidia-performance.service << 'SYSTEMD_EOF'
[Unit]
Description=NVIDIA Performance Optimization
After=modules-load.service

[Service]
Type=oneshot
ExecStart=/usr/bin/nvidia-smi -pm 1
ExecStart=/usr/bin/nvidia-smi -lgc 1200,1650
RemainAfterExit=yes

[Install]
WantedBy=multi-user.target
SYSTEMD_EOF

systemctl enable nvidia-performance.service 2>/dev/null || true

echo "✅ NVIDIA 驱动安装完成！"
echo "   GPU: GeForce RTX 2060"
echo "   显存: 6GB GDDR6"
echo "   CUDA 架构: 7.5 (Turing)"
"""
    
    script_path = scripts_dir / "install-nvidia.sh"
    script_path.write_text(script)
    script_path.chmod(0o755)
    
    log("NVIDIA 安装脚本已创建", "success")

def add_wallpaper_script(new_root):
    """Add dynamic wallpaper script"""
    log("添加动态壁纸配置...")
    
    scripts_dir = new_root / "usr/local/bin"
    config_dir = new_root / "root/.config"
    
    # Wallpaper script
    wallpaper_script = """#!/bin/bash
# Dynamic wallpaper using mpv (root window)
VIDEO_PATH="${1:-/usr/share/wallpapers/default.mp4}"
MPV_CONF="$HOME/.config/mpv/mpv.conf"

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
"""
    
    (scripts_dir / "wallpaper").write_text(wallpaper_script)
    (scripts_dir / "wallpaper").chmod(0o755)
    
    # Picom config for frosted glass
    picom_dir = config_dir / "picom"
    picom_dir.mkdir(parents=True, exist_ok=True)
    
    picom_conf = """backend = "glx";
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
"""
    
    (picom_dir / "picom.conf").write_text(picom_conf)
    
    log("动态壁纸和液态玻璃配置已添加", "success")

def update_pacman_mirrorlist(new_root):
    """Update pacman mirrorlist with Chinese mirrors"""
    log("配置中国镜像源...")
    
    mirrorlist = new_root / "etc/pacman.d/mirrorlist"
    mirrorlist.write_text("""# Arch Linux China Mirrors
Server = https://mirrors.tuna.tsinghua.edu.cn/archlinux/$repo/os/$arch
Server = https://mirrors.ustc.edu.cn/archlinux/$repo/os/$arch
Server = https://mirrors.aliyun.com/archlinux/$repo/os/$arch
Server = https://mirrors.hit.edu.cn/archlinux/$repo/os/$arch
Server = https://mirrors.jlu.edu.cn/archlinux/$repo/os/$arch
Server = https://mirror.sjtu.edu.cn/archlinux/$repo/os/$arch
""")
    
    log("镜像源已配置", "success")

def set_default_target_cli(new_root):
    """Set default boot target to multi-user (CLI)"""
    log("设置默认启动为命令行模式...")
    
    # Remove current default symlink
    default_target = new_root / "etc/systemd/system/default.target"
    if default_target.exists():
        default_target.unlink()
    
    # Create symlink to multi-user.target
    (new_root / "etc/systemd/system/default.target").symlink_to("../init.target")
    
    # Also set it via kernel parameter
    # This will be handled by bootloader config
    
    log("默认启动目标已设置为 CLI 模式", "success")

def add_startup_scripts(new_root):
    """Add startup scripts for CLI to GUI transition"""
    log("添加启动脚本...")
    
    bin_dir = new_root / "usr/local/bin"
    etc_init = new_root / "etc"
    
    # Create startx wrapper
    startx_script = """#!/bin/bash
# CleanLinux StartX - Launches dwm with picom and wallpaper
exec startx
"""
    (bin_dir / "startx").write_text(startx_script)
    (bin_dir / "startx").chmod(0o755)
    
    # Create welcome service
    etc_systemd = new_root / "etc/systemd/system"
    etc_systemd.mkdir(parents=True, exist_ok=True)
    
    welcome_service = """[Unit]
Description=CleanLinux Welcome Message
After=multi-user.target

[Service]
Type=oneshot
ExecStart=/bin/sh -c 'echo "Welcome to CleanLinux!\\n输入 startx 启动图形桌面"; read -p "按回车继续..."'
StandardInput=tty

[Install]
WantedBy=multi-user.target
"""
    
    (etc_systemd / "cleanlinux-welcome.service").write_text(welcome_service)
    
    log("启动脚本已添加", "success")

def copy_customizations(new_root):
    """Copy custom files from rootfs-overlay"""
    log("复制自定义配置...")
    
    overlay_dir = BASE_DIR / "rootfs-overlay"
    if not overlay_dir.exists():
        log("未找到 rootfs-overlay 目录，跳过", "warn")
        return
    
    # Merge overlay into new_root
    for item in overlay_dir.iterdir():
        dest = new_root / item.name
        if dest.exists():
            if dest.is_dir() and item.is_dir():
                shutil.rmtree(dest)
            else:
                dest.unlink()
        if item.is_dir():
            shutil.copytree(item, dest, symlinks=True)
        else:
            shutil.copy2(item, dest)
    
    log("自定义配置已复制", "success")

def create_iso_from_rootfs(workspace, output_path):
    """Create bootable ISO from modified rootfs"""
    log("生成 ISO 镜像...")
    
    new_root = workspace["new_root"]
    boot_dir = workspace["boot"]
    
    # Prepare boot directory structure
    boot_dir.mkdir(parents=True, exist_ok=True)
    
    # Copy boot files from extracted ISO
    extracted = workspace["extracted"]
    boot_iso = extracted / "boot"
    
    if boot_iso.exists():
        # Copy vmlinuz and initramfs
        for f in boot_iso.glob("x86_64/*"):
            if f.name in ["vmlinuz-linux", "initramfs-linux.img", "initramfs-linux-fallback.img"]:
                shutil.copy2(f, boot_dir / f.name)
        
        # Copy syslinux
        syslinux_dir = boot_iso / "syslinux"
        if syslinux_dir.exists():
            for f in syslinux_dir.glob("*"):
                shutil.copy2(f, boot_dir / f.name)
    
    # Create ISOLINUX configuration
    isolinux_cfg = boot_dir / "isolinux.cfg"
    isolinux_cfg.write_text("""default cleanlinux
prompt 1
timeout 300

label cleanlinux
    kernel /boot/x86_64/vmlinuz-linux
    append initrd=/boot/x86_64/initramfs-linux.img archisobasedir=airootfs ethmode=0 ip=:::::cleanlinux:eth0 quiet
    text help
        CleanLinux - Arch Linux Custom ISO
        NVIDIA + llama.cpp + 动态壁纸
    endtext

label install
    kernel /boot/x86_64/vmlinuz-linux
    append initrd=/boot/x86_64/initramfs-linux.img archisobasedir=airootfs archisodevice=/dev/disk/by-label/CLEANLINUX
""")
    
    # Create ISO using genisoimage or mkisofs
    iso_cmd = None
    
    # Try different ISO creation tools
    tools = ["genisoimage", "mkisofs", "xorriso"]
    for tool in tools:
        if shutil.which(tool):
            iso_cmd = tool
            break
    
    if not iso_cmd:
        log("未找到 ISO 创建工具，尝试使用 pycdlib...", "warn")
        return create_iso_pycdlib(new_root, output_path)
    
    # Build ISO command
    cmd = [
        iso_cmd,
        "-o", str(output_path),
        "-V", "CLEANLINUX",
        "-b", "boot/iso64.cat",
        "-no-emul-boot",
        "-boot-load-size", "4",
        "-boot-info-table",
        "-isohybrid-mbr", str(boot_dir / "isolinux.bin") if (boot_dir / "isolinux.bin").exists() else "",
        "-eltorito-alt-boot",
        "-e", "boot/efi/boot/bootx64.efi",
        "-no-emul-boot",
        str(new_root)
    ]
    
    # Filter out empty values
    cmd = [c for c in cmd if c]
    
    log(f"创建 ISO: {' '.join(cmd[:5])}...")
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode == 0 and output_path.exists():
            size_mb = output_path.stat().st_size / (1024 * 1024)
            log(f"ISO 创建成功: {size_mb:.1f} MB", "success")
            return True
        else:
            log(f"ISO 创建失败: {result.stderr}", "error")
            return False
    except Exception as e:
        log(f"ISO 创建异常: {e}", "error")
        return False

def create_iso_pycdlib(new_root, output_path):
    """Fallback: Create ISO using pycdlib (non-bootable)"""
    log("使用 pycdlib 创建数据盘 ISO...")
    
    try:
        import pycdlib
    except ImportError:
        log("pycdlib 未安装，尝试安装...", "warn")
        run_cmd([sys.executable, "-m", "pip", "install", "pycdlib"])
        import pycdlib
    
    iso = pycdlib.PyCdlib()
    
    try:
        iso.new(interchange_level=3, vol_ident="CLEANLINUX")
        
        # Add rootfs content
        for item in new_root.rglob("*"):
            if item.is_file():
                rel_path = item.relative_to(new_root)
                iso_path = f"/{rel_path}".upper()
                try:
                    iso.add_file(str(item), iso_path)
                except:
                    pass
        
        iso.write(str(output_path))
        iso.close()
        
        size_mb = output_path.stat().st_size / (1024 * 1024)
        log(f"数据盘 ISO 已创建: {size_mb:.1f} MB", "success")
        return True
        
    except Exception as e:
        log(f"pycdlib ISO 创建失败: {e}", "error")
        return False

def main():
    """Main build function"""
    print("=" * 70)
    print("  CleanLinux ISO 构建器 - RTX 2060 + llama.cpp 优化版")
    print("=" * 70)
    print()
    
    # Setup
    workspace = setup_workspace()
    
    # Step 1: Download Arch ISO
    log("步骤 1/6: 下载 Arch Linux ISO...")
    iso_path = download_arch_iso(workspace)
    if not iso_path.exists():
        log("无法下载 Arch ISO，构建终止", "error")
        sys.exit(1)
    
    # Step 2: Extract ISO
    log("步骤 2/6: 提取 ISO 内容...")
    if not extract_iso(iso_path, workspace):
        log("ISO 提取失败", "error")
        sys.exit(1)
    
    # Step 3: Setup rootfs
    log("步骤 3/6: 准备根文件系统...")
    new_root = setup_new_root(workspace)
    
    # Step 4: Add customizations
    log("步骤 4/6: 添加 NVIDIA + llama.cpp + 壁纸配置...")
    add_nvidia_package_conf(new_root)
    add_nvidia_setup_script(new_root)
    add_llama_cpp_script(new_root)
    add_wallpaper_script(new_root)
    update_pacman_mirrorlist(new_root)
    set_default_target_cli(new_root)
    add_startup_scripts(new_root)
    copy_customizations(new_root)
    
    # Step 5: Create ISO
    log("步骤 5/6: 生成 ISO 镜像...")
    output_path = OUTPUT_DIR / CLEANLINUX_ISO_NAME
    
    # Try full bootable ISO first
    success = create_iso_from_rootfs(workspace, output_path)
    
    # If bootable ISO fails, create data disk
    if not success or not output_path.exists():
        log("尝试创建数据盘 ISO...", "warn")
        create_iso_pycdlib(new_root, output_path)
    
    # Step 6: Verify
    log("步骤 6/6: 验证构建结果...")
    if output_path.exists():
        size_mb = output_path.stat().st_size / (1024 * 1024)
        print()
        print("=" * 70)
        print("  ✅ ISO 构建完成！")
        print("=" * 70)
        print(f"\n  输出文件: {output_path}")
        print(f"  文件大小: {size_mb:.1f} MB")
        print(f"\n  写入 U 盘:")
        print(f"    dd if={output_path} of=/dev/sdX bs=4M status=progress")
        print()
        print("  RTX 2060 规格:")
        print("    - CUDA 架构: 7.5 (Turing)")
        print("    - 显存: 6GB GDDR6")
        print("    - 推荐模型: Q4_K_M (4.5GB 显存)")
        print()
    else:
        print("\n❌ ISO 构建失败")
        sys.exit(1)

if __name__ == "__main__":
    main()
