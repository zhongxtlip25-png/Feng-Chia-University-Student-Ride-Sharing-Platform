from sqlalchemy import Column, Integer, String, Boolean, DateTime
from sqlalchemy.sql import func
from .database import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    is_active = Column(Boolean, default=True) # 在電子郵件驗證前可設為 False
    is_verified_student = Column(Boolean, default=False) # 額外的人工或自動檢查
    created_at = Column(DateTime(timezone=True), server_default=func.now())
