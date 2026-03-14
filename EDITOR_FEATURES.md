# 📝 AI Notes - 富文本编辑器功能文档

> 版本: 2.0  
> 更新日期: 2026-03-14  
> 状态: ✅ 已完成并验证

---

## 📋 功能概述

AI Notes 集成了强大的 **TipTap.js v2.2+** 富文本编辑器，提供完整的所见即所得（WYSIWYG）编辑体验，支持多种编辑模式、图片/附件上传、表格编辑等功能。

---

## ✨ 已实现功能

### 1. 编辑器核心

#### TipTap.js 集成
- **基于 ProseMirror** 的高性能编辑器内核
- **StarterKit** 提供基础编辑功能
  - 6级标题 (H1-H6)
  - 粗体、斜体、删除线
  - 无序/有序列表
  - 代码块和行内代码
  - 引用块
  - 水平分隔线
- **History** 扩展提供原生撤销/重做（100步历史）

#### 编辑模式
支持三种编辑模式无缝切换：
1. **富文本模式** - 所见即所得的实时编辑
2. **预览模式** - 实时 Markdown 渲染效果
3. **Markdown 模式** - 直接编辑 Markdown 源码

模式间内容自动双向同步。

---

### 2. 图片上传

#### 功能特性
- **点击上传** - 通过工具栏或模态框选择图片
- **拖拽上传** - 直接拖拽图片到编辑器区域
- **URL 插入** - 支持通过图片链接插入
- **格式支持** - JPG、PNG、GIF、WebP、SVG
- **大小限制** - 最大 10MB
- **自动压缩** - 上传前可选压缩
- **Base64 回退** - 上传失败时自动使用 Base64

#### API 端点
```
POST /api/upload/image
Content-Type: multipart/form-data

参数:
  - file: 图片文件 (必填)

响应:
  {
    "id": 1,
    "url": "/uploads/abc123.jpg",
    "filename": "abc123.jpg",
    "original_filename": "photo.jpg",
    "file_size": 102400,
    "width": 1920,
    "height": 1080
  }
```

---

### 3. 附件管理

#### 功能特性
- **多格式支持** - PDF、Word、Excel、PPT、TXT、ZIP 等
- **大小限制** - 最大 50MB
- **文件类型识别** - 自动识别文件类型并显示对应图标
- **附件列表** - 在编辑器下方显示关联附件
- **删除功能** - 支持删除已上传附件

#### 支持的文件类型
| 类型 | 扩展名 | 图标 |
|------|--------|------|
| 图片 | jpg, png, gif, webp, svg | 🖼️ |
| PDF | pdf | 📄 |
| Word | doc, docx | 📝 |
| Excel | xls, xlsx | 📊 |
| PPT | ppt, pptx | 📈 |
| 视频 | mp4, avi, mov | 🎬 |
| 音频 | mp3, wav | 🎵 |
| 压缩包 | zip, rar, 7z | 📦 |
| 文本 | txt, md | 📃 |
| 代码 | json, js, py, html, css | ⚙️ |
| 其他 | - | 📎 |

#### API 端点

**上传附件**
```
POST /api/upload/attachment
Content-Type: multipart/form-data

参数:
  - file: 附件文件 (必填)

响应:
  {
    "id": 1,
    "url": "/uploads/doc_xyz.pdf",
    "filename": "doc_xyz.pdf",
    "original_filename": "document.pdf",
    "file_size": 204800,
    "mime_type": "application/pdf",
    "file_type": "document"
  }
```

**获取笔记附件列表**
```
GET /api/notes/{note_id}/attachments

响应:
  {
    "attachments": [...],
    "total": 5,
    "note_id": 1
  }
```

**更新笔记附件关联**
```
PUT /api/notes/{note_id}/attachments
Content-Type: application/json

参数:
  - attachment_ids: [1, 2, 3] (附件ID数组)

响应:
  {"message": "Attachments updated successfully"}
```

**删除附件**
```
DELETE /api/attachments/{attachment_id}

响应:
  {"message": "附件已删除"}
```

---

### 4. 撤销/重做

#### 功能特性
- **快捷键支持**
  - `Ctrl + Z` - 撤销
  - `Ctrl + Y` - 重做
  - `Ctrl + Shift + Z` - 重做（替代）
- **工具栏按钮** - 撤销 ↩️ / 重做 ↪️ 按钮
- **历史栈** - 最多保存 100 步操作历史
- **按钮状态** - 根据历史栈自动更新按钮禁用状态

---

### 5. 表格编辑

#### 功能特性
- **插入表格** - 支持自定义行列数和表头
- **右键菜单** - 在表格中右键显示上下文菜单
  - 在上方/下方添加行
  - 在左侧/右侧添加列
  - 删除当前行/列
  - 切换表头行
  - 删除整个表格
- **样式支持** - 表头样式、斑马纹、响应式布局

#### 工具栏操作
| 操作 | 说明 |
|------|------|
| 插入表格 | 默认插入 3x3 表格 |
| 添加行 | 在下方添加新行 |
| 添加列 | 在右侧添加新列 |
| 删除行 | 删除光标所在行 |
| 删除列 | 删除光标所在列 |
| 切换表头 | 将当前行设为表头 |

---

### 6. 任务列表

#### 功能特性
- **可勾选任务** - 支持点击勾选/取消
- **嵌套支持** - 任务列表可以嵌套
- **Markdown 兼容** - 支持 `- [ ]` 和 `- [x]` 语法
- **实时同步** - 勾选状态实时保存

---

### 7. 代码高亮

#### 功能特性
- **行内代码** - 使用 `code` 标记
- **代码块** - 使用 ``` 标记，支持语法高亮
- **highlight.js 集成** - 支持 180+ 编程语言
- **自动检测** - 未指定语言时自动检测

---

### 8. 其他功能

#### 文本格式化
- **粗体** (`Ctrl+B`)
- **斜体** (`Ctrl+I`)
- **删除线**
- **高亮标记** (==text==)
- **链接** (`Ctrl+K`)

#### Markdown 支持
- **Turndown.js** - HTML 转 Markdown
- **Marked.js** - Markdown 转 HTML
- **双向同步** - 三种模式间内容自动同步

#### 自动保存
- **本地存储** - 每 30 秒自动保存到 localStorage
- **恢复提示** - 重新打开笔记时提示恢复未保存内容
- **保存指示器** - 状态栏显示保存状态

#### 字数统计
- **实时统计** - 编辑器底部显示字数和字符数
- **词数** - 按空格分隔计算
- **字符数** - 包含所有字符

---

## 🛠️ 技术实现

### 依赖库

| 库 | 版本 | 用途 |
|----|------|------|
| @tiptap/core | 2.2.4 | 编辑器核心 |
| @tiptap/starter-kit | 2.2.4 | 基础功能扩展 |
| @tiptap/extension-image | 2.2.4 | 图片支持 |
| @tiptap/extension-table | 2.2.4 | 表格支持 |
| @tiptap/extension-task-list | 2.2.4 | 任务列表 |
| @tiptap/extension-highlight | 2.2.4 | 文本高亮 |
| @tiptap/extension-link | 2.2.4 | 链接支持 |
| @tiptap/extension-placeholder | 2.2.4 | 占位提示 |
| marked | 9.1.6 | Markdown 渲染 |
| Turndown | 7.1.2 | HTML 转 Markdown |
| highlight.js | 11.9.0 | 代码高亮 |
| DOMPurify | 3.0.6 | XSS 防护 |

### 文件结构

```
ai_notes_project/
├── app/
│   ├── main.py              # API 端点 (2084 行)
│   ├── database.py          # 数据模型 (1461 行)
│   └── schemas.py           # Pydantic 模型
├── static/
│   ├── js/
│   │   └── editor.js        # 编辑器逻辑 (901 行)
│   └── css/
│       └── editor.css       # 编辑器样式 (747 行)
├── templates/
│   └── index.html           # 主页面模板 (655 行)
└── uploads/                 # 上传文件存储目录
```

---

## 📊 API 汇总

### 上传相关

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/api/upload/image` | 上传图片 (最大 10MB) |
| POST | `/api/upload/attachment` | 上传附件 (最大 50MB) |
| GET | `/api/notes/{id}/attachments` | 获取笔记附件列表 |
| PUT | `/api/notes/{id}/attachments` | 更新笔记附件关联 |
| DELETE | `/api/attachments/{id}` | 删除附件 |

### 静态文件服务

| 路径 | 说明 |
|------|------|
| `/uploads/{filename}` | 访问上传的文件 |

---

## 🎯 使用指南

### 基本编辑

1. **创建笔记** - 点击"新建笔记"按钮
2. **编辑内容** - 在富文本编辑器中输入内容
3. **格式化文本** - 使用工具栏按钮或快捷键
4. **保存笔记** - 点击"保存"按钮或按 `Ctrl+S`

### 插入图片

**方法 1: 点击上传**
1. 点击工具栏的 🖼️ 按钮
2. 选择"本地上传"标签
3. 点击选择图片或拖拽到上传区域
4. 点击"插入图片"

**方法 2: 拖拽上传**
1. 直接从文件管理器拖拽图片到编辑器区域
2. 等待上传完成，图片自动插入

**方法 3: URL 插入**
1. 点击工具栏的 🖼️ 按钮
2. 选择"图片链接"标签
3. 输入图片 URL
4. 点击"插入图片"

### 上传附件

1. 点击工具栏的 📎 按钮
2. 选择要上传的文件
3. 点击"上传附件"
4. 附件链接将自动插入到编辑器中

### 插入表格

1. 点击工具栏的 ▦ 按钮
2. 设置行数和列数
3. 勾选"包含表头"（可选）
4. 点击"插入表格"

**表格编辑:**
- 在表格中右键点击打开上下文菜单
- 选择相应操作（添加/删除行列、切换表头等）

### 使用任务列表

1. 点击工具栏的 ☑️ 按钮
2. 输入任务内容
3. 按 Enter 创建新任务项
4. 点击复选框标记完成/未完成

---

## ⌨️ 快捷键

### 编辑器快捷键

| 快捷键 | 功能 |
|--------|------|
| `Ctrl + Z` | 撤销 |
| `Ctrl + Y` | 重做 |
| `Ctrl + Shift + Z` | 重做（替代） |
| `Ctrl + B` | 粗体 |
| `Ctrl + I` | 斜体 |
| `Ctrl + K` | 插入链接 |

### 表格快捷键

| 快捷键 | 功能 |
|--------|------|
| `Tab` | 移动到下一个单元格 |
| `Shift + Tab` | 移动到上一个单元格 |
| `Enter` | 在当前单元格内换行 |
| `Backspace`（空单元格） | 删除当前行 |

---

## 🔧 配置选项

### 文件上传限制

```python
# app/config.py
MAX_UPLOAD_SIZE = 50 * 1024 * 1024  # 50MB
ALLOWED_IMAGE_TYPES = {
    'image/jpeg',
    'image/png',
    'image/gif',
    'image/webp',
    'image/svg+xml'
}
ALLOWED_DOCUMENT_TYPES = {
    'application/pdf',
    'application/msword',
    'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
    # ... 更多文档类型
}
```

### 编辑器配置

```javascript
// editor.js
const editor = new Editor({
    extensions: [
        StarterKit.configure({
            history: {
                depth: 100,        // 历史栈深度
                newGroupDelay: 500 // 新分组延迟(ms)
            }
        }),
        // ... 其他扩展
    ],
    // ... 其他配置
});
```

---

## ✅ 验证清单

| 功能模块 | 状态 | 测试项 |
|---------|------|--------|
| 富文本编辑 | ✅ | 基础格式化、标题、列表、引用 |
| 图片上传 | ✅ | 点击上传、拖拽上传、URL插入 |
| 附件管理 | ✅ | 上传、列表、删除、文件类型识别 |
| 撤销重做 | ✅ | 快捷键、工具栏按钮、历史栈 |
| 表格编辑 | ✅ | 插入、行列操作、右键菜单 |
| 任务列表 | ✅ | 勾选、嵌套、Markdown同步 |
| 代码高亮 | ✅ | 语法高亮、行内代码、代码块 |
| Markdown | ✅ | 双向转换、三种模式切换 |
| 自动保存 | ✅ | 定时保存、恢复提示、状态指示 |
| 字数统计 | ✅ | 实时统计、状态栏显示 |

---

## 🐛 故障排除

### 常见问题

**Q: 图片上传失败**
- 检查图片格式是否支持 (JPG/PNG/GIF/WebP/SVG)
- 检查图片大小是否超过 10MB
- 检查网络连接

**Q: 附件无法上传**
- 检查文件大小是否超过 50MB
- 检查文件类型是否被允许
- 查看浏览器控制台错误信息

**Q: 编辑器无法初始化**
- 检查网络连接（需要加载 CDN 资源）
- 清除浏览器缓存
- 检查浏览器控制台错误信息

**Q: Markdown 转换异常**
- 复杂的 HTML 结构可能无法完美转换
- 表格和任务列表有特殊处理规则

---

## 📝 更新日志

### 2026-03-14 - 富文本编辑器 v2.0 完成
- ✅ 集成 TipTap.js v2.2+ 富文本编辑器
- ✅ 实现三种编辑模式（富文本/预览/Markdown）
- ✅ 图片上传功能（点击/拖拽/URL）
- ✅ 附件管理功能（多格式支持）
- ✅ 撤销/重做功能（快捷键+工具栏）
- ✅ 表格编辑功能（右键菜单）
- ✅ 任务列表功能（可勾选）
- ✅ 代码高亮功能（highlight.js）
- ✅ 自动保存功能（localStorage）
- ✅ 字数统计功能（实时显示）
- ✅ Markdown 导入/导出

---

## 📄 许可证

MIT License

---

**相关文档:**
- [README.md](README.md) - 项目主文档
- [DEVELOPMENT.md](DEVELOPMENT.md) - 开发进度文档
- [COLLABORATION_FEATURES.md](COLLABORATION_FEATURES.md) - 协作功能文档
