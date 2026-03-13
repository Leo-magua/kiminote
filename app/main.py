"""
FastAPI main application for AI Notes
"""
import json
import markdown
from datetime import datetime
from typing import List, Optional
from fastapi import FastAPI, Depends, HTTPException, Query, Request, Response, status
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

from app.config import APP_NAME, APP_VERSION, EXPORTS_DIR, SESSION_COOKIE_NAME
from app.database import (
    get_db, create_note, get_note, get_notes, update_note, 
    delete_note, get_all_notes_for_export, get_notes_count, get_all_tags,
    create_user, get_user_by_username, get_user_by_email
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
    return note.to_dict()


@app.delete(
    "/api/notes/{note_id}",
    response_model=schemas.MessageResponse,
    tags=["Notes"],
    summary="删除笔记",
    description="删除指定 ID 的笔记。只能删除自己的笔记。",
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


if __name__ == "__main__":
    import uvicorn
    from app.config import HOST, PORT
    uvicorn.run(app, host=HOST, port=PORT)
