#!/usr/bin/env python3
"""
障碍物检测和避障系统演示
支持无相机模式，使用模拟数据演示完整功能

作者: cxzandy  
日期: 2025-07-27
"""

import sys
import os
import time
import threading
import numpy as np
from datetime import datetime

# 添加src目录到Python路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from perception.obstacle_detection import ObstacleDetector
from control.turn_control import TurnControlManager
from config import PerceptionConfig, RobotConfig, ControlConfig

class MockRobotCommunication:
    """模拟机器人通信"""
    
    def __init__(self):
        self.command_log = []
        
    def send(self, command):
        """发送命令到机器人"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.command_log.append((timestamp, command))
        print(f"🤖 [{timestamp}] 发送机器人命令: {command}")
        
        # 模拟命令处理时间
        time.sleep(0.1)
        
    def get_command_history(self):
        """获取命令历史"""
        return self.command_log.copy()

class ObstacleAvoidanceDemo:
    """障碍物检测和避障演示"""
    
    def __init__(self):
        self.obstacle_detector = ObstacleDetector(
            depth_threshold=PerceptionConfig.OBSTACLE_DEPTH_THRESHOLD * 1000,
            center_region_width=PerceptionConfig.OBSTACLE_CENTER_REGION_WIDTH,
            critical_distance=PerceptionConfig.OBSTACLE_CRITICAL_DISTANCE * 1000,
            warning_distance=PerceptionConfig.OBSTACLE_WARNING_DISTANCE * 1000
        )
        
        self.turn_controller = TurnControlManager()
        self.robot = MockRobotCommunication()
        self.running = False
        
    def create_scenario_depth_image(self, scenario_id):
        """创建不同场景的深度图像"""
        scenarios = {
            0: ("安全区域", lambda: np.random.randint(2000, 5000, (480, 640), dtype=np.uint16)),
            1: ("远距离障碍物", self._create_far_obstacle),
            2: ("警告距离障碍物", self._create_warning_obstacle),  
            3: ("紧急距离障碍物", self._create_critical_obstacle),
            4: ("左侧障碍物", self._create_left_obstacle),
            5: ("右侧障碍物", self._create_right_obstacle),
            6: ("中央大障碍物", self._create_central_obstacle),
            7: ("多个小障碍物", self._create_multiple_obstacles)
        }
        
        scenario_name, creator = scenarios[scenario_id % len(scenarios)]
        return scenario_name, creator()
    
    def _create_far_obstacle(self):
        """远距离障碍物"""
        depth_img = np.random.randint(2000, 4000, (480, 640), dtype=np.uint16)
        depth_img[200:250, 300:350] = 1800
        return depth_img
        
    def _create_warning_obstacle(self):
        """警告距离障碍物"""
        depth_img = np.random.randint(2000, 4000, (480, 640), dtype=np.uint16)
        depth_img[150:300, 280:360] = 900
        return depth_img
        
    def _create_critical_obstacle(self):
        """紧急距离障碍物"""
        depth_img = np.random.randint(2000, 4000, (480, 640), dtype=np.uint16)
        depth_img[180:350, 290:350] = 300
        return depth_img
        
    def _create_left_obstacle(self):
        """左侧障碍物"""
        depth_img = np.random.randint(2000, 4000, (480, 640), dtype=np.uint16)
        depth_img[200:300, 100:200] = 600
        return depth_img
        
    def _create_right_obstacle(self):
        """右侧障碍物"""
        depth_img = np.random.randint(2000, 4000, (480, 640), dtype=np.uint16)
        depth_img[200:300, 440:540] = 600
        return depth_img
        
    def _create_central_obstacle(self):
        """中央大障碍物"""
        depth_img = np.random.randint(2000, 4000, (480, 640), dtype=np.uint16)
        depth_img[150:350, 250:390] = 450
        return depth_img
        
    def _create_multiple_obstacles(self):
        """多个小障碍物"""
        depth_img = np.random.randint(2000, 4000, (480, 640), dtype=np.uint16)
        # 左前方障碍物
        depth_img[120:180, 200:260] = 700
        # 右前方障碍物  
        depth_img[180:240, 380:440] = 800
        # 中央远处障碍物
        depth_img[100:150, 300:350] = 1600
        return depth_img
    
    def process_frame(self, depth_image, scenario_name):
        """处理单帧数据"""
        # 障碍物检测
        obstacle_mask = self.obstacle_detector.detect(depth_image)
        obstacle_analysis = self.obstacle_detector.analyze_obstacle_threat(depth_image, obstacle_mask)
        
        # 模拟转向检测结果
        mock_turn_result = {
            "direction": "straight",
            "confidence": 0.8,
            "angle": 0.0
        }
        
        # 智能避障决策
        command_sent = self._make_avoidance_decision(obstacle_analysis, mock_turn_result)
        
        # 输出结果
        self._print_frame_results(scenario_name, obstacle_analysis, command_sent)
        
        return obstacle_analysis, command_sent
    
    def _make_avoidance_decision(self, obstacle_analysis, turn_result):
        """智能避障决策逻辑"""
        threat_level = obstacle_analysis["threat_level"]
        min_distance = obstacle_analysis["min_distance"]
        
        if threat_level == "critical":
            self.robot.send(RobotConfig.COMMANDS["OBSTACLE_AVOID"])
            return f"紧急避障 (05) - 距离: {min_distance:.0f}mm"
            
        elif threat_level == "warning":
            self.robot.send(RobotConfig.COMMANDS["OBSTACLE_AVOID"])
            return f"警告避障 (05) - 距离: {min_distance:.0f}mm"
            
        elif threat_level == "caution":
            # 谨慎前进，降低速度
            return f"谨慎前进 - 距离: {min_distance:.0f}mm"
            
        else:
            # 正常前进
            direction = turn_result["direction"]
            confidence = turn_result["confidence"]
            
            if confidence > ControlConfig.MIN_CONFIDENCE_THRESHOLD:
                if direction == "left":
                    self.robot.send(RobotConfig.COMMANDS["TURN_LEFT"])
                    return f"左转 (03) - 置信度: {confidence:.2f}"
                elif direction == "right":
                    self.robot.send(RobotConfig.COMMANDS["TURN_RIGHT"])
                    return f"右转 (04) - 置信度: {confidence:.2f}"
                else:
                    self.robot.send(RobotConfig.COMMANDS["MOVE_FORWARD"])
                    return f"直行 (01) - 置信度: {confidence:.2f}"
            else:
                self.robot.send(RobotConfig.COMMANDS["STOP"])
                return "停止 - 置信度不足"
    
    def _print_frame_results(self, scenario_name, analysis, command):
        """打印帧处理结果"""
        print(f"📋 场景: {scenario_name}")
        print(f"   🎯 威胁等级: {analysis['threat_level'].upper()}")
        print(f"   📏 最近距离: {analysis['min_distance']:.0f}mm")
        print(f"   🔍 障碍物像素: {analysis['total_obstacle_pixels']}")
        print(f"   🎯 中央区域像素: {analysis['center_obstacle_pixels']}")
        print(f"   🤖 机器人动作: {command}")
        print("-" * 50)
    
    def run_demo(self, duration_seconds=30):
        """运行演示"""
        print("🚀 启动障碍物检测和自动避障演示")
        print(f"⏱️  演示时长: {duration_seconds}秒")
        print(f"🔧 检测器配置:")
        print(f"   深度阈值: {PerceptionConfig.OBSTACLE_DEPTH_THRESHOLD * 1000}mm")
        print(f"   紧急距离: {PerceptionConfig.OBSTACLE_CRITICAL_DISTANCE * 1000}mm")
        print(f"   警告距离: {PerceptionConfig.OBSTACLE_WARNING_DISTANCE * 1000}mm")
        print("=" * 60)
        
        self.running = True
        start_time = time.time()
        frame_count = 0
        scenario_id = 0
        
        try:
            while self.running and (time.time() - start_time) < duration_seconds:
                # 创建场景数据
                scenario_name, depth_image = self.create_scenario_depth_image(scenario_id)
                
                # 处理帧
                self.process_frame(depth_image, scenario_name)
                
                # 更新计数器
                frame_count += 1
                scenario_id += 1
                
                # 控制帧率
                time.sleep(2.0)  # 每2秒处理一帧，便于观察
                
        except KeyboardInterrupt:
            print("\n⚠️  用户中断演示")
            
        finally:
            self.running = False
            
        # 显示统计信息
        self._print_demo_summary(frame_count, time.time() - start_time)
    
    def _print_demo_summary(self, frame_count, elapsed_time):
        """打印演示总结"""
        print("\n" + "=" * 60)
        print("📊 演示统计信息")
        print("=" * 60)
        print(f"处理帧数: {frame_count}")
        print(f"运行时间: {elapsed_time:.1f}秒")
        print(f"平均帧率: {frame_count / elapsed_time:.2f} FPS")
        
        # 命令历史
        command_history = self.robot.get_command_history()
        print(f"\n🤖 机器人命令历史 ({len(command_history)} 条):")
        for timestamp, command in command_history[-10:]:  # 显示最后10条
            print(f"   [{timestamp}] {command}")
            
        if len(command_history) > 10:
            print(f"   ... 还有 {len(command_history) - 10} 条命令")
        
        # 命令统计
        command_counts = {}
        for _, command in command_history:
            command_counts[command] = command_counts.get(command, 0) + 1
            
        print(f"\n📈 命令使用统计:")
        for command, count in sorted(command_counts.items()):
            percentage = (count / len(command_history)) * 100 if command_history else 0
            print(f"   {command}: {count} 次 ({percentage:.1f}%)")

def main():
    """主函数"""
    print("🎭 障碍物检测和自动避障系统演示")
    print(f"📅 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    try:
        demo = ObstacleAvoidanceDemo()
        
        print("💡 这个演示将模拟不同的障碍物场景，展示系统如何:")
        print("   1. 检测障碍物威胁等级")
        print("   2. 分析障碍物位置和距离")
        print("   3. 自动发送避障命令给机器人")
        print("   4. 记录所有决策过程")
        print()
        print("🔄 演示将循环播放8种不同场景...")
        print("⌨️  按 Ctrl+C 可随时停止演示")
        print()
        
        # 倒计时开始
        for i in range(3, 0, -1):
            print(f"⏳ {i} 秒后开始...")
            time.sleep(1)
        print("🚀 开始演示!\n")
        
        # 运行演示
        demo.run_demo(duration_seconds=60)  # 运行60秒
        
        print("\n✅ 演示完成！")
        print("💡 当你连接真实相机后，系统将使用实时深度数据执行相同的避障逻辑。")
        
    except Exception as e:
        print(f"❌ 演示过程中出现错误: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
