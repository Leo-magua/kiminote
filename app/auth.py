"""
Authentication module for AI Notes
"""
from datetime import datetime, timedelta
from typing import Optional
from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session

from app.config import SECRET_KEY, ALGORITHM, ACCESS_TOKEN_EXPIRE_DAYS, SESSION_COOKIE_NAME
from app.database import get_db, get_user_by_username, get_user_by_id, create_session, get_session, delete_session

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Security
security = HTTPBearer(auto_error=False)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a plain password against a hashed password"""
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """Hash a password"""
    return pwd_context.hash(password)


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Create a JWT access token"""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(days=ACCESS_TOKEN_EXPIRE_DAYS)
    
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def decode_token(token: str) -> Optional[dict]:
    """Decode a JWT token"""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except JWTError:
        return None


def get_token_from_request(request: Request) -> Optional[str]:
    """Get token from cookie or Authorization header"""
    # First try to get from cookie
    token = request.cookies.get(SESSION_COOKIE_NAME)
    if token:
        return token
    
    # Then try Authorization header
    auth_header = request.headers.get("Authorization")
    if auth_header and auth_header.startswith("Bearer "):
        return auth_header[7:]
    
    return None


async def get_current_user(
    request: Request,
    db: Session = Depends(get_db),
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)
) -> dict:
    """
    Get current user from token (cookie or Authorization header)
    Returns user dict with id, username, email
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Not authenticated",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    # Get token from request
    token = get_token_from_request(request)
    if not token and credentials:
        token = credentials.credentials
    
    if not token:
        raise credentials_exception
    
    # Decode token
    payload = decode_token(token)
    if payload is None:
        raise credentials_exception
    
    user_id = payload.get("sub")
    session_id = payload.get("session_id")
    
    if user_id is None:
        raise credentials_exception
    
    # Check if session is valid in database
    if session_id:
        db_session = get_session(db, session_id)
        if not db_session or not db_session.is_valid:
            raise credentials_exception
        # Update last activity
        db_session.last_activity = datetime.utcnow()
        db.commit()
    
    # Get user from database
    user = get_user_by_id(db, int(user_id))
    if user is None:
        raise credentials_exception
    
    return {
        "id": user.id,
        "username": user.username,
        "email": user.email,
        "is_active": user.is_active
    }


async def get_current_user_optional(
    request: Request,
    db: Session = Depends(get_db)
) -> Optional[dict]:
    """Get current user if authenticated, otherwise return None"""
    try:
        return await get_current_user(request, db)
    except HTTPException:
        return None


def authenticate_user(db: Session, username: str, password: str) -> Optional[dict]:
    """Authenticate a user with username and password"""
    user = get_user_by_username(db, username)
    if not user:
        return None
    if not verify_password(password, user.hashed_password):
        return None
    if not user.is_active:
        return None
    return {
        "id": user.id,
        "username": user.username,
        "email": user.email,
        "is_active": user.is_active
    }


def create_user_session(db: Session, user_id: int, ip_address: str = None, user_agent: str = None) -> str:
    """Create a new session for a user and return the token"""
    # Create session in database
    session_id = create_session(db, user_id=user_id, ip_address=ip_address, user_agent=user_agent)
    
    # Create JWT token
    access_token = create_access_token(
        data={"sub": str(user_id), "session_id": session_id}
    )
    
    return access_token


def invalidate_session(db: Session, token: str) -> bool:
    """Invalidate a session"""
    payload = decode_token(token)
    if payload:
        session_id = payload.get("session_id")
        if session_id:
            return delete_session(db, session_id)
    return False
