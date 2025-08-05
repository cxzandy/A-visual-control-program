#!/usr/bin/env python3
"""
综合测试运行器
运行所有核心模块的测试
"""

import sys
import os
import time
from pathlib import Path

# 添加src目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / "src"))

def test_imports():
    """测试核心模块导入"""
    print("🔍 测试模块导入...")
    
    try:
        # 测试相机模块
        from camera.capture import RealSenseCapture, USBCapture
        from camera.calibration import calibrate_camera
        print("✅ 相机模块导入成功")
        
        # 测试感知模块
        from perception.pipe_tracking import PipeTracker
        from perception.obstacle_detection import ObstacleDetector
        print("✅ 感知模块导入成功")
        
        # 测试控制模块
        from control.turn_control import TurnControlManager
        print("✅ 控制模块导入成功")
        
        # 测试机器人通信
        from robot.communication import RoboMasterCSerial
        print("✅ 机器人通信模块导入成功")
        
        # 测试配置
        from config import CameraConfig, RobotConfig, PerceptionConfig
        print("✅ 配置模块导入成功")
        
        return True
        
    except ImportError as e:
        print(f"❌ 模块导入失败: {e}")
        return False

def test_configuration():
    """测试配置有效性"""
    print("\n⚙️ 测试配置...")
    
    try:
        from config import validate_config
        validate_config()
        print("✅ 配置验证通过")
        return True
    except Exception as e:
        print(f"❌ 配置验证失败: {e}")
        return False

def test_basic_functionality():
    """测试基本功能"""
    print("\n🧪 测试基本功能...")
    
    try:
        # 测试障碍物检测器
        from perception.obstacle_detection import ObstacleDetector
        detector = ObstacleDetector()
        print("✅ 障碍物检测器创建成功")
        
        # 测试管道追踪器
        from perception.pipe_tracking import PipeTracker
        tracker = PipeTracker()
        print("✅ 管道追踪器创建成功")
        
        # 测试转向控制器
        from control.turn_control import TurnControlManager
        controller = TurnControlManager()
        print("✅ 转向控制器创建成功")
        
        return True
        
    except Exception as e:
        print(f"❌ 基本功能测试失败: {e}")
        return False

def main():
    """主测试函数"""
    print("🚀 开始综合测试")
    print("=" * 50)
    
    start_time = time.time()
    
    # 运行测试
    tests = [
        ("模块导入", test_imports),
        ("配置验证", test_configuration), 
        ("基本功能", test_basic_functionality)
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        try:
            if test_func():
                passed += 1
        except Exception as e:
            print(f"❌ {test_name}测试异常: {e}")
    
    # 输出结果
    duration = time.time() - start_time
    print("\n" + "=" * 50)
    print(f"📊 测试完成!")
    print(f"✅ 通过: {passed}/{total}")
    print(f"⏱️ 用时: {duration:.2f}秒")
    
    if passed == total:
        print("🎉 所有测试通过!")
        return 0
    else:
        print("⚠️ 部分测试失败，请检查系统配置")
        return 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)