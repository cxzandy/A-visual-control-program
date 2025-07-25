#!/bin/bash

# Tiaozhanbei2.0 转向控制系统快速启动脚本

echo "🚀 Tiaozhanbei2.0 转向控制系统"
echo "=================================="

# 检查Python环境
if ! command -v python3 &> /dev/null; then
    echo "❌ Python3 未安装"
    exit 1
fi

# 检查是否在项目根目录
if [ ! -f "src/main.py" ]; then
    echo "❌ 请在项目根目录运行此脚本"
    exit 1
fi

echo "选择启动模式:"
echo "1. 转向控制功能测试"
echo "2. 键盘控制测试"
echo "3. 完整系统（含Web界面）"
echo "4. 仅Web控制界面"
echo "5. Jetson部署模式"

read -p "请选择 (1-5): " choice

case $choice in
    1)
        echo "🔧 启动转向控制功能测试..."
        python3 test_turn_control.py
        ;;
    2)
        echo "⌨️ 启动键盘控制测试..."
        python3 test_keyboard_control.py
        ;;
    3)
        echo "🌐 启动完整系统（含Web界面）..."
        python3 run_with_web.py
        ;;
    4)
        echo "🖥️ 启动Web控制界面..."
        cd web
        python3 web_simple.py
        ;;
    5)
        echo "🤖 Jetson部署模式..."
        echo "正在启动Jetson优化版本..."
        cd scripts
        bash run_jetson.sh
        ;;
    *)
        echo "❌ 无效选择"
        exit 1
        ;;
esac
