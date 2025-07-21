from typing import Optional, List, Dict, Any
from datetime import datetime
import uuid
import logging
from app.utils.elasticsearch import ESClient
from app.config.settings import settings

logger = logging.getLogger(__name__)

class ImportTaskService:
    def __init__(self):
        self.es_client = ESClient.get_client()
        self.index_name = f"{settings.DATA_INDEX}_import_tasks"
        self._create_index_if_not_exists()

    def _create_index_if_not_exists(self):
        """创建导入任务索引"""
        if not self.es_client.indices.exists(index=self.index_name):
            mapping = {
                "mappings": {
                    "properties": {
                        "task_id": {"type": "keyword"},
                        "original_filename": {"type": "text"},
                        "user_id": {"type": "keyword"},
                        "status": {"type": "keyword"},  # processing, completed, failed
                        "total_files": {"type": "integer"},
                        "success_count": {"type": "integer"},
                        "failed_count": {"type": "integer"},
                        "total_count": {"type": "integer"},
                        "customs_codes": {"type": "keyword"},
                        "start_date": {"type": "date"},
                        "end_date": {"type": "date"},
                        "created_at": {"type": "date"},
                        "completed_at": {"type": "date"},
                        "processed_files": {"type": "object"},
                        "error_details": {"type": "object"},
                        "processing_options": {"type": "object"}
                    }
                }
            }
            self.es_client.indices.create(index=self.index_name, body=mapping)
            logger.info(f"创建导入任务索引: {self.index_name}")

    async def create_task(
        self, 
        original_filename: str, 
        user_id: str,
        total_files: int = 1,
        processing_options: Optional[Dict] = None
    ) -> str:
        """创建新的导入任务"""
        task_id = str(uuid.uuid4())
        
        task_data = {
            "task_id": task_id,
            "original_filename": original_filename,
            "user_id": user_id,
            "status": "processing",
            "total_files": total_files,
            "success_count": 0,
            "failed_count": 0,
            "total_count": 0,
            "created_at": datetime.now().isoformat(),
            "processing_options": processing_options or {}
        }
        
        self.es_client.index(
            index=self.index_name,
            id=task_id,
            body=task_data
        )
        
        logger.info(f"创建导入任务: {task_id}")
        return task_id

    async def update_task(
        self,
        task_id: str,
        status: Optional[str] = None,
        success_count: Optional[int] = None,
        failed_count: Optional[int] = None,
        duplicate_count: Optional[int] = None,
        customs_codes: Optional[List[str]] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        processed_files: Optional[List[Dict[str, Any]]] = None,
        error_details: Optional[List[Dict[str, Any]]] = None
    ) -> bool:
        """更新导入任务"""
        try:
            update_doc = {
                'updated_at': datetime.now().isoformat()
            }
            
            if status:
                update_doc['status'] = status
                if status == 'completed':
                    update_doc['completed_at'] = datetime.now().isoformat()
            
            if success_count is not None:
                update_doc['success_count'] = success_count
            
            if failed_count is not None:
                update_doc['failed_count'] = failed_count
                
            if duplicate_count is not None:
                update_doc['duplicate_count'] = duplicate_count
            
            if customs_codes:
                update_doc['customs_codes'] = customs_codes
            
            if start_date:
                update_doc['start_date'] = start_date
            
            if end_date:
                update_doc['end_date'] = end_date
            
            if processed_files:
                update_doc['processed_files'] = processed_files
            
            if error_details:
                update_doc['error_details'] = error_details
            
            response = self.es_client.update(
                index=self.index_name,
                id=task_id,
                body={'doc': update_doc}
            )
            
            return response['result'] in ['updated', 'noop']
            
        except Exception as e:
            logger.error(f"更新任务失败: {task_id}, {str(e)}")
            return False

    async def get_task(self, task_id: str) -> Optional[Dict[str, Any]]:
        """获取导入任务详情"""
        try:
            response = self.es_client.get(
                index=self.index_name,
                id=task_id
            )
            return response["_source"]
        except Exception as e:
            logger.error(f"获取导入任务失败: {task_id}, {str(e)}")
            return None

    async def get_tasks(
        self,
        user_id: Optional[str] = None,
        status: Optional[str] = None,
        page: int = 1,
        page_size: int = 20
    ) -> Dict[str, Any]:
        """获取导入任务列表"""
        query = {"bool": {"must": []}}
        
        if user_id:
            query["bool"]["must"].append({"term": {"user_id": user_id}})
        
        if status:
            query["bool"]["must"].append({"term": {"status": status}})
        
        if not query["bool"]["must"]:
            query = {"match_all": {}}
        
        search_body = {
            "query": query,
            "sort": [{"created_at": {"order": "desc"}}],
            "from": (page - 1) * page_size,
            "size": page_size
        }
        
        try:
            response = self.es_client.search(
                index=self.index_name,
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
            logger.error(f"获取导入任务列表失败: {str(e)}")
            return {"data": [], "total": 0, "page": page, "page_size": page_size}

    async def get_statistics(self, user_id: Optional[str] = None) -> Dict[str, Any]:
        """获取导入统计信息"""
        query = {"bool": {"must": []}}
        
        if user_id:
            query["bool"]["must"].append({"term": {"user_id": user_id}})
        
        if not query["bool"]["must"]:
            query = {"match_all": {}}
        
        aggs = {
            "total_imports": {"value_count": {"field": "task_id"}},
            "status_breakdown": {
                "terms": {"field": "status"}
            },
            "total_records": {"sum": {"field": "total_count"}},
            "success_records": {"sum": {"field": "success_count"}},
            "failed_records": {"sum": {"field": "failed_count"}}
        }
        
        search_body = {
            "query": query,
            "size": 0,
            "aggs": aggs
        }
        
        try:
            response = self.es_client.search(
                index=self.index_name,
                body=search_body
            )
            
            aggregations = response["aggregations"]
            status_buckets = {bucket["key"]: bucket["doc_count"] 
                            for bucket in aggregations["status_breakdown"]["buckets"]}
            
            return {
                "totalImports": aggregations["total_imports"]["value"],
                "successfulImports": status_buckets.get("completed", 0),
                "failedImports": status_buckets.get("failed", 0),
                "processingImports": status_buckets.get("processing", 0),
                "totalRecords": aggregations["total_records"]["value"],
                "successRecords": aggregations["success_records"]["value"],
                "failedRecords": aggregations["failed_records"]["value"]
            }
        except Exception as e:
            logger.error(f"获取导入统计信息失败: {str(e)}")
            return {
                "totalImports": 0,
                "successfulImports": 0,
                "failedImports": 0,
                "processingImports": 0,
                "totalRecords": 0,
                "successRecords": 0,
                "failedRecords": 0
            }