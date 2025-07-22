from fastapi import APIRouter, Depends, HTTPException, status
from typing import List, Dict, Any, Optional
from app.services.user_service import UserService, UserCreate, UserUpdate
from app.api.v1.routes.auth import get_current_user
from app.services.user_service import UserInDB
from app.utils.permissions import require_admin, require_permissions
import logging

logger = logging.getLogger(__name__)
router = APIRouter()
user_service = UserService()

@router.post("/", response_model=Dict[str, Any], tags=["用户管理"])
def create_user(
    user_create: UserCreate,
    current_user: UserInDB = Depends(get_current_user)
):
    """创建新用户（仅管理员）"""
    if current_user.role_id != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="没有权限创建用户，需要管理员权限"
        )
    try:
        user = user_service.create_user(user_create)
        return {
            "username": user.username,
            "role_id": user.role_id,
            "allowed_customs_codes": user.allowed_customs_codes,
            "additional_permissions": user.additional_permissions,
            "group_ids": user.group_ids,
            "created_at": user.created_at
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.put("/{username}", response_model=Dict[str, Any], tags=["用户管理"])
def update_user(
    username: str,
    user_update: UserUpdate,
    current_user: UserInDB = Depends(get_current_user)
):
    """更新用户信息（仅管理员或自己）"""
    if current_user.role_id != "admin" and current_user.username != username:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="没有权限更新此用户"
        )
    
    # 防止非管理员修改角色和权限
    if current_user.role_id != "admin":
        if user_update.role_id is not None:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="没有权限修改用户角色"
            )
        if user_update.additional_permissions is not None:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="没有权限修改用户权限"
            )
        if user_update.group_ids is not None:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="没有权限修改用户组"
            )
    
    try:
        user = user_service.update_user(username, user_update)
        if not user:
            raise HTTPException(status_code=404, detail=f"用户 '{username}' 不存在")
        return {
            "username": user.username,
            "role_id": user.role_id,
            "allowed_customs_codes": user.allowed_customs_codes,
            "additional_permissions": user.additional_permissions,
            "group_ids": user.group_ids,
            "updated_at": user.updated_at
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.delete("/{username}", response_model=Dict[str, str], tags=["用户管理"])
def delete_user(
    username: str,
    current_user: UserInDB = Depends(get_current_user)
):
    """删除用户（仅管理员）"""
    if current_user.role_id != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="没有权限删除用户，需要管理员权限"
        )
    if username == current_user.username:
        raise HTTPException(
            status_code=400, detail="不能删除当前登录的用户"
        )
    success = user_service.delete_user(username)
    if not success:
        raise HTTPException(status_code=404, detail=f"用户 '{username}' 不存在或无法删除")
    return {"message": f"用户 '{username}' 删除成功"}

@router.get("/", response_model=List[Dict[str, Any]], tags=["用户管理"])
def list_users(current_user: UserInDB = Depends(get_current_user)):
    """列出所有用户（仅管理员）"""
    if current_user.role_id != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="没有权限查看用户列表，需要管理员权限"
        )
    return user_service.list_users()

@router.get("/{username}", response_model=Dict[str, Any], tags=["用户管理"])
def get_user(
    username: str,
    current_user: UserInDB = Depends(get_current_user)
):
    """获取用户详情（仅管理员或自己）"""
    if current_user.role_id != "admin" and current_user.username != username:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="没有权限查看此用户信息"
        )
    user = user_service.get_user_by_username(username)
    if not user:
        raise HTTPException(status_code=404, detail=f"用户 '{username}'不存在")
    return {
        "username": user.username,
        "role_id": user.role_id,
        "allowed_customs_codes": user.allowed_customs_codes,
        "additional_permissions": user.additional_permissions,
        "group_ids": user.group_ids,
        "created_at": user.created_at,
        "updated_at": user.updated_at
    }