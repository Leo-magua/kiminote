# AI Notes - 开发文档

> 最后更新：2026-04-01

---

## 📋 开发状态

### 已实现功能

| 功能模块 | 状态 | 说明 |
|---------|------|------|
| 用户认证 | ✅ 完成 | JWT + Cookie 认证 |
| 笔记 CRUD | ✅ 完成 | 创建、读取、更新、删除 |
| 富文本编辑器 | ✅ 完成 | TipTap.js 集成，支持三种编辑模式 |
| 图片上传 | ✅ 完成 | 拖拽、点击、粘贴、模态框拖拽上传 |
| 附件管理 | ✅ 完成 | 支持文档、视频、音频，实时同步附件列表 |
| 撤销重做 | ✅ 完成 | 快捷键 + 工具栏 + 自定义历史栈 |
| AI 摘要 | ✅ 完成 | 自动生成笔记摘要 |
| AI 标签 | ✅ 完成 | 自动生成标签 |
| 智能搜索 | ✅ 完成 | 语义搜索 |
| 文本增强 | ✅ 完成 | AI 文本改进 |
| 实时协作 | ✅ 完成 | WebSocket 多人编辑 |
| 版本历史 | ✅ 完成 | 版本管理和恢复 |
| 冲突解决 | ✅ 完成 | 自动冲突检测 |
| 数据统计 | ✅ 完成 | 写作统计分析 |

---

## 🏗️ 架构说明

### 后端架构

```
app/
├── main.py           # FastAPI 主应用，路由定义
├── database.py       # SQLAlchemy 模型和数据库操作
├── auth.py           # 认证逻辑（JWT、密码哈希）
├── ai_service.py     # OpenAI API 封装
├── schemas.py        # Pydantic 数据验证模型
├── websocket.py      # WebSocket 协作管理
└── config.py         # 配置管理
```

### 前端架构

```
static/
├── css/
│   ├── style.css         # 主样式
│   ├── editor.css        # 编辑器样式
│   └── collaboration.css # 协作功能样式
└── js/
    ├── app.js            # 主应用逻辑
    ├── editor.js         # 富文本编辑器
    ├── auth.js           # 认证相关
    └── collaboration.js  # 协作功能
```

---

## 💻 开发环境

### 启动开发服务器

```bash
# 使用启动脚本
python run.py

# 或使用 uvicorn
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### 运行测试

```bash
# 运行所有测试
pytest tests/ -v

# 运行特定测试文件
pytest tests/test_rich_text_editor.py -v
pytest tests/test_collaboration.py -v
```

### 代码检查

```bash
# 类型检查
mypy app/

# 代码格式
black app/ tests/
isort app/ tests/
```

---

## 📦 数据模型

### 核心模型

```python
# User - 用户
- id, username, email, hashed_password
- created_at, is_active

# Note - 笔记
- id, user_id, title, content, content_html
- summary, tags, current_version
- created_at, updated_at

# Attachment - 附件
- id, note_id, user_id
- filename, original_filename, file_path
- file_size, mime_type, file_type
- width, height (图片)

# NoteVersion - 版本历史
- id, note_id, user_id, version_number
- title, content, content_html
- change_type, change_summary

# NoteCollaborator - 协作者
- id, note_id, user_id, permission
- added_by
```

---

## 🔌 API 设计

### RESTful API 规范

- 使用标准 HTTP 方法（GET/POST/PUT/DELETE）
- 返回 JSON 格式数据
- 统一错误响应格式：`{"detail": "错误信息"}`
- 认证使用 Bearer Token 或 Cookie

### WebSocket 协议

```
/ws/collaborate/{note_id}

消息类型：
- connected        - 连接成功
- user_joined      - 用户加入
- user_left        - 用户离开
- content_change   - 内容变更
- cursor_update    - 光标更新
- selection_update - 选区更新
```

---

## 🎨 富文本编辑器

### TipTap.js 配置

```javascript
// 核心扩展
- StarterKit: 基础编辑功能
- Image: 图片支持
- Table: 表格编辑
- TaskList/TaskItem: 任务列表
- Link: 超链接
- Highlight: 文本高亮
- Placeholder: 占位符
```

### 功能清单

- ✅ 三种编辑模式（富文本/预览/Markdown）
- ✅ 图片上传（拖拽、点击、粘贴）
- ✅ 附件管理（支持文档、视频、音频）
- ✅ 撤销重做（Ctrl+Z / Ctrl+Y）
- ✅ 表格编辑（插入、删除行列、表头切换）
- ✅ 任务列表（复选框支持）
- ✅ 代码高亮（30+ 编程语言）
- ✅ 数学公式（KaTeX 支持 LaTeX）
- ✅ 图表绘制（Mermaid 流程图、序列图等）
- ✅ 表情符号选择器
- ✅ 自动保存（localStorage）
- ✅ 字数统计和字符计数
- ✅ 查找替换功能
- ✅ Markdown 导入/导出

---

## 🤖 AI 功能

### 服务层设计

```python
class AIService:
    - generate_summary(content) -> str
    - generate_tags(title, content) -> List[str]
    - smart_search(query, notes) -> List[dict]
    - enhance_content(content, instruction) -> str
```

### 错误处理

- AI 服务不可用时优雅降级
- API 调用超时处理（10秒）
- 失败时返回 None，不阻塞主流程

---

## 👥 协作功能

### 实时协作

- WebSocket 连接管理
- 操作转换（Operational Transformation）
- 光标位置同步
- 选区更新同步

### 版本控制

- 自动版本创建（创建/编辑/恢复）
- 版本比较
- 版本恢复

### 冲突解决

- 基于版本号检测冲突
- 三种解决方式：使用我的/使用服务器的/合并

---

## 📝 提交规范

```
feat: 新功能
fix: 修复问题
docs: 文档更新
style: 代码格式（不影响功能）
refactor: 重构
test: 测试相关
chore: 构建/工具相关
```

示例：
```bash
git commit -m "feat: 添加图片拖拽上传功能

- 支持拖拽上传图片到编辑器
- 自动压缩大图片
- 显示上传进度"
```

---

## 🚀 部署

### 生产环境配置

```bash
# 设置环境变量
export DEBUG=false
export SECRET_KEY=your-secret-key
export OPENAI_API_KEY=your-api-key

# 使用 gunicorn
gunicorn app.main:app -w 4 -k uvicorn.workers.UvicornWorker
```

### Docker 部署

```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
CMD ["python", "run.py"]
```

---

## 📚 参考文档

- [FastAPI 文档](https://fastapi.tiangolo.com/)
- [TipTap.js 文档](https://tiptap.dev/)
- [SQLAlchemy 文档](https://docs.sqlalchemy.org/)
- [OpenAI API 文档](https://platform.openai.com/docs)

---

**项目状态：✅ 完整实现，稳定运行中**

Made with ❤️ using FastAPI + OpenAI + TipTap.js
