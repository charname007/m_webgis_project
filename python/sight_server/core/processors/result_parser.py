"""
结果解析器模块 - Sight Server
负责解析和合并多步查询结果
"""

import logging
from typing import List, Dict, Any, Optional

logger = logging.getLogger(__name__)


class ResultParser:
    """
    结果解析器

    功能:
    - 合并多步查询结果
    - 数据去重和整合
    - 结果质量评估
    """

    def __init__(self):
        """初始化结果解析器"""
        self.logger = logger

    def merge_results(
        self,
        results: List[Dict[str, Any]],
        merge_key: str = "name"
    ) -> List[Dict[str, Any]]:
        """
        合并多个查询结果

        策略:
        1. 使用 merge_key 作为主键去重
        2. 合并相同记录的字段（后续查询补充缺失字段）
        3. 保留所有唯一记录

        Args:
            results: 查询结果列表
            merge_key: 用于合并的主键字段

        Returns:
            合并后的结果列表
        """
        if not results:
            return []

        # 使用字典存储合并结果，key为merge_key的值
        merged_dict: Dict[str, Dict[str, Any]] = {}

        for result_set in results:
            if not result_set or not isinstance(result_set, list):
                continue

            for record in result_set:
                if not isinstance(record, dict):
                    continue

                # 获取主键值
                key_value = record.get(merge_key)
                if not key_value:
                    # 如果没有主键，使用全部字段的hash
                    key_value = hash(frozenset(record.items()))

                # 合并记录
                if key_value in merged_dict:
                    # 已存在，更新字段（补充缺失字段）
                    existing_record = merged_dict[key_value]
                    for field, value in record.items():
                        # 只更新缺失或为None的字段
                        if field not in existing_record or existing_record[field] is None:
                            existing_record[field] = value
                else:
                    # 新记录，直接添加
                    merged_dict[key_value] = record.copy()

        # 转换为列表
        merged_list = list(merged_dict.values())

        self.logger.info(
            f"Merged {len(results)} result sets into {len(merged_list)} unique records"
        )

        return merged_list

    def evaluate_completeness(
        self,
        data: List[Dict[str, Any]],
        required_fields: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        评估结果完整性

        Args:
            data: 查询结果数据
            required_fields: 必需字段列表（可选）

        Returns:
            完整性评估结果:
            {
                "complete": bool,
                "completeness_score": float (0-1),
                "missing_fields": List[str],
                "records_with_missing": int,
                "total_records": int
            }
        """
        if not data:
            return {
                "complete": False,
                "completeness_score": 0.0,
                "missing_fields": [],
                "records_with_missing": 0,
                "total_records": 0
            }

        # 默认必需字段
        if required_fields is None:
            required_fields = [
                'name', 'level', 'coordinates',
                '评分', '门票', '介绍'
            ]

        total_records = len(data)
        records_with_missing = 0
        all_missing_fields = set()

        # 检查每条记录
        for record in data:
            record_missing = []
            for field in required_fields:
                if field not in record or record[field] is None:
                    record_missing.append(field)

            if record_missing:
                records_with_missing += 1
                all_missing_fields.update(record_missing)

        # 计算完整性分数
        completeness_score = 1.0 - (records_with_missing / total_records)

        # 判断是否完整
        complete = completeness_score >= 0.9  # 90%以上视为完整

        return {
            "complete": complete,
            "completeness_score": round(completeness_score, 2),
            "missing_fields": list(all_missing_fields),
            "records_with_missing": records_with_missing,
            "total_records": total_records
        }

    def deduplicate(
        self,
        data: List[Dict[str, Any]],
        key_field: str = "name"
    ) -> List[Dict[str, Any]]:
        """
        数据去重

        Args:
            data: 数据列表
            key_field: 用于去重的字段

        Returns:
            去重后的数据列表
        """
        if not data:
            return []

        seen = set()
        deduplicated = []

        for record in data:
            key_value = record.get(key_field)
            if key_value and key_value not in seen:
                seen.add(key_value)
                deduplicated.append(record)
            elif not key_value:
                # 如果没有去重字段，保留该记录
                deduplicated.append(record)

        removed_count = len(data) - len(deduplicated)
        if removed_count > 0:
            self.logger.info(f"Removed {removed_count} duplicate records")

        return deduplicated

    def filter_by_quality(
        self,
        data: List[Dict[str, Any]],
        min_fields: int = 3
    ) -> List[Dict[str, Any]]:
        """
        按质量过滤结果（移除字段过少的记录）

        Args:
            data: 数据列表
            min_fields: 最小字段数

        Returns:
            过滤后的数据列表
        """
        if not data:
            return []

        filtered = [
            record for record in data
            if len([v for v in record.values() if v is not None]) >= min_fields
        ]

        removed_count = len(data) - len(filtered)
        if removed_count > 0:
            self.logger.info(f"Filtered out {removed_count} low-quality records")

        return filtered


# 测试代码
if __name__ == "__main__":
    # 配置日志
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    print("=== ResultParser 测试 ===\n")

    parser = ResultParser()

    # 测试1: 合并结果
    print("--- 测试1: 合并结果 ---")
    result1 = [
        {"name": "西湖", "level": "5A", "coordinates": [120.15, 30.28]},
        {"name": "千岛湖", "level": "5A"}
    ]
    result2 = [
        {"name": "西湖", "评分": "4.8", "门票": "免费"},  # 补充西湖的详细信息
        {"name": "灵隐寺", "level": "4A"}
    ]

    merged = parser.merge_results([result1, result2])
    print(f"Merged {len(merged)} records:")
    for record in merged:
        print(f"  {record}")
    print()

    # 测试2: 评估完整性
    print("--- 测试2: 评估完整性 ---")
    evaluation = parser.evaluate_completeness(merged)
    print(f"Complete: {evaluation['complete']}")
    print(f"Completeness score: {evaluation['completeness_score']}")
    print(f"Missing fields: {evaluation['missing_fields']}")
    print(f"Records with missing: {evaluation['records_with_missing']}/{evaluation['total_records']}")
    print()

    # 测试3: 去重
    print("--- 测试3: 去重 ---")
    duplicate_data = [
        {"name": "西湖", "level": "5A"},
        {"name": "西湖", "level": "5A"},  # 重复
        {"name": "千岛湖", "level": "5A"}
    ]
    deduplicated = parser.deduplicate(duplicate_data)
    print(f"Deduplicated: {len(duplicate_data)} -> {len(deduplicated)} records")
    print()

    # 测试4: 质量过滤
    print("--- 测试4: 质量过滤 ---")
    mixed_quality_data = [
        {"name": "西湖", "level": "5A", "coordinates": [120, 30], "评分": "4.8"},  # 4个字段
        {"name": "千岛湖"},  # 只有1个字段
        {"name": "灵隐寺", "level": "4A", "coordinates": [120, 30]}  # 3个字段
    ]
    filtered = parser.filter_by_quality(mixed_quality_data, min_fields=3)
    print(f"Filtered: {len(mixed_quality_data)} -> {len(filtered)} records (min_fields=3)")
