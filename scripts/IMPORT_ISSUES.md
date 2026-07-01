# 数据导入问题说明

**日期**: 2026-04-11  
**状态**: ⚠️ 需要修复

---

## 🐛 问题根源

### ID 不匹配问题

**爬虫生成的数据**:
```json
{
  "university_id": 10003,  // 使用高校代码作为 ID
  "major_id": 10003001,    // 使用 代码*1000 + 序号
  "name": "清华大学"
}
```

**数据库中的数据**:
```sql
universities 表:
  id: 1, 2, 3... (自增 ID)
  code: '10001', '10002', '10003'...

majors 表:
  id: 空 (还没有数据)
```

**问题**: 
- ❌ 爬虫用高校代码（10003）作为 university_id
- ❌ 数据库用自增 ID（1, 2, 3...）
- ❌ 专业表为空，major_id 无法对应

---

## ✅ 解决方案

### 方案 1: 修改爬虫（推荐）

让爬虫使用数据库的 ID 映射：

```python
# 在生成 major_id 时，先查询数据库获取正确的 university_id
def _generate_mock_majors(self, university: University) -> List[Major]:
    # 使用数据库中的真实 ID
    db_uni_id = get_university_id_from_db(university.code)
    
    majors = []
    for i, name in enumerate(selected, 1):
        majors.append(Major(
            id=db_uni_id * 1000 + i,  # 使用数据库 ID
            university_id=db_uni_id,   # 使用数据库 ID
            name=name,
            ...
        ))
    return majors
```

### 方案 2: 导入时转换 ID

在导入脚本中进行 ID 映射：

```python
# 导入前建立 code -> id 映射
code_to_id = {}
result = conn.execute("SELECT id, code FROM universities").fetchall()
for db_id, code in result:
    code_to_id[code] = db_id

# 导入时转换
for score in scores:
    db_uni_id = code_to_id.get(score['university_id'])
    db_major_id = code_to_id.get(score['major_id'] // 1000) * 1000 + (score['major_id'] % 1000)
    
    # 使用转换后的 ID 导入
    conn.execute("INSERT INTO ... VALUES (?, ?, ...)", (db_uni_id, db_major_id, ...))
```

### 方案 3: 重新初始化数据库（最简单）

清空数据库，重新导入，确保 ID 一致：

```bash
# 1. 备份现有数据
cp data/duckdb/edu_planning.db data/duckdb/edu_planning.db.backup

# 2. 删除数据库
rm data/duckdb/edu_planning.db

# 3. 重新初始化
uv run python scripts/init_database.py

# 4. 立即导入 2025 年数据（在导入其他数据之前）
uv run python scripts/import_2025_data.py
```

---

## 🚀 快速修复步骤

### 推荐：方案 3（重新初始化）

```bash
cd /Users/limingkai/nas/project/edu_info

# 1. 备份
cp data/duckdb/edu_planning.db data/duckdb/edu_planning.db.backup

# 2. 删除并重新初始化
rm data/duckdb/edu_planning.db
uv run python scripts/init_database.py

# 3. 导入 2025 年数据
uv run python scripts/import_2025_data.py

# 4. 验证
uv run python -c "
import duckdb
conn = duckdb.connect('data/duckdb/edu_planning.db')
print('高校:', conn.execute('SELECT COUNT(*) FROM universities').fetchone()[0])
print('专业:', conn.execute('SELECT COUNT(*) FROM majors').fetchone()[0])
print('2025 分数:', conn.execute('SELECT COUNT(*) FROM admission_scores WHERE year=2025').fetchone()[0])
"
```

---

## 📋 长期改进建议

### 1. 统一 ID 管理

创建 ID 映射表：

```python
# src/edu_info/services/id_mapper.py
class UniversityIDMapper:
    """高校 ID 映射器"""
    
    @staticmethod
    def code_to_db_id(code: str) -> int:
        """将高校代码转换为数据库 ID"""
        # 查询数据库或缓存
        pass
    
    @staticmethod
    def db_id_to_code(db_id: int) -> str:
        """将数据库 ID 转换为高校代码"""
        pass
```

### 2. 数据验证

在导入前验证数据完整性：

```python
def validate_before_import(conn, data):
    """导入前验证"""
    # 检查高校是否存在
    # 检查专业是否关联正确
    # 检查分数是否合理
    pass
```

### 3. 事务处理

使用事务确保数据一致性：

```python
with conn.transaction():
    import_universities(...)
    import_majors(...)
    import_scores(...)
```

---

## ⚠️ 当前建议

**暂时使用方案 3**（重新初始化），可以快速完成数据导入。

长期需要实现：
1. ID 映射机制
2. 数据验证
3. 事务处理
4. 错误回滚

---

**问题清楚，解决方案明确！** 🎯
