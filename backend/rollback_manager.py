#!/usr/bin/env python3
"""
数据导入回滚管理脚本
用于命令行操作回滚功能
"""

import asyncio
import argparse
import sys
import os
from pathlib import Path

# 添加项目根目录到Python路径
sys.path.insert(0, str(Path(__file__).parent))

from app.services.rollback_service import RollbackService
from app.services.import_task_service import ImportTaskService
import json

async def preview_rollback(task_id: str):
    """预览回滚操作"""
    rollback_service = RollbackService()
    result = await rollback_service.preview_rollback(task_id)
    
    if result['success']:
        preview = result['preview']
        print(f"\n=== 回滚预览 ===")
        print(f"任务ID: {preview['task_info']['task_id']}")
        print(f"原始文件: {preview['task_info']['original_filename']}")
        print(f"导入用户: {preview['task_info']['user_id']}")
        print(f"导入时间: {preview['task_info']['created_at']}")
        print(f"\n=== 回滚统计 ===")
        print(f"总导入文档: {preview['rollback_summary']['total_imported_docs']}")
        print(f"现存文档: {preview['rollback_summary']['existing_docs']}")
        print(f"将被删除: {preview['rollback_summary']['will_be_deleted']}")
        print(f"已缺失文档: {preview['rollback_summary']['missing_docs']}")
        
        if preview['sample_data']:
            print(f"\n=== 数据样本 ===")
            for i, doc in enumerate(preview['sample_data'][:3]):
                print(f"{i+1}. ID: {doc['id']}")
                source = doc['source']
                print(f"   海关编码: {source.get('海关编码', 'N/A')}")
                print(f"   产品名称: {source.get('详细产品名称', 'N/A')}")
                print()
    else:
        print(f"预览失败: {result['error']}")

async def execute_rollback(task_id: str, dry_run: bool = False):
    """执行回滚操作"""
    rollback_service = RollbackService()
    
    if not dry_run:
        confirm = input(f"确认要回滚任务 {task_id} 吗？这将永久删除导入的数据！(yes/no): ")
        if confirm.lower() != 'yes':
            print("回滚操作已取消")
            return
    
    result = await rollback_service.execute_rollback(
        task_id=task_id,
        user_id='admin',  # 脚本执行使用admin用户
        dry_run=dry_run
    )
    
    if result['success']:
        rollback_result = result['rollback_result']
        print(f"\n=== 回滚结果 ===")
        print(f"删除文档数: {rollback_result['deleted_count']}")
        print(f"失败文档数: {rollback_result['failed_count']}")
        print(f"总文档数: {rollback_result['total_documents']}")
        print(f"预演模式: {rollback_result['dry_run']}")
        
        if rollback_result['errors']:
            print(f"\n=== 错误信息 ===")
            for error in rollback_result['errors'][:5]:
                print(f"- {error}")
    else:
        print(f"回滚失败: {result['error']}")

async def list_rollback_history():
    """列出回滚历史"""
    rollback_service = RollbackService()
    result = await rollback_service.get_rollback_history(page_size=50)
    
    if result['data']:
        print(f"\n=== 回滚历史 ({result['total']} 条记录) ===")
        for task in result['data']:
            print(f"任务ID: {task['task_id']}")
            print(f"文件名: {task.get('original_filename', 'N/A')}")
            print(f"回滚状态: {task.get('rollback_status', 'none')}")
            print(f"回滚时间: {task.get('rollback_at', 'N/A')}")
            print(f"回滚用户: {task.get('rollback_by', 'N/A')}")
            print("-" * 50)
    else:
        print("没有回滚历史记录")

async def list_completed_tasks():
    """列出可回滚的已完成任务"""
    task_service = ImportTaskService()
    result = await task_service.get_tasks(status='completed', page_size=50)
    
    if result['data']:
        print(f"\n=== 已完成的导入任务 ({result['total']} 条记录) ===")
        for task in result['data']:
            rollback_status = task.get('rollback_status', 'none')
            can_rollback = rollback_status not in ['completed']
            
            print(f"任务ID: {task['task_id']}")
            print(f"文件名: {task.get('original_filename', 'N/A')}")
            print(f"导入用户: {task.get('user_id', 'N/A')}")
            print(f"成功记录: {task.get('success_count', 0)}")
            print(f"回滚状态: {rollback_status}")
            print(f"可回滚: {'是' if can_rollback else '否'}")
            print("-" * 50)
    else:
        print("没有已完成的导入任务")

async def main():
    parser = argparse.ArgumentParser(description='数据导入回滚管理工具')
    parser.add_argument('action', choices=['preview', 'rollback', 'dry-run', 'history', 'list-tasks'], 
                       help='操作类型')
    parser.add_argument('--task-id', help='任务ID')
    
    args = parser.parse_args()
    
    if args.action == 'preview':
        if not args.task_id:
            print("预览操作需要提供 --task-id 参数")
            return
        await preview_rollback(args.task_id)
    
    elif args.action == 'rollback':
        if not args.task_id:
            print("回滚操作需要提供 --task-id 参数")
            return
        await execute_rollback(args.task_id, dry_run=False)
    
    elif args.action == 'dry-run':
        if not args.task_id:
            print("预演操作需要提供 --task-id 参数")
            return
        await execute_rollback(args.task_id, dry_run=True)
    
    elif args.action == 'history':
        await list_rollback_history()
    
    elif args.action == 'list-tasks':
        await list_completed_tasks()

if __name__ == "__main__":
    asyncio.run(main())