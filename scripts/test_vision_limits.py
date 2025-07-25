#!/usr/bin/env python3
"""
测试视角限制下的管道追踪能力
模拟近距离只能看到部分管道的情况
"""

import sys
import os
import numpy as np
import cv2
from pathlib import Path

# 添加项目路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / "src"))

# 导入模块
from perception.pipe_tracking import PipeTracker
from perception.partial_pipe_tracker import PartialPipeTracker
from config import CameraConfig, PerceptionConfig

def create_partial_pipe_scenarios():
    """创建不同的部分管道视角场景"""
    scenarios = {}
    
    # 场景1: 只能看到管道的上边缘
    img1 = np.zeros((480, 640, 3), dtype=np.uint8)
    img1.fill(40)  # 深色背景
    
    # 模拟管道上边缘
    cv2.line(img1, (50, 200), (590, 280), (255, 255, 255), 4)
    # 添加一些噪声
    for i in range(100):
        x, y = np.random.randint(0, 640), np.random.randint(0, 480)
        cv2.circle(img1, (x, y), 1, (100, 100, 100), -1)
    
    scenarios['top_edge_only'] = {
        'image': img1,
        'description': '只能看到管道上边缘',
        'expected_detection': True
    }
    
    # 场景2: 只能看到管道的侧面纹理
    img2 = np.zeros((480, 640, 3), dtype=np.uint8)
    img2.fill(50)
    
    # 模拟管道侧面纹理
    for y in range(150, 350):
        for x in range(100, 540):
            if abs(y - (150 + (x-100) * 0.3)) < 80:  # 弯曲的管道表面
                intensity = 120 + np.random.randint(-30, 30)
                img2[y, x] = (intensity, intensity, intensity)
    
    scenarios['side_texture'] = {
        'image': img2,
        'description': '只能看到管道侧面纹理',
        'expected_detection': False  # 更困难的情况
    }
    
    # 场景3: 管道部分被遮挡
    img3 = np.zeros((480, 640, 3), dtype=np.uint8)
    img3.fill(30)
    
    # 管道的可见部分
    cv2.ellipse(img3, (320, 240), (150, 80), 0, 0, 120, (200, 200, 200), 3)
    cv2.ellipse(img3, (320, 240), (120, 60), 0, 0, 120, (150, 150, 150), 2)
    
    # 遮挡物
    cv2.rectangle(img3, (400, 180), (640, 300), (80, 80, 80), -1)
    
    scenarios['partially_occluded'] = {
        'image': img3,
        'description': '管道部分被遮挡',
        'expected_detection': True
    }
    
    # 场景4: 管道弯曲，只能看到一小段
    img4 = np.zeros((480, 640, 3), dtype=np.uint8)
    img4.fill(45)
    
    # 弯曲管道的一小段
    points = []
    for t in np.linspace(0, np.pi/3, 20):
        x = int(320 + 100 * np.cos(t))
        y = int(240 + 100 * np.sin(t))
        points.append((x, y))
    
    for i in range(len(points)-1):
        cv2.line(img4, points[i], points[i+1], (255, 255, 255), 3)
    
    scenarios['curved_segment'] = {
        'image': img4,
        'description': '弯曲管道的一小段',
        'expected_detection': True
    }
    
    # 场景5: 非常近距离，只能看到管道表面细节
    img5 = np.zeros((480, 640, 3), dtype=np.uint8)
    
    # 模拟管道表面的金属纹理
    for y in range(480):
        for x in range(640):
            # 创建金属纹理
            base_intensity = 100 + 30 * np.sin(x * 0.1) + 20 * np.sin(y * 0.15)
            noise = np.random.randint(-20, 20)
            intensity = max(0, min(255, int(base_intensity + noise)))
            img5[y, x] = (intensity, intensity, intensity)
    
    # 添加一些表面特征线
    cv2.line(img5, (0, 200), (640, 220), (150, 150, 150), 2)
    cv2.line(img5, (0, 280), (640, 300), (150, 150, 150), 2)
    
    scenarios['surface_detail'] = {
        'image': img5,
        'description': '极近距离管道表面细节',
        'expected_detection': False  # 最困难的情况
    }
    
    return scenarios

def test_tracking_algorithms():
    """测试不同算法在各种视角限制下的表现"""
    print("🔍 测试视角限制下的管道追踪算法")
    print("=" * 60)
    
    try:
        # 初始化追踪器
        main_tracker = PipeTracker()
        partial_tracker = PartialPipeTracker()
        
        print("✅ 追踪器初始化成功")
        
    except Exception as e:
        print(f"❌ 追踪器初始化失败: {e}")
        return False
    
    # 创建测试场景
    scenarios = create_partial_pipe_scenarios()
    
    results = {}
    
    for scenario_name, scenario_data in scenarios.items():
        print(f"\n🧪 测试场景: {scenario_data['description']}")
        print("-" * 40)
        
        image = scenario_data['image']
        expected = scenario_data['expected_detection']
        
        # 创建虚拟深度图像
        depth_image = np.ones((480, 640), dtype=np.uint16) * 1000  # 1米距离
        
        scenario_results = {}
        
        # 1. 测试主追踪器（四象限方法）
        try:
            main_tracker.set_tracking_mode("full_quadrant")
            line_params, global_axis, vis_main, prediction = main_tracker.track(image, depth_image)
            
            main_success = (line_params is not None and 
                           any(p is not None for p in line_params if line_params))
            
            scenario_results['main_tracker'] = {
                'success': main_success,
                'method': 'quadrant',
                'detection_count': len([p for p in (line_params or []) if p is not None])
            }
            
            print(f"  四象限方法: {'✅ 成功' if main_success else '❌ 失败'}")
            
        except Exception as e:
            scenario_results['main_tracker'] = {'success': False, 'error': str(e)}
            print(f"  四象限方法: ❌ 异常 - {e}")
        
        # 2. 测试部分视角追踪器
        try:
            partial_result = partial_tracker.track_partial_pipe(image, depth_image)
            partial_success = partial_result['success']
            
            scenario_results['partial_tracker'] = {
                'success': partial_success,
                'method': partial_result.get('tracking_method', 'unknown'),
                'confidence': partial_result.get('confidence', 0.0)
            }
            
            print(f"  部分视角方法: {'✅ 成功' if partial_success else '❌ 失败'}")
            if partial_success:
                print(f"    检测方法: {partial_result['tracking_method']}")
                print(f"    置信度: {partial_result['confidence']:.2f}")
            
        except Exception as e:
            scenario_results['partial_tracker'] = {'success': False, 'error': str(e)}
            print(f"  部分视角方法: ❌ 异常 - {e}")
        
        # 3. 测试自适应追踪器
        try:
            main_tracker.set_tracking_mode("auto")
            line_params, global_axis, vis_auto, prediction = main_tracker.track(image, depth_image)
            
            auto_success = (line_params is not None and 
                           any(p is not None for p in line_params if line_params)) or \
                          (prediction is not None and prediction.get('confidence', 0) > 0)
            
            scenario_results['auto_tracker'] = {
                'success': auto_success,
                'method': 'adaptive',
                'tracking_mode': main_tracker.tracking_mode
            }
            
            print(f"  自适应方法: {'✅ 成功' if auto_success else '❌ 失败'}")
            
        except Exception as e:
            scenario_results['auto_tracker'] = {'success': False, 'error': str(e)}
            print(f"  自适应方法: ❌ 异常 - {e}")
        
        # 4. 保存可视化结果
        try:
            output_dir = "output/vision_test"
            os.makedirs(output_dir, exist_ok=True)
            
            # 保存原始图像
            cv2.imwrite(f"{output_dir}/{scenario_name}_original.jpg", image)
            
            # 保存主追踪器结果
            if 'vis_main' in locals():
                cv2.imwrite(f"{output_dir}/{scenario_name}_main_tracker.jpg", vis_main)
            
            # 保存部分追踪器结果
            if partial_result['success']:
                vis_partial = partial_tracker.visualize_result(image.copy(), partial_result)
                cv2.imwrite(f"{output_dir}/{scenario_name}_partial_tracker.jpg", vis_partial)
            
            # 保存自适应追踪器结果
            if 'vis_auto' in locals():
                cv2.imwrite(f"{output_dir}/{scenario_name}_auto_tracker.jpg", vis_auto)
                
        except Exception as e:
            print(f"    保存可视化失败: {e}")
        
        results[scenario_name] = scenario_results
        
        # 评估结果
        any_success = any(result.get('success', False) 
                         for result in scenario_results.values())
        
        if expected and any_success:
            print(f"  📊 评估: ✅ 符合预期（成功检测）")
        elif not expected and not any_success:
            print(f"  📊 评估: ✅ 符合预期（预期困难）")
        elif expected and not any_success:
            print(f"  📊 评估: ⚠️  未达预期（应该能检测但失败了）")
        else:
            print(f"  📊 评估: 🎉 超出预期（困难场景也检测成功了）")
    
    # 生成总结报告
    print(f"\n{'='*60}")
    print("📋 测试总结报告")
    print("=" * 60)
    
    algorithm_stats = {
        'main_tracker': {'success': 0, 'total': 0},
        'partial_tracker': {'success': 0, 'total': 0},
        'auto_tracker': {'success': 0, 'total': 0}
    }
    
    for scenario_name, scenario_results in results.items():
        for algorithm, result in scenario_results.items():
            if 'success' in result:
                algorithm_stats[algorithm]['total'] += 1
                if result['success']:
                    algorithm_stats[algorithm]['success'] += 1
    
    for algorithm, stats in algorithm_stats.items():
        if stats['total'] > 0:
            success_rate = stats['success'] / stats['total'] * 100
            print(f"{algorithm:15}: {stats['success']}/{stats['total']} ({success_rate:.1f}%)")
    
    # 算法建议
    print(f"\n💡 算法改进建议:")
    print("1. 四象限方法适用于完整管道轮廓可见的情况")
    print("2. 部分视角方法能处理边缘检测和纹理分析")
    print("3. 自适应方法能在不同场景间自动切换")
    print("4. 建议在实际应用中结合深度信息提高鲁棒性")
    print("5. 对于极近距离场景，考虑使用表面纹理特征")
    
    return True

if __name__ == "__main__":
    try:
        success = test_tracking_algorithms()
        if success:
            print("\n🎉 视角限制测试完成！")
            print("📁 可视化结果保存在 output/vision_test/ 目录")
        else:
            print("\n❌ 测试失败")
    except KeyboardInterrupt:
        print("\n⚠️  测试中断")
    except Exception as e:
        print(f"\n❌ 测试异常: {e}")
        import traceback
        traceback.print_exc()
