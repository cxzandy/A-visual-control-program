#!/bin/bash

# Tiaozhanbei2.0 Web界面演示脚本
# 快速启动并打开浏览器

echo "🎬 Tiaozhanbei2.0 Web界面演示"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# 检查环境
if ! command -v conda &> /dev/null; then
    echo "❌ 未找到conda环境"
    exit 1
fi

if ! conda info --envs | grep -q "tiao"; then
    echo "❌ conda环境 'tiao' 不存在"
    echo "请先运行安装脚本"
    exit 1
fi

# 停止已有服务
echo "🔄 停止已有Web服务..."
pkill -f "web/web_simple.py" 2>/dev/null || true
sleep 1

# 启动Web服务
echo "🚀 启动Web服务..."
conda run -n tiao python web/web_simple.py &
WEB_PID=$!

# 等待服务启动
echo "⏳ 等待服务启动..."
sleep 3

# 检查服务状态
if ! curl -s http://localhost:5000 > /dev/null; then
    echo "❌ Web服务启动失败"
    kill $WEB_PID 2>/dev/null
    exit 1
fi

echo "✅ Web服务启动成功!"
echo ""
echo "🌐 访问地址:"
echo "   本地: http://localhost:5000"
if command -v hostname &> /dev/null; then
    LOCAL_IP=$(hostname -I | awk '{print $1}')
    echo "   局域网: http://$LOCAL_IP:5000"
fi
echo ""

# 尝试打开浏览器
if command -v xdg-open &> /dev/null; then
    echo "🌐 正在打开浏览器..."
    xdg-open http://localhost:5000 &
elif command -v open &> /dev/null; then
    echo "🌐 正在打开浏览器..."
    open http://localhost:5000 &
else
    echo "💡 请手动在浏览器中打开: http://localhost:5000"
fi

echo ""
echo "📱 Web界面功能:"
echo "   ✓ 四种运行模式选择"
echo "   ✓ 实时状态监控"
echo "   ✓ 图像实时显示"
echo "   ✓ 系统日志记录"
echo "   ✓ 移动端适配"
echo ""
echo "⏹️  按Ctrl+C停止演示"

# 等待用户中断
trap "echo ''; echo '🛑 停止Web服务...'; kill $WEB_PID 2>/dev/null; echo '✅ 演示结束'; exit 0" INT

# 保持脚本运行
wait $WEB_PID
