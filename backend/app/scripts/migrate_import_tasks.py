"""
数据库迁移脚本：为导入任务索引添加新字段
添加 duplicate_count 和 original_total_count 字段
"""
import sys
import os

# 添加backend目录到Python路径，这样可以导入app模块
backend_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, backend_dir)

from elasticsearch import Elasticsearch
from app.config.settings import settings
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def migrate_import_tasks():
    """为导入任务索引添加新字段"""
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
        
        # 获取导入任务索引名
        import_tasks_index = f"customs_data_import_tasks"
        
        logger.info(f"开始迁移导入任务索引: {import_tasks_index}")
        
        # 1. 检查索引是否存在
        if not es.indices.exists(index=import_tasks_index):
            logger.warning(f"索引 {import_tasks_index} 不存在，无需迁移")
            return
        
        # 2. 更新索引映射，添加新字段
        logger.info("更新索引映射，添加新字段...")
        new_mapping = {
            "properties": {
                "duplicate_count": {"type": "integer"},
                "original_total_count": {"type": "integer"}
            }
        }
        
        try:
            es.indices.put_mapping(
                index=import_tasks_index,
                body=new_mapping
            )
            logger.info("索引映射更新成功")
        except Exception as e:
            logger.error(f"更新索引映射失败: {e}")
            # 继续执行，因为字段可能已经存在
        
        # 3. 查询所有现有的导入任务
        logger.info("查询现有的导入任务...")
        
        query = {
            "query": {"match_all": {}},
            "size": 1000  # 假设导入任务不会太多，如果很多需要使用scroll
        }
        
        try:
            response = es.search(index=import_tasks_index, body=query)
            tasks = response["hits"]["hits"]
            logger.info(f"找到 {len(tasks)} 个导入任务")
        except Exception as e:
            logger.error(f"查询导入任务失败: {e}")
            return
        
        # 4. 为每个任务添加新字段
        migrated_count = 0
        for task_doc in tasks:
            task_data = task_doc["_source"]
            task_id = task_data.get("task_id", "未知")
            
            # 检查是否已经有新字段
            has_duplicate_count = "duplicate_count" in task_data
            has_original_total_count = "original_total_count" in task_data
            
            if has_duplicate_count and has_original_total_count:
                logger.info(f"任务 {task_id} 已有新字段，跳过迁移")
                continue
            
            # 准备更新文档
            update_doc = {}
            
            if not has_duplicate_count:
                update_doc["duplicate_count"] = 0  # 默认值为0
            
            if not has_original_total_count:
                # 如果有total_count，使用它作为original_total_count的默认值
                # 否则使用0
                original_total = task_data.get("total_count", 0)
                update_doc["original_total_count"] = original_total
            
            if update_doc:
                try:
                    es.update(
                        index=import_tasks_index,
                        id=task_doc["_id"],
                        body={"doc": update_doc}
                    )
                    migrated_count += 1
                    logger.info(f"成功迁移任务 {task_id}: 添加字段 {list(update_doc.keys())}")
                except Exception as e:
                    logger.error(f"迁移任务 {task_id} 失败: {e}")
        
        logger.info(f"迁移完成！共迁移 {migrated_count} 个导入任务")
        
        # 5. 验证迁移结果
        logger.info("验证迁移结果...")
        try:
            # 查询几个任务验证
            sample_query = {
                "query": {"match_all": {}},
                "size": 5
            }
            response = es.search(index=import_tasks_index, body=sample_query)
            
            for task_doc in response["hits"]["hits"]:
                task_data = task_doc["_source"]
                task_id = task_data.get("task_id", "未知")
                duplicate_count = task_data.get("duplicate_count", "缺失")
                original_total_count = task_data.get("original_total_count", "缺失")
                
                logger.info(f"任务 {task_id}: duplicate_count={duplicate_count}, original_total_count={original_total_count}")
        
        except Exception as e:
            logger.error(f"验证迁移结果失败: {e}")
        
        # 6. 显示更新后的索引映射信息
        try:
            mapping = es.indices.get_mapping(index=import_tasks_index)
            properties = mapping[import_tasks_index]["mappings"]["properties"]
            
            logger.info("当前索引字段:")
            for field_name, field_config in properties.items():
                field_type = field_config.get("type", "object")
                logger.info(f"  {field_name}: {field_type}")
                
        except Exception as e:
            logger.error(f"获取索引映射信息失败: {e}")
        
    except Exception as e:
        logger.error(f"迁移过程中发生错误: {e}")
        raise

def rollback_migration():
    """回滚迁移（可选功能）"""
    logger.warning("注意：Elasticsearch不支持删除字段，回滚需要重建索引")
    logger.info("如需回滚，请手动备份数据后重建索引")

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='导入任务索引迁移脚本')
    parser.add_argument('--rollback', action='store_true', help='显示回滚信息')
    args = parser.parse_args()
    
    if args.rollback:
        rollback_migration()
    else:
        migrate_import_tasks()