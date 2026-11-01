#!/bin/bash
# GitHub 配置脚本

echo "╔═══════════════════════════════════════════════════════════╗"
echo "║              GitHub 配置向导                               ║"
echo "╚═══════════════════════════════════════════════════════════╝"
echo ""

# 检查 gh 是否安装
if ! command -v gh &>/dev/null; then
    echo "❌ gh CLI 未安装"
    echo ""
    echo "请先安装 gh CLI:"
    echo "  1. 访问 https://github.com/cli/cli/releases/tag/v2.42.1"
    echo "  2. 下载 'gh_2.42.1_macOS_pkg.tar.gz'"
    echo "  3. 解压: tar -xzf gh_2.42.1_macOS_pkg.tar.gz"
    echo "  4. 安装: sudo installer -pkg gh_2.42.1_macOS.pkg -target /"
    echo "  5. 验证: gh --version"
    echo ""
    exit 1
fi

# 检查是否已登录
if gh auth status 2>/dev/null | grep -q "Logged in"; then
    echo "✅ 已登录到 GitHub"
    gh auth status
    exit 0
fi

echo "❌ 未登录 GitHub"
echo ""
echo "请选择登录方式:"
echo "  1. 浏览器登录（推荐）"
echo "  2. 命令行登录"
echo ""
read -p "请选择 (1-2): " choice

case $choice in
    1)
        echo ""
        echo "正在启动浏览器登录..."
        gh auth login --hostname github.com --web
        ;;
    2)
        echo ""
        echo "正在启动命令行登录..."
        gh auth login --hostname github.com --git-protocol https
        ;;
    *)
        echo "无效选择"
        exit 1
        ;;
esac

echo ""
echo "验证登录状态..."
gh auth status
