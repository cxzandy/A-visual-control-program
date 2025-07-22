# Tiaozhanbei2.0 - 管道追踪与法兰识别系统

<div align="center">

![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)
![OpenCV](https://img.shields.io/badge/OpenCV-4.5+-green.svg)
![RealSense](https://img.shields.io/badge/Intel-RealSense-lightblue.svg)
![Flask](https://img.shields.io/badge/Flask-Web-orange.svg)
![Status](https://img.shields.io/badge/Status-Ready-brightgreen.svg)

**基于Intel RealSense D455的实时管道追踪与法兰识别系统**

[快速开始](#-快速开始) • [Web界面](#-web控制界面) • [命令行使用](#-命令行使用) • [项目结构](#-项目结构)

</div>

---

## 📋 项目概述

Tiaozhanbei2.0是一个专为工业管道机器人设计的计算机视觉系统，具备：
- **四象限管道检测** - 高精度管道追踪和轴线拟合
- **实时深度感知** - 基于Intel RealSense D455的3D视觉
- **Web控制界面** - 现代化Web界面，支持实时监控和参数调节
- **机器人通信** - 支持DJI RoboMaster C板串口通信
- **多模式运行** - 演示、标定、追踪、测试四种工作模式

---

## � 快速开始

### 1. 环境安装

```bash
# 克隆项目
git clone https://github.com/cxzandy/A-visual-control-program.git
cd A-visual-control-program

# 创建conda环境
conda create -n tiao python=3.8
conda activate tiao

# 安装依赖
pip install -r requirements.txt
```

### 2. 硬件连接

- 连接Intel RealSense D455相机到USB 3.0端口
- 连接DJI C板到串口（可选，/dev/ttyUSB0）

### 3. 运行测试

```bash
# 激活环境
conda activate tiao

# 验证系统配置
python -m src.main --config-check

# 运行演示模式
python -m src.main --mode demo
```

### 4. Web界面快速体验

```bash
# 启动Web界面
./start_web.sh

# 浏览器访问
# http://localhost:5000
```

---

## 🌐 Web控制界面

### 启动Web服务

```bash
# 方式1：使用启动脚本
./start_web.sh

# 方式2：直接运行
conda run -n tiao python web/web_simple.py

# 方式3：演示模式（自动打开浏览器）
./demo_web.sh
```

### Web界面功能

- 📊 **实时监控** - 查看系统状态和参数
- 🎛️ **参数调节** - 在线调整检测阈值
- 📸 **图像预览** - 实时查看处理结果
- 🔄 **模式切换** - 快速切换不同工作模式
- 📝 **日志查看** - 实时查看系统日志

详细说明请参考：[Web界面使用指南](web/WEB_GUIDE.md)

---

## 📁 项目结构

```
A-visual-control-program/
├── 🎯 核心系统
│   ├── src/                    # 源代码目录
│   │   ├── main.py            # 主程序入口
│   │   ├── config.py          # 系统配置
│   │   ├── camera/            # 相机模块
│   │   ├── perception/        # 感知模块（管道检测）
│   │   ├── robot/             # 机器人通信
│   │   └── utils/             # 工具模块
│   │
├── 🌐 Web控制界面
│   ├── web/                   # Web界面目录
│   │   ├── web_simple.py      # Flask服务器
│   │   ├── templates/         # HTML模板
│   │   └── README.md          # Web使用说明
│   ├── start_web.sh          # Web启动脚本
│   └── demo_web.sh           # Web演示脚本
│   │
├── 🧪 测试和脚本
│   ├── tests/                 # 单元测试
│   │   └── test_quadrant_detection.py  # 四象限检测测试
│   └── scripts/               # 运行脚本
│   │
├── 📊 数据和输出
│   ├── data/calib/           # 标定数据
│   └── output/               # 输出目录
│       ├── images/           # 保存的图像
│       └── logs/             # 日志文件
│   │
└── 📚 文档
    ├── README.md             # 项目说明（本文件）
    ├── docs/                 # 详细文档
    └── requirements.txt      # Python依赖
```

---

## 🎮 命令行使用

### 基本语法

```bash
conda run -n tiao python -m src.main [OPTIONS]
```

### 运行模式

#### 1. 演示模式 (推荐新手使用)
```bash
# 基本演示
python -m src.main --mode demo

# 演示模式 + 图像显示
python -m src.main --mode demo --display

# 演示模式 + 结果保存
python -m src.main --mode demo --display --save
```

#### 2. 实时追踪模式
```bash
# 实时管道追踪
python -m src.main --mode track --display

# 追踪 + 保存结果
python -m src.main --mode track --display --save

# 追踪 + 详细输出
python -m src.main --mode track --display --verbose
```

#### 3. 相机标定模式
```bash
# 相机标定
python -m src.main --mode calib --display

# 标定 + 保存标定文件
python -m src.main --mode calib --display --save
```

#### 4. 系统测试模式
```bash
# 完整系统测试
python -m src.main --mode test --verbose

# 测试 + 显示结果
python -m src.main --mode test --display --verbose
```

### 命令行参数详解

| 参数 | 简写 | 说明 | 示例 |
|------|------|------|------|
| `--mode` | `-m` | 运行模式 | `--mode track` |
| `--display` | `-d` | 启用图像显示 | `--display` |
| `--save` | `-s` | 保存处理结果 | `--save` |
| `--verbose` | `-v` | 详细输出日志 | `--verbose` |
| `--config-check` | `-c` | 仅检查配置 | `--config-check` |

### 常用命令组合

```bash
# 🔍 快速功能验证
python -m src.main --mode demo

# 🎯 实时追踪 + 可视化
python -m src.main --mode track --display

# 🐛 调试模式
python -m src.main --mode track --display --verbose

# 📸 相机标定
python -m src.main --mode calib --display --save

# ✅ 系统全面测试
python -m src.main --mode test --display --verbose --save

# 🔧 配置检查
python -m src.main --config-check
```

### 快速测试脚本

```bash
# 测试四象限管道检测
python tests/test_quadrant_detection.py

# 运行所有测试
python -m pytest tests/ -v
```

### 🌐 Web控制界面

除了命令行操作，系统还提供了友好的Web控制界面：

#### 启动Web界面

```bash
# 方法1：使用启动脚本 (推荐)
./start_web.sh

# 方法2：使用演示脚本
./demo_web.sh

# 方法3：直接运行
conda run -n tiao python web/web_simple.py
```

#### Web界面功能

- **🎮 图形化控制** - 点击按钮启动/停止系统
- **📊 实时状态监控** - 显示FPS、检测结果等统计信息
- **📱 响应式设计** - 支持手机、平板访问
- **🖼️ 图像显示** - 实时显示四象限管道检测结果
- **📝 日志记录** - 实时显示系统运行日志

#### 访问地址

- **本地访问**: http://localhost:5000
- **局域网访问**: http://[您的IP地址]:5000

#### Web界面操作

1. **选择运行模式** - 演示、追踪、标定、测试
2. **启动系统** - 点击"🚀 启动系统"按钮
3. **查看状态** - 监控相机状态、FPS、检测结果
4. **观看图像** - 实时查看管道检测可视化
5. **停止系统** - 点击"⏹️ 停止系统"按钮

---

## 🛠 硬件配置

### 必需硬件

#### Intel RealSense D455 深度相机
- **连接**: USB 3.0接口
- **分辨率**: 640x480 @ 30fps (系统自动适配)
- **深度范围**: 0.2m - 10m

#### DJI RoboMaster C板 (可选)
- **连接**: 串口 /dev/ttyUSB0
- **波特率**: 115200
- **通信协议**: UART

### 系统要求

- **操作系统**: Ubuntu 18.04+, Windows 10+, macOS 10.15+
- **Python**: 3.8 或更高版本
- **内存**: 最少8GB RAM (推荐16GB)
- **USB**: USB 3.0接口 (用于RealSense连接)

---

## 📊 系统状态说明

### 启动时状态检查

```
验证系统配置...
✅ 配置验证通过

🚀 启动 Tiaozhanbei2.0 系统 - 模式: demo
正在初始化硬件组件...
正在尝试连接到RealSense相机...
成功连接到RealSense相机。
RealSense相机已启动: 640x480 @ 30fps
✅ 相机连接成功
串口连接错误: [Errno 2] No such file or directory: '/dev/ttyUSB0'
⚠️  机器人通信连接失败 (串口不存在是正常的)
✅ 系统初始化完成
```

### 运行时状态显示

```
==================================================
Tiaozhanbei2.0 系统状态
==================================================
相机连接: ✓
机器人连接: ✗ (可选)
标定加载: ✗ (首次运行为空)
处理帧数: 152
处理FPS: 28.50
错误计数: 0
==================================================
```

### 可视化窗口内容

运行 `--display` 参数时会显示：

- **四象限检测结果** - 不同颜色显示各象限管道线条
- **管道轴线拟合** - 黄色线条显示拟合的管道中心线
- **象限分割线** - 白色线条分割四个检测区域
- **检测状态信息** - 显示检测到的象限数量和FPS
- **实时统计** - 帧数、处理速度等信息

---

## 🔧 故障排除

### 常见问题

#### 1. ImportError: cannot import name 'PointCloudGenerator'
```bash
# 原因：缺少点云生成器类
# 解决：系统已修复，重新运行即可
python -m src.main --mode demo
```

#### 2. 相机连接失败
```bash
# 检查USB连接
lsusb | grep Intel
# 应显示: Bus xxx Device xxx: Intel Corp. RealSense Camera

# 重新插拔USB连接
# 或尝试其他USB 3.0端口
```

#### 3. 深度值验证失败
```bash
# 错误：depth_scale 超出有效范围
# 原因：配置范围过严
# 解决：系统已修复深度值验证范围
```

#### 4. FPS显示为0.0
```bash
# 原因：FPS计算逻辑错误
# 解决：系统已修复FPS计算
# 正常FPS应在20-30之间
```

#### 5. 窗口标题显示乱码
```bash
# 原因：中文标题在某些系统显示为"????"
# 解决：系统已改为英文标题
```

#### 6. 串口连接失败 (可忽略)
```bash
# 错误：/dev/ttyUSB0: No such file or directory
# 说明：机器人通信为可选功能，不影响视觉系统运行
# 如需连接：请确保DJI C板正确连接到USB串口
```

### 系统依赖检查

```bash
# 检查Python版本
python --version  # 应为3.8+

# 检查conda环境
conda info --envs  # 确认tiao环境存在

# 检查关键包
pip list | grep -E "(opencv|realsense|numpy)"
```

### 日志查看

```bash
# 详细日志输出
python -m src.main --mode demo --verbose

# 日志文件位置
ls output/logs/
```

### 性能优化建议

1. **使用USB 3.0** - 确保相机连接到USB 3.0端口
2. **关闭不必要程序** - 释放CPU和内存资源
3. **调整分辨率** - 系统自动适配最佳分辨率
4. **GPU加速** - 使用NVIDIA GPU可提升处理速度

---

## 📁 输出文件说明

### 目录结构

```
output/
├── images/          # 保存的图像文件 (使用--save参数)
├── logs/            # 系统日志文件
└── point_clouds/    # 点云数据文件 (如果生成)
```

### 保存的文件类型

- **图像文件**: `tracking_YYYYMMDD_HHMMSS.jpg`
- **日志文件**: `tiaozhanbei2_YYYYMMDD.log`
- **配置文件**: `d455_intrinsics.npz` (相机标定结果)

---

## 🎯 快速验证

### 30秒快速测试

```bash
# 1. 激活环境
conda activate tiao

# 2. 连接相机 (RealSense D455)

# 3. 运行测试
python test_pipe_tracking.py

# 4. 查看结果
# 应显示：✅ 四象限管道检测测试完成!
```

### 完整功能测试

```bash
# 运行演示模式
python -m src.main --mode demo --display

# 应该看到：
# - 系统状态正常
# - 相机连接成功
# - FPS显示正常 (20-30)
# - 可视化窗口正常显示
```

---

## 🤝 技术支持

### 系统特性

- ✅ **四象限管道检测** - 高精度管道识别和追踪
- ✅ **实时可视化** - 多窗口实时图像显示
- ✅ **自动适配** - 相机分辨率和配置自动适配
- ✅ **错误恢复** - 完善的异常处理和资源管理
- ✅ **性能监控** - 实时FPS和系统状态监控

### 版本信息

- **当前版本**: Tiaozhanbei2.0
- **最后更新**: 2025年7月22日
- **Python版本**: 3.8.20
- **主要依赖**: OpenCV 4.5+, pyrealsense2, NumPy

### 联系支持

如遇问题请检查：
1. 硬件连接是否正确
2. 环境配置是否完整  
3. 运行命令是否正确
4. 查看详细日志输出 (`--verbose`)

---

**📝 README 更新日期**: 2025年7月22日  
**🚀 项目状态**: 系统完全可用，所有主要功能已修复并测试通过
