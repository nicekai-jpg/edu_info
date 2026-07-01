"""
测试赛道数据仓库

验证 Track 模型和 Repository 是否正常工作
"""

import sys
from pathlib import Path

import pytest

# 添加 src 到路径
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from edu_info.data.repositories.track_repository import TrackRepository
from edu_info.models.track import Domain, MajorCategory, Track


class TestTrackRepository:
    """测试 TrackRepository"""

    @pytest.fixture
    def repo(self):
        """创建 Repository 实例"""
        return TrackRepository()

    def test_get_all_domains(self, repo):
        """测试获取所有领域"""
        domains = repo.get_all_domains()

        assert len(domains) > 0
        assert all(isinstance(d, Domain) for d in domains)

        # 验证领域名称
        domain_names = [d.domain_name for d in domains]
        assert 'AI' in domain_names
        assert '机器人' in domain_names
        assert '低空经济' in domain_names

    def test_get_domain_by_id(self, repo):
        """测试根据 ID 获取领域"""
        domain = repo.get_domain_by_id(1)

        assert domain is not None
        assert domain.domain_id == 1
        assert domain.domain_name == 'AI'

    def test_get_all_tracks(self, repo):
        """测试获取所有赛道"""
        tracks = repo.get_all_tracks()

        assert len(tracks) > 0
        assert all(isinstance(t, Track) for t in tracks)

        # 验证赛道名称
        track_names = [t.track_name for t in tracks]
        assert 'AI 算法工程师' in track_names
        assert '机器人控制算法工程师' in track_names

    def test_get_track_by_id(self, repo):
        """测试根据 ID 获取赛道"""
        track = repo.get_track_by_id(1)

        assert track is not None
        assert track.track_id == 1
        assert track.track_name == 'AI 算法工程师'

        # 验证关联数据已加载
        assert len(track.domains) > 0
        assert track.employment_info is not None
        assert track.requirements is not None

    def test_get_tracks_by_domain(self, repo):
        """测试根据领域获取赛道"""
        # AI 领域的赛道
        tracks = repo.get_tracks_by_domain(1)

        assert len(tracks) > 0
        # AI 领域应该包含 AI 算法、AI 应用、大模型等赛道
        track_names = [t.track_name for t in tracks]
        assert any('AI' in name for name in track_names)

    def test_get_track_domains(self, repo):
        """测试获取赛道关联的领域"""
        domains = repo.get_track_domains(1)

        assert len(domains) > 0
        assert any(d.domain_name == 'AI' for d in domains)

    def test_get_track_employment_info(self, repo):
        """测试获取赛道就业信息"""
        employment_info = repo.get_track_employment_info(1)

        assert employment_info is not None
        assert len(employment_info.typical_positions) > 0
        assert len(employment_info.salary_ranges) > 0

        # 测试封装方法
        salary = employment_info.get_salary_range(2)
        assert salary is not None
        assert "万" in salary

    def test_get_track_requirements(self, repo):
        """测试获取赛道能力要求"""
        requirements = repo.get_track_requirements(1)

        assert requirements is not None
        assert len(requirements.required_skills) > 0
        assert len(requirements.score_requirements) > 0

    def test_get_all_major_categories(self, repo):
        """测试获取所有专业类别"""
        categories = repo.get_all_major_categories()

        assert len(categories) > 0
        assert all(isinstance(c, MajorCategory) for c in categories)

        # 验证专业类别名称
        category_names = [c.category_name for c in categories]
        assert '计算机类' in category_names
        assert '机械类' in category_names

    def test_get_track_categories(self, repo):
        """测试获取赛道关联的专业类别"""
        categories = repo.get_track_categories(1)

        assert len(categories) > 0
        # AI 算法工程师的核心专业类别应该是计算机类或人工智能类
        category_names = [c.category_name for c in categories]
        assert '计算机类' in category_names or '人工智能类' in category_names


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
