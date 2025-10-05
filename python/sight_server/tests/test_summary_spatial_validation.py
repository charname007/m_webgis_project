"""
测试 Summary + Spatial 组合查询的 SQL 验证

验证修复后的 _validate_summary_sql 方法能够：
1. 接受正确的空间统计查询（GROUP BY + AVG经纬度）
2. 拒绝错误的空间统计查询（只有 COUNT(*)）
"""

import logging
import sys
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from core.processors.sql_generator import SQLGenerator

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


class TestSummarySpatialValidation:
    """测试 Summary + Spatial SQL 验证"""

    def __init__(self):
        # 创建 SQLGenerator 实例（不需要真实的 LLM）
        self.generator = SQLGenerator(llm=None, base_prompt="测试提示词")

    def test_correct_sql_group_by_district(self):
        """
        测试正确的 SQL：按行政区分组 + 空间中心（推荐方式）
        """
        sql = """
        SELECT
          COALESCE(a."所属行政区", '未知') as district,
          COUNT(*) as count,
          AVG(a.lng_wgs84) as center_lng,
          AVG(a.lat_wgs84) as center_lat
        FROM a_sight a
        WHERE a."所属城市" = '武汉市'
          AND a.lng_wgs84 IS NOT NULL
          AND a.lat_wgs84 IS NOT NULL
        GROUP BY a."所属行政区"
        ORDER BY count DESC
        """

        is_valid, warning = self.generator._validate_summary_sql(
            sql, intent_type="summary", is_spatial=True
        )

        assert is_valid, f"验证失败: {warning}"
        logger.info("✓ 测试通过: 按行政区分组 + 空间中心")

    def test_correct_sql_group_by_level(self):
        """
        测试正确的 SQL：按等级分组 + 空间中心
        """
        sql = """
        SELECT
          a.level,
          COUNT(*) as count,
          AVG(a.lng_wgs84) as center_lng,
          AVG(a.lat_wgs84) as center_lat
        FROM a_sight a
        WHERE a."所属城市" = '武汉市'
          AND a.lng_wgs84 IS NOT NULL
        GROUP BY a.level
        ORDER BY a.level
        """

        is_valid, warning = self.generator._validate_summary_sql(
            sql, intent_type="summary", is_spatial=True
        )

        assert is_valid, f"验证失败: {warning}"
        logger.info("✓ 测试通过: 按等级分组 + 空间中心")

    def test_correct_sql_bbox(self):
        """
        测试正确的 SQL：空间范围统计（边界框）
        """
        sql = """
        SELECT
          COUNT(*) as total_count,
          MIN(lng_wgs84) as bbox_min_lng,
          MAX(lng_wgs84) as bbox_max_lng,
          MIN(lat_wgs84) as bbox_min_lat,
          MAX(lat_wgs84) as bbox_max_lat,
          AVG(lng_wgs84) as center_lng,
          AVG(lat_wgs84) as center_lat
        FROM a_sight
        WHERE "所属城市" = '武汉市' AND lng_wgs84 IS NOT NULL
        """

        is_valid, warning = self.generator._validate_summary_sql(
            sql, intent_type="summary", is_spatial=True
        )

        assert is_valid, f"验证失败: {warning}"
        logger.info("✓ 测试通过: 空间范围统计（边界框）")

    def test_correct_sql_geohash(self):
        """
        测试正确的 SQL：高级空间分析（ST_GeoHash）
        """
        sql = """
        SELECT
          ST_GeoHash(lng_wgs84, lat_wgs84, 4) as grid_id,
          COUNT(*) as count,
          AVG(lng_wgs84) as center_lng,
          AVG(lat_wgs84) as center_lat
        FROM a_sight
        WHERE "所属城市" = '武汉市'
          AND lng_wgs84 IS NOT NULL
        GROUP BY ST_GeoHash(lng_wgs84, lat_wgs84, 4)
        ORDER BY count DESC
        """

        is_valid, warning = self.generator._validate_summary_sql(
            sql, intent_type="summary", is_spatial=True
        )

        assert is_valid, f"验证失败: {warning}"
        logger.info("✓ 测试通过: 高级空间分析（ST_GeoHash）")

    def test_incorrect_sql_simple_count(self):
        """
        测试错误的 SQL：只有 COUNT(*)，没有空间维度（应该被拒绝）
        """
        sql = """
        SELECT COUNT(*) as count
        FROM a_sight
        WHERE "所属城市" = '武汉市'
        """

        is_valid, warning = self.generator._validate_summary_sql(
            sql, intent_type="summary", is_spatial=True
        )

        assert not is_valid, "应该拒绝只有 COUNT(*) 的查询"
        logger.info(f"✓ 测试通过: 正确拒绝简单计数查询 (原因: {warning})")

    def test_incorrect_sql_no_spatial_fields(self):
        """
        测试错误的 SQL：没有空间字段（应该被拒绝）
        """
        sql = """
        SELECT
          "所属行政区" as district,
          COUNT(*) as count
        FROM a_sight
        WHERE "所属城市" = '武汉市'
        GROUP BY "所属行政区"
        """

        is_valid, warning = self.generator._validate_summary_sql(
            sql, intent_type="summary", is_spatial=True
        )

        assert not is_valid, "应该拒绝没有空间字段的查询"
        logger.info(f"✓ 测试通过: 正确拒绝无空间字段查询 (原因: {warning})")

    def test_non_spatial_summary(self):
        """
        测试普通统计查询（非空间）：应该允许简单的 COUNT(*)
        """
        sql = """
        SELECT COUNT(*) as count
        FROM a_sight
        WHERE level = '5A'
        """

        is_valid, warning = self.generator._validate_summary_sql(
            sql, intent_type="summary", is_spatial=False
        )

        assert is_valid, f"普通统计查询应该通过验证: {warning}"
        logger.info("✓ 测试通过: 普通统计查询（非空间）")

    def run_all_tests(self):
        """运行所有测试"""
        logger.info("=" * 60)
        logger.info("开始测试 Summary + Spatial SQL 验证")
        logger.info("=" * 60)

        test_methods = [
            ("按行政区分组 + 空间中心", self.test_correct_sql_group_by_district),
            ("按等级分组 + 空间中心", self.test_correct_sql_group_by_level),
            ("空间范围统计（边界框）", self.test_correct_sql_bbox),
            ("高级空间分析（ST_GeoHash）", self.test_correct_sql_geohash),
            ("错误SQL：只有COUNT(*)", self.test_incorrect_sql_simple_count),
            ("错误SQL：没有空间字段", self.test_incorrect_sql_no_spatial_fields),
            ("普通统计查询（非空间）", self.test_non_spatial_summary),
        ]

        passed = 0
        failed = 0

        for name, test_method in test_methods:
            try:
                test_method()
                passed += 1
            except AssertionError as e:
                logger.error(f"✗ 测试失败 [{name}]: {e}")
                failed += 1
            except Exception as e:
                logger.error(f"✗ 测试异常 [{name}]: {e}")
                failed += 1

        logger.info("=" * 60)
        logger.info(f"测试结果: {passed} 通过, {failed} 失败")
        logger.info("=" * 60)

        if failed == 0:
            logger.info("🎉 所有测试通过！Summary + Spatial 验证逻辑工作正常。")
            return True
        else:
            logger.error(f"❌ 有 {failed} 个测试失败，请检查验证逻辑。")
            return False


if __name__ == "__main__":
    tester = TestSummarySpatialValidation()
    success = tester.run_all_tests()
    sys.exit(0 if success else 1)
