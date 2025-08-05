#!/bin/bash
# =================================================================
# Jetson AGX Xavier 专用安装脚本
# Installation Script for Jetson AGX Xavier
# Includes RealSense SDK compilation and optimization
# =================================================================

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
WHITE='\033[1;37m'
NC='\033[0m'

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CONDA_ENV="tiao"

echo -e "${BLUE}================================================================${NC}"
echo -e "${WHITE}        🤖 Jetson AGX Xavier 环境安装脚本${NC}"
echo -e "${WHITE}        Tiaozhanbei2.0 Visual Control System${NC}"
echo -e "${BLUE}================================================================${NC}"
echo ""

# 检查是否为Jetson平台
check_jetson_platform() {
    echo -e "${YELLOW}🔍 检查Jetson平台...${NC}"
    
    if [ ! -f "/etc/nv_tegra_release" ]; then
        echo -e "${RED}❌ 此脚本仅适用于NVIDIA Jetson平台${NC}"
        exit 1
    fi
    
    JETSON_MODEL=$(cat /proc/device-tree/model)
    echo -e "${GREEN}✓ 检测到设备: ${JETSON_MODEL}${NC}"
    
    # 检查JetPack版本
    if [ -f "/etc/nv_tegra_release" ]; then
        JETPACK_VERSION=$(head -n 1 /etc/nv_tegra_release)
        echo -e "${CYAN}JetPack版本: ${JETPACK_VERSION}${NC}"
    fi
    
    echo ""
}

# 系统更新和基础包安装
install_system_packages() {
    echo -e "${YELLOW}📦 更新系统并安装基础包...${NC}"
    
    # 更新包列表
    sudo apt update
    
    # 安装编译工具和依赖
    sudo apt install -y \
        build-essential \
        cmake \
        pkg-config \
        git \
        wget \
        curl \
        unzip \
        libjpeg-dev \
        libpng-dev \
        libtiff-dev \
        libavcodec-dev \
        libavformat-dev \
        libswscale-dev \
        libv4l-dev \
        libxvidcore-dev \
        libx264-dev \
        libgtk-3-dev \
        libatlas-base-dev \
        gfortran \
        python3-dev \
        python3-pip \
        libssl-dev \
        libusb-1.0-0-dev \
        libgtk-3-dev \
        libglfw3-dev \
        libgl1-mesa-dev \
        libglu1-mesa-dev
    
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✓ 系统包安装完成${NC}"
    else
        echo -e "${RED}❌ 系统包安装失败${NC}"
        exit 1
    fi
    
    echo ""
}

# 安装Miniforge
install_miniforge() {
    echo -e "${YELLOW}🐍 安装Miniforge for ARM64...${NC}"
    
    # 检查是否已安装
    if command -v conda >/dev/null 2>&1; then
        echo -e "${GREEN}✓ Conda已安装，跳过Miniforge安装${NC}"
        return 0
    fi
    
    cd /tmp
    
    # 下载Miniforge for ARM64
    MINIFORGE_URL="https://github.com/conda-forge/miniforge/releases/latest/download/Miniforge3-Linux-aarch64.sh"
    wget $MINIFORGE_URL -O miniforge.sh
    
    if [ $? -ne 0 ]; then
        echo -e "${RED}❌ Miniforge下载失败${NC}"
        exit 1
    fi
    
    # 安装
    chmod +x miniforge.sh
    bash miniforge.sh -b -p $HOME/miniforge3
    
    # 初始化
    $HOME/miniforge3/bin/conda init bash
    source ~/.bashrc
    
    # 清理
    rm -f miniforge.sh
    
    echo -e "${GREEN}✓ Miniforge安装完成${NC}"
    echo -e "${YELLOW}请重新启动终端或运行 'source ~/.bashrc'${NC}"
    echo ""
}

# 编译安装RealSense SDK
install_realsense_sdk() {
    echo -e "${YELLOW}📷 编译安装Intel RealSense SDK...${NC}"
    
    # 创建工作目录
    mkdir -p ~/realsense_build
    cd ~/realsense_build
    
    # 下载librealsense源码
    echo -e "${CYAN}下载librealsense源码...${NC}"
    git clone https://github.com/IntelRealSense/librealsense.git
    cd librealsense
    
    # 应用Jetson补丁
    echo -e "${CYAN}应用Jetson补丁...${NC}"
    ./scripts/setup_udev_rules.sh
    
    # 检查内核版本并应用补丁
    KERNEL_VERSION=$(uname -r)
    echo -e "${CYAN}内核版本: ${KERNEL_VERSION}${NC}"
    
    # 对于JetPack 4.6+，需要特殊处理
    if [[ $KERNEL_VERSION == *"5.10"* ]]; then
        echo -e "${YELLOW}检测到5.10内核，应用特殊补丁...${NC}"
        ./scripts/patch-realsense-ubuntu-lts-hwe.sh
    else
        echo -e "${YELLOW}应用标准内核补丁...${NC}"
        ./scripts/patch-realsense-ubuntu-lts.sh
    fi
    
    # 创建构建目录
    mkdir build && cd build
    
    # 配置CMake
    echo -e "${CYAN}配置编译选项...${NC}"
    cmake .. \
        -DBUILD_EXAMPLES=true \
        -DCMAKE_BUILD_TYPE=Release \
        -DFORCE_RSUSB_BACKEND=false \
        -DBUILD_WITH_CUDA=true \
        -DBUILD_PYTHON_BINDINGS=true \
        -DPYTHON_EXECUTABLE=/usr/bin/python3 \
        -DBUILD_CV_EXAMPLES=false
    
    # 编译 (使用所有CPU核心)
    echo -e "${CYAN}开始编译 (使用 $(nproc) 个CPU核心)...${NC}"
    make -j$(nproc)
    
    if [ $? -ne 0 ]; then
        echo -e "${RED}❌ RealSense SDK编译失败${NC}"
        return 1
    fi
    
    # 安装
    echo -e "${CYAN}安装RealSense SDK...${NC}"
    sudo make install
    
    # 更新动态链接库缓存
    sudo ldconfig
    
    # 设置udev规则
    sudo cp ../config/99-realsense-libusb.rules /etc/udev/rules.d/
    sudo udevadm control --reload-rules && sudo udevadm trigger
    
    # 将Python绑定复制到系统路径
    if [ -f "wrappers/python/pyrealsense2.cpython-*.so" ]; then
        sudo cp wrappers/python/pyrealsense2.cpython-*.so /usr/local/lib/python3.*/site-packages/ 2>/dev/null || true
    fi
    
    echo -e "${GREEN}✓ RealSense SDK安装完成${NC}"
    
    # 测试安装
    echo -e "${CYAN}测试RealSense SDK...${NC}"
    if python3 -c "import pyrealsense2 as rs; print('RealSense SDK导入成功')" 2>/dev/null; then
        echo -e "${GREEN}✓ RealSense SDK Python绑定工作正常${NC}"
    else
        echo -e "${YELLOW}⚠️ Python绑定可能需要额外配置${NC}"
    fi
    
    # 清理构建文件
    cd ~
    rm -rf ~/realsense_build
    
    echo ""
}

# 安装PyTorch for Jetson
install_pytorch_jetson() {
    echo -e "${YELLOW}🔥 安装PyTorch for Jetson...${NC}"
    
    # 激活conda环境
    source $HOME/miniforge3/bin/activate
    conda activate $CONDA_ENV
    
    # 检查JetPack版本来确定PyTorch版本
    echo -e "${CYAN}为Jetson平台安装优化的PyTorch...${NC}"
    
    # 安装依赖
    pip install Cython
    pip install numpy
    
    # 从NVIDIA官方源安装PyTorch
    # 注意：这里需要根据实际的JetPack版本选择对应的wheel
    echo -e "${YELLOW}正在下载PyTorch wheel文件...${NC}"
    
    # JetPack 4.6 对应的PyTorch版本
    TORCH_URL="https://nvidia.box.com/shared/static/fjtbno0vpo676a25cgvuqc1wty0fkkg6.whl"
    wget $TORCH_URL -O torch-1.10.0-cp38-cp38-linux_aarch64.whl
    
    if [ $? -eq 0 ]; then
        pip install torch-1.10.0-cp38-cp38-linux_aarch64.whl
        rm torch-1.10.0-cp38-cp38-linux_aarch64.whl
        
        # 安装torchvision
        TORCHVISION_URL="https://nvidia.box.com/shared/static/kjm8rk2tx2i2p3w0z4u2k2bnbqb0s5xc.whl"
        wget $TORCHVISION_URL -O torchvision-0.11.0-cp38-cp38-linux_aarch64.whl
        pip install torchvision-0.11.0-cp38-cp38-linux_aarch64.whl
        rm torchvision-0.11.0-cp38-cp38-linux_aarch64.whl
        
        echo -e "${GREEN}✓ PyTorch for Jetson安装完成${NC}"
    else
        echo -e "${YELLOW}⚠️ PyTorch wheel下载失败，将使用CPU版本${NC}"
        pip install torch torchvision --index-url https://download.pytorch.org/whl/cpu
    fi
    
    # 测试PyTorch
    python -c "import torch; print(f'PyTorch版本: {torch.__version__}'); print(f'CUDA可用: {torch.cuda.is_available()}')"
    
    echo ""
}

# 创建conda环境
create_conda_environment() {
    echo -e "${YELLOW}🐍 创建Conda环境...${NC}"
    
    source $HOME/miniforge3/bin/activate
    
    cd $PROJECT_ROOT
    
    # 使用Jetson专用环境配置
    if [ -f "environment_jetson.yml" ]; then
        echo -e "${CYAN}使用Jetson专用环境配置...${NC}"
        conda env create -f environment_jetson.yml
    else
        echo -e "${YELLOW}⚠️ 未找到Jetson环境配置，使用标准配置${NC}"
        conda env create -f environment.yml
    fi
    
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✓ Conda环境创建成功${NC}"
        
        # 激活环境并安装额外包
        conda activate $CONDA_ENV
        
        # 安装项目特定的包
        echo -e "${CYAN}安装项目依赖包...${NC}"
        pip install pyrealsense2 pyserial loguru rich typer
        
        # 安装Jetson GPIO库
        pip install Jetson.GPIO
        
        echo -e "${GREEN}✓ 环境配置完成${NC}"
    else
        echo -e "${RED}❌ 环境创建失败${NC}"
        return 1
    fi
    
    echo ""
}

# 优化Jetson性能
optimize_jetson_performance() {
    echo -e "${YELLOW}⚡ 优化Jetson性能设置...${NC}"
    
    # 设置最大性能模式
    sudo nvpmodel -m 0
    
    # 设置最大CPU和GPU频率
    sudo jetson_clocks
    
    # 增加swap文件大小（如果需要）
    if [ $(free -m | awk '/^Swap:/ {print $2}') -lt 4096 ]; then
        echo -e "${CYAN}增加swap文件大小...${NC}"
        sudo fallocate -l 4G /swapfile
        sudo chmod 600 /swapfile
        sudo mkswap /swapfile
        sudo swapon /swapfile
        echo '/swapfile none swap sw 0 0' | sudo tee -a /etc/fstab
    fi
    
    echo -e "${GREEN}✓ 性能优化完成${NC}"
    echo ""
}

# 验证安装
verify_installation() {
    echo -e "${YELLOW}🔍 验证安装...${NC}"
    
    source $HOME/miniforge3/bin/activate
    conda activate $CONDA_ENV
    
    cd $PROJECT_ROOT
    
    echo -e "${CYAN}测试核心模块...${NC}"
    
    # 测试Python模块
    python -c "
import sys
print(f'Python版本: {sys.version}')

try:
    import cv2
    print(f'✓ OpenCV版本: {cv2.__version__}')
except ImportError as e:
    print(f'❌ OpenCV导入失败: {e}')

try:
    import numpy as np
    print(f'✓ NumPy版本: {np.__version__}')
except ImportError as e:
    print(f'❌ NumPy导入失败: {e}')

try:
    import pyrealsense2 as rs
    print('✓ RealSense SDK导入成功')
    ctx = rs.context()
    devices = ctx.query_devices()
    print(f'  检测到 {devices.size()} 个RealSense设备')
except ImportError as e:
    print(f'❌ RealSense SDK导入失败: {e}')

try:
    import serial
    print(f'✓ PySerial版本: {serial.__version__}')
except ImportError as e:
    print(f'❌ PySerial导入失败: {e}')

try:
    import flask
    print('✓ Flask导入成功')
except ImportError as e:
    print(f'❌ Flask导入失败: {e}')

try:
    import torch
    print(f'✓ PyTorch版本: {torch.__version__}')
    print(f'  CUDA可用: {torch.cuda.is_available()}')
except ImportError as e:
    print(f'❌ PyTorch导入失败: {e}')

try:
    import Jetson.GPIO as GPIO
    print('✓ Jetson.GPIO导入成功')
except ImportError as e:
    print(f'⚠️ Jetson.GPIO导入失败: {e}')
"
    
    echo ""
    echo -e "${CYAN}测试项目模块...${NC}"
    
    # 测试项目模块
    python -c "
try:
    from src import config
    print('✓ 项目配置模块')
except ImportError as e:
    print(f'❌ 配置模块: {e}')

try:
    from src.camera import capture
    print('✓ 相机模块')
except ImportError as e:
    print(f'❌ 相机模块: {e}')

try:
    from src.perception import pipe_tracking
    print('✓ 管道跟踪模块')
except ImportError as e:
    print(f'❌ 管道跟踪模块: {e}')

try:
    from web.web_simple import app
    print('✓ Web应用模块')
except ImportError as e:
    print(f'❌ Web应用模块: {e}')
"
    
    echo ""
}

# 创建启动脚本
create_startup_scripts() {
    echo -e "${YELLOW}📝 创建启动脚本...${NC}"
    
    # 创建环境激活脚本
    cat > $PROJECT_ROOT/activate_env.sh << 'EOF'
#!/bin/bash
# 激活Tiaozhanbei2.0环境
source $HOME/miniforge3/bin/activate
conda activate tiao
echo "✓ Tiaozhanbei2.0环境已激活"
EOF
    
    chmod +x $PROJECT_ROOT/activate_env.sh
    
    # 创建性能优化脚本
    cat > $PROJECT_ROOT/optimize_jetson.sh << 'EOF'
#!/bin/bash
# Jetson性能优化
sudo nvpmodel -m 0  # 最大性能模式
sudo jetson_clocks   # 最大频率
echo "✓ Jetson性能优化完成"
EOF
    
    chmod +x $PROJECT_ROOT/optimize_jetson.sh
    
    echo -e "${GREEN}✓ 启动脚本创建完成${NC}"
    echo ""
}

# 显示安装完成信息
show_completion_info() {
    echo -e "${BLUE}================================================================${NC}"
    echo -e "${GREEN}           🎉 Jetson AGX Xavier 安装完成！${NC}"
    echo -e "${BLUE}================================================================${NC}"
    echo ""
    echo -e "${CYAN}环境信息:${NC}"
    echo -e "  📍 项目目录: ${PROJECT_ROOT}"
    echo -e "  🐍 Conda环境: ${CONDA_ENV}"
    echo -e "  🤖 设备平台: Jetson AGX Xavier"
    echo ""
    echo -e "${CYAN}使用方法:${NC}"
    echo -e "  1. 激活环境: ${YELLOW}source activate_env.sh${NC}"
    echo -e "  2. 启动控制台: ${YELLOW}bash main.sh${NC}"
    echo -e "  3. 性能优化: ${YELLOW}bash optimize_jetson.sh${NC}"
    echo ""
    echo -e "${CYAN}Web界面:${NC}"
    echo -e "  🌐 本地访问: ${YELLOW}http://localhost:5000${NC}"
    echo -e "  🌐 局域网访问: ${YELLOW}http://$(hostname -I | awk '{print $1}'):5000${NC}"
    echo ""
    echo -e "${CYAN}项目功能:${NC}"
    echo -e "  📷 RealSense相机支持"
    echo -e "  🎯 实时管道跟踪"
    echo -e "  🌐 Web控制界面"
    echo -e "  🔧 系统监控和控制"
    echo ""
    echo -e "${YELLOW}注意事项:${NC}"
    echo -e "  • 首次使用前请连接RealSense相机"
    echo -e "  • 建议定期运行性能优化脚本"
    echo -e "  • 可通过main.sh访问所有系统功能"
    echo ""
    echo -e "${GREEN}安装日志已保存到: install_jetson.log${NC}"
    echo -e "${BLUE}================================================================${NC}"
}

# 主安装流程
main_installation() {
    echo -e "${CYAN}开始Jetson AGX Xavier环境安装...${NC}"
    echo -e "${CYAN}预计安装时间: 30-60分钟${NC}"
    echo ""
    
    read -p "是否继续安装? (y/N): " confirm
    if [[ ! $confirm =~ ^[Yy]$ ]]; then
        echo -e "${YELLOW}安装已取消${NC}"
        exit 0
    fi
    
    # 记录安装日志
    exec > >(tee -a install_jetson.log)
    exec 2>&1
    
    echo -e "${CYAN}安装开始时间: $(date)${NC}"
    echo ""
    
    # 执行安装步骤
    check_jetson_platform
    install_system_packages
    install_miniforge
    
    # 重新加载环境变量
    source ~/.bashrc 2>/dev/null || true
    
    create_conda_environment
    install_realsense_sdk
    install_pytorch_jetson
    optimize_jetson_performance
    create_startup_scripts
    verify_installation
    
    echo -e "${CYAN}安装完成时间: $(date)${NC}"
    
    show_completion_info
}

# 检查是否以root权限运行
if [ "$EUID" -eq 0 ]; then
    echo -e "${RED}❌ 请不要以root权限运行此脚本${NC}"
    echo -e "${YELLOW}正确用法: bash install_jetson.sh${NC}"
    exit 1
fi

# 运行主安装流程
main_installation
