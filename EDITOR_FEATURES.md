# 富文本编辑器功能说明

## 已实现功能

### 1. 编辑器核心
- **TipTap.js v2.2+** - 基于 ProseMirror 的高性能富文本编辑器
- **三种编辑模式** - 富文本编辑、实时预览、Markdown 源码，无缝切换
- **StarterKit** - 提供完整的基础编辑功能

### 2. 排版功能
- 6级标题 (H1-H6)
- 粗体、斜体、删除线
- 文本高亮标记
- 无序/有序列表
- 任务列表（可勾选）
- 引用块
- 水平分隔线
- 超链接

### 3. 图片上传
- **点击上传** - 通过工具栏图片按钮选择文件
- **拖拽上传** - 直接拖拽图片到编辑器区域
- **URL 插入** - 支持输入图片地址插入
- **格式支持** - JPG、PNG、GIF、WebP、SVG
- **大小限制** - 最大 10MB
- **自动压缩** - 上传时自动处理

### 4. 附件管理
- **文件上传** - 支持多种文档类型
- **格式支持** - PDF、Word、Excel、PPT、TXT、ZIP 等
- **大小限制** - 最大 50MB
- **附件列表** - 在编辑器下方显示关联附件
- **下载/删除** - 支持点击下载和删除附件

### 5. 撤销/重做
- **工具栏按钮** - 撤销(↩️) / 重做(↪️) 按钮
- **快捷键** - Ctrl+Z 撤销，Ctrl+Y 或 Ctrl+Shift+Z 重做
- **历史栈** - 支持最多 100 步操作历史
- **状态同步** - 按钮状态根据历史栈自动更新

### 6. 表格编辑
- **插入表格** - 支持自定义行列数
- **右键菜单** - 表格内右键显示操作菜单
  - 在上方/下方添加行
  - 在左侧/右侧添加列
  - 删除当前行/列
  - 切换表头行
  - 删除整个表格

### 7. 代码支持
- **行内代码** - 单个反引号包裹
- **代码块** - 三个反引号包裹
- **语法高亮** - 集成 highlight.js 自动识别语言

### 8. Markdown 支持
- **双向转换** - Turndown.js (HTML→Markdown) + Marked.js (Markdown→HTML)
- **导入功能** - 从本地 Markdown 文件导入内容
- **导出功能** - 将笔记导出为 Markdown 文件
- **语法兼容** - 支持标准 Markdown 和 GitHub Flavored Markdown

### 9. 自动保存
- **定时保存** - 每 30 秒自动保存到浏览器 localStorage
- **恢复提示** - 打开笔记时检测未保存内容并提示恢复
- **清理机制** - 保存成功后自动清除自动保存数据

## API 接口

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | /api/upload/image | 上传图片（最大 10MB） |
| POST | /api/upload/attachment | 上传附件（最大 50MB） |
| GET | /api/notes/{id}/attachments | 获取笔记附件列表 |
| PUT | /api/notes/{id}/attachments | 更新笔记附件关联 |
| DELETE | /api/attachments/{id} | 删除附件 |

## 快捷键

| 快捷键 | 功能 |
|--------|------|
| Ctrl + Z | 撤销 |
| Ctrl + Y / Ctrl + Shift + Z | 重做 |
| Ctrl + B | 粗体 |
| Ctrl + I | 斜体 |
| Ctrl + K | 插入链接 |
| Ctrl + S | 保存笔记 |

## 文件位置

- **后端**: `app/main.py` (上传 API), `app/database.py` (Attachment 模型)
- **前端**: `static/js/editor.js` (编辑器核心), `static/js/app.js` (编辑器集成)
- **样式**: `static/css/editor.css` (编辑器样式)
- **模板**: `templates/index.html` (编辑器 UI)

---
*最后更新: 2026-03-14*
