"""
Database models and operations for AI Notes
"""
import uuid
from datetime import datetime, timedelta
from typing import List, Optional
from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime, func, ForeignKey, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session, relationship
from app.config import DATABASE_URL

# Create engine and session
engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


class User(Base):
    """User model"""
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, nullable=False, index=True)
    email = Column(String(100), unique=True, nullable=True)
    hashed_password = Column(String(255), nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    notes = relationship("Note", back_populates="user", cascade="all, delete-orphan")
    sessions = relationship("UserSession", back_populates="user", cascade="all, delete-orphan")
    
    def to_dict(self) -> dict:
        """Convert user to dictionary (excluding sensitive data)"""
        return {
            "id": self.id,
            "username": self.username,
            "email": self.email,
            "is_active": self.is_active,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class UserSession(Base):
    """User session model for token management"""
    __tablename__ = "user_sessions"
    
    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(String(64), unique=True, nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    expires_at = Column(DateTime, nullable=False)
    last_activity = Column(DateTime, default=datetime.utcnow)
    ip_address = Column(String(45), nullable=True)  # IPv6 compatible
    user_agent = Column(String(255), nullable=True)
    is_valid = Column(Boolean, default=True)
    
    # Relationships
    user = relationship("User", back_populates="sessions")
    
    def to_dict(self) -> dict:
        """Convert session to dictionary"""
        return {
            "id": self.id,
            "session_id": self.session_id,
            "user_id": self.user_id,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "expires_at": self.expires_at.isoformat() if self.expires_at else None,
            "last_activity": self.last_activity.isoformat() if self.last_activity else None,
            "is_valid": self.is_valid,
        }


class Note(Base):
    """Note model"""
    __tablename__ = "notes"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    title = Column(String(200), nullable=False)
    content = Column(Text, nullable=False)
    summary = Column(Text, nullable=True)
    tags = Column(String(500), nullable=True)  # Comma-separated tags
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user = relationship("User", back_populates="notes")
    
    def to_dict(self) -> dict:
        """Convert note to dictionary"""
        return {
            "id": self.id,
            "user_id": self.user_id,
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


# ============== User CRUD Operations ==============

def create_user(db: Session, username: str, hashed_password: str, email: str = None) -> User:
    """Create a new user"""
    db_user = User(
        username=username,
        email=email,
        hashed_password=hashed_password
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user


def get_user_by_username(db: Session, username: str) -> Optional[User]:
    """Get user by username"""
    return db.query(User).filter(User.username == username).first()


def get_user_by_email(db: Session, email: str) -> Optional[User]:
    """Get user by email"""
    return db.query(User).filter(User.email == email).first()


def get_user_by_id(db: Session, user_id: int) -> Optional[User]:
    """Get user by ID"""
    return db.query(User).filter(User.id == user_id).first()


def update_user(db: Session, user_id: int, **kwargs) -> Optional[User]:
    """Update user"""
    db_user = db.query(User).filter(User.id == user_id).first()
    if not db_user:
        return None
    
    for key, value in kwargs.items():
        if hasattr(db_user, key):
            setattr(db_user, key, value)
    
    db_user.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(db_user)
    return db_user


def delete_user(db: Session, user_id: int) -> bool:
    """Delete user"""
    db_user = db.query(User).filter(User.id == user_id).first()
    if not db_user:
        return False
    
    db.delete(db_user)
    db.commit()
    return True


# ============== Session CRUD Operations ==============

def create_session(db: Session, user_id: int, ip_address: str = None, user_agent: str = None, expires_days: int = 7) -> UserSession:
    """Create a new session"""
    session_id = str(uuid.uuid4())
    expires_at = datetime.utcnow() + timedelta(days=expires_days)
    
    db_session = UserSession(
        session_id=session_id,
        user_id=user_id,
        expires_at=expires_at,
        ip_address=ip_address,
        user_agent=user_agent
    )
    db.add(db_session)
    db.commit()
    db.refresh(db_session)
    return db_session


def get_session(db: Session, session_id: str) -> Optional[UserSession]:
    """Get session by session_id"""
    db_session = db.query(UserSession).filter(UserSession.session_id == session_id).first()
    if db_session:
        # Check if session is expired
        if db_session.expires_at < datetime.utcnow():
            db_session.is_valid = False
            db.commit()
        return db_session if db_session.is_valid else None
    return None


def get_user_sessions(db: Session, user_id: int) -> List[UserSession]:
    """Get all active sessions for a user"""
    return db.query(UserSession).filter(
        UserSession.user_id == user_id,
        UserSession.is_valid == True,
        UserSession.expires_at > datetime.utcnow()
    ).all()


def delete_session(db: Session, session_id: str) -> bool:
    """Invalidate a session"""
    db_session = db.query(UserSession).filter(UserSession.session_id == session_id).first()
    if not db_session:
        return False
    
    db_session.is_valid = False
    db.commit()
    return True


def delete_all_user_sessions(db: Session, user_id: int) -> int:
    """Invalidate all sessions for a user"""
    sessions = db.query(UserSession).filter(
        UserSession.user_id == user_id,
        UserSession.is_valid == True
    ).all()
    
    count = 0
    for session in sessions:
        session.is_valid = False
        count += 1
    
    db.commit()
    return count


def cleanup_expired_sessions(db: Session) -> int:
    """Clean up all expired sessions"""
    expired = db.query(UserSession).filter(
        UserSession.expires_at < datetime.utcnow(),
        UserSession.is_valid == True
    ).all()
    
    count = 0
    for session in expired:
        session.is_valid = False
        count += 1
    
    db.commit()
    return count


# ============== Note CRUD Operations ==============

def create_note(db: Session, user_id: int, title: str, content: str, summary: str = None, tags: str = None) -> Note:
    """Create a new note"""
    db_note = Note(
        user_id=user_id,
        title=title,
        content=content,
        summary=summary,
        tags=tags
    )
    db.add(db_note)
    db.commit()
    db.refresh(db_note)
    return db_note


def get_note(db: Session, note_id: int, user_id: int = None) -> Optional[Note]:
    """Get a note by ID, optionally filtered by user"""
    query = db.query(Note).filter(Note.id == note_id)
    if user_id is not None:
        query = query.filter(Note.user_id == user_id)
    return query.first()


def get_notes(db: Session, user_id: int, skip: int = 0, limit: int = 100, search: str = None) -> List[Note]:
    """Get all notes for a user with optional search"""
    query = db.query(Note).filter(Note.user_id == user_id)
    
    if search:
        search_pattern = f"%{search}%"
        query = query.filter(
            (Note.title.ilike(search_pattern)) |
            (Note.content.ilike(search_pattern)) |
            (Note.tags.ilike(search_pattern))
        )
    
    return query.order_by(Note.updated_at.desc()).offset(skip).limit(limit).all()


def update_note(db: Session, note_id: int, user_id: int = None, **kwargs) -> Optional[Note]:
    """Update a note, optionally ensuring it belongs to user"""
    query = db.query(Note).filter(Note.id == note_id)
    if user_id is not None:
        query = query.filter(Note.user_id == user_id)
    
    db_note = query.first()
    if not db_note:
        return None
    
    allowed_fields = ['title', 'content', 'summary', 'tags']
    for key, value in kwargs.items():
        if key in allowed_fields:
            setattr(db_note, key, value)
    
    db_note.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(db_note)
    return db_note


def delete_note(db: Session, note_id: int, user_id: int = None) -> bool:
    """Delete a note, optionally ensuring it belongs to user"""
    query = db.query(Note).filter(Note.id == note_id)
    if user_id is not None:
        query = query.filter(Note.user_id == user_id)
    
    db_note = query.first()
    if not db_note:
        return False
    
    db.delete(db_note)
    db.commit()
    return True


def get_all_notes_for_export(db: Session, user_id: int) -> List[Note]:
    """Get all notes for a user for export"""
    return db.query(Note).filter(Note.user_id == user_id).order_by(Note.created_at.desc()).all()


def get_notes_count(db: Session, user_id: int = None) -> int:
    """Get total notes count, optionally filtered by user"""
    query = db.query(Note)
    if user_id is not None:
        query = query.filter(Note.user_id == user_id)
    return query.count()


def get_all_tags(db: Session, user_id: int = None) -> List[str]:
    """Get all unique tags, optionally filtered by user"""
    query = db.query(Note.tags).filter(Note.tags.isnot(None))
    if user_id is not None:
        query = query.filter(Note.user_id == user_id)
    
    notes_with_tags = query.all()
    all_tags = set()
    for (tags_str,) in notes_with_tags:
        if tags_str:
            all_tags.update(tag.strip() for tag in tags_str.split(","))
    return sorted(list(all_tags))
