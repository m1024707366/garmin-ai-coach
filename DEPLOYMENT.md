# 前后端分离部署文档

## 项目结构

```
garmin-ai-coach/
├── backend/          # 后端 Python 应用
│   ├── app/          # 后端源代码
│   └── start.sh      # 后端启动脚本
├── frontend/         # 前端 React 应用
│   ├── src/          # 前端源代码
│   ├── build.sh      # 前端构建脚本
│   └── dist/         # 前端构建产物
├── requirements.txt  # 后端依赖
└── DEPLOYMENT.md     # 部署文档
```

## 后端部署

### 1. 环境要求
- Python 3.8+
- pip

### 2. 配置环境变量
在 `backend/app` 目录下创建 `.env` 文件，配置以下环境变量：

```
# 数据库配置
DATABASE_URL="postgresql://user:password@localhost:5432/garmin_coach"

# Garmin 账号配置
GARMIN_EMAIL="your_garmin_email"
GARMIN_PASSWORD="your_garmin_password"

# LLM 配置
LLM_PROVIDER="openai"  # 可选: openai, gemini, deepseek
OPENAI_API_KEY="your_openai_api_key"

# 其他配置
ENABLE_GARMIN_POLLING=true
```

### 3. 启动后端服务

#### 方法一：使用启动脚本

```bash
cd backend
chmod +x start.sh
./start.sh
```

#### 方法二：手动启动

```bash
cd backend
pip install -r ../requirements.txt
python app/main.py
```

后端服务将在 `http://localhost:8000` 运行。

## 前端部署

### 1. 环境要求
- Node.js 16+
- npm

### 2. 配置环境变量
在 `frontend` 目录下创建 `.env` 文件，配置以下环境变量：

```
VITE_API_BASE_URL="http://localhost:8000"  # 后端 API 地址
```

### 3. 构建前端应用

#### 方法一：使用构建脚本

```bash
cd frontend
chmod +x build.sh
./build.sh
```

#### 方法二：手动构建

```bash
cd frontend
npm install
npm run build
```

构建产物将生成在 `frontend/dist` 目录。

### 4. 部署前端应用

可以将 `frontend/dist` 目录部署到任何静态文件服务器，例如：

- **Nginx**：配置静态文件服务
- **Apache**：配置静态文件服务
- **GitHub Pages**：上传 dist 目录
- **Vercel**：导入前端项目
- **Netlify**：导入前端项目

## 生产环境配置

### 1. 后端配置

- **数据库**：使用 PostgreSQL 或其他生产级数据库
- **CORS**：在 `backend/app/main.py` 中配置具体的前端域名
- **环境变量**：使用环境变量管理敏感信息
- **日志**：配置合适的日志级别

### 2. 前端配置

- **API 地址**：在 `.env` 文件中配置生产环境的后端 API 地址
- **构建优化**：使用 `npm run build` 生成优化后的生产构建
- **静态资源**：配置合适的缓存策略

## 测试前后端连接

1. 启动后端服务
2. 启动前端开发服务器或部署前端构建产物
3. 打开前端应用，检查是否能正常访问后端 API

## 常见问题

### 1. CORS 错误

如果前端出现 CORS 错误，请检查：
- 后端 CORS 配置是否正确
- 前端 API 地址是否配置正确
- 后端服务是否正在运行

### 2. API 调用失败

如果 API 调用失败，请检查：
- 后端服务是否正在运行
- 后端 API 地址是否正确
- 后端是否有相关 API 端点
- 网络连接是否正常

### 3. 构建失败

如果前端构建失败，请检查：
- Node.js 和 npm 版本是否符合要求
- 依赖是否安装成功
- 代码是否有语法错误
