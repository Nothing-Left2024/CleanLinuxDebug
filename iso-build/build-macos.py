#!/usr/bin/env python3
"""
CleanLinux ISO Generator for macOS
Uses pycdlib to create an Arch Linux-based ISO with customizations
"""

import os
import sys
import shutil
import re
from pathlib import Path

try:
    import pycdlib
except ImportError:
    print("请安装 pycdlib: pip3 install pycdlib")
    sys.exit(1)

# ── Configuration ──
BASE_DIR = Path(__file__).parent
OUTPUT_DIR = BASE_DIR / "output"
ISO_NAME = "CleanLinux-x86_64.iso"
ISO_PATH = OUTPUT_DIR / ISO_NAME

def iso_filename(name):
    """Convert filename to ISO9660 compatible format (A-Z, 0-9, _)"""
    base = Path(name).stem.upper()
    ext = Path(name).suffix.upper()
    base = re.sub(r'[^A-Z0-9]', '_', base)
    ext = re.sub(r'[^A-Z0-9]', '_', ext)
    return f"{base}{ext}" if ext else base

def iso_path(path_str):
    """Convert path to ISO9660 compatible format"""
    parts = []
    for part in Path(path_str).parts:
        parts.append(iso_filename(part))
    return "/" + "/".join(parts)

def walk_and_add(iso, source_path, iso_prefix):
    """Add a single file or directory to ISO"""
    source_path = Path(source_path)
    if source_path.is_file():
        iso_path_str = iso_path(f"{iso_prefix}/{source_path.name}")
        iso.add_file(str(source_path), iso_path_str)
    elif source_path.is_dir():
        for item in sorted(source_path.rglob("*")):
            if item.is_file():
                rel_path = item.relative_to(source_path)
                iso_path_str = iso_path(f"{iso_prefix}/{rel_path}")
                try:
                    iso.add_file(str(item), iso_path_str)
                except Exception as e:
                    print(f"  ⚠ 跳过 {iso_path_str}: {e}")

def main():
    print("=" * 60)
    print("CleanLinux ISO 构建器 (macOS 版本)")
    print("=" * 60)
    
    # Ensure output directory
    OUTPUT_DIR.mkdir(exist_ok=True)
    
    print("\n[1/3] 检查依赖...")
    print("  ✓ pycdlib 已安装")
    
    print("\n[2/3] 准备 ISO 内容...")
    
    # Create temporary ISO directory structure
    iso_root = OUTPUT_DIR / "iso_content"
    if iso_root.exists():
        shutil.rmtree(iso_root)
    iso_root.mkdir()
    
    # Copy rootfs-overlay content
    rootfs_dir = BASE_DIR / "rootfs-overlay"
    if rootfs_dir.exists():
        dest = iso_root / "rootfs"
        shutil.copytree(rootfs_dir, dest)
        print(f"  ✓ 已复制 rootfs-overlay 内容")
    
    # Copy documentation
    docs_dir = BASE_DIR.parent / "docs"
    if docs_dir.exists():
        dest = iso_root / "docs"
        shutil.copytree(docs_dir, dest)
        print(f"  ✓ 已复制文档")
    
    # Copy scripts
    scripts_dest = iso_root / "scripts"
    scripts_dest.mkdir()
    for script in BASE_DIR.glob("*.sh"):
        shutil.copy2(script, scripts_dest / script.name)
    print(f"  ✓ 已复制构建脚本")
    
    # Create ISO file system info
    iso_info = iso_root / "ISO-INFO.txt"
    iso_info.write_text("""CleanLinux ISO Information
==========================
Version: 1.0
Build Date: 2026-11-01
Architecture: x86_64
Base: Arch Linux (rolling)

Features:
- NVIDIA proprietary driver pre-installed
- llama.cpp with CUDA support
- picom compositor with frosted glass effects
- mpv dynamic wallpaper
- dwm window manager
- CLI default boot (~100MB RAM)

Chinese Mirrors:
- TUNA (Tsinghua)
- USTC
- Aliyun
- HIT
- JLU
- SJTU
""")
    
    print("\n[3/3] 生成 ISO 镜像...")
    
    iso = pycdlib.PyCdlib()
    try:
        iso.new(
            interchange_level=3,
            sys_ident="CLEANLINUX",
            vol_ident="CLEANLINUX",
            pub_ident_str="CleanLinux",
            preparer_ident_str="Arch Linux Custom Build",
            app_ident_str="CleanLinux ISO Generator",
            joliet=3
        )
        
        # Add files recursively (pycdlib will auto-create directories)
        walk_and_add(iso, iso_root / "ISO-INFO.txt", "/")
        walk_and_add(iso, iso_root / "rootfs", "/ROOTFS")
        walk_and_add(iso, iso_root / "docs", "/DOCS")
        walk_and_add(iso, scripts_dest, "/SCRIPTS")
        
        # Write ISO
        iso.write(str(ISO_PATH))
        iso.close()
        
        file_size = ISO_PATH.stat().st_size / (1024 * 1024)
        print(f"  ✓ ISO 已生成: {ISO_PATH}")
        print(f"  ✓ 文件大小: {file_size:.2f} MB")
        
    except Exception as e:
        print(f"  ✗ 构建失败: {e}")
        import traceback
        traceback.print_exc()
        raise
    finally:
        iso.close()
        # Cleanup temp directory
        if iso_root.exists():
            shutil.rmtree(iso_root)
    
    print("\n" + "=" * 60)
    print("✅ ISO 构建完成！")
    print("=" * 60)
    print(f"\n输出文件: {ISO_PATH}")
    print(f"\n使用方法:")
    print(f"  1. 在 Linux 机器上运行 build-iso.sh 获取完整可启动 ISO")
    print(f"  2. 写入 U 盘: dd if={ISO_PATH} of=/dev/sdX bs=4M status=progress")
    print(f"  3. 或使用 balenaEtcher 写入")
    print(f"\n⚠ 注意: 此 ISO 为数据盘，需要在 Linux 环境下配合 archiso 使用")
    print(f"   完整可启动 ISO 请在装有 archiso 的 Linux 机器上运行:")
    print(f"   sudo bash /path/to/iso-build/build-iso.sh")

if __name__ == "__main__":
    main()
