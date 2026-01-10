# =============================================================================
# Auth Service - Main Application
# =============================================================================
# FastAPI application for authentication and user management
# =============================================================================

from contextlib import asynccontextmanager
from datetime import datetime, timedelta
from typing import Optional

from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jose import JWTError, jwt
from passlib.context import CryptContext
from pydantic import BaseModel, EmailStr
import structlog

import sys
sys.path.insert(0, "/app")

from shared.config.settings import settings
from shared.db.repository import get_session, UserRepository, init_db
from shared.db.models import User

logger = structlog.get_logger(__name__)

# =============================================================================
# Security Configuration
# =============================================================================

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash."""
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """Hash a password."""
    return pwd_context.hash(password)


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Create a JWT access token."""
    to_encode = data.copy()
    expire = datetime.utcnow() + (
        expires_delta or timedelta(minutes=settings.auth.access_token_expire_minutes)
    )
    to_encode.update({"exp": expire})
    return jwt.encode(
        to_encode,
        settings.auth.jwt_secret,
        algorithm=settings.auth.jwt_algorithm
    )


def create_refresh_token(data: dict) -> str:
    """Create a JWT refresh token."""
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(days=settings.auth.refresh_token_expire_days)
    to_encode.update({"exp": expire, "type": "refresh"})
    return jwt.encode(
        to_encode,
        settings.auth.jwt_secret,
        algorithm=settings.auth.jwt_algorithm
    )


# =============================================================================
# Pydantic Models
# =============================================================================

class UserCreate(BaseModel):
    """User registration request."""
    email: EmailStr
    password: str
    full_name: Optional[str] = None


class UserResponse(BaseModel):
    """User response model."""
    id: str
    email: str
    full_name: Optional[str]
    is_active: bool
    created_at: datetime
    
    class Config:
        from_attributes = True


class Token(BaseModel):
    """Token response model."""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class TokenData(BaseModel):
    """Token payload data."""
    email: Optional[str] = None


class RefreshTokenRequest(BaseModel):
    """Refresh token request."""
    refresh_token: str


class PasswordChangeRequest(BaseModel):
    """Password change request."""
    current_password: str
    new_password: str


# =============================================================================
# Application Lifecycle
# =============================================================================

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    logger.info("Starting Auth Service")
    await init_db()
    yield
    logger.info("Shutting down Auth Service")


# =============================================================================
# FastAPI Application
# =============================================================================

app = FastAPI(
    title="Investment Agent System - Auth Service",
    description="Authentication and user management service",
    version="1.0.0",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# =============================================================================
# Dependencies
# =============================================================================

async def get_current_user(token: str = Depends(oauth2_scheme)) -> User:
    """Get the current authenticated user from JWT token."""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        payload = jwt.decode(
            token,
            settings.auth.jwt_secret,
            algorithms=[settings.auth.jwt_algorithm]
        )
        email: str = payload.get("sub")
        if email is None:
            raise credentials_exception
        token_data = TokenData(email=email)
    except JWTError:
        raise credentials_exception
    
    async with get_session() as session:
        user_repo = UserRepository(session)
        user = await user_repo.get_by_email(token_data.email)
        
        if user is None:
            raise credentials_exception
        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Inactive user"
            )
        
        return user


async def get_current_active_superuser(
    current_user: User = Depends(get_current_user)
) -> User:
    """Get current user if they are a superuser."""
    if not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    return current_user


# =============================================================================
# Routes
# =============================================================================

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "service": "auth-service"}


@app.post("/register", response_model=UserResponse)
async def register(user_data: UserCreate):
    """Register a new user."""
    async with get_session() as session:
        user_repo = UserRepository(session)
        
        # Check if user already exists
        existing_user = await user_repo.get_by_email(user_data.email)
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered"
            )
        
        # Create new user
        user = await user_repo.create(
            email=user_data.email,
            hashed_password=get_password_hash(user_data.password),
            full_name=user_data.full_name
        )
        
        logger.info("User registered", email=user.email)
        
        return UserResponse(
            id=str(user.id),
            email=user.email,
            full_name=user.full_name,
            is_active=user.is_active,
            created_at=user.created_at
        )


@app.post("/token", response_model=Token)
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    """Login and get access token."""
    async with get_session() as session:
        user_repo = UserRepository(session)
        user = await user_repo.get_by_email(form_data.username)
        
        if not user or not verify_password(form_data.password, user.hashed_password):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect email or password",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Inactive user"
            )
        
        access_token = create_access_token(data={"sub": user.email})
        refresh_token = create_refresh_token(data={"sub": user.email})
        
        logger.info("User logged in", email=user.email)
        
        return Token(
            access_token=access_token,
            refresh_token=refresh_token
        )


@app.post("/refresh", response_model=Token)
async def refresh_token(request: RefreshTokenRequest):
    """Refresh access token using refresh token."""
    try:
        payload = jwt.decode(
            request.refresh_token,
            settings.auth.jwt_secret,
            algorithms=[settings.auth.jwt_algorithm]
        )
        
        if payload.get("type") != "refresh":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token type"
            )
        
        email: str = payload.get("sub")
        if email is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token"
            )
        
        # Verify user still exists and is active
        async with get_session() as session:
            user_repo = UserRepository(session)
            user = await user_repo.get_by_email(email)
            
            if not user or not user.is_active:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="User not found or inactive"
                )
        
        access_token = create_access_token(data={"sub": email})
        refresh_token = create_refresh_token(data={"sub": email})
        
        return Token(
            access_token=access_token,
            refresh_token=refresh_token
        )
        
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token"
        )


@app.get("/me", response_model=UserResponse)
async def get_current_user_info(current_user: User = Depends(get_current_user)):
    """Get current user information."""
    return UserResponse(
        id=str(current_user.id),
        email=current_user.email,
        full_name=current_user.full_name,
        is_active=current_user.is_active,
        created_at=current_user.created_at
    )


@app.put("/me", response_model=UserResponse)
async def update_current_user(
    full_name: Optional[str] = None,
    current_user: User = Depends(get_current_user)
):
    """Update current user information."""
    async with get_session() as session:
        user_repo = UserRepository(session)
        
        update_data = {}
        if full_name is not None:
            update_data["full_name"] = full_name
        
        if update_data:
            user = await user_repo.update(current_user.id, **update_data)
        else:
            user = current_user
        
        return UserResponse(
            id=str(user.id),
            email=user.email,
            full_name=user.full_name,
            is_active=user.is_active,
            created_at=user.created_at
        )


@app.post("/me/change-password")
async def change_password(
    request: PasswordChangeRequest,
    current_user: User = Depends(get_current_user)
):
    """Change current user's password."""
    if not verify_password(request.current_password, current_user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Incorrect current password"
        )
    
    async with get_session() as session:
        user_repo = UserRepository(session)
        await user_repo.update(
            current_user.id,
            hashed_password=get_password_hash(request.new_password)
        )
    
    logger.info("Password changed", email=current_user.email)
    
    return {"message": "Password changed successfully"}


# =============================================================================
# Admin Routes
# =============================================================================

@app.get("/admin/users", response_model=list[UserResponse])
async def list_users(
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(get_current_active_superuser)
):
    """List all users (admin only)."""
    async with get_session() as session:
        user_repo = UserRepository(session)
        users = await user_repo.get_all(skip=skip, limit=limit)
        
        return [
            UserResponse(
                id=str(user.id),
                email=user.email,
                full_name=user.full_name,
                is_active=user.is_active,
                created_at=user.created_at
            )
            for user in users
        ]


@app.put("/admin/users/{user_id}/activate")
async def activate_user(
    user_id: str,
    current_user: User = Depends(get_current_active_superuser)
):
    """Activate a user (admin only)."""
    from uuid import UUID
    
    async with get_session() as session:
        user_repo = UserRepository(session)
        user = await user_repo.update(UUID(user_id), is_active=True)
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        logger.info("User activated", user_id=user_id, by=current_user.email)
        
        return {"message": "User activated"}


@app.put("/admin/users/{user_id}/deactivate")
async def deactivate_user(
    user_id: str,
    current_user: User = Depends(get_current_active_superuser)
):
    """Deactivate a user (admin only)."""
    from uuid import UUID
    
    async with get_session() as session:
        user_repo = UserRepository(session)
        user = await user_repo.update(UUID(user_id), is_active=False)
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        logger.info("User deactivated", user_id=user_id, by=current_user.email)
        
        return {"message": "User deactivated"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
