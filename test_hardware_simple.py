#!/usr/bin/env python3
"""
简化硬件连接测试
快速检测相机和下位机连接状态

功能：
- 检测RealSense相机连接状态
- 检测USB相机可用性
- 检测串口设备
- 提供针对性的故障排除建议

作者: cxzandy
日期: 2025-07-29
"""

import sys
import os
import time

def test_realsense_camera():
    """测试RealSense相机连接"""
    print("📹 测试RealSense D455相机...")
    
    try:
        import pyrealsense2 as rs
        print("✅ pyrealsense2库已安装")
        
        # 检测RealSense设备
        ctx = rs.context()
        devices = ctx.query_devices()
        
        if len(devices) == 0:
            print("❌ 未检测到RealSense设备")
            print("💡 解决方案:")
            print("   1. 检查USB连接 (确保使用USB 3.0端口)")
            print("   2. 重新插拔相机")
            print("   3. 检查设备管理器中是否显示相机")
            print("   4. 更新RealSense驱动程序")
            return False
        
        # 显示设备信息
        for i, device in enumerate(devices):
            print(f"✅ 设备 {i}: {device.get_info(rs.camera_info.name)}")
            print(f"   序列号: {device.get_info(rs.camera_info.serial_number)}")
            print(f"   固件: {device.get_info(rs.camera_info.firmware_version)}")
        
        # 尝试启动管道
        pipeline = rs.pipeline()
        config = rs.config()
        config.enable_stream(rs.stream.color, 640, 480, rs.format.bgr8, 30)
        config.enable_stream(rs.stream.depth, 640, 480, rs.format.z16, 30)
        
        try:
            pipeline.start(config)
            print("✅ 相机管道启动成功")
            
            # 尝试获取一帧
            frames = pipeline.wait_for_frames(timeout_ms=5000)
            color_frame = frames.get_color_frame()
            depth_frame = frames.get_depth_frame()
            
            if color_frame and depth_frame:
                print("✅ 成功获取彩色和深度图像")
                print(f"   彩色图像: {color_frame.get_width()}x{color_frame.get_height()}")
                print(f"   深度图像: {depth_frame.get_width()}x{depth_frame.get_height()}")
                pipeline.stop()
                return True
            else:
                print("❌ 无法获取图像帧")
                pipeline.stop()
                return False
                
        except Exception as e:
            print(f"❌ 相机管道启动失败: {e}")
            return False
            
    except ImportError:
        print("❌ pyrealsense2库未安装")
        print("💡 安装命令:")
        print("   conda install -c conda-forge pyrealsense2")
        print("   或者")
        print("   pip install pyrealsense2")
        return False
    except Exception as e:
        print(f"❌ RealSense测试失败: {e}")
        return False

def test_usb_camera():
    """测试USB相机"""
    print("\n📷 测试USB相机...")
    
    try:
        import cv2
        
        found_cameras = []
        for i in range(5):  # 测试索引0-4
            cap = cv2.VideoCapture(i)
            if cap.isOpened():
                ret, frame = cap.read()
                if ret and frame is not None:
                    found_cameras.append(i)
                    print(f"✅ USB相机 {i}: {frame.shape}")
            cap.release()
        
        if found_cameras:
            print(f"✅ 找到 {len(found_cameras)} 个USB相机: {found_cameras}")
            return True
        else:
            print("❌ 未找到可用的USB相机")
            print("💡 解决方案:")
            print("   1. 检查USB相机连接")
            print("   2. 确认相机驱动已安装")
            print("   3. 检查是否有其他程序占用相机")
            return False
            
    except ImportError:
        print("❌ OpenCV未安装")
        print("💡 安装命令: pip install opencv-python")
        return False
    except Exception as e:
        print(f"❌ USB相机测试失败: {e}")
        return False

def test_serial_ports():
    """测试串口设备"""
    print("\n🔌 检测串口设备...")
    
    try:
        import serial.tools.list_ports
        
        ports = list(serial.tools.list_ports.comports())
        
        if not ports:
            print("❌ 未检测到串口设备")
            print("💡 解决方案:")
            print("   1. 检查DJI RoboMaster C板USB连接")
            print("   2. 确认设备驱动已安装")
            print("   3. 检查设备管理器中的串口设备")
            return False
        
        print(f"✅ 检测到 {len(ports)} 个串口设备:")
        for port in ports:
            print(f"   📍 {port.device}")
            print(f"      描述: {port.description}")
            if port.manufacturer:
                print(f"      制造商: {port.manufacturer}")
            if port.vid and port.pid:
                print(f"      VID:PID: {port.vid:04X}:{port.pid:04X}")
        
        return True
        
    except ImportError:
        print("❌ pyserial未安装")
        print("💡 安装命令: pip install pyserial")
        return False
    except Exception as e:
        print(f"❌ 串口检测失败: {e}")
        return False

def test_robot_communication():
    """测试机器人通信"""
    print("\n🤖 测试机器人通信...")
    
    try:
        import serial
        import serial.tools.list_ports
        
        ports = list(serial.tools.list_ports.comports())
        if not ports:
            print("⚠️ 无可用串口，跳过通信测试")
            return False
        
        # 尝试连接第一个串口进行基础测试
        test_port = ports[0].device
        print(f"🔍 测试串口: {test_port}")
        
        try:
            ser = serial.Serial(
                port=test_port,
                baudrate=115200,
                timeout=1
            )
            
            print(f"✅ 串口 {test_port} 连接成功")
            
            # 发送测试命令
            test_commands = [b'01\n', b'02\n', b'03\n']
            for cmd in test_commands:
                ser.write(cmd)
                print(f"   ✅ 发送命令: {cmd.decode().strip()}")
                time.sleep(0.1)
            
            # 尝试读取响应
            try:
                response = ser.read(100)
                if response:
                    print(f"   ✅ 收到响应: {response}")
                else:
                    print("   ⚠️ 未收到响应 (可能正常)")
            except:
                print("   ⚠️ 读取响应超时")
            
            ser.close()
            print("✅ 基础串口通信测试完成")
            return True
            
        except serial.SerialException as e:
            print(f"❌ 串口连接失败: {e}")
            print("💡 可能的原因:")
            print("   1. 串口被其他程序占用")
            print("   2. 串口权限不足")
            print("   3. 波特率不匹配")
            return False
            
    except ImportError:
        print("❌ pyserial未安装")
        return False
    except Exception as e:
        print(f"❌ 机器人通信测试失败: {e}")
        return False

def main():
    """主函数"""
    print("🔧 挑战杯2.0系统 - 硬件连接快速测试")
    print("=" * 60)
    
    tests = [
        ("RealSense相机", test_realsense_camera),
        ("USB相机", test_usb_camera),
        ("串口设备", test_serial_ports),
        ("机器人通信", test_robot_communication)
    ]
    
    results = {}
    
    for test_name, test_func in tests:
        try:
            results[test_name] = test_func()
        except Exception as e:
            print(f"❌ {test_name} 测试异常: {e}")
            results[test_name] = False
    
    # 生成总结
    print("\n" + "="*60)
    print("📊 硬件连接测试总结")
    print("="*60)
    
    success_count = sum(results.values())
    total_count = len(results)
    
    for test_name, success in results.items():
        status = "✅ 正常" if success else "❌ 失败"
        print(f"{test_name}: {status}")
    
    print(f"\n成功率: {success_count}/{total_count} ({success_count/total_count*100:.1f}%)")
    
    if success_count == total_count:
        print("\n🎉 所有硬件连接正常！可以运行完整系统。")
        print("\n📋 下一步:")
        print("   python src/main.py --mode track")
    elif success_count > 0:
        print("\n⚠️ 部分硬件连接正常，可以运行对应功能的测试。")
        if results.get("RealSense相机", False):
            print("   相机可用 - 可以运行: cd tests && python test_camera.py")
        if results.get("机器人通信", False):
            print("   机器人可用 - 可以运行: cd tests && python test_robot.py")
    else:
        print("\n❌ 所有硬件连接失败，请检查硬件连接和驱动安装。")
        print("\n📖 参考文档:")
        print("   docs/HARDWARE_CONFIG.md")
        print("   docs/JETSON_DEPLOYMENT.md")
    
    return success_count > 0

if __name__ == "__main__":
    try:
        success = main()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n⚠️ 用户中断测试")
        sys.exit(0)
