from app.utils.data_import import DataImportService
if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description='从Excel文件导入数据到Elasticsearch')
    parser.add_argument('--file', default=r"C:\Users\hslxy\Documents\WeChat Files\wxid_a968lsxxcg0322\FileStorage\File\2025-07\company_data\中国.xlsx", help='Excel文件路径')
    parser.add_argument('--batch-size', type=int, default=500, help='批量导入大小，默认500')
    args = parser.parse_args()
    
    service = DataImportService()
    try:
        result = service.import_from_excel(args.file, args.batch_size)
        print(f"数据导入完成: {result}")
    except Exception as e:
        print(f"数据导入失败: {str(e)}")