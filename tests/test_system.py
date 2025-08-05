#!/usr/bin/env python3
"""
系统集成测试
System Integration Test

统一测试入口，整合所有测试功能
包括：硬件测试、Web API测试、感知模块测试
"""

import sys
import os
import cv2
import numpy as np
import time
import traceback
from datetime import datetime

# 添加项目根目录到Python路径
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

def test_imports():
    """测试所有模块导入"""
    print("📦 测试模块导入...")
    
    modules_to_test = [
        ('src.config', 'CameraConfig'),
        ('src.camera.capture', 'RealSenseCapture'),
        ('src.camera.capture', 'USBCapture'),
        ('src.perception.pipe_tracking', 'PipeTracker'),
        ('src.perception.obstacle_detection', 'ObstacleDetector'),
        ('src.control.turn_control', 'TurnControlManager'),
        ('src.robot.communication', 'RoboMasterCSerial'),
        ('src.utils.logger', 'setup_logger'),
        ('src.utils.display', 'DisplayManager')
    ]
    
    success_count = 0
    for module_name, class_name in modules_to_test:
        try:
            module = __import__(module_name, fromlist=[class_name])
            getattr(module, class_name)
            print(f"   ✅ {module_name}.{class_name}")
            success_count += 1
        except Exception as e:
            print(f"   ❌ {module_name}.{class_name}: {e}")
    
    print(f"导入测试: {success_count}/{len(modules_to_test)} 成功")
    return success_count == len(modules_to_test)

def test_usb_cameras():
    """测试USB相机"""
    print("📷 测试USB相机...")
    
    available_cameras = []
    for i in range(6):
        cap = cv2.VideoCapture(i)
        if cap.isOpened():
            cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
            cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
            
            ret, frame = cap.read()
            if ret and frame is not None:
                h, w = frame.shape[:2]
                fps = cap.get(cv2.CAP_PROP_FPS)
                available_cameras.append(i)
                print(f"   ✅ 相机 {i}: {w}x{h} @ {fps} FPS")
            cap.release()
    
    if available_cameras:
        print(f"发现 {len(available_cameras)} 个可用相机")
        return True
    else:
        print("   ⚠️ 未发现可用USB相机")
        return False

def test_realsense_camera():
    """测试RealSense相机"""
    print("📷 测试RealSense相机...")
    
    try:
        import pyrealsense2 as rs
        
        # 创建上下文
        ctx = rs.context()
        devices = ctx.query_devices()
        
        if len(devices) == 0:
            print("   ⚠️ 未发现RealSense设备")
            return False
        
        for device in devices:
            name = device.get_info(rs.camera_info.name)
            serial = device.get_info(rs.camera_info.serial_number)
            print(f"   ✅ 发现设备: {name} (序列号: {serial})")
        
        # 测试数据流
        pipeline = rs.pipeline()
        config = rs.config()
        config.enable_stream(rs.stream.color, 640, 480, rs.format.bgr8, 30)
        config.enable_stream(rs.stream.depth, 640, 480, rs.format.z16, 30)
        
        pipeline.start(config)
        
        # 获取几帧数据
        for i in range(5):
            frames = pipeline.wait_for_frames()
            color_frame = frames.get_color_frame()
            depth_frame = frames.get_depth_frame()
            
            if color_frame and depth_frame:
                print(f"   ✅ 成功获取第 {i+1} 帧")
            else:
                print(f"   ❌ 第 {i+1} 帧数据异常")
                
        pipeline.stop()
        print("RealSense相机测试完成")
        return True
        
    except ImportError:
        print("   ❌ pyrealsense2 未安装")
        return False
    except Exception as e:
        print(f"   ❌ RealSense测试失败: {e}")
        return False

def test_serial_ports():
    """测试串口设备"""
    print("🔌 测试串口设备...")
    
    try:
        import serial
        import serial.tools.list_ports
        
        ports = list(serial.tools.list_ports.comports())
        
        if not ports:
            print("   ⚠️ 未发现串口设备")
            return False
        
        for port in ports:
            print(f"   ✅ 发现串口: {port.device} ({port.description})")
        
        return True
        
    except ImportError:
        print("   ❌ pyserial 未安装")
        return False
    except Exception as e:
        print(f"   ❌ 串口测试失败: {e}")
        return False

def test_web_api():
    """测试Web API"""
    print("🌐 测试Web API...")
    
    try:
        import requests
        
        base_url = "http://localhost:5000"
        
        # 测试主页
        try:
            response = requests.get(base_url, timeout=3)
            if response.status_code == 200:
                print("   ✅ 主页访问正常")
            else:
                print(f"   ❌ 主页返回状态码: {response.status_code}")
        except:
            print("   ⚠️ Web服务器未运行")
            return False
        
        # 测试API端点
        api_endpoints = ['/api/status', '/api/image']
        
        for endpoint in api_endpoints:
            try:
                response = requests.get(f"{base_url}{endpoint}", timeout=3)
                print(f"   ✅ {endpoint}: {response.status_code}")
            except Exception as e:
                print(f"   ❌ {endpoint}: {e}")
        
        return True
        
    except ImportError:
        print("   ❌ requests 未安装")
        return False
    except Exception as e:
        print(f"   ❌ Web API测试失败: {e}")
        return False

def test_perception_modules():
    """测试感知模块"""
    print("🧠 测试感知模块...")
    
    try:
        from src.perception.obstacle_detection import ObstacleDetector
        from src.perception.pipe_tracking import PipeTracker
        
        # 创建测试数据
        test_depth = np.random.randint(500, 2000, (480, 640), dtype=np.uint16)
        test_color = np.random.randint(0, 255, (480, 640, 3), dtype=np.uint8)
        
        # 测试障碍物检测
        detector = ObstacleDetector()
        mask = detector.detect(test_depth)
        analysis = detector.analyze_obstacle_threat(test_depth, mask)
        print(f"   ✅ 障碍物检测: 威胁等级 {analysis['threat_level']}")
        
        # 测试管道追踪
        tracker = PipeTracker()
        result = tracker.track(test_color, test_depth)
        print(f"   ✅ 管道追踪: 结果类型 {type(result)}")
        
        return True
        
    except Exception as e:
        print(f"   ❌ 感知模块测试失败: {e}")
        return False

def test_config_loading():
    """测试配置加载"""
    print("⚙️ 测试配置加载...")
    
    try:
        from src.config import (
            CameraConfig, RobotConfig, PerceptionConfig, 
            ControlConfig, RunModeConfig, SafetyConfig
        )
        
        # 检查关键配置
        configs = [
            ('CameraConfig.CAMERA_TYPE', CameraConfig.CAMERA_TYPE),
            ('RobotConfig.ROBOT_ENABLED', RobotConfig.ROBOT_ENABLED),
            ('PerceptionConfig.OBSTACLE_DEPTH_THRESHOLD', PerceptionConfig.OBSTACLE_DEPTH_THRESHOLD),
            ('RunModeConfig.DEFAULT_MODE', RunModeConfig.DEFAULT_MODE),
        ]
        
        for name, value in configs:
            print(f"   ✅ {name}: {value}")
        
        return True
        
    except Exception as e:
        print(f"   ❌ 配置加载失败: {e}")
        return False

def main():
    """主测试函数"""
    print("🧪 系统集成测试")
    print("=" * 60)
    print(f"测试时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)
    
    tests = [
        ("模块导入", test_imports),
        ("配置加载", test_config_loading),
        ("USB相机", test_usb_cameras),
        ("RealSense相机", test_realsense_camera),
        ("串口设备", test_serial_ports),
        ("感知模块", test_perception_modules),
        ("Web API", test_web_api),
    ]
    
    results = {}
    passed = 0
    
    for test_name, test_func in tests:
        print(f"\n🔍 {test_name}测试:")
        try:
            result = test_func()
            results[test_name] = result
            if result:
                passed += 1
        except Exception as e:
            print(f"   ❌ 测试异常: {e}")
            results[test_name] = False
    
    # 生成测试报告
    print("\n" + "=" * 60)
    print("📊 测试结果汇总")
    print("=" * 60)
    
    for test_name, result in results.items():
        status = "✅ 通过" if result else "❌ 失败"
        print(f"{test_name:15} {status}")
    
    print(f"\n总体结果: {passed}/{len(tests)} 项测试通过")
    
    if passed == len(tests):
        print("🎉 所有测试通过！系统就绪")
        return True
    else:
        print("⚠️ 部分测试失败，请检查相关组件")
        return False

if __name__ == "__main__":
    try:
        success = main()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n⚠️ 测试中断")
        sys.exit(130)
    except Exception as e:
        print(f"\n❌ 测试程序异常: {e}")
        traceback.print_exc()
        sys.exit(1)
