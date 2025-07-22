#!/bin/bash

# Tiaozhanbei2.0 Web界面启动脚本
# 使用说明：./start_web.sh

echo "🚀 启动Tiaozhanbei2.0 Web控制界面..."
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# 检查conda环境
if ! conda info --envs | grep -q "tiao"; then
    echo "❌ conda环境 'tiao' 不存在"
    echo "请先运行: conda create -n tiao python=3.8"
    exit 1
fi

# 检查是否已有Web服务在运行
if pgrep -f "web_simple.py" > /dev/null; then
    echo "⚠️  Web服务已在运行，正在停止..."
    pkill -f "web_simple.py"
    sleep 2
fi

echo "🔧 激活conda环境..."
echo "📱 启动Web服务器..."
echo ""
echo "🌐 本地访问: http://localhost:5000"
echo "🌐 局域网访问: http://$(hostname -I | awk '{print $1}'):5000"
echo ""
echo "⏹️  按Ctrl+C停止服务"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# 启动Flask应用
conda run -n tiao python web/web_simple.py
