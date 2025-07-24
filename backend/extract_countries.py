import pandas as pd
import json
import os
from pathlib import Path
from collections import defaultdict
import re

def extract_countries_from_excel_files():
    """从Excel文件中提取所有国家信息"""
    company_data_dir = Path("../company_data")
    countries_set = set()
    
    # 遍历所有Excel文件
    for excel_file in company_data_dir.glob("*.xlsx"):
        print(f"处理文件: {excel_file.name}")
        
        try:
            # 读取Excel文件的所有sheet
            excel_data = pd.ExcelFile(excel_file, engine='openpyxl')
            
            for sheet_name in excel_data.sheet_names:
                print(f"  处理sheet: {sheet_name}")
                
                try:
                    # 读取sheet数据
                    df = pd.read_excel(excel_file, sheet_name=sheet_name, engine='openpyxl')
                    
                    # 提取进口商所在国家和出口商所在国家
                    for col in ['进口商所在国家', '出口商所在国家']:
                        if col in df.columns:
                            # 获取该列的所有非空值
                            country_values = df[col].dropna().unique()
                            for country in country_values:
                                if pd.notna(country) and str(country).strip():
                                    countries_set.add(str(country).strip())
                                    
                except Exception as e:
                    print(f"    处理sheet失败: {str(e)}")
                    continue
                    
        except Exception as e:
            print(f"  处理文件失败: {str(e)}")
            continue
    
    return sorted(list(countries_set))

def create_country_mapping():
    """创建新的国家映射格式"""
    # 提取Excel文件中的国家
    excel_countries = extract_countries_from_excel_files()
    print(f"从Excel文件中提取到 {len(excel_countries)} 个国家:")
    for country in excel_countries:
        print(f"  - {country}")
    
    # 读取现有的映射配置
    config_file = Path("app/config/country_mapping.json")
    if config_file.exists():
        with open(config_file, 'r', encoding='utf-8') as f:
            current_config = json.load(f)
            current_mapping = current_config.get("country_mapping", {})
    else:
        current_mapping = {}
    
    # 创建新的映射格式
    new_mapping = {}
    
    # 处理现有映射
    for english_name, chinese_name in current_mapping.items():
        if chinese_name not in new_mapping:
            new_mapping[chinese_name] = []
        
        # 添加英文名称（带代码）
        if english_name not in new_mapping[chinese_name]:
            new_mapping[chinese_name].append(english_name)
        
        # 提取并添加英文名称（不带代码）
        if '(' in english_name and ')' in english_name:
            english_only = english_name.split('(')[0].strip()
            if english_only and english_only not in new_mapping[chinese_name]:
                new_mapping[chinese_name].append(english_only)
        
        # 添加中文名称
        if chinese_name not in new_mapping[chinese_name]:
            new_mapping[chinese_name].append(chinese_name)
    
    # 处理Excel中发现的新国家
    for country in excel_countries:
        # 检查是否已经在映射中
        found = False
        for chinese_name, aliases in new_mapping.items():
            if country in aliases:
                found = True
                break
        
        if not found:
            # 尝试匹配现有的中文名称
            matched = False
            for chinese_name, aliases in new_mapping.items():
                # 检查是否与现有别名匹配
                for alias in aliases:
                    if country.lower() in alias.lower() or alias.lower() in country.lower():
                        if country not in aliases:
                            new_mapping[chinese_name].append(country)
                        matched = True
                        break
                if matched:
                    break
            
            if not matched:
                # 创建新的映射条目，使用国家名称作为中文名称
                if country not in new_mapping:
                    new_mapping[country] = [country]
    
    # 保存新的映射配置
    new_config = {
        "country_mapping": new_mapping
    }
    
    # 备份原文件
    if config_file.exists():
        backup_file = config_file.with_suffix('.json.backup')
        with open(config_file, 'r', encoding='utf-8') as f:
            with open(backup_file, 'w', encoding='utf-8') as bf:
                bf.write(f.read())
        print(f"原配置文件已备份到: {backup_file}")
    
    # 写入新配置
    with open(config_file, 'w', encoding='utf-8') as f:
        json.dump(new_config, f, ensure_ascii=False, indent=2)
    
    print(f"新的国家映射配置已保存到: {config_file}")
    print(f"总共包含 {len(new_mapping)} 个国家映射")
    
    return new_mapping

if __name__ == "__main__":
    try:
        mapping = create_country_mapping()
        print("\n新的映射格式示例:")
        for chinese_name, aliases in list(mapping.items())[:5]:
            print(f"  \"{chinese_name}\": {aliases}")
    except Exception as e:
        print(f"处理失败: {str(e)}")
        import traceback
        traceback.print_exc()