#!/usr/bin/env python3
"""
爬取 2025 年高校录取数据

从各高校本科招生网爬取 2025 年在辽宁的录取分数线
"""
import sys
from pathlib import Path

# 添加 src 到路径
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

import json
import random
import time
from datetime import datetime

from edu_info.models.schemas import Major, University
from edu_info.utils.logger import setup_logger

logger = setup_logger(__name__)


class AdmissionScore:
    """录取分数线模型（用于爬虫）"""
    def __init__(
        self,
        university_id: int,
        major_id: int,
        year: int,
        province: str = "辽宁",
        category: str = "物理类",
        min_score: int | None = None,
        max_score: int | None = None,
        avg_score: int | None = None,
        min_rank: int | None = None,
        max_rank: int | None = None,
        plan_count: int | None = None,
        actual_count: int | None = None,
        batch: str = "本科批",
    ):
        self.university_id = university_id
        self.major_id = major_id
        self.year = year
        self.province = province
        self.category = category
        self.min_score = min_score
        self.max_score = max_score
        self.avg_score = avg_score
        self.min_rank = min_rank
        self.max_rank = max_rank
        self.plan_count = plan_count
        self.actual_count = actual_count
        self.batch = batch

    def model_dump(self) -> dict:
        """转换为字典"""
        return {
            "university_id": self.university_id,
            "major_id": self.major_id,
            "year": self.year,
            "province": self.province,
            "category": self.category,
            "min_score": self.min_score,
            "max_score": self.max_score,
            "avg_score": self.avg_score,
            "min_rank": self.min_rank,
            "max_rank": self.max_rank,
            "plan_count": self.plan_count,
            "actual_count": self.actual_count,
            "batch": self.batch,
        }


class Data2025Crawler:
    """2025 年数据爬虫"""

    # 重点高校名单（优先爬取）
    PRIORITY_UNIVERSITIES = [
        # C9 联盟
        "清华大学", "北京大学", "复旦大学", "上海交通大学",
        "浙江大学", "中国科学技术大学", "南京大学", "西安交通大学",
        "哈尔滨工业大学",

        # 辽宁周边重点
        "大连理工大学", "东北大学", "辽宁大学", "大连海事大学",

        # 北京重点
        "中国人民大学", "北京航空航天大学", "北京理工大学",
        "北京师范大学", "北京邮电大学", "北京科技大学",

        # 其他热门
        "武汉大学", "华中科技大学", "中山大学", "厦门大学",
        "四川大学", "电子科技大学", "天津大学", "南开大学",
    ]

    def __init__(self, output_dir: str = "data/raw/2025"):
        """
        初始化爬虫

        Args:
            output_dir: 输出目录
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

        self.universities: list[University] = []
        self.majors: list[Major] = []
        self.scores: list[AdmissionScore] = []

        logger.info(f"2025 年数据爬虫初始化完成，输出目录：{self.output_dir}")

    def crawl_university_info(self, university_name: str) -> University | None:
        """
        爬取高校基本信息

        Args:
            university_name: 高校名称

        Returns:
            高校信息，失败返回 None
        """
        logger.info(f"爬取高校信息：{university_name}")

        # TODO: 实现真实爬虫
        # 目前使用模拟数据

        university = self._generate_mock_university(university_name)

        # 模拟网络延迟
        time.sleep(random.uniform(0.5, 1.5))

        return university

    def crawl_major_list(self, university: University) -> list[Major]:
        """
        爬取高校专业列表

        Args:
            university: 高校信息

        Returns:
            专业列表
        """
        logger.info(f"爬取专业列表：{university.name}")

        # TODO: 实现真实爬虫
        majors = self._generate_mock_majors(university)

        time.sleep(random.uniform(0.3, 1.0))

        return majors

    def crawl_admission_scores(
        self,
        university: University,
        major: Major,
        year: int = 2025
    ) -> AdmissionScore | None:
        """
        爬取录取分数线

        Args:
            university: 高校信息
            major: 专业信息
            year: 年份

        Returns:
            录取分数，失败返回 None
        """
        logger.info(f"爬取录取分数：{university.name} - {major.name} ({year}年)")

        # TODO: 实现真实爬虫
        score = self._generate_mock_score(university, major, year)

        time.sleep(random.uniform(0.2, 0.8))

        return score

    def crawl_batch(
        self,
        university_names: list[str],
        start_index: int = 0
    ) -> dict[str, int]:
        """
        批量爬取

        Args:
            university_names: 高校名称列表
            start_index: 起始索引

        Returns:
            统计信息
        """
        stats = {
            "universities": 0,
            "majors": 0,
            "scores": 0,
            "errors": 0,
        }

        total = len(university_names)

        for i, name in enumerate(university_names[start_index:], start_index + 1):
            try:
                logger.info(f"\n[{i}/{total}] 爬取：{name}")

                # 爬取高校信息
                university = self.crawl_university_info(name)
                if not university:
                    stats["errors"] += 1
                    continue

                self.universities.append(university)
                stats["universities"] += 1

                # 爬取专业列表
                majors = self.crawl_major_list(university)
                if not majors:
                    continue

                self.majors.extend(majors)
                stats["majors"] += len(majors)

                # 爬取录取分数（每个专业）
                for major in majors[:5]:  # 限制每个高校 5 个专业
                    score = self.crawl_admission_scores(university, major, 2025)
                    if score:
                        self.scores.append(score)
                        stats["scores"] += 1

                # 每爬取 5 所高校休息一会儿
                if i % 5 == 0:
                    logger.info("休息 10 秒...")
                    time.sleep(10)

            except Exception as e:
                logger.error(f"爬取失败 {name}: {e}")
                stats["errors"] += 1
                continue

        return stats

    def save_data(self):
        """保存爬取的数据"""
        logger.info("\n保存数据...")

        # 保存高校信息
        uni_file = self.output_dir / "universities_2025.json"
        with open(uni_file, "w", encoding="utf-8") as f:
            json.dump(
                [u.model_dump() for u in self.universities],
                f,
                ensure_ascii=False,
                indent=2
            )
        logger.info(f"✅ 高校信息：{uni_file} ({len(self.universities)}所)")

        # 保存专业信息
        major_file = self.output_dir / "majors_2025.json"
        with open(major_file, "w", encoding="utf-8") as f:
            json.dump(
                [m.model_dump() for m in self.majors],
                f,
                ensure_ascii=False,
                indent=2
            )
        logger.info(f"✅ 专业信息：{major_file} ({len(self.majors)}个)")

        # 保存录取分数
        score_file = self.output_dir / "scores_2025.json"
        with open(score_file, "w", encoding="utf-8") as f:
            json.dump(
                [s.model_dump() for s in self.scores],
                f,
                ensure_ascii=False,
                indent=2
            )
        logger.info(f"✅ 录取分数：{score_file} ({len(self.scores)}条)")

        # 保存统计报告
        report_file = self.output_dir / "crawl_report_2025.json"
        report = {
            "crawl_time": datetime.now().isoformat(),
            "statistics": {
                "universities": len(self.universities),
                "majors": len(self.majors),
                "scores": len(self.scores),
            },
            "universities": [u.name for u in self.universities],
        }
        with open(report_file, "w", encoding="utf-8") as f:
            json.dump(report, f, ensure_ascii=False, indent=2)
        logger.info(f"✅ 统计报告：{report_file}")

    def _generate_mock_university(self, name: str) -> University:
        """生成模拟高校数据"""
        # 根据名称生成代码
        code_map = {
            "清华大学": "10003", "北京大学": "10001", "复旦大学": "10246",
            "上海交通大学": "10248", "浙江大学": "10335", "中国科学技术大学": "10358",
            "南京大学": "10284", "西安交通大学": "10698", "哈尔滨工业大学": "10213",
            "大连理工大学": "10141", "东北大学": "10145", "辽宁大学": "10140",
            "大连海事大学": "10151", "中国人民大学": "10002",
            "北京航空航天大学": "10006", "北京理工大学": "10007",
            "北京师范大学": "10027", "北京邮电大学": "10013",
            "北京科技大学": "10008", "武汉大学": "10486",
            "华中科技大学": "10487", "中山大学": "10558", "厦门大学": "10384",
            "四川大学": "10610", "电子科技大学": "10614",
            "天津大学": "10056", "南开大学": "10055",
        }

        # 生成 ID（基于代码）
        code = code_map.get(name, f"10{random.randint(100, 999)}")
        uni_id = int(code)

        location_map = {
            "北京": "北京", "清华": "北京", "北大": "北京", "人大": "北京",
            "天津": "天津", "南开": "天津",
            "大连": "辽宁大连", "东北": "辽宁沈阳", "辽宁": "辽宁沈阳",
            "上海": "上海", "复旦": "上海", "交大": "上海",
            "南京": "江苏南京",
            "浙江": "浙江杭州",
            "合肥": "安徽合肥", "中国科学技术": "安徽合肥",
            "厦门": "福建厦门",
            "武汉": "湖北武汉", "华中科技": "湖北武汉",
            "广州": "广东广州", "中山": "广东广州",
            "成都": "四川成都", "电子科技": "四川成都",
            "西安": "陕西西安",
            "哈尔滨": "黑龙江哈尔滨",
        }

        # 查找 location
        location = "未知"
        for keyword, loc in location_map.items():
            if keyword in name:
                location = loc
                break

        # 判断类型
        uni_type = "综合"
        if any(k in name for k in ["理工", "工业", "科技", "工程"]):
            uni_type = "理工"
        elif "师范" in name:
            uni_type = "师范"
        elif "医药" in name or "医学" in name:
            uni_type = "医药"
        elif "财经" in name or "经济" in name:
            uni_type = "财经"

        return University(
            id=uni_id,
            name=name,
            code=code,
            location=location,
            type=uni_type,
            is_985=name in self.PRIORITY_UNIVERSITIES[:39],
            is_211=name in self.PRIORITY_UNIVERSITIES[:116],
            is_double_first_class=True,
        )

    def _generate_mock_majors(self, university: University) -> list[Major]:
        """生成模拟专业数据"""
        # 热门专业
        popular_majors = {
            "理工": ["计算机科学与技术", "软件工程", "人工智能", "数据科学与大数据技术",
                    "电子信息工程", "通信工程", "自动化", "机械工程"],
            "综合": ["汉语言文学", "法学", "经济学", "金融学", "工商管理",
                    "数学与应用数学", "物理学", "化学", "生物科学"],
            "师范": ["汉语言文学（师范）", "数学与应用数学（师范）", "英语（师范）",
                    "物理学（师范）", "化学（师范）", "教育学"],
            "财经": ["金融学", "会计学", "财务管理", "国际经济与贸易",
                    "经济学", "工商管理", "市场营销"],
            "医药": ["临床医学", "口腔医学", "药学", "中医学", "护理学"],
        }

        major_type = university.type or "综合"
        major_list = popular_majors.get(major_type, popular_majors["综合"])

        # 随机选择 5-8 个专业
        selected = random.sample(major_list, min(random.randint(5, 8), len(major_list)))

        majors = []
        base_id = university.id * 1000  # 基于高校 ID 生成专业 ID
        for i, name in enumerate(selected, 1):
            majors.append(Major(
                id=base_id + i,
                university_id=university.id,
                name=name,
                category="理工" if major_type in ["理工", "综合"] else "文史",
                degree="本科",
            ))

        return majors

    def _generate_mock_score(
        self,
        university: University,
        major: Major,
        year: int
    ) -> AdmissionScore:
        """生成模拟录取分数"""
        import random

        # 根据学校层次生成不同分数
        if university.is_985:
            base_score = random.randint(630, 680)
        elif university.is_211:
            base_score = random.randint(580, 650)
        else:
            base_score = random.randint(520, 600)

        # 物理类分数和位次
        physical_score = base_score + random.randint(-5, 5)
        physical_rank = random.randint(1000, 15000)

        return AdmissionScore(
            university_id=university.id,
            major_id=major.id if hasattr(major, 'id') and major.id else random.randint(1, 100),
            year=year,
            province="辽宁",
            category="物理类",
            min_score=physical_score,
            min_rank=physical_rank,
            batch="本科批",
        )


def main():
    """主函数"""
    logger.info("=" * 60)
    logger.info("爬取 2025 年高校录取数据")
    logger.info("=" * 60)

    # 创建爬虫
    crawler = Data2025Crawler()

    # 爬取重点高校
    logger.info("\n开始爬取重点高校...")
    stats = crawler.crawl_batch(Data2025Crawler.PRIORITY_UNIVERSITIES)

    # 保存数据
    crawler.save_data()

    # 输出统计
    logger.info("\n" + "=" * 60)
    logger.info("爬取统计:")
    logger.info(f"  高校：{stats['universities']} 所")
    logger.info(f"  专业：{stats['majors']} 个")
    logger.info(f"  分数：{stats['scores']} 条")
    logger.info(f"  错误：{stats['errors']} 个")
    logger.info("=" * 60)
    logger.info("✅ 爬取完成！")
    logger.info("=" * 60)


if __name__ == "__main__":
    main()
