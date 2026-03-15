# 🤝 AI Notes - 协作功能文档

## 功能概述

AI Notes 提供完整的实时协作功能，支持多用户同时编辑笔记、版本历史管理和智能冲突解决。

## 已实现功能

### 1. WebSocket 实时协作 ✅

#### 后端实现 (`app/websocket.py`)
- **CollaborationManager 类**: 管理所有 WebSocket 连接
  - 连接管理: 用户认证、权限检查、会话管理
  - 自动重连: 最多 5 次重连尝试
  - 心跳检测: 保持连接活跃
  - 广播机制: 用户加入/离开、内容变更、光标位置

#### 操作转换算法
```python
def transform_operation(op1: dict, op2: dict) -> tuple:
    # 处理并发编辑冲突
    # 支持 insert-insert, insert-delete, delete-delete 转换
```

#### WebSocket 端点
```
WS /ws/collaborate/{note_id}
```

#### 消息类型
- `connected` - 连接成功
- `active_users` - 活跃用户列表
- `user_joined` / `user_left` - 用户加入/离开
- `content_change` - 内容变更（操作转换）
- `cursor_update` - 光标位置更新
- `selection_update` - 选区更新
- `user_typing` - 用户正在输入
- `save_requested` - 保存请求
- `ping` / `pong` - 心跳检测

### 2. 版本历史 ✅

#### API 端点
| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/notes/{id}/versions` | 获取笔记版本历史 |
| GET | `/api/notes/{id}/versions/{version_id}` | 获取特定版本详情 |
| POST | `/api/notes/{id}/versions/{version_id}/restore` | 恢复到指定版本 |
| GET | `/api/notes/{id}/versions/compare` | 比较两个版本差异 |

#### 版本类型
- `create` - 创建笔记
- `edit` - 编辑笔记
- `restore` - 恢复版本
- `merge` - 合并更改

### 3. 协作者管理 ✅

#### API 端点
| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/notes/{id}/collaborators` | 获取协作者列表 |
| POST | `/api/notes/{id}/collaborators` | 添加协作者 |
| DELETE | `/api/notes/{id}/collaborators/{user_id}` | 移除协作者 |
| GET | `/api/notes/{id}/collaborators/active` | 获取活跃协作者 |
| GET | `/api/collaborated-notes` | 获取协作笔记列表 |

#### 权限级别
- `read` - 只读：只能查看笔记
- `write` - 读写：可以查看和编辑笔记
- `admin` - 管理员：可以编辑、管理协作者、恢复版本

### 4. 冲突解决 ✅

#### API 端点
| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/api/notes/{id}/conflict/detect` | 检测编辑冲突 |
| POST | `/api/notes/{id}/conflict/resolve` | 解决冲突 |

#### 冲突解决方式
1. **使用我的版本** - 保留当前用户的修改
2. **使用服务器版本** - 放弃本地修改，使用服务器最新版本
3. **合并更改** - 手动合并两个版本的内容

## 前端实现

### 协作管理器 (`static/js/collaboration.js`)

#### CollaborationManager 类
```javascript
class CollaborationManager {
    // WebSocket 连接管理
    async connect(noteId)
    async disconnect()
    
    // 消息发送
    sendContentChange(operation)
    sendCursorUpdate(position, selectionStart, selectionEnd)
    sendTypingStart() / sendTypingEnd()
    
    // 操作转换
    applyRemoteOperation(operation)
    
    // UI 更新
    updateActiveUsersUI()
    showCollaborationStatus(status, type)
}
```

#### VersionHistoryManager 类
```javascript
class VersionHistoryManager {
    async loadVersions(noteId)
    renderVersionsList()
    async viewVersion(versionId)
    async restoreVersion(versionId)
}
```

#### CollaboratorsManager 类
```javascript
class CollaboratorsManager {
    async loadCollaborators(noteId)
    renderCollaboratorsList()
    async addCollaborator(username, permission)
    async removeCollaborator(userId)
}
```

#### ConflictResolutionManager 类
```javascript
class ConflictResolutionManager {
    async detectConflict(noteId, baseVersion)
    showConflictModal(conflictData, onResolve)
    async resolveConflict(resolution, onResolve)
}
```

## 数据库模型

### NoteVersion (版本历史)
```python
class NoteVersion(Base):
    id: int
    note_id: int
    user_id: int
    version_number: int
    title: str
    content: str
    summary: str
    tags: str
    change_summary: str
    change_type: str  # create, edit, restore, merge
    created_at: datetime
```

### NoteCollaborator (协作者)
```python
class NoteCollaborator(Base):
    id: int
    note_id: int
    user_id: int
    permission: str  # read, write, admin
    added_by: int
    created_at: datetime
    updated_at: datetime
```

### CollaborationSession (协作会话)
```python
class CollaborationSession(Base):
    id: int
    note_id: int
    user_id: int
    session_id: str
    websocket_id: str
    is_active: bool
    cursor_position: int
    selection_start: int
    selection_end: int
    last_activity: datetime
```

## 使用指南

### 实时协作
1. 在编辑笔记页面点击"👥 协作"按钮
2. 输入其他用户的用户名并选择权限级别
3. 协作者打开笔记后将自动加入实时协作会话
4. 实时查看其他协作者的光标位置和编辑状态

### 版本历史
1. 点击"📜 版本"按钮查看笔记的版本历史
2. 每个保存操作都会自动创建一个新版本
3. 可以查看任意版本的内容预览
4. 支持恢复到任意历史版本（当前内容会被保存为新版本）

### 冲突解决
1. 当多个用户同时编辑并保存时，系统会自动检测冲突
2. 冲突解决选项：
   - 使用我的版本
   - 使用服务器版本
   - 合并更改

## 文件清单

### 后端文件
- `app/websocket.py` - WebSocket 实时协作管理器 (491 行)
- `app/database.py` - 数据库模型和 CRUD 操作 (1461 行)
- `app/main.py` - API 端点 (2000+ 行)
- `app/schemas.py` - Pydantic 数据模型 (866 行)

### 前端文件
- `static/js/collaboration.js` - 前端协作管理器 (715 行)
- `static/js/app.js` - 应用主逻辑 (1935 行)
- `static/css/style.css` - 样式文件 (2000+ 行，包含完整协作样式)
- `templates/index.html` - 主页面模板 (655 行，包含协作 UI)

## API 统计

- HTTP API 端点总数: 49 个
- WebSocket 端点: 1 个
- 协作相关 API: 12 个
  - 版本历史 API: 4 个
  - 协作者管理 API: 4 个
  - 冲突解决 API: 2 个
  - 其他: 2 个
