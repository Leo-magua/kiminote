# 📝 AI Notes

AI Notes 是一个智能化的笔记应用，集成了 AI 功能来帮助用户更好地管理和组织笔记。

![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)
![FastAPI](https://img.shields.io/badge/FastAPI-0.104+-green.svg)
![License](https://img.shields.io/badge/License-MIT-yellow.svg)

## ✨ 核心功能

### 基础功能
- 📝 **创建、编辑、删除笔记** - 简洁直观的笔记管理
- 🎨 **Markdown 支持** - 支持完整的 Markdown 语法（标题、列表、代码块、表格等）
- 💾 **本地存储** - 使用 SQLite 数据库存储，数据完全本地化管理
- 📤 **导出功能** - 支持导出为 JSON 和 Markdown 格式

### AI 功能
- 🤖 **自动摘要** - AI 自动生成笔记内容摘要
- 🏷️ **智能标签** - AI 自动分析并生成相关标签
- 🔍 **智能搜索** - 基于语义理解的 AI 搜索，不只是关键词匹配
- ✍️ **文本增强** - AI 帮助改进、简化、专业化或扩展文本内容

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
│   ├── ai_service.py      # AI 服务集成
│   └── config.py          # 配置管理
├── static/                # 静态文件
│   ├── css/
│   │   └── style.css      # 样式文件
│   └── js/
│       └── app.js         # 前端逻辑
├── templates/             # HTML 模板
│   └── index.html         # 主页面
├── data/                  # 数据库文件（自动创建）
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

## ⌨️ 快捷键

| 快捷键 | 功能 |
|--------|------|
| `Ctrl + S` | 保存笔记 |
| `Esc` | 返回列表 / 关闭弹窗 |

## 🛠️ 技术栈

- **后端**: Python + FastAPI
- **数据库**: SQLite + SQLAlchemy ORM
- **前端**: 原生 HTML + CSS + JavaScript
- **AI 集成**: OpenAI API
- **Markdown 解析**: Marked.js (前端) + Python-Markdown (后端)

## 🔌 API 接口

### 笔记 CRUD

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/notes` | 获取所有笔记 |
| POST | `/api/notes` | 创建笔记 |
| GET | `/api/notes/{id}` | 获取单个笔记 |
| PUT | `/api/notes/{id}` | 更新笔记 |
| DELETE | `/api/notes/{id}` | 删除笔记 |

### AI 功能

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/api/notes/{id}/summarize` | 生成摘要 |
| POST | `/api/notes/{id}/tags` | 生成标签 |
| POST | `/api/search/smart` | 智能搜索 |
| POST | `/api/ai/enhance` | 文本增强 |

### 导出

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/export/json` | 导出 JSON |
| GET | `/api/export/markdown` | 导出所有 Markdown |
| GET | `/api/export/markdown/{id}` | 导出单个 Markdown |

## 🤝 贡献

欢迎提交 Issue 和 Pull Request！

## 📄 许可证

MIT License

---

Made with ❤️ using FastAPI + OpenAI
