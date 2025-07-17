from typing import Optional, List, Dict, Any
from datetime import datetime
import logging
from app.utils.elasticsearch import ESClient
from app.config.settings import settings
from pydantic import BaseModel

logger = logging.getLogger(__name__)

class CustomsDataCreate(BaseModel):
    海关编码: str
    编码产品描述: str
    日期: str
    进口商: str
    进口商所在国家: str
    出口商: str
    出口商所在国家: str
    数量单位: str
    数量: float
    公吨: Optional[float] = None
    金额美元: float
    详细产品名称: str
    提单号: str
    数据来源: str
    关单号: str

class CustomsDataUpdate(BaseModel):
    海关编码: Optional[str] = None
    编码产品描述: Optional[str] = None
    日期: Optional[str] = None
    进口商: Optional[str] = None
    进口商所在国家: Optional[str] = None
    出口商: Optional[str] = None
    出口商所在国家: Optional[str] = None
    数量单位: Optional[str] = None
    数量: Optional[float] = None
    公吨: Optional[float] = None
    金额美元: Optional[float] = None
    详细产品名称: Optional[str] = None
    提单号: Optional[str] = None
    数据来源: Optional[str] = None
    关单号: Optional[str] = None

class DataService:
    def __init__(self):
        self.es_client = ESClient.get_client()
        self.index_name = settings.DATA_INDEX
        self._create_index_if_not_exists()

    def _create_index_if_not_exists(self):
        """创建数据索引（如果不存在）"""
        if not self.es_client.indices.exists(index=self.index_name):
            mapping = {
                "mappings": {
                    "properties": {
                        "海关编码": {"type": "keyword"},
                        "编码产品描述": {"type": "text"},
                        "日期": {"type": "date", "format": "yyyy-MM-dd"},
                        "进口商": {"type": "keyword"},
                        "进口商所在国家": {"type": "keyword"},
                        "出口商": {"type": "keyword"},
                        "出口商所在国家": {"type": "keyword"},
                        "数量单位": {"type": "keyword"},
                        "数量": {"type": "float"},
                        "公吨": {"type": "float"},
                        "金额美元": {"type": "float"},
                        "详细产品名称": {"type": "text"},
                        "提单号": {"type": "keyword"},
                        "数据来源": {"type": "keyword"},
                        "关单号": {"type": "keyword"},
                        "created_at": {"type": "date"},
                        "updated_at": {"type": "date"}
                    }
                }
            }
            self.es_client.indices.create(index=self.index_name, body=mapping)
            logger.info(f"创建数据索引: {self.index_name}")
        else:
            logger.info(f"数据索引已存在: {self.index_name}")

    def create_customs_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """创建单条海关数据"""
        try:
            # 添加时间戳
            data["created_at"] = datetime.utcnow()
            data["updated_at"] = datetime.utcnow()

            response = self.es_client.index(
                index=self.index_name,
                document=data
            )

            logger.info(f"创建海关数据成功: {response['_id']}")
            return {
                "id": response["_id"],
                "result": "created",
                "data": data
            }
        except Exception as e:
            logger.error(f"创建海关数据失败: {str(e)}", exc_info=True)
            raise

    def bulk_create_customs_data(self, data_list: List[Dict[str, Any]]) -> Dict[str, Any]:
        """批量创建海关数据"""
        try:
            bulk_operations = []
            for data in data_list:
                # 添加时间戳
                data["created_at"] = datetime.utcnow()
                data["updated_at"] = datetime.utcnow()

                bulk_operations.append({
                    "index": {
                        "_index": self.index_name
                    }
                })
                bulk_operations.append(data)

            if bulk_operations:
                response = self.es_client.bulk(body=bulk_operations)

                if response.get("errors"):
                    errors = [item for item in response["items"] if item.get("index", {}).get("error")]
                    logger.error(f"批量创建海关数据部分失败: {len(errors)}条数据出错")
                    return {
                        "result": "partial_failure",
                        "total": len(data_list),
                        "success": len(data_list) - len(errors),
                        "failed": len(errors),
                        "errors": errors
                    }

                logger.info(f"批量创建海关数据成功: {len(data_list)}条")
                return {
                    "result": "success",
                    "total": len(data_list),
                    "success": len(data_list)
                }
            return {
                "result": "success",
                "total": 0,
                "success": 0
            }
        except Exception as e:
            logger.error(f"批量创建海关数据失败: {str(e)}", exc_info=True)
            raise

    def get_customs_data_by_id(self, data_id: str) -> Optional[Dict[str, Any]]:
        """根据ID获取海关数据"""
        try:
            response = self.es_client.get(
                index=self.index_name,
                id=data_id
            )
            if response["found"]:
                data = response["_source"]
                data["id"] = response["_id"]
                return data
            return None
        except Exception as e:
            logger.error(f"获取海关数据失败: {str(e)}", exc_info=True)
            raise

    def update_customs_data(self, data_id: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """更新海关数据"""
        try:
            # 添加更新时间戳
            data["updated_at"] = datetime.utcnow()

            response = self.es_client.update(
                index=self.index_name,
                id=data_id,
                doc=data
            )

            logger.info(f"更新海关数据成功: {data_id}")
            return {
                "id": data_id,
                "result": response["result"]
            }
        except Exception as e:
            logger.error(f"更新海关数据失败: {str(e)}", exc_info=True)
            raise

    def delete_customs_data(self, data_id: str) -> Dict[str, Any]:
        """删除单条海关数据"""
        try:
            response = self.es_client.delete(
                index=self.index_name,
                id=data_id
            )

            logger.info(f"删除海关数据成功: {data_id}")
            return {
                "id": data_id,
                "result": response["result"]
            }
        except Exception as e:
            logger.error(f"删除海关数据失败: {str(e)}", exc_info=True)
            raise

    def bulk_delete_by_condition(self, query_params: Dict[str, Any]) -> Dict[str, Any]:
        """根据条件批量删除海关数据"""
        try:
            # 构建查询条件
            query_body = {"bool": {"must": [], "filter": []}}

            # 添加查询条件
            if query_params.get('customs_code'):
                query_body["bool"]["must"].append({"term": {"海关编码": query_params['customs_code']}})
            
            if query_params.get('import_country'):
                query_body["bool"]["must"].append({"term": {"进口商所在国家": query_params['import_country']}})
            
            if query_params.get('export_country'):
                query_body["bool"]["must"].append({"term": {"出口商所在国家": query_params['export_country']}})
            
            if query_params.get('start_date') or query_params.get('end_date'):
                date_range = {}
                if query_params.get('start_date'):
                    date_range["gte"] = query_params['start_date']
                if query_params.get('end_date'):
                    date_range["lte"] = query_params['end_date']
                query_body["bool"]["must"].append({"range": {"日期": date_range}})
            
            if query_params.get('importer'):
                query_body["bool"]["must"].append({"term": {"进口商": query_params['importer']}})
            
            if query_params.get('exporter'):
                query_body["bool"]["must"].append({"term": {"出口商": query_params['exporter']}})

            # 如果没有条件，不执行删除操作
            if not query_body["bool"]["must"] and not query_body["bool"]["filter"]:
                raise ValueError("删除条件不能为空")

            # 执行删除操作
            response = self.es_client.delete_by_query(
                index=self.index_name,
                query=query_body,
                conflicts="proceed"
            )

            logger.info(f"按条件批量删除海关数据成功: {response['deleted']}条记录")
            return {
                "result": "success",
                "deleted": response['deleted']
            }
        except Exception as e:
            logger.error(f"按条件批量删除海关数据失败: {str(e)}", exc_info=True)
            raise

    def bulk_delete_customs_data(self, data_ids: List[str]) -> Dict[str, Any]:
        """批量删除海关数据"""
        try:
            bulk_operations = []
            for data_id in data_ids:
                bulk_operations.append({
                    "delete": {
                        "_index": self.index_name,
                        "_id": data_id
                    }
                })

            if bulk_operations:
                response = self.es_client.bulk(body=bulk_operations)

                if response.get("errors"):
                    errors = [item for item in response["items"] if item.get("delete", {}).get("error")]
                    logger.error(f"批量删除海关数据部分失败: {len(errors)}条数据出错")
                    return {
                        "result": "partial_failure",
                        "total": len(data_ids),
                        "success": len(data_ids) - len(errors),
                        "failed": len(errors),
                        "errors": errors
                    }

                logger.info(f"批量删除海关数据成功: {len(data_ids)}条")
                return {
                    "result": "success",
                    "total": len(data_ids),
                    "success": len(data_ids)
                }
            return {
                "result": "success",
                "total": 0,
                "success": 0
            }
        except Exception as e:
            logger.error(f"批量删除海关数据失败: {str(e)}", exc_info=True)
            raise