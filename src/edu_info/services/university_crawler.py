#!/usr/bin/env python3
"""
高校信息爬虫

从阳光高考等平台爬取 985/211 高校基本信息
"""
import sys
from pathlib import Path

# 添加 src 到路径
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

import json

from edu_info.models.schemas import University
from edu_info.utils.logger import setup_logger

logger = setup_logger(__name__)


class UniversityCrawler:
    """高校信息爬虫"""

    # 985 高校名单
    PROJECT_985 = [
        "清华大学", "北京大学", "中国人民大学", "北京师范大学",
        "北京理工大学", "北京航空航天大学", "中国农业大学", "中央民族大学",
        "南开大学", "天津大学", "大连理工大学", "东北大学",
        "吉林大学", "哈尔滨工业大学", "复旦大学", "同济大学",
        "上海交通大学", "华东师范大学", "南京大学", "东南大学",
        "浙江大学", "中国科学技术大学", "厦门大学", "山东大学",
        "中国海洋大学", "武汉大学", "华中科技大学", "中南大学",
        "湖南大学", "中山大学", "华南理工大学", "四川大学",
        "电子科技大学", "重庆大学", "西安交通大学", "西北工业大学",
        "兰州大学", "国防科技大学", "西北农林科技大学",
    ]

    # 211 高校（部分，不含 985）
    PROJECT_211 = [
        "北京交通大学", "北京科技大学", "北京化工大学", "北京邮电大学",
        "北京林业大学", "北京协和医学院", "北京中医药大学", "北京外国语大学",
        "对外经济贸易大学", "中央财经大学", "中国政法大学", "华北电力大学",
        "上海财经大学", "上海大学", "第二军医大学", "南京航空航天大学",
        "南京理工大学", "河海大学", "南京农业大学", "中国药科大学",
        "西南交通大学", "西南财经大学", "武汉理工大学", "西安电子科技大学",
        "长安大学", "西北大学", "辽宁大学", "大连海事大学",
        # ... 更多 211 高校
    ]

    def __init__(self, output_path: str | None = None):
        """
        初始化爬虫

        Args:
            output_path: 输出文件路径
        """
        self.output_path = output_path or "data/imports/universities.json"
        self.universities: list[University] = []
        logger.info("高校信息爬虫初始化完成")

    def crawl_from_sun_gaokao(self) -> list[University]:
        """
        从阳光高考平台爬取高校信息

        Returns:
            高校列表
        """
        logger.info("开始从阳光高考爬取高校信息...")

        # 由于阳光高考有反爬，这里使用模拟数据
        # 实际使用时需要实现真实的爬虫逻辑

        universities = []

        # 985 高校
        for i, name in enumerate(self.PROJECT_985, 1):
            location = self._get_location_from_name(name)
            uni_type = self._guess_type_from_name(name)

            university = University(
                id=i,
                name=name,
                code=f"10{i:03d}",  # 模拟代码
                location=location,
                type=uni_type,
                is_985=True,
                is_211=True,
                is_double_first_class=True,
                project_type="A 类" if i <= 36 else "B 类",
            )
            universities.append(university)

        # 211 高校（不含 985）
        for i, name in enumerate(self.PROJECT_211, len(self.PROJECT_985) + 1):
            location = self._get_location_from_name(name)
            uni_type = self._guess_type_from_name(name)

            university = University(
                id=i,
                name=name,
                code=f"10{i:03d}",
                location=location,
                type=uni_type,
                is_985=False,
                is_211=True,
                is_double_first_class=True,
                project_type=None,
            )
            universities.append(university)

        logger.info(f"爬取完成，共 {len(universities)} 所高校")
        return universities

    def crawl_from_manual(self, input_path: str) -> list[University]:
        """
        从手工整理的 Excel/JSON 文件导入

        Args:
            input_path: 输入文件路径

        Returns:
            高校列表
        """
        logger.info(f"从文件导入高校信息：{input_path}")

        input_file = Path(input_path)

        if not input_file.exists():
            logger.warning(f"文件不存在：{input_file}")
            return []

        if input_file.suffix == ".json":
            return self._load_from_json(input_file)
        elif input_file.suffix in [".xlsx", ".xls"]:
            return self._load_from_excel(input_file)
        else:
            logger.warning(f"不支持的文件格式：{input_file.suffix}")
            return []

    def _load_from_json(self, file_path: Path) -> list[University]:
        """从 JSON 加载"""
        with open(file_path, encoding="utf-8") as f:
            data = json.load(f)

        universities = []
        for i, item in enumerate(data, 1):
            university = University(
                id=item.get("id", i),
                name=item.get("name", ""),
                code=item.get("code", ""),
                location=item.get("location", ""),
                type=item.get("type", "综合"),
                is_985=item.get("is_985", False),
                is_211=item.get("is_211", False),
                is_double_first_class=item.get("is_double_first_class", False),
                project_type=item.get("project_type"),
            )
            universities.append(university)

        logger.info(f"从 JSON 加载 {len(universities)} 所高校")
        return universities

    def _load_from_excel(self, file_path: Path) -> list[University]:
        """从 Excel 加载"""
        try:
            import pandas as pd

            df = pd.read_excel(file_path)

            universities = []
            for i, row in df.iterrows():
                university = University(
                    id=row.get("id", i + 1),
                    name=row.get("name", ""),
                    code=row.get("code", ""),
                    location=row.get("location", ""),
                    type=row.get("type", "综合"),
                    is_985=row.get("is_985", False),
                    is_211=row.get("is_211", False),
                    is_double_first_class=row.get("is_double_first_class", False),
                    project_type=row.get("project_type"),
                )
                universities.append(university)

            logger.info(f"从 Excel 加载 {len(universities)} 所高校")
            return universities

        except Exception as e:
            logger.error(f"读取 Excel 失败：{e}")
            return []

    def _get_location_from_name(self, name: str) -> str:
        """从高校名称推测所在地"""
        location_map = {
            "北京": "北京", "清华": "北京", "北大": "北京",
            "天津": "天津", "南开": "天津",
            "大连": "辽宁大连", "东北": "辽宁沈阳", "吉林": "吉林长春",
            "哈尔滨": "黑龙江哈尔滨",
            "上海": "上海", "复旦": "上海", "同济": "上海",
            "南京": "江苏南京", "东南": "江苏南京",
            "浙江": "浙江杭州",
            "合肥": "安徽合肥", "中国科学技术": "安徽合肥",
            "厦门": "福建厦门",
            "山东": "山东济南", "中国海洋": "山东青岛",
            "武汉": "湖北武汉", "华中科技": "湖北武汉",
            "中南": "湖南长沙", "湖南": "湖南长沙",
            "广州": "广东广州", "中山": "广东广州", "华南理工": "广东广州",
            "成都": "四川成都", "电子科技": "四川成都",
            "重庆": "重庆",
            "西安": "陕西西安", "西北": "陕西西安", "兰州": "甘肃兰州",
        }

        for keyword, location in location_map.items():
            if keyword in name:
                return location

        return "未知"

    def _guess_type_from_name(self, name: str) -> str:
        """从名称推测高校类型"""
        type_keywords = {
            "理工": "理工", "工业": "理工", "科技": "理工", "工程": "理工",
            "师范": "师范", "农业": "农林", "林业": "农林",
            "医药": "医药", "医学": "医药", "中医": "医药",
            "财经": "财经", "经济": "财经", "贸易": "财经",
            "政法": "政法", "政治": "政法",
            "外语": "语言", "语言": "语言",
            "民族": "民族",
        }

        for keyword, uni_type in type_keywords.items():
            if keyword in name:
                return uni_type

        return "综合"

    def save_to_json(self, universities: list[University], output_path: str | None = None):
        """
        保存到 JSON 文件

        Args:
            universities: 高校列表
            output_path: 输出路径
        """
        output_file = Path(output_path or self.output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)

        data = [uni.model_dump() for uni in universities]

        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

        logger.info(f"已保存到：{output_file}")

    def save_to_excel(self, universities: list[University], output_path: str):
        """
        保存到 Excel 文件

        Args:
            universities: 高校列表
            output_path: 输出路径
        """
        try:
            import pandas as pd

            data = [uni.model_dump() for uni in universities]
            df = pd.DataFrame(data)

            output_file = Path(output_path)
            output_file.parent.mkdir(parents=True, exist_ok=True)

            df.to_excel(output_file, index=False)
            logger.info(f"已保存到 Excel: {output_file}")

        except Exception as e:
            logger.error(f"保存 Excel 失败：{e}")


def main():
    """主函数"""
    logger.info("=" * 60)
    logger.info("高校信息爬虫")
    logger.info("=" * 60)

    # 创建爬虫
    crawler = UniversityCrawler()

    # 爬取数据
    universities = crawler.crawl_from_sun_gaokao()

    # 保存
    output_path = "src/edu_info/data/universities_985_211.json"
    crawler.save_to_json(universities, output_path)

    # 统计
    logger.info("\n高校统计:")
    logger.info(f"  985 高校：{len([u for u in universities if u.is_985])} 所")
    logger.info(f"  211 高校：{len([u for u in universities if u.is_211])} 所")
    logger.info(f"  双一流：{len([u for u in universities if u.is_double_first_class])} 所")

    # 展示部分
    logger.info("\n部分高校示例:")
    for i, uni in enumerate(universities[:10], 1):
        logger.info(f"  {i}. {uni.name} ({uni.location}) - {uni.type}")

    logger.info("\n" + "=" * 60)


if __name__ == "__main__":
    main()
