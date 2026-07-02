# -*- coding: utf-8 -*-
"""
选科限制库与规则校验引擎
依据教育部发布的《普通高校本科招生专业选考科目要求指引（通用版）》，
提供对高校招生专业选科要求（首选科目物理/历史、再选科目化学等）的自动识别与校验。
"""
from typing import List, Tuple, Optional
import logging

logger = logging.getLogger("subject_validator")

class SubjectValidator:
    # 2024/2025/2026 年教育部指引规定的理工农医类专业核心关键词（必选物理和化学）
    SCIENCE_ENGINEERING_MEDICINE_KEYWORDS = [
        "计算机", "软件", "人工智能", "大数据", "数据科学", "网络工程", "信息安全", "智能科学",
        "电子", "通信", "微电子", "集成电路", "光电", "自动化", "机械", "电气", "土木", "建筑",
        "化学", "化工", "材料", "物理", "数学", "统计", "生物", "医学", "临床", "口腔", "药",
        "护理", "控制", "航空", "航天", "交通", "海洋", "地质", "环境", "食品", "农业", "林业",
        "理科", "工科", "基础医学", "农学", "力学", "水利", "测绘", "地矿", "安全工程", "能源"
    ]

    @classmethod
    def get_required_subjects(cls, major_name: str, category: str) -> Tuple[str, List[str]]:
        """
        根据专业名称和科类自动推断高考专业选科要求限制。
        返回: (首选科目要求, 再选科目要求列表)
        """
        if not major_name:
            return ("无限制", [])
            
        # 物理类理工农医专业，根据新选科指引 100% 必须物理+化学
        if category == "物理类":
            if any(k in major_name for k in cls.SCIENCE_ENGINEERING_MEDICINE_KEYWORDS):
                return ("物理", ["化学"])
            return ("物理", [])
        else:
            # 历史类专业，首选要求历史，暂无化学等强限制
            return ("历史", [])

    @classmethod
    def is_eligible(cls, student_subjects: Optional[List[str]], major_name: str, category: str) -> Tuple[bool, str]:
        """
        验证考生的选科组合是否符合专业选科要求。
        参数:
            student_subjects: 考生的科目列表，如 ['物理', '地理', '生物']。如果为 None/空，则自动根据科类赋予标准默认值。
            major_name: 专业或大类专业名称，如 '计算机类'
            category: 学生高考类别，'物理类' 或 '历史类'
        """
        if not student_subjects:
            # 如果没填，默认视为符合要求（物理+化学+生物 或 历史+政治+地理）
            if category == "物理类":
                student_subjects = ["物理", "化学", "生物"]
            else:
                student_subjects = ["历史", "政治", "地理"]
                
        # 清洗考生科目名称（去除空格和类字等）
        student_subjects_cleaned = [s.strip() for s in student_subjects if s]
        
        req_primary, req_secondaries = cls.get_required_subjects(major_name, category)
        
        # 1. 校验首选科目
        if req_primary != "无限制" and req_primary not in student_subjects_cleaned:
            return False, f"首选科目冲突：专业要求首选 [{req_primary}]，考生未选"
            
        # 2. 校验再选科目（如必选化学）
        for req in req_secondaries:
            if req not in student_subjects_cleaned:
                return False, f"再选科目冲突：专业要求必选 [{req}]，考生未选"
                
        return True, "符合选科要求"
