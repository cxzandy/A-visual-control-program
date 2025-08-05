#!/bin/bash
# Tiaozhanbei2.0 Web演示启动脚本 - 自动打开浏览器

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m'

# 项目根目录
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo -e "${CYAN}🚀 启动Tiaozhanbei2.0 Web演示模式${NC}"

# 检测操作系统
detect_os() {
    if [[ "$OSTYPE" == "linux-gnu"* ]]; then
        if command -v xdg-open >/dev/null 2>&1; then
            BROWSER_CMD="xdg-open"
        elif command -v firefox >/dev/null 2>&1; then
            BROWSER_CMD="firefox"
        elif command -v google-chrome >/dev/null 2>&1; then
            BROWSER_CMD="google-chrome"
        else
            BROWSER_CMD=""
        fi
    elif [[ "$OSTYPE" == "darwin"* ]]; then
        BROWSER_CMD="open"
    elif [[ "$OSTYPE" == "cygwin" ]] || [[ "$OSTYPE" == "msys" ]]; then
        BROWSER_CMD="start"
    else
        BROWSER_CMD=""
    fi
}

# 启动浏览器
open_browser() {
    local url="$1"
    local delay=${2:-3}
    
    if [[ -n "$BROWSER_CMD" ]]; then
        echo -e "${BLUE}⏰ ${delay}秒后自动打开浏览器...${NC}"
        (
            sleep $delay
            echo -e "${GREEN}🌐 正在打开浏览器: $url${NC}"
            $BROWSER_CMD "$url" >/dev/null 2>&1 &
        ) &
    else
        echo -e "${YELLOW}⚠️  无法自动打开浏览器，请手动访问: $url${NC}"
    fi
}

# 检查Web服务是否已启动
check_web_service() {
    local port=${1:-5000}
    local max_attempts=30
    local attempt=0
    
    echo -e "${YELLOW}🔍 等待Web服务启动...${NC}"
    
    while [ $attempt -lt $max_attempts ]; do
        if curl -s "http://localhost:$port" >/dev/null 2>&1; then
            echo -e "${GREEN}✅ Web服务已启动${NC}"
            return 0
        fi
        
        sleep 1
        ((attempt++))
        
        # 显示进度
        if [ $((attempt % 5)) -eq 0 ]; then
            echo -e "${BLUE}⏳ 等待中... ($attempt/$max_attempts)${NC}"
        fi
    done
    
    echo -e "${RED}❌ Web服务启动超时${NC}"
    return 1
}

# 主启动函数
start_demo() {
    detect_os
    
    echo -e "${BLUE}===========================================${NC}"
    echo -e "${CYAN} Tiaozhanbei2.0 Web演示模式${NC}"
    echo -e "${BLUE}===========================================${NC}"
    
    # 启动Web服务（后台）
    echo -e "${CYAN}🚀 启动Web服务...${NC}"
    
    # 确保在项目根目录
    cd "$PROJECT_ROOT"
    
    # 设置环境变量
    export PYTHONPATH="$PROJECT_ROOT:$PYTHONPATH"
    
    # 后台启动Web服务
    python web/web_simple.py >/dev/null 2>&1 &
    WEB_PID=$!
    
    # 检查服务是否启动成功
    if check_web_service 5000; then
        # 获取IP地址
        local_ip=$(hostname -I | awk '{print $1}' 2>/dev/null || echo "localhost")
        
        echo -e "${GREEN}✅ Web服务启动成功${NC}"
        echo -e "${CYAN}📱 访问地址:${NC}"
        echo -e "${GREEN}   本地: http://localhost:5000${NC}"
        echo -e "${GREEN}   局域网: http://$local_ip:5000${NC}"
        
        # 自动打开浏览器
        open_browser "http://localhost:5000" 2
        
        echo -e "${YELLOW}===========================================${NC}"
        echo -e "${CYAN}🎮 演示模式使用说明:${NC}"
        echo -e "${BLUE}1. 页面加载后，选择运行模式${NC}"
        echo -e "${BLUE}2. 点击'启动系统'开始演示${NC}"
        echo -e "${BLUE}3. 可以切换自动/手动控制模式${NC}"
        echo -e "${BLUE}4. 观察实时状态和图像处理结果${NC}"
        echo -e "${YELLOW}===========================================${NC}"
        echo -e "${CYAN}按 Ctrl+C 停止演示${NC}"
        
        # 等待用户中断
        wait $WEB_PID
    else
        echo -e "${RED}❌ Web服务启动失败${NC}"
        kill $WEB_PID 2>/dev/null
        exit 1
    fi
}

# 清理函数
cleanup() {
    echo -e "\n${YELLOW}🛑 正在停止演示服务...${NC}"
    
    # 终止Web服务进程
    if [[ -n "$WEB_PID" ]]; then
        kill $WEB_PID 2>/dev/null
        echo -e "${GREEN}✅ Web服务已停止${NC}"
    fi
    
    # 终止可能的Python进程
    pkill -f "web_simple.py" 2>/dev/null
    
    echo -e "${CYAN}👋 演示结束，感谢使用!${NC}"
    exit 0
}

# 设置中断处理
trap cleanup SIGINT SIGTERM

# 参数处理
case "${1:-}" in
    --help|-h)
        echo "Tiaozhanbei2.0 Web演示启动器"
        echo ""
        echo "用法: $0 [选项]"
        echo ""
        echo "选项:"
        echo "  --help, -h     显示此帮助信息"
        echo "  --port PORT    指定端口号 (默认: 5000)"
        echo ""
        echo "功能:"
        echo "  - 自动启动Web服务"
        echo "  - 自动打开浏览器"
        echo "  - 提供演示指导"
        echo ""
        echo "示例:"
        echo "  $0              # 启动演示模式"
        echo "  $0 --port 8080  # 使用端口8080启动"
        exit 0
        ;;
    --port)
        if [[ -n "$2" ]] && [[ "$2" =~ ^[0-9]+$ ]]; then
            echo -e "${BLUE}使用自定义端口: $2${NC}"
            # 这里可以扩展端口自定义功能
            start_demo
        else
            echo -e "${RED}❌ 无效的端口号: $2${NC}"
            exit 1
        fi
        ;;
    *)
        start_demo
        ;;
esac
