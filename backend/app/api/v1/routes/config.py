from fastapi import APIRouter, Depends, HTTPException, status
from typing import Dict, Any
from app.utils.config_manager import config_manager
from app.api.v1.routes.auth import get_current_user
from app.services.user_service import UserInDB
from pydantic import BaseModel
import logging

logger = logging.getLogger(__name__)
router = APIRouter()

class CountryMappingRequest(BaseModel):
    english_name: str
    chinese_name: str

@router.get("/country-mapping", response_model=Dict[str, str], tags=["配置管理"])
def get_country_mapping(current_user: UserInDB = Depends(get_current_user)):
    """获取国家映射配置"""
    try:
        return config_manager.get_country_mapping()
    except Exception as e:
        logger.error(f"获取国家映射配置失败: {str(e)}")
        raise HTTPException(status_code=500, detail="获取配置失败")

@router.post("/country-mapping", response_model=Dict[str, Any], tags=["配置管理"])
def add_country_mapping(
    request: CountryMappingRequest,
    current_user: UserInDB = Depends(get_current_user)
):
    """添加国家映射配置（仅管理员）"""
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="无权限执行此操作"
        )
    
    try:
        config_manager.add_country_mapping(request.english_name, request.chinese_name)
        return {
            "message": "国家映射添加成功",
            "english_name": request.english_name,
            "chinese_name": request.chinese_name
        }
    except Exception as e:
        logger.error(f"添加国家映射失败: {str(e)}")
        raise HTTPException(status_code=500, detail="添加配置失败")

@router.delete("/country-mapping/{english_name}", response_model=Dict[str, Any], tags=["配置管理"])
def remove_country_mapping(
    english_name: str,
    current_user: UserInDB = Depends(get_current_user)
):
    """删除国家映射配置（仅管理员）"""
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="无权限执行此操作"
        )
    
    try:
        config_manager.remove_country_mapping(english_name)
        return {
            "message": "国家映射删除成功",
            "english_name": english_name
        }
    except Exception as e:
        logger.error(f"删除国家映射失败: {str(e)}")
        raise HTTPException(status_code=500, detail="删除配置失败")

@router.post("/reload", response_model=Dict[str, Any], tags=["配置管理"])
def reload_configs(current_user: UserInDB = Depends(get_current_user)):
    """手动重新加载所有配置（仅管理员）"""
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="无权限执行此操作"
        )
    
    try:
        config_manager.reload_all_configs()
        return {"message": "配置重新加载成功"}
    except Exception as e:
        logger.error(f"重新加载配置失败: {str(e)}")
        raise HTTPException(status_code=500, detail="重新加载配置失败")