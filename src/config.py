"""
Tiaozhanbei2.0 项目全局配置文件
包含相机、机器人通信、感知算法等所有模块的配置参数
"""

import os
import numpy as np

# ========================= 项目基础配置 =========================
PROJECT_NAME = "Tiaozhanbei2.0"
VERSION = "2.1.0"
AUTHOR = "cxzandy"

# 项目根目录
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(PROJECT_ROOT, "data")
OUTPUT_DIR = os.path.join(PROJECT_ROOT, "output")
DOCS_DIR = os.path.join(PROJECT_ROOT, "docs")

# ========================= 相机配置 =========================
class CameraConfig:
    # RealSense D455 相机配置
    CAMERA_TYPE = "realsense_d455"
    
    # 图像分辨率
    COLOR_WIDTH = 1280
    COLOR_HEIGHT = 720
    DEPTH_WIDTH = 1280  
    DEPTH_HEIGHT = 720
    
    # 帧率
    FPS = 30
    
    # 标定相关
    CALIBRATION_DATA_DIR = os.path.join(DATA_DIR, "calib")
    CALIBRATION_CONFIG_PATH = os.path.join(CALIBRATION_DATA_DIR, "config", "d455_intrinsics.npz")
    
    # 棋盘格标定参数
    CHESSBOARD_SIZE = (11, 8)  # 内部角点数量 (列, 行)
    SQUARE_SIZE_METERS = 0.02  # 方格实际边长 (米)
    MIN_CALIBRATION_IMAGES = 5  # 最少需要的有效标定图片数
    
    # 深度相关
    DEPTH_SCALE = 0.001  # RealSense深度比例 (mm to m)
    MIN_DEPTH = 0.1  # 最小深度 (米)
    MAX_DEPTH = 10.0  # 最大深度 (米)
    
    # 点云相关
    POINT_CLOUD_DIR = os.path.join(DATA_DIR, "point_clouds")
    VOXEL_SIZE = 0.01  # 点云下采样体素大小 (米)

# ========================= 机器人通信配置 =========================
class RobotConfig:
    # DJI RoboMaster C板通信配置
    
    # 默认串口配置
    SERIAL_PORT = "COM3"  # 默认值，运行时会根据平台调整
    BAUD_RATE = 115200
    TIMEOUT = 0.5  # 串口超时 (秒)
    
    # 平台特定配置（运行时设置）
    ENABLE_HARDWARE_FLOW_CONTROL = False
    BUFFER_SIZE = 1024
    READ_TIMEOUT = 0.5
    
    # 通信协议
    COMMAND_TERMINATOR = "\n"
    ENCODING = "utf-8"
    
    # 重试机制
    MAX_RETRY_ATTEMPTS = 3
    RETRY_DELAY = 1.0  # 秒
    
    # 常用命令
    COMMANDS = {
        "LED_TEST": "1",
        "MOTOR_TEST": "2", 
        "SENSOR_READ": "3",
        "STATUS_CHECK": "status",
        "RESET": "reset",
        "STOP": "stop"
    }

# ========================= 感知算法配置 =========================
class PerceptionConfig:
    # 障碍物检测
    OBSTACLE_DEPTH_THRESHOLD = 1.0  # 障碍物深度阈值 (米)
    OBSTACLE_MIN_AREA = 100  # 最小障碍物面积 (像素)
    
    # 管道追踪
    PIPE_DEPTH_THRESHOLD = 1.5  # 管道深度阈值 (米)
    PIPE_MIN_LENGTH = 50  # 最小管道长度 (像素)
    PIPE_MAX_GAP = 10  # 管道线段最大间隙 (像素)
    
    # 边缘检测
    CANNY_LOW_THRESHOLD = 50
    CANNY_HIGH_THRESHOLD = 150
    GAUSSIAN_BLUR_KERNEL = (5, 5)
    
    # 霍夫变换
    HOUGH_RHO = 1  # 距离分辨率
    HOUGH_THETA = np.pi / 180  # 角度分辨率
    HOUGH_THRESHOLD = 50  # 累加器阈值
    HOUGH_MIN_LINE_LENGTH = 30  # 最小线段长度
    HOUGH_MAX_LINE_GAP = 5  # 最大线段间隙
    
    # RANSAC 圆柱拟合
    RANSAC_SIGMA = 0.01  # RANSAC阈值
    RANSAC_MIN_RADIUS = 0.05  # 最小圆柱半径 (米)
    RANSAC_MAX_RADIUS = 0.5   # 最大圆柱半径 (米)
    RANSAC_SAMPLE_NUM = 3     # RANSAC采样点数
    RANSAC_ITERATIONS = 1000  # RANSAC迭代次数

# ========================= 方向预测配置 =========================
class PredictionConfig:
    # 历史数据
    HISTORY_SIZE = 15  # 历史轨迹点数量
    MIN_HISTORY_FOR_PREDICTION = 5  # 进行预测所需的最小历史点数
    
    # 预测参数
    PREDICTION_STEPS = 8  # 前瞻预测步数
    CONFIDENCE_THRESHOLD = 0.5  # 置信度阈值
    
    # 曲率分析
    CURVATURE_WINDOW = 3  # 曲率计算窗口大小
    CURVE_THRESHOLD = 0.1  # 弯曲检测阈值
    
    # 方向判断
    DIRECTION_ANGLE_THRESHOLD = 30  # 方向角度阈值 (度)
    MOVEMENT_THRESHOLD = 5.0  # 最小移动距离阈值 (像素)
    
    # 趋势分析
    TREND_WINDOW = 5  # 趋势分析窗口
    TREND_THRESHOLD = 0.3  # 趋势变化阈值
    
    # 可视化
    PREDICTION_ARROW_LENGTH = 50  # 预测箭头长度 (像素)
    PREDICTION_COLORS = {
        'left': (0, 255, 255),    # 黄色
        'right': (0, 255, 255),   # 黄色
        'up': (255, 0, 255),      # 紫色
        'down': (255, 0, 255),    # 紫色
        'unknown': (128, 128, 128) # 灰色
    }

# ========================= 运行模式配置 =========================
class RunModeConfig:
    # 运行模式
    DEMO_MODE = "demo"           # 演示模式
    CALIBRATION_MODE = "calib"   # 标定模式  
    TRACKING_MODE = "track"      # 追踪模式
    TEST_MODE = "test"           # 测试模式
    
    # 默认运行模式
    DEFAULT_MODE = DEMO_MODE
    
    # 显示设置
    DISPLAY_ENABLED = True       # 是否显示图像
    SAVE_RESULTS = True          # 是否保存结果
    VERBOSE_OUTPUT = True        # 是否详细输出

# ========================= 日志配置 =========================
class LogConfig:
    # 日志级别
    LOG_LEVEL = "INFO"  # DEBUG, INFO, WARNING, ERROR, CRITICAL
    
    # 日志文件
    LOG_DIR = os.path.join(OUTPUT_DIR, "logs")
    LOG_FILE = os.path.join(LOG_DIR, f"{PROJECT_NAME}.log")
    
    # 日志格式
    LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    DATE_FORMAT = "%Y-%m-%d %H:%M:%S"
    
    # 日志轮转
    MAX_LOG_SIZE = 10 * 1024 * 1024  # 10MB
    BACKUP_COUNT = 5

# ========================= 输出配置 =========================
class OutputConfig:
    # 结果保存路径
    RESULTS_DIR = os.path.join(OUTPUT_DIR, "results")
    IMAGES_DIR = os.path.join(OUTPUT_DIR, "images")
    VIDEOS_DIR = os.path.join(OUTPUT_DIR, "videos")
    MODELS_DIR = os.path.join(OUTPUT_DIR, "models")
    
    # 文件格式
    IMAGE_FORMAT = "jpg"
    VIDEO_FORMAT = "mp4"
    POINT_CLOUD_FORMAT = "ply"
    
    # 质量设置
    IMAGE_QUALITY = 95  # JPEG质量 (0-100)
    VIDEO_FPS = 30      # 视频帧率

# ========================= 性能配置 =========================
class PerformanceConfig:
    # 多线程
    MAX_WORKERS = 4  # 最大工作线程数
    
    # 内存管理
    MAX_MEMORY_USAGE = 0.8  # 最大内存使用率
    GARBAGE_COLLECTION_THRESHOLD = 100  # 垃圾回收阈值
    
    # 处理优化
    USE_GPU = False  # 是否使用GPU加速
    BATCH_SIZE = 1   # 批处理大小

# ========================= 安全配置 =========================
class SafetyConfig:
    # 系统安全
    EMERGENCY_STOP_ENABLED = True
    MAX_OPERATION_TIME = 3600  # 最大运行时间 (秒)
    
    # 硬件保护
    MAX_CAMERA_FAILURE_COUNT = 5    # 最大相机失败次数
    MAX_ROBOT_TIMEOUT_COUNT = 3     # 最大机器人超时次数
    
    # 数据验证
    VALIDATE_INPUT_DATA = True      # 是否验证输入数据
    CHECK_DISK_SPACE = True         # 是否检查磁盘空间
    MIN_FREE_DISK_SPACE = 1024      # 最小空闲磁盘空间 (MB)

# ========================= 平台配置 =========================
class PlatformConfig:
    # 平台类型检测
    @staticmethod
    def detect_platform():
        """自动检测运行平台"""
        import platform
        import os
        
        # 检查是否是Jetson平台
        if os.path.exists('/proc/device-tree/model'):
            with open('/proc/device-tree/model', 'r') as f:
                model = f.read()
                if 'jetson' in model.lower():
                    if 'agx xavier' in model.lower():
                        return 'jetson_agx_xavier'
                    elif 'nano' in model.lower():
                        return 'jetson_nano'
                    elif 'tx2' in model.lower():
                        return 'jetson_tx2'
                    else:
                        return 'jetson_other'
        
        # 检查操作系统
        system = platform.system()
        if system == 'Windows':
            return 'windows'
        elif system == 'Darwin':
            return 'macos'
        elif system == 'Linux':
            return 'linux'
        else:
            return 'unknown'

# 实例化平台配置
platform_detector = PlatformConfig()
CURRENT_PLATFORM = platform_detector.detect_platform()

# ========================= Jetson AGX Xavier 优化配置 =========================
class JetsonConfig:
    # 硬件配置
    PLATFORM_NAME = "NVIDIA Jetson AGX Xavier"
    GPU_MEMORY_GB = 32
    CPU_CORES = 8
    
    # 性能模式 (nvpmodel)
    PERFORMANCE_MODES = {
        0: {"name": "MAXN", "power": 30, "cpu_cores": 8, "gpu_freq": "max"},
        1: {"name": "MODE_15W_6CORE", "power": 15, "cpu_cores": 6, "gpu_freq": "limited"},
        2: {"name": "MODE_15W_4CORE", "power": 15, "cpu_cores": 4, "gpu_freq": "limited"},
        3: {"name": "MODE_15W_2CORE", "power": 15, "cpu_cores": 2, "gpu_freq": "limited"},
        4: {"name": "MODE_10W", "power": 10, "cpu_cores": 4, "gpu_freq": "low"},
        5: {"name": "MODE_10W_DESKTOP", "power": 10, "cpu_cores": 8, "gpu_freq": "low"}
    }
    DEFAULT_PERFORMANCE_MODE = 0  # 最大性能模式
    
    # UART配置 (Jetson直连DJI C板)
    UART_DEVICE = "/dev/ttyTHS1"  # Jetson UART1接口
    UART_BAUDRATE = 115200
    UART_ENABLE_HARDWARE_FLOW_CONTROL = False
    
    # GPIO配置
    GPIO_UART_TX_PIN = 8   # Pin 8 (UART1_TXD)
    GPIO_UART_RX_PIN = 10  # Pin 10 (UART1_RXD)
    GPIO_GND_PIN = 6       # Pin 6 (GND)
    
    # CUDA配置
    CUDA_DEVICE_ID = 0
    ENABLE_CUDA_ACCELERATION = True
    CUDA_MEMORY_LIMIT_MB = 16384  # 16GB GPU内存限制
    
    # OpenCV优化
    OPENCV_NUM_THREADS = 4  # OpenCV线程数
    ENABLE_NEON_OPTIMIZATION = True  # ARM NEON指令集优化
    
    # 内存优化
    MAX_BUFFER_SIZE = 5  # 减少内存缓冲区
    ENABLE_MEMORY_POOL = True
    GC_THRESHOLD = 10  # 垃圾回收阈值
    
    # 温度监控
    THERMAL_ZONE_PATHS = [
        "/sys/devices/virtual/thermal/thermal_zone0/temp",
        "/sys/devices/virtual/thermal/thermal_zone1/temp"
    ]
    MAX_TEMPERATURE_CELSIUS = 85  # 最大工作温度
    TEMPERATURE_CHECK_INTERVAL = 30  # 温度检查间隔(秒)

# ========================= 配置验证函数 =========================
def validate_config():
    """验证配置参数的有效性"""
    errors = []
    
    # 检查目录是否存在，不存在则创建
    dirs_to_check = [
        DATA_DIR, OUTPUT_DIR, DOCS_DIR,
        CameraConfig.CALIBRATION_DATA_DIR,
        CameraConfig.POINT_CLOUD_DIR,
        LogConfig.LOG_DIR,
        OutputConfig.RESULTS_DIR,
        OutputConfig.IMAGES_DIR,
        OutputConfig.VIDEOS_DIR,
        OutputConfig.MODELS_DIR
    ]
    
    for dir_path in dirs_to_check:
        if not os.path.exists(dir_path):
            try:
                os.makedirs(dir_path, exist_ok=True)
                print(f"创建目录: {dir_path}")
            except Exception as e:
                errors.append(f"无法创建目录 {dir_path}: {e}")
    
    # 验证数值范围
    if not (0 < PerceptionConfig.OBSTACLE_DEPTH_THRESHOLD < 10):
        errors.append("障碍物深度阈值超出合理范围 (0-10米)")
    
    if not (1200 <= RobotConfig.BAUD_RATE <= 921600):
        errors.append("串口波特率超出合理范围")
    
    if not (0.0001 <= CameraConfig.DEPTH_SCALE <= 1.0):
        errors.append("深度比例超出合理范围")
    
    return errors

def print_config_summary():
    """打印配置摘要"""
    print(f"\n{PROJECT_NAME} v{VERSION} 配置摘要")
    print("=" * 50)
    print(f"项目根目录: {PROJECT_ROOT}")
    print(f"相机类型: {CameraConfig.CAMERA_TYPE}")
    print(f"图像分辨率: {CameraConfig.COLOR_WIDTH}x{CameraConfig.COLOR_HEIGHT}")
    print(f"串口配置: {RobotConfig.SERIAL_PORT} @ {RobotConfig.BAUD_RATE}")
    print(f"运行模式: {RunModeConfig.DEFAULT_MODE}")
    print(f"日志级别: {LogConfig.LOG_LEVEL}")
    print("=" * 50)

# ========================= 配置初始化和平台适配 =========================
def initialize_platform_config():
    """根据检测到的平台初始化配置"""
    platform = CURRENT_PLATFORM
    
    if platform == 'jetson_agx_xavier':
        # Jetson AGX Xavier 配置
        RobotConfig.SERIAL_PORT = JetsonConfig.UART_DEVICE
        RobotConfig.ENABLE_HARDWARE_FLOW_CONTROL = JetsonConfig.UART_ENABLE_HARDWARE_FLOW_CONTROL
        RobotConfig.BUFFER_SIZE = 4096
        RobotConfig.READ_TIMEOUT = 1.0
        
        # 相机配置优化 (针对Jetson AGX Xavier)
        CameraConfig.COLOR_WIDTH = 1280
        CameraConfig.COLOR_HEIGHT = 720  
        CameraConfig.FPS = 30
        
    elif platform in ['jetson_nano', 'jetson_tx2']:
        # 其他Jetson平台配置
        RobotConfig.SERIAL_PORT = "/dev/ttyTHS1"
        RobotConfig.ENABLE_HARDWARE_FLOW_CONTROL = False
        RobotConfig.BUFFER_SIZE = 2048
        RobotConfig.READ_TIMEOUT = 1.0
        
    elif platform == 'windows':
        # Windows平台配置
        RobotConfig.SERIAL_PORT = "COM3"
        RobotConfig.ENABLE_HARDWARE_FLOW_CONTROL = False
        RobotConfig.BUFFER_SIZE = 1024
        RobotConfig.READ_TIMEOUT = 0.5
        
    else:
        # Linux/macOS等其他平台
        RobotConfig.SERIAL_PORT = "/dev/ttyUSB0"
        RobotConfig.ENABLE_HARDWARE_FLOW_CONTROL = False
        RobotConfig.BUFFER_SIZE = 1024
        RobotConfig.READ_TIMEOUT = 0.5

def get_platform_info():
    """获取平台信息"""
    platform = PlatformConfig.CURRENT_PLATFORM
    info = {
        'platform': platform,
        'is_jetson': platform.startswith('jetson'),
        'uart_device': RobotConfig.SERIAL_PORT,
        'cuda_available': False,
        'opencv_cuda': False
    }
    
    # 检查CUDA支持
    try:
        import cv2
        info['opencv_cuda'] = cv2.cuda.getCudaEnabledDeviceCount() > 0
    except:
        pass
    
    # 检查Jetson专用功能
    if info['is_jetson']:
        import os
        info['tegrastats_available'] = os.path.exists('/usr/bin/tegrastats')
        info['nvpmodel_available'] = os.path.exists('/usr/sbin/nvpmodel')
        info['jetson_clocks_available'] = os.path.exists('/usr/bin/jetson_clocks')
    
    return info

# 执行平台配置初始化
initialize_platform_config()

def print_platform_config():
    """打印平台配置信息"""
    print("=" * 60)
    print("TIAOZHANBEI2.0 平台配置信息")
    print("=" * 60)
    
    platform_info = get_platform_info()
    print(f"检测到的平台: {platform_info['platform']}")
    print(f"是否为Jetson平台: {platform_info['is_jetson']}")
    print(f"串口设备: {platform_info['uart_device']}")
    print(f"OpenCV CUDA支持: {platform_info['opencv_cuda']}")
    
    if platform_info['is_jetson']:
        print(f"Tegrastats可用: {platform_info.get('tegrastats_available', False)}")
        print(f"NVPmodel可用: {platform_info.get('nvpmodel_available', False)}")
        print(f"Jetson Clocks可用: {platform_info.get('jetson_clocks_available', False)}")
        
        if PlatformConfig.CURRENT_PLATFORM == 'jetson_agx_xavier':
            print(f"性能模式: {JetsonConfig.DEFAULT_PERFORMANCE_MODE}")
            print(f"UART设备: {JetsonConfig.UART_DEVICE}")
            print(f"CUDA设备ID: {JetsonConfig.CUDA_DEVICE_ID}")
    
    print(f"相机分辨率: {CameraConfig.COLOR_WIDTH}x{CameraConfig.COLOR_HEIGHT}")
    
    # 显示平台特定的配置
    if platform_info['is_jetson']:
        print(f"处理线程数: 4 (Jetson优化)")
        print(f"GPU加速: {platform_info['opencv_cuda']}")
    else:
        print(f"处理线程数: 4 (默认)")
        print(f"GPU加速: {platform_info['opencv_cuda']}")
    
    print("=" * 60)

# ========================= 配置初始化 =========================
if __name__ == "__main__":
    # 验证配置
    config_errors = validate_config()
    if config_errors:
        print("配置验证失败:")
        for error in config_errors:
            print(f"  - {error}")
    else:
        print("配置验证通过！")
        print_config_summary()
        print_platform_config()