#!/bin/bash
# Tiaozhanbei2.0 Web服务启动脚本

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# 项目根目录
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo -e "${CYAN}🚀 启动Tiaozhanbei2.0 Web控制界面${NC}"
echo -e "${BLUE}项目目录: $PROJECT_ROOT${NC}"

# 检查Python环境
check_python_env() {
    echo -e "${YELLOW}🔍 检查Python环境...${NC}"
    
    # 检查是否在虚拟环境中
    if [[ -n "$VIRTUAL_ENV" ]]; then
        echo -e "${GREEN}✅ 检测到虚拟环境: $VIRTUAL_ENV${NC}"
    elif [[ -n "$CONDA_DEFAULT_ENV" ]]; then
        echo -e "${GREEN}✅ 检测到Conda环境: $CONDA_DEFAULT_ENV${NC}"
    else
        echo -e "${YELLOW}⚠️  未检测到虚拟环境，建议激活虚拟环境${NC}"
        read -p "是否继续? (y/N): " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            echo -e "${RED}❌ 用户取消启动${NC}"
            exit 1
        fi
    fi
    
    # 检查Python版本
    python_version=$(python --version 2>&1 | cut -d' ' -f2)
    echo -e "${BLUE}Python版本: $python_version${NC}"
    
    # 检查Flask是否安装
    if ! python -c "import flask" 2>/dev/null; then
        echo -e "${RED}❌ Flask未安装，正在安装...${NC}"
        pip install flask
    else
        echo -e "${GREEN}✅ Flask已安装${NC}"
    fi
}

# 检查端口占用
check_port() {
    local port=${1:-5000}
    if netstat -tulpn 2>/dev/null | grep -q ":$port "; then
        echo -e "${YELLOW}⚠️  端口 $port 已被占用${NC}"
        echo -e "${CYAN}尝试使用其他端口启动...${NC}"
        
        # 查找可用端口
        for p in {5001..5010}; do
            if ! netstat -tulpn 2>/dev/null | grep -q ":$p "; then
                echo -e "${GREEN}✅ 使用端口 $p${NC}"
                return $p
            fi
        done
        
        echo -e "${RED}❌ 无法找到可用端口${NC}"
        return 1
    else
        echo -e "${GREEN}✅ 端口 $port 可用${NC}"
        return $port
    fi
}

# 显示网络信息
show_network_info() {
    local port=$1
    local_ip=$(hostname -I | awk '{print $1}')
    
    echo -e "${CYAN}🌐 Web界面访问信息:${NC}"
    echo -e "${GREEN}  本地访问: http://localhost:$port${NC}"
    echo -e "${GREEN}  局域网访问: http://$local_ip:$port${NC}"
    echo -e "${BLUE}  移动设备: 扫描二维码或输入上述地址${NC}"
    echo -e "${YELLOW}  按 Ctrl+C 停止服务${NC}"
}

# 启动Web服务
start_web_service() {
    cd "$PROJECT_ROOT"
    
    # 检查环境
    check_python_env
    
    # 检查端口
    check_port 5000
    port=$?
    
    if [ $port -eq 1 ]; then
        echo -e "${RED}❌ 端口检查失败${NC}"
        exit 1
    fi
    
    # 显示访问信息
    show_network_info $port
    
    echo -e "${CYAN}启动中...${NC}"
    
    # 设置环境变量
    export PYTHONPATH="$PROJECT_ROOT:$PYTHONPATH"
    
    # 启动Web服务
    if [ $port -eq 5000 ]; then
        python web/web_simple.py
    else
        # 使用自定义端口启动
        python -c "
import sys
import os
sys.path.insert(0, '$PROJECT_ROOT')
os.chdir('$PROJECT_ROOT')

from web.web_simple import app
app.run(host='0.0.0.0', port=$port, debug=False, threaded=True)
"
    fi
}

# 处理中断信号
cleanup() {
    echo -e "\n${YELLOW}🛑 正在停止Web服务...${NC}"
    exit 0
}

trap cleanup SIGINT SIGTERM

# 主程序
main() {
    echo -e "${BLUE}===========================================${NC}"
    echo -e "${CYAN} Tiaozhanbei2.0 Web控制界面启动器${NC}"
    echo -e "${BLUE}===========================================${NC}"
    
    start_web_service
}

# 脚本参数处理
case "${1:-}" in
    --help|-h)
        echo "用法: $0 [选项]"
        echo ""
        echo "选项:"
        echo "  --help, -h     显示此帮助信息"
        echo "  --check, -c    仅检查环境，不启动服务"
        echo ""
        echo "示例:"
        echo "  $0              # 启动Web服务"
        echo "  $0 --check      # 检查环境"
        exit 0
        ;;
    --check|-c)
        check_python_env
        exit 0
        ;;
    *)
        main
        ;;
esac
