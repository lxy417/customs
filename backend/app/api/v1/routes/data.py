from fastapi import APIRouter, Depends, Query, HTTPException
from typing import Optional, List, Dict, Any
from datetime import date
from app.utils.elasticsearch import ESClient
from app.config.settings import settings
from .auth import get_current_user
from app.services.user_service import UserInDB
import logging

logger = logging.getLogger(__name__)
router = APIRouter()
es_client = ESClient.get_client()
index_name = settings.DATA_INDEX

@router.get("/search", response_model=Dict[str, Any], tags=["数据查询"])
def search_customs_data(
    current_user: UserInDB = Depends(get_current_user),
    customs_code: Optional[str] = Query(None, description="海关编码"),
    import_country: Optional[str] = Query(None, description="进口国家"),
    export_country: Optional[str] = Query(None, description="出口国家"),
    start_date: Optional[date] = Query(None, description="开始日期 (YYYY-MM-DD)"),
    end_date: Optional[date] = Query(None, description="结束日期 (YYYY-MM-DD)"),
    importer: Optional[str] = Query(None, description="进口商"),
    exporter: Optional[str] = Query(None, description="出口商"),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页条数"),
    sort_by: str = Query("日期", description="排序字段"),
    sort_order: str = Query("desc", pattern="^(asc|desc)$", description="排序方式 (asc/desc)")
):
    """查询海关数据，支持多条件过滤、分页和排序"""
    # 构建查询条件
    query_body = {"bool": {"must": [], "filter": []}}
    # 添加用户权限过滤（非管理员只能查看授权的海关编码）
    if not current_user.is_admin and current_user.allowed_customs_codes:
        query_body["bool"]["filter"].append({
            "terms": {"海关编码": current_user.allowed_customs_codes}
        })
    
    # 添加查询条件
    if customs_code:
        query_body["bool"]["must"].append({"term": {"海关编码": customs_code}})
    
    if import_country:
        query_body["bool"]["must"].append({"term": {"进口商所在国家": import_country}})
    
    if export_country:
        query_body["bool"]["must"].append({"term": {"出口商所在国家": export_country}})
    
    if start_date or end_date:
        date_range = {}
        if start_date:
            date_range["gte"] = start_date.strftime("%Y-%m-%d")
        if end_date:
            date_range["lte"] = end_date.strftime("%Y-%m-%d")
        query_body["bool"]["must"].append({"range": {"日期": date_range}})
    
    if importer:
        query_body["bool"]["must"].append({"term": {"进口商": importer}})
    
    if exporter:
        query_body["bool"]["must"].append({"term": {"出口商": exporter}})
    
        # 更好的处理方式是：如果 must 和 filter 都为空，才使用 match_all。
    # 否则，就使用构建好的 bool 查询。
    if not query_body["bool"]["must"] and not query_body["bool"]["filter"]:
        final_query_body = {"match_all": {}}
    else:
        final_query_body = query_body

    # 构建排序条件
    sort = [{sort_by: {"order": sort_order}}]
    
    # 计算分页
    from_index = (page - 1) * page_size
    
    try:
        # 执行查询
        response = es_client.search(
            index=index_name,
            query=final_query_body,
            sort=sort,
            from_=from_index,
            size=page_size,
            _source=[
                "海关编码", "编码产品描述", "日期", "进口商", "进口商所在国家", 
                "出口商", "出口商所在国家", "数量单位", "数量", "公吨", 
                "金额美元", "详细产品名称", "提单号", "数据来源", "关单号"
            ]
        )
        
        # 处理结果
        total = response["hits"]["total"]["value"]
        hits = response["hits"]["hits"]
        
        data = [hit["_source"] for hit in hits]
        
        return {
            "total": total,
            "page": page,
            "page_size": page_size,
            "total_pages": (total + page_size - 1) // page_size,
            "data": data
        }
    except Exception as e:
        logger.error(f"数据查询失败: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"数据查询失败: {str(e)}")

@router.get("/customs-codes", response_model=List[str], tags=["数据查询"])
def get_all_customs_codes(current_user: UserInDB = Depends(get_current_user)):
    """获取所有可用的海关编码列表"""
    try:
        # 构建聚合查询
        aggs_query = {
            "size": 0,
            "aggs": {
                "customs_codes": {
                    "terms": {
                        "field": "海关编码",
                        "size": 10000,  # 假设海关编码数量不超过10000
                        "order": {"_key": "asc"}
                    }
                }
            }
        }
        
        # 如果不是管理员，只返回有权限的海关编码
        if not current_user.is_admin and current_user.allowed_customs_codes:
            aggs_query["query"] = {
                "terms": {"海关编码": current_user.allowed_customs_codes}
            }
        
        response = es_client.search(index=index_name, body=aggs_query)
        
        # 提取海关编码列表
        customs_codes = [bucket["key"] for bucket in response["aggregations"]["customs_codes"]["buckets"]]
        
        return customs_codes
    except Exception as e:
        logger.error(f"获取海关编码列表失败: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"获取海关编码列表失败: {str(e)}")

@router.get("/countries", response_model=Dict[str, List[str]], tags=["数据查询"])
def get_all_countries(current_user: UserInDB = Depends(get_current_user)):
    """获取所有可用的进口国家和出口国家列表"""
    try:
        # 构建聚合查询
        aggs_query = {
            "size": 0,
            "aggs": {
                "import_countries": {
                    "terms": {
                        "field": "进口商所在国家",
                        "size": 1000,
                        "order": {"_key": "asc"}
                    }
                },
                "export_countries": {
                    "terms": {
                        "field": "出口商所在国家",
                        "size": 1000,
                        "order": {"_key": "asc"}
                    }
                }
            }
        }
        
        # 如果不是管理员，只返回有权限的海关编码相关的国家
        if not current_user.is_admin and current_user.allowed_customs_codes:
            aggs_query["query"] = {
                "terms": {"海关编码": current_user.allowed_customs_codes}
            }
        
        response = es_client.search(index=index_name, body=aggs_query)
        
        # 提取国家列表
        import_countries = [bucket["key"] for bucket in response["aggregations"]["import_countries"]["buckets"]]
        export_countries = [bucket["key"] for bucket in response["aggregations"]["export_countries"]["buckets"]]
        
        return {
            "import_countries": import_countries,
            "export_countries": export_countries
        }
    except Exception as e:
        logger.error(f"获取国家列表失败: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"获取国家列表失败: {str(e)}")