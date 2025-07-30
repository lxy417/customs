from typing import Optional, List, Dict, Any
from datetime import datetime
import logging
import re
from app.utils.elasticsearch import ESClient
from app.config.settings import settings
from pydantic import BaseModel
from elasticsearch.helpers import bulk
import pandas as pd
from .hscode_service import hscode_service

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
                        "编码产品描述": {
                            "type": "text",
                            "fields": {
                                "keyword": {
                                    "type": "keyword",
                                    "ignore_above": 256
                                }
                            }
                        },
                        "日期": {"type": "date", "format": "yyyy-MM-dd"},
                        "进口商": {
                            "type": "keyword",
                            "fields": {
                                "text": {
                                    "type": "text",
                                    "analyzer": "standard"
                                }
                            }
                        },
                        "进口商所在国家": {"type": "keyword"},
                        "出口商": {
                            "type": "keyword",
                            "fields": {
                                "text": {
                                    "type": "text",
                                    "analyzer": "standard"
                                }
                            }
                        },
                        "出口商所在国家": {"type": "keyword"},
                        "数量单位": {"type": "keyword"},
                        "数量": {"type": "float"},
                        "公吨": {"type": "float"},
                        "金额美元": {"type": "float"},
                        "详细产品名称": {
                            "type": "text",
                            "fields": {
                                "keyword": {
                                    "type": "keyword",
                                    "ignore_above": 256
                                }
                            }
                        },
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

    def _clean_customs_code(self, code: Any) -> str:
        """清理海关编码格式"""
        if pd.isna(code):
            return ""
        
        code_str = str(code)
        # 移除小数点（如果是整数形式的浮点数）
        if '.' in code_str and code_str.replace('.', '').isdigit():
            code_str = str(int(float(code_str)))
        
        return code_str

    def _is_valid_value(self, value: Any) -> bool:
        """检查值是否有效（非空、非NaN）"""
        if pd.isna(value):
            return False
        if value is None:
            return False
        if isinstance(value, str) and value.strip() == "":
            return False
        return True

    def _build_query_conditions(self, query_params: Dict[str, Any], enable_fuzzy: bool = False) -> Dict[str, Any]:
        """构建通用的查询条件
        
        Args:
            query_params: 查询参数
            enable_fuzzy: 是否启用模糊查询
            
        Returns:
            构建好的查询条件
        """
        query_body = {"bool": {"must": [], "filter": []}}
        
        # 添加用户权限过滤（非管理员只能查看授权的海关编码）
        if query_params.get('allowed_customs_codes'):
            query_body["bool"]["filter"].append({
                "terms": {"海关编码": query_params['allowed_customs_codes']}
            })
        
        # 修改海关编码查询以支持多个编码和前缀查询
        if query_params.get('customs_code'):
            customs_codes = query_params['customs_code']
            
            # 如果是字符串，转换为列表
            if isinstance(customs_codes, str):
                customs_codes = [customs_codes]
            elif not isinstance(customs_codes, list):
                customs_codes = [str(customs_codes)]
            
            # 过滤空值
            customs_codes = [code for code in customs_codes if code and str(code).strip()]
            
            if customs_codes:
                if len(customs_codes) == 1:
                    code = customs_codes[0].strip()
                    # 检查是否为完整的海关编码（6位数字）
                    if len(code) == 6 and code.isdigit():
                        # 完整编码使用精确匹配
                        query_body["bool"]["must"].append({"term": {"海关编码": code}})
                    else:
                        # 前缀查询：支持2位、4位前缀查询
                        query_body["bool"]["must"].append({"prefix": {"海关编码": code}})
                else:
                    # 多个海关编码的情况，需要分别处理
                    should_queries = []
                    for code in customs_codes:
                        code = code.strip()
                        if len(code) == 6 and code.isdigit():
                            # 完整编码使用精确匹配
                            should_queries.append({"term": {"海关编码": code}})
                        else:
                            # 前缀查询
                            should_queries.append({"prefix": {"海关编码": code}})
                    
                    query_body["bool"]["must"].append({
                        "bool": {
                            "should": should_queries,
                            "minimum_should_match": 1
                        }
                    })
        
        if query_params.get('import_country'):
            query_body["bool"]["must"].append({"term": {"进口商所在国家": query_params['import_country']}})
        
        if query_params.get('export_country'):
            query_body["bool"]["must"].append({"term": {"出口商所在国家": query_params['export_country']}})
        
        # 日期范围查询
        if query_params.get('start_date') or query_params.get('end_date'):
            date_range = {}
            if query_params.get('start_date'):
                date_range["gte"] = query_params['start_date']
            if query_params.get('end_date'):
                date_range["lte"] = query_params['end_date']
            query_body["bool"]["must"].append({"range": {"日期": date_range}})
        
        # 进口商查询（支持模糊查询）
        if query_params.get('importer'):
            importer_query = query_params['importer']
            fuzzy_importer = query_params.get('fuzzy_importer', enable_fuzzy)
            
            if fuzzy_importer:
                # 使用模糊查询
                query_body["bool"]["must"].append({
                    "bool": {
                        "should": [
                            {"wildcard": {"进口商": f"*{importer_query}*"}},
                            {"match": {"进口商.text": {"query": importer_query, "fuzziness": "AUTO"}}},
                            {"match_phrase": {"进口商.text": {"query": importer_query}}}
                        ],
                        "minimum_should_match": 1
                    }
                })
            else:
                # 精确查询
                query_body["bool"]["must"].append({"term": {"进口商": importer_query}})
        
        # 出口商查询（支持模糊查询）
        if query_params.get('exporter'):
            exporter_query = query_params['exporter']
            fuzzy_exporter = query_params.get('fuzzy_exporter', enable_fuzzy)
            
            if fuzzy_exporter:
                # 使用模糊查询
                query_body["bool"]["must"].append({
                    "bool": {
                        "should": [
                            {"wildcard": {"出口商": f"*{exporter_query}*"}},
                            {"match": {"出口商.text": {"query": exporter_query, "fuzziness": "AUTO"}}},
                            {"match_phrase": {"出口商.text": {"query": exporter_query}}}
                        ],
                        "minimum_should_match": 1
                    }
                })
            else:
                # 精确查询
                query_body["bool"]["must"].append({"term": {"出口商": exporter_query}})

        # 如果没有条件，使用match_all
        if not query_body["bool"]["must"] and not query_body["bool"]["filter"]:
            return {"match_all": {}}
        else:
            return query_body

    def _build_sort_conditions(self, query_params: Dict[str, Any]) -> List[Dict[str, Any]]:
        """构建排序条件"""
        sort_by = query_params.get('sort_by', '日期')
        sort_order = query_params.get('sort_order', 'desc')
        
        # 定义需要使用keyword子字段进行排序的text类型字段
        text_fields_with_keyword = ['编码产品描述', '详细产品名称']
        
        if sort_by in text_fields_with_keyword:
            sort_field = f"{sort_by}.keyword"
        else:
            sort_field = sort_by
            
        return [{sort_field: {"order": sort_order}}]

    def _get_default_source_fields(self) -> List[str]:
        """获取默认的返回字段"""
        return [
            "海关编码", "编码产品描述", "日期", "进口商", "进口商所在国家", 
            "出口商", "出口商所在国家", "数量单位", "数量", "公吨", 
            "金额美元", "详细产品名称", "提单号", "数据来源", "关单号"
        ]

    def _format_search_results(self, hits: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """格式化搜索结果"""
        data = []
        for hit in hits:
            doc_data = hit["_source"]
            doc_data["id"] = hit["_id"]
            data.append(doc_data)
        return data

    def create_customs_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """创建单条海关数据"""
        try:
            # 清理数据
            cleaned_data = self._clean_data(data)
            
            # 添加时间戳
            cleaned_data["created_at"] = datetime.utcnow()
            cleaned_data["updated_at"] = datetime.utcnow()

            response = self.es_client.index(
                index=self.index_name,
                document=cleaned_data
            )

            logger.info(f"创建海关数据成功: {response['_id']}")
            return {
                "id": response["_id"],
                "result": "created",
                "data": cleaned_data
            }
        except Exception as e:
            logger.error(f"创建海关数据失败: {str(e)}", exc_info=True)
            raise

    def _clean_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """清理单条数据"""
        cleaned_data = {}
        for key, value in data.items():
            if self._is_valid_value(value):
                if key == '海关编码':
                    cleaned_data[key] = self._clean_customs_code(value)
                else:
                    cleaned_data[key] = value
        return cleaned_data

    def bulk_create_customs_data(self, data_list: List[Dict[str, Any]], batch_size: int = 500) -> Dict[str, Any]:
        """批量创建海关数据"""
        try:
            if not data_list:
                return {
                    "result": "success",
                    "total": 0,
                    "success": 0,
                    "failed": 0,
                    "errors": []
                }

            # 准备批量操作
            actions = []
            for data in data_list:
                # 清理数据
                cleaned_data = self._clean_data(data)
                
                # 添加时间戳
                cleaned_data["created_at"] = datetime.utcnow()
                cleaned_data["updated_at"] = datetime.utcnow()

                action = {
                    '_op_type': 'index',
                    '_index': self.index_name,
                    '_source': cleaned_data
                }
                
                # 如果数据中有_es_id，使用它作为文档ID
                if '_es_id' in data:
                    action['_id'] = data['_es_id']
                
                actions.append(action)

            # 执行批量操作
            success_count = 0
            failed_count = 0
            errors = []

            try:
                success, failed = bulk(
                    self.es_client,
                    actions,
                    chunk_size=batch_size,
                    raise_on_error=False,
                    stats_only=False
                )
                success_count = success
                failed_count = len(failed) if failed else 0
                
                if failed:
                    for error_item in failed[:10]:  # 只记录前10个错误
                        error_info = error_item.get('index', {})
                        error_detail = error_info.get('error', {})
                        errors.append({
                            'error_type': error_detail.get('type', 'unknown'),
                            'error_reason': error_detail.get('reason', 'unknown'),
                            'document_id': error_info.get('_id', 'unknown')
                        })

                logger.info(f"批量创建海关数据完成: 成功 {success_count}, 失败 {failed_count}")
                
                result = "success" if failed_count == 0 else "partial_failure"
                return {
                    "result": result,
                    "total": len(data_list),
                    "success": success_count,
                    "failed": failed_count,
                    "errors": errors
                }
                
            except Exception as e:
                logger.error(f"批量创建海关数据失败: {str(e)}")
                return {
                    "result": "failure",
                    "total": len(data_list),
                    "success": 0,
                    "failed": len(data_list),
                    "errors": [{'error_type': 'BulkImportError', 'error_reason': str(e)}]
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
            # 清理数据
            cleaned_data = self._clean_data(data)
            
            # 添加更新时间戳
            cleaned_data["updated_at"] = datetime.utcnow()

            response = self.es_client.update(
                index=self.index_name,
                id=data_id,
                doc=cleaned_data,
                refresh=True  # 修复：使用布尔值而不是字符串
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
                id=data_id,
                refresh=True  # 修复：使用布尔值而不是字符串
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
            # 构建查询条件（不启用模糊查询，删除操作需要精确匹配）
            query_body = self._build_query_conditions(query_params, enable_fuzzy=False)

            # 删除操作必须有条件，不能删除所有数据
            if query_body.get("match_all"):
                raise ValueError("删除条件不能为空")

            # 执行删除操作
            response = self.es_client.delete_by_query(
                index=self.index_name,
                query=query_body,
                conflicts="proceed",
                refresh=True
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
            if not data_ids:
                return {
                    "result": "success",
                    "total": 0,
                    "success": 0,
                    "failed": 0,
                    "errors": []
                }

            actions = []
            for data_id in data_ids:
                actions.append({
                    '_op_type': 'delete',
                    '_index': self.index_name,
                    '_id': data_id
                })

            success_count = 0
            failed_count = 0
            errors = []

            try:
                success, failed = bulk(
                    self.es_client,
                    actions,
                    chunk_size=500,
                    raise_on_error=False,
                    stats_only=False
                )
                success_count = success
                failed_count = len(failed) if failed else 0
                
                if failed:
                    for error_item in failed[:10]:  # 只记录前10个错误
                        error_info = error_item.get('delete', {})
                        error_detail = error_info.get('error', {})
                        errors.append({
                            'error_type': error_detail.get('type', 'unknown'),
                            'error_reason': error_detail.get('reason', 'unknown'),
                            'document_id': error_info.get('_id', 'unknown')
                        })

                logger.info(f"批量删除海关数据完成: 成功 {success_count}, 失败 {failed_count}")
                
                result = "success" if failed_count == 0 else "partial_failure"
                return {
                    "result": result,
                    "total": len(data_ids),
                    "success": success_count,
                    "failed": failed_count,
                    "errors": errors
                }
                
            except Exception as e:
                logger.error(f"批量删除海关数据失败: {str(e)}")
                return {
                    "result": "failure",
                    "total": len(data_ids),
                    "success": 0,
                    "failed": len(data_ids),
                    "errors": [{'error_type': 'BulkDeleteError', 'error_reason': str(e)}]
                }
                
        except Exception as e:
            logger.error(f"批量删除海关数据失败: {str(e)}", exc_info=True)
            raise

    def export_customs_data(self, query_params: Dict[str, Any], user_role_id: Optional[str] = None) -> Dict[str, Any]:
        """根据条件导出海关数据，支持配置化的条数限制"""
        try:
            # 获取导出限制配置
            from app.services.config_service import ConfigService
            config_service = ConfigService()
            
            # 获取用户有效的导出限制配置
            export_limit = config_service.get_effective_config(
                user_role_id or "user", 
                "export_limit", 
                default_value=2000
            )
            
            # 获取系统最大导出限制（安全上限）
            max_export_limit = config_service.get_effective_config(
                user_role_id or "user",
                "export_max_limit",
                default_value=50000
            )
            
            # 构建查询条件（不启用模糊查询，导出需要精确数据）
            query_body = self._build_query_conditions(query_params, enable_fuzzy=False)
            
            # 构建排序条件
            sort = self._build_sort_conditions(query_params)

            # 确定实际的导出条数限制
            actual_limit = self._determine_export_limit(export_limit, max_export_limit)
            
            logger.info(f"导出配置 - 用户限制: {export_limit}, 系统最大限制: {max_export_limit}, 实际限制: {actual_limit}")

            # 执行查询
            if actual_limit == -1:
                # 不限制条数，使用scroll API进行大量数据导出
                return self._export_with_scroll(query_body, sort)
            else:
                # 限制条数的常规导出
                response = self.es_client.search(
                    index=self.index_name,
                    query=query_body,
                    sort=sort,
                    size=actual_limit,
                    _source=self._get_default_source_fields()
                )

                total = response["hits"]["total"]["value"]
                hits = response["hits"]["hits"]
                
                # 格式化结果
                data = self._format_search_results(hits)
                
                return {
                    "total": total,
                    "exported": len(data),
                    "data": data,
                    "export_limit": export_limit,
                    "actual_limit": actual_limit,
                    "is_limited": total > actual_limit
                }
        except Exception as e:
            logger.error(f"数据导出失败: {str(e)}", exc_info=True)
            raise

    def _determine_export_limit(self, export_limit: int, max_export_limit: int) -> int:
        """确定实际的导出限制"""
        if export_limit == -1:
            # 用户配置为不限制，但仍需检查系统最大限制
            return max_export_limit if max_export_limit > 0 else -1
        elif export_limit <= 0:
            # 无效配置，使用默认值
            return 2000
        else:
            # 用户有限制，取用户限制和系统最大限制的较小值
            if max_export_limit > 0:
                return min(export_limit, max_export_limit)
            else:
                return export_limit

    def _export_with_scroll(self, query_body: Dict[str, Any], sort: List[Dict[str, Any]]) -> Dict[str, Any]:
        """使用scroll API导出大量数据（不限制条数时使用）"""
        try:
            # 初始化scroll搜索
            response = self.es_client.search(
                index=self.index_name,
                query=query_body,
                sort=sort,
                size=1000,  # 每批次1000条
                scroll='5m',
                _source=self._get_default_source_fields()
            )
            
            scroll_id = response['_scroll_id']
            total = response["hits"]["total"]["value"]
            all_data = []
            
            # 处理第一批数据
            hits = response["hits"]["hits"]
            all_data.extend(self._format_search_results(hits))
            
            # 继续scroll获取剩余数据
            while len(hits) > 0:
                response = self.es_client.scroll(
                    scroll_id=scroll_id,
                    scroll='5m'
                )
                hits = response["hits"]["hits"]
                if hits:
                    all_data.extend(self._format_search_results(hits))
                
                # 安全检查：如果数据量过大，停止导出
                if len(all_data) > 100000:  # 硬编码的安全上限
                    logger.warning(f"导出数据量过大，已达到安全上限: {len(all_data)}")
                    break
            
            # 清理scroll
            try:
                self.es_client.clear_scroll(scroll_id=scroll_id)
            except Exception as e:
                logger.warning(f"清理scroll失败: {str(e)}")
            
            return {
                "total": total,
                "exported": len(all_data),
                "data": all_data,
                "export_limit": -1,
                "actual_limit": -1,
                "is_limited": False,
                "is_scroll_export": True
            }
            
        except Exception as e:
            logger.error(f"Scroll导出失败: {str(e)}", exc_info=True)
            raise

    def search_customs_data_with_fuzzy(self, query_params: Dict[str, Any]) -> Dict[str, Any]:
        """支持模糊查询的海关数据搜索"""
        try:
            # 构建查询条件，使用前端传递的模糊搜索参数
            query_body = self._build_query_conditions(query_params, enable_fuzzy=False)
            
            # 构建排序条件
            sort = self._build_sort_conditions(query_params)

            # 处理分页
            page = query_params.get('page', 1)
            page_size = query_params.get('page_size', 20)
            from_index = (page - 1) * page_size

            # 执行查询
            response = self.es_client.search(
                index=self.index_name,
                query=query_body,
                sort=sort,
                from_=from_index,
                size=page_size,
                _source=self._get_default_source_fields()
            )

            total = response["hits"]["total"]["value"]
            hits = response["hits"]["hits"]
            
            # 格式化结果
            data = self._format_search_results(hits)
            
            return {
                "total": total,
                "page": page,
                "page_size": page_size,
                "total_pages": (total + page_size - 1) // page_size,
                "data": data
            }
        except Exception as e:
            logger.error(f"模糊查询失败: {str(e)}", exc_info=True)
            raise

    def get_importers_suggestions(self, query: str, size: int = 10) -> List[str]:
        """获取进口商建议"""
        try:
            response = self.es_client.search(
                index=self.index_name,
                query={
                    "bool": {
                        "should": [
                            {"wildcard": {"进口商": f"*{query}*"}},
                            {"match": {"进口商.text": {"query": query, "fuzziness": "AUTO"}}}
                        ]
                    }
                },
                aggs={
                    "importers": {
                        "terms": {
                            "field": "进口商",
                            "size": size,
                            "include": f".*{query}.*"
                        }
                    }
                },
                size=0
            )
            
            suggestions = []
            if "aggregations" in response and "importers" in response["aggregations"]:
                for bucket in response["aggregations"]["importers"]["buckets"]:
                    suggestions.append(bucket["key"])
            
            return suggestions
        except Exception as e:
            logger.error(f"获取进口商建议失败: {str(e)}", exc_info=True)
            raise

    def get_exporters_suggestions(self, query: str, size: int = 10) -> List[str]:
        """获取出口商建议"""
        try:
            response = self.es_client.search(
                index=self.index_name,
                query={
                    "bool": {
                        "should": [
                            {"wildcard": {"出口商": f"*{query}*"}},
                            {"match": {"出口商.text": {"query": query, "fuzziness": "AUTO"}}}
                        ]
                    }
                },
                aggs={
                    "exporters": {
                        "terms": {
                            "field": "出口商",
                            "size": size,
                            "include": f".*{query}.*"
                        }
                    }
                },
                size=0
            )
            
            suggestions = []
            if "aggregations" in response and "exporters" in response["aggregations"]:
                for bucket in response["aggregations"]["exporters"]["buckets"]:
                    suggestions.append(bucket["key"])
            
            return suggestions
        except Exception as e:
            logger.error(f"获取出口商建议失败: {str(e)}", exc_info=True)
            raise

    def get_customs_codes(self, page: int = 1, page_size: int = 50, search: Optional[str] = None) -> Dict[str, Any]:
        """获取海关编码列表"""
        try:
            query = {"match_all": {}}
            if search:
                query = {
                    "bool": {
                        "should": [
                            {"wildcard": {"海关编码": f"*{search}*"}},
                            {"wildcard": {"编码产品描述": f"*{search}*"}}
                        ]
                    }
                }

            from_index = (page - 1) * page_size
            
            response = self.es_client.search(
                index=self.index_name,
                query=query,
                aggs={
                    "customs_codes": {
                        "terms": {
                            "field": "海关编码",
                            "size": 10000  # 获取所有唯一的海关编码
                        },
                        "aggs": {
                            "description": {
                                "terms": {
                                    "field": "编码产品描述.keyword",
                                    "size": 1
                                }
                            }
                        }
                    }
                },
                size=0
            )
            
            codes_data = []
            if "aggregations" in response and "customs_codes" in response["aggregations"]:
                for bucket in response["aggregations"]["customs_codes"]["buckets"]:
                    code = bucket["key"]
                    description = ""
                    if bucket["description"]["buckets"]:
                        description = bucket["description"]["buckets"][0]["key"]
                    
                    if not search or search in code or search in description:
                        codes_data.append({
                            "code": code,
                            "description": description,
                            "count": bucket["doc_count"]
                        })
            
            # 手动分页
            total = len(codes_data)
            start = from_index
            end = start + page_size
            paginated_data = codes_data[start:end]
            
            return {
                "total": total,
                "page": page,
                "page_size": page_size,
                "total_pages": (total + page_size - 1) // page_size,
                "data": paginated_data
            }
        except Exception as e:
            logger.error(f"获取海关编码列表失败: {str(e)}", exc_info=True)
            raise

    def get_countries(self, field: str = "进口商所在国家") -> List[str]:
        """获取国家列表"""
        try:
            if field not in ["进口商所在国家", "出口商所在国家"]:
                field = "进口商所在国家"
                
            response = self.es_client.search(
                index=self.index_name,
                aggs={
                    "countries": {
                        "terms": {
                            "field": field,
                            "size": 1000
                        }
                    }
                },
                size=0
            )
            
            countries = []
            if "aggregations" in response and "countries" in response["aggregations"]:
                for bucket in response["aggregations"]["countries"]["buckets"]:
                    countries.append(bucket["key"])
            
            return sorted(countries)
        except Exception as e:
            logger.error(f"获取国家列表失败: {str(e)}", exc_info=True)
            raise

    def check_duplicates_by_ids(self, document_ids: List[str]) -> Dict[str, Any]:
        """通过文档ID批量检查重复"""
        try:
            if not document_ids:
                return {"existing_ids": [], "new_ids": []}
            
            # 使用mget批量检查文档是否存在
            response = self.es_client.mget(
                index=self.index_name,
                ids=document_ids,
                _source=False  # 只检查存在性，不需要返回文档内容
            )
            
            existing_ids = []
            new_ids = []
            
            for doc in response['docs']:
                doc_id = doc['_id']
                if doc['found']:
                    existing_ids.append(doc_id)
                else:
                    new_ids.append(doc_id)
            
            return {
                "existing_ids": existing_ids,
                "new_ids": new_ids,
                "total_checked": len(document_ids),
                "existing_count": len(existing_ids),
                "new_count": len(new_ids)
            }
            
        except Exception as e:
            logger.error(f"批量检查文档存在性失败: {str(e)}")
            # 如果检查失败，将所有ID视为新的
            return {
                "existing_ids": [],
                "new_ids": document_ids,
                "total_checked": len(document_ids),
                "existing_count": 0,
                "new_count": len(document_ids),
                "error": str(e)
            }