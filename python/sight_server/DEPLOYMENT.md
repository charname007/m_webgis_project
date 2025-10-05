# Sight Server 部署指南

本指南介绍如何部署 Sight Server 到生产环境。

## 📋 目录

- [Docker 部署（推荐）](#docker-部署推荐)
- [手动部署](#手动部署)
- [环境配置](#环境配置)
- [健康检查](#健康检查)
- [故障排除](#故障排除)

## Docker 部署（推荐）

使用 Docker Compose 快速部署完整环境。

### 前置要求

- Docker 20.10+
- Docker Compose 2.0+

### 快速开始

1. **克隆项目并进入目录**
```bash
cd sight_server
```

2. **配置环境变量**
```bash
cp .env.example .env
# 编辑 .env 文件，至少配置以下必需项：
# - DEEPSEEK_API_KEY
```

3. **启动服务**
```bash
# 启动所有服务
docker-compose up -d

# 查看日志
docker-compose logs -f sight_server

# 仅启动核心服务（不包括 PgAdmin）
docker-compose up -d postgres sight_server
```

4. **验证部署**
```bash
# 健康检查
curl http://localhost:8001/health

# 测试查询
curl -X POST http://localhost:8001/query \
  -H "Content-Type: application/json" \
  -d '{"query": "查询浙江省的5A景区", "limit": 5}'
```

### 服务说明

启动后包含以下服务：

| 服务 | 端口 | 说明 |
|------|------|------|
| sight_server | 8001 | Sight Server API |
| postgres | 5432 | PostgreSQL + PostGIS |
| pgadmin | 5050 | PgAdmin Web UI（可选） |

### Docker Compose 命令

```bash
# 启动服务
docker-compose up -d

# 停止服务
docker-compose down

# 重启服务
docker-compose restart sight_server

# 查看日志
docker-compose logs -f sight_server

# 进入容器
docker-compose exec sight_server bash

# 查看服务状态
docker-compose ps

# 停止并删除数据卷（慎用）
docker-compose down -v
```

### 启动 PgAdmin（可选）

```bash
# 使用 profile 启动 PgAdmin
docker-compose --profile tools up -d

# 访问 PgAdmin
open http://localhost:5050
# 默认账号: admin@sight.com
# 默认密码: admin (在 .env 中配置)
```

## 手动部署

### 系统要求

- Python 3.9+
- PostgreSQL 13+ with PostGIS 3.0+
- 2GB+ RAM
- 1 CPU 核心

### 部署步骤

1. **安装系统依赖**

**Ubuntu/Debian:**
```bash
sudo apt-get update
sudo apt-get install -y \
    python3.9 \
    python3.9-venv \
    python3-pip \
    postgresql-15 \
    postgresql-15-postgis-3 \
    build-essential
```

**CentOS/RHEL:**
```bash
sudo yum install -y \
    python39 \
    python39-devel \
    postgresql15-server \
    postgresql15-contrib \
    postgis33_15
```

2. **创建数据库**
```sql
-- 以 postgres 用户登录
sudo -u postgres psql

-- 创建数据库和用户
CREATE DATABASE WGP_db;
CREATE USER sagasama WITH PASSWORD 'your_password';
GRANT ALL PRIVILEGES ON DATABASE WGP_db TO sagasama;

-- 启用 PostGIS 扩展
\c WGP_db
CREATE EXTENSION postgis;
```

3. **部署应用**
```bash
# 创建应用目录
sudo mkdir -p /opt/sight_server
sudo chown $USER:$USER /opt/sight_server
cd /opt/sight_server

# 克隆代码
git clone <repository> .

# 创建虚拟环境
python3.9 -m venv venv
source venv/bin/activate

# 安装依赖
pip install -r requirements.txt

# 配置环境变量
cp .env.example .env
nano .env
```

4. **使用 systemd 管理服务**

创建 `/etc/systemd/system/sight-server.service`:

```ini
[Unit]
Description=Sight Server API
After=network.target postgresql.service
Wants=postgresql.service

[Service]
Type=simple
User=www-data
Group=www-data
WorkingDirectory=/opt/sight_server
Environment="PATH=/opt/sight_server/venv/bin"
EnvironmentFile=/opt/sight_server/.env
ExecStart=/opt/sight_server/venv/bin/python main.py
Restart=always
RestartSec=10

# 日志
StandardOutput=append:/var/log/sight-server/access.log
StandardError=append:/var/log/sight-server/error.log

# 安全设置
NoNewPrivileges=true
PrivateTmp=true

[Install]
WantedBy=multi-user.target
```

启动服务：
```bash
# 创建日志目录
sudo mkdir -p /var/log/sight-server
sudo chown www-data:www-data /var/log/sight-server

# 重新加载 systemd
sudo systemctl daemon-reload

# 启动服务
sudo systemctl start sight-server

# 设置开机自启
sudo systemctl enable sight-server

# 查看状态
sudo systemctl status sight-server

# 查看日志
sudo journalctl -u sight-server -f
```

5. **配置 Nginx 反向代理（可选）**

创建 `/etc/nginx/sites-available/sight-server`:

```nginx
upstream sight_backend {
    server 127.0.0.1:8001;
}

server {
    listen 80;
    server_name sight.yourdomain.com;

    # 日志
    access_log /var/log/nginx/sight-server-access.log;
    error_log /var/log/nginx/sight-server-error.log;

    # 请求大小限制
    client_max_body_size 10M;

    location / {
        proxy_pass http://sight_backend;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;

        # 超时设置
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }

    # API 文档
    location /docs {
        proxy_pass http://sight_backend/docs;
    }

    location /redoc {
        proxy_pass http://sight_backend/redoc;
    }
}
```

启用配置：
```bash
sudo ln -s /etc/nginx/sites-available/sight-server /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

## 环境配置

### 生产环境配置建议

```env
# ==================== 数据库配置 ====================
DATABASE_URL=postgresql://user:password@localhost:5432/WGP_db
DB_POOL_SIZE=10
DB_MAX_OVERFLOW=20
DB_POOL_TIMEOUT=30

# ==================== LLM 配置 ====================
DEEPSEEK_API_KEY=sk-xxx
LLM_TEMPERATURE=1.0  # 生产环境建议降低温度

# ==================== 服务器配置 ====================
SERVER_HOST=0.0.0.0
SERVER_PORT=8001
SERVER_RELOAD=false  # 生产环境必须为 false
DEBUG=false          # 生产环境必须为 false

# ==================== 日志配置 ====================
LOG_LEVEL=INFO  # 生产环境使用 INFO 或 WARNING

# ==================== Agent 配置 ====================
AGENT_MAX_ITERATIONS=15
AGENT_MAX_EXECUTION_TIME=90

# ==================== CORS 配置 ====================
# 生产环境应限制允许的源
CORS_ORIGINS=["https://yourdomain.com"]
```

### 安全建议

1. **使用强密码**
   - 数据库密码至少 16 位
   - 定期轮换密码

2. **限制 CORS**
   ```env
   CORS_ORIGINS=["https://yourdomain.com", "https://app.yourdomain.com"]
   ```

3. **使用 HTTPS**
   - 配置 SSL 证书（Let's Encrypt）
   - 强制 HTTPS 跳转

4. **防火墙配置**
   ```bash
   # 仅开放必要端口
   sudo ufw allow 22/tcp   # SSH
   sudo ufw allow 80/tcp   # HTTP
   sudo ufw allow 443/tcp  # HTTPS
   sudo ufw enable
   ```

5. **数据库安全**
   - 禁用 PostgreSQL 远程访问（仅本地）
   - 使用独立的数据库用户
   - 定期备份数据

## 健康检查

### API 健康检查

```bash
# 简单检查
curl http://localhost:8001/health

# 详细检查
curl http://localhost:8001/health | jq
```

期望输出：
```json
{
  "status": "healthy",
  "message": "All systems operational",
  "agent_status": "initialized",
  "database_status": "connected",
  "version": "1.0.0"
}
```

### 监控指标

建议监控以下指标：

- **响应时间**: 95th percentile < 3s
- **错误率**: < 1%
- **可用性**: > 99.9%
- **数据库连接**: < 80% pool size

### 日志监控

```bash
# 查看错误日志
tail -f /var/log/sight-server/error.log

# 查看最近的错误
grep ERROR /var/log/sight-server/error.log | tail -20

# 统计错误数量
grep ERROR /var/log/sight-server/error.log | wc -l
```

## 故障排除

### 1. 服务启动失败

**检查日志**:
```bash
# Docker
docker-compose logs sight_server

# Systemd
sudo journalctl -u sight-server -n 50
```

**常见问题**:
- 数据库连接失败 → 检查 `DATABASE_URL`
- API Key 无效 → 检查 `DEEPSEEK_API_KEY`
- 端口被占用 → 修改 `SERVER_PORT`

### 2. 数据库连接问题

```bash
# 测试数据库连接
psql "postgresql://user:password@localhost:5432/WGP_db" -c "\dt"

# 检查 PostGIS 扩展
psql WGP_db -c "SELECT PostGIS_Version();"
```

### 3. Agent 初始化失败

检查：
1. LLM API 可访问性
2. 数据库表是否存在
3. 日志中的详细错误信息

### 4. 性能问题

**数据库优化**:
```sql
-- 创建索引
CREATE INDEX idx_sight_province ON a_sight(所属省份);
CREATE INDEX idx_sight_level ON a_sight(level);
CREATE INDEX idx_sight_geom ON a_sight USING GIST(geom);

-- 分析表
ANALYZE a_sight;
```

**连接池调优**:
```env
DB_POOL_SIZE=20
DB_MAX_OVERFLOW=30
```

### 5. Docker 相关问题

```bash
# 查看容器状态
docker-compose ps

# 重新构建镜像
docker-compose build --no-cache sight_server

# 查看容器资源使用
docker stats

# 进入容器调试
docker-compose exec sight_server bash
```

## 备份和恢复

### 数据库备份

```bash
# 创建备份
docker-compose exec postgres pg_dump -U sagasama WGP_db > backup_$(date +%Y%m%d).sql

# 恢复备份
docker-compose exec -T postgres psql -U sagasama WGP_db < backup_20250104.sql
```

### 自动备份脚本

```bash
#!/bin/bash
# /opt/scripts/backup-sight-db.sh

BACKUP_DIR="/opt/backups/sight_db"
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="$BACKUP_DIR/sight_db_$DATE.sql"

mkdir -p $BACKUP_DIR

# 创建备份
docker-compose exec -T postgres pg_dump -U sagasama WGP_db > $BACKUP_FILE

# 压缩
gzip $BACKUP_FILE

# 删除 7 天前的备份
find $BACKUP_DIR -name "*.sql.gz" -mtime +7 -delete

echo "Backup completed: $BACKUP_FILE.gz"
```

配置 cron:
```bash
# 每天凌晨 2 点备份
0 2 * * * /opt/scripts/backup-sight-db.sh >> /var/log/backup.log 2>&1
```

## 扩展部署

### 负载均衡

使用 Nginx 配置多个后端：

```nginx
upstream sight_backend {
    server 127.0.0.1:8001;
    server 127.0.0.1:8002;
    server 127.0.0.1:8003;
}
```

### 容器编排（Kubernetes）

参考 `kubernetes/` 目录中的配置文件（待补充）。

---

**更新日期**: 2025-10-04
**版本**: 1.0.0
