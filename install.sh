#!/bin/bash
# =================================================================
# Tiaozhanbei2.0 环境安装脚本
# 自动安装项目依赖和配置环境
# =================================================================

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 项目信息
PROJECT_NAME="Tiaozhanbei2.0"
CONDA_ENV_NAME="tiao"
PYTHON_VERSION="3.8"

echo -e "${BLUE}================================================================${NC}"
echo -e "${BLUE}           🚀 $PROJECT_NAME 环境安装脚本${NC}"
echo -e "${BLUE}================================================================${NC}"
echo ""

# 检查Python版本
check_python() {
    if command -v python3 &> /dev/null; then
        PYTHON_VER=$(python3 --version | cut -d' ' -f2 | cut -d'.' -f1,2)
        echo -e "${GREEN}✅ 检测到 Python $PYTHON_VER${NC}"
        if [[ $(echo "$PYTHON_VER >= 3.8" | bc -l) -eq 1 ]]; then
            echo -e "${GREEN}✅ Python版本满足要求 (>= 3.8)${NC}"
        else
            echo -e "${RED}❌ Python版本过低，需要 >= 3.8${NC}"
            exit 1
        fi
    else
        echo -e "${RED}❌ 未找到Python3，请先安装Python${NC}"
        exit 1
    fi
}

# 检查pip
check_pip() {
    if command -v pip &> /dev/null; then
        echo -e "${GREEN}✅ pip 可用${NC}"
    else
        echo -e "${YELLOW}⚠️ 安装pip...${NC}"
        sudo apt update && sudo apt install -y python3-pip
    fi
}

# 检查conda (可选)
check_conda() {
    if command -v conda &> /dev/null; then
        echo -e "${GREEN}✅ conda 可用${NC}"
        CONDA_AVAILABLE=true
    else
        echo -e "${YELLOW}⚠️ conda 未安装，将使用pip安装${NC}"
        CONDA_AVAILABLE=false
    fi
}

# 安装RealSense SDK (Ubuntu)
install_realsense_sdk() {
    echo -e "${YELLOW}📷 安装 Intel RealSense SDK...${NC}"
    
    # 检查是否已安装
    if dpkg -l | grep -q librealsense2; then
        echo -e "${GREEN}✅ RealSense SDK 已安装${NC}"
        return
    fi
    
    # 添加Intel仓库密钥
    sudo apt-key adv --keyserver keyserver.ubuntu.com --recv-key F6E65AC044F831AC80A06380C8B3A55A6F3EFCDE || \
    sudo apt-key adv --keyserver hkp://keyserver.ubuntu.com:80 --recv-key F6E65AC044F831AC80A06380C8B3A55A6F3EFCDE
    
    # 添加仓库
    sudo add-apt-repository "deb https://librealsense.intel.com/Debian/apt-repo $(lsb_release -cs) main" -u
    
    # 安装SDK
    sudo apt install -y librealsense2-dkms librealsense2-utils librealsense2-dev
    
    echo -e "${GREEN}✅ RealSense SDK 安装完成${NC}"
}

# 使用conda创建环境
install_with_conda() {
    echo -e "${YELLOW}🐍 使用conda创建环境...${NC}"
    
    # 检查环境是否已存在
    if conda env list | grep -q "$CONDA_ENV_NAME"; then
        echo -e "${YELLOW}⚠️ conda环境 '$CONDA_ENV_NAME' 已存在${NC}"
        read -p "是否重新创建? (y/N): " recreate
        if [[ $recreate =~ ^[Yy]$ ]]; then
            conda env remove -n "$CONDA_ENV_NAME" -y
        else
            echo -e "${BLUE}使用现有环境${NC}"
            conda activate "$CONDA_ENV_NAME"
            return
        fi
    fi
    
    # 创建环境
    if [ -f "environment.yml" ]; then
        echo -e "${BLUE}📄 使用 environment.yml 创建环境${NC}"
        conda env create -f environment.yml
    else
        echo -e "${BLUE}🔧 手动创建conda环境${NC}"
        conda create -n "$CONDA_ENV_NAME" python=$PYTHON_VERSION -y
        conda activate "$CONDA_ENV_NAME"
        
        # 安装conda包
        conda install -y opencv numpy flask
        
        # 安装pip包
        pip install pyrealsense2 pyserial
    fi
    
    # 激活环境
    conda activate "$CONDA_ENV_NAME"
    echo -e "${GREEN}✅ conda环境创建完成: $CONDA_ENV_NAME${NC}"
}

# 使用pip安装依赖
install_with_pip() {
    echo -e "${YELLOW}📦 使用pip安装依赖...${NC}"
    
    # 升级pip
    pip install --upgrade pip
    
    # 安装核心依赖
    echo -e "${BLUE}安装核心依赖...${NC}"
    pip install -r requirements_pip.txt
    
    echo -e "${GREEN}✅ pip依赖安装完成${NC}"
}

# 配置用户权限 (Linux)
configure_permissions() {
    echo -e "${YELLOW}🔧 配置用户权限...${NC}"
    
    # 串口权限
    sudo usermod -a -G dialout $USER
    
    # 视频设备权限
    sudo usermod -a -G video $USER
    
    echo -e "${GREEN}✅ 权限配置完成${NC}"
    echo -e "${YELLOW}⚠️ 请重新登录以生效权限更改${NC}"
}

# 验证安装
verify_installation() {
    echo -e "${YELLOW}🧪 验证安装...${NC}"
    
    # 运行测试
    if python tests/run_all.py; then
        echo -e "${GREEN}✅ 系统测试通过${NC}"
    else
        echo -e "${RED}❌ 系统测试失败${NC}"
        return 1
    fi
    
    echo -e "${GREEN}🎉 安装验证成功！${NC}"
}

# 显示使用说明
show_usage() {
    echo -e "${BLUE}================================================================${NC}"
    echo -e "${GREEN}🎉 安装完成！${NC}"
    echo -e "${BLUE}================================================================${NC}"
    echo ""
    echo -e "${YELLOW}快速开始:${NC}"
    echo -e "  1. 连接 Intel RealSense D455 相机"
    echo -e "  2. 连接机器人控制板到串口"
    echo -e "  3. 运行主控制台: ${BLUE}./master_control.sh${NC}"
    echo -e "  4. 或启动Web界面: ${BLUE}python web/web_simple.py${NC}"
    echo ""
    echo -e "${YELLOW}文档:${NC}"
    echo -e "  - README.md - 完整使用说明"
    echo -e "  - docs/ - 详细技术文档"
    echo ""
    echo -e "${YELLOW}测试:${NC}"
    echo -e "  - ${BLUE}python tests/run_all.py${NC} - 运行所有测试"
    echo -e "  - ${BLUE}python test_obstacle_avoidance.py${NC} - 测试避障功能"
    echo ""
    if [[ $CONDA_AVAILABLE == true ]]; then
        echo -e "${YELLOW}激活环境:${NC}"
        echo -e "  ${BLUE}conda activate $CONDA_ENV_NAME${NC}"
        echo ""
    fi
}

# 主安装流程
main() {
    echo -e "${BLUE}开始安装 $PROJECT_NAME...${NC}"
    echo ""
    
    # 系统检查
    check_python
    check_pip
    check_conda
    echo ""
    
    # 安装RealSense SDK (仅限Ubuntu)
    if [[ "$OSTYPE" == "linux-gnu"* ]]; then
        install_realsense_sdk
        echo ""
    fi
    
    # 选择安装方式
    if [[ $CONDA_AVAILABLE == true ]]; then
        read -p "使用conda还是pip安装? (conda/pip) [conda]: " install_method
        install_method=${install_method:-conda}
        
        if [[ $install_method == "conda" ]]; then
            install_with_conda
        else
            install_with_pip
        fi
    else
        install_with_pip
    fi
    echo ""
    
    # 配置权限 (仅限Linux)
    if [[ "$OSTYPE" == "linux-gnu"* ]]; then
        configure_permissions
        echo ""
    fi
    
    # 验证安装
    verify_installation
    echo ""
    
    # 显示使用说明
    show_usage
}

# 检查操作系统
if [[ "$OSTYPE" == "darwin"* ]]; then
    echo -e "${YELLOW}⚠️ 检测到macOS，某些步骤可能需要手动操作${NC}"
elif [[ "$OSTYPE" == "msys" ]] || [[ "$OSTYPE" == "win32" ]]; then
    echo -e "${YELLOW}⚠️ 检测到Windows，请手动安装RealSense SDK${NC}"
fi

# 运行主函数
main "$@"
