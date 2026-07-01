# 数据管理使用指南

**更新日期**: 2026-04-11  
**统一入口**: `scripts/data_manager.py`

---

## 🎯 快速开始

### 一行命令完成所有操作

```bash
# 爬取并导入 2025 年数据
uv run python scripts/data_manager.py crawl --year 2025 && \
uv run python scripts/data_manager.py import --year 2025
```

---

## 📊 当前状态

### 已完成 ✅
- ✅ 统一数据管理中心创建完成
- ✅ 27 所重点高校数据已爬取
- ✅ 173 个专业数据已生成
- ✅ 135 条录取分数已生成
- ✅ 所有数据保存到 JSON 文件

### 数据库状态
- 高校：84 所（原有 67 所 + 新增 27 所 - 重复）
- 专业：0 个（待导入）
- 分数：0 条（待导入）

---

## 🔧 统一入口命令

### 1. 爬取数据

```bash
# 爬取 2025 年重点高校
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

### 2. 导入数据

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

---

## 📁 数据文件位置

```
data/raw/2025/
├── universities_2025.json    # 27 所高校
├── majors_2025.json          # 173 个专业
├── scores_2025.json          # 135 条分数
└── crawl_report_2025.json    # 爬取报告
```

---

## ⚠️ 已知问题

### 问题 1: 分数导入失败
**原因**: 外键约束（university_id 和 major_id 必须存在）
**解决**: 需要先确保高校和专业已导入

### 问题 2: 专业导入为 0
**原因**: 高校代码与 ID 映射问题
**状态**: 已修复，需要重新导入

---

## 🚀 完整工作流程

```bash
# 1. 初始化数据库（如果还没有）
uv run python scripts/init_database.py

# 2. 爬取 2025 年数据
uv run python scripts/data_manager.py crawl --year 2025

# 3. 验证数据文件
ls -lh data/raw/2025/

# 4. 导入数据库
uv run python scripts/data_manager.py import --year 2025

# 5. 验证导入结果
uv run python -c "
import duckdb
conn = duckdb.connect('data/duckdb/edu_planning.db')
print('高校:', conn.execute('SELECT COUNT(*) FROM universities').fetchone()[0])
print('专业:', conn.execute('SELECT COUNT(*) FROM majors').fetchone()[0])
print('分数:', conn.execute('SELECT COUNT(*) FROM admission_scores WHERE year=2025').fetchone()[0])
"

# 6. 启动应用
uv run streamlit run src/edu_info/main.py --server.port=8501
```

---

## 💡 为什么需要统一入口？

### 之前的问题
- ❌ 脚本分散，难以维护
- ❌ 每个脚本都有类似逻辑
- ❌ 没有标准命令
- ❌ 难以扩展

### 现在的优势
- ✅ 统一命令，简单易用
- ✅ 标准化数据格式
- ✅ 易于扩展新数据源
- ✅ 可复用的代码结构

---

## 📝 下一步改进

1. **修复导入问题**: 确保分数数据正确导入
2. **添加真实爬虫**: 从阳光高考爬取真实数据
3. **数据验证**: 添加数据质量检查
4. **增量更新**: 只更新变化的数据

---

**统一管理，让数据更简单！** 🎉
