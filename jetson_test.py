#!/usr/bin/env python3
"""
Jetson快速测试脚本
解决OpenCV、摄像头和基本功能问题
"""

def test_opencv():
    """测试OpenCV安装"""
    try:
        import cv2
        print(f"✅ OpenCV版本: {cv2.__version__}")
        return True
    except ImportError as e:
        print(f"❌ OpenCV未安装: {e}")
        print("请运行: pip install opencv-python")
        return False

def test_camera():
    """测试USB摄像头"""
    try:
        import cv2
        cap = cv2.VideoCapture(0)
        if cap.isOpened():
            ret, frame = cap.read()
            if ret:
                print(f"✅ USB摄像头工作正常 - 分辨率: {frame.shape}")
                cap.release()
                return True
            else:
                print("❌ 摄像头无法读取图像")
                cap.release()
                return False
        else:
            print("❌ 无法打开摄像头")
            return False
    except Exception as e:
        print(f"❌ 摄像头测试失败: {e}")
        return False

def test_numpy():
    """测试NumPy"""
    try:
        import numpy as np
        print(f"✅ NumPy版本: {np.__version__}")
        return True
    except ImportError as e:
        print(f"❌ NumPy未安装: {e}")
        return False

def test_imports():
    """测试项目模块导入"""
    try:
        import sys
        import os
        
        # 添加src路径
        sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))
        
        from config import CameraConfig, RobotConfig
        print("✅ 配置模块导入成功")
        
        print(f"  相机类型: {CameraConfig.CAMERA_TYPE}")
        print(f"  机器人启用: {RobotConfig.ROBOT_ENABLED}")
        
        return True
    except Exception as e:
        print(f"❌ 模块导入失败: {e}")
        return False

def fix_config():
    """快速修复配置"""
    try:
        import os
        config_path = "src/config.py"
        
        if os.path.exists(config_path):
            # 备份
            os.system(f"cp {config_path} {config_path}.backup")
            
            # 读取并修改
            with open(config_path, 'r') as f:
                content = f.read()
            
            # 修改配置
            content = content.replace('CAMERA_TYPE = "realsense_d455"', 'CAMERA_TYPE = "usb"')
            content = content.replace('ROBOT_ENABLED = True', 'ROBOT_ENABLED = False')
            
            with open(config_path, 'w') as f:
                f.write(content)
                
            print("✅ 配置文件已自动修复")
            return True
        else:
            print("❌ 配置文件不存在")
            return False
    except Exception as e:
        print(f"❌ 配置修复失败: {e}")
        return False

def run_simple_test():
    """运行简单的系统测试"""
    try:
        import sys
        import os
        
        # 添加路径
        sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))
        
        # 简单测试主程序
        print("🧪 测试主程序导入...")
        from main import Tiaozhanbei2System
        
        print("✅ 主程序导入成功")
        
        # 创建系统实例
        system = Tiaozhanbei2System()
        print("✅ 系统实例创建成功")
        
        # 打印状态
        system.print_system_status()
        
        return True
    except Exception as e:
        print(f"❌ 系统测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """主测试函数"""
    print("🚀 Jetson部署快速诊断")
    print("=" * 50)
    
    tests = [
        ("NumPy测试", test_numpy),
        ("OpenCV测试", test_opencv),
        ("摄像头测试", test_camera),
        ("配置修复", fix_config),
        ("模块导入测试", test_imports),
        ("系统测试", run_simple_test)
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"\n📋 {test_name}...")
        try:
            if test_func():
                passed += 1
            else:
                print(f"   测试失败")
        except Exception as e:
            print(f"   测试异常: {e}")
    
    print(f"\n" + "=" * 50)
    print(f"📊 测试结果: {passed}/{total} 通过")
    
    if passed == total:
        print("🎉 所有测试通过！可以运行主程序了")
        print("建议运行: python -m src.main --mode demo --verbose")
    else:
        print("⚠️  部分测试失败，请根据提示修复问题")
    
    print("=" * 50)

if __name__ == "__main__":
    main()
