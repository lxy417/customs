import re
import json
from bs4 import BeautifulSoup
from datetime import datetime

def parse_html_table(file_path):
    """
    解析HTML文件中的表格数据，提取日期和内容信息
    """
    with open(file_path, 'r', encoding='utf-8') as file:
        content = file.read()
    
    # 使用BeautifulSoup解析HTML
    soup = BeautifulSoup(content, 'html.parser')
    
    # 查找表格
    table = soup.find('table')
    if not table:
        print("未找到表格")
        return []
    
    data = []
    current_year = None
    
    # 遍历表格行
    rows = table.find_all('tr')
    
    for row in rows:
        # 跳过表头
        if row.find('th', {'data-column': '2018'}):
            continue
            
        # 查找年份行（年份标题行）
        year_cell = row.find('th', class_='dw-bold')
        if year_cell and year_cell.get_text().strip().isdigit():
            current_year = year_cell.get_text().strip()
            continue
        
        # 查找日期和内容行
        date_cell = row.find('th', scope='row')
        content_cell = row.find('td')
        
        if date_cell and content_cell and current_year:
            # 提取日期文本
            date_b_tag = date_cell.find('b')
            if date_b_tag:
                date_text = date_b_tag.get_text().strip()
                content_text = content_cell.get_text().strip()
                
                # 跳过空内容或特殊标记
                if not content_text or '*' in date_text:
                    continue
                
                # 解析日期
                parsed_date = parse_date(date_text, current_year)
                if parsed_date:
                    data.append({
                        'date': parsed_date,
                        'content': content_text
                    })
    
    return data

def parse_date(date_text, year):
    """
    将日期文本转换为yyyy-MM-dd格式
    """
    # 月份映射
    months = {
        'January': '01', 'February': '02', 'March': '03', 'April': '04',
        'May': '05', 'June': '06', 'July': '07', 'August': '08',
        'September': '09', 'October': '10', 'November': '11', 'December': '12'
    }
    
    try:
        # 处理特殊情况
        if date_text == 'June':
            return f"{year}-06-01"  # 只有月份的情况，默认为1号
        elif date_text == 'March':
            return f"{year}-03-01"
        
        # 解析 "Month Day" 格式
        for month_name, month_num in months.items():
            if month_name in date_text:
                # 提取日期数字
                day_match = re.search(r'\d+', date_text)
                if day_match:
                    day = day_match.group().zfill(2)
                    return f"{year}-{month_num}-{day}"
                else:
                    # 只有月份，默认为1号
                    return f"{year}-{month_num}-01"
        
        return None
    except Exception as e:
        print(f"解析日期失败: {date_text}, 错误: {e}")
        return None

def save_to_json(data, output_file):
    """
    将数据保存为JSON文件
    """
    with open(output_file, 'w', encoding='utf-8') as file:
        json.dump(data, file, ensure_ascii=False, indent=2)
    print(f"数据已保存到 {output_file}")

def save_to_csv(data, output_file):
    """
    将数据保存为CSV文件
    """
    import csv
    
    with open(output_file, 'w', newline='', encoding='utf-8') as file:
        writer = csv.writer(file)
        writer.writerow(['date', 'content'])  # 写入表头
        
        for item in data:
            writer.writerow([item['date'], item['content']])
    
    print(f"数据已保存到 {output_file}")

def main():
    """
    主函数
    """
    input_file = r'd:\customs\frontend\public\data.html'
    output_json = r'd:\customs\frontend\parsed_table_data.json'
    output_csv = r'd:\customs\frontend\parsed_table_data.csv'
    
    print("开始解析HTML表格数据...")
    
    # 解析数据
    data = parse_html_table(input_file)
    
    if data:
        print(f"成功解析 {len(data)} 条记录")
        
        # 按日期排序
        data.sort(key=lambda x: x['date'])
        
        # 显示前几条数据作为预览
        print("\n前5条数据预览:")
        for i, item in enumerate(data[:5]):
            print(f"{i+1}. date: {item['date']}, content: {item['content'][:80]}...")
        
        # 保存数据
        save_to_json(data, output_json)
        save_to_csv(data, output_csv)
        
        print(f"\n解析完成！共处理 {len(data)} 条记录")
        print(f"JSON文件: {output_json}")
        print(f"CSV文件: {output_csv}")
        
    else:
        print("未找到任何数据")

if __name__ == "__main__":
    main()