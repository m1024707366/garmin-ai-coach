#!/bin/bash

# 前端构建脚本
echo "开始构建前端应用..."

# 检查是否安装了 npm
if ! command -v npm &> /dev/null; then
    echo "错误: 未安装 npm，请先安装 Node.js"
    exit 1
fi

# 安装依赖
echo "安装依赖..."
npm install

if [ $? -ne 0 ]; then
    echo "错误: 依赖安装失败"
    exit 1
fi

# 构建应用
echo "构建应用..."
npm run build

if [ $? -ne 0 ]; then
    echo "错误: 构建失败"
    exit 1
fi

echo "前端构建完成！构建产物位于 dist/ 目录"
echo "可以将 dist/ 目录部署到任何静态文件服务器"
echo "例如：nginx, Apache, GitHub Pages, Vercel 等"
