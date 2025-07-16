from fastapi import APIRouter, Depends, File, UploadFile, HTTPException, BackgroundTasks
from typing import Dict, Any
import os
import tempfile
from app.utils.data_import import DataImportService
from app.api.v1.routes.auth import get_current_user
from app.services.user_service import UserInDB
import logging

logger = logging.getLogger(__name__)
router = APIRouter()

temp_dir = tempfile.mkdtemp()

def import_data_in_background(file_path: str) -> Dict[str, Any]:
    """在后台执行数据导入"""
    try:
        data_import_service = DataImportService()
        result = data_import_service.import_from_excel(file_path)
        # 导入完成后删除临时文件
        if os.path.exists(file_path):
            os.remove(file_path)
        return result
    except Exception as e:
        logger.error(f"后台数据导入失败: {str(e)}", exc_info=True)
        raise

@router.post("/excel", response_model=Dict[str, Any], tags=["数据导入"])
def import_excel_data(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    current_user: UserInDB = Depends(get_current_user)
):
    """上传Excel文件并导入数据（仅管理员）"""
    if not current_user.is_admin:
        raise HTTPException(
            status_code=403,
            detail="没有权限执行数据导入，需要管理员权限"
        )
    
    # 验证文件类型
    if not file.filename.endswith((".xlsx", ".xls")):
        raise HTTPException(
            status_code=400,
            detail="不支持的文件类型，请上传Excel文件 (.xlsx 或 .xls)"
        )
    
    try:
        # 保存临时文件
        file_path = os.path.join(temp_dir, file.filename)
        with open(file_path, "wb") as buffer:
            buffer.write(file.file.read())
        
        # 将数据导入任务添加到后台执行
        background_tasks.add_task(import_data_in_background, file_path)
        
        return {
            "message": "数据导入任务已启动，请稍后查看结果",
            "filename": file.filename
        }
    except Exception as e:
        logger.error(f"文件上传或导入任务启动失败: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"数据导入失败: {str(e)}")