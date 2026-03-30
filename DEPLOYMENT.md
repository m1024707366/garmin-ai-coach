# Garmin AI Coach 部署文档

## 项目概述

Garmin AI Coach 是一个基于 Garmin 运动数据和 AI 技术的跑步教练应用。项目采用前后端分离架构：
- **后端**: FastAPI + Python
- **前端**: React + TypeScript + Vite
- **数据库**: MySQL
- **AI 集成**: DeepSeek, Gemini, OpenAI (可选)

## 系统要求

### 后端环境
- Python 3.8+
- pip
- MySQL 5.7+

### 前端环境
- Node.js 16+
- npm

## 环境变量配置

### 后端配置

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
# 本地开发示例
DATABASE_URL=mysql+pymysql://root:password@localhost:3306/garmin_coach_dev?charset=utf8mb4
# Docker部署示例
# DATABASE_URL=mysql+pymysql://user:password@host:3306/garmin_coach?charset=utf8mb4

# 运行模式
USE_MOCK_MODE=false  # False = 使用真实 API, True = 使用模拟数据

# 分析缓存时间（小时）
ANALYSIS_CACHE_HOURS=24

# 轮询配置
ENABLE_GARMIN_POLLING=false
GARMIN_POLL_INTERVAL_MINUTES=30
```

### 前端配置

在 `frontend` 目录创建 `.env` 文件：

```env
VITE_API_BASE_URL=http://localhost:8000
```

## 本地开发部署（Windows）

适用于开发和测试环境。

### 后端部署

#### 1. 安装依赖

```bash
pip install -r requirements.txt
```

#### 2. 启动后端服务

##### 方法一：使用启动脚本
```bash
cd backend
chmod +x start.sh
./start.sh
```

##### 方法二：手动启动
```bash
cd backend
python app/main.py
```

后端服务将在 `http://localhost:8000` 运行。

### 前端部署

#### 1. 安装依赖

```bash
cd frontend
npm install
```

#### 2. 启动开发服务器

```bash
cd frontend
npm run dev
```

前端开发服务器默认在 `http://localhost:5173` 运行。

### 运行和测试

1. 启动后端服务（端口 8000）
2. 启动前端开发服务器（端口 5173）
3. 访问前端应用：http://localhost:5173
4. 访问 API 文档：
   - Swagger UI: http://localhost:8000/docs
   - ReDoc: http://localhost:8000/redoc
5. 健康检查：http://localhost:8000/health

## 服务器部署（Linux）

适用于生产环境部署。

### 准备服务器

推荐使用 Linux 服务器（Ubuntu 20.04+ 或 CentOS 7+），并确保服务器已安装：
- Python 3.8+
- pip
- MySQL 5.7+
- Git

### 1. 服务器环境准备

```bash
# 更新系统
sudo apt update && sudo apt upgrade -y

# 安装依赖
sudo apt install -y python3 python3-pip python3-venv git mysql-server nginx

# 创建项目目录
sudo mkdir -p /var/www/garmin-ai-coach
sudo chown -R $USER:$USER /var/www/garmin-ai-coach
```

### 2. 数据库配置

#### 创建数据库

```sql
sudo mysql -u root -p

-- 创建数据库（开发环境）
CREATE DATABASE garmin_coach_dev CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

-- 创建数据库（生产环境）
CREATE DATABASE garmin_coach CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

-- 创建数据库用户
CREATE USER 'garmin_user'@'localhost' IDENTIFIED BY 'your_strong_password';
GRANT ALL PRIVILEGES ON garmin_coach_dev.* TO 'garmin_user'@'localhost';
GRANT ALL PRIVILEGES ON garmin_coach.* TO 'garmin_user'@'localhost';
FLUSH PRIVILEGES;
```

### 3. 部署项目

#### 3.1 克隆代码

```bash
cd /var/www/garmin-ai-coach
git clone https://github.com/your-username/garmin-ai-coach.git .
```

#### 3.2 创建环境变量文件

```bash
# 在项目根目录创建 .env 文件
cp .env.example .env

# 编辑 .env 文件，配置数据库连接和其他环境变量
nano .env
```

#### 3.3 使用部署脚本（推荐）

项目提供了自动化部署脚本：

```bash
# 设置执行权限
chmod +x scripts/deploy.sh

# 运行部署脚本（需要 root 权限）
sudo ./scripts/deploy.sh
```

部署脚本会自动：
- 停止当前运行的服务
- 拉取最新代码
- 创建/更新虚拟环境
- 安装依赖
- 启动服务

#### 3.4 手动部署步骤

```bash
# 创建虚拟环境
python3 -m venv venv

# 激活虚拟环境
source venv/bin/activate

# 升级 pip
pip install --upgrade pip

# 安装依赖
pip install -r requirements.txt

# 启动服务
nohup python3 -m uvicorn backend.app.main:app --host 0.0.0.0 --port 8000 > server.log 2>&1 &
```

### 4. 前端部署

前端可以部署到任何静态文件服务器：

#### 4.1 构建前端

```bash
cd frontend
npm install
npm run build
```

构建产物在 `frontend/dist` 目录。

#### 4.2 使用 Nginx 部署前端

```bash
# 安装 Nginx（如果尚未安装）
sudo apt install -y nginx

# 配置 Nginx
sudo nano /etc/nginx/sites-available/garmin-coach
```

配置文件内容：
```nginx
server {
    listen 80;
    server_name your-domain.com;
    
    # 前端静态文件
    location / {
        root /var/www/garmin-ai-coach/frontend/dist;
        index index.html;
        try_files $uri $uri/ /index.html;
    }
    
    # API 反向代理
    location /api/ {
        proxy_pass http://localhost:8000/;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_cache_bypass $http_upgrade;
    }
}
```

启用站点：
```bash
sudo ln -s /etc/nginx/sites-available/garmin-coach /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

### 5. 服务管理

#### 5.1 启动服务

```bash
# 使用启动脚本
chmod +x scripts/start_server.sh
./scripts/start_server.sh

# 或直接启动
cd /var/www/garmin-ai-coach
source venv/bin/activate
python3 -m uvicorn backend.app.main:app --host 0.0.0.0 --port 8000
```

#### 5.2 停止服务

```bash
# 查找进程
ps aux | grep uvicorn

# 终止进程
kill -9 <pid>
```

#### 5.3 查看日志

```bash
# 服务日志
tail -f /var/log/garmin-ai-coach.log

# 或查看当前工作目录的日志
tail -f server.log
```

### 6. 使用 systemd 管理服务（推荐）

创建 systemd 服务文件：

```bash
sudo nano /etc/systemd/system/garmin-ai-coach.service
```

内容：
```ini
[Unit]
Description=Garmin AI Coach Backend
After=network.target

[Service]
Type=simple
User=www-data
WorkingDirectory=/var/www/garmin-ai-coach
Environment=PATH=/var/www/garmin-ai-coach/venv/bin
ExecStart=/var/www/garmin-ai-coach/venv/bin/python3 -m uvicorn backend.app.main:app --host 0.0.0.0 --port 8000
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

启用服务：
```bash
sudo systemctl daemon-reload
sudo systemctl enable garmin-ai-coach
sudo systemctl start garmin-ai-coach

# 查看状态
sudo systemctl status garmin-ai-coach
```

### 7. 数据库初始化

应用启动时会自动创建所需的数据库表。如果需要手动初始化：

```bash
cd /var/www/garmin-ai-coach
source venv/bin/activate
python -c "from backend.app.db.session import init_db; init_db()"
```

## Docker 部署

适用于容器化部署环境。

### 环境要求

- Docker 20.10+
- Docker Compose 1.29+

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
```

### 5. 数据库配置

MySQL 数据库需要自行部署，不在 Docker 部署范围内。配置示例：
- **数据库名**: garmin_coach
- **字符集**: utf8mb4
- **配置示例**: `mysql+pymysql://user:password@host:3306/garmin_coach?charset=utf8mb4`

请确保数据库已创建并配置正确的用户权限。

## 生产环境配置

### 后端配置

- **CORS**: 在 `backend/app/main.py` 中配置具体的前端域名
- **日志**: 配置合适的日志级别
- **进程管理**: 使用 Gunicorn 或 Supervisor 管理进程
- **安全**: 使用 HTTPS，配置防火墙规则

### 前端配置

- **API 地址**: 在 `.env` 文件中配置生产环境的后端 API 地址
- **构建优化**: 使用 `npm run build` 生成优化后的生产构建
- **静态资源**: 配置合适的缓存策略

## 常见问题

### 1. CORS 错误

如果前端出现 CORS 错误，请检查：
- 后端 CORS 配置是否正确
- 前端 API 地址是否配置正确
- 后端服务是否正在运行

### 2. 数据库连接失败

请检查：
- MySQL 服务是否启动
- 数据库用户名和密码是否正确
- 数据库是否已创建
- 防火墙是否允许数据库连接

### 3. Garmin API 认证失败

请检查：
- Garmin 邮箱和密码是否正确
- GARMIN_IS_CN 配置是否正确
- 网络连接是否正常

### 4. LLM 响应错误

请检查：
- API 密钥是否正确
- 网络连接是否正常
- 代理配置（如果需要）

### 5. 构建失败

如果前端构建失败，请检查：
- Node.js 和 npm 版本是否符合要求
- 依赖是否安装成功
- 代码是否有语法错误

## 故障排除

1. **查看日志**: 后端日志会输出详细的错误信息
2. **检查端口**: 确保端口没有被占用
3. **网络连接**: 检查防火墙设置和网络连接
4. **环境变量**: 确保所有必需的环境变量都已正确配置
5. **数据库**: 检查数据库连接和权限

## 维护和更新

### 更新依赖

```bash
# 后端
pip install -U -r requirements.txt

# 前端
cd frontend
npm update
```

### 备份数据库

```bash
mysqldump -u username -p garmin_coach > backup.sql
```

### 查看运行状态

```bash
# 检查后端服务
curl http://localhost:8000/health

# 检查数据库连接
mysql -u username -p garmin_coach -e "SELECT 1;"
```

### 更新部署

```bash
# 拉取最新代码
git pull

# 重新部署
sudo ./scripts/deploy.sh
```

## 联系和支持

如有问题或需要帮助，请查看项目文档或提交 Issue。