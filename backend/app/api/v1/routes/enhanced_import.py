from fastapi import APIRouter, Depends, File, UploadFile, HTTPException, BackgroundTasks, Query
from typing import Dict, Any, List, Optional
import os
import tempfile
import asyncio
from datetime import datetime
from pathlib import Path
from app.utils.enhanced_data_processor import EnhancedDataProcessor
from app.services.import_task_service import ImportTaskService
from app.api.v1.routes.auth import get_current_user
from app.services.user_service import UserInDB
from app.config.logging_config import get_logger
from app.utils.permissions import require_permissions

# 使用专门的日志器
logger = get_logger('app.api.v1.routes.enhanced_import')
router = APIRouter()

# 创建临时目录
temp_dir = Path(tempfile.mkdtemp())
processed_dir = Path("./processed_data")
processed_dir.mkdir(exist_ok=True)

async def process_files_background(
    files: List[Dict[str, str]],
    task_id: str, 
    batch_size: int = 500,
    skip_duplicates: bool = True
):
    """后台处理文件任务"""
    processor = EnhancedDataProcessor(output_dir=str(processed_dir))
    task_service = ImportTaskService()
    
    try:
        total_success = 0
        total_failed = 0
        total_duplicates = 0
        original_total = 0
        processed_files = []
        customs_codes = set()
        all_dates = []
        all_errors = []
        all_imported_document_ids = []
        data_source_counts = {}  # 新增：数据源统计
        detected_data_sources = set()  # 新增：检测到的数据源
        
        for file_info in files:
            file_path = file_info['file_path']
            original_filename = file_info['original_filename']
            
            try:
                logger.info(f"处理文件: {original_filename} (路径: {file_path})")
                
                # 预处理文件
                result = processor.process_excel_file(
                    file_path=file_path,
                    skip_duplicates=skip_duplicates
                )
                
                if not result['success']:
                    raise Exception(result.get('error', '文件处理失败'))
                
                original_total += result.get('total_records', 0)
                
                # 导入到数据库
                file_success = 0
                file_failed = 0
                file_duplicates = 0
                file_errors = []
                file_original_total = result.get('total_records', 0)
                file_imported_ids = []
                file_data_sources = {}  # 单个文件的数据源统计
                
                for output_file in result['output_files']:
                    import_result = await processor.import_to_database(
                        file_path=output_file['filepath'],
                        batch_size=batch_size,
                        check_duplicates=True,
                        task_id=task_id
                    )
                    
                    file_success += import_result['success_count']
                    file_failed += import_result['failed_count']
                    file_duplicates += import_result['duplicate_count']
                    
                    # 收集导入的文档ID
                    if import_result.get('imported_document_ids'):
                        file_imported_ids.extend(import_result['imported_document_ids'])
                        all_imported_document_ids.extend(import_result['imported_document_ids'])
                    
                    # 收集错误信息
                    if import_result.get('errors'):
                        file_errors.extend(import_result['errors'])
                    
                    # 统计数据源信息
                    try:
                        import pandas as pd
                        df = pd.read_excel(output_file['filepath'])
                        if '数据获取网站' in df.columns:
                            source_counts = df['数据获取网站'].value_counts().to_dict()
                            for source, count in source_counts.items():
                                detected_data_sources.add(source)
                                file_data_sources[source] = file_data_sources.get(source, 0) + count
                                data_source_counts[source] = data_source_counts.get(source, 0) + count
                    except Exception as e:
                        logger.warning(f"统计数据源信息失败: {str(e)}")
                
                total_success += file_success
                total_failed += file_failed
                total_duplicates += file_duplicates
                all_errors.extend(file_errors)
                
                # 收集统计信息
                for output_file in result['output_files']:
                    try:
                        import pandas as pd
                        df = pd.read_excel(output_file['filepath'])
                        if '海关编码' in df.columns:
                            codes = df['海关编码'].dropna().unique()
                            customs_codes.update(codes)
                        if '日期' in df.columns:
                            dates = pd.to_datetime(df['日期'], errors='coerce').dropna()
                            all_dates.extend(dates)
                    except Exception as e:
                        logger.warning(f"收集统计信息失败: {str(e)}")
                
                processed_files.append({
                    'filename': original_filename,
                    'success_count': file_success,
                    'failed_count': file_failed,
                    'duplicate_count': file_duplicates,
                    'original_total_count': file_original_total,
                    'imported_document_count': len(file_imported_ids),
                    'data_source_counts': file_data_sources,  # 新增：文件级别的数据源统计
                    'output_files': result['output_files'],
                    'errors': file_errors[:3]
                })
                
            except Exception as e:
                logger.error(f"处理文件失败: {original_filename}, {str(e)}")
                processed_files.append({
                    'filename': original_filename,
                    'success_count': 0,
                    'failed_count': 1,
                    'duplicate_count': 0,
                    'original_total_count': 0,
                    'imported_document_count': len(file_imported_ids),
                    'data_source_counts': {},  # 新增：空的数据源统计
                    'error': str(e)
                })
                total_failed += 1
                all_errors.append({
                    'error_type': 'FileProcessingError',
                    'error_reason': str(e),
                    'filename': original_filename
                })
        
        # 计算日期范围
        start_date = None
        end_date = None
        if all_dates:
            start_date = min(all_dates).strftime('%Y-%m-%d')
            end_date = max(all_dates).strftime('%Y-%m-%d')
        
        # 确定数据源信息
        detected_data_sources = []
        if data_source_counts:
            detected_data_sources = list(data_source_counts.keys())
        
        # 数据源字段记录所有检测到的数据源数组
        data_source_field = detected_data_sources if detected_data_sources else []
        
        # 更新任务状态，包括数据源信息
        await task_service.update_task(
            task_id=task_id,
            status='completed' if total_failed == 0 else 'failed',
            success_count=total_success,
            failed_count=total_failed,
            duplicate_count=total_duplicates,
            original_total_count=original_total,
            customs_codes=list(customs_codes),
            start_date=start_date,
            end_date=end_date,
            processed_files=processed_files,
            error_details=all_errors[:10],
            data_source=data_source_field,  # 修正：数据源数组 ["gtm.sinoimex"] 或 ["国贸通"] 或 ["gtm.sinoimex","国贸通"]
            data_source_counts=data_source_counts  # 详细的数据源统计
        )
        
        # 单独更新导入的文档ID列表
        if all_imported_document_ids:
            await task_service.update_imported_document_ids(task_id, all_imported_document_ids)
            logger.info(f"任务 {task_id} 总共导入了 {len(all_imported_document_ids)} 个文档")
        
        logger.info(f"任务完成: {task_id}, 成功: {total_success}, 失败: {total_failed}, 重复: {total_duplicates}, 原始总数: {original_total}, 数据源: {data_source_counts}")
        
    except Exception as e:
        logger.error(f"后台任务失败: {task_id}, {str(e)}")
        await task_service.update_task(
            task_id=task_id,
            status='failed',
            error_details=[{'error_type': 'ProcessingError', 'error_message': str(e)}]
        )
    finally:
        # 清理临时文件
        for file_info in files:
            try:
                file_path = file_info['file_path']
                if os.path.exists(file_path):
                    os.remove(file_path)
            except Exception as e:
                logger.warning(f"清理临时文件失败: {file_path}, {str(e)}")

@router.post("/upload", response_model=Dict[str, Any], tags=["数据导入"])
@require_permissions(["data_import"])
async def upload_files(
    background_tasks: BackgroundTasks,
    files: List[UploadFile] = File(...),
    batch_size: int = 500,
    skip_duplicates: bool = True,
    current_user: UserInDB = Depends(get_current_user)
):
    """批量上传Excel文件进行预处理和导入"""
    if not files:
        raise HTTPException(status_code=400, detail="没有上传文件")
    
    # 验证文件类型
    allowed_extensions = {'.xlsx', '.xls'}
    for file in files:
        file_ext = Path(file.filename).suffix.lower()
        if file_ext not in allowed_extensions:
            raise HTTPException(
                status_code=400, 
                detail=f"不支持的文件类型: {file.filename}. 只支持 .xlsx 和 .xls 文件"
            )
    
    try:
        # 保存上传的文件，同时记录原始文件名
        saved_files = []
        original_filenames = []
        
        for file in files:
            # 生成唯一的临时文件名
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S_%f')
            temp_filename = f"{current_user.username}_{timestamp}_{file.filename}"
            file_path = temp_dir / temp_filename
            
            with open(file_path, "wb") as buffer:
                content = await file.read()
                buffer.write(content)
            
            saved_files.append({
                'file_path': str(file_path),
                'original_filename': file.filename  # 保存原始文件名
            })
            original_filenames.append(file.filename)
        
        # 创建导入任务
        task_service = ImportTaskService()
        task_id = await task_service.create_task(
            original_filename=", ".join(original_filenames),  # 使用原始文件名列表
            user_id=current_user.username,
            total_files=len(files),
            processing_options={
                'batch_size': batch_size,
                'skip_duplicates': skip_duplicates
            }
        )
        
        # 启动后台处理任务
        background_tasks.add_task(
            process_files_background,
            saved_files,  # 传递包含原始文件名的字典列表
            task_id,
            batch_size,
            skip_duplicates
        )
        
        return {
            "message": "文件上传成功，开始后台处理",
            "task_id": task_id,
            "file_count": len(files),
            "files": original_filenames  # 返回原始文件名列表
        }
        
    except Exception as e:
        logger.error(f"文件上传失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"文件上传失败: {str(e)}")

@router.get("/history", response_model=Dict[str, Any], tags=["增强数据导入"])
@require_permissions(["data_import"])
async def get_import_history(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    status: Optional[str] = Query(None),
    current_user: UserInDB = Depends(get_current_user)
):
    """获取导入历史记录"""
    task_service = ImportTaskService()
    
    # 非管理员只能查看自己的记录
    user_id = None if current_user.is_admin else current_user.username
    
    result = await task_service.get_tasks(
        user_id=user_id,
        status=status,
        page=page,
        page_size=page_size
    )
    
    return result

@router.get("/task/{task_id}", response_model=Dict[str, Any], tags=["增强数据导入"])
@require_permissions(["data_import"])
async def get_task_detail(
    task_id: str,
    current_user: UserInDB = Depends(get_current_user)
):
    """获取导入任务详情"""
    task_service = ImportTaskService()
    task = await task_service.get_task(task_id)
    
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")
    
    # 非管理员只能查看自己的任务
    if not current_user.is_admin and task.get('user_id') != current_user.username:
        raise HTTPException(status_code=403, detail="无权访问此任务")
    
    return task

@router.get("/statistics", response_model=Dict[str, Any], tags=["增强数据导入"])
@require_permissions(["data_import"])
async def get_import_statistics(
    current_user: UserInDB = Depends(get_current_user)
):
    """获取导入统计信息"""
    task_service = ImportTaskService()
    
    # 非管理员只能查看自己的统计
    user_id = None if current_user.is_admin else current_user.username
    
    statistics = await task_service.get_statistics(user_id=user_id)
    return statistics