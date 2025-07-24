import json
import os
import time
from pathlib import Path
from typing import Dict, Any, List
import logging
from threading import Lock

logger = logging.getLogger(__name__)

class ConfigManager:
    """配置管理器，支持热加载"""
    
    def __init__(self):
        self.config_dir = Path(__file__).parent.parent / "config"
        self.country_mapping_file = self.config_dir / "country_mapping.json"
        self._country_mapping = {}
        self._last_modified = {}
        self._lock = Lock()
        
        # 初始加载配置
        self._load_country_mapping()
    
    def _load_country_mapping(self):
        """加载国家映射配置"""
        try:
            if self.country_mapping_file.exists():
                with open(self.country_mapping_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self._country_mapping = data.get('country_mapping', {})
                    self._last_modified['country_mapping'] = os.path.getmtime(self.country_mapping_file)
                    logger.info(f"加载国家映射配置: {len(self._country_mapping)} 个映射")
            else:
                logger.warning(f"国家映射配置文件不存在: {self.country_mapping_file}")
                self._country_mapping = {}
        except Exception as e:
            logger.error(f"加载国家映射配置失败: {str(e)}")
            self._country_mapping = {}
    
    def _check_and_reload_country_mapping(self):
        """检查并重新加载国家映射配置"""
        try:
            if not self.country_mapping_file.exists():
                return
            
            current_modified = os.path.getmtime(self.country_mapping_file)
            last_modified = self._last_modified.get('country_mapping', 0)
            
            if current_modified > last_modified:
                logger.info("检测到国家映射配置文件更新，重新加载...")
                self._load_country_mapping()
        except Exception as e:
            logger.error(f"检查国家映射配置文件失败: {str(e)}")
    
    def get_country_mapping(self) -> Dict[str, List[str]]:
        """获取国家映射配置（支持热加载）
        返回格式: {"中文名": ["English (Code)", "English", "中文名"]}
        """
        with self._lock:
            self._check_and_reload_country_mapping()
            return self._country_mapping.copy()
    
    def find_chinese_name(self, input_country: str) -> str:
        """根据输入的国家名称查找对应的中文名称"""
        if not input_country or not input_country.strip():
            return ""
        
        input_country = input_country.strip()
        
        with self._lock:
            self._check_and_reload_country_mapping()
            
            # 遍历所有映射，查找匹配的国家名称
            for chinese_name, aliases in self._country_mapping.items():
                # 精确匹配
                if input_country in aliases:
                    return chinese_name
                
                # 模糊匹配
                for alias in aliases:
                    # 检查是否包含国家代码
                    if '(' in alias and ')' in alias:
                        country_code = alias.split('(')[1].split(')')[0]
                        if country_code.upper() in input_country.upper():
                            return chinese_name
                    
                    # 检查名称部分匹配
                    alias_name = alias.split('(')[0].strip()
                    if (alias_name.lower() in input_country.lower() or 
                        input_country.lower() in alias_name.lower()):
                        return chinese_name
            
            # 如果没有找到匹配，返回原值
            return input_country
    
    def reload_all_configs(self):
        """手动重新加载所有配置"""
        with self._lock:
            logger.info("手动重新加载所有配置...")
            self._load_country_mapping()
    
    def add_country_mapping(self, chinese_name: str, aliases: List[str]):
        """动态添加国家映射"""
        with self._lock:
            if chinese_name not in self._country_mapping:
                self._country_mapping[chinese_name] = []
            
            # 添加新的别名，避免重复
            for alias in aliases:
                if alias not in self._country_mapping[chinese_name]:
                    self._country_mapping[chinese_name].append(alias)
            
            self._save_country_mapping()
    
    def remove_country_mapping(self, chinese_name: str):
        """动态删除国家映射"""
        with self._lock:
            if chinese_name in self._country_mapping:
                del self._country_mapping[chinese_name]
                self._save_country_mapping()
    
    def _save_country_mapping(self):
        """保存国家映射配置到文件"""
        try:
            data = {"country_mapping": self._country_mapping}
            with open(self.country_mapping_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            self._last_modified['country_mapping'] = os.path.getmtime(self.country_mapping_file)
            logger.info("国家映射配置已保存")
        except Exception as e:
            logger.error(f"保存国家映射配置失败: {str(e)}")

# 全局配置管理器实例
config_manager = ConfigManager()