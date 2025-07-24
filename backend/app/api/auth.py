from fastapi import APIRouter, HTTPException, Depends, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from fastapi.responses import RedirectResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.core.config import settings
from app.core.database import get_db
from app.services.user_service import UserService
from app.models.user import User
from pydantic import BaseModel, EmailStr
from passlib.context import CryptContext
import httpx
import jwt
from datetime import datetime, timedelta
from typing import Optional

router = APIRouter()

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# OAuth2 scheme
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")

# Request/Response models
class UserRegister(BaseModel):
    email: EmailStr
    password: str

class UserResponse(BaseModel):
    id: int
    email: str
    github_username: Optional[str]
    google_email: Optional[str]
    created_at: datetime

class TokenResponse(BaseModel):
    access_token: str
    token_type: str
    user: UserResponse

def create_jwt_token(user_id: int) -> str:
    """JWT 토큰 생성"""
    payload = {
        "sub": str(user_id),
        "exp": datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES),
        "iat": datetime.utcnow()
    }
    return jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.ALGORITHM)

async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db)
) -> User:
    """현재 로그인한 사용자 가져오기"""
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        user_id = int(payload.get("sub"))
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except (jwt.JWTError, ValueError):
        raise HTTPException(status_code=401, detail="Invalid token")
    
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    return user

@router.post("/register", response_model=TokenResponse)
async def register(
    user_data: UserRegister,
    db: AsyncSession = Depends(get_db)
):
    """회원가입"""
    # 이메일 중복 확인
    result = await db.execute(select(User).where(User.email == user_data.email))
    if result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    # 비밀번호 해시
    hashed_password = pwd_context.hash(user_data.password)
    
    # 사용자 생성
    new_user = User(
        email=user_data.email,
        hashed_password=hashed_password
    )
    
    db.add(new_user)
    await db.commit()
    await db.refresh(new_user)
    
    # JWT 토큰 생성
    access_token = create_jwt_token(new_user.id)
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": UserResponse(
            id=new_user.id,
            email=new_user.email,
            github_username=new_user.github_username,
            google_email=new_user.google_email,
            created_at=new_user.created_at
        )
    }

@router.post("/login", response_model=TokenResponse)
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: AsyncSession = Depends(get_db)
):
    """로그인"""
    # 사용자 찾기 (username 필드에 email 사용)
    result = await db.execute(select(User).where(User.email == form_data.username))
    user = result.scalar_one_or_none()
    
    if not user or not pwd_context.verify(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # JWT 토큰 생성
    access_token = create_jwt_token(user.id)
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": UserResponse(
            id=user.id,
            email=user.email,
            github_username=user.github_username,
            google_email=user.google_email,
            created_at=user.created_at
        )
    }

@router.get("/me", response_model=UserResponse)
async def get_me(current_user: User = Depends(get_current_user)):
    """현재 사용자 정보"""
    return UserResponse(
        id=current_user.id,
        email=current_user.email,
        github_username=current_user.github_username,
        google_email=current_user.google_email,
        created_at=current_user.created_at
    )

# GitHub OAuth
@router.get("/github/login")
async def github_login(
    token: Optional[str] = None,
    db: AsyncSession = Depends(get_db)
):
    """GitHub OAuth 로그인 시작"""
    # 토큰으로 사용자 확인
    if not token:
        raise HTTPException(status_code=401, detail="Authentication required")
    
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        user_id = int(payload.get("sub"))
    except:
        raise HTTPException(status_code=401, detail="Invalid token")
    
    # GitHub OAuth 설정 확인
    if not settings.GITHUB_CLIENT_ID or not settings.GITHUB_CLIENT_SECRET:
        print("GitHub OAuth not configured")
        frontend_url = f"http://localhost:5173/dashboard?error=github_oauth_not_configured"
        return RedirectResponse(url=frontend_url)
    
    github_oauth_url = (
        f"https://github.com/login/oauth/authorize"
        f"?client_id={settings.GITHUB_CLIENT_ID}"
        f"&redirect_uri={settings.GITHUB_REDIRECT_URI}"
        f"&scope=repo,workflow"
        f"&state={user_id}"  # 사용자 ID를 state에 포함
        f"&prompt=consent"  # 강제로 권한 재확인
    )
    return RedirectResponse(url=github_oauth_url)

@router.get("/github/callback")
async def github_callback(
    code: str, 
    state: Optional[str] = None,
    db: AsyncSession = Depends(get_db)
):
    """GitHub OAuth 콜백 처리"""
    # state에서 사용자 ID 추출
    if not state:
        # 프론트엔드로 에러와 함께 리다이렉트
        frontend_url = f"http://localhost:5173/dashboard?error=invalid_state"
        return RedirectResponse(url=frontend_url)
    # Access token 요청
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "https://github.com/login/oauth/access_token",
            json={
                "client_id": settings.GITHUB_CLIENT_ID,
                "client_secret": settings.GITHUB_CLIENT_SECRET,
                "code": code,
            },
            headers={"Accept": "application/json"}
        )
        
    if response.status_code != 200:
        # GitHub OAuth 설정이 없는 경우 등
        print(f"GitHub OAuth failed: {response.status_code}, {response.text}")
        frontend_url = f"http://localhost:5173/dashboard?error=github_auth_failed"
        return RedirectResponse(url=frontend_url)
    
    token_data = response.json()
    access_token = token_data.get("access_token")
    
    # GitHub 사용자 정보 가져오기
    async with httpx.AsyncClient() as client:
        user_response = await client.get(
            "https://api.github.com/user",
            headers={
                "Authorization": f"token {access_token}",
                "Accept": "application/json"
            }
        )
    
    if user_response.status_code != 200:
        raise HTTPException(status_code=400, detail="사용자 정보 가져오기 실패")
    
    user_data = user_response.json()
    
    try:
        user_id = int(state)
    except:
        raise HTTPException(status_code=400, detail="Invalid user state")
    
    # 사용자 업데이트
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # GitHub 정보 업데이트
    user_service = UserService(db)
    user.github_username = user_data.get("login")
    user.github_access_token = user_service.encrypt_token(access_token)
    user.github_connected_at = datetime.utcnow()
    
    await db.commit()
    await db.refresh(user)
    
    # 프론트엔드로 리다이렉트
    frontend_url = f"http://localhost:5173/dashboard?from=github&code=success&github_username={user.github_username}"
    return RedirectResponse(url=frontend_url)

# Google Cloud OAuth
@router.get("/google/login")
async def google_login(
    token: Optional[str] = None,
    db: AsyncSession = Depends(get_db)
):
    """Google Cloud OAuth 로그인 시작"""
    # 토큰으로 사용자 확인
    if not token:
        raise HTTPException(status_code=401, detail="Authentication required")
    
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        user_id = int(payload.get("sub"))
    except:
        raise HTTPException(status_code=401, detail="Invalid token")
    
    # Google OAuth 설정 확인
    if not settings.GOOGLE_CLIENT_ID or not settings.GOOGLE_CLIENT_SECRET:
        print("Google OAuth not configured")
        frontend_url = f"http://localhost:5173/dashboard?error=google_oauth_not_configured"
        return RedirectResponse(url=frontend_url)
    
    google_oauth_url = (
        f"https://accounts.google.com/o/oauth2/v2/auth"
        f"?client_id={settings.GOOGLE_CLIENT_ID}"
        f"&redirect_uri={settings.GOOGLE_REDIRECT_URI}"
        f"&response_type=code"
        f"&scope=https://www.googleapis.com/auth/cloud-platform "
        f"https://www.googleapis.com/auth/userinfo.email "
        f"https://www.googleapis.com/auth/userinfo.profile"
        f"&access_type=offline"
        f"&prompt=consent"
        f"&state={user_id}"  # 사용자 ID를 state에 포함
    )
    return RedirectResponse(url=google_oauth_url)

@router.get("/google/callback")
async def google_callback(
    code: str, 
    state: Optional[str] = None,
    db: AsyncSession = Depends(get_db)
):
    """Google OAuth 콜백 처리"""
    # state에서 사용자 ID 추출
    if not state:
        raise HTTPException(status_code=400, detail="Invalid state")
    # Access token 요청
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "https://oauth2.googleapis.com/token",
            data={
                "client_id": settings.GOOGLE_CLIENT_ID,
                "client_secret": settings.GOOGLE_CLIENT_SECRET,
                "code": code,
                "redirect_uri": settings.GOOGLE_REDIRECT_URI,
                "grant_type": "authorization_code",
            }
        )
        
    if response.status_code != 200:
        raise HTTPException(status_code=400, detail="Google 인증 실패")
    
    token_data = response.json()
    access_token = token_data.get("access_token")
    refresh_token = token_data.get("refresh_token")
    
    # Google 사용자 정보 가져오기
    async with httpx.AsyncClient() as client:
        user_response = await client.get(
            "https://www.googleapis.com/oauth2/v2/userinfo",
            headers={
                "Authorization": f"Bearer {access_token}",
                "Accept": "application/json"
            }
        )
    
    if user_response.status_code != 200:
        raise HTTPException(status_code=400, detail="사용자 정보 가져오기 실패")
    
    user_data = user_response.json()
    google_email = user_data.get("email")
    
    try:
        user_id = int(state)
    except:
        raise HTTPException(status_code=400, detail="Invalid user state")
    
    # 사용자 업데이트
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Google 정보 업데이트
    user_service = UserService(db)
    user = await user_service.update_google_connection(
        user_id=user.id,
        google_email=google_email,
        access_token=access_token,
        refresh_token=refresh_token
    )
    
    # 프론트엔드로 리다이렉트
    frontend_url = f"http://localhost:5173/dashboard?from=google&code=success&google_email={google_email}"
    return RedirectResponse(url=frontend_url)

@router.get("/status")
async def auth_status():
    """현재 인증 상태 확인"""
    # TODO: JWT 토큰 검증 후 사용자의 연결 상태 반환
    return {
        "github_connected": False,
        "google_connected": False
    }