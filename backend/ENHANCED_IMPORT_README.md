# 增强数据导入功能说明

## 功能概述

增强数据导入功能提供了全面的Excel数据预处理和批量导入能力，包括：

1. **数据预处理**
   - 多sheet Excel文件拆分为单sheet文件
   - 基于关单号/提单号的去重
   - 基于关键字段组合的去重（海关编码前6位、日期、进口商、出口商、公吨）
   - 国家名称英文转中文（如 "India (IN)" → "印度"）
   - 文件命名规范：原文件名-sheet名-时间戳-随机字符串

2. **批量导入**
   - 支持多文件同时上传
   - 后台异步处理
   - 实时进度跟踪

3. **导入历史**
   - 详细的导入记录
   - 海关编码、日期范围统计
   - 导入时间和文件名记录

4. **进度监控**
   - 任务状态显示（成功/失败）
   - 成功导入数量统计
   - 失败原因详情

## API 接口

### 1. 批量上传文件
POST /api/v1/enhanced-import/upload
参数：
- `files`: 多个Excel文件
- `batch_size`: 批量导入大小（默认500）
- `skip_duplicates`: 是否跳过重复数据（默认true）

### 2. 获取导入历史
GET /api/v1/enhanced-import/history
参数：
- `page`: 页码
- `page_size`: 每页大小
- `status`: 状态筛选

### 3. 获取任务详情
GET /api/v1/enhanced-import/task/{task_id}

### 4. 获取导入统计
GET /api/v1/enhanced-import/statistics

## 本地导入脚本

使用 `enhanced_data_importer.py` 进行本地批量导入：

```bash
# 导入单个文件
python enhanced_data_importer.py --files data.xlsx

# 导入多个文件
python enhanced_data_importer.py --files file1.xlsx file2.xlsx file3.xlsx

# 导入整个目录
python enhanced_data_importer.py --directory ./data_folder

# 仅预处理，不导入数据库
python enhanced_data_importer.py --files data.xlsx --dry-run

# 自定义参数
python enhanced_data_importer.py \
  --directory ./data \
  --batch-size 1000 \
  --output-dir ./processed \
  --skip-duplicates
```

## 数据预处理规则

### 1. 去重逻辑
- **第一层**：基于关单号或提单号去重
- **第二层**：基于关键字段组合哈希去重
  - 海关编码（前6位）
  - 日期
  - 进口商
  - 出口商
  - 公吨数

### 2. 数据清理
- **日期格式化**：支持多种日期格式，统一转换为 YYYY-MM-DD
- **数值清理**：移除逗号、空格，转换为浮点数
- **海关编码**：截取前6位数字
- **国家名称**：英文转中文映射

### 3. 文件输出
- **命名规则**：`原文件名-sheet名-时间戳-随机字符串.xlsx`
- **分sheet保存**：每个sheet生成独立的Excel文件
- **保留原始结构**：保持所有必需的列结构

## 前端功能

### 1. 文件上传
- 拖拽上传支持
- 多文件选择
- 文件类型验证
- 上传进度显示

### 2. 导入历史
- 分页显示历史记录
- 状态筛选（处理中/完成/失败）
- 详细信息查看
- 导入统计展示

### 3. 任务监控
- 实时状态更新
- 进度百分比显示
- 错误信息展示
- 处理文件列表

## 配置说明

### 环境变量
- `DATA_INDEX`: Elasticsearch索引名称
- `ELASTICSEARCH_URL`: Elasticsearch连接地址

### 文件路径
- 临时文件目录：系统临时目录
- 预处理文件输出：`./processed_data`
- 日志文件：按应用配置

## 注意事项

1. **文件大小限制**：建议单文件不超过100MB
2. **并发处理**：后台任务异步处理，避免阻塞
3. **错误处理**：详细的错误日志和用户提示
4. **权限控制**：管理员可查看所有记录，普通用户只能查看自己的记录
5. **数据安全**：临时文件处理完成后自动清理

## 故障排除

### 常见问题
1. **文件格式错误**：确保文件为 .xlsx 或 .xls 格式
2. **内存不足**：调整 batch_size 参数
3. **网络超时**：检查 Elasticsearch 连接
4. **权限问题**：确保用户有导入权限

### 日志查看
```bash
# 查看应用日志
tail -f logs/app.log

# 查看导入任务日志
grep "enhanced_import" logs/app.log
```