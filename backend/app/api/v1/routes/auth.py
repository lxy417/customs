from fastapi import APIRouter, Depends, HTTPException, status
from jose import jwt
from jose.exceptions import JWTError
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from datetime import timedelta
from typing import Optional, Dict, Any
from ....services.user_service import UserService, Token, TokenData, UserInDB
from ....config.settings import settings

router = APIRouter()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")
user_service = UserService()

@router.post("/login", response_model=Token, tags=["认证管理"])
def login(form_data: OAuth2PasswordRequestForm = Depends()):
    """用户登录，获取访问令牌"""
    user = user_service.authenticate_user(form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户名或密码不正确",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = user_service.create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}

async def get_current_user(token: str = Depends(oauth2_scheme)) -> UserInDB:
    """获取当前登录用户"""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="无法验证凭据",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
        token_data = TokenData(username=username)
    except JWTError:
        raise credentials_exception
    user = user_service.get_user_by_username(username=token_data.username)
    if user is None:
        raise credentials_exception
    return user

@router.get("/me", response_model=Dict[str, Any], tags=["认证管理"])
def read_users_me(current_user: UserInDB = Depends(get_current_user)):
    """获取当前用户信息"""
    return {
        "username": current_user.username,
        "is_admin": current_user.is_admin,
        "allowed_customs_codes": current_user.allowed_customs_codes,
        "created_at": current_user.created_at
    }

@router.post("/logout", tags=["认证管理"])
def logout(current_user: UserInDB = Depends(get_current_user)):
    """用户登出（前端应清除本地存储的令牌）"""
    # 在无状态JWT认证中，登出主要由前端清除令牌实现
    return {"message": f"用户 {current_user.username} 已成功登出"}