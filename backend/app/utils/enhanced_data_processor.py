import pandas as pd
import numpy as np
import os
import uuid
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
import hashlib
import re
from app.utils.elasticsearch import ESClient
from app.config.settings import settings
from app.utils.config_manager import config_manager
from elasticsearch.helpers import bulk, scan
from app.config.logging_config import get_logger
from app.services.data_service import DataService

# 使用专门的日志器
logger = get_logger('app.utils.enhanced_data_processor')

class EnhancedDataProcessor:
    def __init__(self, output_dir: str = "./processed_data"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        self.es_client = ESClient.get_client()
        self.index_name = settings.DATA_INDEX
        
        # 使用DataService来处理数据操作
        self.data_service = DataService()

    def _map_country_name(self, country_value: Any) -> str:
        """将英文国家名映射为中文国家名"""
        if not country_value or pd.isna(country_value):
            return ""
        
        country_str = str(country_value).strip()
        if not country_str:
            return ""
        
        # 使用config_manager的新方法查找中文名称
        try:
            chinese_name = config_manager.find_chinese_name(country_str)
            if chinese_name != country_str:
                logger.debug(f"国家映射: {country_str} -> {chinese_name}")
            else:
                logger.warning(f"未找到国家映射: {country_str}")
            return chinese_name
        except Exception as e:
            logger.error(f"国家映射处理失败: {str(e)}")
            return country_str

    def truncate_customs_code(self, code: str) -> str:
        """截断海关编码到前6位"""
        if not code or pd.isna(code):
            return ""
        
        code_str = str(code).strip()
        # 移除非数字字符
        code_str = re.sub(r'[^\d]', '', code_str)
        
        # 截断到前6位
        if len(code_str) >= 6:
            return code_str[:6]
        else:
            # 如果不足6位，用0补齐
            return code_str.ljust(6, '0')

    def _clean_customs_code(self, code: Any) -> str:
        """清理海关编码格式"""
        return self.data_service._clean_customs_code(code)

    def _is_valid_value(self, value: Any) -> bool:
        """检查值是否有效（非空、非NaN）"""
        return self.data_service._is_valid_value(value)

    def _generate_document_id(self, record: Dict[str, Any]) -> str:
        """为记录生成唯一的文档ID"""
        # 优先使用关单号或提单号
        bill_number = record.get('关单号') or record.get('提单号')
        if self._is_valid_value(bill_number):
            return f"bill_{bill_number}"
        
        # 使用组合字段生成哈希ID
        customs_code = self._clean_customs_code(record.get('海关编码'))
        date_value = record.get('日期')
        importer = record.get('进口商')
        exporter = record.get('出口商')
        tonnage = record.get('公吨')
        
        if customs_code and self._is_valid_value(date_value):
            # 构建组合字符串
            combo_parts = [customs_code, str(date_value)]
            if self._is_valid_value(importer):
                combo_parts.append(str(importer))
            if self._is_valid_value(exporter):
                combo_parts.append(str(exporter))
            if self._is_valid_value(tonnage):
                combo_parts.append(str(tonnage))
            
            combo_string = "_".join(combo_parts)
            # 生成MD5哈希
            hash_id = hashlib.md5(combo_string.encode('utf-8')).hexdigest()
            return f"combo_{hash_id}"
        
        # 如果都没有，生成随机ID
        return f"random_{uuid.uuid4().hex[:16]}"

    def find_data_start_row(self, df: pd.DataFrame) -> int:
        """找到数据开始的行"""
        for idx, row in df.iterrows():
            # 检查是否包含海关编码列的有效数据
            for col in df.columns:
                if '海关编码' in str(col) or 'HS' in str(col).upper():
                    value = row[col]
                    if pd.notna(value) and str(value).strip():
                        # 检查是否是数字（可能的海关编码）
                        cleaned_value = re.sub(r'[^\d]', '', str(value))
                        if len(cleaned_value) >= 4:  # 至少4位数字
                            return idx
        return 0

    def process_dataframe(self, df: pd.DataFrame, sheet_name: str = "") -> List[Dict[str, Any]]:
        """处理单个DataFrame"""
        required_columns = [
            "海关编码", "编码产品描述", "日期", "月度", "进口商", "进口商所在国家", 
            "出口商所在国家", "出口商", "重量单位", "数量单位", "数量", "毛重", 
            "净重", "公吨", "金额美元", "美元重量计单价", "美元数量计单价", 
            "本国币种金额", "合同金额", "币种", "成交方式", "详细产品名称", 
            "产品规格型号品牌", "当地港口", "国外港口", "运输方式", "贸易方式", 
            "中转国", "提单号", "编码产品描述本国语言", "详细产品名称本国语言", 
            "产品规格型号品牌本国语言", "进口商本地语言", "数据来源", 
            "出口商本地语言", "关单号", "申报数量"
        ]
        
        # 检查必需列
        missing_cols = [col for col in required_columns if col not in df.columns]
        if missing_cols:
            logger.warning(f"Sheet '{sheet_name}' 缺少列: {missing_cols}")
        
        # 找到数据开始行
        data_start_row = self.find_data_start_row(df)
        logger.info(f"Sheet '{sheet_name}' 数据从第 {data_start_row + 1} 行开始")
        
        processed_records = []
        
        for idx, row in df.iterrows():
            # 跳过表头行
            if idx < data_start_row:
                continue
            
            # 检查是否为空行或无效行
            customs_code = str(row.get('海关编码', '')).strip()
            if customs_code == '海关编码':
                logger.debug(f"跳过表头行: {idx + 1}")
                continue
            
            record = {}
            for col in df.columns:
                value = row[col]
                if pd.notna(value):
                    if col == '海关编码':
                        # 清理并截断海关编码到前6位，确保为字符串
                        cleaned_code = self._clean_customs_code(value)
                        if cleaned_code:
                            # 截断到前6位并确保为字符串格式
                            truncated_code = self.truncate_customs_code(cleaned_code)
                            record[col] = truncated_code
                            logger.debug(f"海关编码处理: {value} -> {cleaned_code} -> {truncated_code}")
                    elif col == '日期':
                        # 处理日期格式
                        if isinstance(value, datetime):
                            record[col] = value.strftime('%Y-%m-%d')
                        else:
                            try:
                                date_obj = pd.to_datetime(value)
                                record[col] = date_obj.strftime('%Y-%m-%d')
                            except:
                                record[col] = str(value)
                    elif col in ['进口商所在国家', '出口商所在国家']:
                        # 处理国家字段，进行英文到中文的映射
                        mapped_country = self._map_country_name(value)
                        record[col] = mapped_country
                        if str(value).strip() != mapped_country:
                            logger.debug(f"国家字段映射 {col}: {value} -> {mapped_country}")
                    else:
                        # 处理其他字段
                        record[col] = value
            
            # 只保留有海关编码的记录
            if record.get('海关编码'):
                processed_records.append(record)
                logger.debug(f"处理记录 {idx + 1}: {len(record)} 个字段")
        
        logger.info(f"Sheet '{sheet_name}' 处理完成，有效记录: {len(processed_records)} 条")
        return processed_records


    def process_excel_file(self, file_path: str, skip_duplicates: bool = True) -> Dict[str, Any]:
        """处理Excel文件，返回处理结果和输出文件信息"""
        logger.info(f"开始处理Excel文件: {file_path}")
        
        all_records = []
        total_records = 0
        output_files = []
        
        try:
            # 获取原始文件名
            original_filename = Path(file_path).name
            
            # 读取Excel文件的所有sheet
            excel_file = pd.ExcelFile(file_path, engine='openpyxl')
            sheet_names = excel_file.sheet_names
            logger.info(f"发现 {len(sheet_names)} 个sheet: {sheet_names}")
            
            for sheet_name in sheet_names:
                try:
                    logger.info(f"处理sheet: {sheet_name}")
                    
                    # 读取sheet数据
                    df = pd.read_excel(file_path, sheet_name=sheet_name, engine='openpyxl')
                    logger.info(f"Sheet '{sheet_name}' 包含 {len(df)} 行数据")
                    
                    # 处理数据
                    records = self.process_dataframe(df, sheet_name)
                    logger.info(f"Sheet '{sheet_name}' 处理后得到 {len(records)} 条记录")
                    
                    # 添加数据来源信息
                    # for record in records:
                    #     if '数据来源' not in record or not record['数据来源']:
                    #         record['数据来源'] = f"{original_filename}#{sheet_name}"
                    
                    all_records.extend(records)
                    total_records += len(records)
                    
                except Exception as e:
                    logger.error(f"处理sheet '{sheet_name}' 失败: {str(e)}")
                    continue
            
            logger.info(f"所有sheet处理完成，共得到 {total_records} 条记录")
            
            # 去重处理
            if skip_duplicates:
                deduplicated_records = self.deduplicate_records(all_records)
                logger.info(f"去重完成: {total_records} -> {len(deduplicated_records)} 条记录")
                final_records = deduplicated_records
            else:
                final_records = all_records
            
            # 保存处理后的数据
            if final_records:
                # 生成输出文件名
                base_name = Path(original_filename).stem
                output_filename = f"processed_{base_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
                output_filepath = self.save_processed_data(final_records, output_filename)
                
                output_files.append({
                    'filename': output_filename,
                    'filepath': output_filepath,
                    'record_count': len(final_records),
                    'sheet_count': len(sheet_names)
                })
            
            return {
                'success': True,
                'original_filename': original_filename,
                'total_records': total_records,
                'processed_records': len(final_records),
                'duplicate_removed': total_records - len(final_records) if skip_duplicates else 0,
                'output_files': output_files,
                'sheet_count': len(sheet_names),
                'message': f"成功处理 {len(sheet_names)} 个sheet，共 {len(final_records)} 条有效记录"
            }
            
        except Exception as e:
            logger.error(f"处理Excel文件失败: {str(e)}")
            return {
                'success': False,
                'original_filename': Path(file_path).name,
                'total_records': 0,
                'processed_records': 0,
                'duplicate_removed': 0,
                'output_files': [],
                'sheet_count': 0,
                'error': str(e),
                'message': f"处理文件失败: {str(e)}"
            }

    def deduplicate_records(self, records: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """去重记录"""
        seen = set()
        unique_records = []
        
        for record in records:
            # 生成记录的唯一标识
            doc_id = self._generate_document_id(record)
            
            if doc_id not in seen:
                seen.add(doc_id)
                record['_es_id'] = doc_id  # 保存生成的ID
                unique_records.append(record)
        
        return unique_records

    def save_processed_data(self, records: List[Dict[str, Any]], filename: str) -> str:
        """保存处理后的数据"""
        output_filepath = self.output_dir / filename
        
        if records:
            df = pd.DataFrame(records)
            df.to_excel(output_filepath, index=False, engine='openpyxl')
            logger.info(f"保存处理后的数据: {output_filepath} ({len(records)} 条记录)")
        
        return str(output_filepath)

    def check_es_duplicates_by_id(self, records: List[Dict[str, Any]]) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
        """使用文档ID检查ES数据库中的重复数据（高效版本）"""
        logger.info(f"开始使用_id检查ES数据库中的重复数据，共 {len(records)} 条记录")
        
        unique_records = []
        duplicate_records = []
        
        # 为所有记录生成ID
        document_ids = []
        record_id_map = {}
        
        for record in records:
            doc_id = self._generate_document_id(record)
            record['_es_id'] = doc_id
            document_ids.append(doc_id)
            record_id_map[doc_id] = record
        
        try:
            # 使用DataService的批量检查方法
            check_result = self.data_service.check_duplicates_by_ids(document_ids)
            
            existing_ids = check_result.get('existing_ids', [])
            new_ids = check_result.get('new_ids', [])
            
            # 分类记录
            for doc_id in existing_ids:
                if doc_id in record_id_map:
                    duplicate_records.append(record_id_map[doc_id])
                    logger.debug(f"发现重复记录，ID: {doc_id}")
            
            for doc_id in new_ids:
                if doc_id in record_id_map:
                    unique_records.append(record_id_map[doc_id])
                    
        except Exception as e:
            logger.error(f"批量检查文档存在性失败: {str(e)}")
            # 如果检查失败，将所有记录视为唯一
            unique_records = records
            duplicate_records = []
        
        logger.info(f"ES _id重复检测完成: 唯一记录 {len(unique_records)}, 重复记录 {len(duplicate_records)}")
        return unique_records, duplicate_records

    async def import_to_database(
        self, 
        file_path: str, 
        batch_size: int = 500,
        check_duplicates: bool = True,
        use_id_dedup: bool = True
    ) -> Dict[str, Any]:
        """将处理后的数据导入到Elasticsearch"""
        try:
            df = pd.read_excel(file_path, engine='openpyxl')
            logger.info(f"准备导入 {len(df)} 条记录到数据库")
            
            # 转换为字典列表
            records = df.to_dict('records')
            
            # ES重复检测
            if check_duplicates and use_id_dedup:
                # 使用新的ID去重方法
                unique_records, duplicate_records = self.check_es_duplicates_by_id(records)
                logger.info(f"ES重复检测: 将导入 {len(unique_records)} 条唯一记录，跳过 {len(duplicate_records)} 条重复记录")
                records = unique_records
            else:
                duplicate_records = []
                # 即使不检查重复，也为记录生成ID
                if use_id_dedup:
                    for record in records:
                        record['_es_id'] = self._generate_document_id(record)
            
            # 使用DataService进行批量导入
            if records:
                result = self.data_service.bulk_create_customs_data(records, batch_size)
                
                return {
                    'success_count': result.get('success', 0),
                    'failed_count': result.get('failed', 0),
                    'duplicate_count': len(duplicate_records),
                    'total_count': len(df),
                    'errors': result.get('errors', []),
                    'failed_records': [],  # DataService已经处理了错误记录
                    'duplicate_records': duplicate_records[:5]  # 只返回前5条重复记录
                }
            else:
                return {
                    'success_count': 0,
                    'failed_count': 0,
                    'duplicate_count': len(duplicate_records),
                    'total_count': len(df),
                    'errors': [],
                    'failed_records': [],
                    'duplicate_records': duplicate_records[:5]
                }
            
        except Exception as e:
            logger.error(f"导入数据库失败: {str(e)}")
            return {
                'success_count': 0,
                'failed_count': 0,
                'duplicate_count': 0,
                'total_count': 0,
                'errors': [{'error_type': 'ImportError', 'error_reason': str(e)}],
                'failed_records': [],
                'duplicate_records': []
            }