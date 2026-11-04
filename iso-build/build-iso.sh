#!/bin/bash
#=============================================================================
# CleanLinux ISO 构建脚本（新版 archiso 布局）
# 支持三种构建方式:
#   1. 本地已装 archiso: 直接 mkarchiso
#   2. Docker 容器构建:  archlinux:latest 容器内执行 (GitHub Actions 用)
#   3. 提示安装
# 用法: sudo bash build-iso.sh [docker]
#=============================================================================
set -euo pipefail

BASE_DIR="$(cd "$(dirname "$0")" && pwd)"
PROFILE="${BASE_DIR}/archiso"
WORK_DIR="${BASE_DIR}/work"
OUT_DIR="${BASE_DIR}/output"
USE_DOCKER="${1:-auto}"

need_deps() { command -v mkarchiso && command -v mtools && command -v xorriso && command -v squashfs-tools && echo ok; }

if [ "$USE_DOCKER" = "docker" ] || { [ "$USE_DOCKER" = "auto" ] && ! need_deps >/dev/null 2>&1; }; then
    if ! command -v docker >/dev/null; then
        echo "❌ 无 Docker 也无 archiso，无法构建"
        exit 1
    fi
    echo "==> 使用 Docker (archlinux:latest) 构建..."
    rm -rf "$WORK_DIR"
    mkdir -p "$WORK_DIR" "$OUT_DIR"
    docker run --rm \
        -v "${BASE_DIR}/archiso:/src:ro" \
        -v "${WORK_DIR}:/root/work" \
        -v "${OUT_DIR}:/root/out" \
        archlinux:latest \
        /bin/bash -e -c "
            echo '==> 安装 archiso 及构建依赖 (国内镜像源) ...'
            pacman -Sy --noconfirm --needed base-devel git xorriso mtools squashfs-tools archiso
            echo '==> 运行 mkarchiso ...'
            mkarchiso -v -w /root/work -o /root/out /src
        "
    echo "==> ✅ ISO 构建完成: ${OUT_DIR}/"
    ls -lh "$OUT_DIR"
    exit 0
fi

# 本地 archiso 构建
echo "==> 使用本地 archiso 构建..."
rm -rf "$WORK_DIR"
mkdir -p "$WORK_DIR" "$OUT_DIR"
sudo mkarchiso -v -w "$WORK_DIR" -o "$OUT_DIR" "$PROFILE"
echo "==> ✅ ISO 构建完成: ${OUT_DIR}/"
