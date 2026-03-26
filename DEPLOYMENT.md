# Garmin AI Coach 部署文档

## 项目概述

Garmin AI Coach 是一个基于 Garmin 运动数据和 AI 技术的跑步教练应用。项目采用前后端分离架构：
- **后端**: FastAPI + Python
- **前端**: React + TypeScript + Vite
- **数据库**: MySQL
- **AI 集成**: DeepSeek, Gemini (可选)

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
LLM_PROVIDER=deepseek  # 可选: deepseek, gemini

# DeepSeek API (默认)
DEEPSEEK_API_KEY=your_deepseek_api_key

# Gemini API (可选)
# GEMINI_API_KEY=your_gemini_api_key

# 数据库配置 (MySQL)
DATABASE_URL=mysql+pymysql://username:password@localhost:3306/garmin_coach?charset=utf8mb4

# 运行模式
USE_MOCK_MODE=false  # False = 使用真实 API, True = 使用模拟数据

# 分析缓存时间（小时）
ANALYSIS_CACHE_HOURS=24

# 轮询配置
ENABLE_GARMIN_POLLING=false
GARMIN_POLL_INTERVAL_MINUTES=30

# 微信小程序配置（可选）
WECHAT_MINI_APPID=
WECHAT_MINI_SECRET=
WECHAT_SUBSCRIBE_TEMPLATE_ID=
```

### 前端配置

在 `frontend` 目录创建 `.env` 文件：

```env
VITE_API_BASE_URL=http://localhost:8000
```

## 后端部署

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

### 2. 启动后端服务

#### 方法一：使用启动脚本
```bash
cd backend
chmod +x start.sh
./start.sh
```

#### 方法二：手动启动
```bash
cd backend
python app/main.py
```

后端服务将在 `http://localhost:8000` 运行。

## 前端部署

### 1. 安装依赖

```bash
cd frontend
npm install
```

### 2. 构建前端应用

#### 方法一：使用构建脚本
```bash
cd frontend
chmod +x build.sh
./build.sh
```

#### 方法二：手动构建
```bash
cd frontend
npm run build
```

构建产物将生成在 `frontend/dist` 目录。

### 3. 部署前端

可以将 `frontend/dist` 目录部署到任何静态文件服务器：
- **Nginx**: 配置静态文件服务
- **Apache**: 配置静态文件服务
- **Vercel**: 导入前端项目
- **Netlify**: 导入前端项目

## 数据库配置

### 1. 创建数据库

```sql
CREATE DATABASE garmin_coach CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
```

### 2. 数据库初始化

应用启动时会自动创建所需的数据库表。

## 运行和测试

### 启动前后端

1. 启动后端服务（端口 8000）
2. 启动前端开发服务器：
   ```bash
   cd frontend
   npm run dev
   ```
3. 前端开发服务器默认在 `http://localhost:5173` 运行

### API 文档

后端提供自动生成的 API 文档：
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## 生产环境配置

### 后端配置

- **CORS**: 在 `backend/app/main.py` 中配置具体的前端域名
- **日志**: 配置合适的日志级别
- **进程管理**: 使用 Gunicorn 或 Supervisor 管理进程

### 前端配置

- **API 地址**: 在 `.env` 文件中配置生产环境的后端 API 地址
- **构建优化**: 使用 `npm run build` 生成优化后的生产构建
- **静态资源**: 配置合适的缓存策略

## Docker 部署（可选）

可以使用 Docker Compose 快速部署整个应用：

```yaml
# docker-compose.yml
version: '3'
services:
  backend:
    build: ./backend
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=mysql+pymysql://admin:password@db:3306/garmin_coach
    depends_on:
      - db
  
  frontend:
    build: ./frontend
    ports:
      - "80:80"
    
  db:
    image: mysql:5.7
    environment:
      - MYSQL_ROOT_PASSWORD=password
      - MYSQL_DATABASE=garmin_coach
      - MYSQL_USER=admin
      - MYSQL_PASSWORD=password
    volumes:
      - mysql_data:/var/lib/mysql

volumes:
  mysql_data:
```

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

### 3. Garmin API 认证失败

请检查：
- Garmin 邮箱和密码是否正确
- GARMIN_IS_CN 配置是否正确

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
2. **检查端口**: 确保 8000 端口没有被占用
3. **网络连接**: 检查防火墙设置和网络连接
4. **环境变量**: 确保所有必需的环境变量都已正确配置

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

## 联系和支持

如有问题或需要帮助，请查看项目文档或提交 Issue。