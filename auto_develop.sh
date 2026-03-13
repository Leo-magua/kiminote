#!/usr/bin/env bash
# AI Notes 主动开发脚本 - 每30分钟推进一个功能

set -e

PROJECT_DIR="/root/ai_notes_project"
cd "$PROJECT_DIR"

# 日志
LOG_FILE="/var/log/ai_notes_develop.log"
echo "[$(date)] 开始开发任务" >> "$LOG_FILE"

# 激活虚拟环境
source "$PROJECT_DIR/venv/bin/activate"
export PATH="$HOME/.local/bin:$PATH"

# 定义开发任务队列（按优先级，已完成的任务会跳过）
TASKS=(
    "添加富文本编辑器：集成 TipTap/Quill，支持图片上传、附件、撤销重做"
    "添加协作功能：WebSocket 实时协作、版本历史、冲突解决"
    "添加移动端优化：PWA 支持、移动端手势操作、响应式改进"
    "添加高级搜索：按标签筛选、按日期范围、全文搜索 FTS"
    "添加主题系统：暗色模式、主题切换、自定义主题色"
    "添加多语言支持：中英文界面切换、RTL 支持"
    "添加插件系统：第三方技能集成、自定义导出格式"
    "添加 AI 使用统计：记录 AI 调用次数、Token 使用情况"
    "添加数据备份功能：自动备份到本地、云端备份选项"
    "添加笔记模板功能：预设模板、自定义模板"
)

# 根据日期和分钟数轮询选择任务（每天不同，每半小时可能不同）
DAY_OF_YEAR=$(date +%j)
HALF_HOUR=$(( ($(date +%M) / 30) ))
TASK_INDEX=$(( (DAY_OF_YEAR * 10 + HALF_HOUR) % ${#TASKS[@]} ))
TASK="${TASKS[$TASK_INDEX]}"

echo "今日开发任务: $TASK" >> "$LOG_FILE"

# 检查任务是否已经在 DEVELOPMENT.md 中标记为完成
if grep -q "\\- \\[x\\] \\*\\*.*$TASK" DEVELOPMENT.md 2>/dev/null; then
    echo "任务已完成，跳过" >> "$LOG_FILE"
    exit 0
fi

# 运行 Kimi 开发任务
kimi --print --prompt "
请继续开发 AI Notes 项目。

当前开发任务：$TASK

项目路径: $PROJECT_DIR

要求：
1. 完整实现该功能，包括数据模型、API、前端界面
2. 遵循现有代码架构和风格
3. 确保与已有功能兼容
4. 更新 README.md 和 DEVELOPMENT.md
5. 不要破坏现有功能
6. 完成后提交代码

请开始实现。" --work-dir "$PROJECT_DIR" --model k2p5 --yolo > "/tmp/kimi_dev_$(date +%s).txt" 2>&1

echo "Kimi 开发完成，检查变更..." >> "$LOG_FILE"

# 等待文件写入
sleep 10

# 检查是否有变更
if git status --porcelain | grep -q .; then
    echo "检测到新功能开发，更新文档并推送..." >> "$LOG_FILE"

    # 更新 DEVELOPMENT.md - 将任务标记为完成
    python3 << 'PYEOF'
from datetime import datetime
import re

with open('DEVELOPMENT.md', 'r', encoding='utf-8') as f:
    content = f.read()

today = datetime.now().strftime('%Y-%m-%d')
new_entry = f"\n### {today}\n- 🚀 Phase 2 功能开发\n- 📌 完成：$TASK\n- ✅ 状态：已完成并推送"

log_marker = "## 📈 开发日志"
if log_marker in content:
    parts = content.split(log_marker)
    after_log = parts[1].split('\n', 1)[1] if '\n' in parts[1] else parts[1]
    content = parts[0] + log_marker + new_entry + '\n' + after_log

# 同时在任务列表中标记为完成
task_marker = f"- [ ] **{TASK.split(':')[0].strip()}"
if task_marker in content:
    content = content.replace(task_marker, f"- [x] **{TASK.split(':')[0].strip()}")

with open('DEVELOPMENT.md', 'w', encoding='utf-8') as f:
    f.write(content)

print("DEVELOPMENT.md updated")
PYEOF

    # 提交并推送（使用当前配置的 Git 用户信息）
    git add .
    git commit -m "Feature: $TASK" -m "Auto-developed by Kimi on $(date)" || true
    git push origin main || true

    echo "[$(date)] 开发完成并已推送" >> "$LOG_FILE"
else
    echo "[$(date)] 无代码变更" >> "$LOG_FILE"
fi

echo "[$(date)] 任务结束" >> "$LOG_FILE"
