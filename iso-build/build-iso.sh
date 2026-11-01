#!/bin/bash
#=============================================================================
# CleanLinux ISO Build Script
# Requires: archiso package (pacman -S archiso)
# Run: sudo bash build-iso.sh
#=============================================================================
set -euo pipefail

BUILD_DIR="/tmp/cleanlinux-build"
OUTPUT_DIR="$(dirname "$0")/output"
ISO_NAME="CleanLinux-x86_64.iso"

echo "==> [1/3] 清理旧构建..."
rm -rf "$BUILD_DIR"
mkdir -p "$BUILD_DIR" "$OUTPUT_DIR"

echo "==> [2/3] 复制配置文件..."
cp -r "$(dirname "$0")/config"/* "$BUILD_DIR/"
cp -r "$(dirname "$0")/packages" "$BUILD_DIR/"
cp -r "$(dirname "$0")/rootfs-overlay" "$BUILD_DIR/rootfs/"

echo "==> [3/3] 构建 ISO..."
cd "$BUILD_DIR"
mkarchiso -v workdir/

echo ""
echo "==> ✅ ISO 构建完成！"
echo "==> 输出文件: $OUTPUT_DIR/$ISO_NAME"
echo "==> 文件大小: $(du -h "$OUTPUT_DIR/$ISO_NAME" | cut -f1)"
echo ""
echo "==> 使用方法:"
echo "    1. 写入 U 盘: dd if=$OUTPUT_DIR/$ISO_NAME of=/dev/sdX bs=4M status=progress"
echo "    2. 或直接双刻启动进入 Live 环境运行 setup 脚本"
