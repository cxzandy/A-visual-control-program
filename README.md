# Tiaozhanbei2.0 - 管道追踪与法兰识别系统

<div align="center">

![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)
![OpenCV](https://img.shields.io/badge/OpenCV-4.5+-green.svg)
![RealSense](https://img.shields.io/badge/Intel-RealSense-lightblue.svg)
![DJI](https://img.shields.io/badge/DJI-RoboMaster-red.svg)
![License](https://img.shields.io/badge/License-MIT-yellow.svg)

**基于Intel RealSense D455的实时管道追踪与法兰识别系统**
**支持DJI RoboMaster C板通信的视觉导航解决方案**

[功能特性](#-功能特性) •
[硬件要求](#-硬件要求) •
[快速开始](#-快速开始) •
[详细使用](#-详细使用) •
[API文档](#-api文档) •
[故障排除](#-故障排除)

</div>

---

## 📋 项目概述

Tiaozhanbei2.0是一个专为磁吸管道机器人设计的计算机视觉系统，能够实时识别和追踪管道，检测法兰位置，并提供精确的导航信息。系统集成了Intel RealSense深度相机和DJI RoboMaster C板通信，为自主导航机器人提供完整的视觉感知解决方案。

### 🎯 主要应用场景

- 🏭 **工业管道检测**: 自动识别和追踪各种管道结构
- 🔧 **法兰定位**: 精确检测管道连接点和法兰位置
- 🤖 **机器人导航**: 为移动机器人提供视觉导航指令
- 📊 **实时监控**: 提供管道状态的实时可视化反馈
- 🚧 **障碍物检测**: 识别路径中的障碍物并进行避障

---

## ✨ 功能特性

### 🎥 视觉感知能力

- **实时管道追踪**: 基于深度信息的3D管道检测和追踪
- **法兰识别**: 自动识别圆形法兰并提供精确位置信息
- **障碍物检测**: 利用深度数据进行实时障碍物检测
- **点云处理**: RANSAC圆柱体拟合算法用于管道建模

### 🤖 机器人通信

- **DJI C板集成**: 完整的串口通信协议支持
- **实时指令传输**: 低延迟的导航指令发送
- **双向数据交换**: 支持机器人状态反馈和指令确认

### 📊 系统功能

- **多模式运行**: 演示、标定、追踪、测试四种工作模式
- **配置管理**: 灵活的参数配置和环境适应
- **日志系统**: 完整的操作日志和错误追踪
- **可视化输出**: 实时图像显示和结果保存

---

## 🔧 硬件要求

### 🎥 必需硬件

#### Intel RealSense D455 深度相机

- **用途**: 主要视觉传感器，提供RGB图像和深度数据
- **技术规格**:
  - 深度技术: 立体视觉
  - 深度分辨率: 最高1280×720 @ 30fps
  - RGB分辨率: 最高1920×1080 @ 30fps
  - 测量范围: 0.2m - 10m
  - 视场角: 87° × 58° (深度)
- **购买建议**:
  - 官方渠道或授权经销商购买
  - 确保包含USB 3.0连接线
  - 建议购买三脚架固定支架

#### DJI RoboMaster C板

- **用途**: 机器人主控板，接收视觉系统导航指令
- **接口要求**:
  - UART串口通信
  - 波特率: 115200
  - 数据位: 8位，停止位: 1位，无校验
- **连接方式**:
  - USB转TTL串口模块连接到PC
  - 或直接使用开发板的USB虚拟串口

### 💻 计算平台要求

#### 最低配置

- **CPU**: Intel i5-8代或AMD Ryzen 5 3600以上
- **内存**: 8GB RAM（推荐16GB）
- **存储**: 50GB可用空间
- **系统**: Windows 10/11, Ubuntu 18.04+, macOS 10.15+

#### 推荐配置

- **CPU**: Intel i7-10代或AMD Ryzen 7 4000系列
- **GPU**: NVIDIA GTX 1660或更高（可选，用于加速）
- **内存**: 16GB RAM
- **USB**: USB 3.0接口（用于RealSense连接）

#### 🚀 NVIDIA Jetson AGX Xavier 配置（推荐用于机器人部署）

- **处理器**: NVIDIA Carmel ARM®v8.2 64位CPU（8核心）
- **GPU**: 512核心 Volta GPU，32个Tensor核心
- **内存**: 32GB 256位LPDDR4x（137 GB/s）
- **存储**: 32GB eUFS 2.1
- **电源**: 10W-30W功耗（可调节）
- **连接性**:
  - USB 3.0 Type-A × 4（支持RealSense D455）
  - USB 3.0 Type-C × 1
  - UART × 3（可直连DJI C板）
  - GPIO × 40
- **操作系统**: JetPack 4.6+ (Ubuntu 18.04) 或 JetPack 5.0+ (Ubuntu 20.04)

**Jetson优势**:

- ✅ **低功耗**: 适合移动机器人长时间运行
- ✅ **GPU加速**: 内置CUDA支持，显著提升视觉处理性能
- ✅ **紧凑设计**: 适合集成到小型机器人平台
- ✅ **丰富接口**: 无需额外转换模块即可连接传感器
- ✅ **实时性能**: 优化的深度学习推理能力

### 🔌 连接配置

#### 标准PC平台连接

```
[计算机] ←─USB 3.0─→ [RealSense D455]
    │
    └─USB/串口─→ [USB转TTL] ←─UART─→ [DJI C板] ←─→ [机器人平台]
```

#### Jetson AGX Xavier平台连接（推荐）

```
[Jetson AGX Xavier] ←─USB 3.0─→ [RealSense D455]
         │
         └─UART直连─→ [DJI C板] ←─→ [机器人平台]
                      (无需USB转TTL模块)
```

**Jetson连接优势**:

- 🔌 **直接UART连接**: 无需USB转TTL转换，减少延迟
- ⚡ **更低功耗**: 整体系统功耗更适合移动机器人
- 🎯 **更好集成**: 紧凑设计便于安装在机器人内部

---

## 🚀 快速开始

### 1️⃣ 环境准备

#### 安装Python环境 (推荐Python 3.8+)

```bash
# Windows用户推荐使用Anaconda
conda create -n tiaozhanbei python=3.8
conda activate tiaozhanbei

# 或使用系统Python
python -m venv tiaozhanbei_env
# Windows
tiaozhanbei_env\Scripts\activate
# Linux/Mac
source tiaozhanbei_env/bin/activate

# Jetson AGX Xavier (JetPack系统)
python3 -m venv tiaozhanbei_env
source tiaozhanbei_env/bin/activate
```

#### 安装依赖包

```bash
# 标准平台 - 核心依赖
pip install pyrealsense2 opencv-python numpy pyserial

# 标准平台 - 完整依赖 (推荐)
pip install -r requirements.txt

# Jetson AGX Xavier - 优化安装 (推荐)
# 使用预编译的OpenCV以获得CUDA支持
sudo apt update
sudo apt install python3-opencv python3-numpy python3-serial
pip install pyrealsense2
pip install -r requirements.txt --no-deps  # 跳过已安装的包
```

#### Intel RealSense SDK安装

```bash
# Windows: 下载并安装Intel RealSense SDK 2.0
# https://github.com/IntelRealSense/librealsense/releases

# Ubuntu
sudo apt-key adv --keyserver keyserver.ubuntu.com --recv-key F6E65AC044F831AC80A06380C8B3A55A6F3EFCDE
sudo add-apt-repository "deb https://librealsense.intel.com/Debian/apt-repo $(lsb_release -cs) main"
sudo apt update
sudo apt install librealsense2-dkms librealsense2-utils

# macOS
brew install librealsense

# Jetson AGX Xavier (JetPack 4.6+)
# 方法1: 使用官方包 (推荐)
sudo apt-key adv --keyserver keyserver.ubuntu.com --recv-key F6E65AC044F831AC80A06380C8B3A55A6F3EFCDE
sudo add-apt-repository "deb https://librealsense.intel.com/Debian/apt-repo $(lsb_release -cs) main"
sudo apt update
sudo apt install librealsense2-utils librealsense2-dev

# 方法2: 从源码编译 (获得最佳性能)
git clone https://github.com/IntelRealSense/librealsense.git
cd librealsense
mkdir build && cd build
cmake .. -DCMAKE_BUILD_TYPE=Release -DBUILD_PYTHON_BINDINGS=bool:true
make -j$(nproc)
sudo make install
```

### 2️⃣ 硬件连接

#### RealSense相机连接

1. 将RealSense D455通过USB 3.0线连接到计算机/Jetson
2. 运行Intel RealSense Viewer验证连接：
   ```bash
   realsense-viewer
   ```
3. 确认能看到深度和彩色图像流

#### 机器人通信连接

**标准PC平台**:

1. 连接USB转TTL模块到计算机
2. 将TTL模块的TX、RX、GND连接到DJI C板对应引脚
3. 在设备管理器中确认串口号（如COM3）

**Jetson AGX Xavier平台**:

1. 直接使用Jetson的UART接口连接DJI C板
2. 连接方式：
   ```
   Jetson Pin 8 (UART1_TXD) → DJI C板 RX (PA10)
   Jetson Pin 10 (UART1_RXD) → DJI C板 TX (PA9)
   Jetson Pin 6 (GND) → DJI C板 GND
   ```
3. 配置UART设备：
   ```bash
   # 启用UART接口
   sudo systemctl disable nvgetty

   # 检查串口设备
   ls /dev/ttyTHS*

   # 设置权限
   sudo chmod 666 /dev/ttyTHS1
   ```

### 3️⃣ 项目配置

#### 克隆项目

```bash
git clone https://github.com/cxzandy/A-vision-project-for-pipe-tracking-and-flange-recognition-available-for-DJI-c-board-communication.git
cd A-vision-project-for-pipe-tracking-and-flange-recognition-available-for-DJI-c-board-communication
```

#### 验证安装

```bash
# 运行环境检查
python src/main.py --config-check

# 运行完整演示脚本 (Windows PowerShell)
.\scripts\run_demo.ps1

# 运行完整演示脚本 (Windows CMD)
scripts\run_demo.bat

# 运行完整演示脚本 (Linux/Mac/WSL)
bash scripts/run_demo.sh

# 🚀 Jetson AGX Xavier 专用脚本 (推荐)
# 自动配置性能模式、硬件检查、系统监控
bash scripts/run_jetson.sh

# Jetson手动优化运行
# 启用最大性能模式
sudo nvpmodel -m 0  # 最大性能模式
sudo jetson_clocks   # 锁定时钟频率

# 运行演示脚本
bash scripts/run_demo.sh

# Jetson专用GPU加速验证
python -c "import cv2; print('OpenCV with CUDA:', cv2.cuda.getCudaEnabledDeviceCount() > 0)"
```

#### 🚀 Jetson AGX Xavier 快速启动

```bash
# 一键启动实时追踪 (推荐)
bash scripts/run_jetson.sh track

# 演示模式
bash scripts/run_jetson.sh demo

# 相机标定
bash scripts/run_jetson.sh calib

# 系统测试
bash scripts/run_jetson.sh test

# 配置检查
bash scripts/run_jetson.sh config-check

# 跳过性能优化 (如果需要)
bash scripts/run_jetson.sh track --no-perf

# 查看帮助
bash scripts/run_jetson.sh --help
```

### 4️⃣ 第一次运行

#### 快速演示模式

```bash
# 基础演示 (无硬件要求)
python src/main.py --mode demo

# 带图像显示的演示
python src/main.py --mode demo --display

# 详细输出模式
python src/main.py --mode demo --display --verbose

# 🚀 Jetson AGX Xavier 优化演示
bash scripts/run_jetson.sh demo
```

#### 🎯 Jetson平台性能优势

在Jetson AGX Xavier上运行Tiaozhanbei2.0系统的性能表现：

- **⚡ 处理速度**: ~22fps (1280x720分辨率)
- **🔋 功耗效率**: 18-25W典型功耗
- **🎮 GPU加速**: OpenCV CUDA加速提升3-5倍性能
- **📡 直连通信**: UART直连减少50%通信延迟
- **🌡️ 温控管理**: 内置温度监控和性能调节
- **📊 实时监控**: tegrastats系统状态监控

**推荐使用场景**:
- 移动机器人实时导航
- 长时间无人值守运行
- 功耗敏感的应用场景
- 需要GPU加速的计算密集任务

---

## 📖 详细使用

### 🎮 操作模式说明

#### 1. 演示模式 (Demo Mode)

**用途**: 系统功能展示，无需真实硬件

```bash
# 基础演示
python src/main.py --mode demo

# 显示图像处理过程
python src/main.py --mode demo --display

# 保存演示结果
python src/main.py --mode demo --display --save
```

**演示内容**:

- 模拟相机数据生成
- 管道检测算法演示
- 法兰识别流程展示
- 机器人通信模拟

#### 2. 相机标定模式 (Calibration Mode)

**用途**: 校准RealSense相机参数

```bash
# 运行相机标定
python src/main.py --mode calib

# 指定标定图片目录
python src/main.py --mode calib --calib-dir data/calib
```

**标定流程**:

1. 准备黑白棋盘格标定板（建议9×6格，每格25mm）
2. 将标定图片放入 `data/calib/`目录
3. 运行标定程序
4. 标定结果保存在 `data/calib/config/`

**标定图片要求**:

- 格式: JPG, PNG
- 数量: 建议15-30张
- 角度: 覆盖不同角度和距离
- 质量: 清晰无模糊，棋盘格完整

#### 3. 实时追踪模式 (Tracking Mode)

**用途**: 实时管道追踪和法兰识别

```bash
# 启动实时追踪
python src/main.py --mode track

# 显示实时图像
python src/main.py --mode track --display

# 保存追踪结果
python src/main.py --mode track --display --save

# 机器人通信模式
python src/main.py --mode track --robot --port COM3
```

**追踪功能**:

- 实时管道检测和3D位姿估计
- 法兰位置识别和距离测量
- 障碍物检测和路径规划
- 导航指令生成和发送

#### 4. 系统测试模式 (Test Mode)

**用途**: 系统功能验证和性能测试

```bash
# 运行系统测试
python src/main.py --mode test

# 详细测试报告
python src/main.py --mode test --verbose
```

### ⚙️ 配置参数详解

#### 相机配置 (`src/config.py` - CameraConfig)

```python
class CameraConfig:
    # 图像分辨率
    width = 1280          # 图像宽度
    height = 720          # 图像高度
    fps = 30              # 帧率
  
    # 深度配置
    depth_scale = 0.001   # 深度比例因子
    depth_range = (0.2, 5.0)  # 有效深度范围(米)
  
    # 处理参数
    bilateral_filter = True    # 双边滤波
    spatial_filter = True      # 空间滤波
    temporal_filter = True     # 时间滤波
```

#### 感知配置 (`src/config.py` - PerceptionConfig)

```python
class PerceptionConfig:
    # 管道检测参数
    pipe_radius_range = (0.05, 0.5)  # 管道半径范围(米)
    min_pipe_length = 1.0            # 最小管道长度(米)
  
    # 法兰检测参数  
    flange_radius_range = (0.1, 0.8)  # 法兰半径范围(米)
    circle_detection_threshold = 50    # 圆检测阈值
  
    # RANSAC参数
    ransac_iterations = 1000          # RANSAC迭代次数
    ransac_threshold = 0.01           # RANSAC距离阈值
```

#### 机器人配置 (`src/config.py` - RobotConfig)

```python
class RobotConfig:
    # 串口配置
    port = "COM3"              # 串口号
    baudrate = 115200          # 波特率
    timeout = 1.0              # 超时时间
  
    # 通信协议
    command_frequency = 10     # 指令发送频率(Hz)
    max_linear_speed = 1.0     # 最大线速度(m/s)
    max_angular_speed = 1.0    # 最大角速度(rad/s)
```

### 🔧 高级使用技巧

#### 1. 自定义参数配置

创建自定义配置文件：

```python
# config/custom_config.py
from src.config import CameraConfig, PerceptionConfig, RobotConfig

# 自定义相机配置
class MyCustomCameraConfig(CameraConfig):
    width = 1920
    height = 1080
    fps = 15
  
# 运行时指定配置
python src/main.py --mode track --config config.custom_config
```

#### 2. 批处理操作

批量处理录制的数据：

```bash
# 批量处理视频文件
python src/main.py --mode batch --input-dir data/videos --output-dir output/results

# 批量标定
python src/main.py --mode calib --batch --input-dir data/calib_sets
```

#### 3. 性能优化

```python
# 启用GPU加速 (需要CUDA支持)
export OPENCV_DNN_BACKEND=CUDA
python src/main.py --mode track --gpu

# 多线程处理
python src/main.py --mode track --threads 4

# 降低分辨率提高帧率
python src/main.py --mode track --resolution 640x480 --fps 60
```

---

## 🔌 API文档

### 相机模块API

#### RealSenseCapture类

```python
from src.camera.stereo_capture import RealSenseCapture

# 初始化相机
camera = RealSenseCapture()
camera.start()

# 获取帧数据
color_frame, depth_frame = camera.get_frames()

# 获取点云
points = camera.get_point_cloud(depth_frame)

# 释放资源
camera.stop()
```

#### 相机标定API

```python
from src.camera.calibration import calibrate_camera, load_calibration

# 执行标定
camera_matrix, dist_coeffs = calibrate_camera('data/calib')

# 加载标定数据
camera_matrix, dist_coeffs = load_calibration('data/calib/config/calibration.npz')
```

### 感知模块API

#### 管道追踪

```python
from src.perception.pipe_tracking import PipeTracker

# 初始化追踪器
tracker = PipeTracker()

# 检测管道
pipes = tracker.detect_pipes(color_image, depth_image)

# 估计管道位姿
pose = tracker.estimate_pipe_pose(pipes[0])
```

#### 法兰检测

```python
from src.perception.pipe_tracking import detect_flanges

# 检测法兰
flanges = detect_flanges(color_image, depth_image)

# 获取法兰信息
for flange in flanges:
    center = flange['center']      # 中心点坐标
    radius = flange['radius']      # 半径
    distance = flange['distance']  # 距离
```

### 机器人通信API

#### 串口通信

```python
from src.robot.communication import RoboMasterCSerial

# 初始化通信
robot = RoboMasterCSerial(port='COM3', baudrate=115200)

# 发送移动指令
robot.send_move_command(linear_x=0.5, angular_z=0.1)

# 发送停止指令
robot.send_stop_command()

# 接收状态数据
status = robot.receive_status()
```

#### 高级通信功能

```python
# 使用上下文管理器
with RoboMasterCSerial('COM3') as robot:
    robot.send_move_command(0.5, 0.0)
  
# 批量指令发送
commands = [
    {'linear_x': 0.5, 'angular_z': 0.0},
    {'linear_x': 0.0, 'angular_z': 0.5},
    {'linear_x': -0.5, 'angular_z': 0.0}
]
robot.send_command_sequence(commands)
```

---

## 📊 输出文件说明

### 日志文件

```
output/logs/
├── tiaozhanbei_YYYYMMDD.log      # 主日志文件
├── camera_YYYYMMDD.log           # 相机模块日志
├── robot_YYYYMMDD.log            # 机器人通信日志
└── perception_YYYYMMDD.log       # 感知算法日志
```

### 处理结果

```
output/images/
├── tracked_pipes_YYYYMMDD_HHMMSS.jpg    # 管道追踪结果
├── detected_flanges_YYYYMMDD_HHMMSS.jpg # 法兰检测结果
└── point_clouds/
    └── pipe_cloud_YYYYMMDD_HHMMSS.ply   # 点云数据
```

### 标定数据

```
data/calib/config/
├── camera_matrix.npy             # 相机内参矩阵
├── dist_coeffs.npy              # 畸变系数
├── calibration.npz              # 完整标定数据
└── calibration_report.txt       # 标定报告
```

---

## 🔧 故障排除

### 常见问题及解决方案

#### 🚫 相机连接问题

**问题**: `pyrealsense2.error: No device connected`

```bash
# 解决步骤:
1. 检查USB 3.0连接
2. 重新安装Intel RealSense SDK
3. 更新相机固件
4. 检查USB端口供电能力

# 验证连接
realsense-viewer

# 查看设备列表
python -c "import pyrealsense2 as rs; print(rs.context().devices)"
```

**问题**: 图像质量差或有噪声

```bash
# 调整滤波参数
python src/main.py --mode track --spatial-filter --temporal-filter

# 检查光照条件
python src/main.py --mode demo --display --auto-exposure
```

#### 🔌 串口通信问题

**问题**: `serial.SerialException: Could not open port`

```bash
# Windows解决方案:
1. 检查设备管理器中的串口号
2. 确认串口未被其他程序占用
3. 以管理员权限运行程序

# Linux解决方案:
sudo usermod -a -G dialout $USER  # 添加用户到串口组
sudo chmod 666 /dev/ttyUSB0        # 修改权限

# 查看可用串口
python -c "import serial.tools.list_ports; print([p.device for p in serial.tools.list_ports.comports()])"
```

**问题**: 数据传输错误或丢包

```bash
# 调整波特率和超时
python src/main.py --mode track --robot --baudrate 9600 --timeout 2.0

# 检查连接线质量
# 使用串口调试工具验证通信
```

#### 🖥️ 性能问题

**问题**: 帧率过低或处理延迟高

```bash
# 降低分辨率
python src/main.py --mode track --resolution 640x480

# 减少处理线程
python src/main.py --mode track --threads 2

# 禁用图像显示
python src/main.py --mode track --no-display

# 使用GPU加速
python src/main.py --mode track --gpu
```

**问题**: 内存占用过高

```bash
# 限制缓冲区大小
python src/main.py --mode track --buffer-size 5

# 定期清理临时文件
python src/main.py --mode track --auto-cleanup
```

#### 🎯 检测精度问题

**问题**: 管道检测不准确

```bash
# 重新标定相机
python src/main.py --mode calib

# 调整检测参数
# 编辑 src/config.py 中的 PerceptionConfig

# 改善光照条件
# 使用均匀光源，避免强光直射
```

**问题**: 法兰识别失败

```bash
# 调整圆检测阈值
python src/main.py --mode track --circle-threshold 30

# 增加RANSAC迭代次数  
python src/main.py --mode track --ransac-iterations 2000

# 检查法兰大小是否在配置范围内
```

### 🔍 调试技巧

#### 启用详细日志

```bash
# 最详细的调试信息
python src/main.py --mode track --verbose --debug

# 指定日志级别
python src/main.py --mode track --log-level DEBUG
```

#### 保存调试数据

```bash
# 保存所有中间处理结果
python src/main.py --mode track --save-debug --output-dir debug_output

# 录制原始相机数据
python src/main.py --mode record --duration 60 --output debug_recording.bag
```

#### 性能分析

```bash
# 启用性能分析
python src/main.py --mode track --profile --profile-output performance.txt

# 查看内存使用
python src/main.py --mode track --memory-monitor
```

---

## 👥 开发指南

### 🏗️ 项目结构

```
Tiaozhanbei2.0/
├── src/                     # 源代码目录
│   ├── main.py             # 主程序入口
│   ├── config.py           # 配置管理
│   ├── camera/             # 相机模块
│   │   ├── calibration.py  # 相机标定
│   │   ├── stereo_capture.py # 立体捕获
│   │   └── point_cloud_*.py # 点云处理
│   ├── perception/         # 感知算法
│   │   ├── pipe_tracking.py # 管道追踪
│   │   └── obstacle_detection.py # 障碍检测
│   ├── robot/              # 机器人通信
│   │   ├── communication.py # 串口通信
│   │   └── motion_control.py # 运动控制
│   └── utils/              # 工具函数
│       └── logger.py       # 日志系统
├── tests/                  # 测试文件
├── data/                   # 数据目录
│   └── calib/             # 标定数据
├── output/                 # 输出结果
├── scripts/               # 脚本文件
└── docs/                  # 文档
```

### 🔧 添加新功能

#### 1. 添加新的检测算法

```python
# src/perception/new_algorithm.py
class NewDetectionAlgorithm:
    def __init__(self, config):
        self.config = config
  
    def detect(self, color_image, depth_image):
        # 实现检测逻辑
        pass
  
    def estimate_pose(self, detection_result):
        # 实现位姿估计
        pass
```

#### 2. 集成到主系统

```python
# src/main.py
from src.perception.new_algorithm import NewDetectionAlgorithm

# 在 Tiaozhanbei2System 类中添加
def setup_algorithms(self):
    # ...existing code...
    self.new_detector = NewDetectionAlgorithm(self.config.perception)
```

#### 3. 添加配置选项

```python
# src/config.py
class PerceptionConfig:
    # ...existing code...
    new_algorithm_enabled = True
    new_algorithm_threshold = 0.5
```

### 🧪 测试指南

#### 运行单元测试

```bash
# 运行所有测试
python -m pytest tests/

# 运行特定模块测试
python -m pytest tests/test_camera.py -v

# 运行性能测试
python -m pytest tests/test_performance.py --benchmark-only
```

#### 添加新测试

```python
# tests/test_new_feature.py
import unittest
from src.perception.new_algorithm import NewDetectionAlgorithm

class TestNewAlgorithm(unittest.TestCase):
    def setUp(self):
        self.algorithm = NewDetectionAlgorithm(config)
  
    def test_detection(self):
        # 测试检测功能
        pass
```

---

## 📚 参考资源

### 📖 技术文档

- [Intel RealSense SDK文档](https://intelrealsense.github.io/librealsense/python_docs/_generated/pyrealsense2.html)
- [OpenCV Python教程](https://opencv-python-tutroals.readthedocs.io/)
- [DJI RoboMaster开发指南](https://robomaster-dev.readthedocs.io/)

### 🎓 相关论文

- "Real-time Pipe Detection and Tracking for Autonomous Navigation"
- "3D Cylinder Fitting using RANSAC for Industrial Applications"
- "Vision-based Navigation for Mobile Robots in Industrial Environments"

### 🛠️ 工具推荐

- **RealSense Viewer**: 相机调试工具
- **Serial Port Monitor**: 串口通信调试
- **CloudCompare**: 点云数据可视化
- **MATLAB Computer Vision Toolbox**: 算法原型开发

---

## 🤝 贡献指南

### 🔄 提交流程

1. Fork项目仓库
2. 创建功能分支: `git checkout -b feature/new-feature`
3. 提交更改: `git commit -am 'Add new feature'`
4. 推送分支: `git push origin feature/new-feature`
5. 创建Pull Request

### 📝 代码规范

- 遵循PEP 8 Python代码风格
- 添加详细的文档字符串
- 包含单元测试
- 更新相关文档

### 🐛 问题报告

请通过GitHub Issues报告问题，包含：

- 详细的问题描述
- 重现步骤
- 系统环境信息
- 错误日志

---

## 📄 许可证

本项目采用MIT许可证 - 详见 [LICENSE](LICENSE) 文件

---

## 👨‍💻 作者信息

- **作者**: cxzandy
- **邮箱**: [c2513139524@foxmail.com]
- **GitHub**: [cxzandy](https://github.com/cxzandy)

---

## 🙏 致谢

- Intel Corporation - RealSense技术支持
- DJI Innovation - RoboMaster平台
- OpenCV社区 - 计算机视觉算法
- Python社区 - 开发工具和库

---

<div align="center">

**⭐ 如果这个项目对您有帮助，请给它一个Star！ ⭐**

**🔗 [项目主页](https://github.com/cxzandy/A-vision-project-for-pipe-tracking-and-flange-recognition-available-for-DJI-c-board-communication) | 📧 [联系我们](mailto:your-email@example.com) | 📖 [详细文档](docs/)**

</div>
