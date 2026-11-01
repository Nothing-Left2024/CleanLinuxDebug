#!/bin/bash
# CleanLinux X11 Startup Script
# Starts: mpv wallpaper -> picom -> dwm

# Kill any existing processes
pkill -f "mpv.*root" 2>/dev/null || true
pkill picom 2>/dev/null || true

# Start dynamic wallpaper (if video exists)
WALLPAPER_VIDEO="/usr/share/wallpapers/default.mp4"
if [ -f "$WALLPAPER_VIDEO" ]; then
    mpv --no-border --no-osc --no-osd-bar \
        --ontop --geometry=100%x100% \
        --force-window --wid=root \
        --loop --volume=0 "$WALLPAPER_VIDEO" &
fi

# Start picom (液态玻璃效果)
picom --config ~/.config/picom/picom.conf &

# Start dwm
exec dwm
