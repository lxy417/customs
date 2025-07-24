import argparse
from datetime import datetime
from typing import Dict, List, Any
from collections import Counter
from elasticsearch.helpers import scan
from app.utils.elasticsearch import ESClient
from app.config.settings import settings
from app.utils.config_manager import config_manager

class CountryUpdateVerifier:
    def __init__(self):
        self.es_client = ESClient.get_client()
        self.index_name = settings.DATA_INDEX

    def print_separator(self, title: str = ""):
        """打印分隔线"""
        if title:
            print(f"\n{'='*60}")
            print(f" {title}")
            print(f"{'='*60}")
        else:
            print(f"{'='*60}")

    def get_country_statistics(self, limit: int = None) -> Dict[str, Any]:
        """获取国家字段统计信息"""
        print("🔍 正在分析国家字段数据...")
        
        importer_countries = Counter()
        exporter_countries = Counter()
        total_records = 0
        
        # 构建查询
        query = {"match_all": {}}
        
        try:
            documents = scan(
                self.es_client,
                query={"query": query},
                index=self.index_name,
                size=1000,
                _source=["进口商所在国家", "出口商所在国家"]
            )
            
            for doc in documents:
                if limit and total_records >= limit:
                    break
                    
                source = doc['_source']
                total_records += 1
                
                # 统计进口商国家
                importer_country = source.get('进口商所在国家', '')
                if importer_country:
                    importer_countries[importer_country] += 1
                
                # 统计出口商国家
                exporter_country = source.get('出口商所在国家', '')
                if exporter_country:
                    exporter_countries[exporter_country] += 1
                
                if total_records % 10000 == 0:
                    print(f"  已分析 {total_records} 条记录...")
            
            return {
                'total_records': total_records,
                'importer_countries': dict(importer_countries),
                'exporter_countries': dict(exporter_countries),
                'unique_importer_countries': len(importer_countries),
                'unique_exporter_countries': len(exporter_countries)
            }
            
        except Exception as e:
            print(f"❌ 分析失败: {str(e)}")
            return {}

    def check_chinese_conversion(self, stats: Dict[str, Any]) -> Dict[str, Any]:
        """检查中文转换情况"""
        print("\n🔍 检查中文转换情况...")
        
        def is_chinese(text: str) -> bool:
            """简单检查是否包含中文字符"""
            return any('\u4e00' <= char <= '\u9fff' for char in text)
        
        def is_english_country(text: str) -> bool:
            """检查是否为英文国家名"""
            # 常见的英文国家名模式
            english_patterns = [
                'United', 'States', 'Kingdom', 'Republic', 'Federation',
                'India', 'China', 'Japan', 'Korea', 'Thailand', 'Vietnam',
                'Germany', 'France', 'Italy', 'Spain', 'Belgium'
            ]
            return any(pattern.lower() in text.lower() for pattern in english_patterns)
        
        analysis = {
            'importer_analysis': {
                'chinese_countries': [],
                'english_countries': [],
                'other_countries': [],
                'chinese_count': 0,
                'english_count': 0,
                'total_records_with_chinese': 0,
                'total_records_with_english': 0
            },
            'exporter_analysis': {
                'chinese_countries': [],
                'english_countries': [],
                'other_countries': [],
                'chinese_count': 0,
                'english_count': 0,
                'total_records_with_chinese': 0,
                'total_records_with_english': 0
            }
        }
        
        # 分析进口商国家
        for country, count in stats.get('importer_countries', {}).items():
            if is_chinese(country):
                analysis['importer_analysis']['chinese_countries'].append((country, count))
                analysis['importer_analysis']['chinese_count'] += 1
                analysis['importer_analysis']['total_records_with_chinese'] += count
            elif is_english_country(country):
                analysis['importer_analysis']['english_countries'].append((country, count))
                analysis['importer_analysis']['english_count'] += 1
                analysis['importer_analysis']['total_records_with_english'] += count
            else:
                analysis['importer_analysis']['other_countries'].append((country, count))
        
        # 分析出口商国家
        for country, count in stats.get('exporter_countries', {}).items():
            if is_chinese(country):
                analysis['exporter_analysis']['chinese_countries'].append((country, count))
                analysis['exporter_analysis']['chinese_count'] += 1
                analysis['exporter_analysis']['total_records_with_chinese'] += count
            elif is_english_country(country):
                analysis['exporter_analysis']['english_countries'].append((country, count))
                analysis['exporter_analysis']['english_count'] += 1
                analysis['exporter_analysis']['total_records_with_english'] += count
            else:
                analysis['exporter_analysis']['other_countries'].append((country, count))
        
        return analysis

    def print_verification_report(self, stats: Dict[str, Any], analysis: Dict[str, Any]):
        """打印验证报告"""
        self.print_separator("国家字段验证报告")
        
        print(f"📊 数据概览:")
        print(f"  总记录数: {stats.get('total_records', 0):,}")
        print(f"  唯一进口商国家数: {stats.get('unique_importer_countries', 0)}")
        print(f"  唯一出口商国家数: {stats.get('unique_exporter_countries', 0)}")
        
        # 进口商国家分析
        print(f"\n🏢 进口商所在国家分析:")
        imp_analysis = analysis['importer_analysis']
        print(f"  中文国家名: {imp_analysis['chinese_count']} 种 ({imp_analysis['total_records_with_chinese']:,} 条记录)")
        print(f"  英文国家名: {imp_analysis['english_count']} 种 ({imp_analysis['total_records_with_english']:,} 条记录)")
        print(f"  其他国家名: {len(imp_analysis['other_countries'])} 种")
        
        # 显示前10个中文国家
        if imp_analysis['chinese_countries']:
            print(f"\n  前10个中文国家 (按记录数排序):")
            sorted_chinese = sorted(imp_analysis['chinese_countries'], key=lambda x: x[1], reverse=True)
            for i, (country, count) in enumerate(sorted_chinese[:10], 1):
                print(f"    {i:2d}. {country}: {count:,} 条")
        
        # 显示英文国家（如果还有）
        if imp_analysis['english_countries']:
            print(f"\n  ⚠️  仍存在的英文国家:")
            sorted_english = sorted(imp_analysis['english_countries'], key=lambda x: x[1], reverse=True)
            for i, (country, count) in enumerate(sorted_english[:10], 1):
                print(f"    {i:2d}. {country}: {count:,} 条")
        
        # 出口商国家分析
        print(f"\n🏭 出口商所在国家分析:")
        exp_analysis = analysis['exporter_analysis']
        print(f"  中文国家名: {exp_analysis['chinese_count']} 种 ({exp_analysis['total_records_with_chinese']:,} 条记录)")
        print(f"  英文国家名: {exp_analysis['english_count']} 种 ({exp_analysis['total_records_with_english']:,} 条记录)")
        print(f"  其他国家名: {len(exp_analysis['other_countries'])} 种")
        
        # 显示前10个中文国家
        if exp_analysis['chinese_countries']:
            print(f"\n  前10个中文国家 (按记录数排序):")
            sorted_chinese = sorted(exp_analysis['chinese_countries'], key=lambda x: x[1], reverse=True)
            for i, (country, count) in enumerate(sorted_chinese[:10], 1):
                print(f"    {i:2d}. {country}: {count:,} 条")
        
        # 显示英文国家（如果还有）
        if exp_analysis['english_countries']:
            print(f"\n  ⚠️  仍存在的英文国家:")
            sorted_english = sorted(exp_analysis['english_countries'], key=lambda x: x[1], reverse=True)
            for i, (country, count) in enumerate(sorted_english[:10], 1):
                print(f"    {i:2d}. {country}: {count:,} 条")
        
        # 计算转换率
        total_imp_records = imp_analysis['total_records_with_chinese'] + imp_analysis['total_records_with_english']
        total_exp_records = exp_analysis['total_records_with_chinese'] + exp_analysis['total_records_with_english']
        
        if total_imp_records > 0:
            imp_conversion_rate = (imp_analysis['total_records_with_chinese'] / total_imp_records) * 100
            print(f"\n📈 进口商国家中文转换率: {imp_conversion_rate:.2f}%")
        
        if total_exp_records > 0:
            exp_conversion_rate = (exp_analysis['total_records_with_chinese'] / total_exp_records) * 100
            print(f"📈 出口商国家中文转换率: {exp_conversion_rate:.2f}%")
        
        # 给出建议
        print(f"\n💡 建议:")
        if imp_analysis['english_countries'] or exp_analysis['english_countries']:
            print(f"  - 仍有英文国家名未转换，建议检查国家映射配置")
            print(f"  - 可以运行 update_country_mapping.py 脚本补充映射")
        else:
            print(f"  - ✅ 所有国家名已成功转换为中文")
        
        if imp_analysis['other_countries'] or exp_analysis['other_countries']:
            print(f"  - 存在其他格式的国家名，建议人工检查")

def main():
    parser = argparse.ArgumentParser(description='验证国家字段更新结果')
    parser.add_argument('--limit', type=int, help='限制分析的记录数量')
    parser.add_argument('--export-stats', help='导出统计结果到JSON文件')
    
    args = parser.parse_args()
    
    verifier = CountryUpdateVerifier()
    
    verifier.print_separator("国家字段验证工具")
    print(f"启动时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"数据库索引: {settings.DATA_INDEX}")
    
    if args.limit:
        print(f"分析限制: {args.limit} 条记录")
    
    try:
        # 获取统计信息
        stats = verifier.get_country_statistics(limit=args.limit)
        
        if not stats:
            print("❌ 无法获取统计信息")
            return
        
        # 分析中文转换情况
        analysis = verifier.check_chinese_conversion(stats)
        
        # 打印报告
        verifier.print_verification_report(stats, analysis)
        
        # 导出统计结果
        if args.export_stats:
            import json
            export_data = {
                'timestamp': datetime.now().isoformat(),
                'statistics': stats,
                'analysis': analysis
            }
            
            with open(args.export_stats, 'w', encoding='utf-8') as f:
                json.dump(export_data, f, ensure_ascii=False, indent=2)
            
            print(f"\n📄 统计结果已导出到: {args.export_stats}")
        
    except Exception as e:
        print(f"❌ 验证过程中发生错误: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()