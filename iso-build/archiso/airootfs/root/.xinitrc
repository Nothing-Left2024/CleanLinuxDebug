#!/bin/sh
# CleanLinux X11 会话
# 壁纸层: mpv 全屏视频壁纸（无 .mp4 时用 feh 静态壁纸兜底）
# 特效层: picom 液态玻璃 / 窗口层: openbox + tint2
cmdline="$(cat /proc/cmdline 2>/dev/null)"
INSTALLER=0
case "$cmdline" in *cleanlinux_session=installer*) INSTALLER=1 ;; esac
[ "${CLEANLINUX_INSTALLER}" = "1" ] && INSTALLER=1

WALL="/usr/share/wallpapers"

# ── 壁纸层 ──
VIDEO="$(ls "$WALL"/*.mp4 2>/dev/null | head -1)"
if [ -n "$VIDEO" ]; then
    # 视频动态壁纸: mpv 全屏作为底层窗口（~40MB 内存）
    mpv --no-border --no-osc --no-osd-bar --loop --volume=0 --fullscreen \
        "$VIDEO" &
elif ls "$WALL"/*.png >/dev/null 2>&1; then
    # 静态壁纸兜底（feh 幻灯片 15s 切换，~5MB 内存）
    feh --bg-scale --slideshow --slideshow-delay 15 --loop \
        $(ls "$WALL"/*.png 2>/dev/null) &
fi

# ── 液态玻璃合成器（macOS 磨砂效果）──
picom --config /etc/picom/cleanlinux.conf &

# ── 窗口管理器 + 面板 ──
openbox &
sleep 1
tint2 -c /etc/tint2/cleanlinux.rc &

# ── 安装器会话：桌面就绪后自动弹出图形安装器 ──
if [ "$INSTALLER" = "1" ]; then
    ( sleep 4
      # 官方安装器 archinstall（运行在图形桌面的终端窗口中）
      alacritty --title "CleanLinux 图形化安装" -e /bin/sh -c 'archinstall; read -p "安装完成，按回车关闭窗口..." ' &
    ) &
fi

wait
