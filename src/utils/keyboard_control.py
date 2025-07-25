#!/usr/bin/env python3
"""
键盘控制模块
处理键盘输入并转换为机器人控制命令

支持的键盘控制：
- W/w: 前进 (发送01)
- S/s: 后退 (发送02)  
- A/a: 左转 (发送03)
- D/d: 右转 (发送04)
- 空格: 停止
- Q/q: 退出
"""

import time
import threading
from typing import Optional, Callable, Dict, Any
import sys
import os

# 添加src目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import RobotConfig, ControlConfig

class KeyboardController:
    """键盘控制器类"""
    
    def __init__(self, robot_comm=None, logger=None):
        """
        初始化键盘控制器
        
        Args:
            robot_comm: 机器人通信对象
            logger: 日志记录器
        """
        self.robot_comm = robot_comm
        self.logger = logger
        self.running = False
        self.control_thread = None
        self.last_command = None
        self.last_command_time = 0
        self.command_callback = None
        
        # 键盘状态
        self.pressed_keys = set()
        self.key_press_times = {}
        
        # 控制统计
        self.command_count = {
            'forward': 0,
            'backward': 0,
            'left': 0,
            'right': 0,
            'stop': 0
        }
        
        self._log_info("键盘控制器初始化完成")
        
    def _log_info(self, message: str):
        """记录信息日志"""
        if self.logger:
            self.logger.info(message)
        else:
            print(f"[键盘控制] {message}")
            
    def _log_debug(self, message: str):
        """记录调试日志"""
        if self.logger:
            self.logger.debug(message)
        else:
            print(f"[键盘控制] {message}")
            
    def _log_warning(self, message: str):
        """记录警告日志"""
        if self.logger:
            self.logger.warning(message)
        else:
            print(f"[键盘控制] 警告: {message}")
    
    def set_command_callback(self, callback: Callable[[str], None]):
        """设置命令回调函数"""
        self.command_callback = callback
        
    def get_keyboard_input(self) -> Optional[str]:
        """
        获取键盘输入（非阻塞）
        返回按下的键，如果没有按键返回None
        """
        try:
            # 尝试导入不同平台的键盘输入模块
            try:
                # Windows
                import msvcrt
                if msvcrt.kbhit():
                    key = msvcrt.getch().decode('utf-8').lower()
                    return key
            except ImportError:
                try:
                    # Linux/macOS - 使用termios
                    import termios
                    import tty
                    import select
                    
                    old_settings = termios.tcgetattr(sys.stdin)
                    try:
                        tty.setraw(sys.stdin.fileno())
                        if select.select([sys.stdin], [], [], 0.1)[0]:
                            key = sys.stdin.read(1).lower()
                            return key
                    finally:
                        termios.tcsetattr(sys.stdin, termios.TCSADRAIN, old_settings)
                        
                except ImportError:
                    # 备用方案：使用input()但会阻塞
                    pass
                    
        except Exception as e:
            self._log_warning(f"获取键盘输入失败: {e}")
            
        return None
        
    def process_key(self, key: str) -> Optional[str]:
        """
        处理按键并返回对应的机器人命令
        
        Args:
            key: 按下的键
            
        Returns:
            对应的机器人命令，如果无效键则返回None
        """
        if not key:
            return None
            
        key = key.lower()
        
        # 检查是否是控制键
        if key in RobotConfig.KEYBOARD_COMMANDS:
            command_name = RobotConfig.KEYBOARD_COMMANDS[key]
            
            if command_name == "QUIT":
                self._log_info("接收到退出命令")
                return "QUIT"
                
            # 转换为机器人命令
            if command_name in RobotConfig.COMMANDS:
                robot_cmd = RobotConfig.COMMANDS[command_name]
                
                # 更新统计
                cmd_type = self._get_command_type(command_name)
                if cmd_type in self.command_count:
                    self.command_count[cmd_type] += 1
                
                self._log_debug(f"键盘输入: {key} -> 命令: {command_name} -> 机器人: {robot_cmd}")
                return robot_cmd
                
        return None
        
    def _get_command_type(self, command_name: str) -> str:
        """获取命令类型（用于统计）"""
        command_mapping = {
            "MOVE_FORWARD": "forward",
            "MOVE_BACKWARD": "backward", 
            "TURN_LEFT": "left",
            "TURN_RIGHT": "right",
            "STOP": "stop"
        }
        return command_mapping.get(command_name, "unknown")
        
    def send_robot_command(self, robot_cmd: str) -> bool:
        """
        发送命令到机器人
        
        Args:
            robot_cmd: 机器人命令
            
        Returns:
            发送是否成功
        """
        try:
            if self.robot_comm:
                success = self.robot_comm.send(robot_cmd)
                if success:
                    self._log_debug(f"成功发送机器人命令: {robot_cmd}")
                else:
                    self._log_warning(f"发送机器人命令失败: {robot_cmd}")
                return success
            else:
                # 没有机器人连接，只记录日志
                self._log_debug(f"模拟发送机器人命令: {robot_cmd}")
                return True
                
        except Exception as e:
            self._log_warning(f"发送机器人命令异常: {e}")
            return False
            
    def start_keyboard_control(self):
        """启动键盘控制线程"""
        if self.running:
            self._log_warning("键盘控制已经在运行")
            return
            
        self.running = True
        self.control_thread = threading.Thread(target=self._keyboard_control_loop, daemon=True)
        self.control_thread.start()
        self._log_info("键盘控制线程已启动")
        
    def stop_keyboard_control(self):
        """停止键盘控制"""
        self.running = False
        if self.control_thread:
            self.control_thread.join(timeout=1.0)
        self._log_info("键盘控制已停止")
        
    def _keyboard_control_loop(self):
        """键盘控制主循环"""
        self._log_info("键盘控制循环开始")
        self._log_info("控制说明: W-前进, S-后退, A-左转, D-右转, 空格-停止, Q-退出")
        
        try:
            while self.running:
                key = self.get_keyboard_input()
                
                if key:
                    robot_cmd = self.process_key(key)
                    
                    if robot_cmd == "QUIT":
                        self._log_info("接收到退出命令，停止键盘控制")
                        break
                    elif robot_cmd:
                        # 避免重复发送相同命令
                        current_time = time.time()
                        if (robot_cmd != self.last_command or 
                            current_time - self.last_command_time > ControlConfig.KEYBOARD_REPEAT_DELAY):
                            
                            if self.send_robot_command(robot_cmd):
                                self.last_command = robot_cmd
                                self.last_command_time = current_time
                                
                                # 调用回调函数
                                if self.command_callback:
                                    self.command_callback(robot_cmd)
                
                time.sleep(0.05)  # 50ms循环间隔
                
        except Exception as e:
            self._log_warning(f"键盘控制循环异常: {e}")
        finally:
            self.running = False
            self._log_info("键盘控制循环结束")
            
    def get_statistics(self) -> Dict[str, Any]:
        """获取控制统计信息"""
        return {
            "command_count": self.command_count.copy(),
            "last_command": self.last_command,
            "last_command_time": self.last_command_time,
            "running": self.running,
            "total_commands": sum(self.command_count.values())
        }
        
    def print_help(self):
        """打印帮助信息"""
        help_text = """
🎮 键盘控制说明
===============
W 或 w : 前进 (发送01到下位机)
S 或 s : 后退 (发送02到下位机) 
A 或 a : 左转 (发送03到下位机)
D 或 d : 右转 (发送04到下位机)
空格键  : 停止
Q 或 q : 退出控制

📊 当前统计:
"""
        print(help_text)
        stats = self.get_statistics()
        for cmd, count in stats["command_count"].items():
            print(f"  {cmd}: {count} 次")
        print(f"  总命令数: {stats['total_commands']}")

def test_keyboard_controller():
    """测试键盘控制器"""
    print("🧪 键盘控制器测试")
    print("=" * 30)
    
    # 创建控制器实例
    controller = KeyboardController()
    
    # 设置命令回调
    def on_command(cmd):
        print(f"✅ 执行命令: {cmd}")
    
    controller.set_command_callback(on_command)
    
    # 打印帮助
    controller.print_help()
    
    try:
        # 启动键盘控制
        controller.start_keyboard_control()
        
        # 主循环
        while controller.running:
            time.sleep(0.1)
            
    except KeyboardInterrupt:
        print("\n⚠️ 用户中断测试")
    finally:
        controller.stop_keyboard_control()
        print("\n📊 最终统计:")
        stats = controller.get_statistics()
        for cmd, count in stats["command_count"].items():
            if count > 0:
                print(f"  {cmd}: {count} 次")

if __name__ == "__main__":
    test_keyboard_controller()
