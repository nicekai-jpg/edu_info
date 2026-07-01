"""
路线穷举器

生成 50-100 条可能的升学路线
"""
import json
from pathlib import Path

from edu_info.models.schemas import PlanningRoute
from edu_info.utils.logger import setup_logger

logger = setup_logger(__name__)


class RouteEnumerator:
    """路线穷举器"""

    # 路线类型定义
    ROUTE_TYPES = {
        "gaokao": {
            "name": "普通高考",
            "categories": ["985 高校", "211 高校", "双一流", "普通本科"],
            "difficulties": ["高", "中等", "低"],
        },
        "qiangji": {
            "name": "强基计划",
            "categories": ["基础学科", "应用学科"],
            "difficulties": ["极高", "高"],
        },
        "keji": {
            "name": "科技特长生",
            "categories": ["信息学", "机器人", "科创"],
            "difficulties": ["高", "中等"],
        },
        "yishu": {
            "name": "艺术特长生",
            "categories": ["音乐", "美术", "舞蹈", "传媒"],
            "difficulties": ["高", "中等", "低"],
        },
        "tiyu": {
            "name": "体育特长生",
            "categories": ["田径", "球类", "游泳", "其他"],
            "difficulties": ["高", "中等", "低"],
        },
        "zongping": {
            "name": "综合评价",
            "categories": ["综合素质", "学科特长"],
            "difficulties": ["高", "中等"],
        },
    }

    # 专业类别
    MAJOR_CATEGORIES = [
        "计算机类", "电子信息类", "机械类", "自动化类",
        "医学类", "经济类", "法学类", "文学类",
        "理学类", "工学类", "农学类", "管理学类"
    ]

    def __init__(self, db_path: str | None = None):
        """
        初始化路线穷举器

        Args:
            db_path: 数据库路径（可选）
        """
        self.db_path = db_path
        self.routes: list[PlanningRoute] = []
        logger.info("路线穷举器初始化完成")

    def enumerate_all(self, student_grade: str = "初三") -> list[PlanningRoute]:
        """
        穷举所有可能的升学路线

        Args:
            student_grade: 学生当前年级

        Returns:
            路线列表
        """
        logger.info(f"开始穷举路线（学生年级：{student_grade}）")

        self.routes = []

        # 1. 普通高考路线
        self._add_gaokao_routes(student_grade)

        # 2. 强基计划路线
        self._add_qiangji_routes(student_grade)

        # 3. 科技特长生路线
        self._add_keji_routes(student_grade)

        # 4. 艺术特长生路线
        self._add_yishu_routes(student_grade)

        # 5. 体育特长生路线
        self._add_tiyu_routes(student_grade)

        # 6. 综合评价路线
        self._add_zongping_routes(student_grade)

        logger.info(f"路线穷举完成，共生成 {len(self.routes)} 条路线")
        return self.routes

    def _add_gaokao_routes(self, student_grade: str):
        """添加普通高考路线"""
        # 高校层次
        university_levels = [
            ("985 高校", "高", 30, 50, ["985"]),
            ("211 高校", "中等", 20, 40, ["211", "985"]),
            ("双一流", "中等", 15, 35, ["双一流", "211", "985"]),
            ("普通本科", "低", 5, 20, ["普通"]),
        ]

        for level_name, difficulty, cost_min, cost_max, uni_types in university_levels:
            for major_cat in self.MAJOR_CATEGORIES[:6]:  # 前 6 个热门专业
                route = PlanningRoute(
                    route_id=f"gaokao_{level_name}_{major_cat}",
                    route_name=f"{level_name} - {major_cat}",
                    route_type="普通高考",
                    category="普通高考",
                    description=f"通过普通高考考入{level_name}的{major_cat}专业",
                    target_university_types=uni_types,
                    target_major_types=[major_cat],
                    cost_min=cost_min,
                    cost_max=cost_max,
                    difficulty=difficulty,
                    success_rate=self._estimate_gaokao_success_rate(level_name),
                    related_policies=["普通高考招生政策"],
                )
                self.routes.append(route)

    def _add_qiangji_routes(self, student_grade: str):
        """添加强基计划路线"""
        disciplines = [
            ("数学", "基础学科"),
            ("物理", "基础学科"),
            ("化学", "基础学科"),
            ("生物", "基础学科"),
            ("历史", "基础学科"),
            ("哲学", "基础学科"),
        ]

        for major, _category in disciplines:
            route = PlanningRoute(
                route_id=f"qiangji_{major}",
                route_name=f"强基计划 - {major}",
                route_type="强基计划",
                category="拔尖人才",
                description=f"通过强基计划考入{major}专业，本硕博贯通培养",
                requirements={
                    "成绩要求": "年级前 5%",
                    "学科特长": f"{major}竞赛省级以上奖项",
                    "综合素质": "优秀"
                },
                target_university_types=["985"],
                target_major_types=[major],
                cost_min=20,
                cost_max=50,
                difficulty="极高",
                success_rate="5-10%",
                related_policies=["强基计划招生政策"],
            )
            self.routes.append(route)

    def _add_keji_routes(self, student_grade: str):
        """添加科技特长生路线"""
        tech_categories = [
            ("信息学", "NOIP/NOI 竞赛", ["计算机类", "电子信息类"]),
            ("机器人", "机器人竞赛", ["自动化类", "机械类"]),
            ("科创", "科技创新大赛", ["电子信息类", "计算机类"]),
        ]

        for tech_type, competition, majors in tech_categories:
            route = PlanningRoute(
                route_id=f"keji_{tech_type}",
                route_name=f"科技特长生 - {tech_type}",
                route_type="科技特长生",
                category="特长生",
                description=f"通过{tech_type}特长生降分录取",
                requirements={
                    "竞赛要求": f"{competition}省级以上奖项",
                    "成绩要求": "年级前 20%",
                    "准备时间": "2-3 年"
                },
                target_university_types=["985", "211"],
                target_major_types=majors,
                cost_min=30,
                cost_max=80,
                difficulty="高",
                success_rate="10-20%",
                related_policies=["科技特长生招生政策"],
            )
            self.routes.append(route)

    def _add_yishu_routes(self, student_grade: str):
        """添加艺术特长生路线"""
        art_categories = ["音乐", "美术", "舞蹈", "传媒"]

        for art_type in art_categories:
            route = PlanningRoute(
                route_id=f"yishu_{art_type}",
                route_name=f"艺术特长生 - {art_type}",
                route_type="艺术特长生",
                category="特长生",
                description=f"通过{art_type}特长生降分录取",
                requirements={
                    "专业要求": f"{art_type}专业水平测试优秀",
                    "成绩要求": "达到艺术类分数线",
                    "准备时间": "5-10 年"
                },
                target_university_types=["211", "双一流", "普通"],
                target_major_types=[f"{art_type}类"],
                cost_min=50,
                cost_max=150,
                difficulty="高",
                success_rate="15-25%",
                related_policies=["艺术特长生招生政策"],
            )
            self.routes.append(route)

    def _add_tiyu_routes(self, student_grade: str):
        """添加体育特长生路线"""
        sport_categories = ["田径", "球类", "游泳"]

        for sport_type in sport_categories:
            route = PlanningRoute(
                route_id=f"tiyu_{sport_type}",
                route_name=f"体育特长生 - {sport_type}",
                route_type="体育特长生",
                category="特长生",
                description=f"通过{sport_type}特长生降分录取",
                requirements={
                    "专业要求": f"{sport_type}国家二级运动员以上",
                    "成绩要求": "达到体育类分数线",
                    "准备时间": "5-10 年"
                },
                target_university_types=["211", "双一流", "普通"],
                target_major_types=["体育类"],
                cost_min=20,
                cost_max=60,
                difficulty="高",
                success_rate="10-20%",
                related_policies=["体育特长生招生政策"],
            )
            self.routes.append(route)

    def _add_zongping_routes(self, student_grade: str):
        """添加综合评价路线"""
        route = PlanningRoute(
            route_id="zongping_comprehensive",
            route_name="综合评价招生",
            route_type="综合评价",
            category="多元升学",
            description="通过综合素质评价和高校考核录取",
            requirements={
                "成绩要求": "年级前 15%",
                "综合素质": "优秀",
                "面试表现": "良好以上"
            },
            target_university_types=["985", "211"],
            target_major_types=self.MAJOR_CATEGORIES[:8],
            cost_min=15,
            cost_max=40,
            difficulty="高",
            success_rate="20-30%",
            related_policies=["综合评价招生政策"],
        )
        self.routes.append(route)

    def _estimate_gaokao_success_rate(self, level: str) -> str:
        """估算高考成功率"""
        rates = {
            "985 高校": "10-15%",
            "211 高校": "20-30%",
            "双一流": "30-40%",
            "普通本科": "60-80%",
        }
        return rates.get(level, "未知")

    def get_routes_by_type(self, route_type: str) -> list[PlanningRoute]:
        """
        根据类型筛选路线

        Args:
            route_type: 路线类型

        Returns:
            筛选后的路线列表
        """
        return [r for r in self.routes if r.route_type == route_type]

    def get_routes_by_difficulty(self, difficulty: str) -> list[PlanningRoute]:
        """
        根据难度筛选路线

        Args:
            difficulty: 难度等级

        Returns:
            筛选后的路线列表
        """
        return [r for r in self.routes if r.difficulty == difficulty]

    def save_routes(self, output_path: str):
        """
        保存路线到 JSON 文件

        Args:
            output_path: 输出文件路径
        """
        routes_data = [r.model_dump() for r in self.routes]

        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)

        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(routes_data, f, ensure_ascii=False, indent=2)

        logger.info(f"路线已保存到：{output_file}")

    def load_routes(self, input_path: str):
        """
        从 JSON 文件加载路线

        Args:
            input_path: 输入文件路径
        """
        input_file = Path(input_path)

        if not input_file.exists():
            logger.warning(f"路线文件不存在：{input_file}")
            return

        with open(input_file, encoding="utf-8") as f:
            routes_data = json.load(f)

        self.routes = [PlanningRoute(**data) for data in routes_data]
        logger.info(f"已加载 {len(self.routes)} 条路线")
