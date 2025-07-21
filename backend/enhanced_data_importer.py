import argparse
import asyncio
import os
from pathlib import Path
from app.utils.enhanced_data_processor import EnhancedDataProcessor
from app.services.import_task_service import ImportTaskService

async def main():
    parser = argparse.ArgumentParser(description='增强数据导入工具 - 支持多文件、多sheet、去重等功能')
    parser.add_argument('--files', nargs='+', help='Excel文件路径列表')
    parser.add_argument('--directory', help='包含Excel文件的目录路径')
    parser.add_argument('--batch-size', type=int, default=500, help='批量导入大小，默认500')
    parser.add_argument('--output-dir', default='./processed_data', help='预处理文件输出目录')
    parser.add_argument('--skip-duplicates', action='store_true', help='跳过重复数据')
    parser.add_argument('--dry-run', action='store_true', help='仅预处理，不导入到数据库')
    parser.add_argument('--reload-config', action='store_true', help='重新加载配置文件')
    
    args = parser.parse_args()
    
    # 重新加载配置（如果需要）
    if args.reload_config:
        from app.utils.config_manager import config_manager
        config_manager.reload_all_configs()
        print("配置文件已重新加载")
    
    # 确定要处理的文件列表
    files_to_process = []
    
    if args.files:
        files_to_process.extend(args.files)
    
    if args.directory:
        directory = Path(args.directory)
        if directory.exists() and directory.is_dir():
            excel_files = list(directory.glob('*.xlsx')) + list(directory.glob('*.xls'))
            files_to_process.extend([str(f) for f in excel_files])
        else:
            print(f"错误：目录 {args.directory} 不存在")
            return
    
    if not files_to_process:
        print("错误：没有指定要处理的文件")
        parser.print_help()
        return
    
    print(f"准备处理 {len(files_to_process)} 个文件:")
    for file_path in files_to_process:
        print(f"  - {file_path}")
    
    # 创建输出目录
    output_dir = Path(args.output_dir)
    output_dir.mkdir(exist_ok=True)
    
    # 初始化处理器和服务
    processor = EnhancedDataProcessor(output_dir=str(output_dir))
    task_service = ImportTaskService()
    
    try:
        # 创建导入任务
        task_id = await task_service.create_task(
            original_filename=f"batch_import_{len(files_to_process)}_files",
            user_id="system",
            total_files=len(files_to_process)
        )
        
        print(f"创建导入任务: {task_id}")
        
        total_success = 0
        total_failed = 0
        processed_files = []
        
        for file_path in files_to_process:
            print(f"\n处理文件: {file_path}")
            
            try:
                # 预处理文件
                result = await processor.process_excel_file(
                    file_path=file_path,
                    skip_duplicates=args.skip_duplicates
                )
                
                print(f"预处理完成:")
                print(f"  - 处理了 {len(result['processed_sheets'])} 个sheet")
                print(f"  - 总记录数: {result['total_records']}")
                print(f"  - 去重后记录数: {result['deduplicated_records']}")
                print(f"  - 生成文件: {len(result['output_files'])}")
                
                if not args.dry_run:
                    # 导入到数据库
                    for output_file in result['output_files']:
                        print(f"导入文件: {output_file['filename']}")
                        
                        import_result = await processor.import_to_database(
                            file_path=output_file['filepath'],
                            batch_size=args.batch_size
                        )
                        
                        total_success += import_result['success_count']
                        total_failed += import_result['failed_count']
                        
                        print(f"  导入结果: 成功 {import_result['success_count']}, 失败 {import_result['failed_count']}")
                
                processed_files.append({
                    'filename': os.path.basename(file_path),
                    'success_count': result['deduplicated_records'],
                    'failed_count': 0,
                    'output_files': result['output_files']
                })
                
            except Exception as e:
                print(f"处理文件失败: {str(e)}")
                processed_files.append({
                    'filename': os.path.basename(file_path),
                    'success_count': 0,
                    'failed_count': 1,
                    'error': str(e)
                })
        
        # 更新任务状态
        await task_service.update_task(
            task_id=task_id,
            status='completed' if total_failed == 0 else 'failed',
            success_count=total_success,
            failed_count=total_failed,
            processed_files=processed_files
        )
        
        print(f"\n批量导入完成:")
        print(f"  - 任务ID: {task_id}")
        print(f"  - 处理文件数: {len(files_to_process)}")
        print(f"  - 成功记录数: {total_success}")
        print(f"  - 失败记录数: {total_failed}")
        print(f"  - 预处理文件保存在: {output_dir}")
        
    except Exception as e:
        print(f"批量导入失败: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())