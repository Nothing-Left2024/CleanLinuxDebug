#!/usr/bin/env python3
"""Generate the Arch Linux NVIDIA + llama.cpp + Wallpaper optimization document."""

from docx import Document
from docx.shared import Inches, Pt, RGBColor, Cm
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.oxml.ns import qn
from docx.oxml import OxmlElement

doc = Document()

# ── style tweaks ────────────────────────────────────────────────────────────
style = doc.styles['Normal']
style.font.name = 'JetBrains Mono'
style.font.size = Pt(10)
try:
    style.element.rPr.get_or_add_rFonts().set(qn('w:eastAsia'), 'PingFang SC')
except Exception:
    pass

for level in range(1, 4):
    hs = doc.styles[f'Heading {level}']
    hs.font.name = 'SF Pro Display'
    hs.font.size = Pt(14 if level == 1 else 12 if level == 2 else 11)
    hs.font.bold = True
    hs.font.color.rgb = RGBColor(0x1D, 0x1D, 0x1F)
    try:
        hs.element.rPr.get_or_add_rFonts().set(qn('w:eastAsia'), 'PingFang SC')
    except Exception:
        pass

def add_code(doc, code_text):
    p = doc.add_paragraph()
    p.paragraph_format.left_indent = Cm(0.5)
    p.paragraph_format.space_before = Pt(2)
    p.paragraph_format.space_after = Pt(2)
    run = p.add_run(code_text)
    run.font.name = 'JetBrains Mono'
    run.font.size = Pt(9)
    run.font.color.rgb = RGBColor(0x36, 0x45, 0x4F)
    # light gray background
    pPr = p._element.get_or_add_pPr()
    shd = OxmlElement('w:shd')
    shd.set(qn('w:val'), 'clear')
    shd.set(qn('w:color'), 'auto')
    shd.set(qn('w:fill'), 'F5F5F5')
    pPr.append(shd)
    doc.add_paragraph()  # spacer

def add_info_box(doc, title, text):
    p = doc.add_paragraph()
    p.paragraph_format.left_indent = Cm(0.5)
    run = p.add_run(f'⚡ {title}  ')
    run.font.bold = True
    run.font.size = Pt(10)
    run.font.color.rgb = RGBColor(0x00, 0x7A, 0xCC)
    run2 = p.add_run(text)
    run2.font.size = Pt(10)
    run2.font.color.rgb = RGBColor(0x42, 0x42, 0x42)

def add_note_box(doc, title, text):
    p = doc.add_paragraph()
    p.paragraph_format.left_indent = Cm(0.5)
    run = p.add_run(f'📌 {title}  ')
    run.font.bold = True
    run.font.size = Pt(10)
    run.font.color.rgb = RGBColor(0xAA, 0x66, 0x00)
    run2 = p.add_run(text)
    run2.font.size = Pt(10)
    run2.font.color.rgb = RGBColor(0x42, 0x42, 0x42)

def set_run_font(run, bold=False, size=Pt(10), color=None, mono=False):
    run.font.bold = bold
    run.font.size = size
    if color:
        run.font.color.rgb = color
    if mono:
        run.font.name = 'JetBrains Mono'
    # East Asian font fallback (safe)
    try:
        rpr = run._element.get_or_add_rPr()
        if rpr is not None:
            rpr.rFonts.set(qn('w:eastAsia'), 'PingFang SC')
    except Exception:
        pass

# ══════════════════════════════════════════════════════════════════════════════
# TITLE PAGE
# ══════════════════════════════════════════════════════════════════════════════
title = doc.add_paragraph()
title.alignment = WD_ALIGN_PARAGRAPH.CENTER
run = title.add_run('Arch Linux 深度优化指南')
set_run_font(run, bold=True, size=Pt(28), color=RGBColor(0x1D, 0x1D, 0x1F))

sub = doc.add_paragraph()
sub.alignment = WD_ALIGN_PARAGRAPH.CENTER
run2 = sub.add_run('NVIDIA GPU · llama.cpp · 动态壁纸 · 液态玻璃桌面')
set_run_font(run2, size=Pt(14), color=RGBColor(0x6E, 0x6E, 0x73))

meta = doc.add_paragraph()
meta.alignment = WD_ALIGN_PARAGRAPH.CENTER
run3 = meta.add_run('\nVersion 1.0 · 2026-11-01\nArch Linux · x86_64\n')
set_run_font(run3, size=Pt(10), color=RGBColor(0x8E, 0x8E, 0x93))

doc.add_page_break()

# ══════════════════════════════════════════════════════════════════════════════
# TABLE OF CONTENTS
# ══════════════════════════════════════════════════════════════════════════════
doc.add_heading('目录', level=1)
toc_items = [
    ('1.', 'NVIDIA 显卡驱动优化'),
    ('   1.1', '驱动安装方案对比'),
    ('   1.2', 'Proprietary 驱动完整安装'),
    ('   1.3', 'NVIDIA NVML 性能监控'),
    ('   1.4', '功耗与散热调优'),
    ('2.', 'llama.cpp 本地推理优化'),
    ('   2.1', 'CUDA 加速编译'),
    ('   2.2', '模型量化与内存管理'),
    ('   2.3', '批量推理与批处理'),
    ('   2.4', '系统级资源隔离'),
    ('3.', '轻量级动态壁纸方案'),
    ('   3.1', '方案选型对比'),
    ('   3.2', 'mpv 动态壁纸配置（推荐）'),
    ('   3.3', '与 picom 液态玻璃效果的集成'),
    ('   3.4', '动态壁纸的电源管理'),
    ('4.', '开机流程与资源占用总览'),
    ('5.', '完整自动化安装脚本'),
]
for num, item in toc_items:
    p = doc.add_paragraph()
    p.paragraph_format.left_indent = Cm(0.3 if len(num) > 2 else 0.8)
    run = p.add_run(f'{num}  {item}')
    set_run_font(run, size=Pt(10.5), color=RGBColor(0x33, 0x33, 0x33))

doc.add_page_break()

# ══════════════════════════════════════════════════════════════════════════════
# CHAPTER 1: NVIDIA
# ══════════════════════════════════════════════════════════════════════════════
doc.add_heading('1. NVIDIA 显卡驱动优化', level=1)

doc.add_heading('1.1 驱动安装方案对比', level=2)
add_info_box(doc, '核心原则',
    'Arch Linux 提供两套主流 NVIDIA 驱动：开源 nouveau（性能差，不支持 CUDA）和专有驱动 nvidia（必须选择）。本机目标为本地推理，必须使用专有驱动。')

tbl = doc.add_table(rows=4, cols=5)
tbl.style = 'Light Grid Accent 1'
tbl.alignment = WD_TABLE_ALIGNMENT.CENTER
headers = ['方案', '包名', 'CUDA 支持', '性能', '推荐度']
data = [
    ['nouveau（开源）', 'xorg-server + nouveau', '❌ 无', '低', '❌ 不推荐'],
    ['nvidia（专有，LTS）', 'nvidia-lts + nvidia-utils', '✅ 稳定', '高', '✅ 生产首选'],
    ['nvidia（专有，最新）', 'nvidia + nvidia-utils', '✅ 最新', '最高', '✅ 日常推荐'],
]
hdr_cells = tbl.rows[0].cells
for i, h in enumerate(headers):
    hdr_cells[i].text = h
    for pp in hdr_cells[i].paragraphs:
        for r in pp.runs:
            r.font.bold = True
            r.font.size = Pt(9)
for ri, row_data in enumerate(data):
    row = tbl.rows[ri + 1].cells
    for ci, val in enumerate(row_data):
        row[ci].text = val
        for pp in row[ci].paragraphs:
            for r in pp.runs:
                r.font.size = Pt(9)

p = doc.add_paragraph()
p.paragraph_format.space_before = Pt(6)
run = p.add_run('说明：')
set_run_font(run, bold=True, size=Pt(10))
run2 = p.add_run('若使用 LTS 内核（服务器/稳定场景），选 nvidia-lts；日常办公推荐 nvidia（跟随滚动更新）。两者均搭配 nvidia-utils 提供 NVML 工具链。')
set_run_font(run2, size=Pt(10))

doc.add_heading('1.2 Proprietary 驱动完整安装', level=2)
add_code(doc, """
# ── 第一步：确认显卡型号与内核版本 ──
lspci -nnk | grep -A3 -i nvidia
uname -r

# ── 第二步：安装专有驱动（推荐方案） ──
# 方案A：跟随最新内核（日常办公）
sudo pacman -S nvidia nvidia-utils opencl-nvidia
# 方案B：使用 LTS 内核（生产环境）
sudo pacman -S nvidia-lts nvidia-utils opencl-nvidia

# ── 第三步：安装 PRIME 合成器（Optimus 双显卡笔记本必备） ──
sudo pacman -S nvidia-prime nvidia-settings

# ── 第四步：更新 initramfs 并启用服务 ──
sudo mkinitcpio -P
sudo systemctl enable nvidia-container.service  # Docker GPU 支持（可选）
""")

add_info_box(doc, '关键检查',
    '安装完成后运行 nvidia-smi，若显示 GPU 详情表格则驱动成功。确保 kernel modules 包含 nvidia_drm.modeset=1，写入 /etc/modprobe.d/nvidia.conf 以支持 Wayland 和透明效果。')

doc.add_heading('1.3 NVML 性能监控', level=2)
add_code(doc, """
# ── 安装 nvtop（任务管理器风格的 GPU 监控） ──
sudo pacman -S nvtop

# ── 启动实时监控 ──
nvtop

# ── llama.cpp 推理时的 GPU 利用率查看 ──
nvtop -i 0    # 仅监控 GPU 0
""")
add_note_box(doc, '性能观察指标',
    'llama.cpp 推理时关注：GPU Memory Used（显存占用）、SM Active（CUDA 核心利用率）、Memory Bandwidth（显存带宽）。理想状态 SM Active > 80%、显存占用 < 90%。')

doc.add_heading('1.4 功耗与散热调优', level=2)
add_code(doc, """
# ── 查询当前功耗状态 ──
nvidia-smi --query-gpu=power.draw,power.limit,temperature.gpu --format=csv

# ── 设置性能偏好模式（最大化推理吞吐） ──
sudo nvidia-smi -pm 1           # 启用持久化模式
sudo nvidia-smi -p 250          # 设置功耗上限（W），按需调整

# ── 设置时钟频率锁定（避免推理时频率波动） ──
sudo nvidia-smi -lgc 1800,1800  # 锁定最小/最大频率 MHz，视 GPU 型号调整

# ── 写入 systemd 服务开机自动配置 ──
sudo tee /etc/systemd/system/nvidia-power.service << 'EOF'
[Unit]
Description=NVIDIA Power & Clock Optimization
After=modules-load.service

[Service]
Type=oneshot
ExecStart=/usr/bin/nvidia-smi -pm 1
ExecStart=/usr/bin/nvidia-smi -lgc 1200,1800
RemainAfterExit=yes

[Install]
WantedBy=multi-user.target
EOF
sudo systemctl enable nvidia-power.service
""")

doc.add_page_break()

# ══════════════════════════════════════════════════════════════════════════════
# CHAPTER 2: llama.cpp
# ══════════════════════════════════════════════════════════════════════════════
doc.add_heading('2. llama.cpp 本地推理优化', level=1)

doc.add_heading('2.1 CUDA 加速编译', level=2)
add_info_box(doc, '编译策略',
    'llama.cpp 默认使用 CPU，需通过 CMake 开启 CUDA 后端才能利用 NVIDIA GPU 加速。编译参数直接影响显存占用和推理速度。')

add_code(doc, """
# ── 安装编译依赖 ──
sudo pacman -S git cmake gcc make cuda cuda-compat-lib

# ── 克隆源码 ──
git clone https://github.com/ggerganov/llama.cpp.git
cd llama.cpp

# ── CUDA 优化编译（推荐参数） ──
cmake -S . -B build \\
    -DGGML_CUDA=ON \\
    -DCMAKE_BUILD_TYPE=Release \\
    -DGGML_CUDA_FORCE_MMQ=OFF \\    # 禁用 legacy MMQ，使用 Tensor Core
    -DCMAKE_CUDA_ARCHITECTURES="80;89"  # 80=Ada, 89=Hopper，按实际 GPU 调整

cmake --build build --config Release -j$(nproc)
cmake --install build

# ── 验证 CUDA 加速生效 ──
./build/bin/llama-cli -h | grep -i cuda
# 或直接运行推理查看 GPU 日志
""")

add_note_box(doc, '架构代号对照',
    'Kepler 5.x / Maxwell 6.x / Pascal 6.1 / Volta 7.0 / Turing 7.5 / Ampere 8.0 / Ada 8.9 / Hopper 9.0。在 CUDA_ARCHITECTURES 中填写对应数值，多架构用分号分隔。')

doc.add_heading('2.2 模型量化与内存管理', level=2)
add_code(doc, """
# ── 模型下载（以 Q4_K_M 量化为例，质量与速度最佳平衡） ──
# 推荐模型：Meta-Llama-3-8B-Instruct / Qwen2.5-7B-Instruct
wget https://huggingface.co/bartowski/Meta-Llama-3-8B-Instruct-GGUF/resolve/main/Meta-Llama-3-8B-Instruct-Q4_K_M.gguf

# ── GGUF 量化等级速查 ──
# Q4_K_M  → 4.5 GB 显存（推荐，质量损失极小）
# Q5_K_M  → 5.5 GB 显存（高质量，速度略降）
# Q8_0    → 9+ GB 显存（近无损，显存充裕时用）
# IQ4_XS  → 3.5 GB 显存（极致压缩，质量中等）

# ── 推理命令（GPU 加速 + 内存优化） ──
./build/bin/llama-cli \\
    -m Meta-Llama-3-8B-Instruct-Q4_K_M.gguf \\
    -ngl 35 \\              # 全部层推送到 GPU（8B 模型约 33-35 层）
    -t 4 \\                 # 线程数 = CPU 核心/2，避免抢占 GPU 资源
    -c 4096 \\              # 上下文长度，按需调整（越长越吃显存）
    --repeat-penalty 1.1 \\ # 减少重复，提升输出质量
    -p "你好，请介绍一下你自己"
""")

add_info_box(doc, '关键参数 -ngl',
    '-ngl（gpu-layers）控制推送到 GPU 的层数。值越高，GPU 计算越多，CPU 介入越少，速度越快。当 -ngl 覆盖全部层时，推理完全在 GPU 上进行，速度提升显著。')

doc.add_heading('2.3 批量推理与批处理', level=2)
add_code(doc, """
# ── llama-server：启动 HTTP API 服务器（支持并发请求） ──
./build/bin/llama-server \\
    -m Meta-Llama-3-8B-Instruct-Q4_K_M.gguf \\
    -ngl 35 \\
    -c 8192 \\
    --host 0.0.0.0 \\
    --port 8080 \\
    --ctx-size 8192 \\
    --batch-size 512 \\     # 每批 tokens，影响显存峰值
    --log-disable          # 生产环境关闭日志，减少 IO

# ── 客户端并发测试 ──
curl http://localhost:8080/v1/chat/completions \\
  -H "Content-Type: application/json" \\
  -d '{"model":"llama","messages":[{"role":"user","content":"Hello"}],"max_tokens":256}'
""")
add_note_box(doc, '批处理调优建议',
    '--batch-size 默认 2048，显存紧张时降至 512 或 256。--cache-type-k/q 可设为 f16 或 f32 提升精度但增加显存。NVIDIA GPU 上 f16 通常是最佳平衡点。')

doc.add_heading('2.4 系统级资源隔离', level=2)
add_code(doc, """
# ── 限制 llama.cpp 使用特定 GPU（多卡环境） ──
export CUDA_VISIBLE_DEVICES=0
./build/bin/llama-cli -m model.gguf -ngl 35 ...

# ── 设置 CPU 亲和性，避免推理进程抢占桌面线程 ──
taskset -c 0-3 ./build/bin/llama-cli -m model.gguf -ngl 35 ...

# ── systemd 服务：开机后自动以低优先级运行推理服务器 ──
sudo tee /etc/systemd/system/llama-server.service << 'EOF'
[Unit]
Description=llama.cpp Local Inference Server
After=network.target nvidia-power.service

[Service]
Type=simple
User=clean
Environment="CUDA_VISIBLE_DEVICES=0"
Environment="HF_HOME=/home/clean/.cache/huggingface"
ExecStart=/home/clean/bin/llama-server \\
    -m /home/clean/models/Meta-Llama-3-8B-Instruct-Q4_K_M.gguf \\
    -ngl 35 -c 4096 --host 127.0.0.1 --port 8080
Nice=10
IOSchedulingPriority=7
CPUSchedulingPolicy=idle
LimitNOFILE=65536

[Install]
WantedBy=multi-user.target
EOF

sudo systemctl daemon-reload
sudo systemctl enable llama-server.service
sudo systemctl start llama-server.service
""")

doc.add_page_break()

# ══════════════════════════════════════════════════════════════════════════════
# CHAPTER 3: Dynamic Wallpaper
# ══════════════════════════════════════════════════════════════════════════════
doc.add_heading('3. 轻量级动态壁纸方案', level=1)

doc.add_heading('3.1 方案选型对比', level=2)
add_info_box(doc, '设计约束',
    '仅图形模式启用动态壁纸，CLI 模式下零开销。方案必须满足：内存 < 100MB、CPU 占用 < 3%、支持 macOS 风格流体动画、与 picom 液态玻璃效果兼容。')

tbl2 = doc.add_table(rows=4, cols=5)
tbl2.style = 'Light Grid Accent 1'
tbl2.alignment = WD_TABLE_ALIGNMENT.CENTER
headers2 = ['方案', '内存', 'CPU', '兼容性', '推荐度']
data2 = [
    ['mpv-bg（mpv + i3lock）', '30-50 MB', '< 2%', '✅ X11 完美', '⭐⭐⭐⭐⭐'],
    ['screensaver-pywal', '40-60 MB', '< 3%', '✅ X11', '⭐⭐⭐⭐'],
    ['Wallpaper Engine（Steam）', '150-300 MB', '5-10%', '⚠️ Steam 依赖', '⭐⭐'],
]
hdr_cells2 = tbl2.rows[0].cells
for i, h in enumerate(headers2):
    hdr_cells2[i].text = h
    for pp in hdr_cells2[i].paragraphs:
        for r in pp.runs:
            r.font.bold = True
            r.font.size = Pt(9)
for ri, row_data in enumerate(data2):
    row = tbl2.rows[ri + 1].cells
    for ci, val in enumerate(row_data):
        row[ci].text = val
        for pp in row[ci].paragraphs:
            for r in pp.runs:
                r.font.size = Pt(9)

doc.add_heading('3.2 mpv 动态壁纸配置（强烈推荐）', level=2)
add_code(doc, """
# ── 安装依赖 ──
sudo pacman -S mpv wmname

# ── 创建动态壁纸脚本 ──
mkdir -p ~/bin ~/.config/mpv
cat > ~/bin/wallpaper-mpv << 'SCRIPT'
#!/bin/bash
# Lightweight dynamic wallpaper using mpv as root window background
# Memory: ~40MB | CPU: <2%

VIDEO_PATH="${1:-$HOME/Pictures/Wallpapers/ocean-loop.mp4}"
MPV_CONF="$HOME/.config/mpv/mpv.conf"

# Ensure mpv runs without GUI window decoration
cat > "$MPV_CONF" << 'EOF'
no-border
no-osc
no-osd-bar
ontop
geometry=100%x100%
force-window
wid=root
loop
volume=0
EOF

# Kill existing wallpaper process
pkill -f "mpv.*root" 2>/dev/null

# Start mpv as root window background
mpv --no-border --no-osc --no-osd-bar \\
    --ontop --geometry=100%x100% \\
    --force-window --wid=root \\
    --loop --volume=0 \\
    "$VIDEO_PATH" &

echo "Dynamic wallpaper started: $VIDEO_PATH"
SCRIPT
chmod +x ~/bin/wallpaper-mpv

# ── 添加便捷命令到 ~/.bashrc（仅图形模式生效） ──
echo '' >> ~/.bashrc
echo '# Dynamic wallpaper (GUI mode only)' >> ~/.bashrc
echo 'wallpaper() { ~/bin/wallpaper-mpv "$1"; }' >> ~/.bashrc
""")

add_info_box(doc, 'Wallpapers 获取',
    '推荐来源：r/wallpaperengine 的免费 MP4 文件、wallpaperhub.app、YouTube 4K 循环视频（用 yt-dlp 下载）。文件格式推荐 MP4 H.264，分辨率匹配显示器 native 分辨率。')

add_code(doc, """
# ── 测试播放（手动） ──
~/bin/wallpaper-mpv ~/Pictures/Wallpapers/aurora-loop.mp4

# ── 集成到 dwm 启动脚本（~/.xinitrc） ──
# 在 exec dwm 之前添加：
~/bin/wallpaper-mpv ~/Pictures/Wallpapers/ocean-loop.mp4 &

# ── 切换壁纸 ──
wallpaper ~/Pictures/Wallpapers/forest-loop.mp4

# ── 停止动态壁纸 ──
pkill -f "mpv.*root"
""")

doc.add_heading('3.3 与 picom 液态玻璃效果的集成', level=2)
add_info_box(doc, '兼容要点',
    'mpv 以 root window 方式运行时，picom 会将其视为普通窗口并应用模糊效果。为确保最佳效果，需要在 picom 配置中排除 wallpaper 进程，避免双重渲染。')

add_code(doc, """
# ~/.config/picom/picom.conf 中已配置的 blur
# picom 会自动对非 root-window 的窗口应用磨砂玻璃效果
# 确保以下排除规则存在，防止 picom 对 mpv root 窗口重复处理：

blur-background-exclude = [
    "window_type = 'desktop'",    # 壁纸层不被 picom 处理
    "class_g = 'mpv'",
    "_NET_WM_WINDOW_TYPE@:w = '_NET_WM_WINDOW_TYPE_DESKTOP'"
]

# 窗体磨砂玻璃效果（针对应用窗口）
blur: exclude = [
    "name = 'Alacritty'",
    "class_g = 'Firefox'"
]
""")

doc.add_heading('3.4 动态壁纸的电源管理', level=2)
add_code(doc, """
# ── 创建 wallpaper-toggle 脚本 ──
cat > ~/bin/wallpaper-toggle << 'EOF'
#!/bin/bash
# Toggle dynamic wallpaper on/off
if pgrep -f "mpv.*root" > /dev/null; then
    pkill -f "mpv.*root"
    echo "Dynamic wallpaper stopped"
else
    ~/bin/wallpaper-mpv "$1"
    echo "Dynamic wallpaper started"
fi
EOF
chmod +x ~/bin/wallpaper-toggle

# ── 笔记本合盖时自动停止（省电） ──
sudo tee /etc/systemd/logind.conf.d/wallpaper-power.conf << 'EOF'
[Login]
# When lid closed, stop dynamic wallpaper
KillUserProcesses=no
EOF

# 通过 logind signal 触发停止（可选高级方案）
sudo tee /etc/systemd/system/wallpaper-lid.service << 'EOF'
[Unit]
Description=Stop wallpaper on laptop lid close
After=sleep.target

[Service]
Type=oneshot
ExecStart=/bin/pkill -f "mpv.*root"

[Install]
WantedBy=sleep.target
EOF
sudo systemctl enable wallpaper-lid.service
""")

doc.add_page_break()

# ══════════════════════════════════════════════════════════════════════════════
# CHAPTER 4: Boot Flow & Resource Overview
# ══════════════════════════════════════════════════════════════════════════════
doc.add_heading('4. 开机流程与资源占用总览', level=1)

doc.add_heading('阶段一：纯命令行模式（CLI）', level=2)
add_code(doc, """
# 默认 target：multi-user.target（无图形界面）
# 启动后内存占用约 80-120 MB

# 查看当前运行状态
systemctl get-default          # 确认 multi-user.target
systemctl list-units --type=service --state=running | head -30
free -h                        # 查看内存使用
""")

doc.add_heading('阶段二：启动图形桌面 + 动态壁纸', level=2)
add_code(doc, """
# 从 CLI 切换到图形桌面（手动触发）
startx                           # 启动 X11 + dwm + picom + mpv 壁纸

# 或使用 sway（Wayland，更现代，性能略优）
sway                            # Wayland compositor，内置合成器无需额外 picom
""")

doc.add_heading('内存占用参考表', level=2)
tbl3 = doc.add_table(rows=6, cols=3)
tbl3.style = 'Light Grid Accent 1'
tbl3.alignment = WD_TABLE_ALIGNMENT.CENTER
headers3 = ['阶段', '组件', '内存占用']
data3 = [
    ['CLI', 'systemd + shell', '~100 MB'],
    ['GUI 启动', 'X11 + dwm + alacritty', '~200 MB'],
    ['特效层', 'picom（液态玻璃）', '+50 MB'],
    ['壁纸层', 'mpv（静态 MP4 循环）', '+40 MB'],
    ['推理服务', 'llama-server（Q4 8B，GPU 加载）', '～4.5 GB 显存 + ~100 MB RAM'],
]
hdr_cells3 = tbl3.rows[0].cells
for i, h in enumerate(headers3):
    hdr_cells3[i].text = h
    for pp in hdr_cells3[i].paragraphs:
        for r in pp.runs:
            r.font.bold = True
            r.font.size = Pt(9)
for ri, row_data in enumerate(data3):
    row = tbl3.rows[ri + 1].cells
    for ci, val in enumerate(row_data):
        row[ci].text = val
        for pp in row[ci].paragraphs:
            for r in pp.runs:
                r.font.size = Pt(9)

doc.add_page_break()

# ══════════════════════════════════════════════════════════════════════════════
# CHAPTER 5: Complete Install Script
# ══════════════════════════════════════════════════════════════════════════════
doc.add_heading('5. 完整自动化安装脚本', level=1)
add_info_box(doc, '使用方法',
    '将以下脚本保存为 install-arch-nvidia.sh，在 Arch 安装完成后以 root 权限执行。脚本会安装所有驱动、编译 llama.cpp、配置桌面环境。')

add_code(doc, """
#!/bin/bash
#=============================================================================
# Arch Linux NVIDIA + llama.cpp + Dynamic Wallpaper 一键安装脚本
# 适用：Arch Linux (x86_64) + NVIDIA GPU
# 执行：sudo bash install-arch-nvidia.sh
#=============================================================================
set -euo pipefail

echo "==> [1/6] 更新系统..."
sudo pacman -Syu --noconfirm

echo "==> [2/6] 安装 NVIDIA 专有驱动..."
sudo pacman -S --noconfirm nvidia nvidia-utils opencl-nvidia nvidia-settings
sudo modprobe nvidia
echo "nvidia_drm" | sudo tee /etc/modules-load.d/nvidia.conf
echo "options nvidia_drm modeset=1 fbdev=1" | sudo tee /etc/modprobe.d/nvidia-drm.conf

echo "==> [3/6] 安装桌面基础组件..."
sudo pacman -S --noconfirm \\
    xorg-server xorg-xinit xorg-apps \\
    dwm dmenu st alacritty \\
    picom mesa \\
    neovim bat less git curl wget \\
    firefox chromium \\
    mpv wmname

echo "==> [4/6] 编译 llama.cpp（CUDA 加速）..."
REPO_DIR="/tmp/llama.cpp"
if [ ! -d "$REPO_DIR" ]; then
    git clone https://github.com/ggerganov/llama.cpp.git "$REPO_DIR"
fi
cd "$REPO_DIR"
git pull
cmake -S . -B build \\
    -DGGML_CUDA=ON \\
    -DCMAKE_BUILD_TYPE=Release \\
    -DGGML_CUDA_FORCE_MMQ=OFF \\
    -DCMAKE_CUDA_ARCHITECTURES="80"
cmake --build build --config Release -j$(nproc)
sudo cmake --install build
cp -f build/bin/llama-cli build/bin/llama-server ~/bin/ 2>/dev/null || true

echo "==> [5/6] 配置动态壁纸..."
mkdir -p ~/bin ~/.config/mpv
cat > ~/bin/wallpaper-mpv << 'INNEREOF'
#!/bin/bash
VIDEO_PATH="${1:-$HOME/Pictures/Wallpapers/default.mp4}"
MPV_CONF="$HOME/.config/mpv/mpv.conf"
cat > "$MPV_CONF" << 'EOF'
no-border
no-osc
no-osd-bar
ontop
geometry=100%x100%
force-window
wid=root
loop
volume=0
EOF
pkill -f "mpv.*root" 2>/dev/null || true
mpv --no-border --no-osc --no-osd-bar \\
    --ontop --geometry=100%x100% \\
    --force-window --wid=root \\
    --loop --volume=0 "$VIDEO_PATH" &
echo "Dynamic wallpaper running."
INNEREOF
chmod +x ~/bin/wallpaper-mpv

echo '# Dynamic wallpaper (GUI mode only)' >> ~/.bashrc
echo 'wallpaper() { ~/bin/wallpaper-mpv "$1"; }' >> ~/.bashrc

echo "==> [6/6] 配置 picom（液态玻璃效果）..."
mkdir -p ~/.config/picom
cat > ~/.config/picom/picom.conf << 'PICOMEOF'
backend = "glx";
glx-no-stencil = true;
glx-no-rebind-pixmap = true;
vsync = true;

# Shadow
shadow = true;
shadow-radius = 12;
shadow-opacity = 0.35;
shadow-offset-x = -8;
shadow-offset-y = -8;

# Blur (frosted glass effect)
blur-method = "dual_kawase";
blur-strength = 15;
blur-background-exclude = [
    "window_type = 'desktop'",
    "class_g = 'mpv'"
];
blur-kern = "5x5 gaussian";

# Fade
fade-in-step = 0.03;
fade-out-step = 0.03;
fade = true;

# DWM integration
dwm-workarounds = true;
inactive-opacity = 0.95;
frame-opacity = 0.9;
inactive-opacity-override = false;
PICOMEOF

echo ""
echo "==> ✅ 安装完成！"
echo "==> 重启后以 multi-user.target 启动（纯命令行）"
echo "==> 输入 'startx' 启动图形桌面 + 动态壁纸"
echo "==> 可用命令："
echo "     wallpaper [视频路径]   切换动态壁纸"
echo "     nvtop                  GPU 监控"
echo "     ~/bin/llama-cli        本地推理"
""")

# ── Final note ──
doc.add_paragraph()
p = doc.add_paragraph()
run = p.add_run('文档版本：v1.0　｜　生成日期：2026-11-01　｜　适用架构：x86_64')
set_run_font(run, size=Pt(9), color=RGBColor(0x8E, 0x8E, 0x93))

# Save
output_path = '/Users/clean/Desktop/CleanLinux/docs/Arch-Linux-NVIDIA-llama-cpp-Wallpaper-Optimization.docx'
doc.save(output_path)
print(f"✅ Document saved: {output_path}")
