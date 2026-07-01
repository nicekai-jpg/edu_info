# 04 - 规划分析引擎设计（v2.1）

## 1. 引擎架构（更新版）

### 1.1 核心理念转变

```
v2.0逻辑（自上而下）：
突破口 → 政策 → 专业 → 高校 → 评估

v2.1逻辑（穷举+匹配）：
穷举所有规划路线 → 学生画像 → 多维度匹配 → 筛选排序 → 推荐
```

### 1.2 引擎架构图

```
规划分析引擎 v2.1
│
├── 输入层
│   └── 学生画像（成绩、兴趣、特长、家庭条件）
│
├── 路线穷举层（Route Enumeration）
│   ├── 普通高考路线（985/211/普通本科）
│   ├── 科技特长生路线（信息学/机器人/科创）
│   ├── 艺术特长生路线（音乐/美术/舞蹈）
│   ├── 体育特长生路线（各体育项目）
│   ├── 拔尖人才路线（奥赛/强基/综评）
│   ├── 特殊类型（港澳/中外合作/艺术校考）
│   └── 职业路线（高职/职业本科）
│   │
│   └── 输出：所有可能的规划路线（50-100条）
│
├── 匹配过滤层（Matching & Filtering）
│   ├── 硬性条件过滤（年级、时间窗口）
│   ├── 兴趣匹配（兴趣领域重合度）
│   ├── 能力匹配（学科成绩、特长）
│   ├── 经济匹配（家庭收入vs路线成本）
│   ├── 地域匹配（目标地区偏好）
│   └── 时间匹配（准备周期可行性）
│   │
│   └── 输出：符合条件的路线（10-20条）
│
├── 评分排序层（Scoring & Ranking）
│   ├── 兴趣契合度评分（40%权重）
│   ├── 可行性评分（30%权重）
│   ├── 经济可承受度评分（20%权重）
│   ├── 发展潜力评分（10%权重）
│   │
│   └── 输出：排序后的Top 10路线
│
├── 目标生成层（Target Generation）
│   ├── 高目标：该路线最好结果
│   ├── 中目标：该路线平均结果
│   ├── 低目标：该路线保底结果
│   │
│   └── 输出：每条路线的三档目标高校
│
├── 可行性评估层（Feasibility Assessment）
│   ├── 当前水平评估
│   ├── 目标要求对比
│   ├── 差距分析
│   └── 达成概率计算
│
└── 输出层
    ├── Top 10规划路线（含三档目标）
    ├── 可行性评估报告
    ├── 备选方案（当首选不可行时）
    └── 行动建议清单
```

## 2. 路线穷举器（RouteEnumerator）

### 2.1 穷举逻辑

```python
"""
路线穷举器 - 生成所有可能的规划路线
"""

from dataclasses import dataclass
from typing import List, Dict, Optional
from enum import Enum

class RouteType(Enum):
    """路线类型"""
    GAOKAO_985 = "普通高考-985"
    GAOKAO_211 = "普通高考-211"
    GAOKAO_NORMAL = "普通高考-普通本科"
    TECH_OI = "科技特长-信息学奥赛"
    TECH_ROBOT = "科技特长-机器人"
    TECH_INNOVATION = "科技特长-科技创新"
    ART_MUSIC = "艺术特长-音乐"
    ART_FINE_ART = "艺术特长-美术"
    ART_DANCE = "艺术特长-舞蹈"
    SPORT_HIGH_LEVEL = "体育特长-高水平运动队"
    SPORT_SINGLE = "体育特长-体育单招"
    ELITE_OLYMPIAD = "拔尖人才-五大学科奥赛"
    ELITE_QIANGJI = "拔尖人才-强基计划"
    ELITE_ZONGPING = "拔尖人才-综合评价"
    SPECIAL_HK_MACAO = "特殊类型-港澳高校"
    SPECIAL_SINO_FOREIGN = "特殊类型-中外合作"
    VOCATIONAL = "职业路线-高职/职业本科"

@dataclass
class PlanningRoute:
    """规划路线定义"""
    route_id: str
    route_type: RouteType
    name: str
    description: str
    
    # 适用条件
    min_grade: str  # 最低年级要求
    max_grade: str  # 最高年级要求
    subject_requirements: List[str]  # 学科要求
    talent_requirements: List[str]  # 特长要求
    
    # 准备信息
    preparation_period: str  # 准备周期
    time_commitment: str  # 时间投入
    difficulty: str  # 难度等级
    success_rate: str  # 成功率
    
    # 成本信息
    cost_range: tuple  # 费用范围（万元）
    cost_items: List[str]  # 费用明细
    
    # 目标高校
    target_universities: List[str]  # 目标高校类型
    target_majors: List[str]  # 目标专业类型
    
    # 相关数据
    related_policies: List[str]  # 相关政策
    related_industries: List[str]  # 关联产业
    future_prospects: str  # 发展前景


class RouteEnumerator:
    """路线穷举器"""
    
    def __init__(self):
        self.routes_db = self._load_routes_database()
    
    def enumerate_all_routes(self) -> List[PlanningRoute]:
        """
        穷举所有可能的规划路线
        
        Returns:
            List[PlanningRoute]: 所有规划路线列表（约50-100条）
        """
        routes = []
        
        # 1. 普通高考路线（细分）
        routes.extend(self._enumerate_gaokao_routes())
        
        # 2. 科技特长生路线
        routes.extend(self._enumerate_tech_routes())
        
        # 3. 艺术特长生路线
        routes.extend(self._enumerate_art_routes())
        
        # 4. 体育特长生路线
        routes.extend(self._enumerate_sport_routes())
        
        # 5. 拔尖人才路线
        routes.extend(self._enumerate_elite_routes())
        
        # 6. 特殊类型路线
        routes.extend(self._enumerate_special_routes())
        
        # 7. 职业路线
        routes.extend(self._enumerate_vocational_routes())
        
        return routes
    
    def _enumerate_gaokao_routes(self) -> List[PlanningRoute]:
        """穷举普通高考路线"""
        routes = []
        
        # 985层次细分
        for tier in ["顶尖985", "中坚985", "末流985"]:
            routes.append(PlanningRoute(
                route_id=f"gaokao_985_{tier}",
                route_type=RouteType.GAOKAO_985,
                name=f"普通高考-{tier}",
                description=f"通过高考进入{tier}高校",
                min_grade="高一",
                max_grade="高三",
                subject_requirements=["全面发展"],
                talent_requirements=[],
                preparation_period="3年",
                time_commitment="高强度",
                difficulty="高",
                success_rate="5-10%" if tier=="顶尖985" else "10-20%",
                cost_range=(1, 10),
                cost_items=["学费", "补课费", "资料费"],
                target_universities=[tier],
                target_majors=["所有专业"],
                related_policies=["高考统招"],
                related_industries=["所有行业"],
                future_prospects="优秀"
            ))
        
        # 211层次
        routes.append(PlanningRoute(
            route_id="gaokao_211",
            route_type=RouteType.GAOKAO_211,
            name="普通高考-211高校",
            description="通过高考进入211高校",
            min_grade="高一",
            max_grade="高三",
            subject_requirements=["较好成绩"],
            talent_requirements=[],
            preparation_period="3年",
            time_commitment="中等强度",
            difficulty="中高",
            success_rate="15-25%",
            cost_range=(1, 8),
            cost_items=["学费", "补课费"],
            target_universities=["211高校"],
            target_majors=["所有专业"],
            related_policies=["高考统招"],
            related_industries=["所有行业"],
            future_prospects="良好"
        ))
        
        # 普通本科（分公办/民办）
        for uni_type in ["公办本科", "民办本科"]:
            routes.append(PlanningRoute(
                route_id=f"gaokao_{uni_type}",
                route_type=RouteType.GAOKAO_NORMAL,
                name=f"普通高考-{uni_type}",
                description=f"通过高考进入{uni_type}",
                min_grade="高一",
                max_grade="高三",
                subject_requirements=["达到本科线"],
                talent_requirements=[],
                preparation_period="3年",
                time_commitment="常规强度",
                difficulty="中",
                success_rate="40-60%",
                cost_range=(2 if uni_type=="公办本科" else 8, 
                           5 if uni_type=="公办本科" else 20),
                cost_items=["学费", "住宿费"],
                target_universities=[uni_type],
                target_majors=["所有专业"],
                related_policies=["高考统招"],
                related_industries=["所有行业"],
                future_prospects="一般"
            ))
        
        return routes
    
    def _enumerate_tech_routes(self) -> List[PlanningRoute]:
        """穷举科技特长生路线"""
        routes = []
        
        # 信息学奥赛路线细分
        oi_levels = [
            ("国集保送", "进入国家集训队保送清北", "极高", "极低", "5-15万", 5, 15),
            ("国赛金牌", "全国赛金牌降分录取", "极高", "极低", "5-12万", 5, 12),
            ("国赛银牌", "全国赛银牌强基破格", "极高", "低", "4-10万", 4, 10),
            ("省一等奖", "省一强基计划", "高", "低", "3-8万", 3, 8),
            ("省二等奖", "省二综评加分", "中高", "中", "2-5万", 2, 5),
        ]
        
        for level, desc, diff, rate, cost, cost_min, cost_max in oi_levels:
            routes.append(PlanningRoute(
                route_id=f"tech_oi_{level}",
                route_type=RouteType.TECH_OI,
                name=f"科技特长-信息学{level}",
                description=desc,
                min_grade="初一",
                max_grade="高三",
                subject_requirements=["数学优秀", "逻辑思维强"],
                talent_requirements=["编程基础"],
                preparation_period="2-5年",
                time_commitment="高强度",
                difficulty=diff,
                success_rate=rate,
                cost_range=(cost_min, cost_max),
                cost_items=["培训费", "比赛费", "设备费"],
                target_universities=["985/211"],
                target_majors=["计算机", "人工智能", "软件工程"],
                related_policies=["强基计划", "综合评价"],
                related_industries=["互联网", "人工智能"],
                future_prospects="优秀"
            ))
        
        # 机器人、科创等其他科技路线...
        
        return routes
    
    def _enumerate_art_routes(self) -> List[PlanningRoute]:
        """穷举艺术特长生路线"""
        routes = []
        
        art_types = ["音乐", "美术", "舞蹈", "传媒"]
        
        for art_type in art_types:
            # 高水平艺术团（985/211降分）
            routes.append(PlanningRoute(
                route_id=f"art_{art_type}_high_level",
                route_type=RouteType.ART_MUSIC if art_type=="音乐" else RouteType.ART_FINE_ART,
                name=f"艺术特长-{art_type}-高水平艺术团",
                description=f"通过{art_type}特长进入985/211",
                min_grade="小学",
                max_grade="高三",
                subject_requirements=["文化课达标"],
                talent_requirements=[f"{art_type}特长", "10级证书"],
                preparation_period="5-10年",
                time_commitment="高强度",
                difficulty="高",
                success_rate="低",
                cost_range=(10, 30),
                cost_items=["培训费", "器材费", "考级费"],
                target_universities=["985/211"],
                target_majors=["相关专业"],
                related_policies=["高水平艺术团"],
                related_industries=["艺术", "传媒"],
                future_prospects="良好"
            ))
            
            # 艺术类统考
            routes.append(PlanningRoute(
                route_id=f"art_{art_type}_tongkao",
                route_type=RouteType.ART_MUSIC if art_type=="音乐" else RouteType.ART_FINE_ART,
                name=f"艺术特长-{art_type}-省统考",
                description=f"通过{art_type}统考进入艺术院校",
                min_grade="高一",
                max_grade="高三",
                subject_requirements=["文化课本科线60%"],
                talent_requirements=[f"{art_type}基础"],
                preparation_period="1-3年",
                time_commitment="高强度",
                difficulty="中高",
                success_rate="中",
                cost_range=(5, 15),
                cost_items=["集训费", "材料费"],
                target_universities=["艺术院校", "综合大学艺术系"],
                target_majors=[f"{art_type}专业"],
                related_policies=["艺术类招生"],
                related_industries=["艺术", "设计", "传媒"],
                future_prospects="中"
            ))
        
        return routes
    
    # 其他路线穷举方法类似...
```

## 3. 多维度匹配器（MultiDimensionalMatcher）

### 3.1 匹配维度

```python
"""
多维度匹配器 - 从多个维度评估路线与学生画像的匹配度
"""

@dataclass
class MatchResult:
    """匹配结果"""
    route: PlanningRoute
    overall_score: float  # 综合得分 0-100
    dimension_scores: Dict[str, float]  # 各维度得分
    is_eligible: bool  # 是否符合硬性条件
    filter_reasons: List[str]  # 被过滤的原因（如不符合）
    recommendation_reasons: List[str]  # 推荐理由


class MultiDimensionalMatcher:
    """多维度匹配器"""
    
    def __init__(self):
        self.weights = {
            'interest': 0.40,      # 兴趣匹配 40%
            'ability': 0.25,       # 能力匹配 25%
            'economic': 0.20,      # 经济匹配 20%
            'time': 0.10,          # 时间匹配 10%
            'region': 0.05         # 地域匹配 5%
        }
    
    def match(self, routes: List[PlanningRoute], profile: StudentProfile) -> List[MatchResult]:
        """
        多维度匹配
        
        Args:
            routes: 所有可能的路线
            profile: 学生画像
        
        Returns:
            List[MatchResult]: 匹配结果列表
        """
        results = []
        
        for route in routes:
            # 1. 硬性条件过滤
            is_eligible, filter_reasons = self._check_eligibility(route, profile)
            
            if not is_eligible:
                results.append(MatchResult(
                    route=route,
                    overall_score=0,
                    dimension_scores={},
                    is_eligible=False,
                    filter_reasons=filter_reasons,
                    recommendation_reasons=[]
                ))
                continue
            
            # 2. 多维度评分
            dimension_scores = {
                'interest': self._score_interest(route, profile),
                'ability': self._score_ability(route, profile),
                'economic': self._score_economic(route, profile),
                'time': self._score_time(route, profile),
                'region': self._score_region(route, profile)
            }
            
            # 3. 计算综合得分
            overall_score = sum(
                dimension_scores[dim] * self.weights[dim]
                for dim in dimension_scores
            )
            
            # 4. 生成推荐理由
            recommendation_reasons = self._generate_recommendations(
                route, profile, dimension_scores
            )
            
            results.append(MatchResult(
                route=route,
                overall_score=overall_score,
                dimension_scores=dimension_scores,
                is_eligible=True,
                filter_reasons=[],
                recommendation_reasons=recommendation_reasons
            ))
        
        return results
    
    def _check_eligibility(self, route: PlanningRoute, profile: StudentProfile) -> tuple:
        """检查是否符合硬性条件"""
        is_eligible = True
        reasons = []
        
        # 检查年级
        if not self._check_grade(route, profile):
            is_eligible = False
            reasons.append(f"年级不符（要求{route.min_grade}-{route.max_grade}）")
        
        # 检查时间窗口（如已错过准备时间）
        if not self._check_time_window(route, profile):
            is_eligible = False
            reasons.append("准备时间不足")
        
        return is_eligible, reasons
    
    def _score_interest(self, route: PlanningRoute, profile: StudentProfile) -> float:
        """
        兴趣匹配评分
        
        算法：
        - 完全匹配：100分
        - 相关匹配：60-80分
        - 无关：0-40分
        """
        route_interests = set(route.related_industries + route.target_majors)
        student_interests = set(profile.interests)
        
        if not route_interests:
            return 50  # 通用路线，中等分数
        
        # 计算重合度
        intersection = route_interests & student_interests
        
        if len(intersection) == 0:
            return 30  # 完全不匹配
        
        match_ratio = len(intersection) / len(route_interests)
        
        if match_ratio >= 0.8:
            return 95
        elif match_ratio >= 0.5:
            return 80
        elif match_ratio >= 0.3:
            return 60
        else:
            return 40
    
    def _score_ability(self, route: PlanningRoute, profile: StudentProfile) -> float:
        """
        能力匹配评分
        
        考虑：
        - 学科成绩匹配
        - 特长匹配
        - 学习潜力
        """
        scores = []
        
        # 学科要求匹配
        if route.subject_requirements:
            subject_match = self._match_subjects(
                route.subject_requirements,
                profile.scores
            )
            scores.append(subject_match)
        
        # 特长匹配
        if route.talent_requirements:
            talent_match = self._match_talents(
                route.talent_requirements,
                profile.special_talents
            )
            scores.append(talent_match)
        
        return sum(scores) / len(scores) if scores else 50
    
    def _score_economic(self, route: PlanningRoute, profile: StudentProfile) -> float:
        """
        经济匹配评分
        
        计算路线成本占家庭收入比例
        """
        cost_min, cost_max = route.cost_range
        avg_cost = (cost_min + cost_max) / 2
        
        # 假设家庭年收入（可根据实际情况输入）
        family_income = profile.family_income
        
        if family_income <= 0:
            return 50  # 未知收入，默认中等
        
        ratio = avg_cost / family_income
        
        if ratio < 0.1:
            return 100  # 轻松负担
        elif ratio < 0.2:
            return 85
        elif ratio < 0.3:
            return 70
        elif ratio < 0.5:
            return 50
        elif ratio < 0.8:
            return 30
        else:
            return 10  # 难以负担
    
    def _score_time(self, route: PlanningRoute, profile: StudentProfile) -> float:
        """
        时间匹配评分
        
        评估剩余时间是否足够准备
        """
        # 获取准备周期（年）
        prep_years = self._parse_preparation_period(route.preparation_period)
        
        # 获取当前年级到高三的时间
        remaining_years = self._calculate_remaining_years(profile.grade)
        
        if remaining_years >= prep_years:
            return 100  # 时间充足
        elif remaining_years >= prep_years * 0.8:
            return 80   # 时间较紧但可行
        elif remaining_years >= prep_years * 0.6:
            return 60   # 时间紧张
        else:
            return 30   # 时间不足
    
    def _score_region(self, route: PlanningRoute, profile: StudentProfile) -> float:
        """
        地域匹配评分
        
        评估目标高校地区是否符合偏好
        """
        if not profile.preferred_regions:
            return 70  # 无偏好，默认中等
        
        # 获取该路线的典型地区
        route_regions = self._get_route_regions(route)
        
        # 计算匹配度
        match_count = len(set(route_regions) & set(profile.preferred_regions))
        
        if match_count > 0:
            return 100
        else:
            return 40
    
    def _generate_recommendations(self, route, profile, dimension_scores) -> List[str]:
        """生成推荐理由"""
        reasons = []
        
        # 兴趣推荐理由
        if dimension_scores['interest'] >= 80:
            reasons.append(f"✓ 高度契合您的兴趣方向：{', '.join(profile.interests[:2])}")
        
        # 能力推荐理由
        if dimension_scores['ability'] >= 80:
            reasons.append("✓ 您的学科优势与该路线要求高度匹配")
        
        # 经济推荐理由
        if dimension_scores['economic'] >= 80:
            reasons.append("✓ 费用在家庭经济承受范围内")
        elif dimension_scores['economic'] < 50:
            reasons.append("⚠ 费用较高，需要家庭充分准备")
        
        # 时间推荐理由
        if dimension_scores['time'] >= 80:
            reasons.append("✓ 准备时间充足")
        elif dimension_scores['time'] < 60:
            reasons.append("⚠ 准备时间紧张，需要立即开始")
        
        return reasons
```

## 4. 目标生成器（TargetGenerator）

### 4.1 三档目标生成

```python
"""
目标生成器 - 为每条路线生成高/中/低三档目标
"""

class TargetGenerator:
    """目标生成器"""
    
    def __init__(self, db_connection):
        self.db = db_connection
    
    def generate_targets(self, route: PlanningRoute, profile: StudentProfile) -> Dict[str, List[Target]]:
        """
        为路线生成三档目标
        
        Returns:
            {
                'high': [Target, ...],    # 高目标（冲刺）
                'medium': [Target, ...],  # 中目标（稳妥）
                'low': [Target, ...]      # 低目标（保底）
            }
        """
        targets = {
            'high': [],
            'medium': [],
            'low': []
        }
        
        # 根据路线类型获取目标高校
        universities = self._get_target_universities(route)
        
        # 高目标：该路线能触及的最好高校
        targets['high'] = self._generate_high_targets(
            universities, route, profile
        )
        
        # 中目标：匹配学生当前水平的高校
        targets['medium'] = self._generate_medium_targets(
            universities, route, profile
        )
        
        # 低目标：确保能录取的保底高校
        targets['low'] = self._generate_low_targets(
            universities, route, profile
        )
        
        return targets
    
    def _generate_high_targets(self, universities, route, profile) -> List[Target]:
        """生成高目标"""
        # 选择该路线最好的5-10所高校
        top_unis = universities[:10]
        
        targets = []
        for uni in top_unis:
            # 获取该高校相关专业的录取数据
            majors = self._get_related_majors(uni, route)
            
            for major in majors[:2]:  # 每个高校取2个专业
                score_data = self._get_score_data(uni, major)
                
                target = Target(
                    university=uni,
                    major=major,
                    admission_type=route.route_type.value,
                    probability=self._calculate_probability(
                        score_data, profile, tier='high'
                    ),
                    score_requirement=score_data['min_score'],
                    rank_requirement=score_data['min_rank'],
                    reason=f"该路线最佳目标，需{route.preparation_period}全力准备"
                )
                targets.append(target)
        
        return targets[:5]  # 返回前5个
    
    def _generate_medium_targets(self, universities, route, profile) -> List[Target]:
        """生成中目标"""
        # 根据学生当前水平匹配
        # TODO: 实现具体逻辑
        pass
    
    def _generate_low_targets(self, universities, route, profile) -> List[Target]:
        """生成低目标"""
        # 选择保底高校
        # TODO: 实现具体逻辑
        pass
```

## 5. 完整规划流程

```python
"""
完整规划流程 - 整合所有模块
"""

class PlanningEngine:
    """规划分析引擎"""
    
    def __init__(self):
        self.route_enumerator = RouteEnumerator()
        self.matcher = MultiDimensionalMatcher()
        self.target_generator = TargetGenerator()
        self.feasibility_assessor = FeasibilityAssessor()
    
    def generate_plan(self, profile: StudentProfile) -> PlanningResult:
        """
        生成完整规划方案
        
        流程：
        1. 穷举所有路线（50-100条）
        2. 多维度匹配（过滤+评分）
        3. 排序筛选（Top 10）
        4. 生成三档目标
        5. 可行性评估
        6. 备选方案
        """
        # Step 1: 穷举路线
        all_routes = self.route_enumerator.enumerate_all_routes()
        
        # Step 2: 多维度匹配
        match_results = self.matcher.match(all_routes, profile)
        
        # Step 3: 筛选符合条件的路线并排序
        eligible_results = [
            r for r in match_results if r.is_eligible
        ]
        eligible_results.sort(key=lambda x: x.overall_score, reverse=True)
        
        top_routes = eligible_results[:10]
        
        # Step 4: 为Top路线生成三档目标
        route_targets = {}
        for result in top_routes:
            targets = self.target_generator.generate_targets(
                result.route, profile
            )
            route_targets[result.route.route_id] = {
                'route': result.route,
                'match_result': result,
                'targets': targets
            }
        
        # Step 5: 可行性评估
        feasibility = self.feasibility_assessor.assess(
            profile, route_targets
        )
        
        # Step 6: 生成备选方案
        alternatives = self._generate_alternatives(
            top_routes, feasibility
        )
        
        # Step 7: 生成行动建议
        action_plan = self._generate_action_plan(
            profile, top_routes[0] if top_routes else None
        )
        
        return PlanningResult(
            profile=profile,
            top_routes=top_routes,
            route_targets=route_targets,
            feasibility=feasibility,
            alternatives=alternatives,
            action_plan=action_plan
        )
```

---

*规划分析引擎设计 v2.1 - 更新版*

- v2.0: 自上而下分析（突破口→政策→专业→高校）
- v2.1: 穷举+匹配模式（穷举路线→多维度匹配→筛选排序→生成目标）
- v2.2: 新增方案存储与版本管理功能

---

## 6. 方案存储管理器（PlanStorageManager）

### 6.1 核心功能

| 功能 | 说明 |
|------|------|
| save_plan() | 保存规划方案，生成版本ID |
| get_latest_version() | 获取最新版本 |
| get_all_versions() | 获取所有历史版本 |
| compare_versions() | 对比两个版本差异 |

### 6.2 存储结构

```
data/plans/
├── student_001_index.json          # 学生方案索引
├── student_001_20250307_143052.json # 具体方案版本
├── student_001_20250415_092133.json
├── student_001_20250601_101245.json
└── ...
```

### 6.3 版本信息

每个方案版本包含：
- 版本ID（时间戳）
- 生成时间
- 数据版本（如2025-03-07）
- 学生当时年级
- 推荐路线列表
- 综合置信度
- 与上一版本的变更摘要

### 6.4 版本对比功能

| 对比项 | 说明 |
|------|------|
| 新增推荐 | 显示新增的升学路线 |
| 移除推荐 | 显示不再推荐的路线 |
| 置信度变化 | 显示各路线匹配度变化 |
| 目标调整 | 显示高校目标的变化 |
| 数据更新 | 标注数据版本变化 |

---

*规划分析引擎设计 v2.2 - 含方案存储功能*
