#!/bin/sh
# CleanLinux 功能编辑器后端库 — 纯逻辑，无 UI
# 前端: cleanlinux-features (yad) / cleanlinux-features-cli (dialog)
# 设计约束: 不依赖 Python（本工具链可能卸载 Python 释放内存）

CONF_DIR="/etc/cleanlinux"
CONF="$CONF_DIR/features.conf"
PICOM_CONF="/etc/picom/cleanlinux.conf"

# ── 配置读写 ─────────────────────────────────────────────

load_conf() {
    WALLPAPER=on
    BLUR_STRENGTH=12
    TASKBAR=on
    CONKY=on
    ZRAM=on
    NVIDIA_PERSISTENCE=off
    [ -r "$CONF" ] && . "$CONF"
    # 净化: 强度必须为 0-20 的整数
    case "$BLUR_STRENGTH" in ''|*[!0-9]*) BLUR_STRENGTH=12 ;; esac
    [ "$BLUR_STRENGTH" -gt 20 ] 2>/dev/null && BLUR_STRENGTH=20
}

save_conf() {
    mkdir -p "$CONF_DIR"
    {
        echo "# CleanLinux 功能配置（cleanlinux-features 自动生成）"
        echo "WALLPAPER=$WALLPAPER"
        echo "BLUR_STRENGTH=$BLUR_STRENGTH"
        echo "TASKBAR=$TASKBAR"
        echo "CONKY=$CONKY"
        echo "ZRAM=$ZRAM"
        echo "NVIDIA_PERSISTENCE=$NVIDIA_PERSISTENCE"
    } > "$CONF.tmp" && mv "$CONF.tmp" "$CONF"
}

# ── 内存统计 ─────────────────────────────────────────────

# 进程组实际 RSS (MB)
rss_mb() {
    ps -o rss= -C "$1" 2>/dev/null | awk '{s+=$1} END{printf "%d", (s+512)/1024}'
}

mem_avail_mb() { free -m | awk '/^Mem:/{print $7}'; }
mem_total_mb() { free -m | awk '/^Mem:/{print $2}'; }

# 桌面组件内存占用汇总（一行）
desktop_mem_line() {
    W=$(rss_mb mpv); P=$(rss_mb picom); T=$(rss_mb tint2)
    printf "壁纸mpv=%sMB 毛玻璃picom=%sMB 任务栏tint2=%sMB" "$W" "$P" "$T"
}

# ── 系统服务开关 ─────────────────────────────────────────

svc_state()   { systemctl is-enabled "$1" 2>/dev/null; }
svc_toggle()  {  # $1=unit $2=on|off
    if [ "$2" = "on" ]; then
        systemctl unmask "$1" 2>/dev/null
        systemctl enable --now "$1" 2>/dev/null
    else
        systemctl disable --now "$1" 2>/dev/null
    fi
}

# 额外终端 tty2-6: mask 阻止 getty.target 动态拉起
getty_state() {
    if systemctl is-enabled getty@tty2 >/dev/null 2>&1; then echo enabled; else echo disabled; fi
}
getty_toggle() {
    i=2
    while [ $i -le 6 ]; do
        if [ "$1" = "on" ]; then
            systemctl unmask "getty@tty$i" 2>/dev/null
            systemctl start  "getty@tty$i" 2>/dev/null
        else
            systemctl mask --now "getty@tty$i" 2>/dev/null
        fi
        i=$((i + 1))
    done
}

# ── 桌面组件实时应用 ─────────────────────────────────────

apply_desktop_live() {
    [ -z "$DISPLAY" ] && return 0   # CLI 模式不碰桌面
    # 壁纸
    if [ "$WALLPAPER" = "on" ]; then
        pgrep -x mpv >/dev/null || /usr/local/bin/wallpaper start >/dev/null 2>&1
    else
        /usr/local/bin/wallpaper stop >/dev/null 2>&1
    fi
    # 毛玻璃（强度 0 = 关闭合成器）
    if [ "$BLUR_STRENGTH" -gt 0 ] 2>/dev/null; then
        sed -i "s/^  strength = .*/  strength = $BLUR_STRENGTH/" "$PICOM_CONF" 2>/dev/null
        pgrep -x picom >/dev/null || picom --config "$PICOM_CONF" >/dev/null 2>&1 &
    else
        pkill -x picom 2>/dev/null
    fi
    # 任务栏
    if [ "$TASKBAR" = "on" ]; then
        pgrep -x tint2 >/dev/null || tint2 -c /etc/tint2/cleanlinux.rc >/dev/null 2>&1 &
    else
        pkill -x tint2 2>/dev/null
    fi
    # HUD 仪表盘
    if [ "$CONKY" = "on" ]; then
        pgrep -x conky >/dev/null || conky -c /etc/conky/cleanlinux.conf >/dev/null 2>&1 &
    else
        pkill -x conky 2>/dev/null
    fi
    return 0
}

# ── AI / 性能 ────────────────────────────────────────────

zram_on() {
    swapon --show=NAME 2>/dev/null | grep -q zram0 && return 0
    modprobe zram 2>/dev/null || return 1
    TOTAL_KB=$(awk '/^MemTotal:/{print $2}' /proc/meminfo)
    echo $((TOTAL_KB * 1024 / 2)) > /sys/block/zram0/disksize 2>/dev/null || return 1
    mkswap /dev/zram0 >/dev/null 2>&1
    swapon -p 100 /dev/zram0 2>/dev/null
}

zram_off() { swapoff /dev/zram0 2>/dev/null; }
zram_state() { swapon --show=NAME 2>/dev/null | grep -q zram0 && echo on || echo off; }

nvidia_persist() {  # $1=on|off
    nvidia-smi -pm "$([ "$1" = on ] && echo 1 || echo 0)" >/dev/null 2>&1
}

# ── 极致模式 ─────────────────────────────────────────────

extreme_on() {
    # 记录释放前内存
    BEFORE=$(mem_avail_mb)
    WALLPAPER=off
    BLUR_STRENGTH=0
    TASKBAR=off
    CONKY=off
    save_conf
    apply_desktop_live
    AFTER=$(mem_avail_mb)
    printf "%d" $((AFTER - BEFORE))
}

# ── Python 卸载/恢复（UI 层负责警告）─────────────────────

python_remove()  { pacman -Rdd --noconfirm python >/dev/null 2>&1; }
python_restore() { pacman -S --noconfirm python >/dev/null 2>&1; }
python_state()   { command -v python >/dev/null 2>&1 && echo on || echo off; }
