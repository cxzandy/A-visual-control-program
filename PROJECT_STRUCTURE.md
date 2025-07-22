# 📁 项目结构整理说明

## 🎯 整理目标

本次整理的目标是让项目结构更加清晰和专业，删除临时文件，将功能相关的文件归类到合适的目录中。

## 📂 新的目录结构

```
A-visual-control-program/
├── 🎯 核心系统模块
│   └── src/                          # 源代码目录
│       ├── main.py                   # 主程序入口
│       ├── config.py                 # 系统配置
│       ├── camera/                   # 相机模块
│       │   ├── stereo_capture.py     # RealSense相机控制
│       │   ├── calibration.py        # 相机标定
│       │   ├── depth_estimation.py   # 深度估计
│       │   └── point_cloud_*.py      # 点云处理
│       ├── perception/               # 感知算法模块
│       │   ├── pipe_tracking.py      # 四象限管道检测
│       │   └── obstacle_detection.py # 障碍物检测
│       ├── robot/                    # 机器人通信模块
│       │   ├── communication.py      # 串口通信
│       │   └── motion_control.py     # 运动控制
│       └── utils/                    # 工具模块
│           ├── logger.py             # 日志系统
│           └── display.py            # 显示工具
│
├── 🌐 Web控制界面
│   ├── web/                          # Web界面目录
│   │   ├── web_simple.py             # Flask Web服务器
│   │   ├── templates/                # HTML模板
│   │   │   └── index.html            # 响应式Web页面
│   │   ├── static/                   # 静态文件（预留）
│   │   ├── README.md                 # Web模块说明
│   │   └── WEB_GUIDE.md              # 详细使用指南
│   ├── start_web.sh                  # Web服务启动脚本
│   └── demo_web.sh                   # Web演示脚本
│
├── 🧪 测试模块
│   ├── tests/                        # 单元测试目录
│   │   ├── test_camera.py            # 相机模块测试
│   │   ├── test_perception.py        # 感知模块测试
│   │   ├── test_robot.py             # 机器人模块测试
│   │   └── test_quadrant_detection.py # 四象限检测专项测试
│   └── scripts/                      # 运行脚本
│       ├── run_demo.sh               # 演示脚本
│       └── run_jetson.sh             # Jetson部署脚本
│
├── 📊 数据和输出
│   ├── data/                         # 输入数据
│   │   └── calib/                    # 标定数据和图像
│   └── output/                       # 输出目录
│       ├── images/                   # 保存的处理结果图像
│       ├── logs/                     # 系统日志文件
│       └── point_clouds/             # 点云数据（如有）
│
└── 📚 文档和配置
    ├── README.md                     # 项目主说明文档
    ├── README_EN.md                  # 英文说明文档
    ├── requirements.txt              # Python依赖包列表
    └── docs/                         # 详细文档目录
        ├── HARDWARE_CONFIG.md        # 硬件配置说明
        ├── JETSON_DEPLOYMENT.md      # Jetson部署指南
        └── QUICK_START_CN.md         # 快速开始指南
```

## 🔄 主要变更

### ✅ 已完成的整理

1. **Web模块整理**
   - 创建了专门的 `web/` 目录
   - 移动了 `web_simple.py` 到 `web/` 目录
   - 移动了 `templates/` 到 `web/` 目录
   - 移动了 `WEB_GUIDE.md` 到 `web/` 目录
   - 创建了 `web/README.md` 说明文件

2. **删除冗余文件**
   - 删除了 `web_interface.py`（保留简化版 `web_simple.py`）
   - 删除了 `WEB_FILES.md`（内容合并到主README）
   - 删除了 `test_pipe_tracking.py`（集成到正式测试中）

3. **测试模块整理**
   - 创建了 `tests/test_quadrant_detection.py` 正式测试文件
   - 测试文件具有完整的文档和错误处理

4. **更新配置文件**
   - 更新了启动脚本路径
   - 更新了README中的项目结构说明
   - 修正了Web服务器的模板路径

### 🎯 整理效果

#### Before (整理前)
```
- 根目录混乱，Web文件散落各处
- 临时测试文件和正式代码混合
- 文档文件分散，缺乏归类
- 路径引用不统一
```

#### After (整理后)
```
✅ 清晰的模块划分
✅ Web相关文件统一管理
✅ 测试文件规范化
✅ 文档结构清晰
✅ 路径引用统一
```

## 🚀 使用方式

### 命令行方式
```bash
# 系统核心功能
python -m src.main --mode demo
python -m src.main --mode track --display

# 测试功能
python tests/test_quadrant_detection.py
```

### Web界面方式
```bash
# 启动Web界面
./start_web.sh

# 演示模式
./demo_web.sh

# 直接运行
conda run -n tiao python web/web_simple.py
```

## 💡 优势总结

1. **更专业的结构** - 符合软件工程最佳实践
2. **更好的维护性** - 功能模块清晰分离
3. **更容易扩展** - 新功能有明确的归属目录
4. **更简洁的根目录** - 减少文件混乱
5. **更清晰的职责** - 每个目录都有明确的用途

现在项目结构更加清晰和专业，既保持了功能的完整性，又提高了代码的可维护性！
