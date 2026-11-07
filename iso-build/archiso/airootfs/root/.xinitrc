#!/bin/sh
# CleanLinux X11 会话
# 壁纸层: mpv 视频壁纸 (无 .mp4 时 xwallpaper 静态+轮播)
# 特效层: picom 液态玻璃 / HUD: conky / 窗口层: openbox + tint2
# 组件开关读取 /etc/cleanlinux/features.conf（cleanlinux-features 管理）
cmdline="$(cat /proc/cmdline 2>/dev/null)"
INSTALLER=0
case "$cmdline" in *cleanlinux_session=installer*) INSTALLER=1 ;; esac
[ "${CLEANLINUX_INSTALLER}" = "1" ] && INSTALLER=1

# ── 终端可用性探测（最先执行, 此时根窗口还是黑的, 闪烁不可见）──
# alacritty 需要 OpenGL 3.3, 虚拟机无 3D 加速时自动回退 xterm
if [ ! -r /run/cleanlinux-term ]; then
    if command -v alacritty >/dev/null 2>&1; then
        alacritty -e sleep 3 >/dev/null 2>&1 &
        TP=$!
        sleep 1
        if kill -0 "$TP" 2>/dev/null; then
            echo alacritty > /run/cleanlinux-term
        else
            echo xterm > /run/cleanlinux-term
        fi
        kill "$TP" 2>/dev/null
        wait "$TP" 2>/dev/null
    else
        echo xterm > /run/cleanlinux-term
    fi
fi

# ── 功能配置（默认值, features.conf 可覆盖）──
WALLPAPER=on
BLUR_STRENGTH=12
TASKBAR=on
CONKY=on
[ -r /etc/cleanlinux/features.conf ] && . /etc/cleanlinux/features.conf

# ── 壁纸层 (wallpaper 脚本统一管理 mpv/xwallpaper) ──
if [ "$WALLPAPER" = "on" ]; then
    /usr/local/bin/wallpaper start >/dev/null 2>&1 &
fi

# ── 液态玻璃合成器（强度 0 = 关闭; glx 失败自动回退 xrender 兼容虚拟机）──
if [ "$BLUR_STRENGTH" -gt 0 ] 2>/dev/null; then
    picom --config /etc/picom/cleanlinux.conf >/dev/null 2>&1 &
    sleep 1
    pgrep -x picom >/dev/null || picom --backend xrender --config /etc/picom/cleanlinux.conf >/dev/null 2>&1 &
fi

# ── 窗口管理器 ──
openbox &
sleep 1

# ── 液态玻璃 HUD 仪表盘 (~2MB) ──
if [ "$CONKY" = "on" ]; then
    conky -c /etc/conky/cleanlinux.conf >/dev/null 2>&1 &
fi

# ── 任务栏 ──
if [ "$TASKBAR" = "on" ]; then
    tint2 -c /etc/tint2/cleanlinux.rc >/dev/null 2>&1 &
fi

# ── 安装器会话：桌面就绪后自动弹出图形安装器 ──
if [ "$INSTALLER" = "1" ]; then
    ( sleep 3
      /usr/local/bin/cleanlinux-terminal "CleanLinux 图形化安装" "archinstall" &
    ) &
fi

wait
