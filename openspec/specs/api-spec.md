# API 规格

## 核心服务接口

### StudentService（学生服务）

```python
class StudentService:
    def create_student(student_data: StudentCreate) -> Student
        """创建学生档案"""

    def get_student(student_id: str) -> Optional[Student]
        """获取学生信息"""

    def update_student(student_id: str, updates: StudentUpdate) -> Student
        """更新学生信息"""

    def delete_student(student_id: str) -> bool
        """删除学生档案"""

    def list_students(filters: StudentFilter) -> List[Student]
        """列出学生列表"""
```

### DataImportService（数据导入服务）

```python
class DataImportService:
    def import_universities(file_path: str, format: str) -> ImportResult
        """导入高校数据（Excel/JSON）"""

    def import_majors(file_path: str, format: str) -> ImportResult
        """导入专业数据"""

    def import_admission_scores(file_path: str, year: int) -> ImportResult
        """导入录取分数数据"""

    def validate_data(data: List[Dict]) -> ValidationResult
        """验证导入数据格式"""
```

### PlanningService（规划服务）

```python
class PlanningService:
    def analyze_student(student_id: str) -> StudentAnalysis
        """分析学生情况"""

    def generate_routes(student_id: str) -> List[PlanRoute]
        """生成规划路线（冲刺/稳妥/保底）"""

    def evaluate_feasibility(student_id: str, target: Target) -> FeasibilityScore
        """评估目标可行性"""

    def get_recommendations(student_id: str) -> List[Recommendation]
        """获取推荐建议"""
```

### DataExportService（数据导出服务）

```python
class DataExportService:
    def export_student_plan(student_id: str, format: str) -> ExportResult
        """导出学生规划方案"""

    def export_universities(filters: UniversityFilter, format: str) -> ExportResult
        """导出高校数据"""

    def export_admission_data(year: int, province: str, format: str) -> ExportResult
        """导出录取数据"""
```

## Streamlit UI 接口

### 页面路由

| 页面 | URL | 功能 |
|------|-----|------|
| 首页 | `/` | 系统概览 |
| 学生管理 | `/students` | 学生档案 CRUD |
| 数据导入 | `/import` | 数据导入界面 |
| 规划分析 | `/planning` | 升学规划分析 |
| 结果展示 | `/results` | 规划结果展示 |
| 数据导出 | `/export` | 数据导出界面 |

### 回调函数

```python
def on_student_select(student_id: str)
    """学生选择回调"""

def on_data_import(file: UploadedFile, data_type: str)
    """数据导入回调"""

def on_plan_generate(student_id: str)
    """生成规划回调"""

def on_export(format: str, filters: Dict)
    """数据导出回调"""
```

## 错误处理

| 错误码 | 描述 | 处理建议 |
|--------|------|----------|
| 400 | 请求参数错误 | 检查输入数据格式 |
| 404 | 资源不存在 | 确认ID是否正确 |
| 409 | 数据冲突 | 检查重复数据 |
| 422 | 验证失败 | 检查数据完整性 |
| 500 | 服务器错误 | 查看日志并重试 |
