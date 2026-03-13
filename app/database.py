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
    shares = relationship("Share", back_populates="user", cascade="all, delete-orphan")
    
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
    shares = relationship("Share", back_populates="note", cascade="all, delete-orphan")
    
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


class Share(Base):
    """Note share model"""
    __tablename__ = "shares"
    
    id = Column(Integer, primary_key=True, index=True)
    share_token = Column(String(32), unique=True, nullable=False, index=True)  # 8位短链接
    note_id = Column(Integer, ForeignKey("notes.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    permission = Column(String(20), default="public")  # public, password, private
    password_hash = Column(String(255), nullable=True)  # 密码保护时使用
    expires_at = Column(DateTime, nullable=True)  # 过期时间，null表示永不过期
    access_count = Column(Integer, default=0)  # 访问次数统计
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    is_active = Column(Boolean, default=True)  # 是否激活
    
    # Relationships
    note = relationship("Note", back_populates="shares")
    user = relationship("User", back_populates="shares")
    
    def to_dict(self) -> dict:
        """Convert share to dictionary"""
        return {
            "id": self.id,
            "share_token": self.share_token,
            "note_id": self.note_id,
            "user_id": self.user_id,
            "permission": self.permission,
            "has_password": self.password_hash is not None,
            "expires_at": self.expires_at.isoformat() if self.expires_at else None,
            "access_count": self.access_count,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "is_active": self.is_active,
            "is_expired": self.expires_at is not None and self.expires_at < datetime.utcnow(),
        }
    
    def is_valid(self) -> bool:
        """Check if share is valid (active and not expired)"""
        if not self.is_active:
            return False
        if self.expires_at and self.expires_at < datetime.utcnow():
            return False
        return True


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


# ============== Statistics Operations ==============

def get_notes_statistics(db: Session, user_id: int) -> dict:
    """Get comprehensive statistics for user's notes"""
    from sqlalchemy import func
    
    # Basic counts
    total_notes = get_notes_count(db, user_id=user_id)
    
    # Total word count (title + content)
    notes = db.query(Note).filter(Note.user_id == user_id).all()
    total_words = 0
    total_chars = 0
    for note in notes:
        # Count words in content (split by whitespace)
        content_words = len(note.content.split()) if note.content else 0
        title_words = len(note.title.split()) if note.title else 0
        total_words += content_words + title_words
        
        # Count characters (including spaces)
        total_chars += len(note.content) if note.content else 0
        total_chars += len(note.title) if note.title else 0
    
    # Get first note date (for calculating writing streak)
    first_note = db.query(Note).filter(
        Note.user_id == user_id
    ).order_by(Note.created_at.asc()).first()
    
    # Writing activity by date (last 30 days)
    from datetime import datetime, timedelta
    thirty_days_ago = datetime.utcnow() - timedelta(days=30)
    
    activity_query = db.query(
        func.date(Note.created_at).label('date'),
        func.count(Note.id).label('count'),
        func.sum(func.length(Note.content)).label('chars')
    ).filter(
        Note.user_id == user_id,
        Note.created_at >= thirty_days_ago
    ).group_by(
        func.date(Note.created_at)
    ).order_by(func.date(Note.created_at)).all()
    
    activity_by_date = [
        {
            "date": row.date.isoformat() if row.date else None,
            "notes_created": row.count,
            "characters_written": row.chars or 0
        }
        for row in activity_query
    ]
    
    # Notes by hour of day (writing habits)
    hour_distribution = db.query(
        func.strftime('%H', Note.created_at).label('hour'),
        func.count(Note.id).label('count')
    ).filter(
        Note.user_id == user_id
    ).group_by(
        func.strftime('%H', Note.created_at)
    ).order_by(func.strftime('%H', Note.created_at)).all()
    
    hourly_stats = [
        {"hour": int(row.hour), "count": row.count}
        for row in hour_distribution
    ]
    
    # Notes by day of week
    weekday_distribution = db.query(
        func.strftime('%w', Note.created_at).label('weekday'),
        func.count(Note.id).label('count')
    ).filter(
        Note.user_id == user_id
    ).group_by(
        func.strftime('%w', Note.created_at)
    ).order_by(func.strftime('%w', Note.created_at)).all()
    
    weekday_names = ['周日', '周一', '周二', '周三', '周四', '周五', '周六']
    weekday_stats = [
        {"day": weekday_names[int(row.weekday)], "count": row.count}
        for row in weekday_distribution
    ]
    
    # Calculate writing streak (consecutive days with notes)
    streak = 0
    if activity_by_date:
        today = datetime.utcnow().date()
        # Check if wrote today
        wrote_today = any(
            datetime.fromisoformat(a['date']).date() == today 
            for a in activity_by_date
        )
        
        # Start from today or yesterday
        check_date = today if wrote_today else today - timedelta(days=1)
        
        all_activity_dates = set(
            datetime.fromisoformat(a['date']).date() 
            for a in activity_by_date
        )
        
        while check_date in all_activity_dates:
            streak += 1
            check_date -= timedelta(days=1)
    
    # Average stats
    avg_words_per_note = round(total_words / total_notes, 1) if total_notes > 0 else 0
    avg_chars_per_note = round(total_chars / total_notes, 1) if total_notes > 0 else 0
    
    # Notes created this week
    week_ago = datetime.utcnow() - timedelta(days=7)
    notes_this_week = db.query(Note).filter(
        Note.user_id == user_id,
        Note.created_at >= week_ago
    ).count()
    
    # Notes created this month
    month_ago = datetime.utcnow() - timedelta(days=30)
    notes_this_month = db.query(Note).filter(
        Note.user_id == user_id,
        Note.created_at >= month_ago
    ).count()
    
    return {
        "total_notes": total_notes,
        "total_words": total_words,
        "total_characters": total_chars,
        "avg_words_per_note": avg_words_per_note,
        "avg_characters_per_note": avg_chars_per_note,
        "notes_this_week": notes_this_week,
        "notes_this_month": notes_this_month,
        "current_streak": streak,
        "first_note_date": first_note.created_at.isoformat() if first_note else None,
        "activity_by_date": activity_by_date,
        "hourly_distribution": hourly_stats,
        "weekday_distribution": weekday_stats
    }


def get_daily_writing_stats(db: Session, user_id: int, days: int = 7) -> List[dict]:
    """Get daily writing statistics for the specified number of days"""
    from sqlalchemy import func
    from datetime import datetime, timedelta
    
    start_date = datetime.utcnow() - timedelta(days=days)
    
    query = db.query(
        func.date(Note.created_at).label('date'),
        func.count(Note.id).label('note_count'),
        func.sum(func.length(Note.content)).label('total_chars'),
        func.avg(func.length(Note.content)).label('avg_chars')
    ).filter(
        Note.user_id == user_id,
        Note.created_at >= start_date
    ).group_by(
        func.date(Note.created_at)
    ).order_by(func.date(Note.created_at)).all()
    
    return [
        {
            "date": row.date.isoformat() if row.date else None,
            "notes_created": row.note_count,
            "total_characters": row.total_chars or 0,
            "avg_characters": round(row.avg_chars, 1) if row.avg_chars else 0
        }
        for row in query
    ]


# ============== Share CRUD Operations ==============

def generate_share_token() -> str:
    """Generate a short share token (8 characters)"""
    import secrets
    import string
    # 使用 URL-safe 字符，8位长度，包含大小写字母和数字
    alphabet = string.ascii_letters + string.digits
    return ''.join(secrets.choice(alphabet) for _ in range(8))


def create_share(
    db: Session, 
    note_id: int, 
    user_id: int, 
    permission: str = "public", 
    password: str = None,
    expires_days: int = None
) -> Share:
    """Create a new share for a note"""
    # Generate unique token
    while True:
        share_token = generate_share_token()
        existing = db.query(Share).filter(Share.share_token == share_token).first()
        if not existing:
            break
    
    # Hash password if provided
    password_hash = None
    if password:
        import hashlib
        password_hash = hashlib.sha256(password.encode()).hexdigest()
    
    # Calculate expiration
    expires_at = None
    if expires_days:
        expires_at = datetime.utcnow() + timedelta(days=expires_days)
    
    db_share = Share(
        share_token=share_token,
        note_id=note_id,
        user_id=user_id,
        permission=permission,
        password_hash=password_hash,
        expires_at=expires_at
    )
    db.add(db_share)
    db.commit()
    db.refresh(db_share)
    return db_share


def get_share_by_token(db: Session, share_token: str) -> Optional[Share]:
    """Get share by token"""
    return db.query(Share).filter(Share.share_token == share_token).first()


def get_share_by_token_with_note(db: Session, share_token: str) -> Optional[Share]:
    """Get share by token with note loaded"""
    share = db.query(Share).filter(Share.share_token == share_token).first()
    return share


def get_shares_by_note(db: Session, note_id: int, user_id: int = None) -> List[Share]:
    """Get all shares for a note, optionally filtered by user"""
    query = db.query(Share).filter(Share.note_id == note_id)
    if user_id is not None:
        query = query.filter(Share.user_id == user_id)
    return query.order_by(Share.created_at.desc()).all()


def get_all_user_shares(db: Session, user_id: int) -> List[Share]:
    """Get all shares created by a user"""
    return db.query(Share).filter(Share.user_id == user_id).order_by(Share.created_at.desc()).all()


def verify_share_password(db: Session, share_token: str, password: str) -> bool:
    """Verify share password"""
    share = get_share_by_token(db, share_token)
    if not share or not share.password_hash:
        return False
    import hashlib
    password_hash = hashlib.sha256(password.encode()).hexdigest()
    return share.password_hash == password_hash


def increment_share_access_count(db: Session, share_token: str) -> bool:
    """Increment access count for a share"""
    share = get_share_by_token(db, share_token)
    if not share:
        return False
    share.access_count += 1
    db.commit()
    return True


def update_share(
    db: Session, 
    share_token: str, 
    user_id: int, 
    **kwargs
) -> Optional[Share]:
    """Update a share (must belong to user)"""
    share = db.query(Share).filter(
        Share.share_token == share_token,
        Share.user_id == user_id
    ).first()
    
    if not share:
        return None
    
    allowed_fields = ['permission', 'is_active', 'expires_at']
    for key, value in kwargs.items():
        if key in allowed_fields:
            setattr(share, key, value)
    
    # Handle password update separately
    if 'password' in kwargs:
        password = kwargs['password']
        if password:
            import hashlib
            share.password_hash = hashlib.sha256(password.encode()).hexdigest()
        else:
            share.password_hash = None
    
    share.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(share)
    return share


def delete_share(db: Session, share_token: str, user_id: int = None) -> bool:
    """Delete a share, optionally ensuring it belongs to user"""
    query = db.query(Share).filter(Share.share_token == share_token)
    if user_id is not None:
        query = query.filter(Share.user_id == user_id)
    
    share = query.first()
    if not share:
        return False
    
    db.delete(share)
    db.commit()
    return True


def cleanup_expired_shares(db: Session) -> int:
    """Deactivate all expired shares"""
    expired = db.query(Share).filter(
        Share.expires_at < datetime.utcnow(),
        Share.is_active == True
    ).all()
    
    count = 0
    for share in expired:
        share.is_active = False
        count += 1
    
    db.commit()
    return count
