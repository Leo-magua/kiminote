"""
Database models and operations for AI Notes
"""
from datetime import datetime
from typing import List, Optional
from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime, func
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from app.config import DATABASE_URL

# Create engine and session
engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


class Note(Base):
    """Note model"""
    __tablename__ = "notes"
    
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(200), nullable=False)
    content = Column(Text, nullable=False)
    summary = Column(Text, nullable=True)
    tags = Column(String(500), nullable=True)  # Comma-separated tags
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def to_dict(self) -> dict:
        """Convert note to dictionary"""
        return {
            "id": self.id,
            "title": self.title,
            "content": self.content,
            "summary": self.summary,
            "tags": self.tags.split(",") if self.tags else [],
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


# Create all tables
Base.metadata.create_all(bind=engine)


# Database dependency
def get_db():
    """Get database session"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# CRUD Operations

def create_note(db: Session, title: str, content: str, summary: str = None, tags: str = None) -> Note:
    """Create a new note"""
    db_note = Note(
        title=title,
        content=content,
        summary=summary,
        tags=tags
    )
    db.add(db_note)
    db.commit()
    db.refresh(db_note)
    return db_note


def get_note(db: Session, note_id: int) -> Optional[Note]:
    """Get a note by ID"""
    return db.query(Note).filter(Note.id == note_id).first()


def get_notes(db: Session, skip: int = 0, limit: int = 100, search: str = None) -> List[Note]:
    """Get all notes with optional search"""
    query = db.query(Note)
    
    if search:
        search_pattern = f"%{search}%"
        query = query.filter(
            (Note.title.ilike(search_pattern)) |
            (Note.content.ilike(search_pattern)) |
            (Note.tags.ilike(search_pattern))
        )
    
    return query.order_by(Note.updated_at.desc()).offset(skip).limit(limit).all()


def update_note(db: Session, note_id: int, title: str = None, content: str = None, 
                summary: str = None, tags: str = None) -> Optional[Note]:
    """Update a note"""
    db_note = db.query(Note).filter(Note.id == note_id).first()
    if not db_note:
        return None
    
    if title is not None:
        db_note.title = title
    if content is not None:
        db_note.content = content
    if summary is not None:
        db_note.summary = summary
    if tags is not None:
        db_note.tags = tags
    
    db_note.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(db_note)
    return db_note


def delete_note(db: Session, note_id: int) -> bool:
    """Delete a note"""
    db_note = db.query(Note).filter(Note.id == note_id).first()
    if not db_note:
        return False
    
    db.delete(db_note)
    db.commit()
    return True


def get_all_notes_for_export(db: Session) -> List[Note]:
    """Get all notes for export"""
    return db.query(Note).order_by(Note.created_at.desc()).all()


def get_notes_count(db: Session) -> int:
    """Get total notes count"""
    return db.query(Note).count()


def get_all_tags(db: Session) -> List[str]:
    """Get all unique tags"""
    notes_with_tags = db.query(Note.tags).filter(Note.tags.isnot(None)).all()
    all_tags = set()
    for (tags_str,) in notes_with_tags:
        if tags_str:
            all_tags.update(tag.strip() for tag in tags_str.split(","))
    return sorted(list(all_tags))
