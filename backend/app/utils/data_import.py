import sys
import pandas as pd
import numpy as np
from typing import List, Dict, Any
import logging
from datetime import datetime
from app.utils.elasticsearch import ESClient
from app.config.settings import settings
from elasticsearch.helpers import bulk

logger = logging.getLogger(__name__)

class DataImportService:
    def __init__(self):
        self.es_client = ESClient.get_client()
        self.index_name = settings.DATA_INDEX
        self._create_index_if_not_exists()
        self.date_formats = ['%Y-%m-%d', '%Y/%m/%d', '%Y%m%d', '%Y年%m月%d日']

    def _create_index_if_not_exists(self):
        """创建数据索引（如果不存在）"""
        if not self.es_client.indices.exists(index=self.index_name):
            mapping = {
                "mappings": {
                    "properties": {
                        "海关编码": {"type": "keyword"},
                        "编码产品描述": {"type": "text"},
                        "日期": {"type": "date", "format": "yyyy-MM-dd||yyyy/MM/dd||yyyyMMdd"},
                        "月度": {"type": "keyword"},
                        "进口商": {"type": "keyword"},
                        "进口商所在国家": {"type": "keyword"},
                        "出口商所在国家": {"type": "keyword"},
                        "出口商": {"type": "keyword"},
                        "重量单位": {"type": "keyword"},
                        "数量单位": {"type": "keyword"},
                        "数量": {"type": "float"},
                        "毛重": {"type": "float"},
                        "净重": {"type": "float"},
                        "公吨": {"type": "float"},
                        "金额美元": {"type": "float"},
                        "美元重量计单价": {"type": "float"},
                        "美元数量计单价": {"type": "float"},
                        "本国币种金额": {"type": "float"},
                        "合同金额": {"type": "float"},
                        "币种": {"type": "keyword"},
                        "成交方式": {"type": "keyword"},
                        "详细产品名称": {"type": "text"},
                        "产品规格型号品牌": {"type": "text"},
                        "当地港口": {"type": "keyword"},
                        "国外港口": {"type": "keyword"},
                        "运输方式": {"type": "keyword"},
                        "贸易方式": {"type": "keyword"},
                        "中转国": {"type": "keyword"},
                        "提单号": {"type": "keyword"},
                        "编码产品描述本国语言": {"type": "text"},
                        "详细产品名称本国语言": {"type": "text"},
                        "产品规格型号品牌本国语言": {"type": "text"},
                        "进口商本地语言": {"type": "keyword"},
                        "数据来源": {"type": "keyword"},
                        "出口商本地语言": {"type": "keyword"},
                        "关单号": {"type": "keyword"},
                        "申报数量": {"type": "float"}
                    }
                }
            }
            self.es_client.indices.create(index=self.index_name, body=mapping)
            logger.info(f"创建数据索引: {self.index_name}")
        else:
            logger.info(f"数据索引已存在: {self.index_name}")

    def _process_excel_data(self, df: pd.DataFrame) -> List[Dict[str, Any]]:        
        """增强数据清洗"""
        # 确保列名与映射完全匹配
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
            print(f"警告：缺少必要列: {missing_cols}")
        
        cleaned_data = []
        for _, row in df.iterrows():
            if row['海关编码'] == "海关编码":
                continue
            record = {}
            for col in required_columns:
                if col in row:
                    if col == "海关编码":
                        record[col] = row[col][:6]
                    # 特殊处理日期字段
                    elif col == '日期':
                        record[col] = self.parse_date(row[col])
                    # 处理数值字段
                    elif col in ['数量', '毛重', '净重', '公吨', '金额美元', 
                               '美元重量计单价', '美元数量计单价', '本国币种金额', 
                               '合同金额', '申报数量']:
                        record[col] = self.clean_numeric(row[col])
                    # 其他字段直接赋值
                    else:
                        value = row[col]
                        record[col] = str(value) if not pd.isna(value) else None
                else:
                    record[col] = None
            
            cleaned_data.append(record)
        return cleaned_data

    def parse_date(self, date_str):
        """解析日期字符串，尝试多种格式"""
        if pd.isna(date_str):
            return None
        for fmt in self.date_formats:
            try:
                return datetime.strptime(str(date_str), fmt).strftime('%Y-%m-%d')
            except ValueError:
                continue
        # 如果所有格式都失败，返回原始值
        return str(date_str)

    def clean_numeric(self, value):
        """处理各种数值类型和空值"""
        if pd.isna(value) or value in ['', 'nan', 'NaN', 'None']:
            return None
            
        try:
            # 处理带逗号的数字字符串
            if isinstance(value, str):
                value = value.replace(',', '')
            return float(value)
        except (ValueError, TypeError):
            return None

    def import_from_excel(self, file_path: str, batch_size: int = 500) -> Dict[str, Any]:
        """从Excel导入数据到Elasticsearch"""
        try:
            # 读取Excel文件
            df = pd.read_excel(file_path, engine='openpyxl')
            print(f"成功读取Excel文件，共 {len(df)} 条记录")

            # 数据清洗
            cleaned_data = self._process_excel_data(df)
            print(f"数据清洗完成，共 {len(cleaned_data)} 条有效记录")

            # 批量导入到Elasticsearch
            actions = [{
                '_op_type': 'index',  # 明确操作类型
                '_index': self.index_name,
                '_source': record
            } for record in cleaned_data]

            # 批量插入，将batch_size参数改为chunk_size
            success, errors = bulk(
                self.es_client, 
                actions, 
                chunk_size=batch_size,
                raise_on_error=False,  # 不因单个错误中断
                stats_only=False  # 返回详细错误信息
            )
            print(f"导入结果: 成功 {success} 条, 失败 {len(errors)} 条")
            
            if errors:
                print("\n错误详情:")
                for i, error in enumerate(errors[:5]):  # 只显示前5个错误
                    print(f"错误 #{i+1}:")
                    print(f"文档: {error['index']['_source']}")
                    print(f"错误类型: {error['index']['error']['type']}")
                    print(f"原因: {error['index']['error']['reason']}")
                    print("-" * 50)

            return success, errors

        except Exception as e:
            import traceback
            print(f"严重错误: {str(e)}")
            traceback.print_exc()
            return 0, [str(e)]
