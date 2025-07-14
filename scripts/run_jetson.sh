#!/bin/bash
# ==================================================================
# Jetson AGX Xavier 专用启动脚本
# Tiaozhanbei2.0 - 管道追踪与法兰识别系统
# 
# 功能:
# 1. 自动检测和配置Jetson环境
# 2. 设置最佳性能模式
# 3. 启动视觉系统
# 4. 提供实时监控
#
# 作者: cxzandy
# 版本: 2.0.0 Jetson Edition
# ==================================================================

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# 项目根目录
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$PROJECT_ROOT"

# 日志函数
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

log_section() {
    echo ""
    echo -e "${PURPLE}===================================================${NC}"
    echo -e "${PURPLE}$1${NC}"
    echo -e "${PURPLE}===================================================${NC}"
    echo ""
}

# 检查是否在Jetson平台上运行
check_jetson_platform() {
    log_section "检查Jetson平台"
    
    if [[ ! -f /proc/device-tree/model ]]; then
        log_error "未检测到Jetson平台，请在Jetson设备上运行此脚本"
        exit 1
    fi
    
    MODEL=$(cat /proc/device-tree/model 2>/dev/null)
    if [[ "$MODEL" == *"jetson"* ]]; then
        log_success "检测到Jetson平台: $MODEL"
        if [[ "$MODEL" == *"AGX Xavier"* ]]; then
            JETSON_MODEL="agx_xavier"
            log_success "确认为Jetson AGX Xavier平台"
        else
            JETSON_MODEL="other"
            log_warning "检测到其他Jetson平台，某些功能可能不可用"
        fi
    else
        log_error "无法确认Jetson平台型号"
        exit 1
    fi
}

# 检查系统工具
check_system_tools() {
    log_section "检查系统工具"
    
    # 检查nvpmodel
    if command -v nvpmodel &> /dev/null; then
        log_success "nvpmodel 工具可用"
        NVPMODEL_AVAILABLE=true
    else
        log_warning "nvpmodel 工具不可用"
        NVPMODEL_AVAILABLE=false
    fi
    
    # 检查jetson_clocks
    if command -v jetson_clocks &> /dev/null; then
        log_success "jetson_clocks 工具可用"
        JETSON_CLOCKS_AVAILABLE=true
    else
        log_warning "jetson_clocks 工具不可用"
        JETSON_CLOCKS_AVAILABLE=false
    fi
    
    # 检查tegrastats
    if command -v tegrastats &> /dev/null; then
        log_success "tegrastats 工具可用"
        TEGRASTATS_AVAILABLE=true
    else
        log_warning "tegrastats 工具不可用"
        TEGRASTATS_AVAILABLE=false
    fi
}

# 设置性能模式
set_performance_mode() {
    log_section "设置性能模式"
    
    if [[ "$NVPMODEL_AVAILABLE" == true ]]; then
        # 显示当前模式
        CURRENT_MODE=$(sudo nvpmodel -q --verbose 2>/dev/null | grep "NV Power Mode" | awk '{print $NF}')
        log_info "当前性能模式: $CURRENT_MODE"
        
        # 设置最大性能模式
        log_info "设置为最大性能模式 (MAXN)..."
        if sudo nvpmodel -m 0; then
            log_success "性能模式设置成功"
        else
            log_error "性能模式设置失败"
        fi
    else
        log_warning "跳过性能模式设置 (nvpmodel不可用)"
    fi
    
    if [[ "$JETSON_CLOCKS_AVAILABLE" == true ]]; then
        log_info "锁定时钟频率以获得稳定性能..."
        if sudo jetson_clocks; then
            log_success "时钟频率锁定成功"
        else
            log_error "时钟频率锁定失败"
        fi
    else
        log_warning "跳过时钟频率锁定 (jetson_clocks不可用)"
    fi
}

# 检查硬件连接
check_hardware() {
    log_section "检查硬件连接"
    
    # 检查RealSense相机
    log_info "检查RealSense D455相机连接..."
    if lsusb | grep -q "Intel"; then
        log_success "检测到Intel RealSense设备"
        
        # 尝试启动realsense-viewer验证
        if command -v realsense-viewer &> /dev/null; then
            log_info "RealSense Viewer可用，可以手动验证相机功能"
        else
            log_warning "RealSense Viewer不可用"
        fi
    else
        log_warning "未检测到Intel RealSense设备"
        log_info "请确保:"
        log_info "1. RealSense D455已连接到USB 3.0端口"
        log_info "2. 设备驱动已正确安装"
    fi
    
    # 检查UART设备
    log_info "检查UART设备..."
    if [[ -e /dev/ttyTHS1 ]]; then
        log_success "检测到UART设备: /dev/ttyTHS1"
        
        # 检查权限
        if [[ -r /dev/ttyTHS1 && -w /dev/ttyTHS1 ]]; then
            log_success "UART设备权限正常"
        else
            log_warning "UART设备权限不足，尝试修复..."
            sudo chmod 666 /dev/ttyTHS1
            if [[ $? -eq 0 ]]; then
                log_success "UART设备权限修复成功"
            else
                log_error "UART设备权限修复失败"
            fi
        fi
    else
        log_warning "未检测到UART设备 /dev/ttyTHS1"
        log_info "请确保UART接口已启用"
    fi
}

# 检查Python环境
check_python_environment() {
    log_section "检查Python环境"
    
    # 检查Python版本
    PYTHON_VERSION=$(python3 --version 2>&1)
    log_info "Python版本: $PYTHON_VERSION"
    
    # 检查虚拟环境
    if [[ -d "tiaozhanbei_env" ]]; then
        log_success "检测到虚拟环境: tiaozhanbei_env"
    else
        log_warning "未找到虚拟环境，将创建新环境"
        python3 -m venv tiaozhanbei_env
        if [[ $? -eq 0 ]]; then
            log_success "虚拟环境创建成功"
        else
            log_error "虚拟环境创建失败"
            exit 1
        fi
    fi
    
    # 激活虚拟环境
    source tiaozhanbei_env/bin/activate
    
    # 检查关键依赖
    log_info "检查Python依赖包..."
    
    python3 -c "import numpy; print('NumPy版本:', numpy.__version__)" 2>/dev/null
    if [[ $? -eq 0 ]]; then
        log_success "NumPy 已安装"
    else
        log_warning "NumPy 未安装"
    fi
    
    python3 -c "import cv2; print('OpenCV版本:', cv2.__version__)" 2>/dev/null
    if [[ $? -eq 0 ]]; then
        log_success "OpenCV 已安装"
        
        # 检查CUDA支持
        CUDA_SUPPORT=$(python3 -c "import cv2; print(cv2.cuda.getCudaEnabledDeviceCount())" 2>/dev/null)
        if [[ "$CUDA_SUPPORT" == "0" ]]; then
            log_warning "OpenCV 未启用CUDA支持"
        else
            log_success "OpenCV 已启用CUDA支持 ($CUDA_SUPPORT 设备)"
        fi
    else
        log_warning "OpenCV 未安装"
    fi
    
    python3 -c "import pyrealsense2" 2>/dev/null
    if [[ $? -eq 0 ]]; then
        log_success "pyrealsense2 已安装"
    else
        log_warning "pyrealsense2 未安装"
    fi
    
    python3 -c "import serial" 2>/dev/null
    if [[ $? -eq 0 ]]; then
        log_success "pyserial 已安装"
    else
        log_warning "pyserial 未安装"
    fi
}

# 启动系统监控
start_monitoring() {
    log_section "启动系统监控"
    
    if [[ "$TEGRASTATS_AVAILABLE" == true ]]; then
        log_info "启动系统监控 (Ctrl+C停止)..."
        
        # 创建监控日志目录
        mkdir -p output/logs
        
        # 后台启动tegrastats
        nohup tegrastats --interval 1000 > output/logs/jetson_stats.log 2>&1 &
        TEGRASTATS_PID=$!
        log_success "系统监控已启动 (PID: $TEGRASTATS_PID)"
        
        # 保存PID用于后续清理
        echo $TEGRASTATS_PID > /tmp/tiaozhanbei_tegrastats.pid
    else
        log_warning "系统监控不可用 (tegrastats未安装)"
    fi
}

# 停止系统监控
stop_monitoring() {
    if [[ -f /tmp/tiaozhanbei_tegrastats.pid ]]; then
        TEGRASTATS_PID=$(cat /tmp/tiaozhanbei_tegrastats.pid)
        if ps -p $TEGRASTATS_PID > /dev/null; then
            log_info "停止系统监控..."
            kill $TEGRASTATS_PID
            rm -f /tmp/tiaozhanbei_tegrastats.pid
            log_success "系统监控已停止"
        fi
    fi
}

# 运行主程序
run_main_program() {
    log_section "启动Tiaozhanbei2.0系统"
    
    # 激活虚拟环境
    source tiaozhanbei_env/bin/activate
    
    # 设置环境变量
    export PYTHONPATH="$PROJECT_ROOT/src:$PYTHONPATH"
    
    # 根据参数选择运行模式
    case "${1:-track}" in
        "demo")
            log_info "启动演示模式..."
            python3 src/main.py --mode demo --display --verbose
            ;;
        "calib")
            log_info "启动相机标定模式..."
            python3 src/main.py --mode calib --verbose
            ;;
        "track")
            log_info "启动实时追踪模式..."
            python3 src/main.py --mode track --display --save --robot --port /dev/ttyTHS1 --verbose
            ;;
        "test")
            log_info "启动系统测试模式..."
            python3 src/main.py --mode test --verbose
            ;;
        "config-check")
            log_info "检查系统配置..."
            python3 src/main.py --config-check
            ;;
        *)
            log_error "未知运行模式: $1"
            log_info "可用模式: demo, calib, track, test, config-check"
            exit 1
            ;;
    esac
}

# 清理函数
cleanup() {
    log_info "正在清理..."
    stop_monitoring
    log_success "清理完成"
}

# 注册清理函数
trap cleanup EXIT

# 显示帮助信息
show_help() {
    echo "Jetson AGX Xavier 启动脚本 - Tiaozhanbei2.0"
    echo ""
    echo "用法: $0 [模式] [选项]"
    echo ""
    echo "模式:"
    echo "  demo        演示模式 (默认)"
    echo "  calib       相机标定模式"
    echo "  track       实时追踪模式"
    echo "  test        系统测试模式"
    echo "  config-check 配置检查模式"
    echo ""
    echo "选项:"
    echo "  -h, --help     显示此帮助信息"
    echo "  --no-perf      跳过性能优化设置"
    echo "  --no-monitor   跳过系统监控"
    echo ""
    echo "示例:"
    echo "  $0 track       # 启动实时追踪"
    echo "  $0 demo        # 启动演示模式"
    echo "  $0 --help      # 显示帮助"
    echo ""
}

# 主函数
main() {
    log_section "Jetson AGX Xavier 启动脚本"
    
    # 处理命令行参数
    MODE="track"
    SKIP_PERF=false
    SKIP_MONITOR=false
    
    while [[ $# -gt 0 ]]; do
        case $1 in
            -h|--help)
                show_help
                exit 0
                ;;
            --no-perf)
                SKIP_PERF=true
                shift
                ;;
            --no-monitor)
                SKIP_MONITOR=true
                shift
                ;;
            demo|calib|track|test|config-check)
                MODE=$1
                shift
                ;;
            *)
                log_error "未知参数: $1"
                show_help
                exit 1
                ;;
        esac
    done
    
    log_info "运行模式: $MODE"
    
    # 执行检查和设置
    check_jetson_platform
    check_system_tools
    
    if [[ "$SKIP_PERF" == false ]]; then
        set_performance_mode
    else
        log_info "跳过性能优化设置"
    fi
    
    check_hardware
    check_python_environment
    
    if [[ "$SKIP_MONITOR" == false ]]; then
        start_monitoring
    else
        log_info "跳过系统监控启动"
    fi
    
    # 启动主程序
    run_main_program $MODE
}

# 脚本入口
main "$@"
