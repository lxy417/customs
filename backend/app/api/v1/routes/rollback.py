from fastapi import APIRouter, Depends, HTTPException, Query
from typing import Dict, Any, Optional
from app.services.rollback_service import RollbackService
from app.api.v1.routes.auth import get_current_user
from app.services.user_service import UserInDB
from app.utils.permissions import require_permissions
from pydantic import BaseModel
import logging

logger = logging.getLogger(__name__)
router = APIRouter()

class RollbackRequest(BaseModel):
    task_id: str
    dry_run: bool = False

@router.get("/preview/{task_id}", response_model=Dict[str, Any], tags=["数据回滚"])
@require_permissions(["data_import"])
async def preview_rollback(
    task_id: str,
    current_user: UserInDB = Depends(get_current_user)
):
    """预览回滚操作"""
    rollback_service = RollbackService()
    
    # 检查权限
    if not current_user.is_admin:
        # 非管理员只能回滚自己的任务
        from app.services.import_task_service import ImportTaskService
        task_service = ImportTaskService()
        task = await task_service.get_task(task_id)
        if not task or task.get('user_id') != current_user.username:
            raise HTTPException(status_code=403, detail="无权访问此任务")
    
    result = await rollback_service.preview_rollback(task_id)
    
    if not result['success']:
        raise HTTPException(status_code=400, detail=result['error'])
    
    return result

@router.post("/execute", response_model=Dict[str, Any], tags=["数据回滚"])
@require_permissions(["data_import"])
async def execute_rollback(
    request: RollbackRequest,
    current_user: UserInDB = Depends(get_current_user)
):
    """执行回滚操作"""
    rollback_service = RollbackService()
    
    # 检查权限
    if not current_user.is_admin:
        # 非管理员只能回滚自己的任务
        from app.services.import_task_service import ImportTaskService
        task_service = ImportTaskService()
        task = await task_service.get_task(request.task_id)
        if not task or task.get('user_id') != current_user.username:
            raise HTTPException(status_code=403, detail="无权访问此任务")
    
    result = await rollback_service.execute_rollback(
        task_id=request.task_id,
        user_id=current_user.username,
        dry_run=request.dry_run
    )
    
    if not result['success']:
        raise HTTPException(status_code=400, detail=result['error'])
    
    return result

@router.get("/can-rollback/{task_id}", response_model=Dict[str, Any], tags=["数据回滚"])
@require_permissions(["data_import"])
async def check_can_rollback(
    task_id: str,
    current_user: UserInDB = Depends(get_current_user)
):
    """检查任务是否可以回滚"""
    rollback_service = RollbackService()
    
    # 检查权限
    if not current_user.is_admin:
        from app.services.import_task_service import ImportTaskService
        task_service = ImportTaskService()
        task = await task_service.get_task(task_id)
        if not task or task.get('user_id') != current_user.username:
            raise HTTPException(status_code=403, detail="无权访问此任务")
    
    result = await rollback_service.can_rollback(task_id)
    return result

@router.get("/history", response_model=Dict[str, Any], tags=["数据回滚"])
@require_permissions(["data_import"])
async def get_rollback_history(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    current_user: UserInDB = Depends(get_current_user)
):
    """获取回滚历史记录"""
    rollback_service = RollbackService()
    
    # 非管理员只能查看自己的回滚记录
    user_id = None if current_user.is_admin else current_user.username
    
    result = await rollback_service.get_rollback_history(
        user_id=user_id,
        page=page,
        page_size=page_size
    )
    
    return result