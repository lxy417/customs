from typing import Optional, List, Dict, Any
from datetime import datetime
import logging
from app.utils.elasticsearch import ESClient
from app.config.settings import settings
from pydantic import BaseModel

logger = logging.getLogger(__name__)

# 权限常量定义
PERMISSIONS = {
    "data_view": "数据查看",
    "data_export": "数据导出", 
    "data_create": "数据创建",
    "data_update": "数据更新",
    "data_delete": "数据删除",
    "data_import": "数据导入",
    "user_manage": "用户管理",
    "group_manage": "用户组管理",
    "role_manage": "角色管理",
    "ai_search": "AI搜索",
}

# 默认角色定义
DEFAULT_ROLES = {
    "admin": {
        "name": "管理员",
        "description": "系统管理员，拥有所有权限",
        "permissions": list(PERMISSIONS.keys()),
        "is_system": True
    },
    "user": {
        "name": "普通用户", 
        "description": "普通用户，只有基础查看和导出权限",
        "permissions": ["data_view", "data_export", "ai_search"],
        "is_system": True
    }
}

class RoleCreate(BaseModel):
    name: str
    description: Optional[str] = None
    permissions: List[str] = []

class RoleUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    permissions: Optional[List[str]] = None

class RoleInDB(BaseModel):
    id: str
    name: str
    description: Optional[str] = None
    permissions: List[str] = []
    is_system: bool = False  # 是否为系统角色（不可删除）
    created_at: datetime
    updated_at: datetime

class RoleService:
    def __init__(self):
        self.es_client = ESClient.get_client()
        self.index_name = f"{settings.ES_INDEX_PREFIX}_roles"
        self._create_index_if_not_exists()
        self._create_default_roles()

    def _create_index_if_not_exists(self):
        """创建角色索引（如果不存在）"""
        if not self.es_client.indices.exists(index=self.index_name):
            mapping = {
                "mappings": {
                    "properties": {
                        "name": {"type": "keyword"},
                        "description": {"type": "text"},
                        "permissions": {"type": "keyword"},
                        "is_system": {"type": "boolean"},
                        "created_at": {"type": "date"},
                        "updated_at": {"type": "date"}
                    }
                }
            }
            self.es_client.indices.create(index=self.index_name, body=mapping)
            logger.info(f"创建角色索引: {self.index_name}")

    def _create_default_roles(self):
        """创建默认角色"""
        for role_id, role_data in DEFAULT_ROLES.items():
            if not self.get_role_by_id(role_id):
                now = datetime.utcnow()
                role_doc = {
                    "name": role_data["name"],
                    "description": role_data["description"],
                    "permissions": role_data["permissions"],
                    "is_system": role_data["is_system"],
                    "created_at": now,
                    "updated_at": now
                }
                self.es_client.index(
                    index=self.index_name,
                    document=role_doc,
                    id=role_id
                )
                logger.info(f"创建默认角色: {role_data['name']}")

    def get_role_by_id(self, role_id: str) -> Optional[RoleInDB]:
        """通过ID获取角色"""
        try:
            response = self.es_client.get(index=self.index_name, id=role_id)
            role_data = response["_source"]
            role_data["id"] = response["_id"]
            return RoleInDB(**role_data)
        except Exception as e:
            logger.debug(f"角色不存在: {role_id}")
            return None

    def create_role(self, role_create: RoleCreate) -> RoleInDB:
        """创建新角色"""
        # 验证权限
        invalid_permissions = [p for p in role_create.permissions if p not in PERMISSIONS]
        if invalid_permissions:
            raise ValueError(f"无效的权限: {invalid_permissions}")

        # 检查角色名是否已存在
        existing_roles = self.list_roles()
        for role in existing_roles:
            if role["name"] == role_create.name:
                raise ValueError(f"角色名 '{role_create.name}' 已存在")

        now = datetime.utcnow()
        role_data = {
            "name": role_create.name,
            "description": role_create.description,
            "permissions": role_create.permissions,
            "is_system": False,
            "created_at": now,
            "updated_at": now
        }

        # 生成角色ID
        role_id = f"role_{int(now.timestamp())}"
        
        self.es_client.index(
            index=self.index_name,
            document=role_data,
            id=role_id
        )

        role_data["id"] = role_id
        logger.info(f"创建角色成功: {role_create.name}")
        return RoleInDB(**role_data)

    def update_role(self, role_id: str, role_update: RoleUpdate) -> Optional[RoleInDB]:
        """更新角色信息"""
        role = self.get_role_by_id(role_id)
        if not role:
            return None

        # 系统角色不允许修改
        if role.is_system:
            raise ValueError("系统角色不允许修改")

        # 验证权限
        if role_update.permissions is not None:
            invalid_permissions = [p for p in role_update.permissions if p not in PERMISSIONS]
            if invalid_permissions:
                raise ValueError(f"无效的权限: {invalid_permissions}")

        # 检查角色名是否已存在
        if role_update.name and role_update.name != role.name:
            existing_roles = self.list_roles()
            for existing_role in existing_roles:
                if existing_role["name"] == role_update.name and existing_role["id"] != role_id:
                    raise ValueError(f"角色名 '{role_update.name}' 已存在")

        # 准备更新数据
        update_data = {"updated_at": datetime.utcnow()}
        if role_update.name is not None:
            update_data["name"] = role_update.name
        if role_update.description is not None:
            update_data["description"] = role_update.description
        if role_update.permissions is not None:
            update_data["permissions"] = role_update.permissions

        self.es_client.update(
            index=self.index_name,
            id=role_id,
            doc=update_data
        )

        return self.get_role_by_id(role_id)

    def delete_role(self, role_id: str) -> bool:
        """删除角色"""
        role = self.get_role_by_id(role_id)
        if not role:
            return False

        # 系统角色不允许删除
        if role.is_system:
            raise ValueError("系统角色不允许删除")

        # 检查是否有用户使用此角色
        from .user_service import UserService
        user_service = UserService()
        users_with_role = user_service.get_users_by_role(role_id)
        if users_with_role:
            raise ValueError(f"角色正在被 {len(users_with_role)} 个用户使用，无法删除")

        self.es_client.delete(index=self.index_name, id=role_id)
        logger.info(f"删除角色成功: {role.name}")
        return True

    def list_roles(self) -> List[Dict[str, Any]]:
        """列出所有角色"""
        try:
            response = self.es_client.search(
                index=self.index_name,
                query={"match_all": {}},
                size=1000,
                sort=[{"created_at": {"order": "asc"}}]
            )
            roles = []
            for hit in response["hits"]["hits"]:
                role_data = hit["_source"]
                role_data["id"] = hit["_id"]
                roles.append(role_data)
            return roles
        except Exception as e:
            logger.error(f"列出角色失败: {str(e)}")
            return []

    def get_available_permissions(self) -> Dict[str, str]:
        """获取所有可用权限"""
        return PERMISSIONS.copy()

    def get_role_permissions(self, role_id: str) -> List[str]:
        """获取角色的权限列表"""
        role = self.get_role_by_id(role_id)
        return role.permissions if role else []