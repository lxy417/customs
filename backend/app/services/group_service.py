from typing import Optional, List, Dict, Any
from datetime import datetime
import logging
from app.utils.elasticsearch import ESClient
from pydantic import BaseModel

logger = logging.getLogger(__name__)

class GroupCreate(BaseModel):
    name: str
    description: Optional[str] = None
    allowed_customs_codes: Optional[List[str]] = None  # 只保留海关编码权限

class GroupUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    allowed_customs_codes: Optional[List[str]] = None  # 只保留海关编码权限

class GroupInDB(BaseModel):
    id: str
    name: str
    description: Optional[str] = None
    allowed_customs_codes: List[str] = []  # 只保留海关编码权限
    created_at: datetime = datetime.utcnow()
    updated_at: datetime = datetime.utcnow()

class GroupService:
    def __init__(self):
        self.es_client = ESClient.get_client()
        self.index_name = "user_groups"
        self._ensure_index_exists()

    def _ensure_index_exists(self):
        """确保索引存在"""
        try:
            if not self.es_client.indices.exists(index=self.index_name):
                mapping = {
                    "mappings": {
                        "properties": {
                            "name": {"type": "keyword"},
                            "description": {"type": "text"},
                            "allowed_customs_codes": {"type": "keyword"},  # 移除permissions字段
                            "created_at": {"type": "date"},
                            "updated_at": {"type": "date"}
                        }
                    }
                }
                self.es_client.indices.create(index=self.index_name, body=mapping)
                logger.info(f"创建索引 {self.index_name}")
        except Exception as e:
            logger.error(f"创建索引失败: {e}")

    def create_group(self, group_create: GroupCreate) -> Dict[str, Any]:
        """创建用户组"""
        try:
            # 检查用户组名是否已存在
            if self.get_group_by_name(group_create.name):
                raise ValueError(f"用户组 '{group_create.name}' 已存在")

            group_data = {
                "name": group_create.name,
                "description": group_create.description,
                "allowed_customs_codes": group_create.allowed_customs_codes or [],  # 移除permissions
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow()
            }

            response = self.es_client.index(
                index=self.index_name,
                document=group_data
            )

            group_data["id"] = response["_id"]
            logger.info(f"创建用户组成功: {group_create.name}")
            return group_data

        except Exception as e:
            logger.error(f"创建用户组失败: {e}")
            raise

    def get_group_by_id(self, group_id: str) -> Optional[GroupInDB]:
        """通过ID获取用户组"""
        try:
            response = self.es_client.get(
                index=self.index_name,
                id=group_id
            )
            group_data = response["_source"]
            group_data["id"] = response["_id"]
            return GroupInDB(**group_data)
        except Exception as e:
            logger.error(f"获取用户组失败: {e}")
            return None

    def get_group_by_name(self, name: str) -> Optional[GroupInDB]:
        """通过名称获取用户组"""
        try:
            response = self.es_client.search(
                index=self.index_name,
                query={"term": {"name": name}}
            )
            if response["hits"]["total"]["value"] > 0:
                group_data = response["hits"]["hits"][0]["_source"]
                group_data["id"] = response["hits"]["hits"][0]["_id"]
                return GroupInDB(**group_data)
            return None
        except Exception as e:
            logger.error(f"获取用户组失败: {e}")
            return None

    def update_group(self, group_id: str, group_update: GroupUpdate) -> Optional[Dict[str, Any]]:
        """更新用户组"""
        try:
            # 检查用户组是否存在
            existing_group = self.get_group_by_id(group_id)
            if not existing_group:
                return None

            # 如果更新名称，检查新名称是否已存在
            if group_update.name and group_update.name != existing_group.name:
                if self.get_group_by_name(group_update.name):
                    raise ValueError(f"用户组名称 '{group_update.name}' 已存在")

            update_data = {}
            if group_update.name is not None:
                update_data["name"] = group_update.name
            if group_update.description is not None:
                update_data["description"] = group_update.description
            if group_update.allowed_customs_codes is not None:
                update_data["allowed_customs_codes"] = group_update.allowed_customs_codes
            
            update_data["updated_at"] = datetime.utcnow()

            self.es_client.update(
                index=self.index_name,
                id=group_id,
                body={"doc": update_data}
            )

            # 返回更新后的用户组
            updated_group = self.get_group_by_id(group_id)
            logger.info(f"更新用户组成功: {group_id}")
            return updated_group.dict() if updated_group else None

        except Exception as e:
            logger.error(f"更新用户组失败: {e}")
            raise

    def delete_group(self, group_id: str) -> bool:
        """删除用户组"""
        try:
            # 检查是否有用户属于此用户组
            from .user_service import UserService
            user_service = UserService()
            users_in_group = user_service.get_users_by_group(group_id)
            
            if users_in_group:
                raise ValueError(f"无法删除用户组，还有 {len(users_in_group)} 个用户属于此用户组")

            self.es_client.delete(
                index=self.index_name,
                id=group_id
            )
            logger.info(f"删除用户组成功: {group_id}")
            return True

        except Exception as e:
            logger.error(f"删除用户组失败: {e}")
            raise

    def list_groups(self) -> List[Dict[str, Any]]:
        """列出所有用户组"""
        try:
            response = self.es_client.search(
                index=self.index_name,
                query={"match_all": {}},
                size=1000,
                sort=[{"created_at": {"order": "desc"}}]
            )

            groups = []
            for hit in response["hits"]["hits"]:
                group_data = hit["_source"]
                group_data["id"] = hit["_id"]
                groups.append(group_data)

            return groups

        except Exception as e:
            logger.error(f"获取用户组列表失败: {e}")
            return []

    # 移除 get_available_permissions 方法，因为用户组不再管理功能权限