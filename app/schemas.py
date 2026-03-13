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
                "updated_at": "2026-03-13T12:30:00"
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
