# CleanLinux: zsh 下同样自动显示菜单
case "$(cat /proc/cmdline 2>/dev/null)" in
  *cleanlinux_session=text*) /usr/local/bin/cleanlinux-menu ;;
esac
