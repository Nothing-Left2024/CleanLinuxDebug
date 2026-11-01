#!/bin/bash
#=============================================================================
# CleanLinux Setup Script
# Runs automatically on first boot from the Live ISO
# Configures: NVIDIA driver, llama.cpp, dynamic wallpaper, desktop environment
#=============================================================================
set -euo pipefail

# ── Colors ──
RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'; CYAN='\033[0;36m'; NC='\033[0m'
printf "${CYAN}╔══════════════════════════════════════════════╗${NC}\n"
printf "${CYAN}║    CleanLinux 初始化设置向导                 ║${NC}\n"
printf "${CYAN}║    Arch Linux + NVIDIA + llama.cpp          ║${NC}\n"
printf "${CYAN}╚══════════════════════════════════════════════╝${NC}\n\n"

# ── 1. Configure Chinese Mirrors ──
printf "${GREEN}[1/6]${NC} 配置国内镜像源...\n"
tee /etc/pacman.d/mirrorlist > /dev/null << 'MIRROR_EOF'
Server = https://mirrors.tuna.tsinghua.edu.cn/archlinux/$repo/os/$arch
Server = https://mirrors.ustc.edu.cn/archlinux/$repo/os/$arch
Server = https://mirrors.aliyun.com/archlinux/$repo/os/$arch
Server = https://mirrors.hit.edu.cn/archlinux/$repo/os/$arch
Server = https://mirrors.jlu.edu.cn/archlinux/$repo/os/$arch
Server = https://mirror.sjtu.edu.cn/archlinux/$repo/os/$arch
MIRROR_EOF

# ── 2. Update System ──
printf "${GREEN}[2/6]${NC} 更新系统...\n"
pacman -Syu --noconfirm 2>/dev/null || pacman -Syu

# ── 3. Install NVIDIA Driver ──
printf "${GREEN}[3/6]${NC} 安装 NVIDIA 专有驱动...\n"
pacman -S --noconfirm nvidia nvidia-utils opencl-nvidia nvidia-settings
cat > /etc/modprobe.d/nvidia.conf << 'NVIDIA_EOF'
options nvidia_drm modeset=1 fbdev=1
NVIDIA_EOF
echo "nvidia_drm" > /etc/modules-load.d/nvidia.conf

# ── 4. Install Desktop Environment (minimal) ──
printf "${GREEN}[4/6]${NC} 安装轻量桌面环境...\n"
pacman -S --noconfirm xorg-server xorg-xinit xorg-apps dwm dmenu st alacritty picom mesa neovim bat less git curl wget firefox chromium mpv wmname --needed

# ── 5. Install llama.cpp (CUDA) ──
printf "${GREEN}[5/6]${NC} 编译安装 llama.cpp (CUDA 加速)...\n"
pacman -S --noconfirm git cmake gcc make cuda cuda-compat-lib --needed
if [ ! -d /opt/llama.cpp ]; then
    git clone --depth=1 https://github.com/ggerganov/llama.cpp.git /opt/llama.cpp
    cd /opt/llama.cpp
    cmake -S . -B build -DGGML_CUDA=ON -DCMAKE_BUILD_TYPE=Release -DGGML_CUDA_FORCE_MMQ=OFF
    cmake --build build --config Release -j$(nproc)
    cmake --install build
fi
ln -sf /opt/llama.cpp/build/bin/llama-cli /usr/local/bin/llama-cli
ln -sf /opt/llama.cpp/build/bin/llama-server /usr/local/bin/llama-server

# ── 6. Configure Dynamic Wallpaper ──
printf "${GREEN}[6/6]${NC} 配置动态壁纸与液态玻璃效果...\n"
mkdir -p /root/.config/mpv /root/.config/picom /usr/local/bin

cat > /usr/local/bin/wallpaper-mpv << 'WALL_EOF'
#!/bin/bash
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
mpv --no-border --no-osc --no-osd-bar \
    --ontop --geometry=100%x100% \
    --force-window --wid=root \
    --loop --volume=0 "$VIDEO_PATH" &
echo "Dynamic wallpaper started."
WALL_EOF
chmod +x /usr/local/bin/wallpaper-mpv

cat > /usr/local/bin/wallpaper-toggle << 'TOG_EOF'
#!/bin/bash
if pgrep -f "mpv.*root" > /dev/null; then
    pkill -f "mpv.*root"
    echo "Dynamic wallpaper stopped"
else
    /usr/local/bin/wallpaper-mpv "$1"
    echo "Dynamic wallpaper started"
fi
TOG_EOF
chmod +x /usr/local/bin/wallpaper-toggle

cat > /root/.config/picom/picom.conf << 'PICOM_EOF'
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
PICOM_EOF

# ── Set default target to multi-user (CLI) ──
systemctl set-default multi-user.target 2>/dev/null || true

# ── Enable services ──
systemctl enable nvidia-power.service 2>/dev/null || true
systemctl enable NetworkManager 2>/dev/null || true

echo ""
printf "${GREEN}✅ CleanLinux 初始化完成！${NC}\n"
printf "${YELLOW}提示：输入 'startx' 启动图形桌面，输入 'wallpaper' 切换动态壁纸${NC}\n"
