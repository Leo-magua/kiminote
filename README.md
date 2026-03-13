# 📝 AI Notes

AI Notes 是一个智能化的笔记应用，集成了 AI 功能来帮助用户更好地管理和组织笔记。支持多用户，每个用户的数据完全隔离。

![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)
![FastAPI](https://img.shields.io/badge/FastAPI-0.104+-green.svg)
![License](https://img.shields.io/badge/License-MIT-yellow.svg)

## ✨ 核心功能

### 基础功能
- 📝 **创建、编辑、删除笔记** - 简洁直观的笔记管理
- 🎨 **富文本编辑器** - 基于 TipTap.js v2.2+ (ProseMirror) 的现代化编辑器
  - **三种编辑模式**：富文本编辑、实时预览、Markdown 源码，自由切换
  - **图片上传**：支持拖拽上传和点击上传（JPG/PNG/GIF/WebP/SVG，最大 10MB）
  - **附件管理**：支持多种文件类型上传（PDF/Word/Excel/PPT/TXT/视频/音频，最大 50MB）
  - **撤销重做**：完整的编辑历史栈，支持工具栏按钮和快捷键（Ctrl+Z / Ctrl+Y）
  - **表格编辑**：插入表格、调整行列、表头支持
  - **任务列表**：可勾选的任务项，支持嵌套
  - **代码高亮**：行内代码和代码块，集成 highlight.js 语法高亮
  - **排版工具**：6级标题、粗体、斜体、删除线、高亮、引用、分隔线
  - **链接插入**：超链接快速插入和编辑
  - **列表支持**：无序列表、有序列表、任务列表
  - **Markdown 双向转换**：Turndown.js (HTML→Markdown) + Marked.js (Markdown→HTML)
- ✍️ **Markdown 支持** - 完整的 Markdown 语法支持，实时预览
- 🖼️ **图片管理** - 自动压缩、尺寸检测、Base64 回退
- 📎 **附件管理** - 文件类型自动识别、图标显示、大小格式化
- ↩️ **编辑历史** - 完整的撤销重做栈，跨操作会话保持
- 💾 **本地存储** - 使用 SQLite 数据库存储，数据完全本地化管理
- 📤 **导出功能** - 支持导出为 JSON 和 Markdown 格式
- 🔐 **用户认证** - 安全的用户注册、登录、登出功能

### AI 功能
- 🤖 **自动摘要** - AI 自动生成笔记内容摘要
- 🏷️ **智能标签** - AI 自动分析并生成相关标签
- 🔍 **智能搜索** - 基于语义理解的 AI 搜索，不只是关键词匹配
- ✍️ **文本增强** - AI 帮助改进、简化、专业化或扩展文本内容

### 协作功能
- 👥 **实时协作** - WebSocket 多人实时协同编辑，支持多用户同时编辑同一笔记
- 📜 **版本历史** - 自动保存笔记历史版本，支持查看、比较和恢复到任意历史版本
- ⚡ **冲突解决** - 智能冲突检测与解决机制，支持合并更改
- 🖱️ **光标同步** - 实时显示其他用户光标位置和编辑状态
- 🔐 **协作者管理** - 添加/移除协作者，支持只读、读写、管理员三种权限级别

### 数据统计
- 📊 **笔记统计** - 笔记数量、字数统计、写作习惯分析
- 🔥 **连续写作天数** - 追踪你的写作 streak
- 📈 **活动时间分布** - 24小时和星期分布图表
- 📅 **活动热力图** - 最近30天写作活动可视化

## 🚀 快速开始

### 1. 克隆项目

```bash
git clone <repository-url>
cd ai_notes_project
```

### 2. 创建虚拟环境（推荐）

```bash
python -m venv venv

# Windows
venv\Scripts\activate

# macOS/Linux
source venv/bin/activate
```

### 3. 安装依赖

```bash
pip install -r requirements.txt
```

### 4. 配置环境变量

```bash
# 复制示例配置文件
cp .env.example .env

# 编辑 .env 文件，填入你的 OpenAI API 密钥
OPENAI_API_KEY=your_api_key_here
```

### 5. 启动应用

```bash
# 使用启动脚本
python run.py

# 或使用 uvicorn 直接启动
uvicorn app.main:app --reload
```

### 6. 访问应用

打开浏览器访问：http://localhost:8000

## 🔧 配置说明

### 环境变量

| 变量名 | 说明 | 默认值 |
|--------|------|--------|
| `OPENAI_API_KEY` | OpenAI API 密钥 | 必填 |
| `OPENAI_BASE_URL` | API 基础 URL | https://api.openai.com/v1 |
| `OPENAI_MODEL` | 使用的模型 | gpt-3.5-turbo |
| `DEBUG` | 调试模式 | false |
| `HOST` | 监听地址 | 0.0.0.0 |
| `PORT` | 监听端口 | 8000 |
| `SECRET_KEY` | JWT 签名密钥（生产环境必须修改） | 随机生成 |
| `ACCESS_TOKEN_EXPIRE_DAYS` | 会话过期天数 | 7 |

### 支持的 AI 提供商

- **OpenAI** (默认): https://api.openai.com/v1
- **Moonshot AI**: https://api.moonshot.cn/v1
- **其他 OpenAI 兼容 API**: 配置 `OPENAI_BASE_URL` 即可

## 📁 项目结构

```
ai_notes_project/
├── app/                    # 后端应用代码
│   ├── __init__.py
│   ├── main.py            # FastAPI 主应用
│   ├── database.py        # 数据库模型和操作
│   ├── auth.py            # 认证相关功能
│   ├── ai_service.py      # AI 服务集成
│   ├── schemas.py         # Pydantic 数据模型
│   └── config.py          # 配置管理
├── static/                # 静态文件
│   ├── css/
│   │   ├── style.css      # 主样式文件
│   │   ├── auth.css       # 认证页面样式
│   │   └── editor.css     # 富文本编辑器样式
│   └── js/
│       ├── app.js         # 前端逻辑
│       ├── auth.js        # 认证相关功能
│       ├── editor.js      # 富文本编辑器
│       └── collaboration.js # 协作功能
├── templates/             # HTML 模板
│   ├── index.html         # 主页面
│   ├── login.html         # 登录页面
│   ├── register.html      # 注册页面
│   └── share.html         # 分享页面
├── data/                  # 数据库文件（自动创建）
├── uploads/               # 上传文件目录
├── exports/               # 导出文件目录
├── requirements.txt       # Python 依赖
├── .env.example          # 环境变量示例
├── run.py                # 启动脚本
└── README.md             # 项目说明
```

## 🎯 使用指南

### 基本操作

1. **创建笔记** - 点击左侧"新建笔记"按钮
2. **编辑笔记** - 点击笔记卡片进入编辑模式
3. **保存笔记** - 点击"保存"按钮或使用 Ctrl+S
4. **删除笔记** - 在编辑模式下点击"删除"按钮
5. **搜索笔记** - 在左侧搜索框输入关键词

### Markdown 语法支持

```markdown
# 标题1
## 标题2
### 标题3

**粗体文本**
*斜体文本*
`行内代码`

- 无序列表项
- 另一个列表项

1. 有序列表项
2. 另一个列表项

> 引用文本

```python
# 代码块
print("Hello World")
```

| 表格 | 列2 |
|------|-----|
| 数据 | 数据 |
```

### AI 功能使用

#### 自动生成摘要和标签
- 创建或编辑笔记并保存后，AI 会自动生成摘要和标签
- 也可以在编辑页面手动点击"生成摘要"或"生成标签"按钮

#### 智能搜索
- 点击搜索框旁边的 🔍 按钮
- 用自然语言描述你想找的内容，例如：
  - "关于项目管理的笔记"
  - "上周记录的技术方案"
  - "包含代码示例的笔记"

#### 文本增强
- 在编辑页面点击"AI 增强"按钮
- 选择增强方式：改进写作、简化内容、专业化、创意写作、扩展内容
- AI 将提供增强后的文本，你可以选择使用

### 导出笔记

- **JSON 导出** - 导出所有笔记为 JSON 格式，方便备份和数据迁移
- **Markdown 导出** - 导出所有笔记为单个 Markdown 文件

### 协作功能使用

#### 实时协作
- 在编辑笔记页面点击"👥 协作"按钮打开协作管理面板
- 输入其他用户的用户名并选择权限级别（只读/读写/管理员）来添加协作者
- 协作者打开笔记后将自动加入实时协作会话
- 实时查看其他协作者的光标位置和编辑状态
- WebSocket 连接支持自动重连，断线后会自动尝试恢复连接

#### 版本历史
- 点击"📜 版本"按钮查看笔记的版本历史
- 每个保存操作都会自动创建一个新版本
- 可以查看任意版本的内容预览
- 支持恢复到任意历史版本（当前内容会被保存为新版本）
- 版本类型包括：创建、编辑、恢复、合并

#### 冲突解决
- 当多个用户同时编辑并保存时，系统会自动检测冲突
- 冲突解决选项：
  - **使用我的版本** - 保留当前用户的修改
  - **使用服务器版本** - 放弃本地修改，使用服务器最新版本
  - **合并更改** - 手动合并两个版本的内容
- 冲突检测基于版本号对比，确保数据一致性

#### 协作者权限
- **只读 (read)** - 只能查看笔记，无法编辑
- **读写 (write)** - 可以查看和编辑笔记内容
- **管理员 (admin)** - 可以编辑笔记、管理协作者、恢复版本

## ⌨️ 快捷键

| 快捷键 | 功能 |
|--------|------|
| `Ctrl + S` | 保存笔记 |
| `Esc` | 返回列表 / 关闭弹窗 |

## 🛠️ 技术栈

- **后端**: Python + FastAPI
- **数据库**: SQLite + SQLAlchemy ORM
- **前端**: 原生 HTML + CSS + JavaScript
- **富文本编辑器**: TipTap.js v2.2+ (基于 ProseMirror)
  - StarterKit：提供基础编辑功能（标题、列表、代码块等）
  - Image 扩展：支持图片插入和 Base64 预览
  - Table/TableRow/TableCell/TableHeader 扩展：完整的表格支持
  - TaskList/TaskItem 扩展：可勾选的任务列表，支持嵌套
  - Highlight 扩展：文本高亮标记
  - Link 扩展：超链接插入和编辑
  - Placeholder 扩展：编辑器占位提示
  - Typography 扩展：排版优化
  - HorizontalRule 扩展：水平分隔线
- **Markdown 转换**: Turndown.js (HTML→Markdown) + Marked.js (Markdown→HTML)
- **Markdown 转换**: Turndown.js (HTML to Markdown) + Marked.js (Markdown to HTML)
- **代码高亮**: highlight.js + lowlight (TipTap 集成)
- **AI 集成**: OpenAI API
- **Markdown 解析**: Marked.js (前端) + Python-Markdown (后端)
- **实时协作**: WebSocket + Operational Transformation
- **代码高亮**: highlight.js

## 🔌 API 接口

### 认证（Auth）

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/api/auth/register` | 用户注册 |
| POST | `/api/auth/login` | 用户登录 |
| POST | `/api/auth/logout` | 用户登出 |
| GET | `/api/auth/me` | 获取当前用户信息 |

### 笔记 CRUD

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/notes` | 获取所有笔记（需登录） |
| POST | `/api/notes` | 创建笔记（需登录） |
| GET | `/api/notes/{id}` | 获取单个笔记（需登录，仅自己的笔记） |
| PUT | `/api/notes/{id}` | 更新笔记（需登录，仅自己的笔记） |
| DELETE | `/api/notes/{id}` | 删除笔记（需登录，仅自己的笔记） |

### AI 功能

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/api/notes/{id}/summarize` | 生成摘要（需登录） |
| POST | `/api/notes/{id}/tags` | 生成标签（需登录） |
| POST | `/api/search/smart` | 智能搜索（需登录） |
| POST | `/api/ai/enhance` | 文本增强（需登录） |

### 导出

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/export/json` | 导出 JSON（需登录） |
| GET | `/api/export/markdown` | 导出所有 Markdown（需登录） |
| GET | `/api/export/markdown/{id}` | 导出单个 Markdown（需登录） |

### 数据统计

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/stats` | 获取应用基本统计（需登录） |
| GET | `/api/stats/detailed` | 获取详细写作统计（需登录） |
| GET | `/api/stats/daily` | 获取每日统计数据（需登录） |

### 文件上传

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/api/upload/image` | 上传图片（JPG/PNG/GIF/WebP/SVG，最大 10MB） |
| POST | `/api/upload/attachment` | 上传附件（文档/图片，最大 50MB） |
| GET | `/api/notes/{id}/attachments` | 获取笔记附件列表 |
| PUT | `/api/notes/{id}/attachments` | 更新笔记附件关联 |
| DELETE | `/api/attachments/{id}` | 删除附件 |

### 富文本编辑器使用说明

AI Notes 集成了强大的 **TipTap.js** 富文本编辑器，支持多种编辑模式和丰富的排版功能。

#### 编辑模式切换

编辑器支持三种模式，通过顶部的标签页切换：

1. **编辑模式** - 所见即所得的富文本编辑
2. **预览模式** - 实时渲染 Markdown 效果
3. **Markdown 模式** - 直接编辑 Markdown 源码

三种模式之间内容自动同步，可以随时切换。

#### 工具栏功能

| 按钮 | 功能 | 快捷键 |
|------|------|--------|
| ↩️ ↪️ | 撤销 / 重做 | Ctrl+Z / Ctrl+Y |
| H | 标题（H1/H2/正文循环） | - |
| B | 粗体 | Ctrl+B |
| I | 斜体 | Ctrl+I |
| S | 删除线 | - |
| 🖍️ | 高亮标记 | - |
| • 1. | 无序 / 有序列表 | - |
| ☑️ | 任务列表 | - |
| ` ` | 行内代码 / 代码块 | - |
| ❝ | 引用块 | - |
| — | 水平分隔线 | - |
| 🔗 | 插入链接 | Ctrl+K |
| 🖼️ | 插入图片（支持拖拽上传） | - |
| ▦ | 插入表格 | - |
| 📎 | 上传附件 | - |
| 📥 📤 | Markdown 导入 / 导出 | - |

#### 图片上传

- **点击上传**：点击图片按钮，选择本地图片文件
- **拖拽上传**：直接拖拽图片到编辑器区域
- **URL 插入**：切换到"图片链接"标签页，输入图片地址

支持格式：JPG、PNG、GIF、WebP、SVG（最大 10MB）

#### 附件管理

- 上传的附件会显示在编辑器下方的附件列表中
- 点击附件名称可下载查看
- 点击 × 按钮可删除附件
- 删除笔记时会自动清理关联的附件文件

支持格式：
- 文档：PDF、Word、Excel、PowerPoint、TXT、Markdown
- 图片：JPG、PNG、GIF、WebP、SVG
- 其他：ZIP、JSON 等（最大 50MB）

### 协作功能

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/notes/{id}/versions` | 获取笔记版本历史 |
| GET | `/api/notes/{id}/versions/{version_id}` | 获取特定版本详情 |
| POST | `/api/notes/{id}/versions/{version_id}/restore` | 恢复到指定版本 |
| GET | `/api/notes/{id}/versions/compare` | 比较两个版本 |
| GET | `/api/notes/{id}/collaborators` | 获取协作者列表 |
| POST | `/api/notes/{id}/collaborators` | 添加协作者 |
| DELETE | `/api/notes/{id}/collaborators/{user_id}` | 移除协作者 |
| GET | `/api/notes/{id}/collaborators/active` | 获取活跃协作者 |
| POST | `/api/notes/{id}/conflict/detect` | 检测编辑冲突 |
| POST | `/api/notes/{id}/conflict/resolve` | 解决冲突 |
| GET | `/api/collaborated-notes` | 获取协作笔记列表 |
| WS | `/ws/collaborate/{note_id}` | WebSocket 实时协作 |

## 🤝 贡献

欢迎提交 Issue 和 Pull Request！

## 📄 许可证

MIT License

---

Made with ❤️ using FastAPI + OpenAI
