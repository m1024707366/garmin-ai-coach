FROM python:3.11-slim

WORKDIR /app

# 设置环境变量
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1
ENV PYTHONPATH=/app

# 安装系统依赖
# 替换为国内阿里云源，解决安装卡住/超时
RUN sed -i 's/deb.debian.org/mirrors.aliyun.com/g' /etc/apt/sources.list.d/debian.sources \
    && apt-get update \
    && apt-get install -y \
        gcc \
        python3-dev \
        default-libmysqlclient-dev \
    && rm -rf /var/lib/apt/lists/*

# 复制依赖文件
COPY requirements.txt .

# 安装Python依赖
# 安装Python依赖，使用清华镜像源（加速）
RUN pip install --no-cache-dir -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple

# 复制整个项目（因为构建上下文是项目根目录）
COPY . .

# 调试：打印当前目录结构
RUN ls -la /app

# 启动应用（先打印调试信息）
CMD ["sh", "-c", "echo 'Python version:' && python --version && echo '\\nCurrent directory:' && pwd && echo '\\nFiles in /app:' && ls -la /app && echo '\\nTrying to import backend...' && python -c 'import backend; print(\"Success\")' || echo 'Failed' && echo '\\nStarting uvicorn...' && python -m uvicorn backend.app.main:app --host 0.0.0.0 --port 8000"]
