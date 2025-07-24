import argparse
import asyncio
import json
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional
from elasticsearch.helpers import scan, bulk
from app.utils.elasticsearch import ESClient
from app.config.settings import settings
from app.utils.config_manager import config_manager
from app.config.logging_config import get_logger

# 使用专门的日志器
logger = get_logger('update_country_fields')

class CountryFieldUpdater:
    def __init__(self):
        self.es_client = ESClient.get_client()
        self.index_name = settings.DATA_INDEX
        self.batch_size = 500
        self.stats = {
            'total_processed': 0,
            'total_updated': 0,
            'importer_country_updated': 0,
            'exporter_country_updated': 0,
            'no_change_needed': 0,
            'errors': 0,
            'error_details': []
        }

    def print_separator(self, title: str = ""):
        """打印分隔线"""
        if title:
            print(f"\n{'='*60}")
            print(f" {title}")
            print(f"{'='*60}")
        else:
            print(f"{'='*60}")

    def print_step(self, step_num: int, title: str):
        """打印步骤标题"""
        print(f"\n[步骤 {step_num}] {title}")
        print("-" * 40)

    def map_country_name(self, country_value: Any) -> str:
        """将英文国家名映射为中文国家名"""
        if not country_value:
            return ""
        
        country_str = str(country_value).strip()
        if not country_str:
            return ""
        
        try:
            chinese_name = config_manager.find_chinese_name(country_str)
            return chinese_name
        except Exception as e:
            logger.error(f"国家映射处理失败: {str(e)}")
            return country_str

    def check_index_exists(self) -> bool:
        """检查索引是否存在"""
        try:
            return self.es_client.indices.exists(index=self.index_name)
        except Exception as e:
            logger.error(f"检查索引失败: {str(e)}")
            return False

    def get_total_documents(self) -> int:
        """获取总文档数量"""
        try:
            response = self.es_client.count(index=self.index_name)
            return response['count']
        except Exception as e:
            logger.error(f"获取文档总数失败: {str(e)}")
            return 0

    def scan_and_update_documents(self, dry_run: bool = False, limit: Optional[int] = None) -> Dict[str, Any]:
        """扫描并更新文档"""
        self.print_step(1, "扫描数据库中的文档")
        
        if not self.check_index_exists():
            print(f"❌ 错误：索引 {self.index_name} 不存在")
            return self.stats

        total_docs = self.get_total_documents()
        print(f"📊 数据库中共有 {total_docs} 条记录")
        
        if limit:
            print(f"⚠️  限制处理数量: {limit} 条")

        # 构建查询
        query = {"match_all": {}}
        
        # 扫描所有文档
        print(f"🔍 开始扫描文档...")
        
        try:
            # 使用scan来遍历所有文档
            documents = scan(
                self.es_client,
                query={"query": query},
                index=self.index_name,
                size=self.batch_size,
                scroll='5m'
            )
            
            batch_updates = []
            processed_count = 0
            
            for doc in documents:
                if limit and processed_count >= limit:
                    break
                    
                processed_count += 1
                doc_id = doc['_id']
                source = doc['_source']
                
                # 检查是否需要更新
                needs_update = False
                updates = {}
                
                # 检查进口商所在国家
                importer_country = source.get('进口商所在国家', '')
                if importer_country:
                    mapped_importer_country = self.map_country_name(importer_country)
                    if mapped_importer_country != importer_country:
                        updates['进口商所在国家'] = mapped_importer_country
                        needs_update = True
                        self.stats['importer_country_updated'] += 1
                        logger.debug(f"进口商国家映射: {importer_country} -> {mapped_importer_country}")

                # 检查出口商所在国家
                exporter_country = source.get('出口商所在国家', '')
                if exporter_country:
                    mapped_exporter_country = self.map_country_name(exporter_country)
                    if mapped_exporter_country != exporter_country:
                        updates['出口商所在国家'] = mapped_exporter_country
                        needs_update = True
                        self.stats['exporter_country_updated'] += 1
                        logger.debug(f"出口商国家映射: {exporter_country} -> {mapped_exporter_country}")

                if needs_update:
                    # 添加更新时间
                    updates['updated_at'] = datetime.now().isoformat()
                    
                    # 准备批量更新操作
                    update_action = {
                        '_op_type': 'update',
                        '_index': self.index_name,
                        '_id': doc_id,
                        '_source': {'doc': updates}
                    }
                    batch_updates.append(update_action)
                    self.stats['total_updated'] += 1
                    
                    # 显示更新详情
                    if len(batch_updates) <= 5:  # 只显示前5条详情
                        print(f"  📝 文档 {doc_id[:8]}... 需要更新:")
                        for field, new_value in updates.items():
                            if field != 'updated_at':
                                old_value = source.get(field, '')
                                print(f"    {field}: {old_value} -> {new_value}")
                else:
                    self.stats['no_change_needed'] += 1

                self.stats['total_processed'] += 1

                # 批量执行更新
                if len(batch_updates) >= self.batch_size:
                    if not dry_run:
                        self._execute_batch_update(batch_updates)
                    else:
                        print(f"  🔍 [Dry Run] 准备更新 {len(batch_updates)} 条记录")
                    batch_updates = []

                # 显示进度
                if processed_count % 1000 == 0:
                    print(f"  📊 已处理: {processed_count} / {total_docs if not limit else min(limit, total_docs)} 条记录")

            # 处理剩余的批量更新
            if batch_updates:
                if not dry_run:
                    self._execute_batch_update(batch_updates)
                else:
                    print(f"  🔍 [Dry Run] 准备更新 {len(batch_updates)} 条记录")

            print(f"✅ 文档扫描完成，共处理 {processed_count} 条记录")
            
        except Exception as e:
            logger.error(f"扫描文档失败: {str(e)}")
            self.stats['errors'] += 1
            self.stats['error_details'].append(f"扫描失败: {str(e)}")
            print(f"❌ 扫描失败: {str(e)}")

        return self.stats

    def _execute_batch_update(self, batch_updates: List[Dict[str, Any]]):
        """执行批量更新"""
        try:
            success, failed = bulk(
                self.es_client,
                batch_updates,
                index=self.index_name,
                chunk_size=self.batch_size,
                request_timeout=60
            )
            
            if failed:
                logger.warning(f"批量更新部分失败: {len(failed)} 条")
                self.stats['errors'] += len(failed)
                for failure in failed[:3]:  # 只记录前3个错误
                    self.stats['error_details'].append(str(failure))
            
            print(f"  ✅ 批量更新完成: 成功 {success} 条")
            
        except Exception as e:
            logger.error(f"批量更新失败: {str(e)}")
            self.stats['errors'] += len(batch_updates)
            self.stats['error_details'].append(f"批量更新失败: {str(e)}")
            print(f"  ❌ 批量更新失败: {str(e)}")

    def create_backup(self) -> Optional[str]:
        """创建数据备份"""
        self.print_step(0, "创建数据备份")
        
        try:
            backup_dir = Path("./backups")
            backup_dir.mkdir(exist_ok=True)
            
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            backup_file = backup_dir / f"country_fields_backup_{timestamp}.json"
            
            print(f"📦 正在创建备份文件: {backup_file}")
            
            # 查询所有包含国家字段的文档
            query = {
                "query": {
                    "bool": {
                        "should": [
                            {"exists": {"field": "进口商所在国家"}},
                            {"exists": {"field": "出口商所在国家"}}
                        ],
                        "minimum_should_match": 1
                    }
                },
                "_source": ["进口商所在国家", "出口商所在国家"]
            }
            
            backup_data = []
            documents = scan(
                self.es_client,
                query=query,
                index=self.index_name,
                size=1000
            )
            
            for doc in documents:
                backup_data.append({
                    'id': doc['_id'],
                    'source': doc['_source']
                })
            
            # 保存备份
            with open(backup_file, 'w', encoding='utf-8') as f:
                json.dump(backup_data, f, ensure_ascii=False, indent=2)
            
            print(f"✅ 备份完成: {len(backup_data)} 条记录已保存到 {backup_file}")
            return str(backup_file)
            
        except Exception as e:
            logger.error(f"创建备份失败: {str(e)}")
            print(f"❌ 创建备份失败: {str(e)}")
            return None

    def print_final_report(self, dry_run: bool = False, backup_file: Optional[str] = None):
        """打印最终报告"""
        self.print_separator("更新完成 - 最终报告")
        
        mode = "预览模式 (Dry Run)" if dry_run else "实际更新模式"
        print(f"🔧 运行模式: {mode}")
        
        if backup_file:
            print(f"📦 备份文件: {backup_file}")
        
        print(f"\n📊 处理统计:")
        print(f"  📝 总处理记录: {self.stats['total_processed']} 条")
        print(f"  ✅ 需要更新记录: {self.stats['total_updated']} 条")
        print(f"  🏢 进口商国家更新: {self.stats['importer_country_updated']} 条")
        print(f"  🏭 出口商国家更新: {self.stats['exporter_country_updated']} 条")
        print(f"  ⚪ 无需更新记录: {self.stats['no_change_needed']} 条")
        print(f"  ❌ 错误记录: {self.stats['errors']} 条")
        
        if self.stats['error_details']:
            print(f"\n❌ 错误详情 (前5条):")
            for i, error in enumerate(self.stats['error_details'][:5], 1):
                print(f"  {i}. {error}")
        
        # 计算更新比例
        if self.stats['total_processed'] > 0:
            update_rate = (self.stats['total_updated'] / self.stats['total_processed']) * 100
            print(f"\n📈 更新比例: {update_rate:.2f}%")
        
        if not dry_run and self.stats['total_updated'] > 0:
            print(f"\n🎉 国家字段更新完成！")
            print(f"💡 建议：运行数据验证脚本确认更新结果")
        elif dry_run:
            print(f"\n🔍 预览完成！使用 --execute 参数执行实际更新")

def main():
    parser = argparse.ArgumentParser(description='更新数据库中现有数据的国家字段为中文')
    parser.add_argument('--dry-run', action='store_true', help='仅预览，不执行实际更新')
    parser.add_argument('--execute', action='store_true', help='执行实际更新操作')
    parser.add_argument('--limit', type=int, help='限制处理的记录数量（用于测试）')
    parser.add_argument('--no-backup', action='store_true', help='跳过备份创建')
    parser.add_argument('--reload-config', action='store_true', help='重新加载国家映射配置')
    parser.add_argument('--batch-size', type=int, default=500, help='批量处理大小')
    
    args = parser.parse_args()
    
    # 参数验证
    if not args.dry_run and not args.execute:
        print("❌ 错误：必须指定 --dry-run 或 --execute 参数")
        parser.print_help()
        return
    
    if args.dry_run and args.execute:
        print("❌ 错误：--dry-run 和 --execute 不能同时使用")
        return

    updater = CountryFieldUpdater()
    updater.batch_size = args.batch_size
    
    updater.print_separator("数据库国家字段更新工具")
    print(f"启动时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"运行模式: {'预览模式' if args.dry_run else '实际更新模式'}")
    print(f"数据库索引: {settings.DATA_INDEX}")
    print(f"批量大小: {args.batch_size}")
    
    if args.limit:
        print(f"处理限制: {args.limit} 条记录")

    # 重新加载配置
    if args.reload_config:
        updater.print_step(0, "重新加载国家映射配置")
        try:
            config_manager.reload_all_configs()
            print("✅ 国家映射配置已重新加载")
        except Exception as e:
            print(f"❌ 重新加载配置失败: {str(e)}")
            return

    # 创建备份（仅在实际更新时）
    backup_file = None
    if args.execute and not args.no_backup:
        backup_file = updater.create_backup()
        if not backup_file:
            print("❌ 备份创建失败，为安全起见，停止更新操作")
            return

    # 执行更新
    try:
        stats = updater.scan_and_update_documents(
            dry_run=args.dry_run,
            limit=args.limit
        )
        
        # 打印最终报告
        updater.print_final_report(
            dry_run=args.dry_run,
            backup_file=backup_file
        )
        
    except KeyboardInterrupt:
        print(f"\n⚠️  操作被用户中断")
        updater.print_final_report(
            dry_run=args.dry_run,
            backup_file=backup_file
        )
    except Exception as e:
        print(f"\n❌ 更新过程中发生错误: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()