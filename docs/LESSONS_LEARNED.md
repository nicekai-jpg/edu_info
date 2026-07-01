# 经验教训总结

**目的**: 记录开发过程中遇到的问题和解决方案，避免未来重复同样的错误

**最后更新**: 2026-04-11

---

## 📋 问题分类索引

| 编号 | 问题类型 | 问题描述 | 解决方案 | 预防措施 |
|------|----------|----------|----------|----------|
| [LL-001](#ll-001-数据导入时的-id-不匹配问题) | 数据一致性 | 爬虫生成的 ID 与数据库 ID 不匹配 | ID 映射转换 | 统一 ID 管理机制 |
| [LL-002](#ll-002-正则表达式-pattern-空格问题) | 数据验证 | pattern 中 `|` 前后有空格导致匹配失败 | 使用 `'|'.join()` 生成 | 添加单元测试 |
| [LL-003](#ll-003-pydantic-v2-配置警告) | 依赖兼容性 | 使用废弃的 `Config` 类 | 改用 `ConfigDict` | 依赖升级检查清单 |
| [LL-004](#ll-004-数据库测试-fixture-失败) | 测试可靠性 | `NamedTemporaryFile` 导致连接失败 | 使用 `mktemp()` | 测试隔离原则 |

---

## 详细问题记录

### LL-001: 数据导入时的 ID 不匹配问题

**问题类型**: 数据一致性 / 架构设计

**发生时间**: 2026-04-11

**问题描述**:
```
爬虫生成的数据使用高校代码（如 10003）作为 university_id
数据库使用自增 ID（1, 2, 3...）
导致导入时外键关联失败
```

**根本原因**:
1. 爬虫模块和数据库模块独立开发，缺乏统一的 ID 管理规范
2. 爬虫生成 mock 数据时没有考虑数据库的实际 ID 结构
3. 缺少数据导入前的验证机制

**影响范围**:
- ❌ 专业数据无法导入（外键约束失败）
- ❌ 分数数据无法关联（university_id 和 major_id 都不匹配）
- ❌ 数据完整性受损

**解决方案**:

**短期方案**（已实施）:
```bash
# 重新初始化数据库，确保 ID 一致
rm data/duckdb/edu_planning.db
uv run python scripts/init_database.py
uv run python scripts/import_2025_data.py
```

**中期方案**（推荐）:
```python
# 在导入脚本中进行 ID 映射转换
code_to_id = {}
result = conn.execute("SELECT id, code FROM universities").fetchall()
for db_id, code in result:
    code_to_id[code] = db_id

# 导入时转换 ID
for score in scores:
    db_uni_id = code_to_id.get(score['university_id'])
    db_major_id = ... # 计算转换
    conn.execute("INSERT ...", (db_uni_id, db_major_id, ...))
```

**长期方案**（架构改进）:
```python
# 创建统一的 ID 映射服务
# src/edu_info/services/id_mapper.py
class UniversityIDMapper:
    """高校 ID 映射器（单例模式）"""
    
    _instance = None
    _cache = {}
    
    @classmethod
    def get_instance(cls):
        if not cls._instance:
            cls._instance = cls()
        return cls._instance
    
    def code_to_db_id(self, code: str) -> int:
        """将高校代码转换为数据库 ID（带缓存）"""
        if code not in self._cache:
            # 查询数据库或返回默认值
            pass
        return self._cache[code]
    
    def db_id_to_code(self, db_id: int) -> str:
        """反向映射"""
        pass
```

**预防措施** ✅:

1. **设计阶段**:
   - [ ] 在架构设计文档中明确 ID 生成规则
   - [ ] 定义统一的数据交换格式（DTO）
   - [ ] 建立模块间的接口契约

2. **开发阶段**:
   - [ ] 使用依赖注入，避免硬编码 ID
   - [ ] 在数据生成时查询数据库获取真实 ID
   - [ ] 实现 Repository 模式，封装数据访问逻辑

3. **测试阶段**:
   - [ ] 添加集成测试，验证数据导入流程
   - [ ] 测试边界情况（空数据、重复数据、错误数据）
   - [ ] 使用真实数据库进行测试，而不是 mock

4. **代码审查清单**:
   - [ ] 检查所有外键关联是否正确
   - [ ] 验证 ID 生成逻辑是否一致
   - [ ] 确认数据转换逻辑是否完整

**相关文件**:
- [`scripts/IMPORT_ISSUES.md`](../scripts/IMPORT_ISSUES.md) - 详细问题分析
- [`scripts/import_2025_data.py`](../scripts/import_2025_data.py) - 导入脚本
- [`src/edu_info/services/data_importer.py`](../src/edu_info/services/data_importer.py) - 数据导入服务

---

### LL-002: 正则表达式 pattern 空格问题

**问题类型**: 数据验证 / 字符串处理

**发生时间**: 2026-04-11

**问题描述**:
```python
# 错误的 pattern（| 前后有空格）
pattern = r'^(初一 | 初二 | 初三 | 高一 | 高二 | 高三)$'

# 正确的pattern（| 前后无空格）
pattern = r'^(初一 | 初二 | 初三 | 高一 | 高二 | 高三)$'
```

**根本原因**:
1. 手动编写正则表达式时，视觉上的空格误导
2. 缺少针对正则表达式的单元测试
3. 代码审查时未注意到字符串内部的空格

**影响范围**:
- ❌ 所有使用该 pattern 的验证都失败
- ❌ 用户输入无法通过验证
- ❌ 静默失败（没有报错，只是匹配不上）

**解决方案**:
```python
# 使用 join 方法生成 pattern，避免手动拼接
GRADES = ['初一', '初二', '初三', '高一', '高二', '高三']
GRADE_PATTERN = f"^({'|'.join(GRADES)})$"

# 而不是:
# GRADE_PATTERN = r'^(初一 | 初二 | 初三 | 高一 | 高二 | 高三)$'
```

**预防措施** ✅:

1. **编码规范**:
   - [ ] 避免手动编写包含 `|` 的正则表达式
   - [ ] 使用 `'|'.join(list)` 生成选择匹配
   - [ ] 将正则表达式定义为常量，便于测试

2. **测试策略**:
   - [ ] 为每个验证 pattern 添加单元测试
   - [ ] 测试有效输入（应该匹配）
   - [ ] 测试无效输入（应该不匹配）
   - [ ] 测试边界情况（空字符串、特殊字符）

3. **代码审查**:
   - [ ] 重点检查字符串字面量中的空格
   - [ ] 验证正则表达式的实际匹配结果
   - [ ] 使用可视化工具辅助检查 pattern

**测试示例**:
```python
def test_grade_pattern():
    """测试年级 pattern"""
    pattern = GRADE_PATTERN
    
    # 有效输入
    assert re.match(pattern, "初一") is not None
    assert re.match(pattern, "高三") is not None
    
    # 无效输入
    assert re.match(pattern, "初 一") is None  # 有空格
    assert re.match(pattern, "一年级") is None
    assert re.match(pattern, "") is None
```

**相关文件**:
- [`src/utils/validators.py`](../src/utils/validators.py) - 验证器模块
- [`tests/test_validators.py`](../tests/test_validators.py) - 验证器测试

---

### LL-003: Pydantic v2 配置警告

**问题类型**: 依赖兼容性 / 技术债务

**发生时间**: 2026-04-11

**问题描述**:
```python
# Pydantic v1 风格（已废弃）
class Student(BaseModel):
    name: str
    age: int
    
    class Config:
        arbitrary_types_allowed = True

# Pydantic v2 风格
from pydantic import ConfigDict

class Student(BaseModel):
    name: str
    age: int
    
    model_config = ConfigDict(arbitrary_types_allowed=True)
```

**根本原因**:
1. 依赖升级时未同步更新代码
2. 缺少对废弃 API 的监控
3. 测试未覆盖配置相关代码

**影响范围**:
- ⚠️ 运行时警告（不影响功能）
- ⚠️ 未来版本可能报错
- ⚠️ 日志污染

**解决方案**:
```python
# 全局替换所有 class Config: 为 model_config = ConfigDict(...)
# 使用脚本批量转换 + 手动检查
```

**预防措施** ✅:

1. **依赖管理**:
   - [ ] 在 `pyproject.toml` 中明确指定主要依赖的版本范围
   - [ ] 定期运行 `uv pip compile --upgrade` 更新依赖
   - [ ] 使用 `DeprecationWarning` 过滤器检测废弃 API

2. **升级检查清单**:
   - [ ] 阅读依赖的 CHANGELOG 和迁移指南
   - [ ] 在独立环境中测试新版本
   - [ ] 运行全量测试套件验证兼容性
   - [ ] 更新受影响的代码

3. **持续监控**:
   - [ ] 在 CI 中启用所有警告
   - [ ] 定期扫描代码中的废弃用法
   - [ ] 建立技术债务跟踪机制

**相关文件**:
- [`src/edu_info/models/schemas.py`](../src/edu_info/models/schemas.py) - 数据模型
- [`pyproject.toml`](../pyproject.toml) - 依赖配置

---

### LL-004: 数据库测试 fixture 失败

**问题类型**: 测试可靠性 / 资源管理

**发生时间**: 2026-04-11

**问题描述**:
```python
# 错误的方式
@pytest.fixture
def db_file():
    with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
        yield f.name  # 文件已创建，DuckDB 连接失败

# 正确的方式
@pytest.fixture
def db_file():
    yield tempfile.mktemp(suffix='.db')  # 只生成路径，不创建文件
```

**根本原因**:
1. 对 `NamedTemporaryFile` 的行为理解不足
2. 测试 fixture 未考虑跨平台差异
3. DuckDB 在文件已存在时的连接行为未充分测试

**影响范围**:
- ❌ 数据库测试失败
- ❌ 测试覆盖率降低
- ❌ CI/CD 流程中断

**解决方案**:
```python
# 使用 mktemp() 只生成路径，不创建文件
@pytest.fixture
def temp_db():
    db_path = tempfile.mktemp(suffix='.db')
    yield db_path
    # 清理
    if os.path.exists(db_path):
        os.remove(db_path)
```

**预防措施** ✅:

1. **测试最佳实践**:
   - [ ] 遵循测试隔离原则，每个测试使用独立资源
   - [ ] 在 fixture 中明确资源的创建和清理
   - [ ] 避免在 fixture 中做隐式操作

2. **资源管理**:
   - [ ] 使用上下文管理器（with 语句）
   - [ ] 确保 finally 块清理资源
   - [ ] 测试失败时也能正确清理

3. **文档和分享**:
   - [ ] 在团队内分享常见陷阱
   - [ ] 建立测试编写规范
   - [ ] 代码审查时关注测试质量

**相关文件**:
- [`tests/conftest.py`](../tests/conftest.py) - 测试配置
- [`tests/test_database.py`](../tests/test_database.py) - 数据库测试

---

## 📊 问题统计

### 按类型分类

| 类型 | 数量 | 占比 |
|------|------|------|
| 数据一致性 | 1 | 25% |
| 数据验证 | 1 | 25% |
| 依赖兼容性 | 1 | 25% |
| 测试可靠性 | 1 | 25% |

### 按严重程度分类

| 级别 | 数量 | 描述 |
|------|------|------|
| 🔴 严重 | 1 | 导致功能完全失败（LL-001） |
| 🟡 中等 | 2 | 部分功能失败或警告（LL-002, LL-004） |
| 🟢 轻微 | 1 | 仅警告，不影响功能（LL-003） |

---

## 🎯 改进行动计划

### 立即执行（本周）

- [ ] 为所有验证器 pattern 添加单元测试
- [ ] 建立依赖升级检查清单
- [ ] 审查所有测试 fixture 的资源管理

### 短期计划（本月）

- [ ] 实现统一的 ID 映射服务
- [ ] 添加数据导入验证机制
- [ ] 建立代码审查清单

### 长期计划（本季度）

- [ ] 完善集成测试覆盖
- [ ] 建立技术债务跟踪机制
- [ ] 定期回顾和更新本文档

---

## 📚 相关资源

### 内部文档
- [AGENTS.md](../AGENTS.md) - 项目状态和修复记录
- [IMPORT_ISSUES.md](../scripts/IMPORT_ISSUES.md) - 数据导入问题分析
- [测试规范](./testing-guidelines.md) - 测试编写指南

### 外部资源
- [Pydantic v2 迁移指南](https://docs.pydantic.dev/latest/migration/)
- [pytest fixture 最佳实践](https://docs.pytest.org/en/latest/explanation/fixtures.html)
- [正则表达式调试工具](https://regex101.com/)

---

## 📝 贡献指南

欢迎提交新的经验教训！请按以下格式提交：

```markdown
### LL-XXX: 问题标题

**问题类型**: 分类 / 子分类

**发生时间**: YYYY-MM-DD

**问题描述**:
简洁描述问题现象

**根本原因**:
1. 原因 1
2. 原因 2

**影响范围**:
- ❌ 影响 1
- ❌ 影响 2

**解决方案**:
代码示例 + 说明

**预防措施**:
- [ ] 预防项 1
- [ ] 预防项 2
```

---

**文档目标**: 让同样的错误不犯第二次！🎯
