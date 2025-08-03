#!/usr/bin/env python3
"""
硬件测试主程序
使用tests文件夹中的现有测试程序来检测相机和下位机

功能：
- 运行相机连接和标定测试 (test_camera.py)
- 运行机器人通信测试 (test_robot.py)
- 运行感知模块测试 (test_perception.py)
- 生成综合测试报告

作者: cxzandy
日期: 2025-07-29
"""

import sys
import os
import subprocess
import time
from datetime import datetime
import json

class HardwareTestRunner:
    """硬件测试运行器"""
    
    def __init__(self):
        """初始化测试运行器"""
        self.project_root = os.path.abspath(os.path.join(os.path.dirname(__file__)))
        self.tests_dir = os.path.join(self.project_root, 'tests')
        
        self.test_results = {
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "camera_test": {"status": "未运行", "details": ""},
            "robot_test": {"status": "未运行", "details": ""},
            "perception_test": {"status": "未运行", "details": ""},
            "overall_status": "未完成"
        }
        
        print("🔧 硬件测试运行器")
        print("使用tests文件夹中的现有测试程序")
        print("=" * 60)
        print(f"项目根目录: {self.project_root}")
        print(f"测试目录: {self.tests_dir}")
    
    def check_test_files(self):
        """检查测试文件是否存在"""
        print("\n📁 检查测试文件...")
        
        required_files = [
            'test_camera.py',
            'test_robot.py', 
            'test_perception.py'
        ]
        
        missing_files = []
        for file in required_files:
            file_path = os.path.join(self.tests_dir, file)
            if os.path.exists(file_path):
                print(f"✅ {file} - 存在")
            else:
                print(f"❌ {file} - 缺失")
                missing_files.append(file)
        
        if missing_files:
            print(f"\n❌ 缺失测试文件: {missing_files}")
            return False
        
        print("✅ 所有测试文件完整")
        return True
    
    def run_camera_test(self):
        """运行相机测试"""
        print("\n📹 运行相机连接和标定测试...")
        print("-" * 40)
        
        try:
            # 运行test_camera.py
            test_file = os.path.join(self.tests_dir, 'test_camera.py')
            
            # 设置环境变量
            env = os.environ.copy()
            env['PYTHONPATH'] = self.project_root
            
            # 运行测试
            result = subprocess.run([
                sys.executable, test_file
            ], cwd=self.project_root, env=env, 
               capture_output=True, text=True, timeout=60)
            
            # 分析结果
            if result.returncode == 0:
                print("✅ 相机测试成功完成")
                self.test_results["camera_test"]["status"] = "成功"
                
                # 检查输出中的关键信息
                output = result.stdout
                if "相机标定测试成功完成" in output:
                    print("✅ 相机标定成功")
                    self.test_results["camera_test"]["details"] += "标定成功; "
                
                if "连接成功" in output or "RealSense" in output:
                    print("✅ RealSense相机连接正常")
                    self.test_results["camera_test"]["details"] += "RealSense连接正常; "
                
            else:
                print("❌ 相机测试失败")
                self.test_results["camera_test"]["status"] = "失败"
                self.test_results["camera_test"]["details"] = f"返回码: {result.returncode}"
            
            # 显示输出
            if result.stdout:
                print("📄 测试输出:")
                print(result.stdout)
            
            if result.stderr:
                print("⚠️ 错误信息:")
                print(result.stderr)
                self.test_results["camera_test"]["details"] += f"错误: {result.stderr[:200]}..."
            
        except subprocess.TimeoutExpired:
            print("❌ 相机测试超时")
            self.test_results["camera_test"]["status"] = "超时"
            self.test_results["camera_test"]["details"] = "测试执行超时"
            
        except Exception as e:
            print(f"❌ 相机测试异常: {e}")
            self.test_results["camera_test"]["status"] = "异常"
            self.test_results["camera_test"]["details"] = str(e)
    
    def run_robot_test(self):
        """运行机器人通信测试"""
        print("\n🤖 运行机器人通信测试...")
        print("-" * 40)
        
        try:
            # 检查是否有可用串口
            import serial.tools.list_ports
            ports = list(serial.tools.list_ports.comports())
            
            if not ports:
                print("⚠️ 未检测到串口设备，跳过机器人测试")
                self.test_results["robot_test"]["status"] = "跳过"
                self.test_results["robot_test"]["details"] = "无可用串口"
                return
            
            print(f"📍 检测到 {len(ports)} 个串口设备:")
            for port in ports:
                print(f"   {port.device} - {port.description}")
            
            # 运行test_robot.py (自动测试模式)
            test_file = os.path.join(self.tests_dir, 'test_robot.py')
            
            # 设置环境变量
            env = os.environ.copy()
            env['PYTHONPATH'] = self.project_root
            
            # 创建输入模拟自动测试
            process_input = "1\n"  # 选择自动测试
            
            # 运行测试
            result = subprocess.run([
                sys.executable, test_file
            ], cwd=self.project_root, env=env,
               input=process_input, capture_output=True, 
               text=True, timeout=30)
            
            # 分析结果
            if result.returncode == 0:
                print("✅ 机器人测试程序执行完成")
                
                # 检查输出中的关键信息
                output = result.stdout
                if "测试成功" in output or "通信正常" in output:
                    print("✅ 机器人通信测试成功")
                    self.test_results["robot_test"]["status"] = "成功"
                    self.test_results["robot_test"]["details"] = "通信正常"
                elif "连接失败" in output or "无法连接" in output:
                    print("❌ 机器人连接失败")
                    self.test_results["robot_test"]["status"] = "失败"
                    self.test_results["robot_test"]["details"] = "连接失败"
                else:
                    print("⚠️ 机器人测试结果不明确")
                    self.test_results["robot_test"]["status"] = "不明确"
                    self.test_results["robot_test"]["details"] = "结果不明确"
                    
            else:
                print("❌ 机器人测试失败")
                self.test_results["robot_test"]["status"] = "失败"
                self.test_results["robot_test"]["details"] = f"返回码: {result.returncode}"
            
            # 显示输出
            if result.stdout:
                print("📄 测试输出:")
                print(result.stdout)
            
            if result.stderr:
                print("⚠️ 错误信息:")
                print(result.stderr)
                
        except subprocess.TimeoutExpired:
            print("❌ 机器人测试超时")
            self.test_results["robot_test"]["status"] = "超时"
            self.test_results["robot_test"]["details"] = "测试执行超时"
            
        except Exception as e:
            print(f"❌ 机器人测试异常: {e}")
            self.test_results["robot_test"]["status"] = "异常"
            self.test_results["robot_test"]["details"] = str(e)
    
    def run_perception_test(self):
        """运行感知模块测试"""
        print("\n👁️ 运行感知模块测试...")
        print("-" * 40)
        
        try:
            # 运行test_perception.py
            test_file = os.path.join(self.tests_dir, 'test_perception.py')
            
            # 检查文件是否存在
            if not os.path.exists(test_file):
                print("⚠️ test_perception.py 不存在，跳过感知测试")
                self.test_results["perception_test"]["status"] = "跳过"
                self.test_results["perception_test"]["details"] = "测试文件不存在"
                return
            
            # 设置环境变量
            env = os.environ.copy()
            env['PYTHONPATH'] = self.project_root
            
            # 运行测试
            result = subprocess.run([
                sys.executable, test_file
            ], cwd=self.project_root, env=env,
               capture_output=True, text=True, timeout=45)
            
            # 分析结果
            if result.returncode == 0:
                print("✅ 感知模块测试成功完成")
                self.test_results["perception_test"]["status"] = "成功"
                self.test_results["perception_test"]["details"] = "测试通过"
            else:
                print("❌ 感知模块测试失败")
                self.test_results["perception_test"]["status"] = "失败"
                self.test_results["perception_test"]["details"] = f"返回码: {result.returncode}"
            
            # 显示输出
            if result.stdout:
                print("📄 测试输出:")
                print(result.stdout)
            
            if result.stderr:
                print("⚠️ 错误信息:")
                print(result.stderr)
                
        except subprocess.TimeoutExpired:
            print("❌ 感知模块测试超时")
            self.test_results["perception_test"]["status"] = "超时"
            self.test_results["perception_test"]["details"] = "测试执行超时"
            
        except Exception as e:
            print(f"❌ 感知模块测试异常: {e}")
            self.test_results["perception_test"]["status"] = "异常"
            self.test_results["perception_test"]["details"] = str(e)
    
    def show_interactive_options(self):
        """显示交互式测试选项"""
        print("\n🎮 交互式测试选项:")
        print("-" * 40)
        print("如果你想进行更详细的交互式测试，可以直接运行:")
        print()
        print("1. 相机标定和测试:")
        print("   cd tests && python test_camera.py")
        print()
        print("2. 机器人交互式测试:")
        print("   cd tests && python test_robot.py")
        print("   (选择交互式模式，可以手动发送命令)")
        print()
        print("3. 感知模块测试:")
        print("   cd tests && python test_perception.py")
        print()
    
    def generate_report(self):
        """生成测试报告"""
        print("\n" + "="*60)
        print("📊 硬件测试综合报告")
        print("="*60)
        
        # 计算总体状态
        test_count = 0
        success_count = 0
        
        for test_name, result in self.test_results.items():
            if test_name in ["timestamp", "overall_status"]:
                continue
                
            test_count += 1
            if result["status"] == "成功":
                success_count += 1
        
        # 设置总体状态
        if success_count == test_count:
            overall_status = "全部成功"
            status_icon = "✅"
        elif success_count > 0:
            overall_status = "部分成功"
            status_icon = "⚠️"
        else:
            overall_status = "全部失败"
            status_icon = "❌"
        
        self.test_results["overall_status"] = overall_status
        
        print(f"测试时间: {self.test_results['timestamp']}")
        print(f"总体状态: {status_icon} {overall_status}")
        print(f"成功率: {success_count}/{test_count} ({success_count/test_count*100:.1f}%)")
        print()
        
        # 详细结果
        test_names = {
            "camera_test": "📹 相机测试",
            "robot_test": "🤖 机器人测试", 
            "perception_test": "👁️ 感知模块测试"
        }
        
        for test_key, test_name in test_names.items():
            result = self.test_results[test_key]
            status = result["status"]
            details = result["details"]
            
            if status == "成功":
                icon = "✅"
            elif status == "失败":
                icon = "❌"
            elif status == "跳过":
                icon = "⏭️"
            elif status == "超时":
                icon = "⏱️"
            else:
                icon = "⚠️"
            
            print(f"{icon} {test_name}: {status}")
            if details:
                print(f"   详情: {details}")
        
        print()
        
        # 建议和下一步
        if overall_status == "全部成功":
            print("🎉 所有硬件测试通过！系统已准备就绪。")
            print()
            print("📋 下一步操作:")
            print("   1. 运行完整系统: python src/main.py --mode track")
            print("   2. 启动Web界面: python web/web_simple.py")
            print("   3. 运行演示模式: python src/main.py --mode demo")
            print("   4. 测试障碍物避障: python test_obstacle_avoidance.py")
            
        else:
            print("⚠️ 部分测试未通过，请检查以下问题:")
            print()
            
            if self.test_results["camera_test"]["status"] != "成功":
                print("📹 相机问题:")
                print("   - 检查RealSense D455是否正确连接")
                print("   - 确认USB端口支持USB 3.0")
                print("   - 安装RealSense驱动和SDK")
                print("   - 运行: conda install -c conda-forge pyrealsense2")
            
            if self.test_results["robot_test"]["status"] == "失败":
                print("🤖 机器人通信问题:")
                print("   - 检查DJI RoboMaster C板连接")
                print("   - 确认串口号和波特率设置")
                print("   - 检查串口权限设置")
                print("   - 确认下位机程序正在运行")
            
            print()
            print("💡 故障排除:")
            print("   1. 参考文档: docs/HARDWARE_CONFIG.md")
            print("   2. 手动运行单个测试进行详细诊断")
            print("   3. 检查系统日志和错误信息")
        
        # 保存报告
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_file = f"hardware_test_report_{timestamp}.json"
        
        try:
            with open(report_file, 'w', encoding='utf-8') as f:
                json.dump(self.test_results, f, ensure_ascii=False, indent=2)
            print(f"\n💾 详细报告已保存: {report_file}")
        except Exception as e:
            print(f"\n⚠️ 报告保存失败: {e}")
        
        return overall_status == "全部成功"
    
    def run_all_tests(self):
        """运行所有硬件测试"""
        print("🚀 开始运行硬件测试...")
        
        # 检查测试文件
        if not self.check_test_files():
            print("❌ 测试文件检查失败，无法继续")
            return False
        
        # 按顺序运行测试
        self.run_camera_test()
        self.run_robot_test()
        self.run_perception_test()
        
        # 显示交互式选项
        self.show_interactive_options()
        
        # 生成报告
        return self.generate_report()

def main():
    """主函数"""
    print("🔧 挑战杯2.0系统 - 硬件测试工具")
    print("使用tests文件夹中的测试程序")
    print("=" * 60)
    
    try:
        # 创建测试运行器
        test_runner = HardwareTestRunner()
        
        print("\n选择测试模式:")
        print("1. 运行所有自动测试")
        print("2. 仅运行相机测试")
        print("3. 仅运行机器人测试")
        print("4. 仅运行感知模块测试")
        print("5. 显示交互式测试指南")
        
        choice = input("\n请选择 (1-5): ").strip()
        
        if choice == "1":
            success = test_runner.run_all_tests()
            return 0 if success else 1
            
        elif choice == "2":
            test_runner.run_camera_test()
            
        elif choice == "3":
            test_runner.run_robot_test()
            
        elif choice == "4":
            test_runner.run_perception_test()
            
        elif choice == "5":
            test_runner.show_interactive_options()
            
        else:
            print("无效选择，运行所有测试...")
            success = test_runner.run_all_tests()
            return 0 if success else 1
        
        return 0
        
    except KeyboardInterrupt:
        print("\n⚠️ 用户中断测试")
        return 0
    except Exception as e:
        print(f"\n❌ 测试运行失败: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
