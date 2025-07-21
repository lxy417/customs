import json
import os
import time
from pathlib import Path
from typing import Dict, Any
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
    
    def get_country_mapping(self) -> Dict[str, str]:
        """获取国家映射配置（支持热加载）"""
        with self._lock:
            self._check_and_reload_country_mapping()
            return self._country_mapping.copy()
    
    def reload_all_configs(self):
        """手动重新加载所有配置"""
        with self._lock:
            logger.info("手动重新加载所有配置...")
            self._load_country_mapping()
    
    def add_country_mapping(self, english_name: str, chinese_name: str):
        """动态添加国家映射"""
        with self._lock:
            self._country_mapping[english_name] = chinese_name
            self._save_country_mapping()
    
    def remove_country_mapping(self, english_name: str):
        """动态删除国家映射"""
        with self._lock:
            if english_name in self._country_mapping:
                del self._country_mapping[english_name]
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