#!/usr/bin/env bash

iso_name="CleanLinux"
iso_label="CLEANLINUX_$(date +%Y%m)"
iso_publisher="CleanLinux <cleanlinux@example.com>"
iso_application="CleanLinux Live/Install (NVIDIA + llama.cpp)"
iso_version="2026.11.07-r2"
install_dir="cleanlinux"
bootmodes=('bios.syslinux'
           'uefi.systemd-boot')
pacman_conf="pacman.conf"
airootfs_image_type="squashfs"
airootfs_image_tool_options=('-comp' 'xz' '-Xbcj' 'x86,arm64' '-b' '1M' '-Xdict-size' '1M')
file_permissions=(
  ["/etc/shadow"]="0:0:400"
  ["/root"]="0:0:750"
  ["/usr/local/bin/cleanlinux-menu"]="0:0:755"
  ["/usr/local/bin/cleanlinux-gui-start"]="0:0:755"
  ["/usr/local/bin/cleanlinux-gui"]="0:0:755"
  ["/usr/local/bin/cleanlinux-features"]="0:0:755"
  ["/usr/local/bin/cleanlinux-features-cli"]="0:0:755"
  ["/usr/local/bin/cleanlinux-monitor"]="0:0:755"
  ["/usr/local/bin/cleanlinux-monitor-cli"]="0:0:755"
  ["/usr/local/bin/cleanlinux-gpu"]="0:0:755"
  ["/usr/local/bin/cleanlinux-panel-status"]="0:0:755"
  ["/usr/local/bin/install-nvidia"]="0:0:755"
  ["/usr/local/bin/install-llama-cpp"]="0:0:755"
  ["/usr/local/bin/wallpaper"]="0:0:755"
)
