from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from app.services.ai_service import call_deepseek_api
from .auth import get_current_user
from app.services.user_service import UserInDB, UserService

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
    # 检查权限
    user_permissions = user_service.get_user_permissions(current_user.username)
    if "ai_search" not in user_permissions:
        raise HTTPException(status_code=403, detail="缺少AI搜索权限")
    
    try:
        result = await call_deepseek_api(
            request.search_value,
            request.export_countries,
            request.import_countries
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))