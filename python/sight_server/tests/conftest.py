"""
测试配置文件
提供测试环境的通用配置和fixture
"""

import pytest
import os
import sys

# 添加项目根目录到 Python 路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))


@pytest.fixture(scope="session")
def test_config():
    """测试配置fixture"""
    return {
        "database_url": os.getenv("TEST_DATABASE_URL", "postgresql://test:test@localhost:5432/test_db"),
        "api_base_url": "http://localhost:8001",
        "timeout": 30
    }


@pytest.fixture(scope="session")
def sample_queries():
    """测试查询样本"""
    return {
        "simple": "查询浙江省的5A景区",
        "statistical": "统计浙江省有多少个4A景区",
        "spatial": "查找距离杭州10公里内的景区",
        "complex": "查找杭州市评分大于4.5且门票低于100的景区"
    }
