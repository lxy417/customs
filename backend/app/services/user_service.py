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

class UserCreate(BaseModel):
    username: str
    password: str
    allowed_customs_codes: Optional[List[str]] = None
    is_admin: bool = False

class UserUpdate(BaseModel):
    password: Optional[str] = None
    allowed_customs_codes: Optional[List[str]] = None
    is_admin: Optional[bool] = None

class UserInDB(BaseModel):
    username: str
    hashed_password: str
    allowed_customs_codes: List[str] = []
    is_admin: bool = False
    created_at: datetime = datetime.utcnow()
    updated_at: datetime = datetime.utcnow()

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    username: Optional[str] = None

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
                        "hashed_password": {"type": "text"},
                        "allowed_customs_codes": {"type": "keyword"},
                        "is_admin": {"type": "boolean"},
                        "created_at": {"type": "date"},
                        "updated_at": {"type": "date"}
                    }
                }
            }
            self.es_client.indices.create(index=self.index_name, body=mapping)
            logger.info(f"创建用户索引: {self.index_name}")
        else:
            logger.info(f"用户索引已存在: {self.index_name}")

    def _create_default_admin_user(self):
        """创建默认管理员用户（如果不存在）"""
        admin_username = "admin"
        admin_password = "admin123"

        # 检查管理员用户是否已存在
        if not self.get_user_by_username(admin_username):
            # 创建管理员用户
            user_data = UserCreate(
                username=admin_username,
                password=admin_password,
                allowed_customs_codes=[],
                is_admin=True
            )
            self.create_user(user_data)
            logger.warning(f"已创建默认管理员用户: {admin_username}, 初始密码: {admin_password}, 请尽快修改!")
        else:
            logger.info(f"管理员用户已存在: {admin_username}")

    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """验证密码"""
        return pwd_context.verify(plain_password, hashed_password)

    def get_password_hash(self, password: str) -> str:
        """生成密码哈希"""
        return pwd_context.hash(password)

    def create_access_token(self, data: dict, expires_delta: Optional[timedelta] = None) -> str:
        """创建JWT访问令牌"""
        to_encode = data.copy()
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(minutes=15)
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

        # 准备用户数据
        now = datetime.utcnow()
        user_data = {
            "username": user_create.username,
            "hashed_password": self.get_password_hash(user_create.password),
            "allowed_customs_codes": user_create.allowed_customs_codes or [],
            "is_admin": user_create.is_admin,
            "created_at": now,
            "updated_at": now
        }

        # 保存用户到ES
        self.es_client.index(
            index=self.index_name,
            document=user_data,
            id=user_create.username  # 使用用户名作为文档ID
        )

        logger.info(f"创建用户成功: {user_create.username}")
        return UserInDB(**user_data)

    def update_user(self, username: str, user_update: UserUpdate) -> Optional[UserInDB]:
        """更新用户信息"""
        user = self.get_user_by_username(username)
        if not user:
            return None

        # 准备更新数据
        update_data = {}
        if user_update.password:
            update_data["hashed_password"] = self.get_password_hash(user_update.password)
        if user_update.allowed_customs_codes is not None:
            update_data["allowed_customs_codes"] = user_update.allowed_customs_codes
        if user_update.is_admin is not None:
            update_data["is_admin"] = user_update.is_admin
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
                users.append(user_data)
            return users
        except Exception as e:
            logger.error(f"列出用户失败: {str(e)}")
            return []

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
        if user.is_admin:
            return True
        # 检查用户是否有权限访问该海关编码
        return customs_code in user.allowed_customs_codes