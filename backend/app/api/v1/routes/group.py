from fastapi import APIRouter, Depends, HTTPException, status
from typing import List, Dict, Any
from app.services.group_service import GroupService, GroupCreate, GroupUpdate
from app.api.v1.routes.auth import get_current_user
from app.services.user_service import UserInDB, UserService
import logging

logger = logging.getLogger(__name__)
router = APIRouter()
group_service = GroupService()
user_service = UserService()

@router.post("/", response_model=Dict[str, Any], tags=["用户组管理"])
def create_group(
    group_create: GroupCreate,
    current_user: UserInDB = Depends(get_current_user)
):
    """创建用户组（仅管理员）"""
    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="无权限执行此操作")
    try:
        return group_service.create_group(group_create)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"创建用户组失败: {str(e)}")
        raise HTTPException(status_code=500, detail="创建用户组失败")

@router.put("/{group_id}", response_model=Dict[str, Any], tags=["用户组管理"])
def update_group(
    group_id: str,
    group_update: GroupUpdate,
    current_user: UserInDB = Depends(get_current_user)
):
    """更新用户组信息（仅管理员）"""
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="没有权限更新用户组，需要管理员权限"
        )
    
    try:
        group = group_service.update_group(group_id, group_update)
        if not group:
            raise HTTPException(status_code=404, detail=f"用户组 '{group_id}' 不存在")
        
        return {
            "message": "用户组更新成功",
            "group": group
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"更新用户组失败: {e}")
        raise HTTPException(status_code=500, detail="更新用户组失败")

@router.delete("/{group_id}", response_model=Dict[str, Any], tags=["用户组管理"])
def delete_group(
    group_id: str,
    current_user: UserInDB = Depends(get_current_user)
):
    """删除用户组（仅管理员）"""
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="没有权限删除用户组，需要管理员权限"
        )
    
    try:
        success = group_service.delete_group(group_id)
        if not success:
            raise HTTPException(status_code=404, detail=f"用户组 '{group_id}' 不存在")
        
        return {"message": "用户组删除成功"}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"删除用户组失败: {e}")
        raise HTTPException(status_code=500, detail="删除用户组失败")

@router.get("/", response_model=List[Dict[str, Any]], tags=["用户组管理"])
def list_groups(current_user: UserInDB = Depends(get_current_user)):
    """列出所有用户组（仅管理员）"""
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="没有权限查看用户组列表，需要管理员权限"
        )
    return group_service.list_groups()

@router.get("/{group_id}", response_model=Dict[str, Any], tags=["用户组管理"])
def get_group(
    group_id: str,
    current_user: UserInDB = Depends(get_current_user)
):
    """获取用户组详情（仅管理员）"""
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="没有权限查看用户组信息"
        )
    
    group = group_service.get_group_by_id(group_id)
    if not group:
        raise HTTPException(status_code=404, detail=f"用户组 '{group_id}' 不存在")
    
    # 获取用户组中的用户列表
    users_in_group = user_service.get_users_by_group(group_id)
    
    group_dict = group.dict()
    group_dict["users"] = users_in_group
    
    return group_dict

# 移除获取可用权限的端点，因为用户组不再管理功能权限

@router.post("/{group_id}/users/{username}", response_model=Dict[str, Any], tags=["用户组管理"])
def add_user_to_group(
    group_id: str,
    username: str,
    current_user: UserInDB = Depends(get_current_user)
):
    """将用户添加到用户组（仅管理员）"""
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="没有权限管理用户组成员"
        )
    
    # 检查用户组是否存在
    group = group_service.get_group_by_id(group_id)
    if not group:
        raise HTTPException(status_code=404, detail=f"用户组 '{group_id}' 不存在")
    
    # 检查用户是否存在
    user = user_service.get_user_by_username(username)
    if not user:
        raise HTTPException(status_code=404, detail=f"用户 '{username}' 不存在")
    
    # 检查用户是否已在用户组中
    if group_id in user.group_ids:
        raise HTTPException(status_code=400, detail=f"用户 '{username}' 已在用户组中")
    
    # 添加用户到用户组
    new_group_ids = user.group_ids + [group_id]
    from app.services.user_service import UserUpdate
    user_update = UserUpdate(group_ids=new_group_ids)
    updated_user = user_service.update_user(username, user_update)
    
    return {
        "message": f"用户 '{username}' 已添加到用户组 '{group.name}'",
        "user": {
            "username": updated_user.username,
            "group_ids": updated_user.group_ids
        }
    }

@router.delete("/{group_id}/users/{username}", response_model=Dict[str, Any], tags=["用户组管理"])
def remove_user_from_group(
    group_id: str,
    username: str,
    current_user: UserInDB = Depends(get_current_user)
):
    """从用户组中移除用户（仅管理员）"""
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="没有权限管理用户组成员"
        )
    
    # 检查用户是否存在
    user = user_service.get_user_by_username(username)
    if not user:
        raise HTTPException(status_code=404, detail=f"用户 '{username}' 不存在")
    
    # 检查用户是否在用户组中
    if group_id not in user.group_ids:
        raise HTTPException(status_code=400, detail=f"用户 '{username}' 不在此用户组中")
    
    # 从用户组中移除用户
    new_group_ids = [gid for gid in user.group_ids if gid != group_id]
    from app.services.user_service import UserUpdate
    user_update = UserUpdate(group_ids=new_group_ids)
    updated_user = user_service.update_user(username, user_update)
    
    return {
        "message": f"用户 '{username}' 已从用户组中移除",
        "user": {
            "username": updated_user.username,
            "group_ids": updated_user.group_ids
        }
    }