#!/bin/bash
# ==================================================================
# Tiaozhanbei2.0 项目演示脚本
# 管道追踪与法兰识别系统 - 完整测试与使用流程
# 
# 功能:
# 1. 系统环境检查
# 2. 各模块单元测试
# 3. 系统集成测试
# 4. 实际使用演示
#
# 作者: cxzandy
# 版本: 2.0.0
# ==================================================================

# 设置颜色输出
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
    echo -e "\n${PURPLE}===================================================${NC}"
    echo -e "${PURPLE}$1${NC}"
    echo -e "${PURPLE}===================================================${NC}\n"
}

# 检查命令是否存在
check_command() {
    if command -v $1 &> /dev/null; then
        log_success "$1 已安装"
        return 0
    else
        log_error "$1 未找到"
        return 1
    fi
}

# 检查Python模块
check_python_module() {
    if python -c "import $1" &> /dev/null; then
        log_success "Python模块 $1 已安装"
        return 0
    else
        log_error "Python模块 $1 未找到"
        return 1
    fi
}

# 执行命令并检查结果
run_command() {
    local cmd="$1"
    local description="$2"
    
    log_info "执行: $description"
    echo "命令: $cmd"
    
    if eval "$cmd"; then
        log_success "$description - 成功"
        return 0
    else
        log_error "$description - 失败"
        return 1
    fi
}

# 暂停等待用户输入
pause_for_user() {
    echo -e "\n${CYAN}按任意键继续，或Ctrl+C退出...${NC}"
    read -n 1 -s
}

# ==================================================================
# 第一阶段：系统环境检查
# ==================================================================
phase1_environment_check() {
    log_section "第一阶段：系统环境检查"
    
    local all_good=true
    
    # 检查基础命令
    log_info "检查基础环境..."
    check_command "python" || all_good=false
    check_command "pip" || all_good=false
    
    # 检查Python版本
    python_version=$(python --version 2>&1)
    log_info "Python版本: $python_version"
    
    # 检查关键Python模块
    log_info "检查Python依赖模块..."
    check_python_module "numpy" || all_good=false
    check_python_module "cv2" || all_good=false
    check_python_module "pyrealsense2" || all_good=false
    check_python_module "serial" || all_good=false
    
    # 检查项目文件结构
    log_info "检查项目文件结构..."
    local required_files=(
        "src/main.py"
        "src/config.py" 
        "src/camera/calibration.py"
        "src/robot/communication.py"
        "src/perception/obstacle_detection.py"
        "src/perception/pipe_tracking.py"
        "src/utils/logger.py"
    )
    
    for file in "${required_files[@]}"; do
        if [[ -f "$file" ]]; then
            log_success "文件存在: $file"
        else
            log_error "文件缺失: $file"
            all_good=false
        fi
    done
    
    # 检查数据目录
    local required_dirs=(
        "data/calib"
        "output"
        "tests"
    )
    
    for dir in "${required_dirs[@]}"; do
        if [[ -d "$dir" ]]; then
            log_success "目录存在: $dir"
        else
            log_warning "目录不存在: $dir (将自动创建)"
            mkdir -p "$dir"
        fi
    done
    
    if $all_good; then
        log_success "环境检查完成 - 所有检查通过！"
        return 0
    else
        log_error "环境检查失败 - 请安装缺失的依赖"
        echo -e "\n${YELLOW}安装命令建议:${NC}"
        echo "pip install pyrealsense2 opencv-python numpy pyserial"
        return 1
    fi
}

# ==================================================================
# 第二阶段：配置验证测试
# ==================================================================
phase2_config_test() {
    log_section "第二阶段：系统配置验证"
    
    run_command "python src/main.py --config-check" "配置文件验证"
    local config_result=$?
    
    if [[ $config_result -eq 0 ]]; then
        log_success "配置验证通过"
    else
        log_error "配置验证失败"
        return 1
    fi
    
    pause_for_user
    return 0
}

# ==================================================================
# 第三阶段：单元测试
# ==================================================================
phase3_unit_tests() {
    log_section "第三阶段：各模块单元测试"
    
    local test_files=(
        "tests/test_camera.py"
        "tests/test_robot.py" 
        "tests/test_perception.py"
    )
    
    local all_tests_passed=true
    
    for test_file in "${test_files[@]}"; do
        if [[ -f "$test_file" ]]; then
            log_info "运行测试: $test_file"
            if python "$test_file"; then
                log_success "测试通过: $test_file"
            else
                log_error "测试失败: $test_file"
                all_tests_passed=false
            fi
            echo "----------------------------------------"
        else
            log_warning "测试文件不存在: $test_file"
        fi
    done
    
    if $all_tests_passed; then
        log_success "所有单元测试通过！"
    else
        log_error "部分单元测试失败"
        log_warning "这可能是由于硬件未连接导致的，可以继续进行系统测试"
    fi
    
    pause_for_user
    return 0
}

# ==================================================================
# 第四阶段：系统集成测试
# ==================================================================
phase4_integration_test() {
    log_section "第四阶段：系统集成测试"
    
    # 演示模式测试
    log_info "测试1: 演示模式（不显示图像）"
    run_command "timeout 30s python src/main.py --mode demo --verbose" "演示模式测试"
    
    echo ""
    
    # 演示模式 + 图像显示
    log_info "测试2: 演示模式（显示图像）"
    log_warning "即将显示图像窗口，请按'q'键或等待自动结束"
    run_command "timeout 15s python src/main.py --mode demo --display --verbose" "演示模式图像显示测试"
    
    echo ""
    
    # 相机标定测试（如果有标定图片）
    if ls data/calib/*.jpg &> /dev/null; then
        log_info "测试3: 相机标定测试"
        log_info "发现标定图片，运行相机标定..."
        run_command "python src/main.py --mode calib --verbose" "相机标定测试"
    else
        log_warning "测试3: 跳过相机标定（未找到标定图片）"
        log_info "如需运行标定，请将棋盘格图片放置在 data/calib/ 目录下"
    fi
    
    pause_for_user
    return 0
}

# ==================================================================
# 第五阶段：实际使用演示
# ==================================================================
phase5_practical_demo() {
    log_section "第五阶段：实际使用演示"
    
    echo -e "${CYAN}选择演示模式:${NC}"
    echo "1) 短时间追踪演示 (30秒)"
    echo "2) 交互式追踪演示 (手动停止)"
    echo "3) 仅显示状态，不运行追踪"
    echo "4) 跳过此阶段"
    echo ""
    read -p "请选择 (1-4): " choice
    
    case $choice in
        1)
            log_info "运行短时间追踪演示..."
            log_warning "即将开始30秒的实时追踪，请确保相机已连接"
            log_warning "按'q'键可提前退出，或等待自动结束"
            run_command "timeout 30s python src/main.py --mode track --display --save --verbose" "短时间追踪演示"
            ;;
        2)
            log_info "运行交互式追踪演示..."
            log_warning "即将开始实时追踪，按Ctrl+C或'q'键退出"
            run_command "python src/main.py --mode track --display --save --verbose" "交互式追踪演示"
            ;;
        3)
            log_info "显示系统状态..."
            run_command "python src/main.py --mode demo --verbose" "系统状态显示"
            ;;
        4)
            log_info "跳过实际使用演示"
            ;;
        *)
            log_warning "无效选择，跳过此阶段"
            ;;
    esac
    
    return 0
}

# ==================================================================
# 第六阶段：结果总结
# ==================================================================
phase6_summary() {
    log_section "第六阶段：演示总结与使用说明"
    
    log_info "演示脚本执行完成！"
    echo ""
    
    echo -e "${CYAN}系统使用方法总结:${NC}"
    echo "1. 配置检查:    python src/main.py --config-check"
    echo "2. 快速演示:    python src/main.py --mode demo --display"
    echo "3. 相机标定:    python src/main.py --mode calib"
    echo "4. 实时追踪:    python src/main.py --mode track --display --save"
    echo "5. 系统测试:    python src/main.py --mode test --verbose"
    echo ""
    
    echo -e "${CYAN}生成的文件位置:${NC}"
    echo "- 日志文件:    output/logs/"
    echo "- 追踪结果:    output/images/"
    echo "- 标定数据:    data/calib/config/"
    echo ""
    
    echo -e "${CYAN}故障排除:${NC}"
    echo "- 相机问题:    检查RealSense驱动和pyrealsense2安装"
    echo "- 机器人问题:  检查串口连接和权限（可忽略继续使用）"
    echo "- 图像问题:    确保显示器支持OpenCV窗口显示"
    echo ""
    
    log_success "感谢使用 Tiaozhanbei2.0 系统！"
}

# ==================================================================
# 主函数
# ==================================================================
main() {
    log_section "Tiaozhanbei2.0 系统演示脚本启动"
    
    echo -e "${CYAN}本脚本将依次执行以下阶段:${NC}"
    echo "1. 系统环境检查"
    echo "2. 配置验证测试"  
    echo "3. 各模块单元测试"
    echo "4. 系统集成测试"
    echo "5. 实际使用演示"
    echo "6. 结果总结"
    echo ""
    
    read -p "是否继续？(y/N): " confirm
    if [[ ! $confirm =~ ^[Yy]$ ]]; then
        log_info "用户取消执行"
        exit 0
    fi
    
    # 执行各个阶段
    phase1_environment_check || {
        log_error "环境检查失败，演示终止"
        exit 1
    }
    
    phase2_config_test || {
        log_error "配置测试失败，演示终止"
        exit 1
    }
    
    phase3_unit_tests
    
    phase4_integration_test
    
    phase5_practical_demo
    
    phase6_summary
    
    log_success "演示脚本执行完成！"
}

# 脚本入口点
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main "$@"
fi