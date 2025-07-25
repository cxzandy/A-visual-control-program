# 转向控制功能使用说明

## 概述

Tiaozhanbei2.0 现在支持左右转向检测功能，并提供Web控制台进行自动/手动模式切换。

## 新增功能

### 1. 转向控制系统
- **左右转向检测**: 基于管道线条的方向分析
- **置信度评估**: 对检测结果进行可靠性评分
- **统计跟踪**: 记录左转、右转、直行的次数
- **模式切换**: 支持自动模式和手动模式

### 2. 键盘控制系统
- **WASD控制**: W-前进(01), S-后退(02), A-左转(03), D-右转(04)
- **实时响应**: 键盘输入直接转换为下位机命令
- **安全机制**: 支持紧急停止和超时保护
- **命令统计**: 记录键盘控制使用情况

### 3. Web控制界面
- **实时监控**: 显示当前转向状态和置信度
- **模式选择**: 一键切换自动/手动控制模式
- **手动控制**: 在手动模式下提供方向按钮控制
- **状态显示**: 实时显示系统运行状态和统计信息

## 文件结构

```
src/
├── control/                    # 新增：控制模块
│   ├── __init__.py
│   └── turn_control.py        # 转向控制管理器
├── utils/                     # 更新：工具模块
│   ├── keyboard_control.py    # 新增：键盘控制器
│   └── display.py
├── config.py                  # 更新：添加控制配置和机器人命令
└── main.py                    # 更新：集成转向控制和键盘控制

web/
├── templates/
│   └── index.html            # 更新：增强控制界面
└── web_simple.py             # 更新：新增控制API

# 新增测试和启动脚本
test_turn_control.py          # 转向控制功能测试
test_keyboard_control.py      # 新增：键盘控制测试
run_with_web.py              # 带Web界面的完整启动脚本
```

## 配置参数

### ControlConfig 类
```python
class ControlConfig:
    # 转向检测参数
    MIN_CONFIDENCE_THRESHOLD = 0.6  # 最小置信度阈值
    DIRECTION_SMOOTHING = 3          # 方向平滑帧数
    
    # 控制模式
    DEFAULT_MODE = "auto"            # 默认控制模式
    MANUAL_COMMAND_TIMEOUT = 2.0     # 手动命令超时时间
```

### PredictionConfig 类
```python
class PredictionConfig:
    # 线条分析参数
    ANGLE_THRESHOLD = 15.0           # 角度阈值（度）
    MIN_LINE_LENGTH = 50             # 最小线条长度
    DIRECTION_HISTORY_SIZE = 10      # 方向历史大小
```

## 使用方法

### 1. 基础功能测试
```bash
python test_turn_control.py
# 选择 1 进行基础功能测试
```

### 2. 键盘控制测试
```bash
python test_keyboard_control.py
# 选择测试模式：
#   1 - 命令映射测试
#   2 - 配置值测试  
#   3 - 完整集成测试
# 
# 键盘控制说明：
#   W键 - 前进 (发送01到下位机)
#   S键 - 后退 (发送02到下位机)
#   A键 - 左转 (发送03到下位机)
#   D键 - 右转 (发送04到下位机)
#   空格 - 停止
#   Q键 - 退出
```

### 3. 摄像头实时测试
```bash
python test_turn_control.py
# 选择 2 进行摄像头实时测试
# 按键控制：
#   q - 退出
#   m - 切换自动/手动模式
#   w/a/s/d - 手动模式下的方向控制（同时发送机器人命令）
```

### 4. 完整系统运行
```bash
python run_with_web.py
# 启动完整系统，包含Web界面
# 访问 http://localhost:5000 进行Web控制
```

### 5. 仅Web界面
```bash
cd web
python web_simple.py
# 访问 http://localhost:5000
```

## Web界面功能

### 控制面板
1. **模式选择**
   - 自动模式：系统自动检测转向并控制
   - 手动模式：通过Web按钮手动控制

2. **手动控制按钮** (仅手动模式可用)
   - ⬅️ 左转
   - ➡️ 右转
   - ⬆️ 前进
   - ⏹️ 停止

3. **状态显示**
   - 当前转向方向
   - 检测置信度
   - 控制模式
   - 转向统计

### API 端点

- `GET /api/status` - 获取系统状态
- `POST /api/control_mode` - 设置控制模式
- `POST /api/manual_command` - 发送手动控制命令

### 机器人命令码

系统向下位机发送的命令码：
- **01** - 前进命令
- **02** - 后退命令  
- **03** - 左转命令
- **04** - 右转命令
- **05** - 避障动作命令

## 核心算法

### 转向检测算法
1. **线条方向分析**：计算检测到的线条的角度
2. **方向分类**：根据角度范围判断左转、右转或直行
3. **置信度计算**：基于线条质量和一致性评分
4. **平滑处理**：使用历史数据平滑检测结果

### 控制逻辑
- **自动模式**：根据检测结果自动执行转向
- **手动模式**：响应用户的手动命令
- **安全检查**：优先处理障碍物检测和紧急停止

## 集成方式

### 在主系统中使用
```python
from control.turn_control import TurnControlManager

# 创建转向控制管理器
turn_controller = TurnControlManager()

# 在主循环中处理
result = turn_controller.process_frame(color_frame, line_params, global_axis)

# 根据结果发送控制命令
if result['confidence'] > 0.6:
    if result['direction'] == 'left':
        robot.send("turn_left")
    elif result['direction'] == 'right':
        robot.send("turn_right")
```

### Web界面集成
```javascript
// 切换控制模式
function setControlMode(mode) {
    fetch('/api/control_mode', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({mode: mode})
    });
}

// 发送手动命令
function sendManualCommand(command) {
    fetch('/api/manual_command', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({command: command})
    });
}
```

## 注意事项

1. **Jetson部署**：确保在Jetson设备上正确配置了摄像头
2. **依赖库**：需要OpenCV、NumPy等库支持
3. **性能优化**：转向检测算法已优化，处理时间通常<10ms
4. **安全考虑**：始终优先处理障碍物检测和紧急停止

## 故障排除

### 常见问题
1. **导入错误**：确保Python路径正确设置
2. **摄像头连接**：检查USB摄像头或RealSense连接
3. **Web服务器启动失败**：检查端口5000是否被占用
4. **控制命令无响应**：确保在手动模式下发送命令

### 调试方法
- 查看控制台输出的日志信息
- 使用测试脚本验证各组件功能
- 检查Web浏览器的开发者工具中的网络请求

## 更新日志

- **v2.1.0**: 添加转向控制功能
- **v2.1.1**: 增强Web界面控制
- **v2.1.2**: 优化检测算法和用户体验
