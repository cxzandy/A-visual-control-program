#!/usr/bin/env python3
"""
障碍物检测和自动避障系统测试脚本
无需真实相机连接

功能：
- 测试增强的障碍物检测算法
- 模拟各种障碍物场景
- 验证自动避障决策逻辑
- 展示完整的控制流程

作者: cxzandy
日期: 2025-07-27
"""

import sys
import os
import numpy as np
import cv2
import time
from datetime import datetime

# 添加src目录到Python路径
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), 'src'))

from perception.obstacle_detection import ObstacleDetector
from config import PerceptionConfig, RobotConfig

class ObstacleAvoidanceSimulator:
    """障碍物避障模拟器"""
    
    def __init__(self):
        """初始化模拟器"""
        print("🚀 初始化障碍物避障模拟器...")
        
        # 创建增强的障碍物检测器
        self.obstacle_detector = ObstacleDetector(
            depth_threshold=PerceptionConfig.OBSTACLE_DEPTH_THRESHOLD * 1000,  # 转换为mm
            center_region_width=PerceptionConfig.OBSTACLE_CENTER_REGION_WIDTH,
            critical_distance=PerceptionConfig.OBSTACLE_CRITICAL_DISTANCE * 1000,  # 转换为mm
            warning_distance=PerceptionConfig.OBSTACLE_WARNING_DISTANCE * 1000  # 转换为mm
        )
        
        # 统计信息
        self.test_results = {
            "total_tests": 0,
            "obstacle_detections": 0,
            "avoidance_triggers": 0,
            "threat_levels": {"none": 0, "caution": 0, "warning": 0, "critical": 0}
        }
        
        print("✅ 障碍物避障模拟器初始化完成")
    
    def create_test_depth_image(self, scenario="random"):
        """创建测试深度图像"""
        # 基础深度图像 (640x480)
        depth_image = np.random.randint(1500, 3000, (480, 640), dtype=np.uint16)
        
        if scenario == "clear_path":
            # 场景1：无障碍物
            pass
            
        elif scenario == "near_obstacle":
            # 场景2：近距离障碍物（紧急避障）
            depth_image[200:300, 280:360] = 400  # 400mm处的障碍物
            
        elif scenario == "medium_obstacle":
            # 场景3：中等距离障碍物（警告避障）
            depth_image[150:250, 250:390] = 1200  # 1200mm处的障碍物
            
        elif scenario == "side_obstacle":
            # 场景4：侧面障碍物
            depth_image[100:200, 50:150] = 800  # 左侧障碍物
            depth_image[280:380, 490:590] = 800  # 右侧障碍物
            
        elif scenario == "center_obstacle":
            # 场景5：正前方障碍物
            center_x = 320
            width = int(640 * PerceptionConfig.OBSTACLE_CENTER_REGION_WIDTH)
            start_x = center_x - width // 2
            end_x = center_x + width // 2
            depth_image[220:280, start_x:end_x] = 900  # 中央区域障碍物
            
        elif scenario == "multiple_obstacles":
            # 场景6：多个障碍物
            depth_image[100:150, 100:180] = 500    # 近距离障碍物
            depth_image[300:350, 460:540] = 1300   # 中距离障碍物
            depth_image[200:240, 300:340] = 800    # 中央障碍物
            
        else:  # random
            # 随机障碍物场景
            num_obstacles = np.random.randint(1, 4)
            for _ in range(num_obstacles):
                h = np.random.randint(50, 100)
                w = np.random.randint(50, 120)
                y = np.random.randint(0, 480 - h)
                x = np.random.randint(0, 640 - w)
                distance = np.random.randint(300, 1400)
                depth_image[y:y+h, x:x+w] = distance
        
        return depth_image
    
    def create_test_color_image(self, depth_image):
        """根据深度图像创建对应的彩色图像"""
        # 将深度图转换为彩色可视化
        depth_normalized = cv2.normalize(depth_image, None, 0, 255, cv2.NORM_MINMAX)
        color_image = cv2.applyColorMap(depth_normalized.astype(np.uint8), cv2.COLORMAP_JET)
        return color_image
    
    def simulate_robot_command(self, analysis, mask):
        """模拟机器人命令决策"""
        import numpy as np
        
        command = None
        reason = ""
        
        # 智能安全检查：障碍物威胁分析
        if analysis:
            threat_level = analysis["threat_level"]
            min_distance = analysis["min_distance"]
            
            if threat_level == "critical":
                command = RobotConfig.COMMANDS["OBSTACLE_AVOID"]  # 05
                reason = f"紧急避障！检测到严重威胁，距离: {min_distance:.0f}mm"
                self.test_results["avoidance_triggers"] += 1
                
            elif threat_level == "warning":
                command = RobotConfig.COMMANDS["OBSTACLE_AVOID"]  # 05
                reason = f"警告避障！检测到障碍物威胁，距离: {min_distance:.0f}mm"
                self.test_results["avoidance_triggers"] += 1
                
            elif threat_level == "caution":
                command = RobotConfig.COMMANDS["MOVE_FORWARD"]  # 01 (谨慎前进)
                reason = f"注意：前方有障碍物，距离: {min_distance:.0f}mm，谨慎前进"
                
            else:
                command = RobotConfig.COMMANDS["MOVE_FORWARD"]  # 01
                reason = "路径清晰，正常前进"
        
        # 备用安全检查：基于面积的传统检测
        elif np.sum(mask > 0) > PerceptionConfig.OBSTACLE_MIN_AREA:
            command = RobotConfig.COMMANDS["OBSTACLE_AVOID"]  # 05
            reason = "检测到障碍物（传统检测），发送避障命令"
            self.test_results["avoidance_triggers"] += 1
        else:
            command = RobotConfig.COMMANDS["MOVE_FORWARD"]  # 01
            reason = "无障碍物检测，正常前进"
        
        return command, reason
    
    def test_scenario(self, scenario_name, depth_image, display=True):
        """测试单个场景"""
        print(f"\n📊 测试场景: {scenario_name}")
        print("-" * 40)
        
        # 障碍物检测
        mask = self.obstacle_detector.detect(depth_image)
        analysis = self.obstacle_detector.analyze_obstacle_threat(depth_image, mask)
        
        # 更新统计
        self.test_results["total_tests"] += 1
        if analysis["total_obstacle_pixels"] > 0:
            self.test_results["obstacle_detections"] += 1
        self.test_results["threat_levels"][analysis["threat_level"]] += 1
        
        # 模拟机器人决策
        command, reason = self.simulate_robot_command(analysis, mask)
        
        # 输出结果
        print(f"威胁等级: {analysis['threat_level'].upper()}")
        print(f"最近距离: {analysis['min_distance']:.0f}mm")
        print(f"障碍物像素: {analysis['total_obstacle_pixels']}")
        print(f"中央区域像素: {analysis['center_obstacle_pixels']}")
        print(f"障碍物密度: {analysis['obstacle_density']:.4f}")
        print(f"机器人命令: {command}")
        print(f"决策原因: {reason}")
        
        # 可视化
        if display:
            color_image = self.create_test_color_image(depth_image)
            vis_image = self.obstacle_detector.draw_obstacles(color_image, mask, analysis)
            
            # 添加场景信息
            cv2.putText(vis_image, scenario_name, (10, 25), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 255), 2)
            cv2.putText(vis_image, f"Command: {command}", (10, vis_image.shape[0] - 10), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
            
            return vis_image
        
        return None
    
    def run_comprehensive_test(self):
        """运行综合测试"""
        print("🧪 开始障碍物检测和自动避障综合测试\n")
        
        # 测试场景列表
        scenarios = [
            ("清晰路径", "clear_path"),
            ("近距离障碍物", "near_obstacle"),
            ("中距离障碍物", "medium_obstacle"),
            ("侧面障碍物", "side_obstacle"),
            ("正前方障碍物", "center_obstacle"),
            ("多个障碍物", "multiple_obstacles"),
            ("随机场景1", "random"),
            ("随机场景2", "random"),
            ("随机场景3", "random")
        ]
        
        all_results = []
        
        for scenario_name, scenario_type in scenarios:
            # 创建测试数据
            depth_image = self.create_test_depth_image(scenario_type)
            
            # 测试场景
            vis_image = self.test_scenario(scenario_name, depth_image, display=True)
            
            if vis_image is not None:
                all_results.append((scenario_name, vis_image))
        
        # 创建结果拼接图像
        if all_results:
            self.create_result_summary(all_results)
        
        # 打印统计信息
        self.print_test_statistics()
    
    def create_result_summary(self, results):
        """创建测试结果总览"""
        if not results:
            return
        
        # 计算网格布局
        num_images = len(results)
        cols = 3
        rows = (num_images + cols - 1) // cols
        
        # 调整图像大小
        target_height, target_width = 200, 300
        resized_images = []
        
        for name, img in results:
            resized = cv2.resize(img, (target_width, target_height))
            # 添加标题
            cv2.putText(resized, name, (5, 20), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
            resized_images.append(resized)
        
        # 填充空白图像
        while len(resized_images) < rows * cols:
            blank = np.zeros((target_height, target_width, 3), dtype=np.uint8)
            resized_images.append(blank)
        
        # 创建网格
        grid_rows = []
        for r in range(rows):
            start_idx = r * cols
            end_idx = start_idx + cols
            row_images = resized_images[start_idx:end_idx]
            grid_row = np.hstack(row_images)
            grid_rows.append(grid_row)
        
        # 合并所有行
        if grid_rows:
            final_grid = np.vstack(grid_rows)
            
            # 添加总体标题
            title_height = 60
            title_img = np.zeros((title_height, final_grid.shape[1], 3), dtype=np.uint8)
            title_text = "障碍物检测和自动避障测试结果总览"
            cv2.putText(title_img, title_text, (20, 35), 
                       cv2.FONT_HERSHEY_SIMPLEX, 1.2, (0, 255, 255), 2)
            
            final_result = np.vstack([title_img, final_grid])
            
            # 保存结果
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_path = f"obstacle_avoidance_test_results_{timestamp}.jpg"
            cv2.imwrite(output_path, final_result)
            print(f"\n💾 测试结果已保存: {output_path}")
            
            # 显示结果（可选）
            try:
                cv2.imshow("障碍物避障测试结果", final_result)
                print("📺 按任意键关闭显示窗口...")
                cv2.waitKey(0)
                cv2.destroyAllWindows()
            except:
                print("⚠️  无法显示图像（可能是因为没有图形界面）")
    
    def print_test_statistics(self):
        """打印测试统计信息"""
        print("\n" + "="*60)
        print("📈 障碍物检测和自动避障测试统计")
        print("="*60)
        print(f"总测试次数: {self.test_results['total_tests']}")
        print(f"障碍物检测次数: {self.test_results['obstacle_detections']}")
        print(f"自动避障触发次数: {self.test_results['avoidance_triggers']}")
        print(f"避障触发率: {self.test_results['avoidance_triggers']/self.test_results['total_tests']*100:.1f}%")
        print()
        print("威胁等级分布:")
        for level, count in self.test_results['threat_levels'].items():
            percentage = count / self.test_results['total_tests'] * 100
            print(f"  {level.capitalize()}: {count} ({percentage:.1f}%)")
        print("="*60)
        
        # 评估测试结果
        if self.test_results['avoidance_triggers'] > 0:
            print("✅ 自动避障系统功能正常！")
        else:
            print("⚠️  未触发避障，可能需要调整参数")
        
        if self.test_results['obstacle_detections'] > 0:
            print("✅ 障碍物检测系统功能正常！")
        else:
            print("⚠️  未检测到障碍物，可能需要检查算法")

def main():
    """主函数"""
    print("🤖 障碍物检测和自动避障系统测试")
    print("=" * 50)
    
    try:
        # 创建模拟器
        simulator = ObstacleAvoidanceSimulator()
        
        # 运行综合测试
        simulator.run_comprehensive_test()
        
        print("\n🎉 所有测试完成！")
        return 0
        
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
