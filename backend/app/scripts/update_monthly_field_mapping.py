#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
更新月度字段映射脚本
将 Elasticsearch 中"月度"字段的类型从 long 更改为 date
"""

import os
import sys
import logging
from datetime import datetime

# 添加项目根目录到 Python 路径
backend_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, backend_dir)

from elasticsearch import Elasticsearch
from app.config.settings import settings
from app.config.elasticsearch_mappings import CUSTOMS_DATA_MAPPING

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def update_monthly_field_mapping():
    """更新月度字段映射从 long 到 date"""
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
        
        current_index = settings.DATA_INDEX
        temp_index = f"{current_index}_temp_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        backup_index = f"{current_index}_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        logger.info(f"开始更新索引: {current_index}")
        logger.info(f"临时索引: {temp_index}")
        logger.info(f"备份索引: {backup_index}")
        
        # 检查原索引是否存在
        if not es.indices.exists(index=current_index):
            logger.error(f"索引 {current_index} 不存在")
            return False
        
        # 获取当前映射
        current_mapping = es.indices.get_mapping(index=current_index)
        current_properties = current_mapping[current_index]['mappings']['properties']
        
        # 检查月度字段当前类型
        if '月度' in current_properties:
            current_type = current_properties['月度'].get('type')
            logger.info(f"月度字段当前类型: {current_type}")
            
            if current_type == 'date':
                logger.info("月度字段已经是 date 类型，无需更新")
                return True
        else:
            logger.warning("月度字段不存在于当前映射中")
        
        # 步骤1: 创建临时索引，使用新的映射
        logger.info("步骤1: 创建临时索引...")
        es.indices.create(index=temp_index, body=CUSTOMS_DATA_MAPPING)
        logger.info("临时索引创建成功")
        
        # 步骤2: 重新索引数据到临时索引
        logger.info("步骤2: 开始重新索引数据...")
        
        reindex_body = {
            "source": {
                "index": current_index
            },
            "dest": {
                "index": temp_index
            }
        }
        
        # 执行重新索引
        reindex_result = es.reindex(body=reindex_body, wait_for_completion=True)
        
        if reindex_result.get('failures'):
            logger.error(f"重新索引过程中出现错误: {reindex_result['failures']}")
            # 清理临时索引
            es.indices.delete(index=temp_index)
            return False
        
        total_docs = reindex_result.get('total', 0)
        logger.info(f"重新索引完成，处理了 {total_docs} 条记录")
        
        # 步骤3: 创建原索引的备份别名
        logger.info("步骤3: 创建备份别名...")
        es.indices.put_alias(index=current_index, name=backup_index)
        logger.info(f"备份别名创建成功: {backup_index}")
        
        # 步骤4: 删除原索引
        logger.info("步骤4: 删除原索引...")
        es.indices.delete(index=current_index)
        logger.info("原索引删除成功")
        
        # 步骤5: 将临时索引重命名为原索引名
        logger.info("步骤5: 重命名临时索引...")
        es.indices.put_alias(index=temp_index, name=current_index)
        logger.info("索引重命名成功")
        
        # 步骤6: 验证新映射
        logger.info("步骤6: 验证新映射...")
        new_mapping = es.indices.get_mapping(index=current_index)
        new_monthly_type = new_mapping[current_index]['mappings']['properties']['月度']['type']
        logger.info(f"更新后月度字段类型: {new_monthly_type}")
        
        if new_monthly_type == 'date':
            logger.info("✅ 月度字段映射更新成功！")
            logger.info(f"📁 备份索引: {backup_index}")
            logger.info("💡 如果确认更新无问题，可以删除备份索引")
            return True
        else:
            logger.error("❌ 月度字段映射更新失败")
            return False
            
    except Exception as e:
        logger.error(f"更新月度字段映射失败: {str(e)}", exc_info=True)
        # 清理可能创建的临时索引
        try:
            if 'temp_index' in locals() and es.indices.exists(index=temp_index):
                es.indices.delete(index=temp_index)
                logger.info("已清理临时索引")
        except:
            pass
        return False

def show_index_info():
    """显示索引信息"""
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
        
        current_index = settings.DATA_INDEX
        
        if not es.indices.exists(index=current_index):
            print(f"❌ 索引 {current_index} 不存在")
            return
        
        # 获取索引信息
        mapping = es.indices.get_mapping(index=current_index)
        stats = es.indices.stats(index=current_index)
        
        print(f"\n📊 索引信息")
        print(f"索引名称: {current_index}")
        print(f"文档数量: {stats['indices'][current_index]['total']['docs']['count']:,}")
        print(f"索引大小: {stats['indices'][current_index]['total']['store']['size_in_bytes']:,} bytes")
        
        # 检查月度字段
        properties = mapping[current_index]['mappings']['properties']
        if '月度' in properties:
            monthly_field = properties['月度']
            field_type = monthly_field.get('type')
            print(f"月度字段类型: {field_type}")
            if 'format' in monthly_field:
                print(f"月度字段格式: {monthly_field['format']}")
            
            # 根据类型显示状态
            if field_type == 'date':
                print("✅ 月度字段已是 date 类型")
            elif field_type == 'long':
                print("⚠️  月度字段是 long 类型，需要更新")
            else:
                print(f"❓ 月度字段类型未知: {field_type}")
        else:
            print("❌ 月度字段不存在")
            
    except Exception as e:
        print(f"❌ 获取索引信息失败: {str(e)}")

def backup_mapping():
    """备份当前映射"""
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
        
        current_index = settings.DATA_INDEX
        
        if not es.indices.exists(index=current_index):
            print(f"❌ 索引 {current_index} 不存在")
            return
        
        # 获取当前映射
        mapping = es.indices.get_mapping(index=current_index)
        
        # 保存到文件
        backup_filename = f"backup_mapping_{current_index}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        import json
        with open(backup_filename, 'w', encoding='utf-8') as f:
            json.dump(mapping, f, ensure_ascii=False, indent=2)
        
        print(f"✅ 映射已备份到: {backup_filename}")
        
    except Exception as e:
        print(f"❌ 备份映射失败: {str(e)}")

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='更新月度字段映射脚本')
    parser.add_argument('--info', action='store_true', help='显示索引信息')
    parser.add_argument('--backup', action='store_true', help='备份当前映射')
    parser.add_argument('--dry-run', action='store_true', help='试运行（仅显示信息）')
    args = parser.parse_args()
    
    print("🔧 月度字段映射更新工具")
    print("=" * 50)
    
    if args.info or args.dry_run:
        show_index_info()
    elif args.backup:
        backup_mapping()
    else:
        # 执行更新
        print("⚠️  警告：此操作将修改索引映射，建议先备份数据")
        print("📋 操作步骤：")
        print("   1. 创建临时索引（使用新映射）")
        print("   2. 重新索引数据到临时索引")
        print("   3. 创建原索引备份")
        print("   4. 删除原索引")
        print("   5. 重命名临时索引为原索引名")
        print("   6. 验证新映射")
        print()
        
        confirm = input("确认继续？(y/N): ")
        if confirm.lower() == 'y':
            success = update_monthly_field_mapping()
            if success:
                print("\n🎉 月度字段映射更新成功！")
            else:
                print("\n💥 月度字段映射更新失败！")
        else:
            print("❌ 操作已取消")