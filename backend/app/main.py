from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from app.api.v1.routes import api_router
from app.config.logging_config import setup_logging
import logging
import time

# 设置日志配置
setup_logging()
logger = logging.getLogger('app')

app = FastAPI(title="海关数据管理系统API", version="1.0")

# 添加请求日志中间件
@app.middleware("http")
async def log_requests(request: Request, call_next):
    start_time = time.time()
    
    # 记录请求开始
    logger.info(f"🔵 {request.method} {request.url.path} - 开始处理请求")
    
    # 处理请求
    response = await call_next(request)
    
    # 计算处理时间
    process_time = time.time() - start_time
    
    # 记录请求完成
    status_emoji = "✅" if response.status_code < 400 else "❌"
    logger.info(f"{status_emoji} {request.method} {request.url.path} - 状态码: {response.status_code} - 耗时: {process_time:.3f}s")
    
    return response

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
    logger.info("🚀 海关数据管理系统API启动完成")

@app.on_event("shutdown")
async def shutdown_event():
    """应用关闭事件"""
    logger.info("🛑 海关数据管理系统API正在关闭")
