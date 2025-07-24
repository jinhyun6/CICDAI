from sqlalchemy import Column, Integer, String, DateTime, Boolean, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base

class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=True)  # OAuth 사용자는 비밀번호 없음
    
    # GitHub 정보
    github_username = Column(String, index=True)  # unique 제거 - 한 GitHub 계정이 여러 사용자에 연결될 수 있음
    github_access_token = Column(Text)  # 암호화해서 저장
    github_connected_at = Column(DateTime(timezone=True))
    
    # Google Cloud 정보
    google_email = Column(String)
    google_access_token = Column(Text)  # 암호화해서 저장
    google_refresh_token = Column(Text)  # 암호화해서 저장
    google_connected_at = Column(DateTime(timezone=True))
    
    # 기본 정보
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    projects = relationship("Project", back_populates="user")