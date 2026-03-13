"""
FastAPI main application for AI Notes
"""
import json
import markdown
from datetime import datetime
from typing import List, Optional
from fastapi import FastAPI, Depends, HTTPException, Query, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, JSONResponse, FileResponse
from sqlalchemy.orm import Session

from app.config import APP_NAME, APP_VERSION, EXPORTS_DIR
from app.database import (
    get_db, create_note, get_note, get_notes, update_note, 
    delete_note, get_all_notes_for_export, get_notes_count, get_all_tags
)
from app.ai_service import ai_service

# Create FastAPI app
app = FastAPI(
    title=APP_NAME,
    version=APP_VERSION,
    description="AI-powered note-taking application"
)

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")

# Templates
templates = Jinja2Templates(directory="templates")


# ============== Web Routes ==============

@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    """Main page"""
    return templates.TemplateResponse("index.html", {
        "request": request,
        "app_name": APP_NAME,
        "ai_available": ai_service.is_available()
    })


# ============== API Routes ==============

@app.get("/api/stats")
async def get_stats(db: Session = Depends(get_db)):
    """Get application statistics"""
    return {
        "total_notes": get_notes_count(db),
        "ai_available": ai_service.is_available(),
        "model": ai_service.model if ai_service.is_available() else None
    }


@app.get("/api/tags")
async def api_get_all_tags(db: Session = Depends(get_db)):
    """Get all unique tags"""
    return {"tags": get_all_tags(db)}


# ============== Notes CRUD API ==============

@app.get("/api/notes", response_model=List[dict])
async def list_notes(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    search: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """List all notes with optional search"""
    notes = get_notes(db, skip=skip, limit=limit, search=search)
    return [note.to_dict() for note in notes]


@app.post("/api/notes")
async def create_new_note(note_data: dict, db: Session = Depends(get_db)):
    """Create a new note"""
    title = note_data.get("title", "").strip()
    content = note_data.get("content", "").strip()
    
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
    
    note = create_note(db, title=title, content=content, summary=summary, tags=tags)
    return note.to_dict()


@app.get("/api/notes/{note_id}")
async def get_note_by_id(note_id: int, db: Session = Depends(get_db)):
    """Get a note by ID"""
    note = get_note(db, note_id)
    if not note:
        raise HTTPException(status_code=404, detail="Note not found")
    return note.to_dict()


@app.put("/api/notes/{note_id}")
async def update_existing_note(note_id: int, note_data: dict, db: Session = Depends(get_db)):
    """Update a note"""
    existing_note = get_note(db, note_id)
    if not existing_note:
        raise HTTPException(status_code=404, detail="Note not found")
    
    title = note_data.get("title")
    content = note_data.get("content")
    
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
        title=title, 
        content=content,
        summary=summary,
        tags=tags
    )
    return note.to_dict()


@app.delete("/api/notes/{note_id}")
async def delete_note_by_id(note_id: int, db: Session = Depends(get_db)):
    """Delete a note"""
    success = delete_note(db, note_id)
    if not success:
        raise HTTPException(status_code=404, detail="Note not found")
    return {"message": "Note deleted successfully"}


# ============== AI Features API ==============

@app.post("/api/notes/{note_id}/summarize")
async def summarize_note(note_id: int, db: Session = Depends(get_db)):
    """Generate or regenerate summary for a note"""
    note = get_note(db, note_id)
    if not note:
        raise HTTPException(status_code=404, detail="Note not found")
    
    if not ai_service.is_available():
        raise HTTPException(status_code=503, detail="AI service not available")
    
    summary = ai_service.generate_summary(note.content)
    if not summary:
        raise HTTPException(status_code=500, detail="Failed to generate summary")
    
    # Update note with new summary
    updated_note = update_note(db, note_id=note_id, summary=summary)
    return {"summary": summary, "note": updated_note.to_dict()}


@app.post("/api/notes/{note_id}/tags")
async def generate_note_tags(note_id: int, db: Session = Depends(get_db)):
    """Generate tags for a note"""
    note = get_note(db, note_id)
    if not note:
        raise HTTPException(status_code=404, detail="Note not found")
    
    if not ai_service.is_available():
        raise HTTPException(status_code=503, detail="AI service not available")
    
    tags_list = ai_service.generate_tags(note.title, note.content)
    tags = ",".join(tags_list) if tags_list else ""
    
    # Update note with new tags
    updated_note = update_note(db, note_id=note_id, tags=tags)
    return {"tags": tags_list, "note": updated_note.to_dict()}


@app.post("/api/search/smart")
async def smart_search_endpoint(search_data: dict, db: Session = Depends(get_db)):
    """Smart AI-powered search"""
    query = search_data.get("query", "").strip()
    
    if not query:
        raise HTTPException(status_code=400, detail="Query is required")
    
    if not ai_service.is_available():
        raise HTTPException(status_code=503, detail="AI service not available")
    
    # Get all notes for AI to analyze
    all_notes = get_notes(db, limit=1000)
    notes_data = [note.to_dict() for note in all_notes]
    
    results = ai_service.smart_search(query, notes_data)
    
    # Enrich results with full note data
    enriched_results = []
    for result in results:
        note_id = result.get("note_id")
        note = get_note(db, note_id)
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


@app.post("/api/ai/enhance")
async def enhance_text(enhance_data: dict):
    """Enhance text using AI"""
    content = enhance_data.get("content", "").strip()
    instruction = enhance_data.get("instruction", "improve")
    
    if not content:
        raise HTTPException(status_code=400, detail="Content is required")
    
    if not ai_service.is_available():
        raise HTTPException(status_code=503, detail="AI service not available")
    
    enhanced = ai_service.enhance_content(content, instruction)
    if not enhanced:
        raise HTTPException(status_code=500, detail="Failed to enhance text")
    
    return {"original": content, "enhanced": enhanced}


# ============== Export API ==============

@app.get("/api/export/json")
async def export_json(db: Session = Depends(get_db)):
    """Export all notes as JSON"""
    notes = get_all_notes_for_export(db)
    data = {
        "export_date": datetime.utcnow().isoformat(),
        "total_notes": len(notes),
        "notes": [note.to_dict() for note in notes]
    }
    
    # Save to file
    export_path = EXPORTS_DIR / f"notes_export_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.json"
    with open(export_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    
    return FileResponse(
        export_path,
        media_type="application/json",
        filename=export_path.name
    )


@app.get("/api/export/markdown/{note_id}")
async def export_markdown_single(note_id: int, db: Session = Depends(get_db)):
    """Export a single note as Markdown"""
    note = get_note(db, note_id)
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


@app.get("/api/export/markdown")
async def export_markdown_all(db: Session = Depends(get_db)):
    """Export all notes as a single Markdown file"""
    notes = get_all_notes_for_export(db)
    
    md_content = f"# AI Notes Export\n\n"
    md_content += f"*Export Date: {datetime.utcnow().isoformat()}*\n\n"
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
    export_path = EXPORTS_DIR / f"notes_export_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.md"
    with open(export_path, "w", encoding="utf-8") as f:
        f.write(md_content)
    
    return FileResponse(
        export_path,
        media_type="text/markdown",
        filename=export_path.name
    )


# ============== Markdown Preview ==============

@app.post("/api/preview")
async def preview_markdown(data: dict):
    """Convert markdown to HTML for preview"""
    content = data.get("content", "")
    html = markdown.markdown(
        content,
        extensions=['fenced_code', 'tables', 'toc']
    )
    return {"html": html}


if __name__ == "__main__":
    import uvicorn
    from app.config import HOST, PORT
    uvicorn.run(app, host=HOST, port=PORT)
