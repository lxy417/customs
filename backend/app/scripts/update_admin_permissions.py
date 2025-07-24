"""
更新admin角色权限脚本：确保admin角色拥有配置管理权限
"""
import sys
import os

# 添加backend目录到Python路径，这样可以导入app模块
backend_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, backend_dir)

from elasticsearch import Elasticsearch
from app.config.settings import settings
from app.services.role_service import RoleService, DEFAULT_ROLES, PERMISSIONS
from datetime import datetime
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def update_admin_permissions():
    """更新admin角色权限，确保包含配置管理权限"""
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
        
        logger.info("开始更新admin角色权限...")
        
        # 1. 检查admin角色是否存在
        admin_role = role_service.get_role_by_id("admin")
        if not admin_role:
            logger.error("admin角色不存在，请先运行角色迁移脚本")
            return
        
        logger.info(f"当前admin角色权限: {admin_role.permissions}")
        
        # 2. 获取所有可用权限
        all_permissions = list(PERMISSIONS.keys())
        logger.info(f"所有可用权限: {all_permissions}")
        
        # 3. 检查是否需要更新
        missing_permissions = [p for p in all_permissions if p not in admin_role.permissions]
        
        if not missing_permissions:
            logger.info("admin角色已拥有所有权限，无需更新")
            return
        
        logger.info(f"admin角色缺少的权限: {missing_permissions}")
        
        # 4. 更新admin角色权限
        role_index = f"{settings.ES_INDEX_PREFIX}_roles"
        update_body = {
            "doc": {
                "permissions": all_permissions,
                "updated_at": datetime.utcnow()
            }
        }
        
        try:
            es.update(
                index=role_index,
                id="admin",
                body=update_body
            )
            logger.info("成功更新admin角色权限")
        except Exception as e:
            logger.error(f"更新admin角色权限失败: {e}")
            return
        
        # 5. 验证更新结果
        updated_admin_role = role_service.get_role_by_id("admin")
        if updated_admin_role:
            logger.info(f"更新后admin角色权限: {updated_admin_role.permissions}")
            
            # 检查配置管理权限
            config_permissions = ["config_manage", "config_view"]
            has_config_permissions = all(p in updated_admin_role.permissions for p in config_permissions)
            
            if has_config_permissions:
                logger.info("✅ admin角色已成功获得配置管理权限")
            else:
                logger.warning("⚠️ admin角色仍缺少配置管理权限")
        else:
            logger.error("无法验证更新结果")
        
        # 6. 检查并更新具有admin角色的用户
        logger.info("检查具有admin角色的用户...")
        
        # 查询所有用户
        user_index = settings.USER_INDEX if hasattr(settings, 'USER_INDEX') else "customs_users"
        
        try:
            query = {
                "query": {
                    "term": {"role_id": "admin"}
                },
                "size": 100
            }
            
            response = es.search(index=user_index, body=query)
            admin_users = response["hits"]["hits"]
            
            logger.info(f"找到 {len(admin_users)} 个admin用户")
            
            for user_doc in admin_users:
                user_data = user_doc["_source"]
                username = user_data.get("username")
                logger.info(f"admin用户: {username}")
                
        except Exception as e:
            logger.warning(f"查询admin用户失败: {e}")
        
        logger.info("admin角色权限更新完成！")
        
    except Exception as e:
        logger.error(f"更新过程中发生错误: {e}")
        raise

def verify_permissions():
    """验证权限配置"""
    logger.info("验证权限配置...")
    
    # 检查所有权限常量
    logger.info("当前定义的权限:")
    for perm_key, perm_desc in PERMISSIONS.items():
        logger.info(f"  {perm_key}: {perm_desc}")
    
    # 检查默认角色配置
    logger.info("默认角色配置:")
    for role_id, role_data in DEFAULT_ROLES.items():
        logger.info(f"  {role_id} ({role_data['name']}): {role_data['permissions']}")

if __name__ == "__main__":
    print("选择操作:")
    print("1. 更新admin角色权限")
    print("2. 验证权限配置")
    print("3. 执行完整更新")
    
    choice = input("请输入选择 (1/2/3): ").strip()
    
    if choice == "1":
        update_admin_permissions()
    elif choice == "2":
        verify_permissions()
    elif choice == "3":
        verify_permissions()
        update_admin_permissions()
    else:
        print("无效选择")