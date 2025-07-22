@echo off
echo 启动海关数据管理系统...
echo.

REM 检查是否在虚拟环境中
if not defined VIRTUAL_ENV (
    echo 警告: 未检测到虚拟环境，建议使用虚拟环境运行
    echo.
)

REM 创建日志目录
if not exist "logs" mkdir logs

REM 启动应用
echo 启动FastAPI应用...
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload --log-level info

pause