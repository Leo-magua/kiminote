"""
FastAPI main application for AI Notes
"""
import json
import markdown
from datetime import datetime
from typing import List, Optional
from fastapi import FastAPI, Depends, HTTPException, Query, Request, Response, status, WebSocket
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, JSONResponse, FileResponse, RedirectResponse
from sqlalchemy.orm import Session

# Markdown extensions configuration
try:
    from markdown.extensions.codehilite import CodeHiliteExtension
    CODE_HIGHLIGHT_AVAILABLE = True
except ImportError:
    CODE_HIGHLIGHT_AVAILABLE = False

# Configure Markdown with extensions
MD_EXTENSIONS = [
    'fenced_code',      # GitHub-style fenced code blocks
    'tables',           # Tables support
    'toc',              # Table of contents
    'nl2br',            # Convert newlines to <br>
    'sane_lists',       # Better list handling
    'md_in_html',       # Markdown inside HTML blocks
]

# Add code highlighting if available
if CODE_HIGHLIGHT_AVAILABLE:
    MD_EXTENSIONS.append(
        CodeHiliteExtension(
            linenums=False,
            guess_lang=True,
            use_pygments=True,
            noclasses=False,
            pygments_style='github'
        )
    )

# Create markdown instance with all extensions
md_converter = markdown.Markdown(extensions=MD_EXTENSIONS)

from app.config import (
    APP_NAME, APP_VERSION, EXPORTS_DIR, SESSION_COOKIE_NAME,
    UPLOADS_DIR, MAX_UPLOAD_SIZE, ALLOWED_IMAGE_TYPES, ALLOWED_DOCUMENT_TYPES
)
from app.database import (
    get_db, create_note, get_note, get_notes, update_note, 
    delete_note, get_all_notes_for_export, get_notes_count, get_all_tags,
    create_user, get_user_by_username, get_user_by_email,
    create_share, get_share_by_token, get_note_shares, get_shares_by_note, get_all_user_shares,
    verify_share_access, revoke_share, revoke_all_shares_for_note,
    update_share, delete_share, verify_share_password, increment_share_access_count,
    Share, get_notes_statistics, get_daily_writing_stats,
    create_attachment, get_attachment, get_note_attachments, delete_attachment
)
from app.auth import (
    get_password_hash, authenticate_user, create_user_session,
    get_current_user, invalidate_session, get_token_from_request
)
from app.ai_service import ai_service

# Import Pydantic schemas
from app import schemas

# Create FastAPI app with enhanced metadata
app = FastAPI(
    title=APP_NAME,
    version=APP_VERSION,
    description="""
    AI-powered note-taking application with intelligent features.
    
    ## Features
    
    * 📝 **Note Management** - Create, edit, delete notes with Markdown support
    * 🤖 **AI Integration** - Auto-summary, smart tags, semantic search
    * 🔐 **User Authentication** - Secure JWT-based authentication
    * 📤 **Export** - Export notes to JSON and Markdown formats
    
    ## Authentication
    
    This API uses JWT token-based authentication. You can authenticate by:
    1. Cookie: Session token is stored in HTTP-only cookie automatically
    2. Bearer Token: Include `Authorization: Bearer <token>` header
    
    ## Rate Limits
    
    AI-related endpoints have rate limiting based on your API provider.
    """,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_tags=[
        {"name": "Authentication", "description": "用户注册、登录、登出等认证操作"},
        {"name": "Notes", "description": "笔记的增删改查操作"},
        {"name": "Upload", "description": "文件上传功能（图片、附件）"},
        {"name": "Shares", "description": "笔记分享功能（创建分享、访问分享、管理分享）"},
        {"name": "Collaboration", "description": "协作功能（版本历史、协作者管理、冲突解决）"},
        {"name": "AI Features", "description": "AI 驱动的智能功能（摘要、标签、搜索、增强）"},
        {"name": "Export", "description": "数据导出功能"},
        {"name": "Utilities", "description": "工具类接口（统计、标签列表、预览等）"},
        {"name": "Web", "description": "Web 页面路由"},
    ]
)

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")

# Templates
templates = Jinja2Templates(directory="templates")


# ============== Web Routes ==============

@app.get("/", response_class=HTMLResponse, tags=["Web"], include_in_schema=False)
async def index(request: Request, current_user: dict = Depends(get_current_user)):
    """Main page - requires authentication"""
    return templates.TemplateResponse("index.html", {
        "request": request,
        "app_name": APP_NAME,
        "ai_available": ai_service.is_available(),
        "user": current_user
    })


@app.get("/login", response_class=HTMLResponse, tags=["Web"], include_in_schema=False)
async def login_page(request: Request):
    """Login page"""
    return templates.TemplateResponse("login.html", {
        "request": request,
        "app_name": APP_NAME
    })


@app.get("/register", response_class=HTMLResponse, tags=["Web"], include_in_schema=False)
async def register_page(request: Request):
    """Register page"""
    return templates.TemplateResponse("register.html", {
        "request": request,
        "app_name": APP_NAME
    })


# ============== Auth API ==============

@app.post(
    "/api/auth/register",
    response_model=schemas.RegisterResponse,
    tags=["Authentication"],
    summary="用户注册",
    description="注册一个新用户账户。用户名至少3个字符，密码至少6个字符。",
    responses={
        200: {"description": "注册成功", "model": schemas.RegisterResponse},
        400: {"description": "参数错误（用户名太短、密码太短、用户名或邮箱已存在）", "model": schemas.ErrorResponse},
    }
)
async def register(
    request: Request,
    user_data: schemas.UserRegisterRequest,
    db: Session = Depends(get_db)
):
    """Register a new user"""
    username = user_data.username.strip()
    email = user_data.email.strip() if user_data.email else None
    password = user_data.password
    
    # Validation
    if not username or len(username) < 3:
        raise HTTPException(status_code=400, detail="用户名至少需要3个字符")
    
    if not password or len(password) < 6:
        raise HTTPException(status_code=400, detail="密码至少需要6个字符")
    
    # Check if username exists
    if get_user_by_username(db, username):
        raise HTTPException(status_code=400, detail="用户名已存在")
    
    # Check if email exists (if provided)
    if email and get_user_by_email(db, email):
        raise HTTPException(status_code=400, detail="邮箱已被使用")
    
    # Create user
    hashed_password = get_password_hash(password)
    user = create_user(db, username=username, email=email, hashed_password=hashed_password)
    
    return {
        "message": "注册成功",
        "user": user.to_dict()
    }


@app.post(
    "/api/auth/login",
    response_model=schemas.LoginResponse,
    tags=["Authentication"],
    summary="用户登录",
    description="使用用户名和密码登录，成功后返回 JWT token 并设置 cookie。",
    responses={
        200: {"description": "登录成功", "model": schemas.LoginResponse},
        401: {"description": "用户名或密码错误", "model": schemas.ErrorResponse},
    }
)
async def login(
    request: Request,
    response: Response,
    credentials: schemas.UserLoginRequest,
    db: Session = Depends(get_db)
):
    """Login user and create session"""
    username = credentials.username.strip()
    password = credentials.password
    remember = credentials.remember
    
    # Authenticate
    user = authenticate_user(db, username, password)
    if not user:
        raise HTTPException(status_code=401, detail="用户名或密码错误")
    
    # Get client info
    ip_address = request.client.host if request.client else None
    user_agent = request.headers.get("user-agent")
    
    # Create session
    token = create_user_session(db, user_id=user["id"], ip_address=ip_address, user_agent=user_agent)
    
    # Set cookie
    max_age = 30 * 24 * 60 * 60 if remember else 7 * 24 * 60 * 60  # 30 days or 7 days
    response.set_cookie(
        key=SESSION_COOKIE_NAME,
        value=token,
        httponly=True,
        secure=False,  # Set to True in production with HTTPS
        samesite="lax",
        max_age=max_age
    )
    
    return {
        "message": "登录成功",
        "user": user,
        "access_token": token
    }


@app.post(
    "/api/auth/logout",
    response_model=schemas.MessageResponse,
    tags=["Authentication"],
    summary="用户登出",
    description="登出当前用户并使会话失效。"
)
async def logout(
    request: Request,
    response: Response,
    db: Session = Depends(get_db)
):
    """Logout user and invalidate session"""
    token = get_token_from_request(request)
    if token:
        invalidate_session(db, token)
    
    # Clear cookie
    response.delete_cookie(key=SESSION_COOKIE_NAME)
    
    return {"message": "已退出登录"}


@app.get(
    "/api/auth/me",
    response_model=schemas.UserResponse,
    tags=["Authentication"],
    summary="获取当前用户信息",
    description="获取当前登录用户的详细信息。",
    responses={
        200: {"description": "成功获取用户信息", "model": schemas.UserResponse},
        401: {"description": "未认证", "model": schemas.ErrorResponse},
    }
)
async def get_me(current_user: dict = Depends(get_current_user)):
    """Get current user info"""
    return current_user


# ============== API Routes ==============

@app.get(
    "/api/stats",
    response_model=schemas.StatsResponse,
    tags=["Utilities"],
    summary="获取应用统计",
    description="获取当前用户的笔记数量、AI 服务状态等统计信息。"
)
async def get_stats(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Get application statistics"""
    return {
        "total_notes": get_notes_count(db, user_id=current_user["id"]),
        "ai_available": ai_service.is_available(),
        "model": ai_service.model if ai_service.is_available() else None
    }


@app.get(
    "/api/tags",
    response_model=schemas.TagsListResponse,
    tags=["Utilities"],
    summary="获取所有标签",
    description="获取当前用户的所有笔记标签列表（去重、排序）。"
)
async def api_get_all_tags(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Get all unique tags for current user"""
    return {"tags": get_all_tags(db, user_id=current_user["id"])}


@app.get(
    "/api/stats/detailed",
    response_model=schemas.DetailedStatsResponse,
    tags=["Utilities"],
    summary="获取详细统计数据",
    description="""
    获取用户的详细写作统计数据，包括：
    
    - 笔记数量统计（总数、本周、本月）
    - 字数统计（总词数、总字符数、平均值）
    - 写作习惯分析（24小时分布、星期分布）
    - 连续写作天数（streak）
    - 最近30天活动记录
    """
)
async def get_detailed_stats(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Get detailed writing statistics for current user"""
    stats = get_notes_statistics(db, user_id=current_user["id"])
    return stats


@app.get(
    "/api/stats/daily",
    response_model=schemas.DailyStatsResponse,
    tags=["Utilities"],
    summary="获取每日统计",
    description="获取指定天数内的每日写作统计数据。"
)
async def get_daily_stats(
    days: int = Query(7, ge=1, le=90, description="统计天数（1-90天）"),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Get daily writing statistics for the specified number of days"""
    stats = get_daily_writing_stats(db, user_id=current_user["id"], days=days)
    return {"days": days, "stats": stats}


# ============== Notes CRUD API ==============

@app.get(
    "/api/notes",
    response_model=List[schemas.NoteResponse],
    tags=["Notes"],
    summary="获取笔记列表",
    description="获取当前用户的所有笔记，支持分页和搜索。",
    responses={
        200: {
            "description": "笔记列表",
            "content": {
                "application/json": {
                    "example": [
                        {
                            "id": 1,
                            "user_id": 1,
                            "title": "我的笔记",
                            "content": "笔记内容",
                            "summary": "摘要",
                            "tags": ["标签1"],
                            "created_at": "2026-03-13T12:00:00",
                            "updated_at": "2026-03-13T12:00:00"
                        }
                    ]
                }
            }
        },
        401: {"description": "未认证", "model": schemas.ErrorResponse},
    }
)
async def list_notes(
    skip: int = Query(0, ge=0, description="跳过的记录数（分页）"),
    limit: int = Query(100, ge=1, le=1000, description="返回的最大记录数"),
    search: Optional[str] = Query(None, description="搜索关键词（标题、内容、标签）"),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """List all notes for current user with optional search"""
    notes = get_notes(db, user_id=current_user["id"], skip=skip, limit=limit, search=search)
    return [note.to_dict() for note in notes]


@app.post(
    "/api/notes",
    response_model=schemas.NoteResponse,
    tags=["Notes"],
    summary="创建笔记",
    description="""
    创建新笔记。如果 AI 服务可用，会自动生成摘要和标签。
    
    - 标题不能为空
    - 内容支持 Markdown 格式
    """,
    responses={
        200: {"description": "创建成功", "model": schemas.NoteResponse},
        400: {"description": "标题不能为空", "model": schemas.ErrorResponse},
        401: {"description": "未认证", "model": schemas.ErrorResponse},
    }
)
async def create_new_note(
    note_data: schemas.NoteCreateRequest,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Create a new note"""
    title = note_data.title.strip()
    content = note_data.content.strip()
    
    if not title:
        raise HTTPException(status_code=400, detail="Title is required")
    
    # Generate AI summary and tags if AI is available
    summary = None
    tags = None
    
    if ai_service.is_available():
        # Generate summary in background (non-blocking for response)
        try:
            summary = ai_service.generate_summary(content)
        except Exception as e:
            print(f"Summary generation failed: {e}")
        
        # Generate tags
        try:
            generated_tags = ai_service.generate_tags(title, content)
            tags = ",".join(generated_tags) if generated_tags else None
        except Exception as e:
            print(f"Tag generation failed: {e}")
    
    note = create_note(
        db,
        user_id=current_user["id"],
        title=title,
        content=content,
        summary=summary,
        tags=tags
    )
    
    # Create initial version
    from app.database import create_note_version
    create_note_version(
        db,
        note_id=note.id,
        user_id=current_user["id"],
        title=note.title,
        content=note.content,
        summary=note.summary,
        tags=note.tags,
        change_summary="Note created",
        change_type="create"
    )
    
    return note.to_dict()


@app.get(
    "/api/notes/{note_id}",
    response_model=schemas.NoteResponse,
    tags=["Notes"],
    summary="获取笔记详情",
    description="根据 ID 获取单篇笔记的详细信息。只能访问自己的笔记。",
    responses={
        200: {"description": "笔记详情", "model": schemas.NoteResponse},
        401: {"description": "未认证", "model": schemas.ErrorResponse},
        404: {"description": "笔记不存在", "model": schemas.ErrorResponse},
    }
)
async def get_note_by_id(
    note_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Get a note by ID (must belong to current user)"""
    note = get_note(db, note_id, user_id=current_user["id"])
    if not note:
        raise HTTPException(status_code=404, detail="Note not found")
    return note.to_dict()


@app.put(
    "/api/notes/{note_id}",
    response_model=schemas.NoteResponse,
    tags=["Notes"],
    summary="更新笔记",
    description="""
    更新笔记内容。如果内容有变化且 AI 服务可用，会自动重新生成摘要和标签。
    
    - 只能更新自己的笔记
    - 传 null 或不传的字段不会被更新
    """,
    responses={
        200: {"description": "更新成功", "model": schemas.NoteResponse},
        401: {"description": "未认证", "model": schemas.ErrorResponse},
        404: {"description": "笔记不存在", "model": schemas.ErrorResponse},
    }
)
async def update_existing_note(
    note_id: int,
    note_data: schemas.NoteUpdateRequest,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Update a note (must belong to current user)"""
    existing_note = get_note(db, note_id, user_id=current_user["id"])
    if not existing_note:
        raise HTTPException(status_code=404, detail="Note not found")
    
    title = note_data.title
    content = note_data.content
    
    # Regenerate AI features if content changed significantly
    summary = None
    tags = None
    
    if ai_service.is_available():
        if content and content != existing_note.content:
            try:
                summary = ai_service.generate_summary(content)
            except Exception as e:
                print(f"Summary generation failed: {e}")
            
            try:
                new_title = title or existing_note.title
                generated_tags = ai_service.generate_tags(new_title, content)
                tags = ",".join(generated_tags) if generated_tags else existing_note.tags
            except Exception as e:
                print(f"Tag generation failed: {e}")
    
    note = update_note(
        db, 
        note_id=note_id,
        user_id=current_user["id"],
        title=title, 
        content=content,
        summary=summary,
        tags=tags
    )
    
    # Create version history after successful update
    if note:
        from app.database import create_note_version
        create_note_version(
            db,
            note_id=note_id,
            user_id=current_user["id"],
            title=note.title,
            content=note.content,
            summary=note.summary,
            tags=note.tags,
            change_summary="Updated via API",
            change_type="edit"
        )
    
    return note.to_dict()


@app.put(
    "/api/notes/{note_id}/attachments",
    response_model=schemas.MessageResponse,
    tags=["Notes"],
    summary="更新笔记附件关联",
    description="将临时上传的附件关联到指定笔记。",
    responses={
        200: {"description": "附件关联成功", "model": schemas.MessageResponse},
        401: {"description": "未认证", "model": schemas.ErrorResponse},
        404: {"description": "笔记不存在", "model": schemas.ErrorResponse},
    }
)
async def update_note_attachments(
    note_id: int,
    attachment_ids: List[int],
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Update attachment associations for a note"""
    note = get_note(db, note_id, user_id=current_user["id"])
    if not note:
        raise HTTPException(status_code=404, detail="Note not found")
    
    from app.database import Attachment
    
    # First, reset all attachments for this note to note_id=0
    existing_attachments = db.query(Attachment).filter(
        Attachment.note_id == note_id
    ).all()
    for att in existing_attachments:
        att.note_id = 0
    
    # Then, associate new attachments
    for att_id in attachment_ids:
        attachment = db.query(Attachment).filter(
            Attachment.id == att_id,
            Attachment.user_id == current_user["id"]
        ).first()
        if attachment:
            attachment.note_id = note_id
    
    db.commit()
    return {"message": "Attachments updated successfully"}


@app.delete(
    "/api/notes/{note_id}",
    response_model=schemas.MessageResponse,
    tags=["Notes"],
    summary="删除笔记",
    description="删除指定 ID 的笔记。只能删除自己的笔记。关联的附件文件也将被删除。",
    responses={
        200: {"description": "删除成功", "model": schemas.MessageResponse},
        401: {"description": "未认证", "model": schemas.ErrorResponse},
        404: {"description": "笔记不存在", "model": schemas.ErrorResponse},
    }
)
async def delete_note_by_id(
    note_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Delete a note (must belong to current user)"""
    # Get attachments before deleting note
    attachments = get_note_attachments(db, note_id)
    
    # Delete attachment files from disk
    for attachment in attachments:
        try:
            file_path = Path(attachment.file_path)
            if file_path.exists():
                file_path.unlink()
        except Exception as e:
            print(f"Failed to delete attachment file: {e}")
    
    # Delete attachment records
    delete_note_attachments(db, note_id)
    
    # Delete the note
    success = delete_note(db, note_id, user_id=current_user["id"])
    if not success:
        raise HTTPException(status_code=404, detail="Note not found")
    return {"message": "Note deleted successfully"}


# ============== AI Features API ==============

@app.post(
    "/api/notes/{note_id}/summarize",
    response_model=schemas.NoteSummaryResponse,
    tags=["AI Features"],
    summary="生成笔记摘要",
    description="为指定笔记生成 AI 摘要并保存到笔记中。",
    responses={
        200: {"description": "摘要生成成功", "model": schemas.NoteSummaryResponse},
        401: {"description": "未认证", "model": schemas.ErrorResponse},
        404: {"description": "笔记不存在", "model": schemas.ErrorResponse},
        503: {"description": "AI 服务不可用", "model": schemas.ErrorResponse},
    }
)
async def summarize_note(
    note_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Generate or regenerate summary for a note"""
    note = get_note(db, note_id, user_id=current_user["id"])
    if not note:
        raise HTTPException(status_code=404, detail="Note not found")
    
    if not ai_service.is_available():
        raise HTTPException(status_code=503, detail="AI service not available")
    
    summary = ai_service.generate_summary(note.content)
    if not summary:
        raise HTTPException(status_code=500, detail="Failed to generate summary")
    
    # Update note with new summary
    updated_note = update_note(db, note_id=note_id, user_id=current_user["id"], summary=summary)
    return {"summary": summary, "note": updated_note.to_dict()}


@app.post(
    "/api/notes/{note_id}/tags",
    response_model=schemas.NoteTagsResponse,
    tags=["AI Features"],
    summary="生成笔记标签",
    description="为指定笔记生成 AI 标签并保存到笔记中。",
    responses={
        200: {"description": "标签生成成功", "model": schemas.NoteTagsResponse},
        401: {"description": "未认证", "model": schemas.ErrorResponse},
        404: {"description": "笔记不存在", "model": schemas.ErrorResponse},
        503: {"description": "AI 服务不可用", "model": schemas.ErrorResponse},
    }
)
async def generate_note_tags(
    note_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Generate tags for a note"""
    note = get_note(db, note_id, user_id=current_user["id"])
    if not note:
        raise HTTPException(status_code=404, detail="Note not found")
    
    if not ai_service.is_available():
        raise HTTPException(status_code=503, detail="AI service not available")
    
    tags_list = ai_service.generate_tags(note.title, note.content)
    tags = ",".join(tags_list) if tags_list else ""
    
    # Update note with new tags
    updated_note = update_note(db, note_id=note_id, user_id=current_user["id"], tags=tags)
    return {"tags": tags_list, "note": updated_note.to_dict()}


@app.post(
    "/api/search/smart",
    response_model=schemas.SmartSearchResponse,
    tags=["AI Features"],
    summary="智能搜索",
    description="""
    使用 AI 进行语义搜索，理解查询意图而非简单关键词匹配。
    
    示例查询：
    - "关于项目管理的笔记"
    - "上周记录的技术方案"
    - "包含代码示例的笔记"
    """,
    responses={
        200: {"description": "搜索成功", "model": schemas.SmartSearchResponse},
        400: {"description": "查询不能为空", "model": schemas.ErrorResponse},
        401: {"description": "未认证", "model": schemas.ErrorResponse},
        503: {"description": "AI 服务不可用", "model": schemas.ErrorResponse},
    }
)
async def smart_search_endpoint(
    search_data: schemas.SmartSearchRequest,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Smart AI-powered search"""
    query = search_data.query.strip()
    
    if not query:
        raise HTTPException(status_code=400, detail="Query is required")
    
    if not ai_service.is_available():
        raise HTTPException(status_code=503, detail="AI service not available")
    
    # Get all notes for current user to analyze
    all_notes = get_notes(db, user_id=current_user["id"], limit=1000)
    notes_data = [note.to_dict() for note in all_notes]
    
    results = ai_service.smart_search(query, notes_data)
    
    # Enrich results with full note data
    enriched_results = []
    for result in results:
        note_id = result.get("note_id")
        note = get_note(db, note_id, user_id=current_user["id"])
        if note:
            note_dict = note.to_dict()
            note_dict["search_relevance"] = result.get("relevance")
            note_dict["search_reason"] = result.get("reason")
            enriched_results.append(note_dict)
    
    return {
        "query": query,
        "results": enriched_results,
        "total": len(enriched_results)
    }


@app.post(
    "/api/ai/enhance",
    response_model=schemas.EnhanceTextResponse,
    tags=["AI Features"],
    summary="文本增强",
    description="""
    使用 AI 增强文本内容。
    
    支持的增强方式：
    - `improve` - 改进写作质量
    - `simplify` - 简化内容
    - `professional` - 专业化表达
    - `creative` - 创意写作
    - `expand` - 扩展内容
    """,
    responses={
        200: {"description": "增强成功", "model": schemas.EnhanceTextResponse},
        400: {"description": "内容不能为空", "model": schemas.ErrorResponse},
        401: {"description": "未认证", "model": schemas.ErrorResponse},
        503: {"description": "AI 服务不可用", "model": schemas.ErrorResponse},
    }
)
async def enhance_text(
    enhance_data: schemas.EnhanceTextRequest,
    current_user: dict = Depends(get_current_user)
):
    """Enhance text using AI"""
    content = enhance_data.content.strip()
    instruction = enhance_data.instruction
    
    if not content:
        raise HTTPException(status_code=400, detail="Content is required")
    
    if not ai_service.is_available():
        raise HTTPException(status_code=503, detail="AI service not available")
    
    enhanced = ai_service.enhance_content(content, instruction)
    if not enhanced:
        raise HTTPException(status_code=500, detail="Failed to enhance text")
    
    return {"original": content, "enhanced": enhanced}


# ============== Export API ==============

@app.get(
    "/api/export/json",
    tags=["Export"],
    summary="导出所有笔记为 JSON",
    description="将所有笔记导出为 JSON 文件，包含完整的笔记数据和元信息。",
    responses={
        200: {
            "description": "JSON 文件",
            "content": {
                "application/json": {
                    "schema": {"type": "string", "format": "binary"}
                }
            }
        },
        401: {"description": "未认证", "model": schemas.ErrorResponse},
    }
)
async def export_json(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Export all notes for current user as JSON"""
    notes = get_all_notes_for_export(db, user_id=current_user["id"])
    data = {
        "export_date": datetime.utcnow().isoformat(),
        "total_notes": len(notes),
        "user": current_user["username"],
        "notes": [note.to_dict() for note in notes]
    }
    
    # Save to file
    export_path = EXPORTS_DIR / f"notes_export_{current_user['username']}_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.json"
    with open(export_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    
    return FileResponse(
        export_path,
        media_type="application/json",
        filename=export_path.name
    )


@app.get(
    "/api/export/markdown/{note_id}",
    tags=["Export"],
    summary="导出单个笔记为 Markdown",
    description="将指定笔记导出为 Markdown 文件。",
    responses={
        200: {
            "description": "Markdown 文件",
            "content": {
                "text/markdown": {
                    "schema": {"type": "string", "format": "binary"}
                }
            }
        },
        401: {"description": "未认证", "model": schemas.ErrorResponse},
        404: {"description": "笔记不存在", "model": schemas.ErrorResponse},
    }
)
async def export_markdown_single(
    note_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Export a single note as Markdown"""
    note = get_note(db, note_id, user_id=current_user["id"])
    if not note:
        raise HTTPException(status_code=404, detail="Note not found")
    
    # Generate markdown content
    md_content = f"# {note.title}\n\n"
    if note.tags:
        md_content += f"**Tags:** {note.tags}\n\n"
    if note.summary:
        md_content += f"> **Summary:** {note.summary}\n\n"
    md_content += f"---\n\n{note.content}\n\n"
    md_content += f"---\n\n"
    md_content += f"*Created: {note.created_at}*\n"
    md_content += f"*Updated: {note.updated_at}*\n"
    
    # Save to file
    safe_title = "".join(c for c in note.title if c.isalnum() or c in (' ', '-', '_')).rstrip()
    export_path = EXPORTS_DIR / f"note_{note.id}_{safe_title}.md"
    with open(export_path, "w", encoding="utf-8") as f:
        f.write(md_content)
    
    return FileResponse(
        export_path,
        media_type="text/markdown",
        filename=export_path.name
    )


@app.get(
    "/api/export/markdown",
    tags=["Export"],
    summary="导出所有笔记为 Markdown",
    description="将所有笔记合并导出为一个 Markdown 文件。",
    responses={
        200: {
            "description": "Markdown 文件",
            "content": {
                "text/markdown": {
                    "schema": {"type": "string", "format": "binary"}
                }
            }
        },
        401: {"description": "未认证", "model": schemas.ErrorResponse},
    }
)
async def export_markdown_all(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Export all notes for current user as a single Markdown file"""
    notes = get_all_notes_for_export(db, user_id=current_user["id"])
    
    md_content = f"# AI Notes Export\n\n"
    md_content += f"*User: {current_user['username']}*\n"
    md_content += f"*Export Date: {datetime.utcnow().isoformat()}*\n"
    md_content += f"*Total Notes: {len(notes)}*\n\n"
    md_content += "---\n\n"
    
    for note in notes:
        md_content += f"# {note.title}\n\n"
        if note.tags:
            md_content += f"**Tags:** {note.tags}\n\n"
        if note.summary:
            md_content += f"> **Summary:** {note.summary}\n\n"
        md_content += f"{note.content}\n\n"
        md_content += f"---\n\n"
    
    # Save to file
    export_path = EXPORTS_DIR / f"notes_export_{current_user['username']}_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.md"
    with open(export_path, "w", encoding="utf-8") as f:
        f.write(md_content)
    
    return FileResponse(
        export_path,
        media_type="text/markdown",
        filename=export_path.name
    )


# ============== Markdown Preview ==============

@app.post(
    "/api/preview",
    response_model=schemas.MarkdownPreviewResponse,
    tags=["Utilities"],
    summary="Markdown 转 HTML",
    description="将 Markdown 内容转换为 HTML，用于实时预览。支持代码高亮。",
    responses={
        200: {"description": "转换成功", "model": schemas.MarkdownPreviewResponse},
        401: {"description": "未认证", "model": schemas.ErrorResponse},
    }
)
async def preview_markdown(
    data: schemas.MarkdownPreviewRequest,
    current_user: dict = Depends(get_current_user)
):
    """Convert markdown to HTML for preview with code highlighting"""
    content = data.content
    
    # Reset the converter state (required for reuse)
    md_converter.reset()
    
    # Convert markdown to HTML
    html = md_converter.convert(content)
    
    return {"html": html}


# ============== Share API ==============

@app.post(
    "/api/shares",
    response_model=schemas.ShareResponse,
    tags=["Shares"],
    summary="创建笔记分享",
    description="""
    为指定笔记创建分享链接。
    
    - 每个笔记可以有多个分享链接
    - 支持公开、密码保护、私密三种权限
    - 可选设置过期时间
    - 返回8位短链接 token
    """,
    responses={
        200: {"description": "分享创建成功", "model": schemas.ShareResponse},
        400: {"description": "参数错误", "model": schemas.ErrorResponse},
        401: {"description": "未认证", "model": schemas.ErrorResponse},
        404: {"description": "笔记不存在", "model": schemas.ErrorResponse},
    }
)
async def create_note_share(
    share_data: schemas.ShareCreateRequest,
    request: Request,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Create a share link for a note"""
    # Check if note exists and belongs to current user
    note = get_note(db, share_data.note_id, user_id=current_user["id"])
    if not note:
        raise HTTPException(status_code=404, detail="Note not found")
    
    # Validate permission
    if share_data.permission not in ["public", "password", "private"]:
        raise HTTPException(status_code=400, detail="Invalid permission type")
    
    # Check password requirement
    if share_data.permission == "password" and not share_data.password:
        raise HTTPException(status_code=400, detail="Password required for password-protected shares")
    
    # Create share
    share = create_share(
        db,
        note_id=share_data.note_id,
        user_id=current_user["id"],
        permission=share_data.permission,
        password=share_data.password,
        expires_days=share_data.expires_days
    )
    
    # Build share URL
    base_url = str(request.base_url).rstrip('/')
    share_url = f"{base_url}/s/{share.token}"
    
    result = share.to_dict()
    result["share_url"] = share_url
    return result


@app.get(
    "/api/shares",
    response_model=schemas.ShareListResponse,
    tags=["Shares"],
    summary="获取用户的所有分享",
    description="获取当前用户创建的所有分享链接列表。"
)
async def list_user_shares(
    request: Request,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """List all shares created by current user"""
    shares = get_note_shares(db, user_id=current_user["id"])
    
    base_url = str(request.base_url).rstrip('/')
    result = []
    for share in shares:
        share_dict = share.to_dict()
        share_dict["share_url"] = f"{base_url}/s/{share.token}"
        # Add note title
        note = get_note(db, share.note_id)
        if note:
            share_dict["note_title"] = note.title
        result.append(share_dict)
    
    return {"shares": result, "total": len(result)}


@app.get(
    "/api/shares/note/{note_id}",
    response_model=schemas.ShareListResponse,
    tags=["Shares"],
    summary="获取笔记的所有分享",
    description="获取指定笔记的所有分享链接列表。"
)
async def list_note_shares(
    note_id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """List all shares for a specific note"""
    # Check if note exists and belongs to current user
    note = get_note(db, note_id, user_id=current_user["id"])
    if not note:
        raise HTTPException(status_code=404, detail="Note not found")
    
    shares = get_note_shares(db, note_id=note_id, user_id=current_user["id"])
    
    base_url = str(request.base_url).rstrip('/')
    result = []
    for share in shares:
        share_dict = share.to_dict()
        share_dict["share_url"] = f"{base_url}/s/{share.token}"
        share_dict["note_title"] = note.title
        result.append(share_dict)
    
    return {"shares": result, "total": len(result)}


@app.get(
    "/api/shares/{token}",
    response_model=schemas.ShareResponse,
    tags=["Shares"],
    summary="获取分享详情",
    description="获取分享链接的详细信息（仅创建者可查看）。"
)
async def get_share_info(
    token: str,
    request: Request,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Get share details (owner only)"""
    share = get_share_by_token(db, token)
    if not share:
        raise HTTPException(status_code=404, detail="Share not found")
    
    # Only owner can view share details
    if share.user_id != current_user["id"]:
        raise HTTPException(status_code=403, detail="Access denied")
    
    base_url = str(request.base_url).rstrip('/')
    result = share.to_dict()
    result["share_url"] = f"{base_url}/s/{share.token}"
    
    # Add note title
    note = get_note(db, share.note_id)
    if note:
        result["note_title"] = note.title
    
    return result


@app.put(
    "/api/shares/{token}",
    response_model=schemas.ShareResponse,
    tags=["Shares"],
    summary="更新分享设置",
    description="更新分享链接的权限、密码、过期时间等设置。"
)
async def update_share_settings(
    token: str,
    update_data: schemas.ShareUpdateRequest,
    request: Request,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Update share settings (owner only)"""
    share = get_share_by_token(db, token)
    if not share:
        raise HTTPException(status_code=404, detail="Share not found")
    
    # Only owner can update
    if share.user_id != current_user["id"]:
        raise HTTPException(status_code=403, detail="Access denied")
    
    # Prepare update kwargs
    kwargs = {}
    if update_data.permission is not None:
        if update_data.permission not in ["public", "password", "private"]:
            raise HTTPException(status_code=400, detail="Invalid permission type")
        kwargs["permission"] = update_data.permission
    
    if update_data.is_active is not None:
        kwargs["is_active"] = update_data.is_active
    
    if update_data.password is not None:
        kwargs["password"] = update_data.password
    
    if update_data.expires_days is not None:
        from datetime import datetime, timedelta
        kwargs["expires_at"] = datetime.utcnow() + timedelta(days=update_data.expires_days)
    
    updated_share = update_share(db, token, current_user["id"], **kwargs)
    
    base_url = str(request.base_url).rstrip('/')
    result = updated_share.to_dict()
    result["share_url"] = f"{base_url}/s/{updated_share.token}"
    
    # Add note title
    note = get_note(db, updated_share.note_id)
    if note:
        result["note_title"] = note.title
    
    return result


@app.delete(
    "/api/shares/{token}",
    response_model=schemas.MessageResponse,
    tags=["Shares"],
    summary="删除分享链接",
    description="删除指定的分享链接。"
)
async def revoke_share_link(
    token: str,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Delete a share link (owner only)"""
    share = get_share_by_token(db, token)
    if not share:
        raise HTTPException(status_code=404, detail="Share not found")
    
    # Only owner can delete
    if share.user_id != current_user["id"]:
        raise HTTPException(status_code=403, detail="Access denied")
    
    success = revoke_share(db, token, current_user["id"])
    if not success:
        raise HTTPException(status_code=500, detail="Failed to delete share")
    
    return {"message": "Share deleted successfully"}


@app.post(
    "/api/shares/{token}/verify",
    response_model=schemas.ShareVerifyResponse,
    tags=["Shares"],
    summary="验证分享密码",
    description="验证密码保护的分享链接。"
)
async def verify_share(
    token: str,
    verify_data: schemas.ShareVerifyRequest,
    request: Request,
    db: Session = Depends(get_db)
):
    """Verify password for a protected share"""
    share = get_share_by_token(db, token)
    if not share:
        raise HTTPException(status_code=404, detail="Share not found")
    
    # Check if share is valid
    if not share.is_valid():
        raise HTTPException(status_code=403, detail="Share link is expired or inactive")
    
    # Check if password is required
    if share.permission != "password":
        return {
            "valid": True,
            "message": "No password required",
            "share_url": f"/s/{token}"
        }
    
    # Verify password
    if verify_share_password(db, token, verify_data.password):
        return {
            "valid": True,
            "message": "Password verified",
            "share_url": f"/s/{token}?verified=true"
        }
    else:
        return {
            "valid": False,
            "message": "Invalid password",
            "share_url": None
        }


@app.get(
    "/api/shares/{token}/access",
    response_model=schemas.ShareNoteResponse,
    tags=["Shares"],
    summary="通过分享访问笔记内容",
    description="通过分享链接访问笔记内容，无需登录。"
)
async def access_shared_note(
    token: str,
    password: str = Query(None, description="访问密码（密码保护时需要）"),
    verified: bool = Query(False, description="是否已通过密码验证"),
    db: Session = Depends(get_db)
):
    """Access note through share link (no authentication required)"""
    share = get_share_by_token(db, token)
    if not share:
        raise HTTPException(status_code=404, detail="Share not found")
    
    # Check if share is valid
    if not share.is_valid():
        raise HTTPException(status_code=403, detail="Share link is expired or inactive")
    
    # Check permission
    if share.permission == "private":
        raise HTTPException(status_code=403, detail="This share is private")
    
    # Check password if required
    if share.permission == "password":
        if not verified and not password:
            raise HTTPException(status_code=401, detail="Password required")
        if password and not verify_share_password(db, token, password):
            raise HTTPException(status_code=401, detail="Invalid password")
    
    # Get note
    note = get_note(db, share.note_id)
    if not note:
        raise HTTPException(status_code=404, detail="Note not found")
    
    # Increment access count
    verify_share_access(db, token)
    
    return {
        "note": note.to_dict(),
        "token": token,
        "permission": share.permission,
        "access_count": share.access_count + 1
    }


# ============== Share Web Routes ==============

@app.get("/s/{token}", response_class=HTMLResponse, tags=["Web"], include_in_schema=False)
async def share_page(
    token: str,
    request: Request,
    password: str = Query(None, description="访问密码"),
    verified: bool = Query(False, description="是否已验证"),
    db: Session = Depends(get_db)
):
    """Share page - displays shared note without login"""
    share = get_share_by_token(db, token)
    if not share:
        return templates.TemplateResponse("share.html", {
            "request": request,
            "app_name": APP_NAME,
            "error": "分享链接不存在或已过期",
            "require_password": False,
            "token": token
        })
    
    # Check if share is valid
    if not share.is_valid():
        return templates.TemplateResponse("share.html", {
            "request": request,
            "app_name": APP_NAME,
            "error": "分享链接已过期或被禁用",
            "require_password": False,
            "token": token
        })
    
    # Check permission
    if share.permission == "private":
        return templates.TemplateResponse("share.html", {
            "request": request,
            "app_name": APP_NAME,
            "error": "此分享为私密分享，无法访问",
            "require_password": False,
            "token": token
        })
    
    # Check password if required
    if share.permission == "password" and not verified:
        # If password provided, verify it
        if password:
            if not verify_share_password(db, token, password):
                return templates.TemplateResponse("share.html", {
                    "request": request,
                    "app_name": APP_NAME,
                    "error": "密码错误，请重试",
                    "require_password": True,
                    "token": token
                })
        else:
            # Show password form
            return templates.TemplateResponse("share.html", {
                "request": request,
                "app_name": APP_NAME,
                "error": None,
                "require_password": True,
                "token": token
            })
    
    # Get note
    note = get_note(db, share.note_id)
    if not note:
        return templates.TemplateResponse("share.html", {
            "request": request,
            "app_name": APP_NAME,
            "error": "笔记不存在或已被删除",
            "require_password": False,
            "token": token
        })
    
    # Increment access count
    verify_share_access(db, token)
    
    # Convert markdown to HTML
    md_converter.reset()
    html_content = md_converter.convert(note.content)
    
    return templates.TemplateResponse("share.html", {
        "request": request,
        "app_name": APP_NAME,
        "note": note,
        "note_dict": note.to_dict(),
        "html_content": html_content,
        "token": token,
        "access_count": share.access_count + 1,
        "error": None,
        "require_password": False
    })


# ============== Collaboration API ==============

@app.get(
    "/api/notes/{note_id}/versions",
    response_model=schemas.VersionListResponse,
    tags=["Collaboration"],
    summary="获取笔记版本历史",
    description="获取指定笔记的所有历史版本列表。"
)
async def get_note_versions(
    note_id: int,
    limit: int = Query(50, ge=1, le=100, description="返回的最大版本数"),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Get version history for a note"""
    from app.database import get_note_versions, is_note_owner_or_collaborator
    
    # Check access
    if not is_note_owner_or_collaborator(db, note_id, current_user["id"]):
        raise HTTPException(status_code=403, detail="Access denied")
    
    note = get_note(db, note_id)
    if not note:
        raise HTTPException(status_code=404, detail="Note not found")
    
    versions = get_note_versions(db, note_id, limit=limit)
    
    return {
        "versions": [v.to_dict() for v in versions],
        "total": len(versions),
        "note_id": note_id,
        "current_version": note.current_version
    }


@app.get(
    "/api/notes/{note_id}/versions/{version_id}",
    response_model=schemas.VersionResponse,
    tags=["Collaboration"],
    summary="获取特定版本详情",
    description="获取指定笔记特定版本的详细内容。"
)
async def get_version_detail(
    note_id: int,
    version_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Get specific version details"""
    from app.database import get_note_version, is_note_owner_or_collaborator
    
    if not is_note_owner_or_collaborator(db, note_id, current_user["id"]):
        raise HTTPException(status_code=403, detail="Access denied")
    
    version = get_note_version(db, version_id)
    if not version or version.note_id != note_id:
        raise HTTPException(status_code=404, detail="Version not found")
    
    return version.to_dict()


@app.post(
    "/api/notes/{note_id}/versions/{version_id}/restore",
    response_model=schemas.NoteResponse,
    tags=["Collaboration"],
    summary="恢复到指定版本",
    description="将笔记恢复到指定的历史版本。"
)
async def restore_version(
    note_id: int,
    version_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Restore note to a specific version"""
    from app.database import restore_note_version
    
    # Check if user is owner or has admin permission
    note = get_note(db, note_id, user_id=current_user["id"])
    if not note:
        # Check if collaborator with admin permission
        from app.database import check_collaborator_permission
        perm = check_collaborator_permission(db, note_id, current_user["id"])
        if perm != "admin":
            raise HTTPException(status_code=403, detail="Admin permission required")
    
    restored_note = restore_note_version(db, note_id, version_id, current_user["id"])
    if not restored_note:
        raise HTTPException(status_code=404, detail="Version not found")
    
    return restored_note.to_dict()


@app.get(
    "/api/notes/{note_id}/versions/compare",
    response_model=schemas.VersionComparisonResponse,
    tags=["Collaboration"],
    summary="比较两个版本",
    description="比较笔记的两个版本，显示差异。"
)
async def compare_note_versions(
    note_id: int,
    version_id1: int,
    version_id2: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Compare two versions of a note"""
    from app.database import compare_versions, is_note_owner_or_collaborator
    
    if not is_note_owner_or_collaborator(db, note_id, current_user["id"]):
        raise HTTPException(status_code=403, detail="Access denied")
    
    result = compare_versions(db, version_id1, version_id2)
    if not result:
        raise HTTPException(status_code=404, detail="Version not found")
    
    return result


@app.post(
    "/api/notes/{note_id}/collaborators",
    response_model=schemas.CollaboratorResponse,
    tags=["Collaboration"],
    summary="添加协作者",
    description="为笔记添加协作者，设置其权限级别。"
)
async def add_note_collaborator(
    note_id: int,
    collaborator_data: schemas.AddCollaboratorRequest,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Add a collaborator to a note"""
    from app.database import add_collaborator, get_user_by_username
    
    # Check if user is owner
    note = get_note(db, note_id, user_id=current_user["id"])
    if not note:
        raise HTTPException(status_code=404, detail="Note not found or access denied")
    
    # Find the user to add
    target_user = get_user_by_username(db, collaborator_data.username)
    if not target_user:
        raise HTTPException(status_code=404, detail="User not found")
    
    if target_user.id == current_user["id"]:
        raise HTTPException(status_code=400, detail="Cannot add yourself as collaborator")
    
    # Validate permission
    if collaborator_data.permission not in ["read", "write", "admin"]:
        raise HTTPException(status_code=400, detail="Invalid permission type")
    
    # Add collaborator
    collaborator = add_collaborator(
        db,
        note_id=note_id,
        user_id=target_user.id,
        permission=collaborator_data.permission,
        added_by=current_user["id"]
    )
    
    result = collaborator.to_dict()
    result["username"] = target_user.username
    result["email"] = target_user.email
    
    return result


@app.delete(
    "/api/notes/{note_id}/collaborators/{user_id}",
    response_model=schemas.MessageResponse,
    tags=["Collaboration"],
    summary="移除协作者",
    description="从笔记中移除协作者。"
)
async def remove_note_collaborator(
    note_id: int,
    user_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Remove a collaborator from a note"""
    from app.database import remove_collaborator
    
    # Check if user is owner
    note = get_note(db, note_id, user_id=current_user["id"])
    if not note:
        raise HTTPException(status_code=404, detail="Note not found or access denied")
    
    # Cannot remove owner
    if user_id == note.user_id:
        raise HTTPException(status_code=400, detail="Cannot remove note owner")
    
    success = remove_collaborator(db, note_id, user_id)
    if not success:
        raise HTTPException(status_code=404, detail="Collaborator not found")
    
    return {"message": "Collaborator removed successfully"}


@app.get(
    "/api/notes/{note_id}/collaborators",
    response_model=schemas.CollaboratorListResponse,
    tags=["Collaboration"],
    summary="获取协作者列表",
    description="获取笔记的所有协作者列表。"
)
async def get_note_collaborators(
    note_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Get all collaborators for a note"""
    from app.database import get_note_collaborators, is_note_owner_or_collaborator, get_user_by_id
    
    if not is_note_owner_or_collaborator(db, note_id, current_user["id"]):
        raise HTTPException(status_code=403, detail="Access denied")
    
    note = get_note(db, note_id)
    if not note:
        raise HTTPException(status_code=404, detail="Note not found")
    
    collaborators = get_note_collaborators(db, note_id)
    
    result = []
    for c in collaborators:
        collab_dict = c.to_dict()
        user = get_user_by_id(db, c.user_id)
        if user:
            collab_dict["username"] = user.username
            collab_dict["email"] = user.email
        result.append(collab_dict)
    
    return {
        "collaborators": result,
        "note_id": note_id,
        "owner_id": note.user_id
    }


@app.get(
    "/api/notes/{note_id}/collaborators/active",
    response_model=schemas.ActiveCollaboratorsResponse,
    tags=["Collaboration"],
    summary="获取活跃协作者",
    description="获取当前正在协作编辑该笔记的活跃用户列表。"
)
async def get_active_collaborators(
    note_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Get active collaborators (currently editing)"""
    from app.database import is_note_owner_or_collaborator, get_active_collaborators, get_user_by_id
    
    if not is_note_owner_or_collaborator(db, note_id, current_user["id"]):
        raise HTTPException(status_code=403, detail="Access denied")
    
    sessions = get_active_collaborators(db, note_id)
    
    result = []
    for session in sessions:
        session_dict = session.to_dict()
        user = get_user_by_id(db, session.user_id)
        if user:
            session_dict["username"] = user.username
        result.append(session_dict)
    
    return {
        "collaborators": result,
        "note_id": note_id
    }


@app.post(
    "/api/notes/{note_id}/conflict/detect",
    response_model=schemas.ConflictDetectionResponse,
    tags=["Collaboration"],
    summary="检测冲突",
    description="检测当前编辑是否与服务器版本存在冲突。"
)
async def detect_note_conflict(
    note_id: int,
    base_version: int = Query(..., description="基础版本号"),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Detect if there's a conflict between versions"""
    from app.database import detect_conflict, is_note_owner_or_collaborator, get_note
    
    if not is_note_owner_or_collaborator(db, note_id, current_user["id"]):
        raise HTTPException(status_code=403, detail="Access denied")
    
    note = get_note(db, note_id)
    if not note:
        raise HTTPException(status_code=404, detail="Note not found")
    
    result = detect_conflict(db, note_id, base_version, note.current_version)
    
    return result


@app.post(
    "/api/notes/{note_id}/conflict/resolve",
    response_model=schemas.NoteResponse,
    tags=["Collaboration"],
    summary="解决冲突",
    description="提交冲突解决方案，合并更改。"
)
async def resolve_note_conflict(
    note_id: int,
    resolution_data: schemas.ConflictResolutionRequest,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Resolve a conflict by merging changes"""
    from app.database import merge_changes, is_note_owner_or_collaborator
    
    if not is_note_owner_or_collaborator(db, note_id, current_user["id"]):
        raise HTTPException(status_code=403, detail="Access denied")
    
    note = get_note(db, note_id)
    if not note:
        raise HTTPException(status_code=404, detail="Note not found")
    
    # Build changes dict
    changes = {
        "change_summary": f"Conflict resolution: {resolution_data.resolution}"
    }
    
    if resolution_data.resolution == "mine":
        # Keep current content (no change needed)
        pass
    elif resolution_data.resolution == "theirs":
        # Should reload from server (client handles this)
        pass
    elif resolution_data.resolution == "merge":
        if resolution_data.merged_content:
            changes["content"] = resolution_data.merged_content
        if resolution_data.merged_title:
            changes["title"] = resolution_data.merged_title
    
    merged_note = merge_changes(
        db, note_id, current_user["id"],
        resolution_data.base_version, changes
    )
    
    if not merged_note:
        raise HTTPException(status_code=500, detail="Failed to merge changes")
    
    return merged_note.to_dict()


# ============== WebSocket Endpoint ==============

@app.websocket("/ws/collaborate/{note_id}")
async def websocket_collaborate(
    websocket: WebSocket,
    note_id: int,
    db: Session = Depends(get_db)
):
    """WebSocket endpoint for real-time collaboration"""
    from app.websocket import handle_websocket
    await handle_websocket(websocket, note_id, db)


# ============== Collaborated Notes API ==============

@app.get(
    "/api/collaborated-notes",
    response_model=List[schemas.NoteResponse],
    tags=["Collaboration"],
    summary="获取协作笔记列表",
    description="获取当前用户作为协作者的所有笔记列表。"
)
async def get_collaborated_notes(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Get all notes where user is a collaborator"""
    from app.database import get_user_collaborated_notes
    
    notes = get_user_collaborated_notes(db, current_user["id"])
    return [note.to_dict() for note in notes]


# ============== File Upload API ==============

import os
import uuid
import mimetypes
from pathlib import Path
from fastapi import File, UploadFile


def get_file_type(mime_type: str) -> str:
    """Determine file type category from MIME type"""
    if mime_type.startswith('image/'):
        return 'image'
    elif mime_type.startswith('video/'):
        return 'video'
    elif mime_type.startswith('audio/'):
        return 'audio'
    elif mime_type in ALLOWED_DOCUMENT_TYPES:
        return 'document'
    else:
        return 'other'


def generate_unique_filename(original_filename: str) -> str:
    """Generate a unique filename for uploaded file"""
    ext = Path(original_filename).suffix.lower()
    unique_id = str(uuid.uuid4())[:8]
    return f"{unique_id}{ext}"


@app.post(
    "/api/upload/image",
    response_model=schemas.ImageUploadResponse,
    tags=["Upload"],
    summary="上传图片",
    description="上传图片文件到服务器，支持 JPG、PNG、GIF、WebP、SVG 格式，最大 10MB。",
    responses={
        200: {"description": "上传成功", "model": schemas.ImageUploadResponse},
        400: {"description": "文件类型错误或文件过大", "model": schemas.ErrorResponse},
        401: {"description": "未认证", "model": schemas.ErrorResponse},
    }
)
async def upload_image(
    file: UploadFile = File(..., description="图片文件"),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Upload an image file"""
    # Validate file type
    mime_type = file.content_type or mimetypes.guess_type(file.filename)[0] or 'application/octet-stream'
    
    if mime_type not in ALLOWED_IMAGE_TYPES:
        raise HTTPException(
            status_code=400, 
            detail=f"不支持的图片格式。支持: {', '.join(ALLOWED_IMAGE_TYPES)}"
        )
    
    # Validate file size (read first chunk to check)
    content = await file.read()
    if len(content) > 10 * 1024 * 1024:  # 10MB limit for images
        raise HTTPException(status_code=400, detail="图片文件大小不能超过 10MB")
    
    # Generate unique filename
    unique_filename = generate_unique_filename(file.filename)
    file_path = UPLOADS_DIR / unique_filename
    
    # Save file
    with open(file_path, "wb") as f:
        f.write(content)
    
    # Get image dimensions if possible
    width, height = None, None
    try:
        from PIL import Image as PILImage
        with PILImage.open(file_path) as img:
            width, height = img.size
    except Exception:
        pass  # Not all images can be processed by PIL
    
    # Create attachment record
    attachment = create_attachment(
        db,
        note_id=0,  # Will be updated when attached to a note
        user_id=current_user["id"],
        filename=unique_filename,
        original_filename=file.filename,
        file_path=str(file_path),
        file_size=len(content),
        mime_type=mime_type,
        file_type='image',
        width=width,
        height=height,
        url_path=unique_filename
    )
    
    return {
        "id": attachment.id,
        "url": f"/uploads/{unique_filename}",
        "filename": unique_filename,
        "original_filename": file.filename,
        "file_size": len(content),
        "width": width,
        "height": height
    }


@app.post(
    "/api/upload/attachment",
    response_model=schemas.AttachmentUploadResponse,
    tags=["Upload"],
    summary="上传附件",
    description="上传附件文件到服务器，支持 PDF、Word、Excel、PPT、TXT 等格式，最大 50MB。",
    responses={
        200: {"description": "上传成功", "model": schemas.AttachmentUploadResponse},
        400: {"description": "文件类型错误或文件过大", "model": schemas.ErrorResponse},
        401: {"description": "未认证", "model": schemas.ErrorResponse},
    }
)
async def upload_attachment(
    file: UploadFile = File(..., description="附件文件"),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Upload an attachment file"""
    # Validate file type
    mime_type = file.content_type or mimetypes.guess_type(file.filename)[0] or 'application/octet-stream'
    
    # Allow images and documents
    allowed_types = ALLOWED_IMAGE_TYPES | ALLOWED_DOCUMENT_TYPES
    if mime_type not in allowed_types:
        raise HTTPException(
            status_code=400, 
            detail="不支持的文件格式"
        )
    
    # Validate file size
    content = await file.read()
    if len(content) > MAX_UPLOAD_SIZE:
        raise HTTPException(status_code=400, detail=f"文件大小不能超过 {MAX_UPLOAD_SIZE // 1024 // 1024}MB")
    
    # Generate unique filename
    unique_filename = generate_unique_filename(file.filename)
    file_path = UPLOADS_DIR / unique_filename
    
    # Save file
    with open(file_path, "wb") as f:
        f.write(content)
    
    # Determine file type
    file_type = get_file_type(mime_type)
    
    # Create attachment record
    attachment = create_attachment(
        db,
        note_id=0,  # Will be updated when attached to a note
        user_id=current_user["id"],
        filename=unique_filename,
        original_filename=file.filename,
        file_path=str(file_path),
        file_size=len(content),
        mime_type=mime_type,
        file_type=file_type,
        url_path=unique_filename
    )
    
    return {
        "id": attachment.id,
        "url": f"/uploads/{unique_filename}",
        "filename": unique_filename,
        "original_filename": file.filename,
        "file_size": len(content),
        "mime_type": mime_type,
        "file_type": file_type
    }


@app.get(
    "/api/notes/{note_id}/attachments",
    response_model=schemas.AttachmentListResponse,
    tags=["Upload"],
    summary="获取笔记附件列表",
    description="获取指定笔记的所有附件列表。",
    responses={
        200: {"description": "附件列表", "model": schemas.AttachmentListResponse},
        401: {"description": "未认证", "model": schemas.ErrorResponse},
        404: {"description": "笔记不存在", "model": schemas.ErrorResponse},
    }
)
async def get_note_attachments_list(
    note_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Get all attachments for a note"""
    # Check if note exists and belongs to current user
    note = get_note(db, note_id, user_id=current_user["id"])
    if not note:
        raise HTTPException(status_code=404, detail="Note not found")
    
    attachments = get_note_attachments(db, note_id)
    
    return {
        "attachments": [att.to_dict() for att in attachments],
        "total": len(attachments),
        "note_id": note_id
    }


@app.delete(
    "/api/attachments/{attachment_id}",
    response_model=schemas.MessageResponse,
    tags=["Upload"],
    summary="删除附件",
    description="删除指定的附件文件。",
    responses={
        200: {"description": "删除成功", "model": schemas.MessageResponse},
        401: {"description": "未认证", "model": schemas.ErrorResponse},
        403: {"description": "无权删除", "model": schemas.ErrorResponse},
        404: {"description": "附件不存在", "model": schemas.ErrorResponse},
    }
)
async def delete_attachment_endpoint(
    attachment_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Delete an attachment"""
    attachment = get_attachment(db, attachment_id)
    if not attachment:
        raise HTTPException(status_code=404, detail="Attachment not found")
    
    # Check ownership
    if attachment.user_id != current_user["id"]:
        raise HTTPException(status_code=403, detail="Access denied")
    
    # Delete file from disk
    try:
        file_path = Path(attachment.file_path)
        if file_path.exists():
            file_path.unlink()
    except Exception as e:
        print(f"Failed to delete file: {e}")
    
    # Delete from database
    success = delete_attachment(db, attachment_id, current_user["id"])
    if not success:
        raise HTTPException(status_code=500, detail="Failed to delete attachment")
    
    return {"message": "附件已删除"}


# Mount uploads directory for serving files
app.mount("/uploads", StaticFiles(directory=str(UPLOADS_DIR)), name="uploads")


if __name__ == "__main__":
    import uvicorn
    from app.config import HOST, PORT
    uvicorn.run(app, host=HOST, port=PORT)
