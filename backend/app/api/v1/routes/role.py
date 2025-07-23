from fastapi import APIRouter, Depends, HTTPException, status
from typing import List, Dict, Any
from app.services.role_service import RoleService, RoleCreate, RoleUpdate
from app.api.v1.routes.auth import get_current_user
from app.services.user_service import UserInDB
from app.utils.permissions import require_permissions, Permissions
import logging

logger = logging.getLogger(__name__)
router = APIRouter()
role_service = RoleService()

@router.post("/", response_model=Dict[str, Any], tags=["角色管理"])
@require_permissions([Permissions.ROLE_MANAGE])
async def create_role(
    role_create: RoleCreate,
    current_user: UserInDB = Depends(get_current_user)
):
    """创建角色（需要角色管理权限）"""
    try:
        role = role_service.create_role(role_create)
        return {
            "message": "角色创建成功",
            "role": {
                "id": role.id,
                "name": role.name,
                "description": role.description,
                "permissions": role.permissions,
                "is_system": role.is_system,
                "created_at": role.created_at,
                "updated_at": role.updated_at
            }
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"创建角色失败: {str(e)}")
        raise HTTPException(status_code=500, detail="创建角色失败")

@router.put("/{role_id}", response_model=Dict[str, Any], tags=["角色管理"])
@require_permissions([Permissions.ROLE_MANAGE])
async def update_role(
    role_id: str,
    role_update: RoleUpdate,
    current_user: UserInDB = Depends(get_current_user)
):
    """更新角色（需要角色管理权限）"""
    try:
        role = role_service.update_role(role_id, role_update)
        if not role:
            raise HTTPException(status_code=404, detail="角色不存在")
        
        return {
            "message": "角色更新成功",
            "role": {
                "id": role.id,
                "name": role.name,
                "description": role.description,
                "permissions": role.permissions,
                "is_system": role.is_system,
                "created_at": role.created_at,
                "updated_at": role.updated_at
            }
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"更新角色失败: {str(e)}")
        raise HTTPException(status_code=500, detail="更新角色失败")

@router.delete("/{role_id}", response_model=Dict[str, Any], tags=["角色管理"])
@require_permissions([Permissions.ROLE_MANAGE])
async def delete_role(
    role_id: str,
    current_user: UserInDB = Depends(get_current_user)
):
    """删除角色（需要角色管理权限）"""
    try:
        success = role_service.delete_role(role_id)
        if not success:
            raise HTTPException(status_code=404, detail="角色不存在")
        
        return {"message": "角色删除成功"}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"删除角色失败: {str(e)}")
        raise HTTPException(status_code=500, detail="删除角色失败")

@router.get("/", response_model=List[Dict[str, Any]], tags=["角色管理"])
@require_permissions([Permissions.ROLE_MANAGE])
async def list_roles(current_user: UserInDB = Depends(get_current_user)):
    """列出所有角色（需要角色管理权限）"""
    try:
        roles = role_service.list_roles()
        return roles
    except Exception as e:
        logger.error(f"列出角色失败: {str(e)}")
        raise HTTPException(status_code=500, detail="获取角色列表失败")

@router.get("/{role_id}", response_model=Dict[str, Any], tags=["角色管理"])
@require_permissions([Permissions.ROLE_MANAGE])
async def get_role(
    role_id: str,
    current_user: UserInDB = Depends(get_current_user)
):
    """获取角色详情（需要角色管理权限）"""
    try:
        role = role_service.get_role_by_id(role_id)
        if not role:
            raise HTTPException(status_code=404, detail="角色不存在")
        
        return {
            "id": role.id,
            "name": role.name,
            "description": role.description,
            "permissions": role.permissions,
            "is_system": role.is_system,
            "created_at": role.created_at,
            "updated_at": role.updated_at
        }
    except Exception as e:
        logger.error(f"获取角色失败: {str(e)}")
        raise HTTPException(status_code=500, detail="获取角色失败")

@router.get("/permissions/available", response_model=Dict[str, str], tags=["角色管理"])
@require_permissions([Permissions.ROLE_MANAGE])
async def get_available_permissions(current_user: UserInDB = Depends(get_current_user)):
    """获取所有可用权限（需要角色管理权限）"""
    try:
        permissions = role_service.get_available_permissions()
        return permissions
    except Exception as e:
        logger.error(f"获取可用权限失败: {str(e)}")
        raise HTTPException(status_code=500, detail="获取可用权限失败")