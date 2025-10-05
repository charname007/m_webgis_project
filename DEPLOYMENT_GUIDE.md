# Web GIS 项目部署指南

## 环境配置说明

本项目支持开发环境和生产环境的自动切换，通过环境变量配置实现。

### 前端环境配置

#### 开发环境
- 配置文件：`m_WGP_vue3/.env.development`
- 后端地址：`http://localhost:8081`
- 启动命令：`npm run dev`

#### 生产环境
- 配置文件：`m_WGP_vue3/.env.production`
- 后端地址：根据实际部署环境配置
- 构建命令：`npm run build`

#### 环境变量优先级
1. `.env.local` (本地覆盖，不提交到版本控制)
2. `.env.development` 或 `.env.production` (环境特定)
3. `.env` (共享配置)

### 后端环境配置

#### 开发环境
- 配置文件：`be/src/main/resources/application-dev.properties`
- 端口：8081
- 数据库：本地 PostgreSQL

#### 生产环境
- 配置文件：`be/src/main/resources/application-prod.properties`
- 端口：8080 (可通过环境变量覆盖)
- 数据库：通过环境变量配置

#### Profile 激活
- 默认激活开发环境：`spring.profiles.active=dev`
- 生产环境激活：设置环境变量 `SPRING_PROFILES_ACTIVE=prod`

## 部署流程

### 1. 开发环境部署

#### 前端
```bash
cd m_WGP_vue3
npm install
npm run dev
```

#### 后端
```bash
cd be
./mvnw spring-boot:run -Dspring.profiles.active=dev
```

### 2. 生产环境部署

#### 前端构建
```bash
cd m_WGP_vue3
npm install
npm run build
```

构建后的文件在 `dist/` 目录，部署到 Web 服务器。

#### 后端部署
```bash
cd be
# 构建 JAR 包
./mvnw clean package -DskipTests

# 运行生产环境
java -jar target/be-*.jar --spring.profiles.active=prod
```

### 3. 环境变量配置（生产环境）

#### 前端环境变量
在部署时设置：
```bash
# 使用服务器IP
export VITE_API_BASE_URL=http://YOUR_SERVER_IP:8080

# 或使用域名
export VITE_API_BASE_URL=https://api.your-domain.com
```

#### 后端环境变量
```bash
# 服务器端口
export SERVER_PORT=8080

# 数据库配置
export DB_HOST=your-db-host
export DB_PORT=5432
export DB_NAME=WGP_db
export DB_USERNAME=your-username
export DB_PASSWORD=your-password

# 前端域名（用于CORS）
export FRONTEND_URL=https://your-domain.com
```

### 4. Docker 部署（可选）

#### 前端 Dockerfile
```dockerfile
FROM nginx:alpine
COPY dist/ /usr/share/nginx/html/
COPY nginx.conf /etc/nginx/nginx.conf
EXPOSE 80
```

#### 后端 Dockerfile
```dockerfile
FROM openjdk:17-jdk-slim
COPY target/be-*.jar app.jar
EXPOSE 8080
ENTRYPOINT ["java", "-jar", "/app.jar", "--spring.profiles.active=prod"]
```

## 环境切换验证

### 开发环境验证
1. 前端访问 `http://localhost:5173`
2. 检查浏览器控制台输出：`API 配置已加载: {mode: "development", baseURL: "http://localhost:8081"}`
3. 后端运行在 `http://localhost:8081`

### 生产环境验证
1. 前端访问生产域名
2. 检查网络请求，确认后端地址为生产环境配置
3. 后端运行在配置的生产端口

## 故障排除

### 常见问题

1. **CORS 错误**
   - 检查后端 `spring.web.cors.allowed-origins` 配置
   - 确保前端域名在允许列表中

2. **环境变量不生效**
   - 确认配置文件命名正确
   - 检查环境变量优先级
   - 重启应用使配置生效

3. **端口冲突**
   - 开发环境：8081
   - 生产环境：8080
   - 可通过环境变量覆盖

### 日志检查

- 前端：浏览器开发者工具控制台
- 后端：应用启动日志，检查激活的 Profile

## 安全建议

1. 生产环境不要使用默认密码
2. 数据库连接信息通过环境变量配置
3. 前端构建后检查是否包含敏感信息
4. 使用 HTTPS 协议
5. 配置适当的 CORS 策略
