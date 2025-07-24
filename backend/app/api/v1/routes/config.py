from fastapi import APIRouter, Depends, HTTPException, status
from typing import Dict, Any, List, Optional
from app.services.config_service import ConfigService, SystemConfigUpdate, RoleConfigOverride
from app.api.v1.routes.auth import get_current_user
from app.services.user_service import UserInDB
from app.utils.permissions import require_permissions, Permissions
from pydantic import BaseModel
import logging

logger = logging.getLogger(__name__)
router = APIRouter()

class CountryMappingRequest(BaseModel):
    english_name: str
    chinese_name: str

class ConfigUpdateRequest(BaseModel):
    config_value: str
    description: Optional[str] = None

class RoleConfigRequest(BaseModel):
    config_value: str

@router.get("/country-mapping", response_model=Dict[str, str], tags=["配置管理"])
async def get_country_mapping(current_user: UserInDB = Depends(get_current_user)):
    """获取国家映射配置"""
    try:
        from app.utils.config_manager import config_manager
        return config_manager.get_country_mapping()
    except Exception as e:
        logger.error(f"获取国家映射配置失败: {str(e)}")
        raise HTTPException(status_code=500, detail="获取配置失败")

@router.post("/country-mapping", tags=["配置管理"])
@require_permissions([Permissions.CONFIG_MANAGE])
async def add_country_mapping(
    request: CountryMappingRequest,
    current_user: UserInDB = Depends(get_current_user)
):
    """添加国家映射配置"""
    try:
        from app.utils.config_manager import config_manager
        config_manager.add_country_mapping(request.english_name, request.chinese_name)
        return {"message": "国家映射添加成功"}
    except Exception as e:
        logger.error(f"添加国家映射配置失败: {str(e)}")
        raise HTTPException(status_code=500, detail="添加配置失败")

# 系统配置管理
@router.get("/system", response_model=List[Dict[str, Any]], tags=["系统配置"])
@require_permissions([Permissions.CONFIG_VIEW])
async def get_system_configs(
    category: Optional[str] = None,
    current_user: UserInDB = Depends(get_current_user)
):
    """获取系统配置列表"""
    try:
        config_service = ConfigService()
        configs = config_service.get_all_system_configs(category=category)
        logger.info(f"用户 {current_user.username} 查看系统配置，类别: {category}")
        return configs
    except Exception as e:
        logger.error(f"获取系统配置失败: {str(e)}")
        raise HTTPException(status_code=500, detail="获取系统配置失败")

@router.put("/system/{config_key}", tags=["系统配置"])
@require_permissions([Permissions.CONFIG_MANAGE])
async def update_system_config(
    config_key: str,
    request: ConfigUpdateRequest,
    current_user: UserInDB = Depends(get_current_user)
):
    """更新系统配置"""
    try:
        config_service = ConfigService()
        config_update = SystemConfigUpdate(
            config_value=request.config_value,
            description=request.description
        )
        updated_config = config_service.update_system_config(config_key, config_update)
        
        if not updated_config:
            raise HTTPException(status_code=404, detail="配置项不存在")
        
        logger.info(f"用户 {current_user.username} 更新系统配置: {config_key} = {request.config_value}")
        return {"message": "配置更新成功", "config": updated_config.dict()}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"更新系统配置失败: {str(e)}")
        raise HTTPException(status_code=500, detail="更新配置失败")

# 角色配置覆盖管理 - 获取所有角色配置覆盖（必须放在其他路由之前）
@router.get("/role-overrides/all", response_model=List[Dict[str, Any]], tags=["角色配置"])
@require_permissions([Permissions.CONFIG_VIEW])
async def get_all_role_config_overrides(
    current_user: UserInDB = Depends(get_current_user)
):
    """获取所有角色的配置覆盖"""
    try:
        config_service = ConfigService()
        overrides = config_service.get_all_role_config_overrides()
        logger.info(f"用户 {current_user.username} 查看所有角色配置覆盖")
        return overrides
    except Exception as e:
        logger.error(f"获取所有角色配置覆盖失败: {str(e)}")
        raise HTTPException(status_code=500, detail="获取所有角色配置覆盖失败")

# 角色配置覆盖管理 - 支持查询参数方式（必须放在路径参数路由之前）
@router.get("/role-overrides", response_model=List[Dict[str, Any]], tags=["角色配置"])
@require_permissions([Permissions.CONFIG_VIEW])
async def get_role_config_overrides_by_query(
    role_id: Optional[str] = None,
    current_user: UserInDB = Depends(get_current_user)
):
    """获取角色配置覆盖（查询参数方式）"""
    if not role_id:
        raise HTTPException(status_code=400, detail="role_id参数是必需的")
    
    try:
        config_service = ConfigService()
        overrides = config_service.get_role_config_overrides(role_id)
        logger.info(f"用户 {current_user.username} 查看角色 {role_id} 的配置覆盖")
        return overrides
    except Exception as e:
        logger.error(f"获取角色配置覆盖失败: {str(e)}")
        raise HTTPException(status_code=500, detail="获取角色配置覆盖失败")

@router.get("/role-overrides/{role_id}", response_model=List[Dict[str, Any]], tags=["角色配置"])
@require_permissions([Permissions.CONFIG_VIEW])
async def get_role_config_overrides(
    role_id: str,
    current_user: UserInDB = Depends(get_current_user)
):
    """获取角色配置覆盖"""
    try:
        config_service = ConfigService()
        overrides = config_service.get_role_config_overrides(role_id)
        logger.info(f"用户 {current_user.username} 查看角色 {role_id} 的配置覆盖")
        return overrides
    except Exception as e:
        logger.error(f"获取角色配置覆盖失败: {str(e)}")
        raise HTTPException(status_code=500, detail="获取角色配置覆盖失败")

@router.put("/role-overrides/{role_id}/{config_key}", tags=["角色配置"])
@require_permissions([Permissions.CONFIG_MANAGE])
async def set_role_config_override(
    role_id: str,
    config_key: str,
    request: RoleConfigRequest,
    current_user: UserInDB = Depends(get_current_user)
):
    """设置角色配置覆盖"""
    try:
        config_service = ConfigService()
        role_config = RoleConfigOverride(
            role_id=role_id,
            config_key=config_key,
            config_value=request.config_value
        )
        override = config_service.set_role_config_override(role_config)
        
        logger.info(f"用户 {current_user.username} 设置角色 {role_id} 的配置覆盖: {config_key} = {request.config_value}")
        return {"message": "角色配置覆盖设置成功", "override": override.dict()}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"设置角色配置覆盖失败: {str(e)}")
        raise HTTPException(status_code=500, detail="设置角色配置覆盖失败")

@router.delete("/role-overrides/{role_id}/{config_key}", tags=["角色配置"])
@require_permissions([Permissions.CONFIG_MANAGE])
async def delete_role_config_override(
    role_id: str,
    config_key: str,
    current_user: UserInDB = Depends(get_current_user)
):
    """删除角色配置覆盖"""
    try:
        config_service = ConfigService()
        success = config_service.delete_role_config_override(role_id, config_key)
        
        if not success:
            raise HTTPException(status_code=404, detail="配置覆盖不存在")
        
        logger.info(f"用户 {current_user.username} 删除角色 {role_id} 的配置覆盖: {config_key}")
        return {"message": "角色配置覆盖删除成功"}
    except Exception as e:
        logger.error(f"删除角色配置覆盖失败: {str(e)}")
        raise HTTPException(status_code=500, detail="删除角色配置覆盖失败")

# 用户有效配置
@router.get("/effective", response_model=Dict[str, Any], tags=["用户配置"])
async def get_user_effective_configs(
    current_user: UserInDB = Depends(get_current_user)
):
    """获取当前用户的有效配置"""
    try:
        config_service = ConfigService()
        effective_configs = config_service.get_user_effective_configs(current_user.role_id)
        return effective_configs
    except Exception as e:
        logger.error(f"获取用户有效配置失败: {str(e)}")
        raise HTTPException(status_code=500, detail="获取用户配置失败")