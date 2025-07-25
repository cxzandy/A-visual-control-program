#!/usr/bin/env python3
"""
键盘控制集成测试脚本
测试WASD键盘控制与机器人命令的集成
"""

import sys
import os
import time

# 添加src目录到Python路径
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(project_root, 'src'))

from utils.keyboard_control import KeyboardController
from config import RobotConfig, ControlConfig

class MockRobotComm:
    """模拟机器人通信类"""
    
    def __init__(self):
        self.command_history = []
        
    def send(self, command: str) -> bool:
        """模拟发送命令"""
        self.command_history.append({
            'command': command,
            'timestamp': time.time()
        })
        
        # 根据命令显示对应的说明
        command_desc = {
            "01": "前进",
            "02": "后退", 
            "03": "左转",
            "04": "右转",
            "05": "避障",
            "stop": "停止"
        }
        
        desc = command_desc.get(command, "未知命令")
        print(f"📡 发送到下位机: {command} ({desc})")
        return True
        
    def get_history(self):
        """获取命令历史"""
        return self.command_history

def test_keyboard_control_integration():
    """测试键盘控制集成"""
    print("🧪 键盘控制集成测试")
    print("=" * 50)
    print("📋 命令映射:")
    print("  W 键 -> 01 (前进)")
    print("  S 键 -> 02 (后退)")
    print("  A 键 -> 03 (左转)")
    print("  D 键 -> 04 (右转)")
    print("  空格 -> stop (停止)")
    print("  Q 键 -> 退出")
    print("=" * 50)
    
    # 创建模拟机器人通信
    mock_robot = MockRobotComm()
    
    # 创建键盘控制器
    controller = KeyboardController(robot_comm=mock_robot)
    
    # 设置命令回调
    def on_command(cmd):
        print(f"✅ 键盘命令处理: {cmd}")
    
    controller.set_command_callback(on_command)
    
    try:
        print("\n🎮 开始键盘控制测试...")
        print("请按 WASD 键进行测试，按 Q 退出")
        
        # 启动键盘控制
        controller.start_keyboard_control()
        
        # 主循环
        while controller.running:
            time.sleep(0.1)
            
    except KeyboardInterrupt:
        print("\n⚠️ 用户中断测试")
    finally:
        controller.stop_keyboard_control()
        
        # 显示测试结果
        print("\n📊 测试结果统计:")
        stats = controller.get_statistics()
        print(f"  总命令数: {stats['total_commands']}")
        for cmd, count in stats['command_count'].items():
            if count > 0:
                print(f"  {cmd}: {count} 次")
        
        print("\n📜 机器人命令历史:")
        history = mock_robot.get_history()
        for i, record in enumerate(history[-10:], 1):  # 显示最后10条
            print(f"  {i}. {record['command']} (时间: {record['timestamp']:.2f})")

def test_command_mapping():
    """测试命令映射"""
    print("\n🔗 测试命令映射:")
    print("-" * 30)
    
    controller = KeyboardController()
    
    test_keys = ['w', 'a', 's', 'd', ' ', 'q']
    
    for key in test_keys:
        robot_cmd = controller.process_key(key)
        if robot_cmd:
            print(f"  '{key}' -> {robot_cmd}")
        else:
            print(f"  '{key}' -> 无效")

def test_config_values():
    """测试配置值"""
    print("\n⚙️ 测试配置值:")
    print("-" * 30)
    
    print("机器人命令:")
    for name, code in RobotConfig.COMMANDS.items():
        if name.startswith("MOVE_") or name.startswith("TURN_") or name == "OBSTACLE_AVOID":
            print(f"  {name}: {code}")
    
    print("\n键盘映射:")
    for key, cmd in RobotConfig.KEYBOARD_COMMANDS.items():
        print(f"  '{key}' -> {cmd}")
    
    print("\n控制配置:")
    print(f"  键盘控制启用: {ControlConfig.KEYBOARD_CONTROL_ENABLED}")
    print(f"  重复延迟: {ControlConfig.KEYBOARD_REPEAT_DELAY}s")
    print(f"  最大连续时间: {ControlConfig.MAX_CONTINUOUS_COMMAND_TIME}s")

def main():
    """主函数"""
    print("🚀 Tiaozhanbei2.0 键盘控制测试程序")
    print("选择测试模式:")
    print("1. 命令映射测试")
    print("2. 配置值测试")
    print("3. 完整集成测试")
    
    try:
        choice = input("请输入选择 (1-3): ").strip()
        
        if choice == "1":
            test_command_mapping()
        elif choice == "2":
            test_config_values()
        elif choice == "3":
            test_command_mapping()
            test_config_values()
            test_keyboard_control_integration()
        else:
            print("无效选择")
            
    except KeyboardInterrupt:
        print("\n\n👋 测试中断")
    except Exception as e:
        print(f"\n❌ 测试出错: {e}")

if __name__ == "__main__":
    main()
