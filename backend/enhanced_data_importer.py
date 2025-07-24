import argparse
import asyncio
import os
import json
from pathlib import Path
from datetime import datetime
from app.utils.enhanced_data_processor import EnhancedDataProcessor
from app.services.import_task_service import ImportTaskService

def print_separator(title: str = ""):
    """打印分隔线"""
    if title:
        print(f"\n{'='*60}")
        print(f" {title}")
        print(f"{'='*60}")
    else:
        print(f"{'='*60}")

def print_step(step_num: int, title: str):
    """打印步骤标题"""
    print(f"\n[步骤 {step_num}] {title}")
    print("-" * 40)

def print_result_summary(result: dict, step_name: str):
    """打印结果摘要"""
    print(f"\n{step_name} 结果摘要:")
    if result.get('success', True):
        print(f"  ✓ 状态: 成功")
        print(f"  ✓ 原始文件: {result.get('original_filename', 'N/A')}")
        print(f"  ✓ Sheet数量: {result.get('sheet_count', 0)}")
        print(f"  ✓ 总记录数: {result.get('total_records', 0)}")
        print(f"  ✓ 处理后记录数: {result.get('processed_records', 0)}")
        print(f"  ✓ 去重移除: {result.get('duplicate_removed', 0)}")
        print(f"  ✓ 输出文件数: {len(result.get('output_files', []))}")
        
        # 显示输出文件详情
        for i, output_file in enumerate(result.get('output_files', []), 1):
            print(f"    文件{i}: {output_file.get('filename', 'N/A')} ({output_file.get('record_count', 0)} 条记录)")
    else:
        print(f"  ✗ 状态: 失败")
        print(f"  ✗ 错误: {result.get('error', 'Unknown error')}")

def print_import_result(result: dict):
    """打印导入结果"""
    print(f"\n数据库导入结果:")
    print(f"  ✓ 成功导入: {result.get('success_count', 0)} 条")
    print(f"  ✗ 导入失败: {result.get('failed_count', 0)} 条")
    print(f"  ⚠ 重复跳过: {result.get('duplicate_count', 0)} 条")
    print(f"  📊 总计处理: {result.get('total_count', 0)} 条")
    
    # 显示错误详情
    errors = result.get('errors', [])
    if errors:
        print(f"\n错误详情 (前5条):")
        for i, error in enumerate(errors[:5], 1):
            print(f"    {i}. {error.get('error_type', 'Unknown')}: {error.get('error_reason', 'No reason')}")
    
    # 显示重复记录样例
    duplicate_records = result.get('duplicate_records', [])
    if duplicate_records:
        print(f"\n重复记录样例 (前3条):")
        for i, record in enumerate(duplicate_records[:3], 1):
            customs_code = record.get('海关编码', 'N/A')
            date = record.get('日期', 'N/A')
            importer = record.get('进口商', 'N/A')
            print(f"    {i}. 海关编码: {customs_code}, 日期: {date}, 进口商: {importer}")

def save_detailed_report(results: list, output_dir: Path):
    """保存详细报告"""
    report = {
        'timestamp': datetime.now().isoformat(),
        'summary': {
            'total_files': len(results),
            'successful_files': len([r for r in results if r.get('success', False)]),
            'failed_files': len([r for r in results if not r.get('success', False)]),
            'total_records_processed': sum(r.get('processed_records', 0) for r in results),
            'total_records_imported': sum(r.get('import_result', {}).get('success_count', 0) for r in results),
            'total_duplicates_skipped': sum(r.get('import_result', {}).get('duplicate_count', 0) for r in results),
        },
        'detailed_results': results
    }
    
    report_file = output_dir / f"import_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(report_file, 'w', encoding='utf-8') as f:
        json.dump(report, f, ensure_ascii=False, indent=2)
    
    print(f"\n📋 详细报告已保存: {report_file}")
    return str(report_file)

async def process_single_file(processor: EnhancedDataProcessor, file_path: str, args, file_index: int, total_files: int):
    """处理单个文件"""
    print_separator(f"处理文件 {file_index}/{total_files}: {os.path.basename(file_path)}")
    
    result = {
        'file_path': file_path,
        'filename': os.path.basename(file_path),
        'success': False,
        'processing_steps': []
    }
    
    try:
        # 步骤1: 预处理文件
        print_step(1, "Excel文件预处理")
        print(f"文件路径: {file_path}")
        print(f"跳过重复: {args.skip_duplicates}")
        
        process_result = processor.process_excel_file(
            file_path=file_path,
            skip_duplicates=args.skip_duplicates
        )
        
        result['process_result'] = process_result
        result['processing_steps'].append('预处理完成')
        
        print_result_summary(process_result, "预处理")
        
        if not process_result.get('success', False):
            result['error'] = process_result.get('error', 'Unknown processing error')
            return result
        
        result['success'] = True
        result['processed_records'] = process_result.get('processed_records', 0)
        result['output_files'] = process_result.get('output_files', [])
        
        # 步骤2: 数据库导入（如果不是dry-run）
        if not args.dry_run and result['output_files']:
            print_step(2, "数据库导入")
            
            total_success = 0
            total_failed = 0
            total_duplicates = 0
            all_import_results = []
            
            for i, output_file in enumerate(result['output_files'], 1):
                print(f"\n导入文件 {i}/{len(result['output_files'])}: {output_file['filename']}")
                print(f"文件路径: {output_file['filepath']}")
                print(f"记录数量: {output_file['record_count']}")
                
                import_result = await processor.import_to_database(
                    file_path=output_file['filepath'],
                    batch_size=args.batch_size,
                    check_duplicates=True,
                    use_id_dedup=True
                )
                
                all_import_results.append(import_result)
                total_success += import_result.get('success_count', 0)
                total_failed += import_result.get('failed_count', 0)
                total_duplicates += import_result.get('duplicate_count', 0)
                
                print_import_result(import_result)
            
            # 汇总导入结果
            result['import_result'] = {
                'success_count': total_success,
                'failed_count': total_failed,
                'duplicate_count': total_duplicates,
                'total_count': sum(r.get('total_count', 0) for r in all_import_results),
                'detailed_results': all_import_results
            }
            
            result['processing_steps'].append('数据库导入完成')
            
            print(f"\n文件 {os.path.basename(file_path)} 导入汇总:")
            print(f"  ✓ 成功导入: {total_success} 条")
            print(f"  ✗ 导入失败: {total_failed} 条")
            print(f"  ⚠ 重复跳过: {total_duplicates} 条")
        
        elif args.dry_run:
            print_step(2, "跳过数据库导入 (Dry Run 模式)")
            result['processing_steps'].append('跳过数据库导入(dry-run)')
        
        return result
        
    except Exception as e:
        result['error'] = str(e)
        result['processing_steps'].append(f'处理失败: {str(e)}')
        print(f"\n❌ 处理文件失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return result

async def main():
    parser = argparse.ArgumentParser(description='增强数据导入工具 - 支持多文件、多sheet、去重等功能')
    parser.add_argument('--files', nargs='+', help='Excel文件路径列表')
    parser.add_argument('--directory', help='包含Excel文件的目录路径')
    parser.add_argument('--batch-size', type=int, default=500, help='批量导入大小，默认500')
    parser.add_argument('--output-dir', default='./processed_data', help='预处理文件输出目录')
    parser.add_argument('--skip-duplicates', action='store_true', help='跳过重复数据')
    parser.add_argument('--dry-run', action='store_true', help='仅预处理，不导入到数据库')
    parser.add_argument('--reload-config', action='store_true', help='重新加载配置文件')
    parser.add_argument('--verbose', action='store_true', help='显示详细日志')
    parser.add_argument('--save-report', action='store_true', help='保存详细报告到JSON文件')
    
    args = parser.parse_args()
    
    print_separator("增强数据导入工具")
    print(f"启动时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Dry Run 模式: {'是' if args.dry_run else '否'}")
    print(f"跳过重复数据: {'是' if args.skip_duplicates else '否'}")
    print(f"批量大小: {args.batch_size}")
    print(f"输出目录: {args.output_dir}")
    
    # 重新加载配置（如果需要）
    if args.reload_config:
        print_step(0, "重新加载配置文件")
        from app.utils.config_manager import config_manager
        config_manager.reload_all_configs()
        print("✓ 配置文件已重新加载")
    
    # 确定要处理的文件列表
    files_to_process = []
    
    if args.files:
        files_to_process.extend(args.files)
    
    if args.directory:
        directory = Path(args.directory)
        if directory.exists() and directory.is_dir():
            excel_files = list(directory.glob('*.xlsx')) + list(directory.glob('*.xls'))
            files_to_process.extend([str(f) for f in excel_files])
            print(f"✓ 从目录 {args.directory} 发现 {len(excel_files)} 个Excel文件")
        else:
            print(f"❌ 错误：目录 {args.directory} 不存在")
            return
    
    if not files_to_process:
        print("❌ 错误：没有指定要处理的文件")
        parser.print_help()
        return
    
    print(f"\n📁 准备处理 {len(files_to_process)} 个文件:")
    for i, file_path in enumerate(files_to_process, 1):
        file_size = os.path.getsize(file_path) / (1024 * 1024)  # MB
        print(f"  {i}. {os.path.basename(file_path)} ({file_size:.2f} MB)")
    
    # 创建输出目录
    output_dir = Path(args.output_dir)
    output_dir.mkdir(exist_ok=True)
    print(f"✓ 输出目录已创建: {output_dir}")
    
    # 初始化处理器
    processor = EnhancedDataProcessor(output_dir=str(output_dir))
    
    # 处理所有文件
    all_results = []
    start_time = datetime.now()
    
    for i, file_path in enumerate(files_to_process, 1):
        file_result = await process_single_file(processor, file_path, args, i, len(files_to_process))
        all_results.append(file_result)
    
    # 生成最终报告
    end_time = datetime.now()
    duration = end_time - start_time
    
    print_separator("处理完成 - 最终报告")
    
    successful_files = [r for r in all_results if r.get('success', False)]
    failed_files = [r for r in all_results if not r.get('success', False)]
    
    total_processed = sum(r.get('processed_records', 0) for r in successful_files)
    total_imported = sum(r.get('import_result', {}).get('success_count', 0) for r in successful_files)
    total_duplicates = sum(r.get('import_result', {}).get('duplicate_count', 0) for r in successful_files)
    total_failed_imports = sum(r.get('import_result', {}).get('failed_count', 0) for r in successful_files)
    
    print(f"📊 处理统计:")
    print(f"  ⏱ 总耗时: {duration}")
    print(f"  📁 处理文件: {len(files_to_process)} 个")
    print(f"  ✓ 成功文件: {len(successful_files)} 个")
    print(f"  ✗ 失败文件: {len(failed_files)} 个")
    print(f"  📝 处理记录: {total_processed} 条")
    
    if not args.dry_run:
        print(f"  💾 导入成功: {total_imported} 条")
        print(f"  ❌ 导入失败: {total_failed_imports} 条")
        print(f"  ⚠ 重复跳过: {total_duplicates} 条")
    
    # 显示失败文件详情
    if failed_files:
        print(f"\n❌ 失败文件详情:")
        for i, failed_file in enumerate(failed_files, 1):
            print(f"  {i}. {failed_file['filename']}: {failed_file.get('error', 'Unknown error')}")
    
    # 显示输出文件位置
    if successful_files:
        print(f"\n📂 预处理文件位置:")
        for result in successful_files:
            for output_file in result.get('output_files', []):
                print(f"  - {output_file['filepath']}")
    
    # 保存详细报告
    if args.save_report:
        report_file = save_detailed_report(all_results, output_dir)
    
    print_separator()
    print("🎉 处理完成！")

if __name__ == "__main__":
    asyncio.run(main())