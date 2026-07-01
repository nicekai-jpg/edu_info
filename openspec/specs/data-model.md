# 数据模型规格

## 核心实体

### Student（学生）
```python
class Student(BaseModel):
    id: str                      # 唯一标识
    name: str                    # 姓名
    grade: int                   # 年级（初一=1，高一=1）
    school_type: str            # 学校类型（初中/高中）
    subjects: List[str]         # 选科/科目
    scores: Dict[str, float]    # 各科成绩
    target_areas: List[str]     # 目标地区
    target_majors: List[str]    # 目标专业
    created_at: datetime
    updated_at: datetime
```

### University（高校）
```python
class University(BaseModel):
    id: str                      # 唯一标识
    name: str                    # 学校名称
    province: str               # 所在省份
    type: str                   # 类型（985/211/双一流/普通）
    level: str                  # 层次（本科/专科）
    majors: List[str]           # 开设专业列表
    ranking: Optional[int]      # 排名
```

### Major（专业）
```python
class Major(BaseModel):
    id: str                      # 唯一标识
    name: str                    # 专业名称
    category: str               # 学科门类
    duration: int               # 学制（年）
    degree: str                 # 授予学位
    description: str            # 专业介绍
    career_prospects: str       # 就业前景
```

### AdmissionScore（录取分数）
```python
class AdmissionScore(BaseModel):
    id: str                      # 唯一标识
    university_id: str          # 高校ID
    major_id: str               # 专业ID
    year: int                   # 年份
    province: str               # 省份
    score_min: int              # 最低分
    score_max: int              # 最高分
    score_avg: int              # 平均分
    rank_min: int               # 最低位次
    plan_count: int             # 计划招生数
```

### PlanRoute（规划路线）
```python
class PlanRoute(BaseModel):
    id: str                      # 唯一标识
    student_id: str             # 学生ID
    route_type: str             # 路线类型（冲刺/稳妥/保底）
    target_universities: List[str]  # 目标高校
    recommended_majors: List[str]   # 推荐专业
    feasibility_score: float    # 可行性评分（0-100）
    action_items: List[str]     # 行动建议
    created_at: datetime
```

## 关系图

```
┌──────────────┐     ┌──────────────┐     ┌──────────────┐
│   Student    │────<│  PlanRoute   │>────│  University  │
└──────────────┘     └──────────────┘     └──────┬───────┘
                                                  │
                    ┌──────────────┐             │
                    │     Major    │<────────────┘
                    └──────────────┘
                           ▲
                           │
                    ┌──────────────┐
                    │AdmissionScore│
                    └──────────────┘
```

## 数据库表结构

| 表名 | 主键 | 主要字段 | 索引 |
|------|------|----------|------|
| students | id | name, grade, school_type | grade, school_type |
| universities | id | name, province, type | province, type |
| majors | id | name, category | category |
| admission_scores | id | university_id, major_id, year, province | university_id, year, province |
| plan_routes | id | student_id, route_type | student_id |
