from functools import wraps
from fastapi import HTTPException, status, Depends, Request
from typing import List, Optional, Callable, Any
from ..api.v1.routes.auth import get_current_user
from ..services.user_service import UserInDB, UserService
from ..services.role_service import PERMISSIONS
import inspect

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

def require_customs_code_access(customs_code_param: str = "customs_code"):
    """海关编码访问权限检查装饰器
    
    Args:
        customs_code_param: 海关编码参数名，默认为 'customs_code'
    """
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # 获取current_user
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
            
            # 管理员跳过海关编码检查
            if current_user.role_id == "admin":
                return await func(*args, **kwargs)
            
            # 获取海关编码参数值
            customs_code = kwargs.get(customs_code_param)
            if customs_code:
                # 检查用户是否有权限访问该海关编码
                if not user_service.check_customs_code_permission(current_user.username, customs_code):
                    raise HTTPException(
                        status_code=status.HTTP_403_FORBIDDEN,
                        detail=f"无权限访问海关编码: {customs_code}"
                    )
            
            return await func(*args, **kwargs)
        return wrapper
    return decorator

def require_data_access():
    """数据访问权限检查装饰器（自动过滤用户可访问的海关编码）"""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # 获取current_user
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
            
            # 非管理员用户需要添加海关编码过滤
            if current_user.role_id != "admin":
                allowed_customs_codes = user_service.get_user_customs_codes(current_user.username)
                if allowed_customs_codes:  # 如果有限制，则应用过滤
                    # 将允许的海关编码添加到kwargs中，供业务逻辑使用
                    kwargs['allowed_customs_codes'] = allowed_customs_codes
            
            return await func(*args, **kwargs)        
        return wrapper
    return decorator

def check_customs_code_access(username: str, customs_code: str) -> bool:
    """检查用户是否有权限访问特定海关编码"""
    return user_service.check_customs_code_permission(username, customs_code)

def check_permission(username: str, permission: str) -> bool:
    """检查用户是否有特定权限"""
    return user_service.check_permission(username, permission)

# 动态生成权限常量类
class PermissionsMeta(type):
    """权限类的元类，用于动态生成权限常量"""
    def __new__(cls, name, bases, attrs):
        # 从 role_service 的 PERMISSIONS 字典动态生成类属性
        for key in PERMISSIONS.keys():
            # 将权限键名转换为大写常量格式
            const_name = key.upper()
            attrs[const_name] = key
        
        # 添加获取所有权限的类方法
        attrs['get_all_permissions'] = classmethod(lambda cls: PERMISSIONS.copy())
        attrs['__doc__'] = "权限常量类，自动从 role_service.py 中的 PERMISSIONS 生成"
        
        return super().__new__(cls, name, bases, attrs)

class Permissions(metaclass=PermissionsMeta):
    """权限常量类，自动从 role_service.py 中的 PERMISSIONS 生成"""
    pass
