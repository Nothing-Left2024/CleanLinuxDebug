# CleanLinux: 命令行模式下自动显示系统菜单
cmdline="$(cat /proc/cmdline 2>/dev/null)"
case "$cmdline" in
  *cleanlinux_session=text*)
    if [ -z "$CLEANLINUX_MENU" ] && [ -x /usr/local/bin/cleanlinux-menu ]; then
      case $- in
        *i*) CLEANLINUX_MENU=1; /usr/local/bin/cleanlinux-menu ;;
      esac
    fi
    ;;
esac
