"""
测试路线穷举器
"""
import sys
from pathlib import Path

import pytest

# 添加 src 到路径
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from edu_info.core.route_enumerator import RouteEnumerator


class TestRouteEnumerator:
    """测试路线穷举器"""

    @pytest.fixture
    def enumerator(self):
        """创建路线穷举器实例"""
        return RouteEnumerator()

    def test_init(self, enumerator):
        """测试初始化"""
        assert enumerator is not None
        assert isinstance(enumerator.routes, list)

    def test_enumerate_all(self, enumerator):
        """测试穷举所有路线"""
        routes = enumerator.enumerate_all("初三")

        # 验证生成了路线
        assert len(routes) > 0
        assert len(routes) >= 20, "应该至少生成 20 条路线"

        # 验证路线类型
        route_types = set(r.route_type for r in routes)
        assert "普通高考" in route_types
        assert "强基计划" in route_types
        assert "科技特长生" in route_types

    def test_gaokao_routes(self, enumerator):
        """测试普通高考路线"""
        routes = enumerator.enumerate_all("初三")
        gaokao_routes = [r for r in routes if r.route_type == "普通高考"]

        # 验证有不同层次的高考路线
        assert len(gaokao_routes) > 0

        # 验证有不同专业
        major_types = set()
        for route in gaokao_routes:
            if route.target_major_types:
                major_types.update(route.target_major_types)

        assert len(major_types) > 3, "应该有多个专业类别"

    def test_special_routes(self, enumerator):
        """测试特殊类型路线"""
        routes = enumerator.enumerate_all("初三")

        # 强基计划
        qiangji_routes = [r for r in routes if r.route_type == "强基计划"]
        assert len(qiangji_routes) > 0

        # 科技特长生
        keji_routes = [r for r in routes if r.route_type == "科技特长生"]
        assert len(keji_routes) > 0

        # 艺术特长生
        yishu_routes = [r for r in routes if r.route_type == "艺术特长生"]
        assert len(yishu_routes) > 0

        # 体育特长生
        tiyu_routes = [r for r in routes if r.route_type == "体育特长生"]
        assert len(tiyu_routes) > 0

    def test_route_fields(self, enumerator):
        """测试路线字段完整性"""
        routes = enumerator.enumerate_all("初三")

        for route in routes[:5]:  # 测试前 5 条
            assert route.route_id is not None
            assert route.route_name is not None
            assert route.route_type is not None
            assert route.category is not None
            assert route.difficulty in ["低", "中等", "高", "极高"]

    def test_filter_by_type(self, enumerator):
        """测试按类型筛选路线"""
        enumerator.enumerate_all("初三")

        # 筛选科技特长生
        keji_routes = enumerator.get_routes_by_type("科技特长生")
        assert len(keji_routes) > 0
        assert all(r.route_type == "科技特长生" for r in keji_routes)

    def test_filter_by_difficulty(self, enumerator):
        """测试按难度筛选路线"""
        enumerator.enumerate_all("初三")

        # 筛选高难度路线
        hard_routes = enumerator.get_routes_by_difficulty("高")
        assert len(hard_routes) > 0
        assert all(r.difficulty == "高" for r in hard_routes)

    def test_save_and_load(self, enumerator, tmp_path):
        """测试保存和加载路线"""
        # 生成路线
        enumerator.enumerate_all("初三")
        original_count = len(enumerator.routes)

        # 保存到临时文件
        output_file = tmp_path / "test_routes.json"
        enumerator.save_routes(str(output_file))

        # 验证文件存在
        assert output_file.exists()

        # 加载路线
        new_enumerator = RouteEnumerator()
        new_enumerator.load_routes(str(output_file))

        # 验证加载成功
        assert len(new_enumerator.routes) == original_count


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
