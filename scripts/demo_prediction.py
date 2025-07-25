#!/usr/bin/env python3
"""
方向预测演示脚本
展示管道方向预测功能的使用方法
"""

import sys
import os
import time
import numpy as np
import cv2
from typing import List, Tuple

# 添加src路径
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(__file__)), 'src'))

try:
    from perception.pipe_direction_predictor import PipeDirectionPredictor
    from config import PredictionConfig
except ImportError as e:
    print(f"导入错误: {e}")
    print("请确保在项目根目录运行此脚本")
    sys.exit(1)

def create_simulated_trajectory(trajectory_type: str, num_points: int = 20) -> List[Tuple[float, float]]:
    """创建模拟轨迹数据"""
    points = []
    base_x, base_y = 320, 240  # 图像中心
    
    if trajectory_type == "left_turn":
        # 左转轨迹
        for i in range(num_points):
            angle = np.pi * i / (num_points - 1)  # 0 到 π
            x = base_x + 100 * np.cos(angle)
            y = base_y + 50 * np.sin(angle)
            points.append((x, y))
            
    elif trajectory_type == "right_turn":
        # 右转轨迹
        for i in range(num_points):
            angle = np.pi * i / (num_points - 1)  # 0 到 π
            x = base_x + 100 * np.cos(np.pi - angle)
            y = base_y + 50 * np.sin(angle)
            points.append((x, y))
            
    elif trajectory_type == "up":
        # 上升轨迹
        for i in range(num_points):
            x = base_x + i * 2
            y = base_y - i * 3
            points.append((x, y))
            
    elif trajectory_type == "down":
        # 下降轨迹
        for i in range(num_points):
            x = base_x + i * 2
            y = base_y + i * 3
            points.append((x, y))
            
    elif trajectory_type == "straight":
        # 直线轨迹
        for i in range(num_points):
            x = base_x + i * 5
            y = base_y + np.random.randint(-2, 3)  # 轻微噪声
            points.append((x, y))
            
    return points

def visualize_prediction(points: List[Tuple[float, float]], 
                        prediction: dict, 
                        trajectory_type: str) -> np.ndarray:
    """可视化预测结果"""
    # 创建图像
    img = np.zeros((480, 640, 3), dtype=np.uint8)
    img.fill(30)  # 深色背景
    
    # 绘制轨迹点
    for i, (x, y) in enumerate(points):
        color_intensity = int(255 * (i + 1) / len(points))
        cv2.circle(img, (int(x), int(y)), 3, (color_intensity, color_intensity, 0), -1)
        
        # 连接线
        if i > 0:
            prev_x, prev_y = points[i-1]
            cv2.line(img, (int(prev_x), int(prev_y)), (int(x), int(y)), (100, 100, 100), 1)
    
    # 绘制预测箭头
    if len(points) > 0:
        last_point = points[-1]
        center_x, center_y = int(last_point[0]), int(last_point[1])
        
        direction = prediction.get('direction', 'unknown')
        confidence = prediction.get('confidence', 0.0)
        
        arrow_length = 60
        
        if direction == 'left':
            end_x, end_y = center_x - arrow_length, center_y
            color = (0, 255, 255)  # 黄色
        elif direction == 'right':
            end_x, end_y = center_x + arrow_length, center_y
            color = (0, 255, 255)
        elif direction == 'up':
            end_x, end_y = center_x, center_y - arrow_length
            color = (255, 0, 255)  # 紫色
        elif direction == 'down':
            end_x, end_y = center_x, center_y + arrow_length
            color = (255, 0, 255)
        else:
            end_x, end_y = center_x, center_y
            color = (128, 128, 128)  # 灰色
        
        if direction != 'unknown':
            cv2.arrowedLine(img, (center_x, center_y), (end_x, end_y), 
                           color, 4, tipLength=0.3)
    
    # 添加文本信息
    cv2.putText(img, f"Expected: {trajectory_type.upper()}", 
               (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
    cv2.putText(img, f"Predicted: {prediction.get('direction', 'unknown').upper()}", 
               (10, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
    cv2.putText(img, f"Confidence: {prediction.get('confidence', 0.0):.2f}", 
               (10, 90), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
    cv2.putText(img, f"Turn Angle: {prediction.get('turn_angle', 0.0):.1f}°", 
               (10, 120), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
    
    return img

def demo_direction_prediction():
    """演示方向预测功能"""
    print("🎯 管道方向预测演示")
    print("=" * 50)
    
    # 初始化预测器
    predictor = PipeDirectionPredictor()
    print(f"✅ 预测器初始化完成 - 历史大小: {predictor.history_size}")
    
    # 测试不同类型的轨迹
    trajectory_types = ["straight", "left_turn", "right_turn", "up", "down"]
    
    for traj_type in trajectory_types:
        print(f"\n🔍 测试轨迹类型: {traj_type.upper()}")
        
        # 创建模拟轨迹
        points = create_simulated_trajectory(traj_type, 15)
        
        # 逐步添加点并预测
        for i, point in enumerate(points):
            predictor.add_frame_data(
                center_point=point,
                angle=np.random.uniform(-10, 10),  # 模拟角度噪声
                timestamp=time.time()
            )
            
            # 从第5个点开始预测
            if i >= 4:
                prediction = predictor.predict_direction()
                
                if i == len(points) - 1:  # 最后一个点
                    print(f"  最终预测: {prediction['direction']} "
                          f"(置信度: {prediction['confidence']:.2f})")
                    
                    # 可视化结果
                    img = visualize_prediction(points[:i+1], prediction, traj_type)
                    
                    # 保存图像
                    output_path = f"output/prediction_demo_{traj_type}.jpg"
                    os.makedirs(os.path.dirname(output_path), exist_ok=True)
                    cv2.imwrite(output_path, img)
                    print(f"  可视化保存至: {output_path}")
        
        time.sleep(0.5)  # 短暂延迟
    
    print("\n🎉 演示完成！")
    print("\n📊 配置参数:")
    print(f"  - 历史大小: {PredictionConfig.HISTORY_SIZE}")
    print(f"  - 预测步数: {PredictionConfig.PREDICTION_STEPS}")
    print(f"  - 置信度阈值: {PredictionConfig.CONFIDENCE_THRESHOLD}")
    print(f"  - 最小历史: {PredictionConfig.MIN_HISTORY_FOR_PREDICTION}")

if __name__ == "__main__":
    try:
        demo_direction_prediction()
    except KeyboardInterrupt:
        print("\n\n⚠️  演示中断")
    except Exception as e:
        print(f"\n❌ 演示失败: {e}")
        import traceback
        traceback.print_exc()
