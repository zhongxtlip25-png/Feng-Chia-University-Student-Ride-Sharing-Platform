from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from datetime import timedelta

from .. import models, schemas, security, database
from ..dependencies import get_db, get_current_active_user

router = APIRouter(
    prefix="/auth",
    tags=["身分驗證 (Authentication)"]
)

def validate_fcu_email(email: str) -> bool:
    """
    驗證是否為逢甲大學的信箱網域
    學生網域: @o365.fcu.edu.tw 或 @fcu.edu.tw
    """
    allowed_domains = ["@o365.fcu.edu.tw", "@fcu.edu.tw"]
    return any(email.lower().endswith(domain) for domain in allowed_domains)

@router.post("/register", response_model=schemas.UserResponse, status_code=status.HTTP_201_CREATED, summary="學生帳號註冊")
def register(user: schemas.UserCreate, db: Session = Depends(get_db)):
    # 1. 驗證是否為逢甲大學信箱，確保平台使用者真實性
    if not validate_fcu_email(user.email):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="註冊失敗：必須使用逢甲大學學生信箱 (@o365.fcu.edu.tw 或 @fcu.edu.tw) 進行註冊，以確保使用者身分之真實性。"
        )
    
    # 2. 檢查信箱是否已被註冊
    db_user = db.query(models.User).filter(models.User.email == user.email).first()
    if db_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="註冊失敗：此電子郵件已被註冊。"
        )
    
    # 3. 建立新使用者，密碼進行雜湊加密
    hashed_password = security.get_password_hash(user.password)
    new_user = models.User(
        email=user.email,
        hashed_password=hashed_password,
        is_active=True,             # 預設啟用，若有串接驗證信可改為 False
        is_verified_student=True    # 通過信箱網域檢查，標記為已驗證學生
    )
    
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user

@router.post("/login", response_model=schemas.Token, summary="學生帳號登入（獲取 JWT Token）")
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    # 1. 查詢使用者
    user = db.query(models.User).filter(models.User.email == form_data.username).first()
    if not user or not security.verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="登入失敗：帳號或密碼錯誤。",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # 2. 檢查帳號是否啟用
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="登入失敗：此帳號尚未啟用或已被停用。"
        )
        
    # 3. 產生 JWT Token
    access_token_expires = timedelta(minutes=security.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = security.create_access_token(
        data={"sub": user.email}, expires_delta=access_token_expires
    )
    
    return {"access_token": access_token, "token_type": "bearer"}

@router.get("/me", response_model=schemas.UserResponse, summary="取得當前登入使用者資訊")
def get_me(current_user: models.User = Depends(get_current_active_user)):
    return current_user
