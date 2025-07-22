#!/usr/bin/env python3
"""
Tiaozhanbei2.0 主程序入口
管道追踪与法兰识别系统 - DJI RoboMaster C板通信版本

功能:
- 相机标定与连接检查
- 实时管道追踪与法兰识别  
- 障碍物检测
- 机器人通信控制
- 点云处理与可视化

作者: cxzandy
版本: 2.0.0
"""

import sys
import os
import argparse
import time
import signal
import traceback
from typing import Optional, Dict, Any

# 添加src目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# 导入配置
from config import (
    CameraConfig, RobotConfig, PerceptionConfig, 
    RunModeConfig, LogConfig, SafetyConfig, OutputConfig,
    validate_config, print_config_summary
)

# 导入各个模块
from camera.calibration import calibrate_camera, check_realsense_connection
from camera.stereo_capture import RealSenseCapture
from camera.depth_estimation import DepthEstimator
from camera.point_cloud_generator import PointCloudGenerator
from robot.communication import RoboMasterCSerial
from perception.obstacle_detection import ObstacleDetector
from perception.pipe_tracking import PipeTracker
from utils.logger import setup_logger
from utils.display import DisplayManager

class Tiaozhanbei2System:
    """挑战杯2.0 系统主类"""
    
    def __init__(self):
        """初始化系统"""
        self.logger = setup_logger(__name__)
        self.running = False
        self.emergency_stop = False
        
        # 显示管理器
        self.display = DisplayManager()
        
        # 硬件组件
        self.camera = None
        self.robot = None
        self.depth_estimator = None
        self.point_cloud_generator = None
        
        # 算法组件
        self.obstacle_detector = None
        self.pipe_tracker = None
        
        # 系统状态
        self.system_status = {
            "camera_connected": False,
            "robot_connected": False,
            "calibration_loaded": False,
            "processing_fps": 0.0,
            "total_frames": 0,
            "error_count": 0
        }
        
        # 注册信号处理器
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
        
    def _signal_handler(self, signum, frame):
        """信号处理器 - 优雅退出"""
        self.logger.info(f"接收到信号 {signum}，正在安全退出...")
        self.emergency_stop = True
        self.running = False
        
    def initialize_hardware(self) -> bool:
        """初始化硬件组件"""
        self.logger.info("正在初始化硬件组件...")
        
        # 1. 检查相机连接
        try:
            if check_realsense_connection():
                self.camera = RealSenseCapture()
                self.system_status["camera_connected"] = True
                self.logger.info("相机连接成功")
            else:
                self.logger.error("相机连接失败")
                return False
        except Exception as e:
            self.logger.error(f"相机初始化失败: {e}")
            return False
            
        # 2. 初始化机器人通信
        try:
            self.robot = RoboMasterCSerial(
                port=RobotConfig.SERIAL_PORT,
                baudrate=RobotConfig.BAUD_RATE,
                timeout=RobotConfig.TIMEOUT
            )
            self.system_status["robot_connected"] = True
            self.logger.info("机器人通信连接成功")
        except Exception as e:
            self.logger.warning(f"机器人通信连接失败: {e}")
            self.robot = None  # 允许无机器人模式运行
            
        # 3. 初始化深度估计器
        try:
            self.depth_estimator = DepthEstimator(camera_instance=self.camera)
            self.logger.info("深度估计器初始化成功")
        except Exception as e:
            self.logger.error(f"深度估计器初始化失败: {e}")
            return False
            
        # 4. 初始化点云生成器
        try:
            self.point_cloud_generator = PointCloudGenerator()
            self.logger.info("点云生成器初始化成功")
        except Exception as e:
            self.logger.warning(f"点云生成器初始化失败: {e}")
            
        return True
        
    def initialize_algorithms(self) -> bool:
        """初始化算法组件"""
        self.logger.info("正在初始化算法组件...")
        
        try:
            # 障碍物检测器
            self.obstacle_detector = ObstacleDetector(
                depth_threshold=PerceptionConfig.OBSTACLE_DEPTH_THRESHOLD
            )
            
            # 管道追踪器
            self.pipe_tracker = PipeTracker(
                depth_threshold=PerceptionConfig.PIPE_DEPTH_THRESHOLD,
                camera_intrinsics=self._load_camera_intrinsics()
            )
            
            self.logger.info("算法组件初始化成功")
            return True
            
        except Exception as e:
            self.logger.error(f"算法组件初始化失败: {e}")
            return False
            
    def _load_camera_intrinsics(self) -> Optional[list]:
        """加载相机内参"""
        try:
            import numpy as np
            if os.path.exists(CameraConfig.CALIBRATION_CONFIG_PATH):
                data = np.load(CameraConfig.CALIBRATION_CONFIG_PATH)
                mtx = data['mtx']
                # 返回 [fx, fy, cx, cy] 格式
                return [mtx[0,0], mtx[1,1], mtx[0,2], mtx[1,2]]
            else:
                self.logger.warning("未找到相机标定文件，使用默认内参")
                # 默认 RealSense D455 内参估计值
                return [600.0, 600.0, 640.0, 360.0]
        except Exception as e:
            self.logger.error(f"加载相机内参失败: {e}")
            return None
            
    def run_calibration_mode(self) -> bool:
        """运行相机标定模式"""
        self.logger.info("开始相机标定模式...")
        
        try:
            camera_matrix, distortion_coeffs = calibrate_camera(
                images_dir=CameraConfig.CALIBRATION_DATA_DIR,
                chessboard_size=CameraConfig.CHESSBOARD_SIZE,
                square_size=CameraConfig.SQUARE_SIZE_METERS,
                save_path=CameraConfig.CALIBRATION_CONFIG_PATH
            )
            
            if camera_matrix is not None:
                self.system_status["calibration_loaded"] = True
                self.logger.info("相机标定完成")
                return True
            else:
                self.logger.error("相机标定失败")
                return False
                
        except Exception as e:
            self.logger.error(f"标定模式执行失败: {e}")
            return False
            
    def run_tracking_mode(self) -> bool:
        """运行实时追踪模式"""
        self.logger.info("开始实时追踪模式...")
        
        if not self.system_status["camera_connected"]:
            self.logger.error("相机未连接，无法运行追踪模式")
            return False
            
        self.running = True
        frame_count = 0
        start_time = time.time()
        
        try:
            while self.running and not self.emergency_stop:
                # 获取图像帧
                color_frame, depth_frame = self.camera.get_frames()
                if color_frame is None or depth_frame is None:
                    self.logger.warning("获取图像帧失败")
                    continue
                    
                frame_start_time = time.time()
                
                # 障碍物检测
                obstacle_mask = self.obstacle_detector.detect(depth_frame)
                
                # 管道追踪
                line_params, global_axis, vis_image = self.pipe_tracker.track(
                    color_frame, depth_frame
                )
                
                # 处理结果
                self._process_tracking_results(
                    obstacle_mask, line_params, global_axis, vis_image
                )
                
                # 更新统计信息
                frame_count += 1
                self.system_status["total_frames"] = frame_count
                
                # 计算FPS
                frame_time = time.time() - frame_start_time
                self.system_status["processing_fps"] = 1.0 / frame_time if frame_time > 0 else 0
                
                # 每100帧输出一次状态
                if frame_count % 100 == 0:
                    elapsed_time = time.time() - start_time
                    avg_fps = frame_count / elapsed_time
                    self.logger.info(f"处理帧数: {frame_count}, 平均FPS: {avg_fps:.2f}")
                    
                # 安全检查
                if not self._safety_check():
                    break
                    
        except Exception as e:
            self.logger.error(f"追踪模式执行失败: {e}")
            self.logger.error(traceback.format_exc())
            return False
            
        finally:
            self.running = False
            
        self.logger.info(f"追踪模式结束，共处理 {frame_count} 帧")
        return True
        
    def _process_tracking_results(self, obstacle_mask, line_params, global_axis, vis_image):
        """处理追踪结果"""
        try:
            # 发送控制命令到机器人
            if self.robot and self.system_status["robot_connected"]:
                self._send_robot_commands(obstacle_mask, line_params, global_axis)
                
            # 显示结果
            if RunModeConfig.DISPLAY_ENABLED and vis_image is not None:
                # 添加状态信息到图像
                from utils.display import add_fps_overlay, add_status_overlay
                
                # 添加FPS显示
                display_image = add_fps_overlay(vis_image, self.system_status["processing_fps"])
                
                # 添加系统状态
                status_info = {
                    "Camera": "OK" if self.system_status["camera_connected"] else "ERROR",
                    "Robot": "OK" if self.system_status["robot_connected"] else "DISCONNECTED",
                    "Frames": self.system_status["total_frames"]
                }
                display_image = add_status_overlay(display_image, status_info, start_y=60)
                
                # 显示图像
                key = self.display.show_image("Pipe Tracking", display_image)
                if key == ord('q'):
                    self.running = False
                    
            # 保存结果
            if RunModeConfig.SAVE_RESULTS:
                self._save_results(vis_image, obstacle_mask, line_params)
                
        except Exception as e:
            self.logger.error(f"处理追踪结果失败: {e}")
            
    def _send_robot_commands(self, obstacle_mask, line_params, global_axis):
        """向机器人发送控制命令"""
        try:
            import numpy as np
            
            # 简单的控制逻辑示例
            if np.sum(obstacle_mask > 0) > PerceptionConfig.OBSTACLE_MIN_AREA:
                # 检测到障碍物，发送停止命令
                self.robot.send(RobotConfig.COMMANDS["STOP"])
                self.logger.warning("检测到障碍物，发送停止命令")
            elif line_params and any(p is not None for p in line_params):
                # 检测到管道，发送跟踪命令
                self.robot.send("track_pipe")
                self.logger.debug("发送管道跟踪命令")
            else:
                # 无目标，发送搜索命令
                self.robot.send("search")
                self.logger.debug("发送搜索命令")
                
        except Exception as e:
            self.logger.error(f"发送机器人命令失败: {e}")
            
    def _save_results(self, vis_image, obstacle_mask, line_params):
        """保存处理结果"""
        try:
            import cv2
            from datetime import datetime
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            
            if vis_image is not None:
                image_path = os.path.join(
                    OutputConfig.IMAGES_DIR,
                    f"tracking_{timestamp}.jpg"
                )
                cv2.imwrite(image_path, vis_image)
                
        except Exception as e:
            self.logger.error(f"保存结果失败: {e}")
            
    def _safety_check(self) -> bool:
        """安全检查"""
        try:
            # 检查运行时间
            if SafetyConfig.MAX_OPERATION_TIME > 0:
                if time.time() - self.start_time > SafetyConfig.MAX_OPERATION_TIME:
                    self.logger.warning("达到最大运行时间，系统安全退出")
                    return False
                    
            # 检查错误计数
            if self.system_status["error_count"] > 10:
                self.logger.warning("错误次数过多，系统安全退出")
                return False
                
            # 检查紧急停止
            if self.emergency_stop:
                self.logger.warning("紧急停止激活")
                return False
                
            return True
            
        except Exception as e:
            self.logger.error(f"安全检查失败: {e}")
            return False
            
    def run_demo_mode(self) -> bool:
        """运行演示模式"""
        self.logger.info("开始演示模式...")
        
        try:
            # 1. 检查系统状态
            self.print_system_status()
            
            # 2. 简单的功能演示
            if self.system_status["camera_connected"]:
                self.logger.info("相机功能正常")
                
            if self.system_status["robot_connected"]:
                self.robot.send(RobotConfig.COMMANDS["LED_TEST"])
                response = self.robot.recv(timeout_sec=2)
                self.logger.info(f"机器人响应: {response}")
                
            # 3. 运行短时间的追踪
            self.logger.info("运行5秒追踪演示...")
            demo_end_time = time.time() + 5
            self.running = True
            
            frame_count = 0
            demo_start_time = time.time()
            
            while time.time() < demo_end_time and self.running:
                frame_start_time = time.time()
                
                color_frame, depth_frame = self.camera.get_frames()
                if color_frame is not None and depth_frame is not None:
                    # 简单处理
                    obstacle_mask = self.obstacle_detector.detect(depth_frame)
                    line_params, _, vis_image = self.pipe_tracker.track(color_frame, depth_frame)
                    
                    # 计算FPS
                    frame_count += 1
                    elapsed_time = time.time() - demo_start_time
                    current_fps = frame_count / elapsed_time if elapsed_time > 0 else 0.0
                    
                    if vis_image is not None and RunModeConfig.DISPLAY_ENABLED:
                        from utils.display import add_fps_overlay, add_status_overlay
                        
                        # 添加FPS显示到演示图像
                        display_image = add_fps_overlay(vis_image, current_fps)
                        
                        # 添加演示状态信息
                        demo_status = {
                            "Mode": "DEMO",
                            "Frame": frame_count,
                            "Time": f"{elapsed_time:.1f}s"
                        }
                        display_image = add_status_overlay(display_image, demo_status, start_y=60)
                        
                        # 显示图像
                        key = self.display.show_image("Demo Mode", display_image)
                        if key == ord('q'):
                            break
                            
            self.running = False
            self.logger.info("演示模式完成")
            return True
            
        except Exception as e:
            self.logger.error(f"演示模式执行失败: {e}")
            return False
            
    def print_system_status(self):
        """打印系统状态"""
        print("\n" + "="*50)
        print("Tiaozhanbei2.0 系统状态")
        print("="*50)
        print(f"相机连接: {'✓' if self.system_status['camera_connected'] else '✗'}")
        print(f"机器人连接: {'✓' if self.system_status['robot_connected'] else '✗'}")
        print(f"标定加载: {'✓' if self.system_status['calibration_loaded'] else '✗'}")
        print(f"处理帧数: {self.system_status['total_frames']}")
        print(f"处理FPS: {self.system_status['processing_fps']:.2f}")
        print(f"错误计数: {self.system_status['error_count']}")
        print("="*50)
        
    def cleanup(self):
        """清理资源"""
        self.logger.info("正在清理系统资源...")
        
        try:
            if self.camera:
                self.camera.stop()
                
            if self.robot:
                self.robot.close()
                
            # 关闭显示窗口
            self.display.close_window()
            
            self.logger.info("资源清理完成")
            
        except Exception as e:
            self.logger.error(f"资源清理失败: {e}")

def create_argument_parser():
    """创建命令行参数解析器"""
    parser = argparse.ArgumentParser(
        description="Tiaozhanbei2.0 管道追踪与法兰识别系统",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
运行模式说明:
  demo     - 演示模式，展示系统基本功能
  calib    - 相机标定模式
  track    - 实时追踪模式
  test     - 测试模式

使用示例:
  python main.py --mode demo
  python main.py --mode calib
  python main.py --mode track --display
  python main.py --mode test --verbose
        """
    )
    
    parser.add_argument(
        "--mode", "-m",
        choices=[RunModeConfig.DEMO_MODE, RunModeConfig.CALIBRATION_MODE, 
                RunModeConfig.TRACKING_MODE, RunModeConfig.TEST_MODE],
        default=RunModeConfig.DEFAULT_MODE,
        help="运行模式 (默认: demo)"
    )
    
    parser.add_argument(
        "--display", "-d",
        action="store_true",
        help="启用图像显示"
    )
    
    parser.add_argument(
        "--save", "-s",
        action="store_true", 
        help="保存处理结果"
    )
    
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="详细输出"
    )
    
    parser.add_argument(
        "--config-check", "-c",
        action="store_true",
        help="仅检查配置并退出"
    )
    
    return parser

def main():
    """主函数"""
    # 解析命令行参数
    parser = create_argument_parser()
    args = parser.parse_args()
    
    # 更新配置
    if args.display:
        RunModeConfig.DISPLAY_ENABLED = True
    if args.save:
        RunModeConfig.SAVE_RESULTS = True
    if args.verbose:
        LogConfig.LOG_LEVEL = "DEBUG"
        RunModeConfig.VERBOSE_OUTPUT = True
    
    # 验证配置
    print("验证系统配置...")
    config_errors = validate_config()
    if config_errors:
        print("❌ 配置验证失败:")
        for error in config_errors:
            print(f"  - {error}")
        return 1
    else:
        print("✅ 配置验证通过")
        
    if args.config_check:
        print_config_summary()
        return 0
    
    # 创建系统实例
    system = None
    try:
        print(f"\n🚀 启动 Tiaozhanbei2.0 系统 - 模式: {args.mode}")
        system = Tiaozhanbei2System()
        system.start_time = time.time()
        
        # 初始化硬件
        if not system.initialize_hardware():
            print("❌ 硬件初始化失败")
            return 1
            
        # 初始化算法
        if not system.initialize_algorithms():
            print("❌ 算法初始化失败")
            return 1
            
        print("✅ 系统初始化完成")
        
        # 根据模式运行
        success = False
        if args.mode == RunModeConfig.DEMO_MODE:
            success = system.run_demo_mode()
        elif args.mode == RunModeConfig.CALIBRATION_MODE:
            success = system.run_calibration_mode()
        elif args.mode == RunModeConfig.TRACKING_MODE:
            success = system.run_tracking_mode()
        elif args.mode == RunModeConfig.TEST_MODE:
            # 运行所有模式的简化版本
            success = (system.run_demo_mode() and 
                      system.run_calibration_mode())
        
        if success:
            print(f"✅ {args.mode} 模式执行成功")
            return 0
        else:
            print(f"❌ {args.mode} 模式执行失败")
            return 1
            
    except KeyboardInterrupt:
        print("\n⚠️  用户中断程序")
        return 0
    except Exception as e:
        print(f"❌ 系统运行失败: {e}")
        if args.verbose:
            traceback.print_exc()
        return 1
    finally:
        if system:
            system.cleanup()
        print("👋 系统已退出")

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)