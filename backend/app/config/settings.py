from pydantic_settings import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    # Elasticsearch配置
    ELASTICSEARCH_HOST: str = "localhost"
    ELASTICSEARCH_PORT: int = 9200
    ELASTICSEARCH_USER: Optional[str] = "elastic"
    ELASTICSEARCH_PASSWORD: Optional[str] = "changeme"
    ELASTICSEARCH_SCHEME: str = "http"
    ELASTICSEARCH_VERIFY_CERTS: bool = False
    
    # JWT认证配置
    SECRET_KEY: str = "your-secret-key-here-change-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    # 数据索引名称
    DATA_INDEX: str = "customs_data"
    USER_INDEX: str = "customs_users"

    class Config:
        case_sensitive = True
        env_file = ".env"

settings = Settings()