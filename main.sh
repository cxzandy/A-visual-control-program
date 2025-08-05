#!/bin/bash
# =================================================================
# Tiaozhanbei2.0 系统总控制台
# Master Control Terminal for Tiaozhanbei2.0 System
# Updated with Environment Setup and Jetson Support
# =================================================================

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
WHITE='\033[1;37m'
NC='\033[0m' # No Color

# 项目根目录
PROJECT_ROOT="/home/aaa/A-visual-control-program"
CONDA_ENV="tiao"

# 检测平台
detect_platform() {
    if [ -f "/proc/device-tree/model" ]; then
        if grep -q "Xavier" /proc/device-tree/model; then
            PLATFORM="jetson"
            echo -e "${CYAN}🤖 检测到 Jetson AGX Xavier 平台${NC}"
        else
            PLATFORM="linux"
        fi
    else
        PLATFORM="linux"
    fi
}

# 显示Logo和欢迎信息
show_header() {
    clear
    echo -e "${BLUE}================================================================${NC}"
    echo -e "${WHITE}                 🚀 Tiaozhanbei2.0 总控制台${NC}"
    echo -e "${WHITE}                   Master Control Terminal${NC}"
    echo -e "${BLUE}================================================================${NC}"
    echo -e "${CYAN}项目路径: ${PROJECT_ROOT}${NC}"
    echo -e "${CYAN}Python环境: ${CONDA_ENV}${NC}"
    echo -e "${CYAN}运行平台: ${PLATFORM}${NC}"
    echo -e "${CYAN}日期时间: $(date '+%Y-%m-%d %H:%M:%S')${NC}"
    echo -e "${BLUE}================================================================${NC}"
    echo ""
}

# 检查环境
check_environment() {
    echo -e "${YELLOW}🔍 检查运行环境...${NC}"
    
    # 检查conda/miniforge
    if command -v conda >/dev/null 2>&1; then
        CONDA_PATH=$(which conda)
        echo -e "${GREEN}✓ 找到 conda: $CONDA_PATH${NC}"
    elif command -v mamba >/dev/null 2>&1; then
        CONDA_PATH=$(which mamba)
        echo -e "${GREEN}✓ 找到 mamba (miniforge): $CONDA_PATH${NC}"
    else
        echo -e "${RED}❌ 未找到 conda 或 miniforge${NC}"
        echo -e "${YELLOW}请选择安装选项或手动安装 conda/miniforge${NC}"
        return 1
    fi
    
    # 检查conda环境
    if ! conda info --envs | grep -q "$CONDA_ENV"; then
        echo -e "${YELLOW}⚠️ conda环境 '$CONDA_ENV' 不存在${NC}"
        echo -e "${CYAN}可以使用安装选项创建环境${NC}"
        return 1
    fi
    
    # 检查项目目录
    if [ ! -d "$PROJECT_ROOT" ]; then
        echo -e "${RED}❌ 项目目录不存在: $PROJECT_ROOT${NC}"
        exit 1
    fi
    
    echo -e "${GREEN}✓ 环境检查通过${NC}"
    echo ""
    return 0
}

# 激活conda环境
activate_environment() {
    echo -e "${YELLOW}🔧 激活conda环境...${NC}"
    
    # 寻找conda初始化脚本
    if [ -f "/home/aaa/anaconda3/bin/activate" ]; then
        source /home/aaa/anaconda3/bin/activate
    elif [ -f "/home/aaa/miniforge3/bin/activate" ]; then
        source /home/aaa/miniforge3/bin/activate
    elif [ -f "$HOME/anaconda3/bin/activate" ]; then
        source $HOME/anaconda3/bin/activate
    elif [ -f "$HOME/miniforge3/bin/activate" ]; then
        source $HOME/miniforge3/bin/activate
    else
        echo -e "${YELLOW}⚠️ 未找到conda激活脚本，尝试直接激活...${NC}"
    fi
    
    conda activate $CONDA_ENV
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✓ 已激活 $CONDA_ENV 环境${NC}"
    else
        echo -e "${RED}❌ 环境激活失败${NC}"
        return 1
    fi
    echo ""
}

# 安装miniforge (适用于Jetson)
install_miniforge() {
    echo -e "${YELLOW}🔧 安装 Miniforge...${NC}"
    echo -e "${CYAN}适用于 ARM64/aarch64 架构 (Jetson)${NC}"
    echo ""
    
    cd /tmp
    
    # 下载 miniforge
    echo -e "${YELLOW}下载 Miniforge 安装包...${NC}"
    if [ "$PLATFORM" = "jetson" ]; then
        wget https://github.com/conda-forge/miniforge/releases/latest/download/Miniforge3-Linux-aarch64.sh
        INSTALLER="Miniforge3-Linux-aarch64.sh"
    else
        wget https://github.com/conda-forge/miniforge/releases/latest/download/Miniforge3-Linux-x86_64.sh
        INSTALLER="Miniforge3-Linux-x86_64.sh"
    fi
    
    if [ $? -ne 0 ]; then
        echo -e "${RED}❌ 下载失败${NC}"
        return 1
    fi
    
    # 安装 miniforge
    echo -e "${YELLOW}安装 Miniforge...${NC}"
    chmod +x $INSTALLER
    bash $INSTALLER -b -p $HOME/miniforge3
    
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✓ Miniforge 安装成功${NC}"
        
        # 初始化
        echo -e "${YELLOW}初始化 conda...${NC}"
        $HOME/miniforge3/bin/conda init bash
        source ~/.bashrc
        
        echo -e "${GREEN}✓ 请重新启动脚本以使用新安装的 miniforge${NC}"
    else
        echo -e "${RED}❌ Miniforge 安装失败${NC}"
        return 1
    fi
    
    # 清理
    rm -f $INSTALLER
}

# 安装RealSense SDK (适用于Jetson)
install_realsense_jetson() {
    echo -e "${YELLOW}🔧 安装 RealSense SDK for Jetson...${NC}"
    echo ""
    
    # 检查是否为Jetson平台
    if [ "$PLATFORM" != "jetson" ]; then
        echo -e "${YELLOW}⚠️ 非Jetson平台，使用标准安装方式${NC}"
        return 0
    fi
    
    echo -e "${CYAN}开始为 Jetson AGX Xavier 安装 RealSense SDK...${NC}"
    
    # 更新系统
    echo -e "${YELLOW}更新系统包...${NC}"
    sudo apt update
    
    # 安装依赖
    echo -e "${YELLOW}安装编译依赖...${NC}"
    sudo apt install -y \
        git libssl-dev libusb-1.0-0-dev pkg-config \
        libgtk-3-dev libglfw3-dev libgl1-mesa-dev \
        libglu1-mesa-dev cmake build-essential
    
    # 克隆并编译 librealsense
    echo -e "${YELLOW}下载并编译 librealsense...${NC}"
    cd /tmp
    git clone https://github.com/IntelRealSense/librealsense.git
    cd librealsense
    
    # 应用Jetson补丁
    echo -e "${YELLOW}应用 Jetson 补丁...${NC}"
    ./scripts/setup_udev_rules.sh
    ./scripts/patch-realsense-ubuntu-lts-hwe.sh
    
    # 编译
    echo -e "${YELLOW}编译 RealSense SDK...${NC}"
    mkdir build && cd build
    cmake .. -DBUILD_EXAMPLES=true -DCMAKE_BUILD_TYPE=Release -DFORCE_RSUSB_BACKEND=false
    make -j4
    sudo make install
    
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✓ RealSense SDK 安装成功${NC}"
        
        # 更新动态链接库
        sudo ldconfig
        
        # 设置udev规则
        sudo cp config/99-realsense-libusb.rules /etc/udev/rules.d/
        sudo udevadm control --reload-rules && sudo udevadm trigger
        
        echo -e "${GREEN}✓ RealSense 驱动配置完成${NC}"
    else
        echo -e "${RED}❌ RealSense SDK 编译失败${NC}"
        return 1
    fi
    
    # 清理
    cd /
    rm -rf /tmp/librealsense
}

# 创建虚拟环境
create_environment() {
    echo -e "${YELLOW}🔧 创建 Python 虚拟环境...${NC}"
    echo ""
    
    # 选择环境配置文件
    if [ "$PLATFORM" = "jetson" ]; then
        ENV_FILE="environment_jetson.yml"
        echo -e "${CYAN}使用 Jetson 专用环境配置${NC}"
    else
        ENV_FILE="environment.yml"
        echo -e "${CYAN}使用标准环境配置${NC}"
    fi
    
    cd $PROJECT_ROOT
    
    if [ ! -f "$ENV_FILE" ]; then
        echo -e "${RED}❌ 环境配置文件不存在: $ENV_FILE${NC}"
        return 1
    fi
    
    echo -e "${YELLOW}创建环境: $CONDA_ENV${NC}"
    conda env create -f $ENV_FILE
    
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✓ 环境创建成功${NC}"
        
        # 激活环境并安装额外依赖
        conda activate $CONDA_ENV
        
        # 对于Jetson，需要特殊处理一些包
        if [ "$PLATFORM" = "jetson" ]; then
            echo -e "${YELLOW}安装 Jetson 专用包...${NC}"
            
            # 安装PyTorch for Jetson
            pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cpu
            
            # 从源码安装OpenCV (如果需要GPU加速)
            if [ ! -f "/usr/local/lib/python3.8/site-packages/cv2.so" ]; then
                echo -e "${YELLOW}OpenCV 将使用conda版本，如需GPU加速请手动编译${NC}"
            fi
        fi
        
        echo -e "${GREEN}✓ 虚拟环境配置完成${NC}"
    else
        echo -e "${RED}❌ 环境创建失败${NC}"
        return 1
    fi
}

# 完整的环境安装
full_environment_setup() {
    echo -e "${BLUE}================================================================${NC}"
    echo -e "${WHITE}             🚀 完整环境安装向导${NC}"
    echo -e "${BLUE}================================================================${NC}"
    echo ""
    
    detect_platform
    
    echo -e "${CYAN}将执行以下安装步骤:${NC}"
    echo -e "1. 安装/检查 conda/miniforge"
    echo -e "2. 创建Python虚拟环境"
    if [ "$PLATFORM" = "jetson" ]; then
        echo -e "3. 安装 RealSense SDK for Jetson"
    fi
    echo -e "4. 验证安装"
    echo ""
    
    read -p "是否继续安装? (y/N): " confirm
    if [[ ! $confirm =~ ^[Yy]$ ]]; then
        echo -e "${YELLOW}安装已取消${NC}"
        return
    fi
    
    # 步骤1：安装miniforge
    if ! command -v conda >/dev/null 2>&1 && ! command -v mamba >/dev/null 2>&1; then
        echo -e "${YELLOW}步骤1: 安装 Miniforge${NC}"
        install_miniforge
        if [ $? -ne 0 ]; then
            echo -e "${RED}❌ 安装失败，请检查网络连接${NC}"
            return 1
        fi
        
        echo -e "${YELLOW}请重新运行此脚本以继续安装${NC}"
        return 0
    else
        echo -e "${GREEN}✓ 步骤1: conda/miniforge 已存在${NC}"
    fi
    
    # 步骤2：创建环境
    echo -e "${YELLOW}步骤2: 创建虚拟环境${NC}"
    create_environment
    if [ $? -ne 0 ]; then
        echo -e "${RED}❌ 环境创建失败${NC}"
        return 1
    fi
    
    # 步骤3：安装RealSense SDK (仅Jetson)
    if [ "$PLATFORM" = "jetson" ]; then
        echo -e "${YELLOW}步骤3: 安装 RealSense SDK${NC}"
        install_realsense_jetson
        if [ $? -ne 0 ]; then
            echo -e "${YELLOW}⚠️ RealSense SDK 安装失败，但不影响基本功能${NC}"
        fi
    fi
    
    # 步骤4：验证安装
    echo -e "${YELLOW}步骤4: 验证安装${NC}"
    conda activate $CONDA_ENV
    python -c "import cv2, numpy, flask; print('✓ 基础模块导入成功')"
    
    if [ "$PLATFORM" = "jetson" ]; then
        python -c "import pyrealsense2; print('✓ RealSense SDK 导入成功')" 2>/dev/null || echo "⚠️ RealSense SDK 不可用"
    fi
    
    echo ""
    echo -e "${GREEN}🎉 环境安装完成！${NC}"
    echo -e "${CYAN}现在可以使用项目的所有功能了${NC}"
    echo ""
    read -p "按Enter键继续..."
}

# 显示系统状态
show_system_status() {
    echo -e "${CYAN}📊 系统状态检查${NC}"
    echo -e "${BLUE}----------------------------------------------------------------${NC}"
    
    # 检查平台
    detect_platform
    echo -e "${CYAN}🖥️ 运行平台: ${PLATFORM}${NC}"
    
    # 检查conda环境
    if conda info --envs | grep -q "$CONDA_ENV"; then
        echo -e "${GREEN}🐍 Python环境: $CONDA_ENV (已创建)${NC}"
        
        # 检查关键包
        conda activate $CONDA_ENV 2>/dev/null
        python -c "import cv2; print('✓ OpenCV:', cv2.__version__)" 2>/dev/null || echo -e "${YELLOW}⚠️ OpenCV: 未安装${NC}"
        python -c "import numpy; print('✓ NumPy:', numpy.__version__)" 2>/dev/null || echo -e "${YELLOW}⚠️ NumPy: 未安装${NC}"
        python -c "import flask; print('✓ Flask: 已安装')" 2>/dev/null || echo -e "${YELLOW}⚠️ Flask: 未安装${NC}"
        
        if [ "$PLATFORM" = "jetson" ]; then
            python -c "import pyrealsense2; print('✓ RealSense SDK: 已安装')" 2>/dev/null || echo -e "${YELLOW}⚠️ RealSense SDK: 未安装${NC}"
        fi
    else
        echo -e "${YELLOW}🐍 Python环境: $CONDA_ENV (未创建)${NC}"
    fi
    
    # 检查Web服务
    if pgrep -f "web_simple.py" > /dev/null; then
        echo -e "${GREEN}🌐 Web服务: 运行中${NC}"
    else
        echo -e "${YELLOW}🌐 Web服务: 未运行${NC}"
    fi
    
    # 检查主程序
    if pgrep -f "main.py" > /dev/null; then
        echo -e "${GREEN}🎯 主程序: 运行中${NC}"
    else
        echo -e "${YELLOW}🎯 主程序: 未运行${NC}"
    fi
    
    echo -e "${BLUE}----------------------------------------------------------------${NC}"
    echo ""
}

# 主菜单
show_main_menu() {
    echo -e "${WHITE}请选择要执行的操作:${NC}"
    echo ""
    echo -e "${GREEN}🔧 环境管理:${NC}"
    echo -e "  ${CYAN}1)${NC} 🚀 完整环境安装 (推荐新用户)"
    echo -e "  ${CYAN}2)${NC} 🐍 创建虚拟环境"
    echo -e "  ${CYAN}3)${NC} 📦 安装 Miniforge"
    if [ "$PLATFORM" = "jetson" ]; then
        echo -e "  ${CYAN}4)${NC} 📷 安装 RealSense SDK (Jetson)"
    fi
    echo ""
    echo -e "${GREEN}📱 Web界面相关:${NC}"
    if [ "$PLATFORM" = "jetson" ]; then
        echo -e "  ${CYAN}5)${NC} 🌐 启动Web控制界面"
        echo -e "  ${CYAN}6)${NC} 🛑 停止Web服务"
    else
        echo -e "  ${CYAN}4)${NC} 🌐 启动Web控制界面"
        echo -e "  ${CYAN}5)${NC} 🛑 停止Web服务"
    fi
    echo ""
    echo -e "${GREEN}🎯 系统功能:${NC}"
    if [ "$PLATFORM" = "jetson" ]; then
        echo -e "  ${CYAN}7)${NC} 🧪 运行测试模式"
        echo -e "  ${CYAN}8)${NC} 📷 相机标定模式"
        echo -e "  ${CYAN}9)${NC} 🎯 实时追踪模式"
    else
        echo -e "  ${CYAN}6)${NC} 🧪 运行测试模式"
        echo -e "  ${CYAN}7)${NC} 📷 相机标定模式"
        echo -e "  ${CYAN}8)${NC} 🎯 实时追踪模式"
    fi
    echo ""
    echo -e "${GREEN}🔧 系统管理:${NC}"
    if [ "$PLATFORM" = "jetson" ]; then
        echo -e "  ${CYAN}10)${NC} ⚙️ 配置检查"
        echo -e "  ${CYAN}11)${NC} 📊 查看系统状态"
        echo -e "  ${CYAN}12)${NC} 🔄 重启所有服务"
        echo -e "  ${CYAN}13)${NC} 🧹 清理进程"
    else
        echo -e "  ${CYAN}9)${NC} ⚙️ 配置检查"
        echo -e "  ${CYAN}10)${NC} 📊 查看系统状态"
        echo -e "  ${CYAN}11)${NC} 🔄 重启所有服务"
        echo -e "  ${CYAN}12)${NC} 🧹 清理进程"
    fi
    echo ""
    echo -e "${GREEN}💻 开发工具:${NC}"
    if [ "$PLATFORM" = "jetson" ]; then
        echo -e "  ${CYAN}14)${NC} 🐍 Python交互环境"
        echo -e "  ${CYAN}15)${NC} 📂 项目目录浏览"
    else
        echo -e "  ${CYAN}13)${NC} 🐍 Python交互环境"
        echo -e "  ${CYAN}14)${NC} 📂 项目目录浏览"
    fi
    echo ""
    echo -e "${RED}0)${NC} 🚪 退出控制台"
    echo ""
    echo -e "${BLUE}================================================================${NC}"
}

# 启动Web界面
start_web_interface() {
    echo -e "${YELLOW}🌐 启动Web控制界面...${NC}"
    
    # 检查环境
    if ! conda info --envs | grep -q "$CONDA_ENV"; then
        echo -e "${RED}❌ 环境 '$CONDA_ENV' 不存在，请先创建环境${NC}"
        read -p "按Enter键继续..."
        return
    fi
    
    # 检查是否已运行
    if pgrep -f "web_simple.py" > /dev/null; then
        echo -e "${YELLOW}⚠️ Web服务已在运行${NC}"
        echo -e "${CYAN}访问地址: http://localhost:5000${NC}"
        read -p "按Enter键继续..."
        return
    fi
    
    cd $PROJECT_ROOT
    conda activate $CONDA_ENV
    
    echo -e "${CYAN}📱 访问地址: http://localhost:5000${NC}"
    echo -e "${CYAN}🌐 局域网访问: http://$(hostname -I | awk '{print $1}'):5000${NC}"
    echo -e "${YELLOW}⏹️ 按Ctrl+C停止服务${NC}"
    echo ""
    
    python web/web_simple.py
}

# 停止Web服务
stop_web_service() {
    echo -e "${YELLOW}🛑 停止Web服务...${NC}"
    
    if pgrep -f "web_simple.py" > /dev/null; then
        pkill -f "web_simple.py"
        echo -e "${GREEN}✓ Web服务已停止${NC}"
    else
        echo -e "${YELLOW}⚠️ Web服务未运行${NC}"
    fi
    
    read -p "按Enter键继续..."
}

# 运行测试模式
run_test_mode() {
    echo -e "${YELLOW}🧪 启动测试模式...${NC}"
    
    if ! conda info --envs | grep -q "$CONDA_ENV"; then
        echo -e "${RED}❌ 环境 '$CONDA_ENV' 不存在，请先创建环境${NC}"
        read -p "按Enter键继续..."
        return
    fi
    
    cd $PROJECT_ROOT
    conda activate $CONDA_ENV
    
    echo -e "${CYAN}运行系统测试...${NC}"
    python tests/test_system.py
    
    read -p "按Enter键继续..."
}

# 相机标定模式
run_calibration_mode() {
    echo -e "${YELLOW}📷 启动相机标定模式...${NC}"
    
    if ! conda info --envs | grep -q "$CONDA_ENV"; then
        echo -e "${RED}❌ 环境 '$CONDA_ENV' 不存在，请先创建环境${NC}"
        read -p "按Enter键继续..."
        return
    fi
    
    cd $PROJECT_ROOT
    conda activate $CONDA_ENV
    
    echo -e "${CYAN}启动相机标定程序...${NC}"
    python -c "from src.camera.calibration import CameraCalibration; cal = CameraCalibration(); cal.run_calibration()"
    
    read -p "按Enter键继续..."
}

# 实时追踪模式
run_tracking_mode() {
    echo -e "${YELLOW}🎯 启动实时追踪模式...${NC}"
    
    if ! conda info --envs | grep -q "$CONDA_ENV"; then
        echo -e "${RED}❌ 环境 '$CONDA_ENV' 不存在，请先创建环境${NC}"
        read -p "按Enter键继续..."
        return
    fi
    
    cd $PROJECT_ROOT
    conda activate $CONDA_ENV
    
    echo -e "${CYAN}启动管道追踪系统...${NC}"
    python src/main.py --mode tracking
    
    read -p "按Enter键继续..."
}

# 配置检查
check_configuration() {
    echo -e "${YELLOW}⚙️ 检查系统配置...${NC}"
    echo ""
    
    cd $PROJECT_ROOT
    
    # 检查配置文件
    echo -e "${CYAN}📄 配置文件检查:${NC}"
    
    if [ -f "src/config.py" ]; then
        echo -e "${GREEN}✓ src/config.py${NC}"
    else
        echo -e "${RED}❌ src/config.py 缺失${NC}"
    fi
    
    if [ -f "environment.yml" ]; then
        echo -e "${GREEN}✓ environment.yml${NC}"
    else
        echo -e "${RED}❌ environment.yml 缺失${NC}"
    fi
    
    if [ -f "environment_jetson.yml" ]; then
        echo -e "${GREEN}✓ environment_jetson.yml${NC}"
    else
        echo -e "${YELLOW}⚠️ environment_jetson.yml 缺失 (仅Jetson需要)${NC}"
    fi
    
    # 检查数据目录
    echo -e "${CYAN}📁 数据目录检查:${NC}"
    
    for dir in "data/calib" "output/images" "output/logs" "output/models"; do
        if [ -d "$dir" ]; then
            echo -e "${GREEN}✓ $dir${NC}"
        else
            echo -e "${YELLOW}⚠️ $dir 不存在，将自动创建${NC}"
            mkdir -p "$dir"
        fi
    done
    
    echo ""
    read -p "按Enter键继续..."
}

# 重启所有服务
restart_all_services() {
    echo -e "${YELLOW}🔄 重启所有服务...${NC}"
    
    # 停止所有相关进程
    echo -e "${YELLOW}停止现有进程...${NC}"
    pkill -f "web_simple.py" 2>/dev/null
    pkill -f "main.py" 2>/dev/null
    sleep 2
    
    echo -e "${GREEN}✓ 服务已重启准备就绪${NC}"
    echo -e "${CYAN}请手动启动需要的服务${NC}"
    
    read -p "按Enter键继续..."
}

# 清理进程
cleanup_processes() {
    echo -e "${YELLOW}🧹 清理相关进程...${NC}"
    
    echo -e "${YELLOW}停止Web服务...${NC}"
    pkill -f "web_simple.py" 2>/dev/null
    
    echo -e "${YELLOW}停止主程序...${NC}"
    pkill -f "main.py" 2>/dev/null
    
    echo -e "${YELLOW}停止测试程序...${NC}"
    pkill -f "test_system.py" 2>/dev/null
    
    echo -e "${GREEN}✓ 进程清理完成${NC}"
    
    read -p "按Enter键继续..."
}

# Python交互环境
enter_python_env() {
    echo -e "${YELLOW}🐍 进入Python交互环境...${NC}"
    
    if ! conda info --envs | grep -q "$CONDA_ENV"; then
        echo -e "${RED}❌ 环境 '$CONDA_ENV' 不存在，请先创建环境${NC}"
        read -p "按Enter键继续..."
        return
    fi
    
    cd $PROJECT_ROOT
    conda activate $CONDA_ENV
    
    echo -e "${CYAN}提示: 输入 'exit()' 返回控制台${NC}"
    echo -e "${CYAN}项目路径已添加到 sys.path${NC}"
    echo ""
    
    python -c "
import sys
sys.path.insert(0, '.')
print('Python环境已准备就绪')
print('可以直接导入项目模块: from src import config')
print('')
import code
code.interact(local=locals())
"
    
    echo -e "${GREEN}✓ 已返回控制台${NC}"
}

# 项目目录浏览
open_project_directory() {
    echo -e "${YELLOW}📂 项目目录浏览${NC}"
    echo -e "${BLUE}----------------------------------------------------------------${NC}"
    
    cd $PROJECT_ROOT
    
    echo -e "${CYAN}当前位置: $(pwd)${NC}"
    echo -e "${CYAN}目录结构:${NC}"
    
    tree -L 2 2>/dev/null || ls -la
    
    echo -e "${BLUE}----------------------------------------------------------------${NC}"
    echo ""
    echo -e "${WHITE}选择操作:${NC}"
    echo -e "  ${CYAN}1)${NC} 📝 编辑配置文件"
    echo -e "  ${CYAN}2)${NC} 📋 查看日志文件"  
    echo -e "  ${CYAN}3)${NC} 🔍 查看测试结果"
    echo -e "  ${CYAN}4)${NC} 💻 进入bash环境"
    echo -e "  ${CYAN}0)${NC} 🔙 返回主菜单"
    echo ""
    
    while true; do
        read -p "请选择 (0-4): " choice
        
        case $choice in
            1)
                echo -e "${YELLOW}📝 编辑配置文件...${NC}"
                if command -v nano >/dev/null 2>&1; then
                    nano src/config.py
                else
                    vi src/config.py
                fi
                ;;
            2)
                echo -e "${YELLOW}📋 查看日志文件...${NC}"
                if [ -d "output/logs" ] && [ "$(ls -A output/logs)" ]; then
                    ls -la output/logs/
                    echo ""
                    read -p "输入日志文件名查看内容 (按Enter跳过): " logfile
                    if [ -n "$logfile" ] && [ -f "output/logs/$logfile" ]; then
                        tail -50 "output/logs/$logfile"
                    fi
                else
                    echo -e "${YELLOW}⚠️ 日志目录为空${NC}"
                fi
                read -p "按Enter键继续..."
                ;;
            3)
                echo -e "${YELLOW}🔍 查看测试结果...${NC}"
                if [ -d "output/results" ] && [ "$(ls -A output/results)" ]; then
                    ls -la output/results/
                else
                    echo -e "${YELLOW}⚠️ 测试结果目录为空${NC}"
                fi
                read -p "按Enter键继续..."
                ;;
            4)
                echo -e "${YELLOW}💻 进入项目bash环境...${NC}"
                echo -e "${CYAN}提示: 输入 'exit' 返回控制台${NC}"
                echo ""
                (
                    export PS1="[Tiaozhanbei2.0] \u@\h:\w\$ "
                    bash --norc
                )
                echo -e "${GREEN}✓ 已返回控制台${NC}"
                ;;
            0)
                echo -e "${GREEN}✓ 返回主菜单${NC}"
                return
                ;;
            *)
                echo -e "${RED}❌ 无效选择${NC}"
                sleep 1
                ;;
        esac
        echo -e "${BLUE}----------------------------------------------------------------${NC}"
    done
}

# 主程序循环
main_loop() {
    while true; do
        show_header
        show_system_status
        show_main_menu
        
        if [ "$PLATFORM" = "jetson" ]; then
            read -p "请输入选择 (0-15): " choice
        else
            read -p "请输入选择 (0-14): " choice
        fi
        echo ""
        
        case $choice in
            1)
                full_environment_setup
                ;;
            2)
                create_environment
                read -p "按Enter键继续..."
                ;;
            3)
                install_miniforge
                read -p "按Enter键继续..."
                ;;
            4)
                if [ "$PLATFORM" = "jetson" ]; then
                    install_realsense_jetson
                    read -p "按Enter键继续..."
                else
                    start_web_interface
                fi
                ;;
            5)
                if [ "$PLATFORM" = "jetson" ]; then
                    start_web_interface
                else
                    stop_web_service
                fi
                ;;
            6)
                if [ "$PLATFORM" = "jetson" ]; then
                    stop_web_service
                else
                    run_test_mode
                fi
                ;;
            7)
                if [ "$PLATFORM" = "jetson" ]; then
                    run_test_mode
                else
                    run_calibration_mode
                fi
                ;;
            8)
                if [ "$PLATFORM" = "jetson" ]; then
                    run_calibration_mode
                else
                    run_tracking_mode
                fi
                ;;
            9)
                if [ "$PLATFORM" = "jetson" ]; then
                    run_tracking_mode
                else
                    check_configuration
                fi
                ;;
            10)
                if [ "$PLATFORM" = "jetson" ]; then
                    check_configuration
                else
                    show_system_status
                    read -p "按Enter键继续..."
                fi
                ;;
            11)
                if [ "$PLATFORM" = "jetson" ]; then
                    show_system_status
                    read -p "按Enter键继续..."
                else
                    restart_all_services
                fi
                ;;
            12)
                if [ "$PLATFORM" = "jetson" ]; then
                    restart_all_services
                else
                    cleanup_processes
                fi
                ;;
            13)
                if [ "$PLATFORM" = "jetson" ]; then
                    cleanup_processes
                else
                    enter_python_env
                fi
                ;;
            14)
                if [ "$PLATFORM" = "jetson" ]; then
                    enter_python_env
                else
                    open_project_directory
                fi
                ;;
            15)
                if [ "$PLATFORM" = "jetson" ]; then
                    open_project_directory
                else
                    echo -e "${YELLOW}⚠️ 无效选择${NC}"
                    sleep 2
                fi
                ;;
            0)
                echo -e "${GREEN}👋 感谢使用 Tiaozhanbei2.0 控制台${NC}"
                echo -e "${CYAN}再见！${NC}"
                exit 0
                ;;
            *)
                echo -e "${RED}❌ 无效选择，请重新输入${NC}"
                sleep 2
                ;;
        esac
    done
}

# 程序入口
echo -e "${YELLOW}正在初始化...${NC}"
detect_platform

# 检查环境，但不强制退出
if check_environment; then
    activate_environment
    echo -e "${GREEN}✓ 环境就绪，启动主控制台${NC}"
else
    echo -e "${YELLOW}⚠️ 环境未完全配置，建议使用安装选项${NC}"
fi

# 启动主循环
main_loop
