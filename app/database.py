from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.orm import declarative_base

SQLALCHEMY_DATABASE_URL = "sqlite:///./ride_sharing.db"
# 若使用 PostgreSQL，URL 將為：
# SQLALCHEMY_DATABASE_URL = "postgresql://user:password@postgresserver/db"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False} # check_same_thread 僅在 SQLite 中需要
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

# 取得資料庫工作階段的依賴項
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
