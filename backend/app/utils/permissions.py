from functools import wraps
from fastapi import HTTPException, status, Depends
from typing import List
from ..api.v1.routes.auth import get_current_user
from ..services.user_service import UserInDB, UserService

user_service = UserService()

def require_permissions(required_permissions: List[str]):
    """权限检查装饰器"""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # 从kwargs中获取current_user
            current_user = None
            for key, value in kwargs.items():
                if isinstance(value, UserInDB):
                    current_user = value
                    break
            
            if not current_user:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="未找到用户信息"
                )
            
            # 检查用户权限（角色权限 + 额外权限）
            user_permissions = user_service.get_user_permissions(current_user.username)
            
            for permission in required_permissions:
                if permission not in user_permissions:
                    raise HTTPException(
                        status_code=status.HTTP_403_FORBIDDEN,
                        detail=f"缺少必要权限: {permission}"
                    )
            
            return await func(*args, **kwargs)
        return wrapper
    return decorator

def require_admin():
    """管理员权限检查装饰器"""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # 从kwargs中获取current_user
            current_user = None
            for key, value in kwargs.items():
                if isinstance(value, UserInDB):
                    current_user = value
                    break
            
            if not current_user:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="未找到用户信息"
                )
            
            if current_user.role_id != "admin":
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="需要管理员权限"
                )
            
            return await func(*args, **kwargs)
        return wrapper
    return decorator

def check_customs_code_access(username: str, customs_code: str) -> bool:
    """检查用户是否有权限访问特定海关编码"""
    return user_service.check_customs_code_permission(username, customs_code)

def check_permission(username: str, permission: str) -> bool:
    """检查用户是否有特定权限"""
    return user_service.check_permission(username, permission)