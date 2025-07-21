from typing import Optional, List, Dict, Any
from datetime import datetime
import logging
from app.utils.elasticsearch import ESClient
from app.config.settings import settings
from pydantic import BaseModel
from enum import Enum

logger = logging.getLogger(__name__)

class ImportStatus(str, Enum):
    PENDING = "pending"      # 等待处理
    PROCESSING = "processing"  # 处理中
    SUCCESS = "success"      # 成功
    FAILED = "failed"        # 失败
    PARTIAL = "partial"      # 部分成功

class ImportHistoryCreate(BaseModel):
    filename: str
    original_filename: str
    file_size: int
    user_id: str
    customs_codes: List[str] = []
    date_range_start: Optional[str] = None
    date_range_end: Optional[str] = None
    total_sheets: int = 0
    total_records: int = 0
    processed_records: int = 0
    failed_records: int = 0
    duplicates_removed: int = 0
    status: ImportStatus = ImportStatus.PENDING
    error_message: Optional[str] = None
    processing_details: Dict[str, Any] = {}

class ImportHistoryUpdate(BaseModel):
    status: Optional[ImportStatus] = None
    processed_records: Optional[int] = None
    failed_records: Optional[int] = None
    duplicates_removed: Optional[int] = None
    error_message: Optional[str] = None
    processing_details: Optional[Dict[str, Any]] = None
    completed_at: Optional[str] = None

class ImportHistoryService:
    def __init__(self):
        self.es_client = ESClient.get_client()
        self.index_name = f"{settings.DATA_INDEX}_import_history"
        self._create_index_if_not_exists()

    def _create_index_if_not_exists(self):
        """创建导入历史索引"""
        if not self.es_client.indices.exists(index=self.index_name):
            mapping = {
                "mappings": {
                    "properties": {
                        "filename": {"type": "keyword"},
                        "original_filename": {"type": "keyword"},
                        "file_size": {"type": "long"},
                        "user_id": {"type": "keyword"},
                        "customs_codes": {"type": "keyword"},
                        "date_range_start": {"type": "date", "format": "yyyy-MM-dd"},
                        "date_range_end": {"type": "date", "format": "yyyy-MM-dd"},
                        "total_sheets": {"type": "integer"},
                        "total_records": {"type": "integer"},
                        "processed_records": {"type": "integer"},
                        "failed_records": {"type": "integer"},
                        "duplicates_removed": {"type": "integer"},
                        "status": {"type": "keyword"},
                        "error_message": {"type": "text"},
                        "processing_details": {"type": "object"},
                        "created_at": {"type": "date"},
                        "updated_at": {"type": "date"},
                        "completed_at": {"type": "date"}
                    }
                }
            }
            self.es_client.indices.create(index=self.index_name, body=mapping)
            logger.info(f"创建导入历史索引: {self.index_name}")

    def create_import_record(self, import_data: ImportHistoryCreate) -> str:
        """创建导入记录"""
        try:
            doc = import_data.dict()
            doc['created_at'] = datetime.now().isoformat()
            doc['updated_at'] = datetime.now().isoformat()
            
            response = self.es_client.index(
                index=self.index_name,
                body=doc
            )
            
            import_id = response['_id']
            logger.info(f"创建导入记录成功: {import_id}")
            return import_id
            
        except Exception as e:
            logger.error(f"创建导入记录失败: {str(e)}")
            raise

    def update_import_record(self, import_id: str, update_data: ImportHistoryUpdate) -> bool:
        """更新导入记录"""
        try:
            doc = {k: v for k, v in update_data.dict().items() if v is not None}
            doc['updated_at'] = datetime.now().isoformat()
            
            response = self.es_client.update(
                index=self.index_name,
                id=import_id,
                body={"doc": doc}
            )
            
            logger.info(f"更新导入记录成功: {import_id}")
            return True
            
        except Exception as e:
            logger.error(f"更新导入记录失败: {str(e)}")
            return False

    def get_import_record(self, import_id: str) -> Optional[Dict[str, Any]]:
        """获取导入记录"""
        try:
            response = self.es_client.get(
                index=self.index_name,
                id=import_id
            )
            
            record = response['_source']
            record['id'] = response['_id']
            return record
            
        except Exception as e:
            logger.error(f"获取导入记录失败: {str(e)}")
            return None

    def get_import_history(self, user_id: Optional[str] = None, 
                          status: Optional[ImportStatus] = None,
                          page: int = 1, size: int = 20) -> Dict[str, Any]:
        """获取导入历史列表"""
        try:
            query = {"bool": {"must": []}}
            
            if user_id:
                query["bool"]["must"].append({"term": {"user_id": user_id}})
            
            if status:
                query["bool"]["must"].append({"term": {"status": status.value}})
            
            if not query["bool"]["must"]:
                query = {"match_all": {}}
            
            from_index = (page - 1) * size
            
            response = self.es_client.search(
                index=self.index_name,
                body={
                    "query": query,
                    "sort": [{"created_at": {"order": "desc"}}],
                    "from": from_index,
                    "size": size
                }
            )
            
            records = []
            for hit in response['hits']['hits']:
                record = hit['_source']
                record['id'] = hit['_id']
                records.append(record)
            
            return {
                "records": records,
                "total": response['hits']['total']['value'],
                "page": page,
                "size": size,
                "total_pages": (response['hits']['total']['value'] + size - 1) // size
            }
            
        except Exception as e:
            logger.error(f"获取导入历史失败: {str(e)}")
            return {"records": [], "total": 0, "page": page, "size": size, "total_pages": 0}

    def get_import_statistics(self, user_id: Optional[str] = None) -> Dict[str, Any]:
        """获取导入统计信息"""
        try:
            query = {"bool": {"must": []}}
            
            if user_id:
                query["bool"]["must"].append({"term": {"user_id": user_id}})
            
            if not query["bool"]["must"]:
                query = {"match_all": {}}
            
            response = self.es_client.search(
                index=self.index_name,
                body={
                    "query": query,
                    "size": 0,
                    "aggs": {
                        "status_stats": {
                            "terms": {"field": "status"}
                        },
                        "total_records": {
                            "sum": {"field": "total_records"}
                        },
                        "processed_records": {
                            "sum": {"field": "processed_records"}
                        },
                        "failed_records": {
                            "sum": {"field": "failed_records"}
                        },
                        "duplicates_removed": {
                            "sum": {"field": "duplicates_removed"}
                        },
                        "recent_imports": {
                            "date_histogram": {
                                "field": "created_at",
                                "calendar_interval": "day",
                                "order": {"_key": "desc"}
                            }
                        }
                    }
                }
            )
            
            aggs = response['aggregations']
            
            status_counts = {}
            for bucket in aggs['status_stats']['buckets']:
                status_counts[bucket['key']] = bucket['doc_count']
            
            recent_imports = []
            for bucket in aggs['recent_imports']['buckets']:
                recent_imports.append({
                    'date': bucket['key_as_string'][:10],
                    'count': bucket['doc_count']
                })
            
            return {
                "status_counts": status_counts,
                "total_records": int(aggs['total_records']['value']),
                "processed_records": int(aggs['processed_records']['value']),
                "failed_records": int(aggs['failed_records']['value']),
                "duplicates_removed": int(aggs['duplicates_removed']['value']),
                "recent_imports": recent_imports[:30]  # 最近30天
            }
            
        except Exception as e:
            logger.error(f"获取导入统计失败: {str(e)}")
            return {
                "status_counts": {},
                "total_records": 0,
                "processed_records": 0,
                "failed_records": 0,
                "duplicates_removed": 0,
                "recent_imports": []
            }

    def delete_import_record(self, import_id: str) -> bool:
        """删除导入记录"""
        try:
            self.es_client.delete(
                index=self.index_name,
                id=import_id
            )
            logger.info(f"删除导入记录成功: {import_id}")
            return True
            
        except Exception as e:
            logger.error(f"删除导入记录失败: {str(e)}")
            return False