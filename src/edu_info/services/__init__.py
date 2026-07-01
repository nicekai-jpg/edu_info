"""爬虫服务模块"""
from edu_info.services.data_importer import (
    export_to_json,
    import_majors_from_json,
    import_routes_from_json,
    import_sample_data,
    import_scores_from_excel,
    import_students_from_json,
    import_universities_from_json,
)

__all__ = [
    "import_universities_from_json",
    "import_majors_from_json",
    "import_scores_from_excel",
    "import_students_from_json",
    "import_routes_from_json",
    "import_sample_data",
    "export_to_json",
]
