#!/usr/bin/env python3
"""
转向控制测试脚本
简单测试转向控制管理器的功能
"""

import sys
import os
import cv2
import time
import numpy as np

# 添加src目录到Python路径
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(project_root, 'src'))

from control.turn_control import TurnControlManager
from config import ControlConfig

def test_turn_control():
    """测试转向控制功能"""
    print("🚀 开始测试转向控制功能")
    print("=" * 50)
    
    # 创建转向控制管理器
    turn_controller = TurnControlManager()
    
    # 创建一个简单的测试图像
    test_image = np.zeros((480, 640, 3), dtype=np.uint8)
    
    # 模拟不同的线条参数来测试转向检测
    test_cases = [
        # (线条参数, 全局轴向, 期望方向)
        ([[100, 100, 200, 200]], None, "直行或右转"),  # 向右倾斜的线
        ([[200, 200, 100, 100]], None, "直行或左转"),  # 向左倾斜的线
        ([[100, 100, 100, 200]], None, "直行"),        # 垂直线
        ([[100, 100, 200, 100]], None, "直行"),        # 水平线
        (None, None, "无检测"),                        # 无线条
    ]
    
    print("\n📊 测试不同的线条参数:")
    for i, (line_params, global_axis, expected) in enumerate(test_cases):
        print(f"\n测试用例 {i+1}: 期望 {expected}")
        
        result = turn_controller.process_frame(test_image, line_params, global_axis)
        
        print(f"  检测结果: {result['direction']}")
        print(f"  置信度: {result['confidence']:.2f}")
        print(f"  处理时间: {result['processing_time']:.3f}s")
        
        time.sleep(0.1)
    
    print("\n📈 测试控制模式切换:")
    
    # 测试模式切换
    print(f"当前模式: {turn_controller.control_mode}")
    
    turn_controller.set_control_mode("manual")
    print(f"切换后模式: {turn_controller.control_mode}")
    
    # 测试手动命令
    print("\n🎮 测试手动控制命令:")
    manual_commands = ["left", "right", "forward", "stop"]
    
    for cmd in manual_commands:
        turn_controller.set_manual_command(cmd)
        manual_cmd = turn_controller.get_manual_command()
        print(f"  设置命令: {cmd} -> 获取命令: {manual_cmd}")
        time.sleep(0.5)
    
    # 切换回自动模式
    turn_controller.set_control_mode("auto")
    print(f"\n切换回自动模式: {turn_controller.control_mode}")
    
    # 显示统计信息
    print("\n📊 统计信息:")
    stats = turn_controller.get_statistics()
    for key, value in stats.items():
        print(f"  {key}: {value}")
    
    print("\n✅ 转向控制测试完成!")

def test_with_camera():
    """使用摄像头进行实时测试"""
    print("\n🎥 开始摄像头实时测试 (按'q'退出, 按'm'切换模式)")
    
    # 尝试打开摄像头
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        print("❌ 无法打开摄像头")
        return
    
    turn_controller = TurnControlManager()
    
    try:
        while True:
            ret, frame = cap.read()
            if not ret:
                break
            
            # 简单的线条检测（这里使用Hough变换作为示例）
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            edges = cv2.Canny(gray, 50, 150)
            lines = cv2.HoughLinesP(edges, 1, np.pi/180, threshold=100, 
                                  minLineLength=100, maxLineGap=10)
            
            # 转换为我们的格式
            line_params = []
            if lines is not None:
                for line in lines[:5]:  # 最多使用5条线
                    x1, y1, x2, y2 = line[0]
                    line_params.append([x1, y1, x2, y2])
                    # 在图像上绘制线条
                    cv2.line(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
            else:
                line_params = None
            
            # 处理转向控制
            result = turn_controller.process_frame(frame, line_params, None)
            
            # 在图像上显示结果
            cv2.putText(frame, f"Direction: {result['direction']}", 
                       (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 255), 2)
            cv2.putText(frame, f"Confidence: {result['confidence']:.2f}", 
                       (10, 70), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 255), 2)
            cv2.putText(frame, f"Mode: {turn_controller.control_mode}", 
                       (10, 110), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 0), 2)
            
            if turn_controller.control_mode == "manual":
                manual_cmd = turn_controller.get_manual_command()
                cv2.putText(frame, f"Manual: {manual_cmd}", 
                           (10, 150), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 0, 255), 2)
            
            cv2.imshow("Turn Control Test", frame)
            
            key = cv2.waitKey(1) & 0xFF
            if key == ord('q'):
                break
            elif key == ord('m'):
                # 切换模式
                new_mode = "manual" if turn_controller.control_mode == "auto" else "auto"
                turn_controller.set_control_mode(new_mode)
                print(f"模式切换为: {new_mode}")
            elif key == ord('a') and turn_controller.control_mode == "manual":
                turn_controller.set_manual_command("left")
            elif key == ord('d') and turn_controller.control_mode == "manual":
                turn_controller.set_manual_command("right")
            elif key == ord('w') and turn_controller.control_mode == "manual":
                turn_controller.set_manual_command("forward")
            elif key == ord('s') and turn_controller.control_mode == "manual":
                turn_controller.set_manual_command("stop")
                
    finally:
        cap.release()
        cv2.destroyAllWindows()
        
        # 显示最终统计
        print("\n📊 最终统计:")
        stats = turn_controller.get_statistics()
        for key, value in stats.items():
            print(f"  {key}: {value}")

def main():
    """主函数"""
    print("🔧 Tiaozhanbei2.0 转向控制测试程序")
    print("选择测试模式:")
    print("1. 基础功能测试")
    print("2. 摄像头实时测试")
    
    try:
        choice = input("请输入选择 (1-2): ").strip()
        
        if choice == "1":
            test_turn_control()
        elif choice == "2":
            test_with_camera()
        else:
            print("无效选择")
            
    except KeyboardInterrupt:
        print("\n\n👋 测试中断")
    except Exception as e:
        print(f"\n❌ 测试出错: {e}")

if __name__ == "__main__":
    main()
