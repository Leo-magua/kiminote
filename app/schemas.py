"""
Pydantic schemas for AI Notes API
Provides request/response models and examples for API documentation
"""
from typing import List, Optional
from pydantic import BaseModel, Field
from datetime import datetime


# ============== Base Models ==============

class UserBase(BaseModel):
    """Base user schema"""
    username: str = Field(..., min_length=3, max_length=50, description="用户名")
    email: Optional[str] = Field(None, max_length=100, description="邮箱地址")


class NoteBase(BaseModel):
    """Base note schema"""
    title: str = Field(..., min_length=1, max_length=200, description="笔记标题")
    content: str = Field(..., description="笔记内容 (支持 Markdown)")


# ============== Request Models ==============

class UserRegisterRequest(BaseModel):
    """用户注册请求"""
    username: str = Field(..., min_length=3, max_length=50, description="用户名，至少3个字符")
    email: Optional[str] = Field(None, max_length=100, description="邮箱地址（可选）")
    password: str = Field(..., min_length=6, description="密码，至少6个字符")
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "username": "john_doe",
                "email": "john@example.com",
                "password": "secure_password"
            }
        }
    }


class UserLoginRequest(BaseModel):
    """用户登录请求"""
    username: str = Field(..., description="用户名")
    password: str = Field(..., description="密码")
    remember: bool = Field(False, description="是否记住登录状态（30天 vs 7天）")
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "username": "john_doe",
                "password": "secure_password",
                "remember": True
            }
        }
    }


class NoteCreateRequest(BaseModel):
    """创建笔记请求"""
    title: str = Field(..., min_length=1, max_length=200, description="笔记标题")
    content: str = Field(..., description="笔记内容 (支持 Markdown)")
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "title": "我的第一篇笔记",
                "content": "# 欢迎使用 AI Notes\n\n这是一个支持 **Markdown** 的笔记应用。"
            }
        }
    }


class NoteUpdateRequest(BaseModel):
    """更新笔记请求"""
    title: Optional[str] = Field(None, min_length=1, max_length=200, description="笔记标题")
    content: Optional[str] = Field(None, description="笔记内容 (支持 Markdown)")
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "title": "更新后的标题",
                "content": "更新后的内容"
            }
        }
    }


class SmartSearchRequest(BaseModel):
    """智能搜索请求"""
    query: str = Field(..., min_length=1, max_length=500, description="搜索查询（自然语言）")
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "query": "关于项目管理的笔记"
            }
        }
    }


class EnhanceTextRequest(BaseModel):
    """文本增强请求"""
    content: str = Field(..., min_length=1, max_length=10000, description="需要增强的文本内容")
    instruction: str = Field("improve", description="增强方式: improve(改进), simplify(简化), professional(专业化), creative(创意), expand(扩展)")
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "content": "这个方案不错，可以试试看。",
                "instruction": "professional"
            }
        }
    }


class MarkdownPreviewRequest(BaseModel):
    """Markdown 预览请求"""
    content: str = Field(..., description="Markdown 内容")
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "content": "# 标题\n\n**粗体文本** 和 *斜体文本*"
            }
        }
    }


class ShareCreateRequest(BaseModel):
    """创建分享请求"""
    note_id: int = Field(..., description="要分享的笔记ID")
    permission: str = Field("public", description="分享权限: public(公开), password(密码保护), private(私密)")
    password: Optional[str] = Field(None, min_length=4, max_length=50, description="访问密码（仅password权限时需要）")
    expires_days: Optional[int] = Field(None, ge=1, le=365, description="过期天数（可选，1-365天）")
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "note_id": 1,
                "permission": "public",
                "password": None,
                "expires_days": 7
            }
        }
    }


class ShareVerifyRequest(BaseModel):
    """验证分享密码请求"""
    password: str = Field(..., min_length=1, description="访问密码")
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "password": "123456"
            }
        }
    }


class ShareUpdateRequest(BaseModel):
    """更新分享请求"""
    permission: Optional[str] = Field(None, description="分享权限: public, password, private")
    password: Optional[str] = Field(None, description="新密码（设置为null则移除密码）")
    is_active: Optional[bool] = Field(None, description="是否激活")
    expires_days: Optional[int] = Field(None, ge=1, le=365, description="新的过期天数（从当前时间开始计算）")
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "permission": "password",
                "password": "newpassword",
                "is_active": True
            }
        }
    }


# ============== Collaboration Request Models ==============

class AddCollaboratorRequest(BaseModel):
    """添加协作者请求"""
    username: str = Field(..., min_length=3, max_length=50, description="协作者用户名")
    permission: str = Field("write", description="权限级别: read(只读), write(读写), admin(管理员)")
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "username": "collaborator_user",
                "permission": "write"
            }
        }
    }


class UpdateCollaboratorRequest(BaseModel):
    """更新协作者权限请求"""
    permission: str = Field(..., description="权限级别: read, write, admin")
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "permission": "admin"
            }
        }
    }


class RestoreVersionRequest(BaseModel):
    """恢复版本请求"""
    version_id: int = Field(..., description="要恢复的版本ID")
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "version_id": 5
            }
        }
    }


class ConflictResolutionRequest(BaseModel):
    """冲突解决请求"""
    base_version: int = Field(..., description="基础版本号")
    resolution: str = Field(..., description="解决方式: mine(使用我的), theirs(使用对方的), merge(合并)")
    merged_content: Optional[str] = Field(None, description="合并后的内容（当 resolution 为 merge 时需要）")
    merged_title: Optional[str] = Field(None, description="合并后的标题（可选）")
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "base_version": 3,
                "resolution": "merge",
                "merged_content": "合并后的笔记内容",
                "merged_title": "合并后的标题"
            }
        }
    }


class WebSocketAuthRequest(BaseModel):
    """WebSocket 认证请求"""
    token: str = Field(..., description="访问令牌 (JWT)")
    note_id: int = Field(..., description="要协作编辑的笔记ID")


class CursorUpdateRequest(BaseModel):
    """光标位置更新请求"""
    position: int = Field(..., ge=0, description="光标位置")
    selection_start: Optional[int] = Field(None, ge=0, description="选区开始位置")
    selection_end: Optional[int] = Field(None, ge=0, description="选区结束位置")


class OperationRequest(BaseModel):
    """协同编辑操作请求"""
    type: str = Field(..., description="操作类型: insert(插入), delete(删除), retain(保留)")
    position: int = Field(..., ge=0, description="操作位置")
    content: Optional[str] = Field(None, description="插入的内容（仅 insert 类型需要）")
    length: Optional[int] = Field(None, ge=0, description="删除的长度（仅 delete 类型需要）")
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "type": "insert",
                "position": 10,
                "content": "插入的文本"
            }
        }
    }


# ============== Response Models ==============

class UserResponse(BaseModel):
    """用户信息响应"""
    id: int = Field(..., description="用户ID")
    username: str = Field(..., description="用户名")
    email: Optional[str] = Field(None, description="邮箱地址")
    is_active: bool = Field(..., description="账户是否激活")
    created_at: Optional[str] = Field(None, description="创建时间 (ISO 8601 格式)")
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "id": 1,
                "username": "john_doe",
                "email": "john@example.com",
                "is_active": True,
                "created_at": "2026-03-13T12:00:00"
            }
        }
    }


class NoteResponse(BaseModel):
    """笔记详情响应"""
    id: int = Field(..., description="笔记ID")
    user_id: int = Field(..., description="所属用户ID")
    title: str = Field(..., description="笔记标题")
    content: str = Field(..., description="笔记内容")
    summary: Optional[str] = Field(None, description="AI 生成的摘要")
    tags: List[str] = Field(default_factory=list, description="标签列表")
    created_at: Optional[str] = Field(None, description="创建时间 (ISO 8601 格式)")
    updated_at: Optional[str] = Field(None, description="更新时间 (ISO 8601 格式)")
    current_version: int = Field(1, description="当前版本号")
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "id": 1,
                "user_id": 1,
                "title": "我的第一篇笔记",
                "content": "# 欢迎使用 AI Notes",
                "summary": "这是一篇欢迎笔记，介绍了 AI Notes 的基本功能。",
                "tags": ["欢迎", "介绍"],
                "created_at": "2026-03-13T12:00:00",
                "updated_at": "2026-03-13T12:30:00",
                "current_version": 5
            }
        }
    }


class NoteSummaryResponse(BaseModel):
    """笔记摘要生成响应"""
    summary: str = Field(..., description="生成的摘要")
    note: NoteResponse = Field(..., description="更新后的笔记信息")


class NoteTagsResponse(BaseModel):
    """笔记标签生成响应"""
    tags: List[str] = Field(..., description="生成的标签列表")
    note: NoteResponse = Field(..., description="更新后的笔记信息")


class TagsListResponse(BaseModel):
    """标签列表响应"""
    tags: List[str] = Field(..., description="所有标签列表")
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "tags": ["工作", "学习", "生活", "项目", "灵感"]
            }
        }
    }


class SearchResultItem(NoteResponse):
    """搜索结果项"""
    search_relevance: float = Field(..., ge=0, le=1, description="搜索相关度 (0-1)")
    search_reason: str = Field(..., description="相关原因说明")


class SmartSearchResponse(BaseModel):
    """智能搜索响应"""
    query: str = Field(..., description="搜索查询")
    results: List[SearchResultItem] = Field(..., description="搜索结果列表")
    total: int = Field(..., ge=0, description="结果总数")
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "query": "关于项目管理的笔记",
                "results": [],
                "total": 0
            }
        }
    }


class EnhanceTextResponse(BaseModel):
    """文本增强响应"""
    original: str = Field(..., description="原始文本")
    enhanced: str = Field(..., description="增强后的文本")
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "original": "这个方案不错，可以试试看。",
                "enhanced": "该方案具有较高的可行性，建议进一步深入评估并考虑实施。"
            }
        }
    }


class MarkdownPreviewResponse(BaseModel):
    """Markdown 预览响应"""
    html: str = Field(..., description="转换后的 HTML")
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "html": "<h1>标题</h1>\n<p><strong>粗体文本</strong> 和 <em>斜体文本</em></p>"
            }
        }
    }


class StatsResponse(BaseModel):
    """应用统计响应"""
    total_notes: int = Field(..., ge=0, description="笔记总数")
    ai_available: bool = Field(..., description="AI 服务是否可用")
    model: Optional[str] = Field(None, description="当前使用的 AI 模型")
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "total_notes": 42,
                "ai_available": True,
                "model": "gpt-3.5-turbo"
            }
        }
    }


class MessageResponse(BaseModel):
    """通用消息响应"""
    message: str = Field(..., description="消息内容")
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "message": "操作成功"
            }
        }
    }


class LoginResponse(BaseModel):
    """登录响应"""
    message: str = Field(..., description="登录结果消息")
    user: UserResponse = Field(..., description="用户信息")
    access_token: str = Field(..., description="访问令牌 (JWT)")
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "message": "登录成功",
                "user": {
                    "id": 1,
                    "username": "john_doe",
                    "email": "john@example.com",
                    "is_active": True
                },
                "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
            }
        }
    }


class RegisterResponse(BaseModel):
    """注册响应"""
    message: str = Field(..., description="注册结果消息")
    user: UserResponse = Field(..., description="用户信息")
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "message": "注册成功",
                "user": {
                    "id": 1,
                    "username": "john_doe",
                    "email": "john@example.com",
                    "is_active": True
                }
            }
        }
    }


class ErrorResponse(BaseModel):
    """错误响应"""
    detail: str = Field(..., description="错误详情")
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "detail": "请求参数错误"
            }
        }
    }


class ShareResponse(BaseModel):
    """分享信息响应"""
    id: int = Field(..., description="分享ID")
    share_token: str = Field(..., description="分享令牌（短链接码）")
    note_id: int = Field(..., description="笔记ID")
    user_id: int = Field(..., description="创建者用户ID")
    permission: str = Field(..., description="分享权限")
    has_password: bool = Field(..., description="是否有密码保护")
    expires_at: Optional[str] = Field(None, description="过期时间")
    access_count: int = Field(..., description="访问次数")
    created_at: Optional[str] = Field(None, description="创建时间")
    updated_at: Optional[str] = Field(None, description="更新时间")
    is_active: bool = Field(..., description="是否激活")
    is_expired: bool = Field(..., description="是否已过期")
    share_url: Optional[str] = Field(None, description="完整分享链接")
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "id": 1,
                "share_token": "aB3xK9mP",
                "note_id": 1,
                "user_id": 1,
                "permission": "public",
                "has_password": False,
                "expires_at": "2026-03-20T12:00:00",
                "access_count": 5,
                "created_at": "2026-03-13T12:00:00",
                "updated_at": "2026-03-13T12:00:00",
                "is_active": True,
                "is_expired": False,
                "share_url": "http://localhost:8000/s/aB3xK9mP"
            }
        }
    }


class ShareListResponse(BaseModel):
    """分享列表响应"""
    shares: List[ShareResponse] = Field(..., description="分享列表")
    total: int = Field(..., description="总数")


class ShareNoteResponse(BaseModel):
    """通过分享访问笔记的响应"""
    note: NoteResponse = Field(..., description="笔记内容")
    share_token: str = Field(..., description="分享令牌")
    permission: str = Field(..., description="分享权限")
    access_count: int = Field(..., description="访问次数")
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "note": {
                    "id": 1,
                    "user_id": 1,
                    "title": "我的笔记",
                    "content": "# 笔记内容",
                    "summary": None,
                    "tags": [],
                    "created_at": "2026-03-13T12:00:00",
                    "updated_at": "2026-03-13T12:00:00"
                },
                "share_token": "aB3xK9mP",
                "permission": "public",
                "access_count": 5
            }
        }
    }


class ShareVerifyResponse(BaseModel):
    """分享密码验证响应"""
    valid: bool = Field(..., description="密码是否正确")
    message: str = Field(..., description="提示信息")
    share_url: Optional[str] = Field(None, description="验证通过后的访问链接")


# ============== Collaboration Response Models ==============

class VersionResponse(BaseModel):
    """笔记版本响应"""
    id: int = Field(..., description="版本ID")
    note_id: int = Field(..., description="笔记ID")
    user_id: int = Field(..., description="创建者用户ID")
    version_number: int = Field(..., description="版本号")
    title: str = Field(..., description="版本标题")
    content: str = Field(..., description="版本内容")
    summary: Optional[str] = Field(None, description="摘要")
    tags: List[str] = Field(default_factory=list, description="标签列表")
    change_summary: Optional[str] = Field(None, description="变更摘要")
    change_type: str = Field(..., description="变更类型")
    created_at: Optional[str] = Field(None, description="创建时间")
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "id": 1,
                "note_id": 1,
                "user_id": 1,
                "version_number": 3,
                "title": "笔记标题 v3",
                "content": "笔记内容...",
                "summary": "摘要",
                "tags": ["标签1"],
                "change_summary": "更新了内容",
                "change_type": "edit",
                "created_at": "2026-03-13T12:00:00"
            }
        }
    }


class VersionListResponse(BaseModel):
    """版本列表响应"""
    versions: List[VersionResponse] = Field(..., description="版本列表")
    total: int = Field(..., description="总数")
    note_id: int = Field(..., description="笔记ID")
    current_version: int = Field(..., description="当前版本号")


class VersionComparisonResponse(BaseModel):
    """版本比较响应"""
    version1: VersionResponse = Field(..., description="版本1")
    version2: VersionResponse = Field(..., description="版本2")
    title_changed: bool = Field(..., description="标题是否变更")
    content_changed: bool = Field(..., description="内容是否变更")
    tags_changed: bool = Field(..., description="标签是否变更")


class CollaboratorResponse(BaseModel):
    """协作者响应"""
    id: int = Field(..., description="协作者记录ID")
    note_id: int = Field(..., description="笔记ID")
    user_id: int = Field(..., description="协作者用户ID")
    username: Optional[str] = Field(None, description="协作者用户名")
    email: Optional[str] = Field(None, description="协作者邮箱")
    permission: str = Field(..., description="权限级别")
    added_by: int = Field(..., description="添加者用户ID")
    created_at: Optional[str] = Field(None, description="创建时间")
    updated_at: Optional[str] = Field(None, description="更新时间")
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "id": 1,
                "note_id": 1,
                "user_id": 2,
                "username": "collaborator",
                "email": "collab@example.com",
                "permission": "write",
                "added_by": 1,
                "created_at": "2026-03-13T12:00:00",
                "updated_at": "2026-03-13T12:00:00"
            }
        }
    }


class CollaboratorListResponse(BaseModel):
    """协作者列表响应"""
    collaborators: List[CollaboratorResponse] = Field(..., description="协作者列表")
    note_id: int = Field(..., description="笔记ID")
    owner_id: int = Field(..., description="笔记所有者ID")


class CollaborationSessionResponse(BaseModel):
    """协作会话响应"""
    session_id: str = Field(..., description="会话ID")
    note_id: int = Field(..., description="笔记ID")
    user_id: int = Field(..., description="用户ID")
    username: Optional[str] = Field(None, description="用户名")
    is_active: bool = Field(..., description="是否活跃")
    cursor_position: Optional[int] = Field(None, description="光标位置")
    selection_start: Optional[int] = Field(None, description="选区开始")
    selection_end: Optional[int] = Field(None, description="选区结束")
    last_activity: Optional[str] = Field(None, description="最后活动时间")
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "session_id": "550e8400-e29b-41d4-a716-446655440000",
                "note_id": 1,
                "user_id": 2,
                "username": "collaborator",
                "is_active": True,
                "cursor_position": 150,
                "last_activity": "2026-03-13T12:00:00"
            }
        }
    }


class ActiveCollaboratorsResponse(BaseModel):
    """活跃协作者响应"""
    collaborators: List[CollaborationSessionResponse] = Field(..., description="活跃协作者列表")
    note_id: int = Field(..., description="笔记ID")


class ConflictDetectionResponse(BaseModel):
    """冲突检测响应"""
    has_conflict: bool = Field(..., description="是否存在冲突")
    base_version: Optional[VersionResponse] = Field(None, description="基础版本")
    current_version: Optional[VersionResponse] = Field(None, description="当前版本")
    title_changed: bool = Field(False, description="标题是否变更")
    content_changed: bool = Field(False, description="内容是否变更")
    tags_changed: bool = Field(False, description="标签是否变更")
    error: Optional[str] = Field(None, description="错误信息")


class WebSocketMessage(BaseModel):
    """WebSocket 消息"""
    type: str = Field(..., description="消息类型")
    data: dict = Field(default_factory=dict, description="消息数据")
    timestamp: str = Field(..., description="时间戳")
    sender_id: Optional[int] = Field(None, description="发送者用户ID")
    sender_username: Optional[str] = Field(None, description="发送者用户名")


class WebSocketAuthResponse(BaseModel):
    """WebSocket 认证响应"""
    success: bool = Field(..., description="是否认证成功")
    message: str = Field(..., description="消息")
    session_id: Optional[str] = Field(None, description="协作会话ID")
    note_id: Optional[int] = Field(None, description="笔记ID")


# ============== Statistics Models ==============

class ActivityItem(BaseModel):
    """每日活动统计项"""
    date: Optional[str] = Field(None, description="日期 (ISO 8601 格式)")
    notes_created: int = Field(..., ge=0, description="创建的笔记数量")
    characters_written: int = Field(..., ge=0, description="写入的字符数")


class HourlyDistributionItem(BaseModel):
    """小时分布统计项"""
    hour: int = Field(..., ge=0, le=23, description="小时 (0-23)")
    count: int = Field(..., ge=0, description="笔记数量")


class WeekdayDistributionItem(BaseModel):
    """星期分布统计项"""
    day: str = Field(..., description="星期名称")
    count: int = Field(..., ge=0, description="笔记数量")


class DetailedStatsResponse(BaseModel):
    """详细统计数据响应"""
    total_notes: int = Field(..., ge=0, description="笔记总数")
    total_words: int = Field(..., ge=0, description="总词数")
    total_characters: int = Field(..., ge=0, description="总字符数")
    avg_words_per_note: float = Field(..., description="平均每笔记词数")
    avg_characters_per_note: float = Field(..., description="平均每笔记字符数")
    notes_this_week: int = Field(..., ge=0, description="本周创建笔记数")
    notes_this_month: int = Field(..., ge=0, description="本月创建笔记数")
    current_streak: int = Field(..., ge=0, description="当前连续写作天数")
    first_note_date: Optional[str] = Field(None, description="第一篇笔记创建时间")
    activity_by_date: List[ActivityItem] = Field(default_factory=list, description="最近30天活动统计")
    hourly_distribution: List[HourlyDistributionItem] = Field(default_factory=list, description="24小时写作分布")
    weekday_distribution: List[WeekdayDistributionItem] = Field(default_factory=list, description="星期分布统计")
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "total_notes": 42,
                "total_words": 15000,
                "total_characters": 45000,
                "avg_words_per_note": 357.1,
                "avg_characters_per_note": 1071.4,
                "notes_this_week": 5,
                "notes_this_month": 18,
                "current_streak": 7,
                "first_note_date": "2026-01-15T08:30:00",
                "activity_by_date": [
                    {"date": "2026-03-13", "notes_created": 2, "characters_written": 1200}
                ],
                "hourly_distribution": [
                    {"hour": 9, "count": 5},
                    {"hour": 14, "count": 8}
                ],
                "weekday_distribution": [
                    {"day": "周一", "count": 10},
                    {"day": "周二", "count": 8}
                ]
            }
        }
    }


class DailyStatsItem(BaseModel):
    """每日统计数据项"""
    date: Optional[str] = Field(None, description="日期 (ISO 8601 格式)")
    notes_created: int = Field(..., ge=0, description="创建的笔记数量")
    total_characters: int = Field(..., ge=0, description="总字符数")
    avg_characters: float = Field(..., description="平均字符数")


class DailyStatsResponse(BaseModel):
    """每日统计响应"""
    days: int = Field(..., description="统计天数")
    stats: List[DailyStatsItem] = Field(..., description="每日统计数据")
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "days": 7,
                "stats": [
                    {"date": "2026-03-13", "notes_created": 2, "total_characters": 1200, "avg_characters": 600}
                ]
            }
        }
    }
