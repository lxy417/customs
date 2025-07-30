import csv
import os
import logging
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)

class HSCodeService:
    def __init__(self):
        self.hscode_data: Dict[str, str] = {}
        self._load_hscode_data()
    
    def _load_hscode_data(self):
        """从CSV文件加载HSCode数据到内存"""
        try:
            # 获取CSV文件路径
            current_dir = os.path.dirname(os.path.abspath(__file__))
            csv_path = os.path.join(current_dir, '..', 'config', 'HSCode.csv')
            csv_path = os.path.normpath(csv_path)
            
            if not os.path.exists(csv_path):
                logger.error(f"HSCode.csv文件不存在: {csv_path}")
                return
            
            # 读取CSV文件
            with open(csv_path, 'r', encoding='utf-8') as file:
                reader = csv.DictReader(file)
                for row in reader:
                    hscode = row.get('HSCode', '').strip()
                    chinese_desc = row.get('ChineseDescription', '').strip()
                    
                    if hscode and chinese_desc:
                        self.hscode_data[hscode] = chinese_desc
            
            logger.info(f"成功加载 {len(self.hscode_data)} 条HSCode数据")
            
        except Exception as e:
            logger.error(f"加载HSCode数据失败: {str(e)}", exc_info=True)
    
    def get_multiple_descriptions(self, hscodes: List[str]) -> Dict[str, str]:
        """批量获取多个HSCode的中文描述"""
        result = {}
        for hscode in hscodes:
            if hscode and str(hscode).strip():
                clean_hscode = str(hscode).strip()
                chinese_desc = self.hscode_data.get(clean_hscode)
                if chinese_desc:
                    result[clean_hscode] = chinese_desc
        return result

# 创建全局实例
hscode_service = HSCodeService()