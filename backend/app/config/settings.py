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

    DEEPSEEK_API_URL: str = "https://api.deepseek.com/v1/chat/completions"
    DEEPSEEK_API_KEY: str = "sk-d543c6900c10491b9255709d0510d711"

    class Config:
        case_sensitive = True
        env_file = ".env"

settings = Settings()