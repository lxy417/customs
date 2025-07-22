@echo off
echo 清理日志文件...

if exist "logs" (
    echo 删除旧日志文件...
    del /q logs\*.log.* 2>nul
    echo 清空当前日志文件...
    type nul > logs\app.log 2>nul
    type nul > logs\error.log 2>nul
    type nul > logs\import.log 2>nul
    echo 日志清理完成
) else (
    echo 日志目录不存在
)

pause