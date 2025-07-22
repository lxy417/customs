from fastapi import APIRouter, Depends, Query, HTTPException, Body
from typing import Optional, List, Dict, Any
from datetime import date
from app.utils.elasticsearch import ESClient
from app.config.settings import settings
from .auth import get_current_user
from app.services.user_service import UserInDB, UserService
from app.services.data_service import DataService, CustomsDataCreate, CustomsDataUpdate
from app.utils.permissions import (
    require_permissions, 
    require_admin, 
    require_data_access, 
    require_customs_code_access,
    Permissions
)
import logging

logger = logging.getLogger(__name__)
router = APIRouter()
es_client = ESClient.get_client()
index_name = settings.DATA_INDEX
data_service = DataService()
user_service = UserService()  # 添加用户服务实例

@router.post("/", response_model=Dict[str, Any], tags=["数据管理"])
@require_permissions([Permissions.DATA_CREATE])
async def create_customs_data(
    data: CustomsDataCreate = Body(...),
    current_user: UserInDB = Depends(get_current_user)
):
    """创建海关数据（需要数据创建权限）"""
    try:
        return data_service.create_customs_data(data.dict())
    except Exception as e:
        logger.error(f"创建海关数据失败: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"创建海关数据失败: {str(e)}")

@router.put("/{data_id}", response_model=Dict[str, Any], tags=["数据管理"])
@require_permissions([Permissions.DATA_UPDATE])
async def update_customs_data(
    data_id: str,
    data: CustomsDataUpdate = Body(...),
    current_user: UserInDB = Depends(get_current_user)
):
    """更新海关数据（需要数据更新权限）"""
    try:
        return data_service.update_customs_data(data_id, data.dict(exclude_unset=True))
    except Exception as e:
        logger.error(f"更新海关数据失败: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"更新海关数据失败: {str(e)}")

@router.delete("/{data_id}", response_model=Dict[str, Any], tags=["数据管理"])
@require_permissions([Permissions.DATA_DELETE])
async def delete_customs_data(
    data_id: str,
    current_user: UserInDB = Depends(get_current_user)
):
    """删除海关数据（需要数据删除权限）"""
    try:
        return data_service.delete_customs_data(data_id)
    except Exception as e:
        logger.error(f"删除海关数据失败: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"删除海关数据失败: {str(e)}")

@router.post("/bulk-delete-by-condition", response_model=Dict[str, Any], tags=["数据管理"])
@require_admin()
async def bulk_delete_by_condition(
    query_params: Dict[str, Any] = Body(..., embed=True),
    current_user: UserInDB = Depends(get_current_user)
):
    """按条件批量删除海关数据（仅管理员）"""
    try:
        return data_service.bulk_delete_by_condition(query_params)
    except Exception as e:
        logger.error(f"按条件批量删除海关数据失败: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"按条件批量删除海关数据失败: {str(e)}")

@router.post("/bulk-delete", response_model=Dict[str, Any], tags=["数据管理"])
@require_permissions([Permissions.DATA_DELETE])
async def bulk_delete_customs_data(
    data_ids: List[str] = Body(..., embed=True),
    current_user: UserInDB = Depends(get_current_user)
):
    """批量删除海关数据（需要数据删除权限）"""
    try:
        return data_service.bulk_delete_customs_data(data_ids)
    except Exception as e:
        logger.error(f"批量删除海关数据失败: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"批量删除海关数据失败: {str(e)}")

@router.post("/export", response_model=Dict[str , Any], tags=["数据管理"])
@require_permissions([Permissions.DATA_EXPORT])
@require_data_access()
async def export_customs_data(
    query_params: Dict[str, Any] = Body(..., embed=True),
    current_user: UserInDB = Depends(get_current_user),
    allowed_customs_codes: Optional[List[str]] = None
):
    """导出海关数据，最多2000条（需要数据导出权限，自动过滤海关编码）"""
    try:
        # 如果用户不是管理员，添加海关编码过滤
        if allowed_customs_codes is not None:
            query_params['allowed_customs_codes'] = allowed_customs_codes
        
        return data_service.export_customs_data(query_params)
    except Exception as e:
        logger.error(f"数据导出失败: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"数据导出失败: {str(e)}")

@router.get("/search", response_model=Dict[str, Any], tags=["数据查询"])
@require_permissions([Permissions.DATA_VIEW])
@require_data_access()
async def search_customs_data(
    current_user: UserInDB = Depends(get_current_user),
    customs_code: Optional[str] = Query(None, description="海关编码"),
    import_country: Optional[str] = Query(None, description="进口国家"),
    export_country: Optional[str] = Query(None, description="出口国家"),
    start_date: Optional[date] = Query(None, description="开始日期 (YYYY-MM-DD)"),
    end_date: Optional[date] = Query(None, description="结束日期 (YYYY-MM-DD)"),
    importer: Optional[str] = Query(None, description="进口商"),
    exporter: Optional[str] = Query(None, description="出口商"),
    fuzzy_importer: bool = Query(False, description="是否对进口商进行模糊查询"),
    fuzzy_exporter: bool = Query(False, description="是否对出口商进行模糊查询"),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页条数"),
    sort_by: str = Query("日期", description="排序字段"),
    sort_order: str = Query("desc", pattern="^(asc|desc)$", description="排序方式 (asc/desc)"),
    allowed_customs_codes: Optional[List[str]] = None
):
    """查询海关数据，支持多条件过滤、分页、排序和模糊查询（需要数据查看权限，自动过滤海关编码）"""
    # 构建查询参数
    query_params = {
        'customs_code': customs_code,
        'import_country': import_country,
        'export_country': export_country,
        'start_date': start_date.strftime("%Y-%m-%d") if start_date else None,
        'end_date': end_date.strftime("%Y-%m-%d") if end_date else None,
        'importer': importer,
        'exporter': exporter,
        'fuzzy_importer': fuzzy_importer,
        'fuzzy_exporter': fuzzy_exporter,
        'page': page,
        'page_size': page_size,
        'sort_by': sort_by,
        'sort_order': sort_order
    }
    
    # 如果用户不是管理员，添加海关编码过滤
    if allowed_customs_codes is not None:
        query_params['allowed_customs_codes'] = allowed_customs_codes
    
    try:
        return data_service.search_customs_data_with_fuzzy(query_params)
    except Exception as e:
        logger.error(f"数据查询失败: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"数据查询失败: {str(e)}")

@router.get("/importers/suggestions", response_model=List[str], tags=["数据查询"])
@require_permissions([Permissions.DATA_VIEW])
async def get_importers_suggestions(
    query: str = Query(..., description="查询关键词"),
    limit: int = Query(10, ge=1, le=50, description="返回结果数量限制"),
    current_user: UserInDB = Depends(get_current_user)
):
    """获取进口商建议列表（用于自动完成，需要数据查看权限）"""
    try:
        return data_service.get_importers_suggestions(query, limit)
    except Exception as e:
        logger.error(f"获取进口商建议失败: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"获取进口商建议失败: {str(e)}")

@router.get("/exporters/suggestions", response_model=List[str], tags=["数据查询"])
@require_permissions([Permissions.DATA_VIEW])
async def get_exporters_suggestions(
    query: str = Query(..., description="查询关键词"),
    limit: int = Query(10, ge=1, le=50, description="返回结果数量限制"),
    current_user: UserInDB = Depends(get_current_user)
):
    """获取出口商建议列表（用于自动完成，需要数据查看权限）"""
    try:
        return data_service.get_exporters_suggestions(query, limit)
    except Exception as e:
        logger.error(f"获取出口商建议失败: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"获取出口商建议失败: {str(e)}")

@router.get("/customs-codes", response_model=List[str], tags=["数据查询"])
@require_permissions([Permissions.DATA_VIEW])
@require_data_access()
async def get_all_customs_codes(
    current_user: UserInDB = Depends(get_current_user),
    allowed_customs_codes: Optional[List[str]] = None
):
    """获取所有可用的海关编码列表（需要数据查看权限，自动过滤海关编码）"""
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
        
        # 如果用户不是管理员，添加海关编码过滤
        if allowed_customs_codes is not None:
            aggs_query["query"] = {
                "terms": {"海关编码": allowed_customs_codes}
            }
        
        response = es_client.search(index=index_name, body=aggs_query)
        
        # 提取海关编码列表
        customs_codes = [bucket["key"] for bucket in response["aggregations"]["customs_codes"]["buckets"]]
        
        return customs_codes
    except Exception as e:
        logger.error(f"获取海关编码列表失败: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"获取海关编码列表失败: {str(e)}")

@router.get("/countries", response_model=Dict[str, List[str]], tags=["数据查询"])
@require_permissions([Permissions.DATA_VIEW])
@require_data_access()
async def get_all_countries(
    current_user: UserInDB = Depends(get_current_user),
    allowed_customs_codes: Optional[List[str]] = None
):
    """获取所有可用的进口国家和出口国家列表（需要数据查看权限，自动过滤海关编码）"""
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
        
        # 如果用户不是管理员，添加海关编码过滤
        if allowed_customs_codes is not None:
            aggs_query["query"] = {
                "terms": {"海关编码": allowed_customs_codes}
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