#!/usr/bin/env bash
# AI Notes 自动优化与进度同步脚本

set -e

PROJECT_DIR="/root/ai_notes_project"
cd "$PROJECT_DIR"

echo "[$（date）] 开始自动优化任务" >> /var/log/ai_notes_auto_optimize.log

# 激活虚拟环境
source "$PROJECT_DIR/venv/bin/activate"
export PATH="$HOME/.local/bin:$PATH"

# 记录当前状态
git status --porcelain > /tmp/git_status_before.txt 2>&1 || true

# 运行 Kimi 优化任务（简化版，只做代码检查）
kimi --print --prompt "请快速审查 AI Notes 项目的代码质量，找出明显的问题并提出改进建议。不要修改代码，只输出分析报告。" --work-dir "$PROJECT_DIR" --model k2p5 --yolo > /tmp/kimi_review_$(date +%s).txt 2>&1 || true

# 检查是否有文件变更（Kimi 可能自动修复了一些问题）
if git status --porcelain | grep -q .; then
    # 有变更，更新 DEVELOPMENT.md
    python3 << 'PYEOF'
from datetime import datetime
import re

with open('DEVELOPMENT.md', 'r', encoding='utf-8') as f:
    content = f.read()

# 添加新日志
today = datetime.now().strftime('%Y-%m-%d')
new_entry = f"\n### {today}\n- 🔄 自动优化任务执行\n- 📊 检测到代码变更，已自动提交"

# 找到"开发日志"部分
log_marker = "## 📈 开发日志"
if log_marker in content:
    parts = content.split(log_marker)
    after_log = parts[1].split('\n', 1)[1] if '\n' in parts[1] else parts[1]
    content = parts[0] + log_marker + new_entry + '\n' + after_log

with open('DEVELOPMENT.md', 'w', encoding='utf-8') as f:
    f.write(content)

print("DEVELOPMENT.md updated")
PYEOF

    # 提交并推送
    git add DEVELOPMENT.md
    git add -A  # 添加所有变更
    git commit -m "Auto-optimization $(date +%Y-%m-%d)" -m "Kimi automated code review and fixes" || true
    git push origin main || true
    
    echo "[$(date)] 优化完成并已推送" >> /var/log/ai_notes_auto_optimize.log
else
    echo "[$(date)] 无代码变更" >> /var/log/ai_notes_auto_optimize.log
fi

echo "[$(date)] 任务结束" >> /var/log/ai_notes_auto_optimize.log
