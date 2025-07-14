# 🚀 Tiaozhanbei2.0 快速入门指南

## ⚡ 5分钟快速开始

### 1. 📦 安装依赖
```bash
# 标准平台安装
pip install pyrealsense2 opencv-python numpy pyserial

# Jetson AGX Xavier优化安装
sudo apt install python3-opencv python3-numpy python3-serial
pip install pyrealsense2

# 验证安装
python -c "import pyrealsense2, cv2, numpy, serial; print('✅ 所有依赖安装成功!')"
```

### 2. 🔧 硬件连接
- **RealSense D455**: USB 3.0 连接到电脑/Jetson
- **DJI C板**: 
  - PC平台: 通过USB转TTL连接
  - Jetson平台: 直接UART连接 (推荐)

### 3. ▶️ 立即运行
```bash
# 下载项目
git clone https://github.com/cxzandy/A-vision-project-for-pipe-tracking-and-flange-recognition-available-for-DJI-c-board-communication.git
cd A-vision-project-for-pipe-tracking-and-flange-recognition-available-for-DJI-c-board-communication

# 快速演示 (无需硬件)
python src/main.py --mode demo --display

# 实时追踪 (需要RealSense)
python src/main.py --mode track --display --save

# 🚀 Jetson AGX Xavier 一键启动 (推荐)
bash scripts/run_jetson.sh track
```

## 🎯 核心功能演示

### 🎥 演示模式 - 无需硬件
```bash
# 基础演示
python src/main.py --mode demo

# 显示处理过程
python src/main.py --mode demo --display --verbose
```

### 📐 相机标定 - 提高精度
```bash
# 1. 拍摄棋盘格图片到 data/calib/ 
# 2. 运行标定
python src/main.py --mode calib
```

### 🎯 实时追踪 - 核心功能
```bash
# 仅追踪显示
python src/main.py --mode track --display

# 追踪 + 保存结果
python src/main.py --mode track --display --save

# 追踪 + 机器人控制
python src/main.py --mode track --robot --port COM3
```

## 🛠️ 一键测试脚本

### Windows用户
```powershell
# PowerShell (推荐)
.\scripts\run_demo.ps1

# 批处理
scripts\run_demo.bat
```

### Linux/Mac用户
```bash
bash scripts/run_demo.sh
```

## 📊 输出结果说明

运行后会在以下位置生成文件：
- **日志**: `output/logs/tiaozhanbei_*.log`
- **图像**: `output/images/tracked_*.jpg`
- **点云**: `output/images/point_clouds/*.ply`

## ⚠️ 常见问题

### 🔴 相机连接失败
```bash
# 检查RealSense连接
realsense-viewer

# 重新安装驱动
# Windows: 下载Intel RealSense SDK 2.0
# Linux: sudo apt install librealsense2-utils
```

### 🔴 模块导入错误
```bash
# 检查Python路径
echo $PYTHONPATH

# 从项目根目录运行
cd /path/to/Tiaozhanbei2.0
python src/main.py --mode demo
```

### 🔴 串口访问被拒绝
```bash
# Linux添加用户到串口组
sudo usermod -a -G dialout $USER

# Windows确认串口号和权限
# 设备管理器 -> 端口(COM和LPT)
```

## 🎮 参数配置

### 📝 修改配置文件 `src/config.py`
```python
# 相机分辨率
CameraConfig.width = 1280
CameraConfig.height = 720

# 串口设置  
RobotConfig.port = "COM3"  # Windows
RobotConfig.port = "/dev/ttyUSB0"  # Linux

# 检测参数
PerceptionConfig.pipe_radius_range = (0.05, 0.5)  # 管道半径范围
PerceptionConfig.flange_radius_range = (0.1, 0.8)  # 法兰半径范围
```

## 📞 获取帮助

- **📚 完整文档**: [README.md](../README.md)
- **🐛 问题报告**: [GitHub Issues](https://github.com/cxzandy/A-vision-project-for-pipe-tracking-and-flange-recognition-available-for-DJI-c-board-communication/issues)
- **💬 使用交流**: 在Issues中提问

---

**🎉 恭喜！您已经完成了快速入门。现在可以开始探索更多高级功能了！**

## 🚀 Jetson AGX Xavier 专用指南

### 🎯 一键启动 (推荐)
```bash
# 实时追踪模式 (自动性能优化)
bash scripts/run_jetson.sh track

# 演示模式
bash scripts/run_jetson.sh demo

# 相机标定
bash scripts/run_jetson.sh calib

# 系统测试
bash scripts/run_jetson.sh test
```

### ⚙️ Jetson优势特性
- ✅ **自动性能优化**: 自动设置nvpmodel和jetson_clocks
- ✅ **直连通信**: UART直连DJI C板，无需USB转TTL
- ✅ **GPU加速**: OpenCV CUDA支持，性能提升3-5倍
- ✅ **低功耗**: 18-25W功耗，适合移动机器人
- ✅ **实时监控**: tegrastats系统状态监控
- ✅ **温度保护**: 自动温度监控和性能调节

### 🔧 Jetson硬件连接
```
Jetson AGX Xavier 40-Pin GPIO:
Pin 6  (GND)      → DJI C板 GND
Pin 8  (UART1_TX) → DJI C板 RX (PA10)  
Pin 10 (UART1_RX) → DJI C板 TX (PA9)

USB 3.0 Type-A → RealSense D455
```

### ⚡ 性能对比
| 平台 | 处理速度 | 功耗 | GPU加速 | 通信延迟 |
|------|---------|------|---------|----------|
| PC (i7) | ~30fps | 65W+ | 可选 | ~5ms |
| Jetson AGX Xavier | ~22fps | 25W | ✅ | ~2ms |
| Jetson Nano | ~15fps | 10W | ✅ | ~2ms |
