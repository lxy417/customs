"""
数据库迁移脚本：将用户的is_admin字段转换为role_id
"""
import sys
import os

# 添加backend目录到Python路径，这样可以导入app模块
backend_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, backend_dir)

from elasticsearch import Elasticsearch
from app.config.settings import settings
from app.services.role_service import RoleService, DEFAULT_ROLES
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def migrate_users_to_roles():
    """将现有用户的is_admin字段转换为role_id"""
    try:
        # 构建Elasticsearch URL
        es_url = f"{settings.ELASTICSEARCH_SCHEME}://{settings.ELASTICSEARCH_HOST}:{settings.ELASTICSEARCH_PORT}"
        
        # 初始化Elasticsearch连接
        if settings.ELASTICSEARCH_USER and settings.ELASTICSEARCH_PASSWORD:
            es = Elasticsearch(
                [es_url],
                basic_auth=(settings.ELASTICSEARCH_USER, settings.ELASTICSEARCH_PASSWORD),
                verify_certs=settings.ELASTICSEARCH_VERIFY_CERTS
            )
        else:
            es = Elasticsearch([es_url])
            
        role_service = RoleService()
        
        # 1. 创建默认角色
        logger.info("创建默认角色...")
        for role_id, role_data in DEFAULT_ROLES.items():
            try:
                existing_role = role_service.get_role_by_id(role_id)
                if existing_role:
                    logger.info(f"角色 {role_data['name']} 已存在，跳过创建")
                    continue
                
                # 注意：RoleService的_create_default_roles()方法已经会自动创建默认角色
                # 这里只是确认角色已经存在
                logger.info(f"角色 {role_data['name']} 已通过RoleService创建")
            except Exception as e:
                logger.error(f"检查角色 {role_data['name']} 时出错: {e}")
        
        # 2. 迁移现有用户
        logger.info("开始迁移现有用户...")
        
        # 查询所有用户
        query = {
            "query": {"match_all": {}},
            "size": 1000
        }
        
        # 使用正确的用户索引名
        user_index = settings.USER_INDEX if hasattr(settings, 'USER_INDEX') else "customs_users"
        
        try:
            response = es.search(index=user_index, body=query)
            users = response["hits"]["hits"]
        except Exception as e:
            logger.error(f"查询用户索引失败: {e}")
            logger.info("尝试使用 'users' 索引...")
            try:
                response = es.search(index="users", body=query)
                users = response["hits"]["hits"]
            except Exception as e2:
                logger.error(f"查询 'users' 索引也失败: {e2}")
                return
        
        migrated_count = 0
        for user_doc in users:
            user_data = user_doc["_source"]
            username = user_data.get("username")
            
            # 检查是否已经有role_id字段
            if "role_id" in user_data:
                logger.info(f"用户 {username} 已有role_id，跳过迁移")
                continue
            
            # 根据is_admin字段设置role_id
            is_admin = user_data.get("is_admin", False)
            role_id = "admin" if is_admin else "user"
            
            # 更新用户文档
            update_body = {
                "doc": {
                    "role_id": role_id,
                    "additional_permissions": []  # 初始化额外权限为空列表
                }
            }
            
            try:
                es.update(
                    index=user_index,
                    id=user_doc["_id"],
                    body=update_body
                )
                migrated_count += 1
                logger.info(f"成功迁移用户 {username}: is_admin={is_admin} -> role_id={role_id}")
            except Exception as e:
                logger.error(f"迁移用户 {username} 失败: {e}")
        
        logger.info(f"迁移完成！共迁移 {migrated_count} 个用户")
        
        # 3. 验证迁移结果
        logger.info("验证迁移结果...")
        try:
            response = es.search(index=user_index, body={"query": {"match_all": {}}})
            for user_doc in response["hits"]["hits"]:
                user_data = user_doc["_source"]
                username = user_data.get("username")
                role_id = user_data.get("role_id", "未设置")
                logger.info(f"用户 {username}: role_id={role_id}")
        except Exception as e:
            logger.error(f"验证迁移结果失败: {e}")
        
    except Exception as e:
        logger.error(f"迁移过程中发生错误: {e}")
        raise

if __name__ == "__main__":
    migrate_users_to_roles()