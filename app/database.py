"""
Database models and operations for AI Notes - Share functionality
"""
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
    
    # Relationships
    notes = relationship("Note", back_populates="user")
    shares = relationship("Share", back_populates="owner")
    
    def to_dict(self) -> dict:
        """Convert user to dictionary"""
        return {
            "id": self.id,
            "username": self.username,
            "email": self.email,
            "is_active": self.is_active,
            "created_at": self.created_at.isoformat() if self.created_at else None
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
    
    # Version control
    current_version = Column(Integer, default=1)  # Current version number
    
    # Relationships
    user = relationship("User", back_populates="notes")
    shares = relationship("Share", back_populates="note", cascade="all, delete-orphan")
    collaborators = relationship("NoteCollaborator", back_populates="note", cascade="all, delete-orphan")
    versions = relationship("NoteVersion", back_populates="note", cascade="all, delete-orphan")
    
    def to_dict(self) -> dict:
        """Convert note to dictionary"""
        return {
            "id": self.id,
            "user_id": self.user_id,
            "title": self.title,
            "content": self.content,
            "summary": self.summary,
            "tags": [tag.strip() for tag in self.tags.split(",")] if self.tags else [],
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "current_version": self.current_version,
        }


class Share(Base):
    """Share model for note sharing"""
    __tablename__ = "shares"
    
    id = Column(Integer, primary_key=True, index=True)
    note_id = Column(Integer, ForeignKey("notes.id"), nullable=False)
    owner_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    # Share token (unique, used in URL)
    token = Column(String(64), unique=True, nullable=False, index=True)
    
    # Share settings
    permission = Column(String(20), default="public")  # public, password, private
    is_active = Column(Boolean, default=True)
    password_hash = Column(String(255), nullable=True)  # Optional password protection
    max_access = Column(Integer, nullable=True)  # Max number of accesses (None = unlimited)
    access_count = Column(Integer, default=0)  # Current access count
    expires_at = Column(DateTime, nullable=True)  # Expiration time (None = never expires)
    
    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_accessed_at = Column(DateTime, nullable=True)
    
    # Relationships
    note = relationship("Note", back_populates="shares")
    owner = relationship("User", back_populates="shares")
    
    def is_valid(self) -> bool:
        """Check if share is valid (active and not expired)"""
        if not self.is_active:
            return False
        if self.expires_at and self.expires_at < datetime.utcnow():
            return False
        return True
    
    def is_expired(self) -> bool:
        """Check if share is expired"""
        if self.expires_at and self.expires_at < datetime.utcnow():
            return True
        return False
    
    def to_dict(self) -> dict:
        """Convert share to dictionary (exclude sensitive data)"""
        return {
            "id": self.id,
            "token": self.token,
            "note_id": self.note_id,
            "permission": self.permission,
            "is_active": self.is_active,
            "has_password": self.password_hash is not None,
            "max_access": self.max_access,
            "access_count": self.access_count,
            "expires_at": self.expires_at.isoformat() if self.expires_at else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "last_accessed_at": self.last_accessed_at.isoformat() if self.last_accessed_at else None,
            "is_expired": self.is_expired(),
        }
    
    def is_valid(self) -> bool:
        """Check if share is still valid (active and not expired)"""
        if not self.is_active:
            return False
        if self.expires_at and self.expires_at < datetime.utcnow():
            return False
        if self.max_access and self.access_count >= self.max_access:
            return False
        return True


class UserSession(Base):
    """User session model"""
    __tablename__ = "user_sessions"
    
    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(String(36), unique=True, nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    is_valid = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    expires_at = Column(DateTime, nullable=False)
    last_activity = Column(DateTime, nullable=True)
    ip_address = Column(String(45), nullable=True)
    user_agent = Column(String(255), nullable=True)
    
    # Relationships
    user = relationship("User")


class NoteVersion(Base):
    """Note version history for tracking changes"""
    __tablename__ = "note_versions"
    
    id = Column(Integer, primary_key=True, index=True)
    note_id = Column(Integer, ForeignKey("notes.id"), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    # Version data
    version_number = Column(Integer, nullable=False)  # Sequential version number
    title = Column(String(200), nullable=False)
    content = Column(Text, nullable=False)
    summary = Column(Text, nullable=True)
    tags = Column(String(500), nullable=True)
    
    # Change metadata
    change_summary = Column(String(500), nullable=True)  # Brief description of changes
    change_type = Column(String(50), default="edit")  # create, edit, delete, restore
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    note = relationship("Note", back_populates="versions")
    user = relationship("User")
    
    def to_dict(self) -> dict:
        """Convert version to dictionary"""
        return {
            "id": self.id,
            "note_id": self.note_id,
            "user_id": self.user_id,
            "version_number": self.version_number,
            "title": self.title,
            "content": self.content,
            "summary": self.summary,
            "tags": [tag.strip() for tag in self.tags.split(",")] if self.tags else [],
            "change_summary": self.change_summary,
            "change_type": self.change_type,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class NoteCollaborator(Base):
    """Note collaborators - users who can edit shared notes"""
    __tablename__ = "note_collaborators"
    
    id = Column(Integer, primary_key=True, index=True)
    note_id = Column(Integer, ForeignKey("notes.id"), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    
    # Permission level
    permission = Column(String(20), default="write")  # read, write, admin
    
    # Who added this collaborator
    added_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    note = relationship("Note", back_populates="collaborators")
    user = relationship("User", foreign_keys=[user_id])
    
    def to_dict(self) -> dict:
        """Convert collaborator to dictionary"""
        return {
            "id": self.id,
            "note_id": self.note_id,
            "user_id": self.user_id,
            "permission": self.permission,
            "added_by": self.added_by,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


class CollaborationSession(Base):
    """Active collaboration sessions for real-time editing"""
    __tablename__ = "collaboration_sessions"
    
    id = Column(Integer, primary_key=True, index=True)
    note_id = Column(Integer, ForeignKey("notes.id"), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    # Session info
    session_id = Column(String(36), unique=True, nullable=False, index=True)
    websocket_id = Column(String(64), nullable=True)  # WebSocket connection ID
    
    # User presence
    is_active = Column(Boolean, default=True)
    last_activity = Column(DateTime, default=datetime.utcnow)
    
    # Cursor position (for showing where user is editing)
    cursor_position = Column(Integer, nullable=True)
    selection_start = Column(Integer, nullable=True)
    selection_end = Column(Integer, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    note = relationship("Note")
    user = relationship("User")
    
    def to_dict(self) -> dict:
        """Convert session to dictionary"""
        return {
            "id": self.id,
            "note_id": self.note_id,
            "user_id": self.user_id,
            "session_id": self.session_id,
            "is_active": self.is_active,
            "cursor_position": self.cursor_position,
            "selection_start": self.selection_start,
            "selection_end": self.selection_end,
            "last_activity": self.last_activity.isoformat() if self.last_activity else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class Attachment(Base):
    """File attachments for notes"""
    __tablename__ = "attachments"
    
    id = Column(Integer, primary_key=True, index=True)
    note_id = Column(Integer, ForeignKey("notes.id"), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    # File info
    filename = Column(String(255), nullable=False)
    original_filename = Column(String(255), nullable=False)
    file_path = Column(String(500), nullable=False)
    file_size = Column(Integer, nullable=False)  # in bytes
    mime_type = Column(String(100), nullable=False)
    
    # File type category
    file_type = Column(String(20), nullable=False)  # image, document, video, audio, other
    
    # For images
    width = Column(Integer, nullable=True)
    height = Column(Integer, nullable=True)
    
    # Access URL
    url_path = Column(String(255), unique=True, nullable=False, index=True)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    note = relationship("Note")
    user = relationship("User")
    
    def to_dict(self) -> dict:
        """Convert attachment to dictionary"""
        return {
            "id": self.id,
            "note_id": self.note_id,
            "user_id": self.user_id,
            "filename": self.filename,
            "original_filename": self.original_filename,
            "file_size": self.file_size,
            "mime_type": self.mime_type,
            "file_type": self.file_type,
            "width": self.width,
            "height": self.height,
            "url": f"/uploads/{self.url_path}",
            "created_at": self.created_at.isoformat() if self.created_at else None,
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


def get_all_users(db: Session) -> List[User]:
    """Get all users"""
    return db.query(User).all()


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
        if key in allowed_fields and value is not None:
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


# ============== Share CRUD Operations ==============

import secrets

def generate_share_token() -> str:
    """Generate a unique share token"""
    return secrets.token_urlsafe(32)


def create_share(
    db: Session,
    note_id: int,
    owner_id: int,
    permission: str = "public",
    password: str = None,
    max_access: int = None,
    expires_days: int = None
) -> Optional[Share]:
    """Create a new share for a note"""
    # Verify note exists and belongs to owner
    note = get_note(db, note_id, user_id=owner_id)
    if not note:
        return None
    
    # Generate unique token
    token = generate_share_token()
    while db.query(Share).filter(Share.token == token).first():
        token = generate_share_token()
    
    # Hash password if provided
    password_hash = None
    if password:
        from app.auth import get_password_hash
        password_hash = get_password_hash(password)
    
    # Calculate expiration
    expires_at = None
    if expires_days:
        expires_at = datetime.utcnow() + timedelta(days=expires_days)
    
    # Create share
    share = Share(
        note_id=note_id,
        owner_id=owner_id,
        token=token,
        permission=permission,
        password_hash=password_hash,
        max_access=max_access,
        expires_at=expires_at
    )
    db.add(share)
    db.commit()
    db.refresh(share)
    
    return share


def get_share_by_token(db: Session, token: str) -> Optional[Share]:
    """Get share by token"""
    return db.query(Share).filter(Share.token == token).first()


def verify_share_access(db: Session, token: str, password: str = None) -> Optional[dict]:
    """
    Verify if a share is accessible.
    Returns note dict if accessible, None otherwise.
    """
    share = get_share_by_token(db, token)
    if not share:
        return None
    
    # Check if share is active
    if not share.is_active:
        return None
    
    # Check expiration
    if share.expires_at and share.expires_at < datetime.utcnow():
        return None
    
    # Check max access
    if share.max_access and share.access_count >= share.max_access:
        return None
    
    # Verify password if required
    if share.password_hash:
        if not password:
            return {"error": "password_required", "share": share.to_dict()}
        from app.auth import verify_password
        if not verify_password(password, share.password_hash):
            return {"error": "invalid_password", "share": share.to_dict()}
    
    # Increment access count
    share.access_count += 1
    share.last_accessed_at = datetime.utcnow()
    db.commit()
    
    # Get note
    note = share.note
    return {
        "note": note.to_dict(),
        "share": share.to_dict()
    }


def revoke_share(db: Session, share_id: int, owner_id: int) -> bool:
    """Revoke a share (deactivate)"""
    share = db.query(Share).filter(
        Share.id == share_id,
        Share.owner_id == owner_id
    ).first()
    if not share:
        return False
    
    share.is_active = False
    db.commit()
    return True


def get_note_shares(db: Session, note_id: int, owner_id: int) -> List[Share]:
    """Get all shares for a note (owner only)"""
    return db.query(Share).filter(
        Share.note_id == note_id,
        Share.owner_id == owner_id
    ).all()


def revoke_all_shares_for_note(db: Session, note_id: int, owner_id: int) -> int:
    """Revoke all shares for a note"""
    shares = db.query(Share).filter(
        Share.note_id == note_id,
        Share.owner_id == owner_id
    ).all()
    count = len(shares)
    for share in shares:
        share.is_active = False
    db.commit()
    return count


def get_shares_by_note(db: Session, note_id: int, user_id: int) -> List[Share]:
    """Get all shares for a specific note"""
    return db.query(Share).filter(
        Share.note_id == note_id,
        Share.owner_id == user_id
    ).all()


def get_all_user_shares(db: Session, user_id: int) -> List[Share]:
    """Get all shares created by a user"""
    return db.query(Share).filter(
        Share.owner_id == user_id
    ).order_by(Share.created_at.desc()).all()


def update_share(
    db: Session,
    share_token: str,
    owner_id: int,
    **kwargs
) -> Optional[Share]:
    """Update share settings"""
    share = get_share_by_token(db, share_token)
    if not share or share.owner_id != owner_id:
        return None
    
    if "permission" in kwargs:
        # Handle permission changes
        permission = kwargs["permission"]
        if permission == "public":
            share.password_hash = None
        elif permission == "private":
            share.is_active = False
    
    if "password" in kwargs:
        from app.auth import get_password_hash
        password = kwargs["password"]
        if password:
            share.password_hash = get_password_hash(password)
        else:
            share.password_hash = None
    
    if "is_active" in kwargs:
        share.is_active = kwargs["is_active"]
    
    if "expires_at" in kwargs:
        share.expires_at = kwargs["expires_at"]
    
    db.commit()
    db.refresh(share)
    return share


def delete_share(db: Session, share_token: str, owner_id: int) -> bool:
    """Delete a share by token"""
    share = get_share_by_token(db, share_token)
    if not share or share.owner_id != owner_id:
        return False
    
    db.delete(share)
    db.commit()
    return True


def verify_share_password(db: Session, share_token: str, password: str) -> bool:
    """Verify password for a share"""
    share = get_share_by_token(db, share_token)
    if not share or not share.password_hash:
        return False
    
    from app.auth import verify_password
    return verify_password(password, share.password_hash)


def increment_share_access_count(db: Session, share_token: str) -> bool:
    """Increment access count for a share"""
    share = get_share_by_token(db, share_token)
    if not share:
        return False
    
    share.access_count += 1
    share.last_accessed_at = datetime.utcnow()
    db.commit()
    return True


# ============== Session CRUD Operations ==============

import uuid

def create_session(db: Session, user_id: int, ip_address: str = None, user_agent: str = None, expires_days: int = 7) -> str:
    """Create a new session for a user and return the session token"""
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
    return session_id


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
    count = len(sessions)
    for session in sessions:
        session.is_valid = False
    db.commit()
    return count


def cleanup_expired_sessions(db: Session) -> int:
    """Clean up all expired sessions"""
    expired = db.query(UserSession).filter(
        UserSession.expires_at < datetime.utcnow(),
        UserSession.is_valid == True
    ).all()
    count = len(expired)
    for session in expired:
        session.is_valid = False
    db.commit()
    return count


# ============== Statistics Operations ==============

def get_notes_statistics(db: Session, user_id: int) -> dict:
    """Get detailed writing statistics for a user"""
    from sqlalchemy import func
    
    # Get all notes for user
    notes = db.query(Note).filter(Note.user_id == user_id).all()
    
    if not notes:
        return {
            "total_notes": 0,
            "total_words": 0,
            "total_characters": 0,
            "avg_words_per_note": 0.0,
            "avg_characters_per_note": 0.0,
            "notes_this_week": 0,
            "notes_this_month": 0,
            "current_streak": 0,
            "first_note_date": None,
            "activity_by_date": [],
            "hourly_distribution": [],
            "weekday_distribution": []
        }
    
    # Basic counts
    total_notes = len(notes)
    total_chars = sum(len(note.content) for note in notes)
    total_words = sum(len(note.content.split()) for note in notes)
    
    # Date calculations
    now = datetime.utcnow()
    week_start = now - timedelta(days=now.weekday())
    month_start = now.replace(day=1)
    
    notes_this_week = sum(1 for note in notes if note.created_at >= week_start)
    notes_this_month = sum(1 for note in notes if note.created_at >= month_start)
    
    # First note date
    first_note = min(notes, key=lambda x: x.created_at)
    first_note_date = first_note.created_at.isoformat() if first_note else None
    
    # Calculate writing streak
    writing_days = set()
    for note in notes:
        writing_days.add(note.created_at.date())
    
    current_streak = 0
    today = now.date()
    for i in range(365):  # Check up to 1 year back
        check_date = today - timedelta(days=i)
        if check_date in writing_days:
            current_streak += 1
        else:
            if i > 0:  # Break if not consecutive from today
                break
    
    # Activity by date (last 30 days)
    activity_by_date = []
    for i in range(29, -1, -1):
        date = (now - timedelta(days=i)).date()
        day_notes = [n for n in notes if n.created_at.date() == date]
        if day_notes or True:  # Include empty days for complete chart
            activity_by_date.append({
                "date": date.isoformat(),
                "notes_created": len(day_notes),
                "characters_written": sum(len(n.content) for n in day_notes)
            })
    
    # Hourly distribution
    hourly_counts = [0] * 24
    for note in notes:
        hour = note.created_at.hour
        hourly_counts[hour] += 1
    
    hourly_distribution = [
        {"hour": h, "count": c} for h, c in enumerate(hourly_counts)
    ]
    
    # Weekday distribution
    weekday_names = ["周一", "周二", "周三", "周四", "周五", "周六", "周日"]
    weekday_counts = [0] * 7
    for note in notes:
        # weekday() returns 0=Monday, 6=Sunday
        weekday = note.created_at.weekday()
        weekday_counts[weekday] += 1
    
    weekday_distribution = [
        {"day": weekday_names[i], "count": c} for i, c in enumerate(weekday_counts)
    ]
    
    return {
        "total_notes": total_notes,
        "total_words": total_words,
        "total_characters": total_chars,
        "avg_words_per_note": round(total_words / total_notes, 1),
        "avg_characters_per_note": round(total_chars / total_notes, 1),
        "notes_this_week": notes_this_week,
        "notes_this_month": notes_this_month,
        "current_streak": current_streak,
        "first_note_date": first_note_date,
        "activity_by_date": activity_by_date,
        "hourly_distribution": hourly_distribution,
        "weekday_distribution": weekday_distribution
    }


def get_daily_writing_stats(db: Session, user_id: int, days: int = 7) -> List[dict]:
    """Get daily writing statistics for the specified number of days"""
    now = datetime.utcnow()
    start_date = now - timedelta(days=days)
    
    # Get notes in date range
    notes = db.query(Note).filter(
        Note.user_id == user_id,
        Note.created_at >= start_date
    ).all()
    
    # Group by date
    stats_by_date = {}
    for i in range(days):
        date = (now - timedelta(days=days - 1 - i)).date()
        stats_by_date[date.isoformat()] = {
            "date": date.isoformat(),
            "notes_created": 0,
            "total_characters": 0,
            "avg_characters": 0.0
        }
    
    for note in notes:
        date_key = note.created_at.date().isoformat()
        if date_key in stats_by_date:
            stats_by_date[date_key]["notes_created"] += 1
            stats_by_date[date_key]["total_characters"] += len(note.content)
    
    # Calculate averages
    for date_key, stat in stats_by_date.items():
        if stat["notes_created"] > 0:
            stat["avg_characters"] = round(stat["total_characters"] / stat["notes_created"], 1)
    
    return list(stats_by_date.values())


# ============== Version Control Operations ==============

def create_note_version(
    db: Session,
    note_id: int,
    user_id: int,
    title: str,
    content: str,
    summary: str = None,
    tags: str = None,
    change_summary: str = None,
    change_type: str = "edit"
) -> NoteVersion:
    """Create a new version for a note"""
    # Get the latest version number
    latest_version = db.query(NoteVersion).filter(
        NoteVersion.note_id == note_id
    ).order_by(NoteVersion.version_number.desc()).first()
    
    version_number = 1 if not latest_version else latest_version.version_number + 1
    
    version = NoteVersion(
        note_id=note_id,
        user_id=user_id,
        version_number=version_number,
        title=title,
        content=content,
        summary=summary,
        tags=tags,
        change_summary=change_summary,
        change_type=change_type
    )
    db.add(version)
    
    # Update note's current version
    note = db.query(Note).filter(Note.id == note_id).first()
    if note:
        note.current_version = version_number
    
    db.commit()
    db.refresh(version)
    return version


def get_note_versions(db: Session, note_id: int, limit: int = 50) -> List[NoteVersion]:
    """Get version history for a note"""
    return db.query(NoteVersion).filter(
        NoteVersion.note_id == note_id
    ).order_by(NoteVersion.version_number.desc()).limit(limit).all()


def get_note_version(db: Session, version_id: int) -> Optional[NoteVersion]:
    """Get a specific version by ID"""
    return db.query(NoteVersion).filter(NoteVersion.id == version_id).first()


def get_note_version_by_number(db: Session, note_id: int, version_number: int) -> Optional[NoteVersion]:
    """Get a specific version by note ID and version number"""
    return db.query(NoteVersion).filter(
        NoteVersion.note_id == note_id,
        NoteVersion.version_number == version_number
    ).first()


def restore_note_version(db: Session, note_id: int, version_id: int, user_id: int) -> Optional[Note]:
    """Restore a note to a specific version"""
    version = db.query(NoteVersion).filter(
        NoteVersion.id == version_id,
        NoteVersion.note_id == note_id
    ).first()
    
    if not version:
        return None
    
    # Update the note
    note = db.query(Note).filter(Note.id == note_id).first()
    if not note:
        return None
    
    note.title = version.title
    note.content = version.content
    note.summary = version.summary
    note.tags = version.tags
    note.updated_at = datetime.utcnow()
    
    # Create a new version for the restore action
    create_note_version(
        db,
        note_id=note_id,
        user_id=user_id,
        title=version.title,
        content=version.content,
        summary=version.summary,
        tags=version.tags,
        change_summary=f"Restored to version {version.version_number}",
        change_type="restore"
    )
    
    db.commit()
    db.refresh(note)
    return note


# ============== Attachment CRUD Operations ==============

def create_attachment(
    db: Session,
    note_id: int,
    user_id: int,
    filename: str,
    original_filename: str,
    file_path: str,
    file_size: int,
    mime_type: str,
    file_type: str,
    width: int = None,
    height: int = None,
    url_path: str = None
) -> Attachment:
    """Create a new attachment record"""
    attachment = Attachment(
        note_id=note_id,
        user_id=user_id,
        filename=filename,
        original_filename=original_filename,
        file_path=file_path,
        file_size=file_size,
        mime_type=mime_type,
        file_type=file_type,
        width=width,
        height=height,
        url_path=url_path or filename
    )
    db.add(attachment)
    db.commit()
    db.refresh(attachment)
    return attachment


def get_attachment(db: Session, attachment_id: int) -> Optional[Attachment]:
    """Get attachment by ID"""
    return db.query(Attachment).filter(Attachment.id == attachment_id).first()


def get_attachment_by_url_path(db: Session, url_path: str) -> Optional[Attachment]:
    """Get attachment by URL path"""
    return db.query(Attachment).filter(Attachment.url_path == url_path).first()


def get_note_attachments(db: Session, note_id: int) -> List[Attachment]:
    """Get all attachments for a note"""
    return db.query(Attachment).filter(Attachment.note_id == note_id).order_by(Attachment.created_at.desc()).all()


def get_user_attachments(db: Session, user_id: int, limit: int = 100) -> List[Attachment]:
    """Get all attachments for a user"""
    return db.query(Attachment).filter(Attachment.user_id == user_id).order_by(Attachment.created_at.desc()).limit(limit).all()


def delete_attachment(db: Session, attachment_id: int, user_id: int = None) -> bool:
    """Delete an attachment"""
    query = db.query(Attachment).filter(Attachment.id == attachment_id)
    if user_id is not None:
        query = query.filter(Attachment.user_id == user_id)
    
    attachment = query.first()
    if not attachment:
        return False
    
    db.delete(attachment)
    db.commit()
    return True


def delete_note_attachments(db: Session, note_id: int) -> int:
    """Delete all attachments for a note"""
    attachments = db.query(Attachment).filter(Attachment.note_id == note_id).all()
    count = len(attachments)
    for attachment in attachments:
        db.delete(attachment)
    db.commit()
    return count


def get_attachment_count(db: Session, note_id: int = None, user_id: int = None) -> int:
    """Get attachment count, optionally filtered by note or user"""
    query = db.query(Attachment)
    if note_id is not None:
        query = query.filter(Attachment.note_id == note_id)
    if user_id is not None:
        query = query.filter(Attachment.user_id == user_id)
    return query.count()


def cleanup_orphan_attachments(db: Session, user_id: int = None) -> int:
    """Clean up attachments that don't have associated notes"""
    from sqlalchemy.orm import joinedload
    
    query = db.query(Attachment).options(joinedload(Attachment.note))
    if user_id is not None:
        query = query.filter(Attachment.user_id == user_id)
    
    attachments = query.all()
    deleted_count = 0
    
    for attachment in attachments:
        if attachment.note is None:
            db.delete(attachment)
            deleted_count += 1
    
    if deleted_count > 0:
        db.commit()
    
    return deleted_count


def compare_versions(db: Session, version_id1: int, version_id2: int) -> dict:
    """Compare two versions and return differences"""
    v1 = db.query(NoteVersion).filter(NoteVersion.id == version_id1).first()
    v2 = db.query(NoteVersion).filter(NoteVersion.id == version_id2).first()
    
    if not v1 or not v2:
        return None
    
    return {
        "version1": v1.to_dict(),
        "version2": v2.to_dict(),
        "title_changed": v1.title != v2.title,
        "content_changed": v1.content != v2.content,
        "tags_changed": v1.tags != v2.tags,
    }


def cleanup_old_versions(db: Session, note_id: int, keep_count: int = 100) -> int:
    """Clean up old versions, keeping only the specified number of recent versions"""
    versions = db.query(NoteVersion).filter(
        NoteVersion.note_id == note_id
    ).order_by(NoteVersion.version_number.desc()).offset(keep_count).all()
    
    count = len(versions)
    for version in versions:
        db.delete(version)
    
    db.commit()
    return count


# ============== Collaboration Operations ==============

def add_collaborator(
    db: Session,
    note_id: int,
    user_id: int,
    permission: str = "write",
    added_by: int = None
) -> Optional[NoteCollaborator]:
    """Add a collaborator to a note"""
    # Check if already a collaborator
    existing = db.query(NoteCollaborator).filter(
        NoteCollaborator.note_id == note_id,
        NoteCollaborator.user_id == user_id
    ).first()
    
    if existing:
        # Update permission
        existing.permission = permission
        existing.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(existing)
        return existing
    
    collaborator = NoteCollaborator(
        note_id=note_id,
        user_id=user_id,
        permission=permission,
        added_by=added_by
    )
    db.add(collaborator)
    db.commit()
    db.refresh(collaborator)
    return collaborator


def remove_collaborator(db: Session, note_id: int, user_id: int) -> bool:
    """Remove a collaborator from a note"""
    collaborator = db.query(NoteCollaborator).filter(
        NoteCollaborator.note_id == note_id,
        NoteCollaborator.user_id == user_id
    ).first()
    
    if not collaborator:
        return False
    
    db.delete(collaborator)
    db.commit()
    return True


def get_note_collaborators(db: Session, note_id: int) -> List[NoteCollaborator]:
    """Get all collaborators for a note"""
    return db.query(NoteCollaborator).filter(
        NoteCollaborator.note_id == note_id
    ).all()


def get_user_collaborated_notes(db: Session, user_id: int) -> List[Note]:
    """Get all notes that a user is a collaborator on"""
    collaborations = db.query(NoteCollaborator).filter(
        NoteCollaborator.user_id == user_id
    ).all()
    
    note_ids = [c.note_id for c in collaborations]
    if not note_ids:
        return []
    
    return db.query(Note).filter(Note.id.in_(note_ids)).all()


def check_collaborator_permission(db: Session, note_id: int, user_id: int) -> Optional[str]:
    """Check if a user is a collaborator on a note and return their permission level"""
    collaborator = db.query(NoteCollaborator).filter(
        NoteCollaborator.note_id == note_id,
        NoteCollaborator.user_id == user_id
    ).first()
    
    return collaborator.permission if collaborator else None


def is_note_owner_or_collaborator(db: Session, note_id: int, user_id: int) -> bool:
    """Check if user is the owner or a collaborator of the note"""
    note = db.query(Note).filter(Note.id == note_id).first()
    if not note:
        return False
    
    # Check if owner
    if note.user_id == user_id:
        return True
    
    # Check if collaborator
    permission = check_collaborator_permission(db, note_id, user_id)
    return permission is not None


# ============== Collaboration Session Operations ==============

def create_collaboration_session(
    db: Session,
    note_id: int,
    user_id: int,
    websocket_id: str = None
) -> CollaborationSession:
    """Create a new collaboration session"""
    import uuid
    
    session = CollaborationSession(
        note_id=note_id,
        user_id=user_id,
        session_id=str(uuid.uuid4()),
        websocket_id=websocket_id
    )
    db.add(session)
    db.commit()
    db.refresh(session)
    return session


def get_collaboration_session(db: Session, session_id: str) -> Optional[CollaborationSession]:
    """Get a collaboration session by ID"""
    return db.query(CollaborationSession).filter(
        CollaborationSession.session_id == session_id
    ).first()


def get_active_collaborators(db: Session, note_id: int) -> List[CollaborationSession]:
    """Get all active collaboration sessions for a note"""
    # Clean up inactive sessions first (older than 5 minutes)
    cutoff = datetime.utcnow() - timedelta(minutes=5)
    db.query(CollaborationSession).filter(
        CollaborationSession.note_id == note_id,
        CollaborationSession.last_activity < cutoff
    ).update({"is_active": False})
    db.commit()
    
    return db.query(CollaborationSession).filter(
        CollaborationSession.note_id == note_id,
        CollaborationSession.is_active == True
    ).all()


def update_collaboration_session(
    db: Session,
    session_id: str,
    cursor_position: int = None,
    selection_start: int = None,
    selection_end: int = None
) -> Optional[CollaborationSession]:
    """Update collaboration session with cursor position"""
    session = db.query(CollaborationSession).filter(
        CollaborationSession.session_id == session_id
    ).first()
    
    if not session:
        return None
    
    if cursor_position is not None:
        session.cursor_position = cursor_position
    if selection_start is not None:
        session.selection_start = selection_start
    if selection_end is not None:
        session.selection_end = selection_end
    
    session.last_activity = datetime.utcnow()
    db.commit()
    db.refresh(session)
    return session


def deactivate_collaboration_session(db: Session, session_id: str) -> bool:
    """Deactivate a collaboration session"""
    session = db.query(CollaborationSession).filter(
        CollaborationSession.session_id == session_id
    ).first()
    
    if not session:
        return False
    
    session.is_active = False
    db.commit()
    return True


def cleanup_inactive_sessions(db: Session, inactive_minutes: int = 30) -> int:
    """Clean up inactive collaboration sessions"""
    cutoff = datetime.utcnow() - timedelta(minutes=inactive_minutes)
    
    sessions = db.query(CollaborationSession).filter(
        CollaborationSession.is_active == True,
        CollaborationSession.last_activity < cutoff
    ).all()
    
    count = len(sessions)
    for session in sessions:
        session.is_active = False
    
    db.commit()
    return count


# ============== Conflict Resolution Operations ==============

def detect_conflict(
    db: Session,
    note_id: int,
    base_version: int,
    current_version: int
) -> dict:
    """Detect if there's a conflict between versions"""
    base = get_note_version_by_number(db, note_id, base_version)
    current = get_note_version_by_number(db, note_id, current_version)
    
    if not base or not current:
        return {"has_conflict": False, "error": "Version not found"}
    
    # If versions are the same, no conflict
    if base_version == current_version:
        return {"has_conflict": False}
    
    # Check what fields changed
    return {
        "has_conflict": True,
        "base_version": base.to_dict(),
        "current_version": current.to_dict(),
        "title_changed": base.title != current.title,
        "content_changed": base.content != current.content,
        "tags_changed": base.tags != current.tags,
    }


def merge_changes(
    db: Session,
    note_id: int,
    user_id: int,
    base_version: int,
    changes: dict
) -> Optional[Note]:
    """Merge changes from a conflict resolution"""
    note = db.query(Note).filter(Note.id == note_id).first()
    if not note:
        return None
    
    # Apply changes
    if "title" in changes:
        note.title = changes["title"]
    if "content" in changes:
        note.content = changes["content"]
    if "summary" in changes:
        note.summary = changes["summary"]
    if "tags" in changes:
        note.tags = changes["tags"]
    
    note.updated_at = datetime.utcnow()
    
    # Create a new version
    create_note_version(
        db,
        note_id=note_id,
        user_id=user_id,
        title=note.title,
        content=note.content,
        summary=note.summary,
        tags=note.tags,
        change_summary=changes.get("change_summary", "Merged changes"),
        change_type="merge"
    )
    
    db.commit()
    db.refresh(note)
    return note
