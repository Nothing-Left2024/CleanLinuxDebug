# CleanLinux ISO Profile Configuration
# Arch Linux + NVIDIA + llama.cpp + Dynamic Wallpaper
PROFILE_NAME="CleanLinux"
PROFILE_PRESET="cleanlinux"
ISO_LABEL="CLEANLINUX"
ISO_TYPES="hybrid"
ARCH="x86_64"
PACKAGES=("base" "linux" "linux-firmware" "intel-ucode" "networkmanager" "dhcpcd" "vim" "bash-completion" "git" "wget" "curl" "neovim" "less" "htop" "procps-ng" "pciutils" "usbutils" "lm_sensors" "inxi" "sysstat" "lsof" "net-tools" "iproute2" "iputils" "wireless_tools" "wpa_supplicant" "dialog" "mtdev" "libwacom" "xf86-input-libinput" "xorg-server" "xorg-xinit" "xorg-apps" "xorg-utils" "xorg-setxkbmap" "xdg-utils" "fontawesome-free" "nerd-fonts" "power-profiles-daemon")
HOOKS=("base" "encrypt" "udev" " autodetect" "modconf" "kms" "keymap" "consolefont" "overlay" "smartcard" "network" "networkdropbear" "sshcreds" "fsck" "shutdown" "resumeswap" "keyboard" "fsck")
