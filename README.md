# 📝 AI Notes

AI Notes 是一个智能化的笔记应用，集成了 AI 功能来帮助用户更好地管理和组织笔记。支持多用户，每个用户的数据完全隔离。

![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)
![FastAPI](https://img.shields.io/badge/FastAPI-0.104+-green.svg)
![License](https://img.shields.io/badge/License-MIT-yellow.svg)

## ✨ 核心功能

### 基础功能
- 📝 **创建、编辑、删除笔记** - 简洁直观的笔记管理
- 🎨 **富文本编辑器** - 基于 TipTap.js v2.2+ (ProseMirror) 的现代化编辑器
  - 三种编辑模式：富文本编辑、实时预览、Markdown 源码
  - 双模式内容存储：同时保存 Markdown 和 HTML
  - 图片上传：拖拽、点击、剪贴板粘贴
  - 附件管理：支持多种文件类型
  - 撤销重做：快捷键和工具栏按钮
  - 表格编辑、任务列表、代码高亮
  - 数学公式、图表绘制、表情符号
- 💾 **本地存储** - SQLite 数据库，数据完全本地化管理
- 📤 **导出功能** - 支持导出为 JSON 和 Markdown
- 🔐 **用户认证** - 安全的 JWT + Cookie 认证

### AI 功能
- 🤖 **自动摘要** - AI 自动生成笔记内容摘要
- 🏷️ **智能标签** - AI 自动分析并生成相关标签
- 🔍 **智能搜索** - 基于语义理解的 AI 搜索
- ✍️ **文本增强** - AI 帮助改进、简化、专业化文本

### 协作功能
- 👥 **实时协作** - WebSocket 多人实时协同编辑
- 📜 **版本历史** - 自动保存笔记历史版本，支持恢复
- ⚡ **冲突解决** - 智能冲突检测与解决机制
- 🔐 **协作者管理** - 只读、读写、管理员三种权限

### 数据统计
- 📊 **笔记统计** - 笔记数量、字数统计、写作习惯分析
- 🔥 **连续写作天数** - 追踪你的写作 streak
- 📈 **活动时间分布** - 24小时和星期分布图表

## 🚀 快速开始

### 1. 克隆项目

```bash
git clone <repository-url>
cd ai_notes_project
```

### 2. 创建虚拟环境

```bash
python -m venv venv
source venv/bin/activate  # Linux/macOS
# 或
venv\Scripts\activate  # Windows
```

### 3. 安装依赖

```bash
pip install -r requirements.txt
```

### 4. 配置环境变量

```bash
cp .env.example .env
# 编辑 .env 文件，填入你的 OpenAI API 密钥
```

### 5. 启动应用

```bash
python run.py
# 或
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
| `SECRET_KEY` | JWT 签名密钥 | 随机生成 |
| `ACCESS_TOKEN_EXPIRE_DAYS` | 会话过期天数 | 7 |

## 📁 项目结构

```
ai_notes_project/
├── app/                    # 后端应用代码
│   ├── main.py            # FastAPI 主应用
│   ├── database.py        # 数据库模型和操作
│   ├── auth.py            # 认证相关功能
│   ├── ai_service.py      # AI 服务集成
│   ├── schemas.py         # Pydantic 数据模型
│   ├── websocket.py       # WebSocket 实时协作
│   └── config.py          # 配置管理
├── static/                # 静态文件
│   ├── css/               # 样式文件
│   └── js/                # JavaScript 文件
├── templates/             # HTML 模板
├── tests/                 # 测试文件
├── data/                  # 数据库文件
├── uploads/               # 上传文件目录
├── exports/               # 导出文件目录
├── requirements.txt       # Python 依赖
├── run.py                 # 启动脚本
└── README.md              # 项目说明
```

## 🎯 使用指南

### 基本操作

1. **创建笔记** - 点击左侧"新建笔记"按钮
2. **编辑笔记** - 点击笔记卡片进入编辑模式
3. **保存笔记** - 点击"保存"按钮或使用 Ctrl+S
4. **删除笔记** - 在编辑模式下点击"删除"按钮
5. **搜索笔记** - 在左侧搜索框输入关键词

### 富文本编辑器

- **编辑模式切换**：富文本 / 预览 / Markdown
- **图片上传**：拖拽、点击、粘贴
- **附件管理**：支持 PDF、Word、Excel、视频、音频等
- **撤销重做**：Ctrl+Z / Ctrl+Y
- **表格编辑**：插入表格、调整行列
- **代码高亮**：支持 30+ 编程语言
- **数学公式**：LaTeX 语法支持
- **图表绘制**：Mermaid 语法支持

### AI 功能

- **自动生成摘要和标签** - 保存笔记时自动生成
- **智能搜索** - 点击搜索框旁的 🔍 按钮，用自然语言描述
- **文本增强** - 点击"AI 增强"按钮选择增强方式

### 协作功能

- **添加协作者** - 点击"👥 协作"按钮，输入用户名
- **版本历史** - 点击"📜 版本"按钮查看和恢复
- **实时协作** - 多个用户同时编辑同一笔记

### 快捷键

| 快捷键 | 功能 |
|--------|------|
| Ctrl + S | 保存笔记 |
| Ctrl + Z | 撤销 |
| Ctrl + Y / Ctrl+Shift+Z | 重做 |
| Ctrl + B | 粗体 |
| Ctrl + I | 斜体 |
| Ctrl + K | 插入链接 |
| Esc | 返回列表 / 关闭弹窗 |

## 🔌 API 接口

### 认证
| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/api/auth/register` | 用户注册 |
| POST | `/api/auth/login` | 用户登录 |
| POST | `/api/auth/logout` | 用户登出 |
| GET | `/api/auth/me` | 获取当前用户信息 |

### 笔记
| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/notes` | 获取笔记列表 |
| POST | `/api/notes` | 创建笔记 |
| GET | `/api/notes/{id}` | 获取笔记详情 |
| PUT | `/api/notes/{id}` | 更新笔记 |
| DELETE | `/api/notes/{id}` | 删除笔记 |

### 文件上传
| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/api/upload/image` | 上传图片 |
| POST | `/api/upload/attachment` | 上传附件 |
| GET | `/api/notes/{id}/attachments` | 获取附件列表 |
| DELETE | `/api/attachments/{id}` | 删除附件 |

### AI 功能
| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/api/notes/{id}/summarize` | 生成摘要 |
| POST | `/api/notes/{id}/tags` | 生成标签 |
| POST | `/api/search/smart` | 智能搜索 |
| POST | `/api/ai/enhance` | 文本增强 |

### 协作
| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/notes/{id}/versions` | 获取版本历史 |
| POST | `/api/notes/{id}/versions/{version_id}/restore` | 恢复版本 |
| GET | `/api/notes/{id}/collaborators` | 获取协作者 |
| POST | `/api/notes/{id}/collaborators` | 添加协作者 |
| WS | `/ws/collaborate/{note_id}` | WebSocket 协作 |

## 🧪 运行测试

```bash
# 运行所有测试
pytest tests/ -v

# 运行富文本编辑器测试
pytest tests/test_rich_text_editor.py -v

# 运行协作功能测试
pytest tests/test_collaboration.py -v
```

## 🛠️ 技术栈

- **后端**: Python + FastAPI
- **数据库**: SQLite + SQLAlchemy
- **前端**: 原生 HTML + CSS + JavaScript
- **富文本编辑器**: TipTap.js v2.2+ (ProseMirror)
- **Markdown**: Turndown.js + Marked.js
- **代码高亮**: highlight.js
- **数学公式**: KaTeX
- **图表绘制**: Mermaid
- **AI 集成**: OpenAI API
- **实时协作**: WebSocket + Operational Transformation
- **认证**: JWT + HTTP-only Cookie

## 🤝 贡献

欢迎提交 Issue 和 Pull Request！

## 📄 许可证

MIT License

---

Made with ❤️ using FastAPI + OpenAI + TipTap.js
