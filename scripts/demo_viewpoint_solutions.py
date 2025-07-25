#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
视角限制解决方案演示
Demo script for viewpoint limitation solutions
"""

import sys
import os
import numpy as np
import cv2
from pathlib import Path
import time

# 添加项目路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / "src"))

# 导入模块
from perception.pipe_tracking import PipeTracker
from perception.partial_pipe_tracker import PartialPipeTracker
from config import CameraConfig, PerceptionConfig

def create_demo_scenarios():
    """创建演示场景"""
    scenarios = {}
    
    # 场景1: 摄像头过于接近管道上方，只能看到上边缘
    scenarios['close_top'] = {
        'name': '近距离上方视角',
        'description': '摄像头接近管道上方，只能看到上边缘',
        'image': np.ones((480, 640, 3), dtype=np.uint8) * 50,
        'challenge': '只有部分管道信息可见'
    }
    
    # 在图像上绘制部分管道边缘
    image = scenarios['close_top']['image']
    # 绘制管道上边缘 - 更真实的管道外观
    cv2.ellipse(image, (320, 240), (200, 50), 0, 0, 180, (150, 150, 150), 12)
    cv2.ellipse(image, (320, 240), (180, 40), 0, 0, 180, (120, 120, 120), 8)
    
    # 添加管道表面纹理
    for i in range(120, 520, 25):
        cv2.line(image, (i, 245), (i+15, 255), (100, 100, 100), 3)
        cv2.line(image, (i+5, 250), (i+20, 260), (90, 90, 90), 2)
    
    # 添加一些噪声和光照变化
    noise = np.random.normal(0, 15, image.shape).astype(np.int16)
    image = np.clip(image.astype(np.int16) + noise, 0, 255).astype(np.uint8)
    
    # 场景2: 摄像头在管道侧面，只能看到侧面纹理
    scenarios['side_view'] = {
        'name': '侧面视角',
        'description': '摄像头在管道侧面，主要看到表面纹理',
        'image': np.ones((480, 640, 3), dtype=np.uint8) * 40,
        'challenge': '缺少完整的管道轮廓'
    }
    
    # 绘制侧面纹理 - 更复杂的纹理模式
    image = scenarios['side_view']['image']
    for y in range(180, 300, 3):
        # 创建波浪状的管道表面
        intensity = 70 + int(30 * np.sin((y-180) * 0.2)) + int(15 * np.cos((y-180) * 0.5))
        for x in range(0, 640, 20):
            x_offset = int(10 * np.sin((x + y) * 0.1))
            cv2.line(image, (x, y), (x+15, y), (intensity, intensity, intensity), 2)
    
    # 添加管道边缘的部分轮廓
    cv2.line(image, (50, 200), (590, 220), (120, 120, 120), 4)
    cv2.line(image, (60, 280), (600, 290), (100, 100, 100), 3)
    
    # 场景3: 管道在视野边缘，部分被遮挡
    scenarios['partial_occlusion'] = {
        'name': '部分遮挡',
        'description': '管道部分在视野外或被遮挡',
        'image': np.ones((480, 640, 3), dtype=np.uint8) * 60,
        'challenge': '信息不完整且有干扰'
    }
    
    # 绘制部分管道和遮挡
    image = scenarios['partial_occlusion']['image']
    # 绘制完整的管道轮廓
    cv2.ellipse(image, (320, 300), (180, 60), 0, 0, 360, (110, 110, 110), 8)
    cv2.ellipse(image, (320, 300), (160, 50), 0, 0, 360, (90, 90, 90), 4)
    
    # 添加管道内部纹理
    for i in range(160, 480, 30):
        cv2.ellipse(image, (320, 300), (i//2, 25), 0, 0, 360, (80, 80, 80), 2)
    
    # 添加遮挡物
    cv2.rectangle(image, (450, 200), (640, 400), (20, 20, 20), -1)
    cv2.rectangle(image, (0, 350), (200, 480), (30, 30, 30), -1)
    
    return scenarios

def demonstrate_tracking_methods():
    """演示不同的追踪方法"""
    print("🎬 视角限制解决方案演示")
    print("=" * 60)
    
    # 初始化追踪器
    try:
        main_tracker = PipeTracker()
        partial_tracker = PartialPipeTracker()
        print("✅ 追踪器初始化成功\n")
    except Exception as e:
        print(f"❌ 追踪器初始化失败: {e}")
        return
    
    # 创建演示场景
    scenarios = create_demo_scenarios()
    
    print("📋 演示场景说明:")
    print("-" * 40)
    for key, scenario in scenarios.items():
        print(f"  🎯 {scenario['name']}: {scenario['description']}")
        print(f"     挑战: {scenario['challenge']}")
    print()
    
    # 对每个场景进行演示
    for scenario_name, scenario in scenarios.items():
        print(f"🔍 场景: {scenario['name']}")
        print("-" * 30)
        
        image = scenario['image']
        edges = cv2.Canny(cv2.cvtColor(image, cv2.COLOR_BGR2GRAY), 50, 150)
        
        # 测试传统四象限方法
        start_time = time.time()
        try:
            tracking_result, pipe_edges, mask, stats = main_tracker.track(image, None)
            traditional_time = time.time() - start_time
            traditional_success = tracking_result is not None and len(tracking_result) > 0
        except Exception as e:
            traditional_success = False
            traditional_time = 0
        
        # 测试部分视角方法
        start_time = time.time()
        try:
            partial_result = partial_tracker.track_partial_pipe(edges, image, None)
            partial_time = time.time() - start_time
            partial_success = partial_result.get('success', False)
            partial_method = partial_result.get('tracking_method', 'unknown')
            partial_confidence = partial_result.get('confidence', 0.0)
        except Exception as e:
            partial_success = False
            partial_time = 0
            partial_method = 'error'
            partial_confidence = 0.0
        
        # 测试自适应方法（包含部分视角）
        start_time = time.time()
        try:
            # 先尝试传统方法
            tracking_result, pipe_edges, mask, stats = main_tracker.track(image, None)
            if tracking_result is None or len(tracking_result) == 0:
                # 如果传统方法失败，使用部分视角方法
                partial_result = partial_tracker.track_partial_pipe(edges, image, None)
                adaptive_success = partial_result.get('success', False)
            else:
                adaptive_success = True
            adaptive_time = time.time() - start_time
        except:
            adaptive_success = False
            adaptive_time = 0
        
        # 显示结果
        print(f"  🔧 传统四象限方法: {'✅ 成功' if traditional_success else '❌ 失败'} ({traditional_time*1000:.1f}ms)")
        print(f"  🧠 部分视角方法: {'✅ 成功' if partial_success else '❌ 失败'} ({partial_time*1000:.1f}ms)")
        if partial_success:
            print(f"     └─ 检测算法: {partial_method}, 置信度: {partial_confidence:.2f}")
        print(f"  🎯 自适应方法: {'✅ 成功' if adaptive_success else '❌ 失败'} ({adaptive_time*1000:.1f}ms)")
        
        # 性能评估
        success_count = sum([traditional_success, partial_success, adaptive_success])
        if success_count == 3:
            print(f"  📊 评估: 🎉 所有方法都成功!")
        elif success_count >= 2:
            print(f"  📊 评估: ✅ 多数方法成功 ({success_count}/3)")
        elif success_count == 1:
            print(f"  📊 评估: ⚠️  只有部分方法成功 ({success_count}/3)")
        else:
            print(f"  📊 评估: ❌ 所有方法都失败")
        
        print()
    
    print("=" * 60)
    print("💡 关键技术特点:")
    print("1. 🔄 自适应切换: 根据场景自动选择最佳算法")
    print("2. 🎯 部分视角处理: 专门针对视角限制的算法")
    print("3. 📊 置信度评估: 实时评估检测结果可靠性")
    print("4. ⚡ 实时性能: 所有算法都能实时运行")
    print("5. 🛡️ 鲁棒性: 在困难条件下仍能工作")
    print()
    
    print("🚀 部署建议:")
    print("- 在80公里远程监控中，使用自适应方法获得最佳效果")
    print("- 根据摄像头位置和管道特征调整算法参数")
    print("- 结合多个检测结果提高整体可靠性")
    print("- 定期校准和更新检测阈值")

if __name__ == "__main__":
    demonstrate_tracking_methods()
