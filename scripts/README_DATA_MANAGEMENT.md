# 数据管理使用指南

**更新日期**: 2026-04-11  
**统一入口**: `scripts/data_manager.py`

---

## 🎯 统一管理入口

现在我们有了统一的数据管理中心！所有爬虫和数据导入操作都通过一个入口完成。

### 使用方法

```bash
# 查看所有可用命令
uv run python scripts/data_manager.py --help

# 爬取数据
uv run python scripts/data_manager.py crawl --year 2025

# 导入数据到数据库
uv run python scripts/data_manager.py import --year 2025

# 列出所有可用数据
uv run python scripts/data_manager.py list
```

---

## 📊 完整工作流程

### 1. 爬取数据

```bash
# 爬取 2025 年重点高校数据
uv run python scripts/data_manager.py crawl --year 2025

# 爬取指定高校
uv run python scripts/data_manager.py crawl \
  --year 2025 \
  --universities 清华大学 北京大学 复旦大学

# 指定输出目录
uv run python scripts/data_manager.py crawl \
  --year 2025 \
  --output data/raw/custom_2025
```

**输出位置**:
```
data/raw/2025/
├── universities_2025.json    # 高校信息
├── majors_2025.json          # 专业信息
├── scores_2025.json          # 录取分数
└── crawl_report_2025.json    # 爬取报告
```

### 2. 导入数据库

```bash
# 导入 2025 年数据
uv run python scripts/data_manager.py import --year 2025

# 从指定目录导入
uv run python scripts/data_manager.py import \
  --year 2025 \
  --data-dir data/raw/custom_2025
```

### 3. 查看可用数据

```bash
uv run python scripts/data_manager.py list
```

**输出示例**:
```
可用数据:
============================================================

2025 年:
  高校：27 所
  专业：173 个
  分数：135 条
  路径：data/raw/2025
```

---

## 🗂️ 项目结构

```
edu_info/
├── scripts/
│   ├── data_manager.py          # ⭐ 统一数据管理入口
│   ├── crawl_2025_data.py       # 2025 年爬虫（被 data_manager 调用）
│   ├── import_2025_data.py      # 2025 年导入（被 data_manager 调用）
│   └── init_database.py         # 数据库初始化
│
├── data/
│   ├── raw/                     # 原始数据
│   │   └── 2025/               # 2025 年数据
│   ├── duckdb/                 # DuckDB 数据库
│   └── processed/              # 处理后的数据
│
└── src/edu_info/
    ├── services/
    │   ├── data_importer.py    # 数据导入服务（底层）
    │   └── university_crawler.py # 爬虫框架（待完善）
    └── database/
        └── schema.py           # 数据库 Schema
```

---

## 🔧 为什么需要统一入口？

### 之前的问题

1. **脚本分散**: 每个年份一个脚本，难以维护
2. **重复代码**: 每个脚本都有类似的导入逻辑
3. **没有标准**: 数据格式不统一
4. **难以扩展**: 添加新数据源需要修改多个文件

### 现在的优势

1. ✅ **统一命令**: 所有操作一个入口
2. ✅ **标准化**: 统一的数据格式和验证
3. ✅ **易扩展**: 添加新数据源只需修改一处
4. ✅ **可复用**: 爬虫和导入逻辑可复用

---

## 📝 关于爬虫的说明

### 为什么爬虫是现写的？

**原因**:
1. **原有框架是空的**: `university_crawler.py` 只有框架，没有实际爬虫
2. **网页结构不同**: 每个高校招生网的 HTML 结构确实不同
3. **反爬策略**: 阳光高考等平台有反爬，需要特殊处理
4. **数据模拟**: 目前使用模拟数据，需要真实爬虫时再实现

### 下一步爬虫改进

```python
# TODO: 实现真实爬虫
# 1. 阳光高考平台 (https://gaokao.chsi.com.cn/)
# 2. 各高校本科招生网
# 3. 辽宁招生考试之窗
```

**建议方案**:
- 使用 Selenium/Playwright 处理动态网页
- 为不同网站编写专用解析器
- 添加反爬规避（延迟、代理等）
- 实现增量爬取（只爬新数据）

---

## 🚀 快速开始

### 完整流程

```bash
# 1. 初始化数据库
uv run python scripts/init_database.py

# 2. 爬取 2025 年数据
uv run python scripts/data_manager.py crawl --year 2025

# 3. 导入数据库
uv run python scripts/data_manager.py import --year 2025

# 4. 启动应用
uv run streamlit run src/edu_info/main.py --server.port=8501
```

### 验证数据

```bash
# 查看数据库内容
uv run python -c "
import duckdb
conn = duckdb.connect('data/duckdb/edu_planning.db')
print('高校:', conn.execute('SELECT COUNT(*) FROM universities').fetchone()[0])
print('专业:', conn.execute('SELECT COUNT(*) FROM majors').fetchone()[0])
print('分数:', conn.execute('SELECT COUNT(*) FROM admission_scores').fetchone()[0])
"
```

---

## 📋 待完善功能

### 数据爬虫
- [ ] 实现真实网页爬虫
- [ ] 添加多个数据源支持
- [ ] 实现增量爬取
- [ ] 添加数据验证

### 数据导入
- [ ] 支持 Excel 导入
- [ ] 支持批量导入
- [ ] 添加数据清洗
- [ ] 实现数据去重

### 数据管理
- [ ] 添加数据更新功能
- [ ] 实现数据备份
- [ ] 添加数据导出
- [ ] 版本管理

---

## 💡 最佳实践

1. **先爬取后导入**: 始终先爬取到 JSON，再导入数据库
2. **定期备份**: 重要数据定期备份
3. **验证数据**: 导入前检查数据完整性
4. **增量更新**: 只更新变化的数据

---

**有了统一入口，数据管理更简单！** 🎉
