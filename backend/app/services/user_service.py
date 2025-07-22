from datetime import datetime, timedelta
from typing import Optional, Dict, List, Any
from passlib.context import CryptContext
from jose import JWTError, jwt
import logging
from app.utils.elasticsearch import ESClient
from app.config.settings import settings
from pydantic import BaseModel, EmailStr, validator

logger = logging.getLogger(__name__)

# 密码加密上下文
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Token相关模型
class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    username: Optional[str] = None

class UserCreate(BaseModel):
    username: str
    password: str
    role_id: str = "user"  # 默认为普通用户角色
    allowed_customs_codes: Optional[List[str]] = None
    additional_permissions: Optional[List[str]] = None  # 额外权限
    group_ids: Optional[List[str]] = None

class UserUpdate(BaseModel):
    password: Optional[str] = None
    role_id: Optional[str] = None
    allowed_customs_codes: Optional[List[str]] = None
    additional_permissions: Optional[List[str]] = None  # 额外权限
    group_ids: Optional[List[str]] = None

class UserInDB(BaseModel):
    username: str
    hashed_password: str
    role_id: str = "user"
    allowed_customs_codes: List[str] = []
    additional_permissions: List[str] = []  # 额外权限
    group_ids: List[str] = []
    created_at: datetime
    updated_at: datetime
    
    # 保持向后兼容
    @property
    def is_admin(self) -> bool:
        """向后兼容的管理员检查"""
        return self.role_id == "admin"

class UserService:
    def __init__(self):
        self.es_client = ESClient.get_client()
        self.index_name = settings.USER_INDEX
        self._create_index_if_not_exists()
        self._create_default_admin_user()

    def _create_index_if_not_exists(self):
        """创建用户索引（如果不存在）"""
        if not self.es_client.indices.exists(index=self.index_name):
            mapping = {
                "mappings": {
                    "properties": {
                        "username": {"type": "keyword"},
                        "hashed_password": {"type": "keyword"},
                        "role_id": {"type": "keyword"},
                        "allowed_customs_codes": {"type": "keyword"},
                        "additional_permissions": {"type": "keyword"},
                        "group_ids": {"type": "keyword"},
                        "created_at": {"type": "date"},
                        "updated_at": {"type": "date"}
                    }
                }
            }
            self.es_client.indices.create(index=self.index_name, body=mapping)
            logger.info(f"创建用户索引: {self.index_name}")

    def _create_default_admin_user(self):
        """创建默认管理员用户"""
        admin_username = "admin"
        if not self.get_user_by_username(admin_username):
            admin_user = UserCreate(
                username=admin_username,
                password="admin123",
                role_id="admin"
            )
            self.create_user(admin_user)
            logger.info("创建默认管理员用户")

    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """验证密码"""
        return pwd_context.verify(plain_password, hashed_password)

    def get_password_hash(self, password: str) -> str:
        """获取密码哈希"""
        return pwd_context.hash(password)

    def create_access_token(self, data: dict, expires_delta: Optional[timedelta] = None):
        """创建访问令牌"""
        to_encode = data.copy()
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        to_encode.update({"exp": expire})
        encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
        return encoded_jwt

    def get_user_by_username(self, username: str) -> Optional[UserInDB]:
        """通过用户名获取用户"""
        try:
            response = self.es_client.search(
                index=self.index_name,
                query={"term": {"username": username}}
            )
            if response["hits"]["total"]["value"] > 0:
                user_data = response["hits"]["hits"][0]["_source"]
                # 向后兼容：如果没有role_id，根据is_admin设置
                if "role_id" not in user_data:
                    user_data["role_id"] = "admin" if user_data.get("is_admin", False) else "user"
                if "additional_permissions" not in user_data:
                    user_data["additional_permissions"] = []
                return UserInDB(**user_data)
            return None
        except Exception as e:
            logger.error(f"获取用户失败: {str(e)}")
            return None

    def create_user(self, user_create: UserCreate) -> UserInDB:
        """创建新用户"""
        # 检查用户是否已存在
        if self.get_user_by_username(user_create.username):
            raise ValueError(f"用户名 '{user_create.username}' 已存在")

        # 验证角色是否存在
        from .role_service import RoleService
        role_service = RoleService()
        if not role_service.get_role_by_id(user_create.role_id):
            raise ValueError(f"角色 '{user_create.role_id}' 不存在")

        # 验证额外权限
        if user_create.additional_permissions:
            available_permissions = role_service.get_available_permissions()
            invalid_permissions = [p for p in user_create.additional_permissions if p not in available_permissions]
            if invalid_permissions:
                raise ValueError(f"无效的权限: {invalid_permissions}")

        # 准备用户数据
        now = datetime.utcnow()
        user_data = {
            "username": user_create.username,
            "hashed_password": self.get_password_hash(user_create.password),
            "role_id": user_create.role_id,
            "allowed_customs_codes": user_create.allowed_customs_codes or [],
            "additional_permissions": user_create.additional_permissions or [],
            "group_ids": user_create.group_ids or [],
            "created_at": now,
            "updated_at": now
        }

        # 保存用户到ES
        self.es_client.index(
            index=self.index_name,
            document=user_data,
            id=user_create.username
        )

        logger.info(f"创建用户成功: {user_create.username}")
        return UserInDB(**user_data)

    def update_user(self, username: str, user_update: UserUpdate) -> Optional[UserInDB]:
        """更新用户信息"""
        user = self.get_user_by_username(username)
        if not user:
            return None

        # 验证角色是否存在
        if user_update.role_id:
            from .role_service import RoleService
            role_service = RoleService()
            if not role_service.get_role_by_id(user_update.role_id):
                raise ValueError(f"角色 '{user_update.role_id}' 不存在")

        # 验证额外权限
        if user_update.additional_permissions is not None:
            from .role_service import RoleService
            role_service = RoleService()
            available_permissions = role_service.get_available_permissions()
            invalid_permissions = [p for p in user_update.additional_permissions if p not in available_permissions]
            if invalid_permissions:
                raise ValueError(f"无效的权限: {invalid_permissions}")

        # 准备更新数据
        update_data = {}
        if user_update.password:
            update_data["hashed_password"] = self.get_password_hash(user_update.password)
        if user_update.role_id is not None:
            update_data["role_id"] = user_update.role_id
        if user_update.allowed_customs_codes is not None:
            update_data["allowed_customs_codes"] = user_update.allowed_customs_codes
        if user_update.additional_permissions is not None:
            update_data["additional_permissions"] = user_update.additional_permissions
        if user_update.group_ids is not None:
            update_data["group_ids"] = user_update.group_ids
        update_data["updated_at"] = datetime.utcnow()

        # 更新用户数据
        self.es_client.update(
            index=self.index_name,
            id=username,
            doc=update_data
        )

        # 返回更新后的用户信息
        return self.get_user_by_username(username)

    def delete_user(self, username: str) -> bool:
        """删除用户"""
        if username == "admin":
            logger.warning("尝试删除管理员用户，操作被拒绝")
            return False

        user = self.get_user_by_username(username)
        if not user:
            return False

        self.es_client.delete(index=self.index_name, id=username)
        logger.info(f"删除用户成功: {username}")
        return True

    def list_users(self) -> List[Dict[str, Any]]:
        """列出所有用户"""
        try:
            response = self.es_client.search(
                index=self.index_name,
                query={"match_all": {}},
                size=1000
            )
            users = []
            for hit in response["hits"]["hits"]:
                user_data = hit["_source"]
                # 不返回密码哈希
                user_data.pop("hashed_password", None)
                # 向后兼容
                if "role_id" not in user_data:
                    user_data["role_id"] = "admin" if user_data.get("is_admin", False) else "user"
                if "additional_permissions" not in user_data:
                    user_data["additional_permissions"] = []
                users.append(user_data)
            return users
        except Exception as e:
            logger.error(f"列出用户失败: {str(e)}")
            return []

    def get_users_by_group(self, group_id: str) -> List[Dict[str, Any]]:
        """获取属于特定用户组的用户列表"""
        try:
            response = self.es_client.search(
                index=self.index_name,
                query={"term": {"group_ids": group_id}},
                size=1000
            )
            users = []
            for hit in response["hits"]["hits"]:
                user_data = hit["_source"]
                user_data.pop("hashed_password", None)
                users.append(user_data)
            return users
        except Exception as e:
            logger.error(f"获取用户组用户失败: {str(e)}")
            return []

    def get_users_by_role(self, role_id: str) -> List[Dict[str, Any]]:
        """获取使用特定角色的用户列表"""
        try:
            response = self.es_client.search(
                index=self.index_name,
                query={"term": {"role_id": role_id}},
                size=1000
            )
            users = []
            for hit in response["hits"]["hits"]:
                user_data = hit["_source"]
                user_data.pop("hashed_password", None)
                users.append(user_data)
            return users
        except Exception as e:
            logger.error(f"获取角色用户失败: {str(e)}")
            return []

    def get_user_permissions(self, username: str) -> List[str]:
        """获取用户的功能权限（角色权限 + 额外权限）"""
        user = self.get_user_by_username(username)
        if not user:
            return []
        
        # 获取角色权限
        from .role_service import RoleService
        role_service = RoleService()
        role_permissions = role_service.get_role_permissions(user.role_id)
        
        # 合并角色权限和额外权限
        all_permissions = set(role_permissions)
        all_permissions.update(user.additional_permissions)
        
        return list(all_permissions)

    def get_user_customs_codes(self, username: str) -> List[str]:
        """获取用户可访问的海关编码（包括用户组权限）"""
        user = self.get_user_by_username(username)
        if not user:
            return []
        
        # 管理员可以访问所有海关编码
        if user.role_id == "admin":
            return []  # 空列表表示可以访问所有
        
        # 收集用户直接权限和用户组权限
        customs_codes = set(user.allowed_customs_codes or [])
        
        if user.group_ids:
            from .group_service import GroupService
            group_service = GroupService()
            for group_id in user.group_ids:
                group = group_service.get_group_by_id(group_id)
                if group and group.allowed_customs_codes:
                    customs_codes.update(group.allowed_customs_codes)
        
        return list(customs_codes)

    def authenticate_user(self, username: str, password: str) -> Optional[UserInDB]:
        """验证用户凭据"""
        user = self.get_user_by_username(username)
        if not user or not self.verify_password(password, user.hashed_password):
            return None
        return user

    def check_customs_code_permission(self, username: str, customs_code: str) -> bool:
        """检查用户是否有权限访问特定海关编码的数据"""
        user = self.get_user_by_username(username)
        if not user:
            return False
        # 管理员可以访问所有数据
        if user.role_id == "admin":
            return True
        
        # 获取用户可访问的海关编码（包括用户组权限）
        allowed_codes = self.get_user_customs_codes(username)
        return not allowed_codes or customs_code in allowed_codes

    def check_permission(self, username: str, permission: str) -> bool:
        """检查用户是否有特定权限"""
        user_permissions = self.get_user_permissions(username)
        return permission in user_permissions