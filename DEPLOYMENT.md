# Garmin AI Coach Docker 部署文档

## 项目概述

Garmin AI Coach 是一个基于 Garmin 运动数据和 AI 技术的跑步教练应用。项目采用前后端分离架构：
- **后端**: FastAPI + Python
- **前端**: React + TypeScript + Vite
- **数据库**: MySQL（外部部署）
- **AI 集成**: DeepSeek, Gemini, OpenAI (可选)

## 环境要求

- Docker 20.10+
- Docker Compose 1.29+
- MySQL 5.7+（外部部署）

## 环境变量配置

在项目根目录创建 `.env` 文件，配置以下环境变量：

```env
# Garmin API 配置
GARMIN_EMAIL=your_garmin_email@example.com
GARMIN_PASSWORD=your_garmin_password
GARMIN_IS_CN=false  # True 表示中国区，False 表示国际版

# Garmin 凭证加密密钥
GARMIN_CRED_ENCRYPTION_KEY=your_32_byte_encryption_key

# LLM 配置
LLM_PROVIDER=deepseek  # 可选: deepseek, gemini, openai

# DeepSeek API (默认)
DEEPSEEK_API_KEY=your_deepseek_api_key

# Gemini API (可选)
# GEMINI_API_KEY=your_gemini_api_key

# OpenAI API (可选)
# OPENAI_API_KEY=your_openai_api_key

# 数据库配置 (MySQL)
# 请配置外部 MySQL 数据库连接
DATABASE_URL=mysql+pymysql://user:password@host:3306/garmin_coach?charset=utf8mb4

# 运行模式
USE_MOCK_MODE=false  # False = 使用真实 API, True = 使用模拟数据

# 分析缓存时间（小时）
ANALYSIS_CACHE_HOURS=24

# 轮询配置
ENABLE_GARMIN_POLLING=false
GARMIN_POLL_INTERVAL_MINUTES=30
```

## Docker 部署

### 1. 配置环境变量

```bash
# 复制环境变量文件
cp .env.example .env

# 编辑 .env 文件，配置数据库连接和其他环境变量
nano .env
```

### 2. 启动服务

```bash
# 构建并启动容器
docker compose up -d --build
```

### 3. 访问地址

- **前端应用**: http://localhost:3000
- **后端 API**: http://localhost:8000
- **健康检查**: http://localhost:8000/health
- **API 文档**: http://localhost:8000/docs

### 4. 常用命令

```bash
# 查看日志
docker logs garmin-coach-backend
docker logs garmin-coach-frontend

# 停止服务
docker compose down

# 重启服务
docker compose restart

# 查看容器状态
docker compose ps

# 进入后端容器
docker exec -it garmin-coach-backend bash

# 重新构建并启动
docker compose up -d --build
```

### 5. 数据库配置

MySQL 数据库需要自行部署，不在 Docker 部署范围内。配置要求：

- **数据库名**: garmin_coach
- **字符集**: utf8mb4
- **配置示例**: `mysql+pymysql://user:password@host:3306/garmin_coach?charset=utf8mb4`

请确保：
1. 数据库已创建
2. 数据库用户有足够的权限（CREATE, INSERT, UPDATE, DELETE, SELECT）
3. 数据库服务可从容器网络访问

## 生产环境配置

### 安全配置

- **HTTPS**: 使用 Nginx 或 Traefik 配置 HTTPS
- **CORS**: 在 `backend/app/main.py` 中配置具体的前端域名
- **防火墙**: 只开放必要的端口（80, 443）

### 性能优化

- **资源限制**: 在 `docker-compose.yml` 中配置容器资源限制
- **缓存**: 配置适当的缓存策略
- **日志**: 配置集中式日志管理

## 常见问题

### 1. 数据库连接失败

请检查：
- MySQL 服务是否启动
- 数据库用户名和密码是否正确
- 数据库是否已创建
- 防火墙是否允许数据库连接
- 数据库主机地址是否正确（容器网络可达）

### 2. Garmin API 认证失败

请检查：
- Garmin 邮箱和密码是否正确
- GARMIN_IS_CN 配置是否正确
- 网络连接是否正常
- Garmin 账号是否启用了两步验证

### 3. LLM 响应错误

请检查：
- API 密钥是否正确
- 网络连接是否正常
- 代理配置（如果需要）
- API 服务是否正常运行

### 4. 构建失败

如果构建失败，请检查：
- Docker 是否有足够的磁盘空间
- 网络连接是否正常
- 依赖是否可以正常下载
- 代码是否有语法错误

### 5. 端口冲突

如果端口 3000 或 8000 已被占用，请修改 `docker-compose.yml` 中的端口映射：

```yaml
services:
  backend:
    ports:
      - "8001:8000"  # 修改主机端口
    
  frontend:
    ports:
      - "3001:80"  # 修改主机端口
```

## 故障排除

1. **查看日志**: 
   ```bash
   docker logs garmin-coach-backend
   docker logs garmin-coach-frontend
   ```

2. **检查容器状态**:
   ```bash
   docker compose ps
   ```

3. **检查网络连接**:
   ```bash
   docker network inspect garmin-coach-network
   ```

4. **检查环境变量**:
   ```bash
   docker exec garmin-coach-backend env | grep -E "GARMIN_|DATABASE_URL|LLM_"
   ```

5. **测试数据库连接**:
   ```bash
   docker exec garmin-coach-backend python -c "from sqlalchemy import create_engine; engine = create_engine('${DATABASE_URL}'); engine.connect()"
   ```

## 维护和更新

### 更新代码

```bash
# 拉取最新代码
git pull

# 重新构建并启动
docker compose up -d --build
```

### 备份数据库

```bash
mysqldump -u username -p garmin_coach > backup.sql
```

### 更新依赖

```bash
# 更新 requirements.txt 后重新构建
docker compose up -d --build
```

### 查看运行状态

```bash
# 检查后端服务
curl http://localhost:8000/health

# 检查前端服务
curl http://localhost:3000
```

## 联系和支持

如有问题或需要帮助，请查看项目文档或提交 Issue。
