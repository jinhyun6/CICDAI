from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.user import User
from datetime import datetime
from typing import Optional
import json
from cryptography.fernet import Fernet
from app.core.config import settings
import httpx

class UserService:
    def __init__(self, db: AsyncSession):
        self.db = db
        # 암호화 키 (실제로는 환경변수에서 가져와야 함)
        self.cipher = Fernet(settings.ENCRYPTION_KEY.encode()) if settings.ENCRYPTION_KEY else None
    
    def encrypt_token(self, token: str) -> str:
        """토큰 암호화"""
        if self.cipher:
            return self.cipher.encrypt(token.encode()).decode()
        return token  # 암호화 키가 없으면 그대로 저장 (개발용)
    
    def decrypt_token(self, encrypted_token: str) -> str:
        """토큰 복호화"""
        if self.cipher and encrypted_token:
            return self.cipher.decrypt(encrypted_token.encode()).decode()
        return encrypted_token
    
    async def get_or_create_user_by_github(
        self, 
        github_username: str, 
        github_email: str,
        access_token: str
    ) -> User:
        """GitHub 사용자 조회 또는 생성"""
        # 기존 사용자 조회
        result = await self.db.execute(
            select(User).where(User.github_username == github_username)
        )
        user = result.scalar_one_or_none()
        
        if user:
            # 기존 사용자 - 토큰 업데이트
            user.github_access_token = self.encrypt_token(access_token)
            user.github_connected_at = datetime.utcnow()
            if github_email and not user.email:
                user.email = github_email
        else:
            # 새 사용자 생성
            user = User(
                email=github_email or f"{github_username}@github.local",
                github_username=github_username,
                github_access_token=self.encrypt_token(access_token),
                github_connected_at=datetime.utcnow()
            )
            self.db.add(user)
        
        await self.db.commit()
        await self.db.refresh(user)
        return user
    
    async def update_google_connection(
        self,
        user_id: int,
        google_email: str,
        access_token: str,
        refresh_token: str
    ) -> User:
        """Google 연결 정보 업데이트"""
        result = await self.db.execute(
            select(User).where(User.id == user_id)
        )
        user = result.scalar_one_or_none()
        
        if not user:
            raise ValueError("User not found")
        
        user.google_email = google_email
        user.google_access_token = self.encrypt_token(access_token)
        user.google_refresh_token = self.encrypt_token(refresh_token)
        user.google_connected_at = datetime.utcnow()
        
        await self.db.commit()
        await self.db.refresh(user)
        return user
    
    async def get_user_by_email(self, email: str) -> Optional[User]:
        """이메일로 사용자 조회"""
        result = await self.db.execute(
            select(User).where(User.email == email)
        )
        return result.scalar_one_or_none()
    
    async def get_user_tokens(self, user_id: int) -> dict:
        """사용자의 복호화된 토큰 반환"""
        result = await self.db.execute(
            select(User).where(User.id == user_id)
        )
        user = result.scalar_one_or_none()
        
        if not user:
            return {}
        
        return {
            "github_token": self.decrypt_token(user.github_access_token) if user.github_access_token else None,
            "google_token": self.decrypt_token(user.google_access_token) if user.google_access_token else None,
            "google_refresh_token": self.decrypt_token(user.google_refresh_token) if user.google_refresh_token else None
        }
    
    async def refresh_google_token(self, user_id: int) -> Optional[str]:
        """Google 액세스 토큰 갱신"""
        result = await self.db.execute(
            select(User).where(User.id == user_id)
        )
        user = result.scalar_one_or_none()
        
        if not user or not user.google_refresh_token:
            return None
        
        refresh_token = self.decrypt_token(user.google_refresh_token)
        
        try:
            # Google OAuth2 토큰 갱신 요청
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    "https://oauth2.googleapis.com/token",
                    data={
                        "client_id": settings.GOOGLE_CLIENT_ID,
                        "client_secret": settings.GOOGLE_CLIENT_SECRET,
                        "refresh_token": refresh_token,
                        "grant_type": "refresh_token"
                    }
                )
            
            if response.status_code == 200:
                token_data = response.json()
                new_access_token = token_data.get("access_token")
                
                # 새 액세스 토큰 저장
                user.google_access_token = self.encrypt_token(new_access_token)
                await self.db.commit()
                
                return new_access_token
            else:
                print(f"Failed to refresh Google token: {response.status_code} - {response.text}")
                return None
                
        except Exception as e:
            print(f"Error refreshing Google token: {e}")
            return None