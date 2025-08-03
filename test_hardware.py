#!/usr/bin/env python3
"""
硬件连接测试脚本
测试下位机(DJI RoboMaster C板)和相机(RealSense D455)连接状态

功能：
- 检测RealSense相机连接状态
- 测试USB相机可用性
- 检测串口下位机连接
- 测试基础通信功能
- 生成硬件状态报告

作者: cxzandy
日期: 2025-07-29
"""

import sys
import os
import time
import serial
import serial.tools.list_ports
import cv2
import numpy as np
from datetime import datetime

# 添加src目录到Python路径
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), 'src'))

try:
    from config import CameraConfig, RobotConfig
    from camera.stereo_capture import RealSenseCapture
    from robot.communication import RoboMasterCSerial
except ImportError as e:
    print(f"⚠️  导入模块失败: {e}")
    print("请确保在项目根目录运行此脚本")

class HardwareTestSuite:
    """硬件测试套件"""
    
    def __init__(self):
        """初始化测试套件"""
        self.test_results = {
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "realsense_camera": {"status": "未测试", "details": {}},
            "usb_camera": {"status": "未测试", "details": {}},
            "serial_ports": {"status": "未测试", "details": {}},
            "robot_communication": {"status": "未测试", "details": {}},
            "overall_status": "未完成"
        }
        
        print("🔧 硬件连接测试套件初始化")
        print("=" * 60)
    
    def test_realsense_camera(self):
        """测试RealSense相机"""
        print("\n📹 测试RealSense D455相机连接...")
        
        try:
            # 检查pyrealsense2是否可用
            try:
                import pyrealsense2 as rs
                print("✅ pyrealsense2库已安装")
            except ImportError:
                self.test_results["realsense_camera"] = {
                    "status": "失败",
                    "details": {"error": "pyrealsense2库未安装", "solution": "pip install pyrealsense2"}
                }
                print("❌ pyrealsense2库未安装")
                print("💡 解决方案: conda install -c conda-forge pyrealsense2")
                return False
            
            # 枚举RealSense设备
            ctx = rs.context()
            devices = ctx.query_devices()
            
            if len(devices) == 0:
                self.test_results["realsense_camera"] = {
                    "status": "失败",
                    "details": {"error": "未检测到RealSense设备", "device_count": 0}
                }
                print("❌ 未检测到RealSense设备")
                print("💡 请检查:")
                print("   1. 相机是否正确连接USB端口")
                print("   2. USB端口是否支持USB 3.0")
                print("   3. 相机驱动是否正确安装")
                return False
            
            # 获取设备信息
            device_info = {}
            for i, device in enumerate(devices):
                info = {
                    "name": device.get_info(rs.camera_info.name),
                    "serial": device.get_info(rs.camera_info.serial_number),
                    "firmware": device.get_info(rs.camera_info.firmware_version),
                    "usb_type": device.get_info(rs.camera_info.usb_type_descriptor)
                }
                device_info[f"device_{i}"] = info
                print(f"✅ 设备 {i}: {info['name']}")
                print(f"   序列号: {info['serial']}")
                print(f"   固件版本: {info['firmware']}")
                print(f"   USB类型: {info['usb_type']}")
            
            # 尝试创建RealSense捕获实例
            try:
                rs_capture = RealSenseCapture()
                print("✅ RealSense捕获实例创建成功")
                
                # 测试获取帧
                color_frame, depth_frame = rs_capture.get_frames()
                if color_frame is not None and depth_frame is not None:
                    print(f"✅ 成功获取图像帧")
                    print(f"   彩色图像尺寸: {color_frame.shape}")
                    print(f"   深度图像尺寸: {depth_frame.shape}")
                    
                    # 保存测试图像
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    cv2.imwrite(f"test_realsense_color_{timestamp}.jpg", color_frame)
                    cv2.imwrite(f"test_realsense_depth_{timestamp}.png", depth_frame)
                    print(f"✅ 测试图像已保存")
                    
                    device_info["test_success"] = True
                    device_info["frame_size"] = {
                        "color": color_frame.shape,
                        "depth": depth_frame.shape
                    }
                else:
                    print("❌ 无法获取图像帧")
                    device_info["test_success"] = False
                
                rs_capture.stop()
                
            except Exception as e:
                print(f"❌ RealSense测试失败: {e}")
                device_info["test_error"] = str(e)
                device_info["test_success"] = False
            
            self.test_results["realsense_camera"] = {
                "status": "成功" if device_info.get("test_success", False) else "失败",
                "details": device_info
            }
            
            return device_info.get("test_success", False)
            
        except Exception as e:
            self.test_results["realsense_camera"] = {
                "status": "失败",
                "details": {"error": str(e)}
            }
            print(f"❌ RealSense测试异常: {e}")
            return False
    
    def test_usb_camera(self):
        """测试USB相机"""
        print("\n📷 测试USB相机连接...")
        
        usb_results = {}
        success_count = 0
        
        # 测试多个USB设备索引
        for index in range(5):  # 测试索引0-4
            try:
                cap = cv2.VideoCapture(index)
                if cap.isOpened():
                    # 尝试读取一帧
                    ret, frame = cap.read()
                    if ret and frame is not None:
                        print(f"✅ USB摄像头 {index} 可用")
                        print(f"   图像尺寸: {frame.shape}")
                        
                        # 保存测试图像
                        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                        cv2.imwrite(f"test_usb_camera_{index}_{timestamp}.jpg", frame)
                        
                        usb_results[f"camera_{index}"] = {
                            "available": True,
                            "frame_size": frame.shape,
                            "test_image_saved": True
                        }
                        success_count += 1
                    else:
                        usb_results[f"camera_{index}"] = {
                            "available": False,
                            "error": "无法读取图像帧"
                        }
                else:
                    usb_results[f"camera_{index}"] = {
                        "available": False,
                        "error": "无法打开设备"
                    }
                cap.release()
            except Exception as e:
                usb_results[f"camera_{index}"] = {
                    "available": False,
                    "error": str(e)
                }
        
        if success_count > 0:
            print(f"✅ 找到 {success_count} 个可用的USB摄像头")
        else:
            print("❌ 未找到可用的USB摄像头")
            print("💡 请检查:")
            print("   1. USB摄像头是否正确连接")
            print("   2. 摄像头驱动是否正确安装")
            print("   3. 是否有其他程序占用摄像头")
        
        self.test_results["usb_camera"] = {
            "status": "成功" if success_count > 0 else "失败",
            "details": {
                "available_cameras": success_count,
                "camera_details": usb_results
            }
        }
        
        return success_count > 0
    
    def test_serial_ports(self):
        """测试串口连接"""
        print("\n🔌 检测可用串口...")
        
        # 获取所有可用串口
        ports = serial.tools.list_ports.comports()
        port_info = {}
        
        if not ports:
            print("❌ 未检测到任何串口设备")
            self.test_results["serial_ports"] = {
                "status": "失败",
                "details": {"error": "未检测到串口设备", "available_ports": 0}
            }
            return False
        
        print(f"✅ 检测到 {len(ports)} 个串口设备:")
        
        for port in ports:
            info = {
                "device": port.device,
                "description": port.description,
                "manufacturer": port.manufacturer,
                "vid": port.vid,
                "pid": port.pid,
                "serial_number": port.serial_number
            }
            port_info[port.device] = info
            
            print(f"   📍 {port.device}")
            print(f"      描述: {port.description}")
            print(f"      制造商: {port.manufacturer}")
            if port.vid and port.pid:
                print(f"      VID:PID: {port.vid:04X}:{port.pid:04X}")
            if port.serial_number:
                print(f"      序列号: {port.serial_number}")
        
        self.test_results["serial_ports"] = {
            "status": "成功",
            "details": {
                "available_ports": len(ports),
                "port_details": port_info
            }
        }
        
        return True
    
    def test_robot_communication(self):
        """测试机器人通信"""
        print("\n🤖 测试机器人下位机通信...")
        
        # 获取可用串口
        ports = serial.tools.list_ports.comports()
        if not ports:
            print("❌ 无可用串口，跳过机器人通信测试")
            self.test_results["robot_communication"] = {
                "status": "跳过",
                "details": {"error": "无可用串口"}
            }
            return False
        
        # 尝试连接每个串口
        for port in ports:
            print(f"\n🔍 测试串口: {port.device}")
            
            try:
                # 使用配置的参数尝试连接
                robot = RoboMasterCSerial(
                    port=port.device,
                    baudrate=RobotConfig.BAUD_RATE,
                    timeout=RobotConfig.TIMEOUT
                )
                
                print(f"✅ 串口 {port.device} 连接成功")
                
                # 测试发送命令
                test_commands = ["01", "02", "03", "04", "05"]
                success_count = 0
                
                for cmd in test_commands:
                    try:
                        robot.send(cmd)
                        print(f"   ✅ 命令 {cmd} 发送成功")
                        success_count += 1
                        time.sleep(0.1)  # 短暂延迟
                    except Exception as e:
                        print(f"   ❌ 命令 {cmd} 发送失败: {e}")
                
                # 尝试接收响应
                try:
                    response = robot.recv(timeout_sec=2)
                    if response:
                        print(f"   ✅ 收到响应: {response}")
                    else:
                        print("   ⚠️  未收到响应 (可能正常，取决于下位机实现)")
                except Exception as e:
                    print(f"   ⚠️  接收响应失败: {e}")
                
                robot.close()
                
                # 如果成功发送所有命令，认为测试成功
                if success_count == len(test_commands):
                    print(f"✅ 机器人通信测试成功 (端口: {port.device})")
                    self.test_results["robot_communication"] = {
                        "status": "成功",
                        "details": {
                            "port": port.device,
                            "baudrate": RobotConfig.BAUD_RATE,
                            "commands_sent": success_count,
                            "total_commands": len(test_commands)
                        }
                    }
                    return True
                else:
                    print(f"⚠️  部分命令发送失败 ({success_count}/{len(test_commands)})")
                
            except Exception as e:
                print(f"❌ 串口 {port.device} 连接失败: {e}")
                continue
        
        print("❌ 所有串口测试失败")
        print("💡 请检查:")
        print("   1. DJI RoboMaster C板是否正确连接")
        print("   2. 串口参数是否正确配置")
        print("   3. 下位机程序是否正在运行")
        print("   4. 串口权限是否正确设置")
        
        self.test_results["robot_communication"] = {
            "status": "失败",
            "details": {"error": "所有串口连接测试失败"}
        }
        
        return False
    
    def generate_report(self):
        """生成测试报告"""
        print("\n" + "="*60)
        print("📊 硬件测试报告")
        print("="*60)
        
        # 计算总体状态
        success_count = 0
        total_tests = 0
        
        for test_name, result in self.test_results.items():
            if test_name in ["timestamp", "overall_status"]:
                continue
            total_tests += 1
            if result["status"] == "成功":
                success_count += 1
        
        overall_success = success_count == total_tests
        self.test_results["overall_status"] = "成功" if overall_success else "部分失败"
        
        print(f"测试时间: {self.test_results['timestamp']}")
        print(f"总体状态: {'✅ 全部成功' if overall_success else '⚠️  部分失败'}")
        print(f"成功率: {success_count}/{total_tests} ({success_count/total_tests*100:.1f}%)")
        print()
        
        # 详细结果
        for test_name, result in self.test_results.items():
            if test_name in ["timestamp", "overall_status"]:
                continue
            
            status_icon = "✅" if result["status"] == "成功" else "❌" if result["status"] == "失败" else "⚠️"
            test_display_name = {
                "realsense_camera": "RealSense相机",
                "usb_camera": "USB相机",
                "serial_ports": "串口检测",
                "robot_communication": "机器人通信"
            }.get(test_name, test_name)
            
            print(f"{status_icon} {test_display_name}: {result['status']}")
        
        print()
        
        # 建议和下一步
        if overall_success:
            print("🎉 所有硬件测试通过！系统已准备就绪。")
            print()
            print("📋 下一步:")
            print("   1. 运行完整系统: python src/main.py --mode track")
            print("   2. 启动Web界面: python web/web_simple.py")
            print("   3. 运行演示模式: python src/main.py --mode demo")
        else:
            print("⚠️  部分硬件测试失败，请检查以下项目:")
            print()
            for test_name, result in self.test_results.items():
                if result["status"] == "失败":
                    print(f"❌ {test_name}: {result.get('details', {}).get('error', '未知错误')}")
            print()
            print("💡 故障排除建议:")
            print("   1. 检查所有硬件连接")
            print("   2. 确认驱动程序正确安装")
            print("   3. 检查系统权限设置")
            print("   4. 参考文档: docs/HARDWARE_CONFIG.md")
        
        # 保存报告到文件
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_file = f"hardware_test_report_{timestamp}.json"
        
        try:
            import json
            with open(report_file, 'w', encoding='utf-8') as f:
                json.dump(self.test_results, f, ensure_ascii=False, indent=2)
            print(f"\n💾 详细报告已保存: {report_file}")
        except Exception as e:
            print(f"\n⚠️  报告保存失败: {e}")
        
        return overall_success
    
    def run_all_tests(self):
        """运行所有硬件测试"""
        print("🚀 开始硬件连接测试...")
        
        # 按顺序运行所有测试
        tests = [
            ("RealSense相机", self.test_realsense_camera),
            ("USB相机", self.test_usb_camera),
            ("串口检测", self.test_serial_ports),
            ("机器人通信", self.test_robot_communication)
        ]
        
        for test_name, test_func in tests:
            try:
                test_func()
            except Exception as e:
                print(f"❌ {test_name} 测试异常: {e}")
                # 继续执行其他测试
        
        # 生成最终报告
        return self.generate_report()

def main():
    """主函数"""
    print("🔧 硬件连接测试工具")
    print("测试目标: RealSense相机 + DJI RoboMaster C板")
    print("=" * 60)
    
    try:
        # 创建测试套件
        test_suite = HardwareTestSuite()
        
        # 运行所有测试
        success = test_suite.run_all_tests()
        
        return 0 if success else 1
        
    except KeyboardInterrupt:
        print("\n⚠️  用户中断测试")
        return 0
    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
