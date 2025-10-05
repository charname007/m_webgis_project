"""
API 端点测试
测试所有 FastAPI 端点的功能
"""

import pytest
import requests
import time


class TestHealthEndpoints:
    """健康检查端点测试"""

    @pytest.fixture(autouse=True)
    def setup(self, test_config):
        """设置测试配置"""
        self.base_url = test_config["api_base_url"]
        self.timeout = test_config["timeout"]

    def test_root_health_check(self):
        """测试根路径健康检查"""
        response = requests.get(f"{self.base_url}/", timeout=self.timeout)

        assert response.status_code == 200
        data = response.json()

        assert "status" in data
        assert "message" in data
        assert "agent_status" in data
        assert "version" in data

    def test_health_endpoint(self):
        """测试详细健康检查"""
        response = requests.get(f"{self.base_url}/health", timeout=self.timeout)

        assert response.status_code == 200
        data = response.json()

        assert data["status"] in ["healthy", "degraded"]
        assert data["agent_status"] in ["initialized", "not_initialized"]
        assert data["database_status"] in ["connected", "error", "unknown"]
        assert "version" in data


class TestQueryEndpoints:
    """查询端点测试"""

    @pytest.fixture(autouse=True)
    def setup(self, test_config, sample_queries):
        """设置测试配置"""
        self.base_url = test_config["api_base_url"]
        self.timeout = test_config["timeout"]
        self.queries = sample_queries

    def test_standard_query(self):
        """测试标准查询端点"""
        payload = {
            "query": self.queries["simple"],
            "limit": 10,
            "include_sql": False
        }

        response = requests.post(
            f"{self.base_url}/query",
            json=payload,
            timeout=self.timeout
        )

        assert response.status_code == 200
        data = response.json()

        # 检查响应结构
        assert "status" in data
        assert "answer" in data
        assert "data" in data or data.get("count", 0) == 0
        assert "count" in data
        assert "message" in data
        assert "execution_time" in data

        # 检查状态
        assert data["status"] in ["success", "error", "partial"]

    def test_standard_query_with_sql(self):
        """测试返回 SQL 的查询"""
        payload = {
            "query": self.queries["simple"],
            "limit": 10,
            "include_sql": True
        }

        response = requests.post(
            f"{self.base_url}/query",
            json=payload,
            timeout=self.timeout
        )

        assert response.status_code == 200
        data = response.json()

        # 应该包含 SQL 字段
        if data["status"] == "success":
            assert "sql" in data

    def test_geojson_query(self):
        """测试 GeoJSON 查询端点"""
        payload = {
            "query": self.queries["simple"],
            "coordinate_system": "wgs84",
            "limit": 100,
            "include_properties": True
        }

        response = requests.post(
            f"{self.base_url}/query/geojson",
            json=payload,
            timeout=self.timeout
        )

        assert response.status_code == 200
        data = response.json()

        # 检查 GeoJSON 结构
        assert data["type"] == "FeatureCollection"
        assert "features" in data
        assert "metadata" in data

        # 检查元数据
        metadata = data["metadata"]
        assert "count" in metadata
        assert "coordinate_system" in metadata
        assert metadata["coordinate_system"] == "wgs84"

    def test_geojson_query_gcj02(self):
        """测试 GCJ02 坐标系 GeoJSON 查询"""
        payload = {
            "query": self.queries["simple"],
            "coordinate_system": "gcj02",
            "limit": 10
        }

        response = requests.post(
            f"{self.base_url}/query/geojson",
            json=payload,
            timeout=self.timeout
        )

        assert response.status_code == 200
        data = response.json()

        assert data["metadata"]["coordinate_system"] == "gcj02"

    def test_thought_chain_query(self):
        """测试思维链查询端点"""
        payload = {
            "query": self.queries["statistical"],
            "verbose": True
        }

        response = requests.post(
            f"{self.base_url}/query/thought-chain",
            json=payload,
            timeout=self.timeout
        )

        assert response.status_code == 200
        data = response.json()

        # 检查响应结构
        assert "status" in data
        assert "final_answer" in data
        assert "thought_chain" in data
        assert "step_count" in data
        assert "sql_queries" in data

        # 如果成功，应该有思维链步骤
        if data["status"] == "success":
            assert data["step_count"] > 0

    def test_thought_chain_query_non_verbose(self):
        """测试非详细模式的思维链查询"""
        payload = {
            "query": self.queries["statistical"],
            "verbose": False
        }

        response = requests.post(
            f"{self.base_url}/query/thought-chain",
            json=payload,
            timeout=self.timeout
        )

        assert response.status_code == 200
        data = response.json()

        # 非详细模式下思维链应该为空
        assert data["thought_chain"] == []


class TestDatabaseEndpoints:
    """数据库端点测试"""

    @pytest.fixture(autouse=True)
    def setup(self, test_config):
        """设置测试配置"""
        self.base_url = test_config["api_base_url"]
        self.timeout = test_config["timeout"]

    def test_get_tables(self):
        """测试获取表列表"""
        response = requests.get(f"{self.base_url}/tables", timeout=self.timeout)

        assert response.status_code in [200, 503]  # 503 if agent not initialized

        if response.status_code == 200:
            data = response.json()

            assert "status" in data
            assert "tables" in data
            assert "count" in data
            assert "spatial_tables" in data
            assert "spatial_count" in data

    def test_get_database_info(self):
        """测试获取数据库信息"""
        response = requests.get(f"{self.base_url}/database/info", timeout=self.timeout)

        assert response.status_code in [200, 503]

        if response.status_code == 200:
            data = response.json()
            assert "status" in data


class TestValidation:
    """输入验证测试"""

    @pytest.fixture(autouse=True)
    def setup(self, test_config):
        """设置测试配置"""
        self.base_url = test_config["api_base_url"]
        self.timeout = test_config["timeout"]

    def test_empty_query(self):
        """测试空查询"""
        payload = {
            "query": "",
            "limit": 10
        }

        response = requests.post(
            f"{self.base_url}/query",
            json=payload,
            timeout=self.timeout
        )

        # 应该返回验证错误
        assert response.status_code == 422

    def test_dangerous_query(self):
        """测试危险查询（包含 DROP）"""
        payload = {
            "query": "DROP TABLE a_sight",
            "limit": 10
        }

        response = requests.post(
            f"{self.base_url}/query",
            json=payload,
            timeout=self.timeout
        )

        # 应该返回验证错误
        assert response.status_code == 422

    def test_invalid_limit(self):
        """测试无效的 limit 参数"""
        payload = {
            "query": "查询浙江省的5A景区",
            "limit": 1000  # 超过最大值 100
        }

        response = requests.post(
            f"{self.base_url}/query",
            json=payload,
            timeout=self.timeout
        )

        # 应该返回验证错误
        assert response.status_code == 422

    def test_invalid_coordinate_system(self):
        """测试无效的坐标系"""
        payload = {
            "query": "查询浙江省的5A景区",
            "coordinate_system": "invalid_system"
        }

        response = requests.post(
            f"{self.base_url}/query/geojson",
            json=payload,
            timeout=self.timeout
        )

        # 应该返回验证错误
        assert response.status_code == 422


class TestPerformance:
    """性能测试"""

    @pytest.fixture(autouse=True)
    def setup(self, test_config, sample_queries):
        """设置测试配置"""
        self.base_url = test_config["api_base_url"]
        self.timeout = test_config["timeout"]
        self.queries = sample_queries

    def test_query_response_time(self):
        """测试查询响应时间"""
        payload = {
            "query": self.queries["simple"],
            "limit": 10
        }

        start_time = time.time()
        response = requests.post(
            f"{self.base_url}/query",
            json=payload,
            timeout=self.timeout
        )
        end_time = time.time()

        assert response.status_code == 200

        # 响应时间应该在合理范围内（例如 < 10秒）
        response_time = end_time - start_time
        assert response_time < 10.0, f"查询耗时过长: {response_time:.2f}s"

    def test_concurrent_queries(self):
        """测试并发查询"""
        import concurrent.futures

        payload = {
            "query": self.queries["simple"],
            "limit": 10
        }

        def make_request():
            return requests.post(
                f"{self.base_url}/query",
                json=payload,
                timeout=self.timeout
            )

        # 并发发送 5 个请求
        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            futures = [executor.submit(make_request) for _ in range(5)]
            results = [f.result() for f in concurrent.futures.as_completed(futures)]

        # 所有请求都应该成功
        for response in results:
            assert response.status_code == 200


# 运行测试
if __name__ == "__main__":
    pytest.main([__file__, "-v"])
