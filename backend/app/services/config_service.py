from typing import Optional, List, Dict, Any, Union
from datetime import datetime
import logging
from app.utils.elasticsearch import ESClient
from app.config.settings import settings
from pydantic import BaseModel
import json

logger = logging.getLogger(__name__)

# 配置项模型
class SystemConfigCreate(BaseModel):
    config_key: str
    config_value: str
    config_type: str = "string"  # string, number, boolean, json
    description: Optional[str] = None
    category: str = "system"  # export, import, system
    is_editable: bool = True

class SystemConfigUpdate(BaseModel):
    config_value: Optional[str] = None
    description: Optional[str] = None
    is_editable: Optional[bool] = None

class RoleConfigOverride(BaseModel):
    role_id: str
    config_key: str
    config_value: str
    config_type: str = "string"

class SystemConfigInDB(BaseModel):
    config_key: str
    config_value: str
    config_type: str
    description: Optional[str] = None
    category: str
    is_editable: bool
    created_at: datetime
    updated_at: datetime

class RoleConfigOverrideInDB(BaseModel):
    role_id: str
    config_key: str
    config_value: str
    config_type: str
    created_at: datetime
    updated_at: datetime

# 默认系统配置
DEFAULT_SYSTEM_CONFIGS = {
    "export_limit": {
        "config_value": "2000",
        "config_type": "number",
        "description": "数据导出条数限制，设置为-1表示不限制",
        "category": "export",
        "is_editable": True
    },
    "export_max_limit": {
        "config_value": "50000",
        "config_type": "number", 
        "description": "数据导出最大条数限制（安全上限）",
        "category": "export",
        "is_editable": True
    },
    "import_batch_size": {
        "config_value": "500",
        "config_type": "number",
        "description": "数据导入批次大小",
        "category": "import",
        "is_editable": True
    },
    "search_page_size": {
        "config_value": "20",
        "config_type": "number",
        "description": "搜索结果每页显示条数",
        "category": "system",
        "is_editable": True
    }
}

class ConfigService:
    def __init__(self):
        self.es_client = ESClient.get_client()
        self.system_config_index = f"{settings.ES_INDEX_PREFIX}_system_configs"
        self.role_config_index = f"{settings.ES_INDEX_PREFIX}_role_config_overrides"
        self._create_indices_if_not_exist()
        self._create_default_configs()

    def _create_indices_if_not_exist(self):
        """创建配置相关索引"""
        # 系统配置索引
        if not self.es_client.indices.exists(index=self.system_config_index):
            system_mapping = {
                "mappings": {
                    "properties": {
                        "config_key": {"type": "keyword"},
                        "config_value": {"type": "text"},
                        "config_type": {"type": "keyword"},
                        "description": {"type": "text"},
                        "category": {"type": "keyword"},
                        "is_editable": {"type": "boolean"},
                        "created_at": {"type": "date"},
                        "updated_at": {"type": "date"}
                    }
                }
            }
            self.es_client.indices.create(index=self.system_config_index, body=system_mapping)
            logger.info(f"创建系统配置索引: {self.system_config_index}")

        # 角色配置覆盖索引
        if not self.es_client.indices.exists(index=self.role_config_index):
            role_mapping = {
                "mappings": {
                    "properties": {
                        "role_id": {"type": "keyword"},
                        "config_key": {"type": "keyword"},
                        "config_value": {"type": "text"},
                        "config_type": {"type": "keyword"},
                        "created_at": {"type": "date"},
                        "updated_at": {"type": "date"}
                    }
                }
            }
            self.es_client.indices.create(index=self.role_config_index, body=role_mapping)
            logger.info(f"创建角色配置覆盖索引: {self.role_config_index}")

    def _create_default_configs(self):
        """创建默认系统配置"""
        for config_key, config_data in DEFAULT_SYSTEM_CONFIGS.items():
            if not self.get_system_config(config_key):
                now = datetime.utcnow()
                config_doc = {
                    "config_key": config_key,
                    "config_value": config_data["config_value"],
                    "config_type": config_data["config_type"],
                    "description": config_data["description"],
                    "category": config_data["category"],
                    "is_editable": config_data["is_editable"],
                    "created_at": now,
                    "updated_at": now
                }
                self.es_client.index(
                    index=self.system_config_index,
                    document=config_doc,
                    id=config_key
                )
                logger.info(f"创建默认配置: {config_key}")

    def get_system_config(self, config_key: str) -> Optional[SystemConfigInDB]:
        """获取系统配置"""
        try:
            response = self.es_client.get(index=self.system_config_index, id=config_key)
            config_data = response["_source"]
            return SystemConfigInDB(**config_data)
        except Exception as e:
            logger.debug(f"系统配置不存在: {config_key}")
            return None

    def get_all_system_configs(self, category: Optional[str] = None) -> List[Dict[str, Any]]:
        """获取所有系统配置"""
        try:
            query = {"match_all": {}}
            if category:
                query = {"term": {"category": category}}

            response = self.es_client.search(
                index=self.system_config_index,
                query=query,
                size=1000,
                sort=[{"category": {"order": "asc"}}, {"config_key": {"order": "asc"}}]
            )
            
            configs = []
            for hit in response["hits"]["hits"]:
                config_data = hit["_source"]
                config_data["id"] = hit["_id"]
                configs.append(config_data)
            return configs
        except Exception as e:
            logger.error(f"获取系统配置失败: {str(e)}")
            return []

    def update_system_config(self, config_key: str, config_update: SystemConfigUpdate) -> Optional[SystemConfigInDB]:
        """更新系统配置"""
        config = self.get_system_config(config_key)
        if not config:
            raise ValueError(f"配置项不存在: {config_key}")

        if not config.is_editable:
            raise ValueError(f"配置项不可编辑: {config_key}")

        # 准备更新数据
        update_data = {"updated_at": datetime.utcnow()}
        if config_update.config_value is not None:
            # 验证配置值
            self._validate_config_value(config_key, config_update.config_value, config.config_type)
            update_data["config_value"] = config_update.config_value
        if config_update.description is not None:
            update_data["description"] = config_update.description
        if config_update.is_editable is not None:
            update_data["is_editable"] = config_update.is_editable

        self.es_client.update(
            index=self.system_config_index,
            id=config_key,
            doc=update_data
        )

        return self.get_system_config(config_key)

    def get_all_role_config_overrides(self) -> List[Dict[str, Any]]:
        """获取所有角色的配置覆盖"""
        try:
            response = self.es_client.search(
                index=self.role_config_index,
                query={"match_all": {}},
                size=1000,
                sort=[{"role_id": {"order": "asc"}}, {"config_key": {"order": "asc"}}]
            )
            
            overrides = []
            for hit in response["hits"]["hits"]:
                override_data = hit["_source"]
                override_data["id"] = hit["_id"]
                overrides.append(override_data)
            return overrides
        except Exception as e:
            logger.error(f"获取所有角色配置覆盖失败: {str(e)}")
            return []

    def get_role_config_override(self, role_id: str, config_key: str) -> Optional[RoleConfigOverrideInDB]:
        """获取角色配置覆盖"""
        try:
            override_id = f"{role_id}_{config_key}"
            response = self.es_client.get(index=self.role_config_index, id=override_id)
            override_data = response["_source"]
            return RoleConfigOverrideInDB(**override_data)
        except Exception as e:
            logger.debug(f"角色配置覆盖不存在: {role_id}_{config_key}")
            return None

    def get_role_config_overrides(self, role_id: str) -> List[Dict[str, Any]]:
        """获取角色的所有配置覆盖"""
        try:
            response = self.es_client.search(
                index=self.role_config_index,
                query={"term": {"role_id": role_id}},
                size=1000
            )
            
            overrides = []
            for hit in response["hits"]["hits"]:
                override_data = hit["_source"]
                override_data["id"] = hit["_id"]
                overrides.append(override_data)
            return overrides
        except Exception as e:
            logger.error(f"获取角色配置覆盖失败: {str(e)}")
            return []

    def set_role_config_override(self, role_config: RoleConfigOverride) -> RoleConfigOverrideInDB:
        """设置角色配置覆盖"""
        # 验证系统配置是否存在
        system_config = self.get_system_config(role_config.config_key)
        if not system_config:
            raise ValueError(f"系统配置不存在: {role_config.config_key}")

        # 验证配置值
        self._validate_config_value(role_config.config_key, role_config.config_value, system_config.config_type)

        now = datetime.utcnow()
        override_id = f"{role_config.role_id}_{role_config.config_key}"
        
        # 检查是否已存在覆盖配置
        existing_override = self.get_role_config_override(role_config.role_id, role_config.config_key)
        
        override_data = {
            "role_id": role_config.role_id,
            "config_key": role_config.config_key,
            "config_value": role_config.config_value,
            "config_type": system_config.config_type,
            "updated_at": now
        }
        
        if not existing_override:
            override_data["created_at"] = now

        self.es_client.index(
            index=self.role_config_index,
            document=override_data,
            id=override_id,
            refresh=True  # 强制刷新索引，确保数据立即可用
        )

        # 直接构造返回对象，而不是重新查询
        return RoleConfigOverrideInDB(**override_data)

    def delete_role_config_override(self, role_id: str, config_key: str) -> bool:
        """删除角色配置覆盖"""
        try:
            override_id = f"{role_id}_{config_key}"
            self.es_client.delete(index=self.role_config_index, id=override_id)
            logger.info(f"删除角色配置覆盖: {role_id}_{config_key}")
            return True
        except Exception as e:
            logger.error(f"删除角色配置覆盖失败: {str(e)}")
            return False

    def get_effective_config(self, user_role_id: str, config_key: str, default_value: Any = None) -> Any:
        """获取用户的有效配置值（角色覆盖 > 系统配置 > 默认值）"""
        # 首先检查角色配置覆盖
        role_override = self.get_role_config_override(user_role_id, config_key)
        if role_override:
            return self._convert_config_value(role_override.config_value, role_override.config_type)

        # 然后检查系统配置
        system_config = self.get_system_config(config_key)
        if system_config:
            return self._convert_config_value(system_config.config_value, system_config.config_type)

        # 最后返回默认值
        return default_value

    def get_user_effective_configs(self, user_role_id: str) -> Dict[str, Any]:
        """获取用户的所有有效配置"""
        effective_configs = {}
        
        # 获取所有系统配置
        system_configs = self.get_all_system_configs()
        for config in system_configs:
            config_key = config["config_key"]
            effective_configs[config_key] = self.get_effective_config(user_role_id, config_key)
        
        return effective_configs

    def _validate_config_value(self, config_key: str, config_value: str, config_type: str):
        """验证配置值"""
        try:
            if config_type == "number":
                value = int(config_value)
                # 特殊验证规则
                if config_key == "export_limit" and value < -1:
                    raise ValueError("导出限制不能小于-1")
                elif config_key == "export_max_limit" and value <= 0:
                    raise ValueError("导出最大限制必须大于0")
            elif config_type == "boolean":
                if config_value.lower() not in ["true", "false"]:
                    raise ValueError("布尔值必须是true或false")
            elif config_type == "json":
                json.loads(config_value)
        except (ValueError, json.JSONDecodeError) as e:
            raise ValueError(f"配置值格式错误: {str(e)}")

    def _convert_config_value(self, config_value: str, config_type: str) -> Any:
        """转换配置值为对应类型"""
        try:
            if config_type == "number":
                return int(config_value)
            elif config_type == "boolean":
                return config_value.lower() == "true"
            elif config_type == "json":
                return json.loads(config_value)
            else:
                return config_value
        except (ValueError, json.JSONDecodeError):
            logger.warning(f"配置值转换失败，返回原始字符串: {config_value}")
            return config_value