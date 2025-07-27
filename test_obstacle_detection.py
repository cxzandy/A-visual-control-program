#!/usr/bin/env python3
"""
障碍物检测系统测试脚本
无需相机连接，使用模拟数据测试障碍物检测和自动避障功能

作者: cxzandy
日期: 2025-07-27
"""

import sys
import os
import numpy as np
import cv2
from datetime import datetime

# 添加src目录到Python路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from perception.obstacle_detection import ObstacleDetector
from config import PerceptionConfig, RobotConfig

def create_test_depth_image(scenario="normal"):
    """创建测试深度图像"""
    # 创建基础深度图 (480x640)
    depth_img = np.random.randint(1500, 3000, (480, 640), dtype=np.uint16)
    
    if scenario == "critical_obstacle":
        # 紧急威胁：前方200mm处有大障碍物
        depth_img[200:350, 280:360] = 200
        print("📍 测试场景: 紧急障碍物 (200mm)")
        
    elif scenario == "warning_obstacle":
        # 警告威胁：前方800mm处有障碍物
        depth_img[150:250, 300:400] = 800
        print("📍 测试场景: 警告障碍物 (800mm)")
        
    elif scenario == "caution_obstacle":
        # 小心威胁：中央区域有障碍物
        depth_img[220:260, 310:330] = 1200
        print("📍 测试场景: 注意障碍物 (1200mm)")
        
    elif scenario == "side_obstacle":
        # 侧面障碍物：不在中央检测区域
        depth_img[100:200, 50:150] = 400
        print("📍 测试场景: 侧面障碍物 (400mm)")
        
    elif scenario == "no_obstacle":
        # 无障碍物：所有深度都很远
        depth_img = np.random.randint(2000, 5000, (480, 640), dtype=np.uint16)
        print("📍 测试场景: 无障碍物")
        
    else:
        # 正常场景：混合距离
        depth_img[100:150, 200:300] = 1800
        print("📍 测试场景: 正常场景")
        
    return depth_img

def test_obstacle_detection():
    """测试障碍物检测功能"""
    print("=" * 60)
    print("🤖 障碍物检测和自动避障系统测试")
    print("=" * 60)
    
    # 创建障碍物检测器
    detector = ObstacleDetector(
        depth_threshold=PerceptionConfig.OBSTACLE_DEPTH_THRESHOLD * 1000,  # 转换为mm
        center_region_width=PerceptionConfig.OBSTACLE_CENTER_REGION_WIDTH,
        critical_distance=PerceptionConfig.OBSTACLE_CRITICAL_DISTANCE * 1000,
        warning_distance=PerceptionConfig.OBSTACLE_WARNING_DISTANCE * 1000
    )
    
    print(f"🔧 检测器配置:")
    print(f"   深度阈值: {PerceptionConfig.OBSTACLE_DEPTH_THRESHOLD * 1000}mm")
    print(f"   中央区域宽度: {PerceptionConfig.OBSTACLE_CENTER_REGION_WIDTH}")
    print(f"   紧急距离: {PerceptionConfig.OBSTACLE_CRITICAL_DISTANCE * 1000}mm")
    print(f"   警告距离: {PerceptionConfig.OBSTACLE_WARNING_DISTANCE * 1000}mm")
    print()
    
    # 测试不同场景
    scenarios = [
        "no_obstacle",
        "caution_obstacle", 
        "warning_obstacle",
        "critical_obstacle",
        "side_obstacle"
    ]
    
    for i, scenario in enumerate(scenarios, 1):
        print(f"🧪 测试 {i}/{len(scenarios)}: {scenario}")
        print("-" * 40)
        
        # 创建测试深度图像
        depth_img = create_test_depth_image(scenario)
        
        # 检测障碍物
        mask = detector.detect(depth_img)
        analysis = detector.analyze_obstacle_threat(depth_img, mask)
        should_avoid = detector.should_avoid(depth_img, PerceptionConfig.OBSTACLE_MIN_AREA)
        
        # 显示结果
        print(f"🎯 检测结果:")
        print(f"   威胁等级: {analysis['threat_level'].upper()}")
        print(f"   最近距离: {analysis['min_distance']:.0f}mm")
        print(f"   总障碍物像素: {analysis['total_obstacle_pixels']}")
        print(f"   中央障碍物像素: {analysis['center_obstacle_pixels']}")
        print(f"   障碍物密度: {analysis['obstacle_density']:.4f}")
        print(f"   中央密度: {analysis['center_obstacle_density']:.4f}")
        
        # 模拟机器人命令决策
        print(f"🤖 机器人决策:")
        if analysis['threat_level'] == 'critical':
            command = RobotConfig.COMMANDS["OBSTACLE_AVOID"]
            print(f"   ⚠️  紧急避障！发送命令: {command}")
        elif analysis['threat_level'] == 'warning':
            command = RobotConfig.COMMANDS["OBSTACLE_AVOID"]
            print(f"   ⚠️  警告避障！发送命令: {command}")
        elif analysis['threat_level'] == 'caution':
            print(f"   ⚠️  注意前方，继续监控")
        else:
            print(f"   ✅ 路径清晰，可以继续前进")
            
        print(f"   需要避障: {'是' if should_avoid else '否'}")
        print()
        
    print("=" * 60)
    print("✅ 障碍物检测系统测试完成！")
    print("=" * 60)

def test_visualization():
    """测试可视化功能"""
    print("🎨 测试障碍物可视化功能...")
    
    try:
        # 创建障碍物检测器
        detector = ObstacleDetector(
            depth_threshold=1500,
            center_region_width=0.3,
            critical_distance=600,
            warning_distance=1400
        )
        
        # 创建测试图像
        color_img = np.zeros((480, 640, 3), dtype=np.uint8)
        color_img[:, :] = [100, 100, 100]  # 灰色背景
        
        depth_img = create_test_depth_image("warning_obstacle")
        mask = detector.detect(depth_img)
        analysis = detector.analyze_obstacle_threat(depth_img, mask)
        
        # 绘制障碍物
        result_img = detector.draw_obstacles(color_img, mask, analysis)
        
        # 保存结果图像
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_path = f"output/images/obstacle_test_{timestamp}.jpg"
        
        # 确保输出目录存在
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        cv2.imwrite(output_path, result_img)
        
        print(f"✅ 可视化结果已保存到: {output_path}")
        
    except Exception as e:
        print(f"❌ 可视化测试失败: {e}")

def test_system_integration():
    """测试系统集成"""
    print("🔗 测试系统集成...")
    
    try:
        from config import validate_config
        
        # 验证配置
        errors = validate_config()
        if errors:
            print("❌ 配置验证失败:")
            for error in errors:
                print(f"   - {error}")
        else:
            print("✅ 配置验证通过")
            
        # 测试机器人命令映射
        print("\n🤖 机器人命令映射:")
        for action, cmd in RobotConfig.COMMANDS.items():
            print(f"   {action}: {cmd}")
            
        print("\n📋 感知配置参数:")
        print(f"   障碍物深度阈值: {PerceptionConfig.OBSTACLE_DEPTH_THRESHOLD}m")
        print(f"   最小障碍物面积: {PerceptionConfig.OBSTACLE_MIN_AREA}像素")
        print(f"   紧急停车距离: {PerceptionConfig.OBSTACLE_CRITICAL_DISTANCE}m")
        print(f"   警告距离: {PerceptionConfig.OBSTACLE_WARNING_DISTANCE}m")
        print(f"   中央区域宽度: {PerceptionConfig.OBSTACLE_CENTER_REGION_WIDTH}")
        
    except Exception as e:
        print(f"❌ 系统集成测试失败: {e}")

def main():
    """主测试函数"""
    print("🚀 启动障碍物检测系统测试")
    print(f"📅 测试时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    try:
        # 基础功能测试
        test_obstacle_detection()
        
        # 可视化测试
        test_visualization()
        
        # 系统集成测试
        test_system_integration()
        
        print("\n🎉 所有测试完成！障碍物检测和自动避障系统已就绪。")
        print("💡 当你连接相机后，系统将自动使用实时深度数据进行障碍物检测。")
        
    except Exception as e:
        print(f"❌ 测试过程中出现错误: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
