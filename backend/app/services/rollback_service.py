from typing import Optional, List, Dict, Any
from datetime import datetime
import logging
from app.utils.elasticsearch import ESClient
from app.config.settings import settings
from app.services.import_task_service import ImportTaskService
from app.services.data_service import DataService
from elasticsearch.helpers import bulk

logger = logging.getLogger(__name__)

class RollbackService:
    def __init__(self):
        self.es_client = ESClient.get_client()
        self.data_index = settings.DATA_INDEX
        self.import_task_service = ImportTaskService()
        self.data_service = DataService()

    async def preview_rollback(self, task_id: str) -> Dict[str, Any]:
        """预览回滚操作，显示将要删除的数据"""
        try:
            # 获取任务信息
            task = await self.import_task_service.get_task(task_id)
            if not task:
                return {
                    'success': False,
                    'error': '任务不存在'
                }
            
            # 检查任务状态
            if task.get('status') != 'completed':
                return {
                    'success': False,
                    'error': '只能回滚已完成的导入任务'
                }
            
            if task.get('rollback_status') == 'completed':
                return {
                    'success': False,
                    'error': '该任务已经被回滚'
                }
            
            # 获取导入的文档ID列表
            document_ids = task.get('imported_document_ids', [])
            if not document_ids:
                return {
                    'success': False,
                    'error': '该任务没有记录导入的文档ID，无法回滚'
                }
            
            # 检查这些文档是否仍然存在
            existing_docs = []
            missing_docs = []
            
            # 批量检查文档存在性
            for i in range(0, len(document_ids), 100):  # 每次检查100个
                batch_ids = document_ids[i:i+100]
                try:
                    response = self.es_client.mget(
                        index=self.data_index,
                        body={'ids': batch_ids}
                    )
                    
                    for doc in response['docs']:
                        if doc['found']:
                            existing_docs.append({
                                'id': doc['_id'],
                                'source': doc['_source']
                            })
                        else:
                            missing_docs.append(doc['_id'])
                            
                except Exception as e:
                    logger.error(f"检查文档存在性失败: {str(e)}")
                    continue
            
            # 统计信息
            preview_data = {
                'task_info': {
                    'task_id': task_id,
                    'original_filename': task.get('original_filename'),
                    'user_id': task.get('user_id'),
                    'created_at': task.get('created_at'),
                    'success_count': task.get('success_count', 0)
                },
                'rollback_summary': {
                    'total_imported_docs': len(document_ids),
                    'existing_docs': len(existing_docs),
                    'missing_docs': len(missing_docs),
                    'will_be_deleted': len(existing_docs)
                },
                'sample_data': existing_docs[:5],  # 显示前5条数据样本
                'missing_doc_ids': missing_docs[:10]  # 显示前10个缺失的文档ID
            }
            
            return {
                'success': True,
                'preview': preview_data
            }
            
        except Exception as e:
            logger.error(f"预览回滚失败: {task_id}, {str(e)}")
            return {
                'success': False,
                'error': f'预览回滚失败: {str(e)}'
            }

    async def execute_rollback(
        self, 
        task_id: str, 
        user_id: str,
        dry_run: bool = False
    ) -> Dict[str, Any]:
        """执行回滚操作"""
        try:
            # 更新回滚状态为进行中
            await self.import_task_service.update_rollback_status(
                task_id=task_id,
                rollback_status='pending',
                rollback_by=user_id
            )
            
            # 获取任务信息
            task = await self.import_task_service.get_task(task_id)
            if not task:
                return {
                    'success': False,
                    'error': '任务不存在'
                }
            
            document_ids = task.get('imported_document_ids', [])
            if not document_ids:
                return {
                    'success': False,
                    'error': '该任务没有记录导入的文档ID，无法回滚'
                }
            
            deleted_count = 0
            failed_count = 0
            errors = []
            
            if not dry_run:
                # 执行实际删除
                for i in range(0, len(document_ids), 100):  # 批量删除，每次100个
                    batch_ids = document_ids[i:i+100]
                    
                    try:
                        # 构建批量删除操作
                        actions = []
                        for doc_id in batch_ids:
                            actions.append({
                                '_op_type': 'delete',
                                '_index': self.data_index,
                                '_id': doc_id
                            })
                        
                        # 执行批量删除
                        success, failed = bulk(
                            self.es_client,
                            actions,
                            index=self.data_index,
                            raise_on_error=False,
                            raise_on_exception=False
                        )
                        
                        deleted_count += success
                        failed_count += len(failed)
                        
                        # 记录失败的操作
                        for failure in failed:
                            errors.append({
                                'doc_id': failure.get('delete', {}).get('_id'),
                                'error': str(failure.get('delete', {}).get('error', 'Unknown error'))
                            })
                            
                    except Exception as e:
                        logger.error(f"批量删除失败: {str(e)}")
                        failed_count += len(batch_ids)
                        errors.append({
                            'batch': f"{i}-{i+len(batch_ids)}",
                            'error': str(e)
                        })
            
            # 更新回滚状态
            rollback_details = {
                'deleted_count': deleted_count,
                'failed_count': failed_count,
                'total_documents': len(document_ids),
                'errors': errors[:10],  # 只保留前10个错误
                'dry_run': dry_run
            }
            
            rollback_status = 'completed' if failed_count == 0 else 'failed'
            if dry_run:
                rollback_status = 'preview'
            
            await self.import_task_service.update_rollback_status(
                task_id=task_id,
                rollback_status=rollback_status,
                rollback_by=user_id,
                rollback_details=rollback_details
            )
            
            return {
                'success': True,
                'rollback_result': rollback_details
            }
            
        except Exception as e:
            logger.error(f"执行回滚失败: {task_id}, {str(e)}")
            
            # 更新回滚状态为失败
            await self.import_task_service.update_rollback_status(
                task_id=task_id,
                rollback_status='failed',
                rollback_by=user_id,
                rollback_details={'error': str(e)}
            )
            
            return {
                'success': False,
                'error': f'执行回滚失败: {str(e)}'
            }

    async def get_rollback_history(
        self,
        user_id: Optional[str] = None,
        page: int = 1,
        page_size: int = 20
    ) -> Dict[str, Any]:
        """获取回滚历史记录"""
        try:
            query = {
                "bool": {
                    "must": [
                        {"exists": {"field": "rollback_status"}},
                        {"bool": {"must_not": [{"term": {"rollback_status": "none"}}]}}
                    ]
                }
            }
            
            if user_id:
                query["bool"]["must"].append({"term": {"rollback_by": user_id}})
            
            search_body = {
                "query": query,
                "sort": [{"rollback_at": {"order": "desc"}}],
                "from": (page - 1) * page_size,
                "size": page_size
            }
            
            response = self.es_client.search(
                index=self.import_task_service.index_name,
                body=search_body
            )
            
            tasks = [hit["_source"] for hit in response["hits"]["hits"]]
            total = response["hits"]["total"]["value"]
            
            return {
                "data": tasks,
                "total": total,
                "page": page,
                "page_size": page_size
            }
            
        except Exception as e:
            logger.error(f"获取回滚历史失败: {str(e)}")
            return {"data": [], "total": 0, "page": page, "page_size": page_size}

    async def can_rollback(self, task_id: str) -> Dict[str, Any]:
        """检查任务是否可以回滚"""
        try:
            task = await self.import_task_service.get_task(task_id)
            if not task:
                return {
                    'can_rollback': False,
                    'reason': '任务不存在'
                }
            
            # 检查任务状态
            if task.get('status') != 'completed':
                return {
                    'can_rollback': False,
                    'reason': '只能回滚已完成的导入任务'
                }
            
            # 检查是否已经回滚
            if task.get('rollback_status') == 'completed':
                return {
                    'can_rollback': False,
                    'reason': '该任务已经被回滚'
                }
            
            # 检查是否有导入的文档ID
            document_ids = task.get('imported_document_ids', [])
            if not document_ids:
                return {
                    'can_rollback': False,
                    'reason': '该任务没有记录导入的文档ID，无法回滚'
                }
            
            return {
                'can_rollback': True,
                'document_count': len(document_ids)
            }
            
        except Exception as e:
            logger.error(f"检查回滚条件失败: {task_id}, {str(e)}")
            return {
                'can_rollback': False,
                'reason': f'检查失败: {str(e)}'
            }