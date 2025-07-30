#将全球贸易监测的数据转换为国贸通的数据格式
import pandas as pd
import numpy as np
from datetime import datetime
import os
import re
from pathlib import Path

class GlobalTradeConverter:
    """全球贸易监测数据转换器"""
    
    def __init__(self):
        # 字段映射关系
        self.field_mapping = {
            'DATE': '日期',
            'IMPORTER': '进口商', 
            'EXPORTER': '出口商',
            'HS_CODE': '海关编码',
            'PRODUCT': '详细产品名称',
            'COMMODITY': '详细产品名称本国语言',
            'WEIGHT_KG': '净重',
            'QTY': '数量',
            'QTY_UNIT': '数量单位',
            'LOAD_PORT': '当地港口',
            'LOAD_COUNTRY': '出口商所在国家',
            'DES_COUNTRY': '进口商所在国家',
            'DES_PORT': '国外港口',
            'TRANS_MODE': '运输方式',
            'DATASOURCE': '数据来源'
        }
        
        # 目标表头（与中国.xlsx一致）
        self.target_columns = [
            "海关编码", "编码产品描述", "日期", "月度", "进口商", "进口商所在国家", 
            "出口商所在国家", "出口商", "重量单位", "数量单位", "数量", "毛重", 
            "净重", "公吨", "金额美元", "美元重量计单价", "美元数量计单价", 
            "本国币种金额", "合同金额", "币种", "成交方式", "详细产品名称", 
            "产品规格型号品牌", "当地港口", "国外港口", "运输方式", "贸易方式", 
            "中转国", "提单号", "编码产品描述本国语言", "详细产品名称本国语言", 
            "产品规格型号品牌本国语言", "进口商本地语言", "数据来源", 
            "出口商本地语言", "关单号", "申报数量"
        ]

    def analyze_excel_structure(self, file_path):
        """分析Excel文件结构"""
        print(f"分析文件: {file_path}")
        
        try:
            # 读取Excel文件
            excel_file = pd.ExcelFile(file_path)
            print(f"工作表数量: {len(excel_file.sheet_names)}")
            print(f"工作表名称: {excel_file.sheet_names}")
            
            # 分析第一个工作表
            sheet_name = excel_file.sheet_names[0]
            print(f"\n分析工作表: {sheet_name}")
            
            # 读取前15行来查看结构
            df_preview = pd.read_excel(file_path, sheet_name=sheet_name, header=None, nrows=15)
            print(f"前15行数据:")
            for i, row in df_preview.iterrows():
                row_data = [str(val)[:50] + "..." if len(str(val)) > 50 else str(val) for val in row.values]
                print(f"第{i+1}行: {row_data}")
            
            return sheet_name
            
        except Exception as e:
            print(f"分析失败: {e}")
            return None

    def find_header_row(self, file_path, sheet_name):
        """查找表头行"""
        try:
            # 读取前20行
            df_preview = pd.read_excel(file_path, sheet_name=sheet_name, header=None, nrows=20)
            
            # 查找包含预期字段的行
            expected_fields = ['DATE', 'IMPORTER', 'EXPORTER', 'HS_CODE', 'PRODUCT']
            
            for i, row in df_preview.iterrows():
                row_str = ' '.join([str(val).upper() for val in row.values if pd.notna(val)])
                matches = sum(1 for field in expected_fields if field in row_str)
                if matches >= 3:  # 至少匹配3个字段
                    print(f"找到表头行: 第{i+1}行")
                    print(f"表头内容: {list(row.values)}")
                    return i
            
            # 如果没找到，默认使用第7行（索引6）
            print("未找到明确的表头行，使用默认第7行")
            return 6
            
        except Exception as e:
            print(f"查找表头行失败: {e}")
            return 6

    def clean_hs_code(self, hs_code):
        """清理并截取海关编码前6位"""
        if pd.isna(hs_code) or not hs_code:
            return ""
        
        # 转换为字符串并移除非数字字符
        hs_str = str(hs_code).strip()
        hs_str = re.sub(r'[^\d]', '', hs_str)
        
        # 取前6位
        if len(hs_str) >= 6:
            return hs_str[:6]
        elif len(hs_str) > 0:
            # 如果不足6位，保持原样
            return hs_str
        else:
            return ""

    def calculate_month(self, date_value):
        """从日期计算月度"""
        if pd.isna(date_value):
            return ""
        
        try:
            if isinstance(date_value, str):
                # 尝试解析字符串日期
                date_obj = pd.to_datetime(date_value)
            else:
                date_obj = date_value
            
            return date_obj.strftime('%Y%m')
        except:
            return ""

    def calculate_tonnage(self, weight_kg):
        """从净重(KG)计算公吨"""
        if pd.isna(weight_kg) or not weight_kg:
            return ""
        
        try:
            weight_float = float(weight_kg)
            return weight_float / 1000
        except:
            return ""

    def convert_file(self, input_file_path, output_file_path=None):
        """转换Excel文件"""
        print(f"开始转换文件: {input_file_path}")
        
        # 检查文件是否存在
        if not os.path.exists(input_file_path):
            print(f"文件不存在: {input_file_path}")
            return False
        
        # 分析文件结构
        sheet_name = self.analyze_excel_structure(input_file_path)
        if not sheet_name:
            return False
        
        # 查找表头行
        header_row = self.find_header_row(input_file_path, sheet_name)
        
        # 读取数据
        try:
            # 使用找到的表头行读取数据
            df = pd.read_excel(input_file_path, sheet_name=sheet_name, header=header_row)
            print(f"原始数据形状: {df.shape}")
            print(f"原始列名: {list(df.columns)}")
            
            # 跳过可能的空行（第8行）
            if header_row == 6:  # 如果表头是第7行，跳过第8行
                df = df.iloc[1:].reset_index(drop=True)
                print(f"跳过空行后数据形状: {df.shape}")
            
        except Exception as e:
            print(f"读取Excel文件失败: {e}")
            return False
        
        # 创建目标DataFrame
        converted_data = []
        
        for index, row in df.iterrows():
            # 跳过空行
            if row.isna().all():
                continue
                
            # 创建新记录
            new_record = {}
            
            # 初始化所有目标列为空
            for col in self.target_columns:
                new_record[col] = ""
            
            # 映射字段 - 使用模糊匹配
            for source_col in df.columns:
                source_col_upper = str(source_col).upper()
                target_col = None
                
                # 模糊匹配字段名
                if 'DATE' in source_col_upper:
                    target_col = '日期'
                elif 'IMPORTER' in source_col_upper:
                    target_col = '进口商'
                elif 'EXPORTER' in source_col_upper:
                    target_col = '出口商'
                elif 'HS_CODE' in source_col_upper or 'HSCODE' in source_col_upper:
                    target_col = '海关编码'
                elif 'PRODUCT' in source_col_upper and 'COMMODITY' not in source_col_upper:
                    target_col = '详细产品名称'
                elif 'COMMODITY' in source_col_upper:
                    target_col = '详细产品名称本国语言'
                elif 'WEIGHT_KG' in source_col_upper or ('WEIGHT' in source_col_upper and 'KG' in source_col_upper):
                    target_col = '净重'
                elif 'QTY_UNIT' in source_col_upper:
                    target_col = '数量单位'
                elif 'QTY' in source_col_upper and 'UNIT' not in source_col_upper:
                    target_col = '数量'
                elif 'LOAD_PORT' in source_col_upper:
                    target_col = '当地港口'
                elif 'LOAD_COUNTRY' in source_col_upper:
                    target_col = '出口商所在国家'
                elif 'DES_COUNTRY' in source_col_upper:
                    target_col = '进口商所在国家'
                elif 'DES_PORT' in source_col_upper:
                    target_col = '国外港口'
                elif 'TRANS_MODE' in source_col_upper:
                    target_col = '运输方式'
                elif 'DATASOURCE' in source_col_upper or 'DATA_SOURCE' in source_col_upper:
                    target_col = '数据来源'
                
                # 如果找到匹配的字段，进行转换
                if target_col and target_col in new_record:
                    value = row[source_col]
                    if pd.notna(value):
                        if target_col == '海关编码':
                            new_record[target_col] = self.clean_hs_code(value)
                        elif target_col == '日期':
                            # 处理日期格式
                            if isinstance(value, datetime):
                                new_record[target_col] = value.strftime('%Y-%m-%d')
                            else:
                                try:
                                    date_obj = pd.to_datetime(value)
                                    new_record[target_col] = date_obj.strftime('%Y-%m-%d')
                                except:
                                    new_record[target_col] = str(value)
                        else:
                            new_record[target_col] = str(value)
            
            # 计算衍生字段
            # 月度
            if new_record['日期']:
                new_record['月度'] = self.calculate_month(new_record['日期'])
            
            # 重量单位统一为KG
            new_record['重量单位'] = 'KG'
            
            # 公吨计算
            if new_record['净重']:
                new_record['公吨'] = self.calculate_tonnage(new_record['净重'])
            
            # 只保留有海关编码的记录
            if new_record['海关编码']:
                converted_data.append(new_record)
        
        # 创建转换后的DataFrame
        result_df = pd.DataFrame(converted_data, columns=self.target_columns)
        print(f"转换后数据形状: {result_df.shape}")
        print(f"有效记录数: {len(converted_data)}")
        
        # 保存结果
        if output_file_path is None:
            input_path = Path(input_file_path)
            output_file_path = input_path.parent / f"{input_path.stem}_converted.xlsx"
        
        try:
            result_df.to_excel(output_file_path, index=False, engine='openpyxl')
            print(f"转换完成，输出文件: {output_file_path}")
            
            # 显示转换统计
            print("\n转换统计:")
            print(f"- 总记录数: {len(result_df)}")
            print(f"- 有海关编码记录: {len(result_df[result_df['海关编码'] != ''])}")
            print(f"- 有日期记录: {len(result_df[result_df['日期'] != ''])}")
            print(f"- 有进口商记录: {len(result_df[result_df['进口商'] != ''])}")
            print(f"- 有出口商记录: {len(result_df[result_df['出口商'] != ''])}")
            
            # 显示样本数据
            print("\n样本数据（前3条）:")
            for i, row in result_df.head(3).iterrows():
                print(f"记录 {i+1}:")
                for col in ['海关编码', '日期', '进口商', '出口商', '详细产品名称']:
                    if row[col]:
                        print(f"  {col}: {row[col]}")
                print()
            
            return True
            
        except Exception as e:
            print(f"保存文件失败: {e}")
            return False

def main():
    """主函数"""
    converter = GlobalTradeConverter()
    
    # 输入文件路径
    input_file = r"d:\customs\company_data\全球贸易监测\e6a8a199ad424c2dae4d188883e579d6202507302004324419.xlsx"
    
    # 输出文件路径
    output_file = r"d:\customs\company_data\全球贸易监测\converted_data.xlsx"
    
    # 执行转换
    success = converter.convert_file(input_file, output_file)
    
    if success:
        print("数据转换成功完成！")
    else:
        print("数据转换失败！")

if __name__ == "__main__":
    main()