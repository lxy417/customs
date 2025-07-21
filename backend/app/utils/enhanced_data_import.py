import os
import tempfile
import shutil
from typing import List, Dict, Any, Optional
import logging
from datetime import datetime
import pandas as pd
from app.utils.data_import import DataImportService
from app.utils.data_preprocessor import DataPreprocessor
from app.services.import_history_service import ImportHistoryService, ImportHistoryCreate, ImportHistoryUpdate, ImportStatus
from app.config.settings import settings

logger = logging.getLogger(__name__)

class EnhancedDataImportService:
    """增强的数据导入服务 - 支持预处理、批量导入、历史记录"""
    
    def __init__(self):
        self.data_import_service = DataImportService()
        self.preprocessor = DataPreprocessor()
        self.history_service = ImportHistoryService()
        
        # 创建预处理文件存储目录
        self.processed_files_dir = os.path.join(settings.BASE_DIR, "processed_files")
        if not os.path.exists(self.processed_files_dir):
            os.makedirs(self.processed_files_dir)
    
    def process_and_import_file(self, file_path: str, original_filename: str, 
                               user_id: str, batch_size: int = 500) -> Dict[str, Any]:
        """处理并导入单个文件"""
        import_id = None
        
        try:
            # 获取文件信息
            file_size = os.path.getsize(file_path)
            
            # 创建导入记录
            import_record = ImportHistoryCreate(
                filename=os.path.basename(file_path),
                original_filename=original_filename,
                file_size=file_size,
                user_id=user_id,
                status=ImportStatus.PROCESSING
            )
            
            import_id = self.history_service.create_import_record(import_record)
            
            # 数据预处理
            logger.info(f"开始预处理文件: {file_path}")
            preprocess_result = self.preprocessor.process_excel_file(file_path, self.processed_files_dir)
            
            # 更新导入记录 - 预处理完成
            update_data = ImportHistoryUpdate(
                total_sheets=preprocess_result['total_sheets'],
                total_records=preprocess_result['total_original_records'],
                processed_records=preprocess_result['total_processed_records'],
                duplicates_removed=preprocess_result['total_duplicates_removed'],
                processing_details=preprocess_result
            )
            self.history_service.update_import_record(import_id, update_data)
            
            # 导入预处理后的文件到Elasticsearch
            total_imported = 0
            total_failed = 0
            import_errors = []
            customs_codes = set()
            date_range = {'start': None, 'end': None}
            
            for processed_file in preprocess_result['processed_files']:
                try:
                    logger.info(f"导入文件到Elasticsearch: {processed_file}")
                    
                    # 读取文件获取海关编码和日期范围
                    df = pd.read_excel(processed_file, engine='openpyxl')
                    
                    # 收集海关编码
                    if '海关编码' in df.columns:
                        codes = df['海关编码'].dropna().unique()
                        customs_codes.update([str(code) for code in codes])
                    
                    # 收集日期范围
                    if '日期' in df.columns:
                        dates = pd.to_datetime(df['日期'], errors='coerce').dropna()
                        if not dates.empty:
                            min_date = dates.min().strftime('%Y-%m-%d')
                            max_date = dates.max().strftime('%Y-%m-%d')
                            
                            if date_range['start'] is None or min_date < date_range['start']:
                                date_range['start'] = min_date
                            if date_range['end'] is None or max_date > date_range['end']:
                                date_range['end'] = max_date
                    
                    # 导入到Elasticsearch
                    success_count, errors = self.data_import_service.import_from_excel(
                        processed_file, batch_size
                    )
                    
                    total_imported += success_count
                    if errors:
                        total_failed += len(errors)
                        import_errors.extend(errors[:10])  # 只保留前10个错误
                    
                except Exception as e:
                    logger.error(f"导入文件失败: {processed_file}, 错误: {str(e)}")
                    import_errors.append(f"文件 {os.path.basename(processed_file)}: {str(e)}")
                    continue
            
            # 确定最终状态
            if total_failed == 0:
                final_status = ImportStatus.SUCCESS
            elif total_imported > 0:
                final_status = ImportStatus.PARTIAL
            else:
                final_status = ImportStatus.FAILED
            
            # 更新最终导入记录
            final_update = ImportHistoryUpdate(
                status=final_status,
                processed_records=total_imported,
                failed_records=total_failed,
                customs_codes=list(customs_codes),
                date_range_start=date_range['start'],
                date_range_end=date_range['end'],
                error_message='; '.join(import_errors[:5]) if import_errors else None,
                completed_at=datetime.now().isoformat()
            )
            self.history_service.update_import_record(import_id, final_update)
            
            # 清理临时文件
            try:
                for processed_file in preprocess_result['processed_files']:
                    if os.path.exists(processed_file):
                        os.remove(processed_file)
            except Exception as e:
                logger.warning(f"清理临时文件失败: {str(e)}")
            
            return {
                'import_id': import_id,
                'status': final_status.value,
                'total_sheets': preprocess_result['total_sheets'],
                'total_original_records': preprocess_result['total_original_records'],
                'total_processed_records': preprocess_result['total_processed_records'],
                'duplicates_removed': preprocess_result['total_duplicates_removed'],
                'imported_records': total_imported,
                'failed_records': total_failed,
                'customs_codes': list(customs_codes),
                'date_range': date_range,
                'errors': import_errors[:10],
                'preprocess_details': preprocess_result
            }
            
        except Exception as e:
            logger.error(f"处理文件失败: {str(e)}")
            
            # 更新导入记录为失败状态
            if import_id:
                error_update = ImportHistoryUpdate(
                    status=ImportStatus.FAILED,
                    error_message=str(e),
                    completed_at=datetime.now().isoformat()
                )
                self.history_service.update_import_record(import_id, error_update)
            
            raise
    
    def batch_process_and_import(self, file_paths: List[str], original_filenames: List[str],
                                user_id: str, batch_size: int = 500) -> Dict[str, Any]:
        """批量处理并导入多个文件"""
        batch_results = {
            'total_files': len(file_paths),
            'processed_files': 0,
            'failed_files': 0,
            'import_ids': [],
            'file_results': [],
            'summary': {
                'total_original_records': 0,
                'total_processed_records': 0,
                'total_imported_records': 0,
                'total_failed_records': 0,
                'total_duplicates_removed': 0,
                'all_customs_codes': set(),
                'date_range': {'start': None, 'end': None}
            }
        }
        
        for i, file_path in enumerate(file_paths):
            original_filename = original_filenames[i] if i < len(original_filenames) else os.path.basename(file_path)
            
            try:
                result = self.process_and_import_file(file_path, original_filename, user_id, batch_size)
                
                batch_results['file_results'].append(result)
                batch_results['import_ids'].append(result['import_id'])
                batch_results['processed_files'] += 1
                
                # 更新汇总信息
                summary = batch_results['summary']
                summary['total_original_records'] += result['total_original_records']
                summary['total_processed_records'] += result['total_processed_records']
                summary['total_imported_records'] += result['imported_records']
                summary['total_failed_records'] += result['failed_records']
                summary['total_duplicates_removed'] += result['duplicates_removed']
                summary['all_customs_codes'].update(result['customs_codes'])
                
                # 更新日期范围
                if result['date_range']['start']:
                    if summary['date_range']['start'] is None or result['date_range']['start'] < summary['date_range']['start']:
                        summary['date_range']['start'] = result['date_range']['start']
                if result['date_range']['end']:
                    if summary['date_range']['end'] is None or result['date_range']['end'] > summary['date_range']['end']:
                        summary['date_range']['end'] = result['date_range']['end']
                
            except Exception as e:
                logger.error(f"批量处理文件失败: {file_path}, 错误: {str(e)}")
                batch_results['failed_files'] += 1
                batch_results['file_results'].append({
                    'file_path': file_path,
                    'original_filename': original_filename,
                    'status': 'failed',
                    'error': str(e)
                })
        
        # 转换set为list
        batch_results['summary']['all_customs_codes'] = list(batch_results['summary']['all_customs_codes'])
        
        return batch_results
    
    def get_import_progress(self, import_id: str) -> Optional[Dict[str, Any]]:
        """获取导入进度"""
        return self.history_service.get_import_record(import_id)
    
    def get_import_history(self, user_id: Optional[str] = None, 
                          status: Optional[ImportStatus] = None,
                          page: int = 1, size: int = 20) -> Dict[str, Any]:
        """获取导入历史"""
        return self.history_service.get_import_history(user_id, status, page, size)
    
    def get_import_statistics(self, user_id: Optional[str] = None) -> Dict[str, Any]:
        """获取导入统计"""
        return self.history_service.get_import_statistics(user_id)