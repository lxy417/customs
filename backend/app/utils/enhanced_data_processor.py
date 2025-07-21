import pandas as pd
import numpy as np
import os
import uuid
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
import logging
import hashlib
import re
from app.utils.elasticsearch import ESClient
from app.config.settings import settings
from app.utils.config_manager import config_manager
from elasticsearch.helpers import bulk, scan

logger = logging.getLogger(__name__)

class EnhancedDataProcessor:
    def __init__(self, output_dir: str = "./processed_data"):
        self.es_client = ESClient.get_client()
        self.index_name = settings.DATA_INDEX
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        self.date_formats = ['%Y-%m-%d', '%Y/%m/%d', '%Y%m%d', '%Y年%m月%d日']
        
        # 定义表头关键词，用于识别和跳过表头行
        self.header_keywords = [
            '海关编码'
        ]

    def get_country_mapping(self) -> Dict[str, str]:
        """获取国家映射配置（支持热加载）"""
        return config_manager.get_country_mapping()

    def convert_country_name(self, country_name: str) -> str:
        """将英文国家名转换为中文"""
        if not country_name or pd.isna(country_name):
            return country_name
        
        country_str = str(country_name).strip()
        country_mapping = self.get_country_mapping()
        
        # 直接映射
        if country_str in country_mapping:
            return country_mapping[country_str]
        
        # 模糊匹配（提取括号内的国家代码）
        for eng_name, chn_name in country_mapping.items():
            if country_str.lower() in eng_name.lower() or eng_name.lower() in country_str.lower():
                return chn_name
        
        # 如果没有找到映射，返回原值
        return country_str

    def truncate_customs_code(self, code: str) -> str:
        """截取海关编码前6位"""
        if not code or pd.isna(code):
            return code
        
        code_str = str(code).strip()
        # 移除非数字字符，只保留数字
        digits_only = re.sub(r'\D', '', code_str)
        
        # 返回前6位
        return digits_only[:6] if len(digits_only) >= 6 else digits_only

    def parse_date(self, date_str) -> Optional[str]:
        """解析日期字符串"""
        if pd.isna(date_str):
            return None
        
        for fmt in self.date_formats:
            try:
                return datetime.strptime(str(date_str), fmt).strftime('%Y-%m-%d')
            except ValueError:
                continue
        
        # 如果所有格式都失败，尝试pandas的日期解析
        try:
            parsed_date = pd.to_datetime(str(date_str))
            return parsed_date.strftime('%Y-%m-%d')
        except:
            return str(date_str)

    def clean_numeric(self, value) -> Optional[float]:
        """清理数值数据"""
        if pd.isna(value) or value in ['', 'nan', 'NaN', 'None']:
            return None
        
        try:
            if isinstance(value, str):
                value = value.replace(',', '').replace(' ', '')
            return float(value)
        except (ValueError, TypeError):
            return None

    def is_header_row(self, row: pd.Series) -> bool:
        """判断是否为表头行"""
        # 将行转换为字符串列表
        row_values = [str(val).strip() for val in row.values if not pd.isna(val)]
        
        # 如果行中包含多个表头关键词，则认为是表头行
        keyword_count = 0
        for value in row_values:
            for keyword in self.header_keywords:
                if keyword in value:
                    keyword_count += 1
                    break
        
        # 如果包含3个或以上的表头关键词，认为是表头行
        return keyword_count >= 3

    def find_data_start_row(self, df: pd.DataFrame) -> int:
        """找到数据开始的行号"""
        for idx, (_, row) in enumerate(df.iterrows()):
            if not self.is_header_row(row):
                # 检查是否有有效的海关编码数据
                customs_code = str(row.get('海关编码', '')).strip()
                if customs_code and customs_code != '海关编码' and len(customs_code) > 0:
                    # 进一步验证：检查是否包含数字
                    if re.search(r'\d', customs_code):
                        return idx
        return 0

    def generate_record_hash(self, record: Dict[str, Any]) -> str:
        """生成记录的哈希值用于去重"""
        # 使用关键字段生成哈希
        key_fields = [
            str(record.get('关单号', '')),
            str(record.get('提单号', '')),
            str(record.get('海关编码', '')),
            str(record.get('日期', '')),
            str(record.get('进口商', '')),
            str(record.get('出口商', '')),
            str(record.get('公吨', ''))
        ]
        
        key_string = '|'.join(key_fields)
        return hashlib.md5(key_string.encode('utf-8')).hexdigest()

    def deduplicate_records(self, records: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """去重逻辑"""
        seen_hashes = set()
        seen_bill_numbers = set()
        deduplicated = []
        
        for record in records:
            # 第一层去重：根据关单号或提单号
            bill_number = record.get('关单号') or record.get('提单号')
            if bill_number and bill_number in seen_bill_numbers:
                continue
            
            # 第二层去重：根据关键字段组合
            record_hash = self.generate_record_hash(record)
            if record_hash in seen_hashes:
                continue
            
            # 记录已见过的标识
            if bill_number:
                seen_bill_numbers.add(bill_number)
            seen_hashes.add(record_hash)
            
            deduplicated.append(record)
        
        return deduplicated

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
        
        # 检查缺失列
        missing_cols = set(required_columns) - set(df.columns)
        if missing_cols:
            logger.warning(f"Sheet '{sheet_name}' 缺少列: {missing_cols}")
        
        # 找到数据开始的行
        data_start_row = self.find_data_start_row(df)
        logger.info(f"Sheet '{sheet_name}' 数据从第 {data_start_row + 1} 行开始")
        
        processed_records = []
        
        # 从数据开始行处理
        for idx, (_, row) in enumerate(df.iterrows()):
            if idx < data_start_row:
                continue
                
            # 跳过表头行
            if self.is_header_row(row):
                logger.debug(f"跳过表头行: {idx + 1}")
                continue
            
            # 检查是否为空行或无效行
            customs_code = str(row.get('海关编码', '')).strip()
            if not customs_code or customs_code in ['nan', 'NaN', 'None', '']:
                continue
            
            record = {}
            
            for col in required_columns:
                if col in row:
                    value = row[col]
                    
                    # 特殊处理不同类型的字段
                    if col == "海关编码":
                        record[col] = self.truncate_customs_code(value)
                    elif col == "日期":
                        record[col] = self.parse_date(value)
                    elif col in ["进口商所在国家", "出口商所在国家"]:
                        record[col] = self.convert_country_name(value)
                    elif col in ['数量', '毛重', '净重', '公吨', '金额美元', 
                               '美元重量计单价', '美元数量计单价', '本国币种金额', 
                               '合同金额', '申报数量']:
                        record[col] = self.clean_numeric(value)
                    else:
                        record[col] = str(value) if not pd.isna(value) else None
                else:
                    record[col] = None
            
            # 添加数据来源信息
            record['数据来源'] = sheet_name or '未知来源'
            
            processed_records.append(record)
        
        logger.info(f"Sheet '{sheet_name}' 处理完成，有效记录: {len(processed_records)} 条")
        return processed_records

    async def process_excel_file(
        self, 
        file_path: str, 
        skip_duplicates: bool = True
    ) -> Dict[str, Any]:
        """处理Excel文件的所有sheet"""
        file_path = Path(file_path)
        if not file_path.exists():
            raise FileNotFoundError(f"文件不存在: {file_path}")
        
        logger.info(f"开始处理Excel文件: {file_path}")
        
        # 读取所有sheet
        try:
            excel_file = pd.ExcelFile(file_path, engine='openpyxl')
            sheet_names = excel_file.sheet_names
        except Exception as e:
            raise Exception(f"无法读取Excel文件: {str(e)}")
        
        logger.info(f"发现 {len(sheet_names)} 个sheet: {sheet_names}")
        
        all_records = []
        processed_sheets = []
        output_files = []
        
        # 处理每个sheet
        for sheet_name in sheet_names:
            try:
                logger.info(f"处理sheet: {sheet_name}")
                
                df = pd.read_excel(file_path, sheet_name=sheet_name, engine='openpyxl')
                logger.info(f"Sheet '{sheet_name}' 包含 {len(df)} 行数据")
                
                # 处理数据
                records = self.process_dataframe(df, sheet_name)
                logger.info(f"Sheet '{sheet_name}' 处理后得到 {len(records)} 条记录")
                
                if records:
                    all_records.extend(records)
                    processed_sheets.append({
                        'sheet_name': sheet_name,
                        'original_rows': len(df),
                        'processed_records': len(records)
                    })
                
            except Exception as e:
                logger.error(f"处理sheet '{sheet_name}' 失败: {str(e)}")
                processed_sheets.append({
                    'sheet_name': sheet_name,
                    'error': str(e)
                })
        
        total_records = len(all_records)
        logger.info(f"所有sheet处理完成，共得到 {total_records} 条记录")
        
        # 去重处理
        if skip_duplicates and all_records:
            deduplicated_records = self.deduplicate_records(all_records)
            logger.info(f"去重完成: {total_records} -> {len(deduplicated_records)} 条记录")
        else:
            deduplicated_records = all_records
        
        # 按sheet分组保存处理后的数据
        if deduplicated_records:
            # 生成输出文件名
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            random_suffix = str(uuid.uuid4())[:8]
            base_filename = file_path.stem
            
            # 按sheet分组数据
            sheet_groups = {}
            for record in deduplicated_records:
                sheet_name = record.get('数据来源', 'unknown')
                if sheet_name not in sheet_groups:
                    sheet_groups[sheet_name] = []
                sheet_groups[sheet_name].append(record)
            
            # 为每个sheet创建单独的文件
            for sheet_name, records in sheet_groups.items():
                output_filename = f"{base_filename}-{sheet_name}-{timestamp}-{random_suffix}.xlsx"
                output_filepath = self.output_dir / output_filename
                
                # 转换为DataFrame并保存
                output_df = pd.DataFrame(records)
                output_df.to_excel(output_filepath, index=False, engine='openpyxl')
                
                output_files.append({
                    'filename': output_filename,
                    'filepath': str(output_filepath),
                    'sheet_name': sheet_name,
                    'record_count': len(records)
                })
                
                logger.info(f"保存处理后的数据: {output_filepath} ({len(records)} 条记录)")
        
        return {
            'original_file': str(file_path),
            'processed_sheets': processed_sheets,
            'total_records': total_records,
            'deduplicated_records': len(deduplicated_records),
            'output_files': output_files
        }

    def check_es_duplicates(self, records: List[Dict[str, Any]]) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
        """检查ES数据库中的重复数据"""
        if not records:
            return [], []
        
        logger.info(f"开始检查ES数据库中的重复数据，共 {len(records)} 条记录")
        
        unique_records = []
        duplicate_records = []
        
        # 批量检查重复数据
        batch_size = 100
        for i in range(0, len(records), batch_size):
            batch_records = records[i:i + batch_size]
            
            # 构建查询条件
            should_queries = []
            for record in batch_records:
                # 使用多个字段组合查询重复数据
                record_queries = []
                
                # 关单号或提单号
                bill_number = record.get('关单号') or record.get('提单号')
                if bill_number:
                    record_queries.append({
                        "bool": {
                            "should": [
                                {"term": {"关单号.keyword": bill_number}},
                                {"term": {"提单号.keyword": bill_number}}
                            ],
                            "minimum_should_match": 1
                        }
                    })
                
                # 海关编码 + 日期 + 进口商/出口商
                customs_code = record.get('海关编码')
                date_value = record.get('日期')
                importer = record.get('进口商')
                exporter = record.get('出口商')
                
                if customs_code and date_value and (importer or exporter):
                    date_conditions = [
                        {"term": {"海关编码.keyword": customs_code}},
                        {"term": {"日期": date_value}}
                    ]
                    
                    if importer:
                        date_conditions.append({"term": {"进口商.keyword": importer}})
                    if exporter:
                        date_conditions.append({"term": {"出口商.keyword": exporter}})
                    
                    record_queries.append({
                        "bool": {
                            "must": date_conditions
                        }
                    })
                
                # 只有当有有效查询条件时才添加到should_queries
                if record_queries:
                    should_queries.append({
                        "bool": {
                            "should": record_queries,
                            "minimum_should_match": 1
                        }
                    })
            
            # 只有当有查询条件时才执行查询
            if should_queries:
                # 执行查询
                query = {
                    "query": {
                        "bool": {
                            "should": should_queries,
                            "minimum_should_match": 1
                        }
                    },
                    "_source": ["关单号", "提单号", "海关编码", "日期", "进口商", "出口商"]
                }
                
                try:
                    # 使用scan获取所有匹配的文档
                    existing_docs = list(scan(
                        self.es_client,
                        query=query,
                        index=self.index_name,
                        size=1000
                    ))
                    
                    # 创建已存在数据的标识集合
                    existing_identifiers = set()
                    for doc in existing_docs:
                        source = doc['_source']
                        
                        # 关单号/提单号标识
                        bill_number = source.get('关单号') or source.get('提单号')
                        if bill_number:
                            existing_identifiers.add(f"bill_{bill_number}")
                        
                        # 组合字段标识
                        customs_code = source.get('海关编码')
                        date_value = source.get('日期')
                        importer = source.get('进口商')
                        exporter = source.get('出口商')
                        
                        if customs_code and date_value:
                            if importer:
                                existing_identifiers.add(f"combo_{customs_code}_{date_value}_{importer}")
                            if exporter:
                                existing_identifiers.add(f"combo_{customs_code}_{date_value}_{exporter}")
                    
                    # 检查当前批次的记录是否重复
                    for record in batch_records:
                        is_duplicate = False
                        
                        # 检查关单号/提单号
                        bill_number = record.get('关单号') or record.get('提单号')
                        if bill_number and f"bill_{bill_number}" in existing_identifiers:
                            is_duplicate = True
                        
                        # 检查组合字段
                        if not is_duplicate:
                            customs_code = record.get('海关编码')
                            date_value = record.get('日期')
                            importer = record.get('进口商')
                            exporter = record.get('出口商')
                            
                            if customs_code and date_value:
                                if importer and f"combo_{customs_code}_{date_value}_{importer}" in existing_identifiers:
                                    is_duplicate = True
                                elif exporter and f"combo_{customs_code}_{date_value}_{exporter}" in existing_identifiers:
                                    is_duplicate = True
                        
                        if is_duplicate:
                            duplicate_records.append(record)
                        else:
                            unique_records.append(record)
                
                except Exception as e:
                    logger.error(f"查询ES数据库失败: {str(e)}")
                    # 如果查询失败，将所有记录视为唯一
                    unique_records.extend(batch_records)
            else:
                # 如果没有查询条件，将所有记录视为唯一
                unique_records.extend(batch_records)
        
        logger.info(f"ES重复检测完成: 唯一记录 {len(unique_records)}, 重复记录 {len(duplicate_records)}")
        return unique_records, duplicate_records

    async def import_to_database(
        self, 
        file_path: str, 
        batch_size: int = 500,
        check_duplicates: bool = True
    ) -> Dict[str, Any]:
        """将处理后的数据导入到Elasticsearch"""
        try:
            df = pd.read_excel(file_path, engine='openpyxl')
            logger.info(f"准备导入 {len(df)} 条记录到数据库")
            
            # 转换为字典列表
            records = df.to_dict('records')
            
            # ES重复检测
            if check_duplicates:
                unique_records, duplicate_records = self.check_es_duplicates(records)
                logger.info(f"ES重复检测: 将导入 {len(unique_records)} 条唯一记录，跳过 {len(duplicate_records)} 条重复记录")
                records = unique_records
            else:
                duplicate_records = []
            
            # 构建批量导入的actions
            actions = []
            for record in records:
                # 清理None值
                cleaned_record = {k: v for k, v in record.items() if pd.notna(v)}
                
                actions.append({
                    '_op_type': 'index',
                    '_index': self.index_name,
                    '_source': cleaned_record
                })
            
            # 批量导入
            success_count = 0
            failed_count = 0
            errors = []
            failed_records = []
            
            if actions:
                try:
                    success, failed = bulk(
                        self.es_client,
                        actions,
                        chunk_size=batch_size,
                        raise_on_error=False,
                        stats_only=False
                    )
                    success_count = success
                    failed_count = len(failed) if failed else 0
                    
                    if failed:
                        errors = []
                        failed_records = []
                        for error_item in failed[:10]:  # 只记录前10个错误
                            error_info = error_item.get('index', {})
                            error_detail = error_info.get('error', {})
                            errors.append({
                                'error_type': error_detail.get('type', 'unknown'),
                                'error_reason': error_detail.get('reason', 'unknown'),
                                'document_id': error_info.get('_id', 'unknown')
                            })
                            
                            # 记录失败的记录详情
                            if 'data' in error_info:
                                failed_records.append(error_info['data'])
                    
                    logger.info(f"导入完成: 成功 {success_count}, 失败 {failed_count}")
                    
                except Exception as e:
                    logger.error(f"批量导入失败: {str(e)}")
                    failed_count = len(records)
                    errors = [{'error_type': 'BulkImportError', 'error_reason': str(e)}]
            
            return {
                'success_count': success_count,
                'failed_count': failed_count,
                'duplicate_count': len(duplicate_records),
                'total_count': len(df),
                'errors': errors,
                'failed_records': failed_records[:5],  # 只返回前5条失败记录
                'duplicate_records': duplicate_records[:5]  # 只返回前5条重复记录
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