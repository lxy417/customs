from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.v1.routes import api_router
from app.config.logging_config import setup_logging
import logging

# 设置日志配置
setup_logging()
logger = logging.getLogger('app')

app = FastAPI(title="海关数据管理系统API", version="1.0")

# 配置CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 在生产环境中应指定具体的前端域名
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 包含API路由
app.include_router(api_router, prefix="/api/v1")

@app.get("/")
def read_root():
    logger.info("访问根路径")
    return {"message": "欢迎使用海关数据管理系统API，请访问/api/v1获取接口文档"}

@app.on_event("startup")
async def startup_event():
    """应用启动事件"""
    logger.info("应用启动完成")

@app.on_event("shutdown")
async def shutdown_event():
    """应用关闭事件"""
    logger.info("应用正在关闭")
