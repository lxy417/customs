from elasticsearch import Elasticsearch, AsyncElasticsearch
from elasticsearch.exceptions import ConnectionError
from app.config.settings import settings
from typing import Optional, Dict, Any
import logging

logger = logging.getLogger(__name__)

class ESClient:
    _client: Optional[Elasticsearch] = None
    _async_client: Optional[AsyncElasticsearch] = None

    @classmethod
    def get_client(cls) -> Elasticsearch:
        if cls._client is None:
            cls._init_client()
        return cls._client

    @classmethod
    def _init_client(cls):
        try:
            # 构建ES连接参数
            es_params: Dict[str, Any] = {
                'hosts': [f"{settings.ELASTICSEARCH_SCHEME}://{settings.ELASTICSEARCH_HOST}:{settings.ELASTICSEARCH_PORT}"],
                'verify_certs': settings.ELASTICSEARCH_VERIFY_CERTS
            }

            # 如果提供了用户名和密码，则添加认证信息
            if settings.ELASTICSEARCH_USER and settings.ELASTICSEARCH_PASSWORD:
                es_params['basic_auth'] = (
                    settings.ELASTICSEARCH_USER,
                    settings.ELASTICSEARCH_PASSWORD
                )

            cls._client = Elasticsearch(**es_params)
            # 测试连接
            if cls._client.ping():
                logger.info("成功连接到Elasticsearch")
            else:
                logger.warning("Elasticsearch连接测试失败")
        except ConnectionError as e:
            logger.error(f"Elasticsearch连接错误: {str(e)}")
            raise
        except Exception as e:
            logger.error(f"初始化Elasticsearch客户端时发生错误: {str(e)}")
            raise

    @classmethod
    def get_async_client(cls) -> AsyncElasticsearch:
        if cls._async_client is None:
            cls._init_async_client()
        return cls._async_client

    @classmethod
    def _init_async_client(cls):
        try:
            # 构建异步ES连接参数
            es_params: Dict[str, Any] = {
                'hosts': [f"{settings.ELASTICSEARCH_SCHEME}://{settings.ELASTICSEARCH_HOST}:{settings.ELASTICSEARCH_PORT}"],
                'verify_certs': settings.ELASTICSEARCH_VERIFY_CERTS
            }

            # 如果提供了用户名和密码，则添加认证信息
            if settings.ELASTICSEARCH_USER and settings.ELASTICSEARCH_PASSWORD:
                es_params['basic_auth'] = (
                    settings.ELASTICSEARCH_USER,
                    settings.ELASTICSEARCH_PASSWORD
                )

            cls._async_client = AsyncElasticsearch(**es_params)
            logger.info("成功初始化异步Elasticsearch客户端")
        except Exception as e:
            logger.error(f"初始化异步Elasticsearch客户端时发生错误: {str(e)}")
            raise

    @classmethod
    def close_client(cls):
        if cls._client:
            cls._client.close()
            cls._client = None
            logger.info("Elasticsearch客户端已关闭")

    @classmethod
    def close_async_client(cls):
        if cls._async_client:
            import asyncio
            asyncio.run(cls._async_client.close())
            cls._async_client = None
            logger.info("异步Elasticsearch客户端已关闭")