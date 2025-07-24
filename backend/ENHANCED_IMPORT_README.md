# 增强数据导入功能说明

## 功能概述

增强数据导入功能提供了全面的Excel数据预处理和批量导入能力，包括：

1. **数据预处理**
   - 多sheet Excel文件处理
   - 基于关单号/提单号的去重
   - 基于关键字段组合的去重（海关编码前6位、日期、进口商、出口商、公吨）
   - 国家名称英文转中文映射（如 "India (IN)" → "印度"）
   - 海关编码标准化（截取前6位）
   - 日期格式统一化

2. **批量导入**
   - 支持多文件同时处理
   - 后台异步处理
   - 实时进度跟踪
   - 详细的中间结果输出

3. **数据库维护**
   - 现有数据国家字段更新
   - 数据验证和统计
   - 备份和恢复功能

4. **导入历史**
   - 详细的导入记录
   - 海关编码、日期范围统计
   - 导入时间和文件名记录

5. **进度监控**
   - 任务状态显示（成功/失败）
   - 成功导入数量统计
   - 失败原因详情

## 脚本工具说明

### 1. 数据导入脚本 (enhanced_data_importer.py)

用于处理和导入Excel文件到数据库。

#### 基本用法

```bash
# 进入后端目录
cd d:\customs\backend

# 导入单个文件
python enhanced_data_importer.py --files data.xlsx

# 导入多个文件
python enhanced_data_importer.py --files file1.xlsx file2.xlsx file3.xlsx

# 导入整个目录
python enhanced_data_importer.py --directory ../company_data

# 仅预处理，不导入数据库（测试模式）
python enhanced_data_importer.py --files data.xlsx --dry-run

# 显示详细日志并保存报告
python enhanced_data_importer.py --files data.xlsx --verbose --save-report
```

#### 高级用法

```bash
# 完整参数示例
python enhanced_data_importer.py \
  --directory ../company_data \
  --batch-size 1000 \
  --output-dir ./processed \
  --skip-duplicates \
  --reload-config \
  --verbose \
  --save-report

# 测试国家映射功能
python enhanced_data_importer.py \
  --files ../company_data/美国.xlsx \
  --dry-run \
  --reload-config \
  --verbose
```

### 2. 国家字段更新脚本 (update_country_fields.py)

用于更新数据库中现有数据的国家字段，将英文转换为中文。

#### 基本用法

```bash
# 预览更新（不执行实际更新）
python update_country_fields.py --dry-run

# 执行实际更新
python update_country_fields.py --execute

# 重新加载配置后更新
python update_country_fields.py --execute --reload-config

# 限制处理数量（测试用）
python update_country_fields.py --dry-run --limit 1000
```

#### 高级用法

```bash
# 跳过备份直接更新
python update_country_fields.py --execute --no-backup

# 自定义批量大小
python update_country_fields.py --execute --batch-size 200

# 完整更新流程
python update_country_fields.py \
  --execute \
  --reload-config \
  --batch-size 500
```

#### 安全注意事项

⚠️ **重要提醒**：
- 首次使用请先运行 `--dry-run` 预览更新内容
- 实际更新前会自动创建备份（除非使用 `--no-backup`）
- 建议在非生产环境先测试
- 更新完成后使用验证脚本检查结果

### 3. 国家字段验证脚本 (verify_country_update.py)

用于验证国家字段更新的结果，分析转换情况。

#### 基本用法

```bash
# 验证更新结果
python verify_country_update.py

# 限制分析数量
python verify_country_update.py --limit 10000

# 导出统计结果
python verify_country_update.py --export-stats country_stats.json
```

#### 输出说明

验证脚本会显示：
- 总记录数和唯一国家数量
- 中文/英文国家名的分布
- 转换率统计
- 仍需处理的英文国家名
- 改进建议

## 完整工作流程

### 新数据导入流程

```bash
# 1. 测试导入（预览模式）
python enhanced_data_importer.py \
  --files ../company_data/新文件.xlsx \
  --dry-run \
  --verbose

# 2. 实际导入
python enhanced_data_importer.py \
  --files ../company_data/新文件.xlsx \
  --skip-duplicates \
  --save-report

# 3. 验证导入结果
python verify_country_update.py
```

### 现有数据更新流程

```bash
# 1. 重新加载最新的国家映射配置
python update_country_fields.py --dry-run --reload-config

# 2. 预览更新内容
python update_country_fields.py --dry-run

# 3. 执行更新
python update_country_fields.py --execute

# 4. 验证更新结果
python verify_country_update.py

# 5. 导出验证报告
python verify_country_update.py --export-stats update_verification.json
```

### 批量处理流程

```bash
# 1. 批量导入所有文件
python enhanced_data_importer.py \
  --directory ../company_data \
  --skip-duplicates \
  --batch-size 1000 \
  --save-report

# 2. 更新所有国家字段
python update_country_fields.py --execute --reload-config

# 3. 全面验证
python verify_country_update.py --export-stats final_verification.json
```

## 参数说明

### enhanced_data_importer.py 参数

| 参数 | 说明 | 默认值 | 示例 |
|------|------|--------|------|
| `--files` | 指定要处理的Excel文件列表 | 无 | `--files file1.xlsx file2.xlsx` |
| `--directory` | 指定包含Excel文件的目录 | 无 | `--directory ../company_data` |
| `--batch-size` | 批量导入大小 | 500 | `--batch-size 1000` |
| `--output-dir` | 预处理文件输出目录 | `./processed_data` | `--output-dir ./output` |
| `--skip-duplicates` | 跳过重复数据 | False | `--skip-duplicates` |
| `--dry-run` | 仅预处理，不导入数据库 | False | `--dry-run` |
| `--reload-config` | 重新加载配置文件 | False | `--reload-config` |
| `--verbose` | 显示详细日志 | False | `--verbose` |
| `--save-report` | 保存详细报告到JSON文件 | False | `--save-report` |

### update_country_fields.py 参数

| 参数 | 说明 | 默认值 | 示例 |
|------|------|--------|------|
| `--dry-run` | 仅预览，不执行实际更新 | False | `--dry-run` |
| `--execute` | 执行实际更新操作 | False | `--execute` |
| `--limit` | 限制处理的记录数量 | 无 | `--limit 1000` |
| `--no-backup` | 跳过备份创建 | False | `--no-backup` |
| `--reload-config` | 重新加载国家映射配置 | False | `--reload-config` |
| `--batch-size` | 批量处理大小 | 500 | `--batch-size 200` |

### verify_country_update.py 参数

| 参数 | 说明 | 默认值 | 示例 |
|------|------|--------|------|
| `--limit` | 限制分析的记录数量 | 无 | `--limit 10000` |
| `--export-stats` | 导出统计结果到JSON文件 | 无 | `--export-stats stats.json` |

## 测试验证流程

### 1. 测试国家映射功能
```bash
# 重新加载国家映射配置并测试
python enhanced_data_importer.py \
  --files ../company_data/美国.xlsx \
  --dry-run \
  --reload-config \
  --verbose
```

**验证要点：**
- 查看日志中的"国家字段映射"信息
- 确认英文国家名正确转换为中文
- 检查未映射的国家名称警告

### 2. 测试去重逻辑
```bash
# 测试去重功能
python enhanced_data_importer.py \
  --files ../company_data/中国.xlsx \
  --skip-duplicates \
  --dry-run \
  --save-report
```

**验证要点：**
- 查看"去重移除"数量
- 检查重复记录的识别逻辑
- 确认基于关单号/提单号的去重优先级

### 3. 测试现有数据更新
```bash
# 小范围测试更新
python update_country_fields.py --dry-run --limit 100

# 验证更新效果
python verify_country_update.py --limit 1000
```

**验证要点：**
- 更新记录数量合理
- 中文转换率符合预期
- 无意外的数据变化

### 4. 实际导入测试
```bash
# 小批量实际导入测试
python enhanced_data_importer.py \
  --files ../company_data/泰国.xlsx \
  --batch-size 100 \
  --verbose \
  --save-report
```

**验证要点：**
- 数据库连接正常
- 导入成功率
- 重复检测有效性
- 错误处理机制

## 输出结果说明

### 控制台输出示例

#### enhanced_data_importer.py 输出
# ============================================================
增强数据导入工具
启动时间: 2024-01-15 10:30:00
Dry Run 模式: 否
跳过重复数据: 是
批量大小: 500
输出目录: ./processed_data

## [步骤 1] Excel文件预处理
文件路径: ../company_data/中国.xlsx
跳过重复: True

预处理 结果摘要:
✓ 状态: 成功
✓ 原始文件: 中国.xlsx
✓ Sheet数量: 1
✓ 总记录数: 1500
✓ 处理后记录数: 1450
✓ 去重移除: 50
✓ 输出文件数: 1

#### update_country_fields.py 输出
# ============================================================
数据库国家字段更新工具
启动时间: 2024-01-15 14:30:00
运行模式: 实际更新模式
数据库索引: customs_data
批量大小: 500

## [步骤 0] 创建数据备份
📦 正在创建备份文件: ./backups/country_fields_backup_20240115_143000.json
✅ 备份完成: 15000 条记录已保存

## [步骤 1] 扫描数据库中的文档
📊 数据库中共有 15000 条记录
🔍 开始扫描文档...
📝 文档 a1b2c3d4... 需要更新:
进口商所在国家: United States -> 美国
出口商所在国家: India -> 印度
✅ 批量更新完成: 成功 500 条
📊 已处理: 10000 / 15000 条记录
✅ 文档扫描完成，共处理 15000 条记录

# ============================================================
更新完成 - 最终报告
🔧 运行模式: 实际更新模式
📦 备份文件: ./backups/country_fields_backup_20240115_143000.json

📊 处理统计:
📝 总处理记录: 15000 条
✅ 需要更新记录: 3500 条
🏢 进口商国家更新: 1800 条
🏭 出口商国家更新: 1700 条
⚪ 无需更新记录: 11500 条
❌ 错误记录: 0 条

📈 更新比例: 23.33%
🎉 国家字段更新完成！

#### verify_country_update.py 输出
# ============================================================
国家字段验证报告
📊 数据概览:
总记录数: 15,000
唯一进口商国家数: 25
唯一出口商国家数: 30

🏢 进口商所在国家分析:
中文国家名: 20 种 (13,500 条记录)
英文国家名: 3 种 (1,200 条记录)
其他国家名: 2 种

前10个中文国家 (按记录数排序):
1. 中国: 5,200 条
2. 美国: 2,800 条
3. 印度: 1,900 条
4. 德国: 1,200 条
5. 日本: 1,100 条

⚠️  仍存在的英文国家:
1. United Kingdom: 800 条
2. South Korea: 400 条

📈 进口商国家中文转换率: 91.84%
📈 出口商国家中文转换率: 89.23%

💡 建议:

- 仍有英文国家名未转换，建议检查国家映射配置
- 可以运行 update_country_mapping.py 脚本补充映射

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

### 3. 国家映射
- 支持完全匹配：`United States` → `美国`
- 支持模糊匹配：`United States (US)` → `美国`
- 支持国家代码：`US` → `美国`
- 支持部分匹配：`States` → `美国`

## 配置说明

### 环境变量
- `DATA_INDEX`: Elasticsearch索引名称
- `ELASTICSEARCH_URL`: Elasticsearch连接地址

### 配置文件
- `app/config/country_mapping.json`: 国家映射配置
- `app/config/settings.py`: 应用设置

### 文件路径
- 临时文件目录：系统临时目录
- 预处理文件输出：`./processed_data`
- 备份文件目录：`./backups`
- 日志文件：`logs/app.log`

## 注意事项

1. **文件大小限制**：建议单文件不超过100MB
2. **并发处理**：本地脚本为串行处理，API支持并发
3. **错误处理**：详细的错误日志和用户提示
4. **数据安全**：
   - 更新前自动创建备份
   - 支持dry-run模式预览
   - 详细的操作日志
5. **配置热加载**：使用 `--reload-config` 重新加载配置
6. **内存管理**：大数据量时调整batch-size参数

## 故障排除

### 常见问题

#### 1. 文件格式错误
```bash
# 确保文件为正确格式
file ../company_data/文件名.xlsx
```

#### 2. 国家映射不生效
```bash
# 检查配置文件
cat app/config/country_mapping.json

# 重新加载配置
python enhanced_data_importer.py --files test.xlsx --reload-config --dry-run

# 更新国家映射
python update_country_mapping.py
```

#### 3. 数据库连接问题
```bash
# 检查Elasticsearch连接
curl -X GET "localhost:9200/_cluster/health"

# 查看应用日志
tail -f logs/app.log
```

#### 4. 内存不足
```bash
# 减小批量大小
python enhanced_data_importer.py --files large_file.xlsx --batch-size 100
python update_country_fields.py --execute --batch-size 200
```

#### 5. 更新失败回滚
```bash
# 查看备份文件
ls -la backups/

# 如需回滚，联系管理员使用备份文件恢复
```

### 日志查看
```bash
# 查看应用日志
tail -f logs/app.log

# 查看导入任务日志
grep "enhanced_import" logs/app.log

# 查看国家映射日志
grep "国家映射" logs/app.log

# 查看更新操作日志
grep "update_country_fields" logs/app.log
```

### 性能优化
```bash
# 大文件处理
python enhanced_data_importer.py --files large_file.xlsx --batch-size 200

# 大数据库更新
python update_country_fields.py --execute --batch-size 200

# 分批处理
python update_country_fields.py --execute --limit 10000
```

### 数据验证
```bash
# 定期验证数据质量
python verify_country_update.py --export-stats daily_check.json

# 比较更新前后的统计
diff old_stats.json new_stats.json
```
