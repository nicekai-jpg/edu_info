# 开发规范文档

本文档描述了智能升学规划系统的开发规范和最佳实践。

## 📋 目录

- [代码风格](#代码风格)
- [提交规范](#提交规范)
- [测试规范](#测试规范)
- [文档规范](#文档规范)
- [开发流程](#开发流程)

---

## 代码风格

### Python 代码规范

1. **使用类型注解**

```python
# ✅ 推荐
def calculate_score(scores: list[float]) -> float:
    return sum(scores) / len(scores)

# ❌ 不推荐
def calculate_score(scores):
    return sum(scores) / len(scores)
```

2. **使用 docstring**

```python
# ✅ 推荐
def validate_student_profile(data: dict) -> StudentProfile:
    """
    验证学生档案数据
    
    Args:
        data: 学生档案字典数据
        
    Returns:
        验证通过的 StudentProfile 对象
        
    Raises:
        ValidationError: 验证失败时抛出
    """
    return StudentProfile.model_validate(data)

# ❌ 不推荐
def validate_student_profile(data):
    # 验证数据
    return StudentProfile.model_validate(data)
```

3. **遵循 PEP 8**

- 使用 4 空格缩进
- 行宽限制 88 字符（black 格式化）
- 导入顺序：标准库 → 第三方库 → 本地模块

4. **错误处理**

```python
# ✅ 推荐
from src.utils.errors import DataImportError, handle_errors

@handle_errors(DataImportError)
def import_data(file_path: str):
    if not Path(file_path).exists():
        raise DataImportError(f"文件不存在：{file_path}")

# ❌ 不推荐
def import_data(file_path):
    try:
        # 一堆代码
    except Exception as e:
        print(f"出错了：{e}")
```

### 命名规范

```python
# 类名：大驼峰
class StudentProfile:
    pass

# 函数和变量：小写 + 下划线
def calculate_score():
    pass

student_name = "张三"

# 常量：全大写
MAX_SCORE = 150

# 私有变量：单下划线前缀
_internal_cache = {}

# 模块级别私有：双下划线前缀
__version__ = "0.1.0"
```

---

## 提交规范

### Git Commit Message

遵循 [Conventional Commits](https://www.conventionalcommits.org/) 规范：

```
<type>(<scope>): <subject>

<body>

<footer>
```

#### Type 类型

- `feat`: 新功能
- `fix`: 修复 bug
- `docs`: 文档更新
- `style`: 代码格式调整
- `refactor`: 重构
- `test`: 测试相关
- `chore`: 构建/工具/配置

#### 示例

```bash
# 新功能
git commit -m "feat(engine): 添加多维度匹配器实现"

# 修复 bug
git commit -m "fix(data): 修复分数线导入验证逻辑"

# 文档更新
git commit -m "docs: 更新开发规范文档"

# 重构
git commit -m "refactor(utils): 重构错误处理模块"
```

---

## 测试规范

### 测试文件组织

```
tests/
├── __init__.py
├── conftest.py          # 通用 fixture
├── test_database.py     # 数据库测试
├── test_validators.py   # 验证模块测试
├── test_engine/         # 引擎测试
│   ├── __init__.py
│   ├── test_matcher.py
│   └── test_planner.py
└── test_ui/             # UI 测试
    └── __init__.py
```

### 测试编写规范

```python
# ✅ 推荐
class TestStudentProfileValidation:
    """学生档案验证测试"""

    def test_valid_profile(self, sample_student_profile):
        """测试有效的学生档案"""
        result = validate_student_profile(sample_student_profile)
        assert result is not None
        assert result.name == "张三"

    def test_invalid_grade(self):
        """测试无效年级"""
        profile = {"name": "李四", "current_grade": "三年级"}
        
        with pytest.raises(ValidationError):
            validate_student_profile(profile)

# ❌ 不推荐
def test_1():
    # 测试 1
    pass

def test_2():
    # 测试 2
    pass
```

### 测试覆盖率要求

- 核心算法模块（engine/）：> 80%
- 数据模块（data/）：> 70%
- 工具模块（utils/）：> 60%
- UI 模块：> 40%

运行测试：

```bash
# 运行所有测试
pytest

# 运行测试并生成覆盖率报告
pytest --cov=src --cov-report=html

# 运行特定测试
pytest tests/test_validators.py -v
```

---

## 文档规范

### 代码注释

```python
# ✅ 推荐：解释为什么
# 使用 DuckDB 而非 SQLite，因为分析型查询性能更好
conn = duckdb.connect(db_path)

# ❌ 不推荐：解释是什么
# 连接数据库
conn = duckdb.connect(db_path)
```

### README 规范

每个模块应该有 README.md：

```markdown
# 模块名称

## 功能说明

简要描述模块功能

## 使用方法

```python
from src.data import Database

db = Database()
result = db.query("SELECT * FROM universities")
```

## API 参考

### 类

#### Database

参数:
- db_path (str): 数据库文件路径

方法:
- query(sql: str) -> list: 执行查询
- insert(table: str, data: dict) -> None: 插入数据
```

---

## 开发流程

### 1. 功能开发流程

```
1. 创建需求文档（如需要）
   ↓
2. 编写测试（TDD）
   ↓
3. 实现功能
   ↓
4. 运行测试
   ↓
5. 代码审查
   ↓
6. 合并代码
```

### 2. Bug 修复流程

```
1. 复现 Bug
   ↓
2. 编写失败的测试
   ↓
3. 修复 Bug
   ↓
4. 验证测试通过
   ↓
5. 提交代码
```

### 3. 代码审查清单

- [ ] 代码通过所有测试
- [ ] 测试覆盖率符合要求
- [ ] 代码通过 linting（ruff）
- [ ] 代码已格式化（black）
- [ ] 类型注解完整
- [ ] docstring 完整
- [ ] 错误处理完善
- [ ] 日志记录适当

---

## 工具使用

### 代码检查

```bash
# Linting
ruff check src/ tests/

# 格式化
black src/ tests/

# 类型检查
mypy src/
```

### 预提交钩子

建议配置 pre-commit 钩子：

```yaml
# .pre-commit-config.yaml
repos:
  - repo: https://github.com/astral-sh/ruff-pre-commit
    rev: v0.3.3
    hooks:
      - id: ruff
      - id: ruff-format
  - repo: https://github.com/pre-commit/mirrors-mypy
    rev: v1.9.0
    hooks:
      - id: mypy
```

---

## 常见问题

### Q: 如何处理数据库迁移？

A: 使用版本号管理 schema，在 `src/data/migrations/` 中存放迁移脚本。

### Q: 如何添加新的规划路线？

A: 在 `data/routes/planning_routes.json` 中添加路线定义，确保符合 schema。

### Q: 如何调试数据导入问题？

A: 启用 DEBUG 日志级别，查看详细的验证错误信息。

---

## 参考资源

- [Python 官方风格指南](https://peps.python.org/pep-0008/)
- [Conventional Commits](https://www.conventionalcommits.org/)
- [pytest 最佳实践](https://docs.pytest.org/en/latest/)
- [pydantic 文档](https://docs.pydantic.dev/)
