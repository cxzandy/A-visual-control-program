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
    ControlConfig, PredictionConfig,
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
from control.turn_control import TurnControlManager
from utils.logger import setup_logger
from utils.display import DisplayManager
from utils.keyboard_control import KeyboardController

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
        self.turn_controller = None
        
        # 控制组件
        self.keyboard_controller = None
        
        # 系统状态
        self.system_status = {
            "camera_connected": False,
            "robot_connected": False,
            "calibration_loaded": False,
            "processing_fps": 0.0,
            "total_frames": 0,
            "error_count": 0,
            "control_mode": "auto",
            "turn_direction": "straight",
            "turn_confidence": 0.0,
            "keyboard_control_enabled": False,
            "last_keyboard_command": None
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
            if CameraConfig.CAMERA_TYPE == "usb":
                # 使用USB摄像头
                import cv2
                test_cap = cv2.VideoCapture(CameraConfig.USB_CAMERA_INDEX)
                if test_cap.isOpened():
                    test_cap.release()
                    # 这里需要创建USB摄像头类，暂时使用RealSense类作为占位符
                    self.camera = RealSenseCapture()  # TODO: 替换为USB摄像头类
                    self.system_status["camera_connected"] = True
                    self.logger.info("USB摄像头连接成功")
                else:
                    self.logger.error("USB摄像头连接失败")
                    return False
            else:
                # 使用RealSense摄像头
                if check_realsense_connection():
                    self.camera = RealSenseCapture()
                    self.system_status["camera_connected"] = True
                    self.logger.info("RealSense相机连接成功")
                else:
                    self.logger.error("RealSense相机连接失败")
                    return False
        except Exception as e:
            self.logger.error(f"相机初始化失败: {e}")
            return False
            
        # 2. 初始化机器人通信（如果启用）
        if RobotConfig.ROBOT_ENABLED:
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
                self.robot = None
        else:
            self.logger.info("机器人功能已禁用（配置设置）")
            self.robot = None
            
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
                depth_threshold=PerceptionConfig.OBSTACLE_DEPTH_THRESHOLD * 1000,  # 转换为mm
                center_region_width=PerceptionConfig.OBSTACLE_CENTER_REGION_WIDTH,
                critical_distance=PerceptionConfig.OBSTACLE_CRITICAL_DISTANCE * 1000,  # 转换为mm
                warning_distance=PerceptionConfig.OBSTACLE_WARNING_DISTANCE * 1000  # 转换为mm
            )
            
            # 管道追踪器
            self.pipe_tracker = PipeTracker(
                depth_threshold=PerceptionConfig.PIPE_DEPTH_THRESHOLD,
                camera_intrinsics=self._load_camera_intrinsics()
            )
            
            # 转向控制管理器
            self.turn_controller = TurnControlManager()
            
            # 键盘控制器
            self.keyboard_controller = KeyboardController(
                robot_comm=self.robot,
                logger=self.logger
            )
            
            # 设置键盘命令回调
            self.keyboard_controller.set_command_callback(self._on_keyboard_command)
            
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
            
        # 启用键盘控制
        if ControlConfig.KEYBOARD_CONTROL_ENABLED:
            self.enable_keyboard_control()
            self.logger.info("键盘控制已启用 - WASD控制, Q退出, M切换模式")
            
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
                obstacle_analysis = self.obstacle_detector.analyze_obstacle_threat(depth_frame, obstacle_mask)
                
                # 管道追踪（包含方向预测）
                result = self.pipe_tracker.track(color_frame, depth_frame)
                if isinstance(result, tuple) and len(result) >= 3:
                    line_params, global_axis, vis_image = result[:3]
                    prediction_info = result[3] if len(result) > 3 else None
                else:
                    line_params, global_axis, vis_image, prediction_info = None, None, color_frame, None
                
                # 处理结果
                self._process_tracking_results(
                    obstacle_mask, line_params, global_axis, vis_image, prediction_info, obstacle_analysis
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
            # 禁用键盘控制
            self.disable_keyboard_control()
            
        self.logger.info(f"追踪模式结束，共处理 {frame_count} 帧")
        return True
        
    def _process_tracking_results(self, obstacle_mask, line_params, global_axis, vis_image, prediction_info=None, obstacle_analysis=None):
        """处理追踪结果（集成转向控制）"""
        try:
            # 转向检测和控制决策
            turn_result = self.turn_controller.process_frame(
                vis_image, line_params, global_axis
            )
            
            # 更新系统状态
            self.system_status["turn_direction"] = turn_result["direction"]
            self.system_status["turn_confidence"] = turn_result["confidence"]
            self.system_status["control_mode"] = self.turn_controller.control_mode
            
            # 发送控制命令到机器人
            if self.robot and self.system_status["robot_connected"]:
                self._send_robot_commands(obstacle_mask, turn_result, obstacle_analysis)
                
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
                    "Frames": self.system_status["total_frames"],
                    "Mode": self.system_status["control_mode"].upper(),
                    "Turn": f"{turn_result['direction']} ({turn_result['confidence']:.2f})",
                    "Keyboard": "ON" if self.system_status["keyboard_control_enabled"] else "OFF"
                }
                
                # 添加最后键盘命令
                if self.system_status["last_keyboard_command"]:
                    status_info["LastKey"] = self.system_status["last_keyboard_command"]
                
                # 添加转向控制统计
                turn_stats = self.turn_controller.get_statistics()
                if turn_stats:
                    status_info.update({
                        "Left": f"{turn_stats['left_count']}",
                        "Right": f"{turn_stats['right_count']}",
                        "Straight": f"{turn_stats['straight_count']}"
                    })
                
                # 添加键盘控制统计
                if self.keyboard_controller:
                    kb_stats = self.keyboard_controller.get_statistics()
                    if kb_stats["total_commands"] > 0:
                        status_info["KB_Cmds"] = str(kb_stats["total_commands"])
                
                display_image = add_status_overlay(display_image, status_info, start_y=60)
                
                # 显示图像
                key = self.display.show_image("Turn Control Tracking", display_image)
                if key == ord('q'):
                    self.running = False
                elif key == ord('m'):
                    # 切换控制模式
                    new_mode = "manual" if self.turn_controller.control_mode == "auto" else "auto"
                    self.turn_controller.set_control_mode(new_mode)
                    self.logger.info(f"控制模式切换为: {new_mode}")
                    
            # 保存结果
            if RunModeConfig.SAVE_RESULTS:
                self._save_results(vis_image, obstacle_mask, line_params, turn_result, obstacle_analysis)
                
        except Exception as e:
            self.logger.error(f"处理追踪结果失败: {e}")
            
    def _send_robot_commands(self, obstacle_mask, turn_result, obstacle_analysis=None):
        """向机器人发送控制命令（基于转向控制和智能避障）"""
        try:
            import numpy as np
            
            # 智能安全检查：障碍物威胁分析
            if obstacle_analysis:
                threat_level = obstacle_analysis["threat_level"]
                min_distance = obstacle_analysis["min_distance"]
                
                if threat_level == "critical":
                    self.robot.send(RobotConfig.COMMANDS["OBSTACLE_AVOID"])  # 发送05
                    self.logger.error(f"紧急避障！检测到严重威胁，距离: {min_distance:.0f}mm (05)")
                    return
                elif threat_level == "warning":
                    self.robot.send(RobotConfig.COMMANDS["OBSTACLE_AVOID"])  # 发送05
                    self.logger.warning(f"警告避障！检测到障碍物威胁，距离: {min_distance:.0f}mm (05)")
                    return
                elif threat_level == "caution":
                    self.logger.info(f"注意：前方有障碍物，距离: {min_distance:.0f}mm，继续监控")
            
            # 备用安全检查：基于面积的传统检测
            elif np.sum(obstacle_mask > 0) > PerceptionConfig.OBSTACLE_MIN_AREA:
                self.robot.send(RobotConfig.COMMANDS["OBSTACLE_AVOID"])  # 发送05
                self.logger.warning("检测到障碍物（传统检测），发送避障命令 (05)")
                return
                
            # 根据控制模式发送命令
            if self.turn_controller.control_mode == "manual":
                # 手动模式：执行手动命令
                manual_cmd = self.turn_controller.get_manual_command()
                if manual_cmd:
                    if manual_cmd == "left":
                        self.robot.send(RobotConfig.COMMANDS["TURN_LEFT"])  # 发送03
                        self.logger.info("执行手动左转命令 (03)")
                    elif manual_cmd == "right":
                        self.robot.send(RobotConfig.COMMANDS["TURN_RIGHT"])  # 发送04
                        self.logger.info("执行手动右转命令 (04)")
                    elif manual_cmd == "forward":
                        self.robot.send(RobotConfig.COMMANDS["MOVE_FORWARD"])  # 发送01
                        self.logger.info("执行手动前进命令 (01)")
                    elif manual_cmd == "backward":
                        self.robot.send(RobotConfig.COMMANDS["MOVE_BACKWARD"])  # 发送02
                        self.logger.info("执行手动后退命令 (02)")
                    elif manual_cmd == "stop":
                        self.robot.send(RobotConfig.COMMANDS["STOP"])
                        self.logger.info("执行手动停止命令")
                else:
                    # 无手动命令时保持当前状态
                    pass
            else:
                # 自动模式：根据转向检测结果发送命令
                direction = turn_result["direction"]
                confidence = turn_result["confidence"]
                
                if confidence > ControlConfig.MIN_CONFIDENCE_THRESHOLD:
                    if direction == "left":
                        self.robot.send(RobotConfig.COMMANDS["TURN_LEFT"])  # 发送03
                        self.logger.info(f"自动左转，置信度: {confidence:.2f} (03)")
                    elif direction == "right":
                        self.robot.send(RobotConfig.COMMANDS["TURN_RIGHT"])  # 发送04
                        self.logger.info(f"自动右转，置信度: {confidence:.2f} (04)")
                    else:
                        self.robot.send(RobotConfig.COMMANDS["MOVE_FORWARD"])  # 发送01
                        self.logger.debug("直线前进 (01)")
                else:
                    # 置信度不足，保持当前状态或搜索
                    self.robot.send(RobotConfig.COMMANDS["STOP"])
                    self.logger.debug("置信度不足，发送停止命令")
                
        except Exception as e:
            self.logger.error(f"发送机器人命令失败: {e}")
            
    def _save_results(self, vis_image, obstacle_mask, line_params, turn_result, obstacle_analysis=None):
        """保存处理结果（包含转向控制和障碍物检测信息）"""
        try:
            import cv2
            import json
            from datetime import datetime
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            
            if vis_image is not None:
                # 在可视化图像上绘制障碍物信息
                if obstacle_analysis:
                    vis_image = self.obstacle_detector.draw_obstacles(vis_image, obstacle_mask, obstacle_analysis)
                    
                image_path = os.path.join(
                    OutputConfig.IMAGES_DIR,
                    f"turn_tracking_{timestamp}.jpg"
                )
                cv2.imwrite(image_path, vis_image)
                
            # 保存转向控制和障碍物检测信息
            if turn_result or obstacle_analysis:
                json_path = os.path.join(
                    OutputConfig.LOGS_DIR,
                    f"detection_results_{timestamp}.json"
                )
                
                save_data = {
                    "timestamp": timestamp,
                    "turn_result": turn_result,
                    "obstacle_analysis": obstacle_analysis,
                    "control_mode": self.turn_controller.control_mode,
                    "statistics": self.turn_controller.get_statistics()
                }
                
                with open(json_path, 'w') as f:
                    json.dump(save_data, f, indent=2, default=str)
                    
        except Exception as e:
            self.logger.error(f"保存结果失败: {e}")
            
    def set_control_mode(self, mode: str) -> bool:
        """设置控制模式（供Web界面调用）"""
        try:
            if self.turn_controller:
                self.turn_controller.set_control_mode(mode)
                self.system_status["control_mode"] = mode
                self.logger.info(f"控制模式已切换为: {mode}")
                return True
            return False
        except Exception as e:
            self.logger.error(f"设置控制模式失败: {e}")
            return False
            
    def send_manual_command(self, command: str) -> bool:
        """发送手动控制命令（供Web界面调用）"""
        try:
            if self.turn_controller and self.turn_controller.control_mode == "manual":
                self.turn_controller.set_manual_command(command)
                self.logger.info(f"接收到手动命令: {command}")
                return True
            return False
        except Exception as e:
            self.logger.error(f"发送手动命令失败: {e}")
            return False
            
    def get_system_state(self) -> Dict[str, Any]:
        """获取系统状态（供Web界面调用）"""
        try:
            state = self.system_status.copy()
            if self.turn_controller:
                state.update({
                    "turn_statistics": self.turn_controller.get_statistics(),
                    "manual_command": self.turn_controller.manual_command
                })
            return state
        except Exception as e:
            self.logger.error(f"获取系统状态失败: {e}")
            return {}
            
    def _on_keyboard_command(self, command: str):
        """键盘命令回调函数"""
        try:
            self.system_status["last_keyboard_command"] = command
            self.logger.info(f"键盘控制命令: {command}")
            
            # 如果是手动模式，直接执行键盘命令
            if (self.turn_controller and 
                self.turn_controller.control_mode == "manual"):
                
                # 将机器人命令转换为手动控制命令
                manual_cmd = self._robot_cmd_to_manual_cmd(command)
                if manual_cmd:
                    self.turn_controller.set_manual_command(manual_cmd)
                    
        except Exception as e:
            self.logger.error(f"处理键盘命令失败: {e}")
            
    def _robot_cmd_to_manual_cmd(self, robot_cmd: str) -> Optional[str]:
        """将机器人命令转换为手动控制命令"""
        cmd_mapping = {
            RobotConfig.COMMANDS["MOVE_FORWARD"]: "forward",
            RobotConfig.COMMANDS["MOVE_BACKWARD"]: "backward", 
            RobotConfig.COMMANDS["TURN_LEFT"]: "left",
            RobotConfig.COMMANDS["TURN_RIGHT"]: "right",
            RobotConfig.COMMANDS["STOP"]: "stop"
        }
        return cmd_mapping.get(robot_cmd)
        
    def enable_keyboard_control(self):
        """启用键盘控制"""
        try:
            if self.keyboard_controller and ControlConfig.KEYBOARD_CONTROL_ENABLED:
                self.keyboard_controller.start_keyboard_control()
                self.system_status["keyboard_control_enabled"] = True
                self.logger.info("键盘控制已启用")
                return True
            return False
        except Exception as e:
            self.logger.error(f"启用键盘控制失败: {e}")
            return False
            
    def disable_keyboard_control(self):
        """禁用键盘控制"""
        try:
            if self.keyboard_controller:
                self.keyboard_controller.stop_keyboard_control()
                self.system_status["keyboard_control_enabled"] = False
                self.logger.info("键盘控制已禁用")
        except Exception as e:
            self.logger.error(f"禁用键盘控制失败: {e}")
            
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
                    result = self.pipe_tracker.track(color_frame, depth_frame)
                    
                    # 安全解包结果
                    if isinstance(result, tuple) and len(result) >= 3:
                        line_params, _, vis_image = result[:3]
                    else:
                        line_params, vis_image = None, color_frame
                    
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
            # 禁用键盘控制
            self.disable_keyboard_control()
            
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