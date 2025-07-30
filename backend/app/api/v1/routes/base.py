from fastapi import APIRouter

api_router = APIRouter()

# 后续将导入并包含各个功能模块的路由
from . import auth, data, user, import_data, ai, group, enhanced_import, config, role, rollback
api_router.include_router(auth.router, prefix="/auth", tags=["认证管理"])
api_router.include_router(data.router, prefix="/data", tags=["数据管理"])
api_router.include_router(user.router, prefix="/user", tags=["用户管理"])
api_router.include_router(group.router, prefix="/group", tags=["用户组管理"])
api_router.include_router(role.router, prefix="/role", tags=["角色管理"])
# api_router.include_router(import_data.router, prefix="/import", tags=["数据导入"])
api_router.include_router(enhanced_import.router, prefix="/enhanced-import", tags=["数据导入"])
api_router.include_router(config.router, prefix="/config", tags=["配置管理"])
api_router.include_router(ai.router, prefix="/ai", tags=["AI接口"])
api_router.include_router(rollback.router, prefix="/rollback", tags=["数据回滚"])
