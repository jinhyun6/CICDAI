import asyncio
from sqlalchemy.ext.asyncio import create_async_engine
from app.core.database import Base
from app.models.user import User
from app.models.project import Project

async def create_tables():
    # 데이터베이스 URL
    DATABASE_URL = "postgresql+asyncpg://cicdai_user:cicdai_password@localhost:5432/cicdai_db"
    
    # 엔진 생성
    engine = create_async_engine(DATABASE_URL, echo=True)
    
    # 테이블 생성
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    await engine.dispose()
    print("✅ Tables created successfully!")

# 실행
asyncio.run(create_tables())
