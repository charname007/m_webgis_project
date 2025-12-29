#!/bin/bash

# Sight Server 快速启动脚本

set -e

echo "🚀 Sight Server Quick Start"
echo "============================"

# 检查 Python 版本
echo ""
echo "📋 检查 Python 版本..."
python_version=$(python3 --version 2>&1 | awk '{print $2}')
required_version="3.9"

if [ "$(printf '%s\n' "$required_version" "$python_version" | sort -V | head -n1)" != "$required_version" ]; then
    echo "❌ Python 版本过低，需要 3.9+，当前版本: $python_version"
    exit 1
fi
echo "✅ Python 版本: $python_version"

# 检查虚拟环境
echo ""
echo "📦 检查虚拟环境..."
if [ ! -d "venv" ]; then
    echo "⚙️  创建虚拟环境..."
    python3 -m venv venv
    echo "✅ 虚拟环境已创建"
else
    echo "✅ 虚拟环境已存在"
fi

# 激活虚拟环境
echo ""
echo "🔌 激活虚拟环境..."
source venv/bin/activate
echo "✅ 虚拟环境已激活"

# 安装依赖
echo ""
echo "📥 安装依赖..."
pip install -q --upgrade pip
pip install -q -r requirements.txt
echo "✅ 依赖安装完成"

# 检查环境变量
echo ""
echo "🔍 检查环境变量..."
if [ ! -f ".env" ]; then
    echo "⚠️  未找到 .env 文件"
    if [ -f ".env.example" ]; then
        echo "📋 从 .env.example 创建 .env..."
        cp .env.example .env
        echo "⚠️  请编辑 .env 文件并配置必需的环境变量："
        echo "   - DATABASE_URL"
        echo "   - DEEPSEEK_API_KEY"
        echo ""
        read -p "按 Enter 继续编辑 .env 文件，或按 Ctrl+C 退出..."
        ${EDITOR:-nano} .env
    else
        echo "❌ 未找到 .env.example 文件"
        exit 1
    fi
else
    echo "✅ .env 文件已存在"
fi

# 检查数据库连接（可选）
echo ""
echo "🗄️  检查数据库连接..."
if command -v psql &> /dev/null; then
    # 从 .env 读取数据库 URL
    if grep -q "DATABASE_URL" .env; then
        echo "✅ 找到数据库配置"
        # 可以添加更详细的数据库连接测试
    else
        echo "⚠️  未找到 DATABASE_URL 配置"
    fi
else
    echo "⚠️  未安装 psql，跳过数据库连接检查"
fi

# 启动服务
echo ""
echo "🎯 启动 Sight Server..."
echo "============================"
echo ""
echo "访问以下地址："
echo "  • API 文档: http://localhost:8001/docs"
echo "  • ReDoc: http://localhost:8001/redoc"
echo "  • 健康检查: http://localhost:8001/health"
echo ""
echo "按 Ctrl+C 停止服务"
echo ""

python main.py
