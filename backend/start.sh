#!/bin/bash

# 后端启动脚本
echo "开始启动后端服务..."

# 检查是否安装了 Python
if ! command -v python3 &> /dev/null; then
    echo "错误: 未安装 Python 3，请先安装 Python 3.8+"
    exit 1
fi

# 检查是否安装了 pip
if ! command -v pip3 &> /dev/null; then
    echo "错误: 未安装 pip，请先安装 pip"
    exit 1
fi

# 安装依赖
echo "安装依赖..."
pip3 install -r ../requirements.txt

if [ $? -ne 0 ]; then
    echo "错误: 依赖安装失败"
    exit 1
fi

# 启动服务
echo "启动后端服务..."
python3 app/main.py
