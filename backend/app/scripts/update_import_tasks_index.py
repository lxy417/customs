"""
执行索引更新
python d:\customs\backend\app\scripts\update_import_tasks_index.py
显示索引信息
python d:\customs\backend\app\scripts\update_import_tasks_index.py --info
备份索引映射
python d:\customs\backend\app\scripts\update_import_tasks_index.py --backup
试运行（不执行实际更新）
python d:\customs\backend\app\scripts\update_import_tasks_index.py --dry-run
索引更新脚本：为导入任务索引添加回滚相关字段和优化索引结构
添加回滚相关字段：imported_document_ids, rollback_status, rollback_at, rollback_by, rollback_details
同时优化索引性能和添加缺失字段
"""
import sys
import os

# 添加backend目录到Python路径，这样可以导入app模块
backend_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, backend_dir)

from elasticsearch import Elasticsearch
from app.config.settings import settings
import logging
from datetime import datetime

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def update_import_tasks_index():
    """更新导入任务索引，添加回滚相关字段和优化索引结构"""
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
        import_tasks_index = f"{settings.DATA_INDEX}_import_tasks"
        
        logger.info(f"开始更新导入任务索引: {import_tasks_index}")
        
        # 1. 检查索引是否存在
        if not es.indices.exists(index=import_tasks_index):
            logger.warning(f"索引 {import_tasks_index} 不存在，将创建新索引")
            create_new_index(es, import_tasks_index)
            return
        
        # 2. 获取当前索引映射
        logger.info("获取当前索引映射...")
        try:
            current_mapping = es.indices.get_mapping(index=import_tasks_index)
            current_properties = current_mapping[import_tasks_index]["mappings"]["properties"]
            logger.info(f"当前索引包含 {len(current_properties)} 个字段")
        except Exception as e:
            logger.error(f"获取当前索引映射失败: {e}")
            return
        
        # 3. 定义需要添加的新字段
        new_fields = {
            "imported_document_ids": {"type": "keyword"},  # 导入的文档ID列表
            "rollback_status": {"type": "keyword"},  # none, pending, completed, failed
            "rollback_at": {"type": "date"},  # 回滚时间
            "rollback_by": {"type": "keyword"},  # 回滚操作用户
            "rollback_details": {"type": "object"},  # 回滚详情
            "updated_at": {"type": "date"}  # 更新时间
        }
        
        # 4. 检查哪些字段需要添加
        fields_to_add = {}
        for field_name, field_config in new_fields.items():
            if field_name not in current_properties:
                fields_to_add[field_name] = field_config
                logger.info(f"需要添加字段: {field_name}")
            else:
                logger.info(f"字段已存在: {field_name}")
        
        # 5. 更新索引映射
        if fields_to_add:
            logger.info(f"更新索引映射，添加 {len(fields_to_add)} 个新字段...")
            new_mapping = {"properties": fields_to_add}
            
            try:
                es.indices.put_mapping(
                    index=import_tasks_index,
                    body=new_mapping
                )
                logger.info("索引映射更新成功")
            except Exception as e:
                logger.error(f"更新索引映射失败: {e}")
                return
        else:
            logger.info("所有字段已存在，无需更新映射")
        
        # 6. 查询所有现有的导入任务并更新默认值
        logger.info("查询现有的导入任务...")
        
        # 使用scroll API处理大量数据
        query = {
            "query": {"match_all": {}},
            "size": 100
        }
        
        try:
            response = es.search(
                index=import_tasks_index, 
                body=query,
                scroll='5m'
            )
            
            scroll_id = response['_scroll_id']
            total_hits = response['hits']['total']['value']
            logger.info(f"找到 {total_hits} 个导入任务")
            
            updated_count = 0
            batch_count = 0
            
            while True:
                hits = response['hits']['hits']
                if not hits:
                    break
                
                batch_count += 1
                logger.info(f"处理第 {batch_count} 批，包含 {len(hits)} 个任务")
                
                # 批量更新任务
                for task_doc in hits:
                    task_data = task_doc["_source"]
                    task_id = task_data.get("task_id", "未知")
                    
                    # 准备更新文档
                    update_doc = {}
                    
                    # 添加缺失的回滚相关字段
                    if "rollback_status" not in task_data:
                        update_doc["rollback_status"] = "none"
                    
                    if "imported_document_ids" not in task_data:
                        update_doc["imported_document_ids"] = []
                    
                    if "updated_at" not in task_data:
                        update_doc["updated_at"] = datetime.now().isoformat()
                    
                    # 确保其他必要字段存在
                    if "duplicate_count" not in task_data:
                        update_doc["duplicate_count"] = 0
                    
                    if "original_total_count" not in task_data:
                        update_doc["original_total_count"] = task_data.get("total_count", 0)
                    
                    if update_doc:
                        try:
                            es.update(
                                index=import_tasks_index,
                                id=task_doc["_id"],
                                body={"doc": update_doc}
                            )
                            updated_count += 1
                            logger.debug(f"成功更新任务 {task_id}: 添加字段 {list(update_doc.keys())}")
                        except Exception as e:
                            logger.error(f"更新任务 {task_id} 失败: {e}")
                
                # 获取下一批数据
                try:
                    response = es.scroll(scroll_id=scroll_id, scroll='5m')
                except Exception as e:
                    logger.error(f"滚动查询失败: {e}")
                    break
            
            # 清理scroll
            try:
                es.clear_scroll(scroll_id=scroll_id)
            except:
                pass
            
            logger.info(f"索引更新完成！共更新 {updated_count} 个导入任务")
            
        except Exception as e:
            logger.error(f"查询和更新导入任务失败: {e}")
            return
        
        # 7. 验证更新结果
        logger.info("验证更新结果...")
        verify_index_update(es, import_tasks_index)
        
        # 8. 优化索引性能
        logger.info("优化索引性能...")
        optimize_index(es, import_tasks_index)
        
    except Exception as e:
        logger.error(f"索引更新过程中发生错误: {e}")
        raise

def create_new_index(es, index_name):
    """创建新的导入任务索引"""
    logger.info(f"创建新索引: {index_name}")
    
    mapping = {
        "mappings": {
            "properties": {
                "task_id": {"type": "keyword"},
                "original_filename": {"type": "text"},
                "user_id": {"type": "keyword"},
                "status": {"type": "keyword"},  # processing, completed, failed, rolled_back
                "total_files": {"type": "integer"},
                "success_count": {"type": "integer"},
                "failed_count": {"type": "integer"},
                "duplicate_count": {"type": "integer"},
                "original_total_count": {"type": "integer"},
                "total_count": {"type": "integer"},
                "customs_codes": {"type": "keyword"},
                "start_date": {"type": "date"},
                "end_date": {"type": "date"},
                "created_at": {"type": "date"},
                "completed_at": {"type": "date"},
                "updated_at": {"type": "date"},
                "processed_files": {"type": "object"},
                "error_details": {"type": "object"},
                "processing_options": {"type": "object"},
                # 回滚相关字段
                "imported_document_ids": {"type": "keyword"},
                "rollback_status": {"type": "keyword"},  # none, pending, completed, failed
                "rollback_at": {"type": "date"},
                "rollback_by": {"type": "keyword"},
                "rollback_details": {"type": "object"}
            }
        },
        "settings": {
            "number_of_shards": 1,
            "number_of_replicas": 0,
            "refresh_interval": "1s"
        }
    }
    
    try:
        es.indices.create(index=index_name, body=mapping)
        logger.info(f"成功创建索引: {index_name}")
    except Exception as e:
        logger.error(f"创建索引失败: {e}")
        raise

def verify_index_update(es, index_name):
    """验证索引更新结果"""
    try:
        # 查询几个任务验证
        sample_query = {
            "query": {"match_all": {}},
            "size": 3
        }
        response = es.search(index=index_name, body=sample_query)
        
        logger.info("验证样本任务:")
        for task_doc in response["hits"]["hits"]:
            task_data = task_doc["_source"]
            task_id = task_data.get("task_id", "未知")
            rollback_status = task_data.get("rollback_status", "缺失")
            imported_document_ids = task_data.get("imported_document_ids", "缺失")
            
            logger.info(f"任务 {task_id}: rollback_status={rollback_status}, imported_document_ids={len(imported_document_ids) if isinstance(imported_document_ids, list) else imported_document_ids}")
    
    except Exception as e:
        logger.error(f"验证索引更新结果失败: {e}")

def optimize_index(es, index_name):
    """优化索引性能"""
    try:
        # 刷新索引
        es.indices.refresh(index=index_name)
        logger.info("索引刷新完成")
        
        # 强制合并段（可选，对于小索引有用）
        es.indices.forcemerge(index=index_name, max_num_segments=1)
        logger.info("索引段合并完成")
        
    except Exception as e:
        logger.warning(f"索引优化失败（可忽略）: {e}")

def show_index_info(es, index_name):
    """显示索引信息"""
    try:
        # 获取索引统计信息
        stats = es.indices.stats(index=index_name)
        doc_count = stats['indices'][index_name]['total']['docs']['count']
        size_in_bytes = stats['indices'][index_name]['total']['store']['size_in_bytes']
        
        logger.info(f"索引统计信息:")
        logger.info(f"  文档数量: {doc_count}")
        logger.info(f"  索引大小: {size_in_bytes / 1024 / 1024:.2f} MB")
        
        # 获取索引映射信息
        mapping = es.indices.get_mapping(index=index_name)
        properties = mapping[index_name]["mappings"]["properties"]
        
        logger.info(f"索引字段 ({len(properties)} 个):")
        for field_name, field_config in sorted(properties.items()):
            field_type = field_config.get("type", "object")
            logger.info(f"  {field_name}: {field_type}")
            
    except Exception as e:
        logger.error(f"获取索引信息失败: {e}")

def backup_index_mapping(es, index_name):
    """备份索引映射"""
    try:
        mapping = es.indices.get_mapping(index=index_name)
        
        # 保存到文件
        import json
        backup_file = f"backup_mapping_{index_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        with open(backup_file, 'w', encoding='utf-8') as f:
            json.dump(mapping, f, indent=2, ensure_ascii=False)
        
        logger.info(f"索引映射已备份到: {backup_file}")
        
    except Exception as e:
        logger.warning(f"备份索引映射失败: {e}")

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='导入任务索引更新脚本')
    parser.add_argument('--info', action='store_true', help='显示索引信息')
    parser.add_argument('--backup', action='store_true', help='备份索引映射')
    parser.add_argument('--dry-run', action='store_true', help='试运行（不执行实际更新）')
    args = parser.parse_args()
    
    try:
        # 构建Elasticsearch连接
        es_url = f"{settings.ELASTICSEARCH_SCHEME}://{settings.ELASTICSEARCH_HOST}:{settings.ELASTICSEARCH_PORT}"
        
        if settings.ELASTICSEARCH_USER and settings.ELASTICSEARCH_PASSWORD:
            es = Elasticsearch(
                [es_url],
                basic_auth=(settings.ELASTICSEARCH_USER, settings.ELASTICSEARCH_PASSWORD),
                verify_certs=settings.ELASTICSEARCH_VERIFY_CERTS
            )
        else:
            es = Elasticsearch([es_url])
        
        index_name = f"{settings.DATA_INDEX}_import_tasks"
        
        if args.info:
            show_index_info(es, index_name)
        elif args.backup:
            backup_index_mapping(es, index_name)
        elif args.dry_run:
            logger.info("试运行模式 - 不会执行实际更新")
            logger.info(f"将要更新的索引: {index_name}")
            # 这里可以添加试运行逻辑
        else:
            # 备份映射
            backup_index_mapping(es, index_name)
            # 执行更新
            update_import_tasks_index()
            
    except Exception as e:
        logger.error(f"脚本执行失败: {e}")
        sys.exit(1)