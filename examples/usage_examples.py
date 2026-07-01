"""
使用示例

展示如何使用升学规划系统的各个模块
"""

from pathlib import Path


def example_database_usage():
    """数据库使用示例"""
    print("=" * 60)
    print("示例 1: 数据库操作")
    print("=" * 60)

    from src.data.database import Database

    # 创建数据库连接
    with Database() as db:
        # 查询数据
        results = db.query("SELECT * FROM universities LIMIT 5")
        print(f"查询结果：{len(results)} 条记录")

        # DataFrame 查询
        df = db.query_df("SELECT * FROM universities")
        print(f"DataFrame 形状：{df.shape}")

        # 插入数据
        db.insert(
            "universities",
            {
                "university_id": 1001,
                "name": "示例大学",
                "code": "10001",
                "province": "辽宁",
                "city": "沈阳",
                "level": "211",
                "is_211": True,
            },
        )
        print("数据插入成功")


def example_validation():
    """数据验证使用示例"""
    print("\n" + "=" * 60)
    print("示例 2: 数据验证")
    print("=" * 60)

    from pydantic import ValidationError

    from src.utils.validators import validate_score_data, validate_student_profile

    # 验证学生档案
    profile_data = {
        "name": "张三",
        "current_grade": "高一",
        "school": "辽宁省实验中学",
        "city": "沈阳",
        "scores": {
            "语文": 120,
            "数学": 135,
            "英语": 130,
        },
        "interests": ["计算机", "人工智能"],
        "family_income": 300000,
    }

    try:
        profile = validate_student_profile(profile_data)
        print(f"✓ 学生档案验证通过：{profile.name}")
    except ValidationError as e:
        print(f"✗ 验证失败：{e}")

    # 验证分数线数据
    score_data = {
        "university_id": 1,
        "major_id": 1,
        "year": 2024,
        "admission_type": "统招",
        "subject_type": "物理类",
        "min_score": 650,
        "min_rank": 1000,
    }

    try:
        score = validate_score_data(score_data)
        print(f"✓ 分数线数据验证通过：{score.year}年，{score.min_score}分")
    except ValidationError as e:
        print(f"✗ 验证失败：{e}")


def example_error_handling():
    """错误处理使用示例"""
    print("\n" + "=" * 60)
    print("示例 3: 错误处理")
    print("=" * 60)

    from src.utils.errors import (
        DataImportError,
        DataNotFoundError,
        handle_errors,
    )

    # 使用装饰器处理错误
    @handle_errors(DataImportError)
    def import_file(file_path: str):
        path = Path(file_path)
        if not path.exists():
            raise DataImportError(f"文件不存在：{file_path}")
        return True

    # 测试错误处理
    try:
        import_file("nonexistent.xlsx")
    except DataImportError as e:
        print(f"捕获到错误：{e.user_message}")
        print(f"错误代码：{e.code}")
        print(f"详细信息：{e.details}")

    # 手动抛出错误
    try:
        raise DataNotFoundError(
            resource_type="学生档案",
            resource_id="123",
        )
    except DataNotFoundError as e:
        print(f"\n数据未找到：{e.user_message}")


def example_config_usage():
    """配置使用示例"""
    print("\n" + "=" * 60)
    print("示例 4: 配置管理")
    print("=" * 60)

    from src.utils.config import get_config

    config = get_config()

    print(f"应用名称：{config.app_name}")
    print(f"应用版本：{config.app_version}")
    print(f"调试模式：{config.debug}")
    print(f"数据库路径：{config.full_db_path}")
    print(f"日志级别：{config.log_level}")

    # 获取匹配权重
    weights = config.get_match_weights()
    print("\n匹配权重配置:")
    for key, value in weights.items():
        print(f"  {key}: {value}")

    # 验证权重
    if config.validate_weights():
        print("\n✓ 权重配置验证通过")
    else:
        print("\n✗ 权重配置验证失败")


def example_data_importer():
    """数据导入器使用示例"""
    print("\n" + "=" * 60)
    print("示例 5: 数据导入")
    print("=" * 60)

    from src.data.database import Database
    from src.data.importer import DataImporter

    # 创建导入器
    db = Database()
    importer = DataImporter(db)

    print("数据导入器已初始化")
    print("支持的导入格式:")
    print("  - Excel: 高校信息、分数线数据")
    print("  - JSON: 规划路线数据")
    print("  - CSV: 分数线数据")

    # 示例：导入分数线
    # count = importer.import_scores_excel("data/raw/scores/2024_scores.xlsx")
    # print(f"导入完成：{count} 条记录")

    importer.close()


def main():
    """运行所有示例"""
    print("\n" + "=" * 60)
    print("智能升学规划系统 - 使用示例")
    print("=" * 60)

    # 运行示例
    try:
        example_database_usage()
    except Exception as e:
        print(f"示例 1 执行失败：{e}")

    try:
        example_validation()
    except Exception as e:
        print(f"示例 2 执行失败：{e}")

    try:
        example_error_handling()
    except Exception as e:
        print(f"示例 3 执行失败：{e}")

    try:
        example_config_usage()
    except Exception as e:
        print(f"示例 4 执行失败：{e}")

    try:
        example_data_importer()
    except Exception as e:
        print(f"示例 5 执行失败：{e}")

    print("\n" + "=" * 60)
    print("所有示例执行完成")
    print("=" * 60)


if __name__ == "__main__":
    main()
