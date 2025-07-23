from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
import logging
from app.services.ai_service import call_deepseek_api
from .auth import get_current_user
from app.services.user_service import UserInDB, UserService

# 添加日志器
logger = logging.getLogger(__name__)

router = APIRouter()
user_service = UserService()

class AISearchRequest(BaseModel):
    search_value: str
    export_countries: list[str]
    import_countries: list[str]

@router.post("/search")
async def search(
    request: AISearchRequest,
    current_user: UserInDB = Depends(get_current_user)
):
    """AI搜索（需要AI搜索权限）"""
    logger.info(f"用户 {current_user.username} 发起AI搜索请求: {request.search_value}")
    
    # 检查权限
    user_permissions = user_service.get_user_permissions(current_user.username)
    if "ai_search" not in user_permissions:
        logger.warning(f"用户 {current_user.username} 缺少AI搜索权限")
        raise HTTPException(status_code=403, detail="缺少AI搜索权限")
    
    try:
        result = await call_deepseek_api(
            request.search_value,
            request.export_countries,
            request.import_countries
        )
        logger.info(f"用户 {current_user.username} AI搜索成功")
        return result
    except Exception as e:
        logger.error(f"用户 {current_user.username} AI搜索失败: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))