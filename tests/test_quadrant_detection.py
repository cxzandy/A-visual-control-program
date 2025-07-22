#!/usr/bin/env python3
"""
管道追踪四象限检测测试
集成在tests目录中的正式测试文件
"""

import cv2
import numpy as np
import sys
import os

# 添加项目路径
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

from src.perception.pipe_tracking import PipeTracker
from src.utils.logger import get_logger

def test_quadrant_detection():
    """测试四象限管道检测功能"""
    logger = get_logger("test_quadrant")
    
    print("🧪 测试四象限管道追踪功能")
    print("="*50)
    
    try:
        # 创建管道追踪器
        tracker = PipeTracker()
        print("✅ 管道追踪器创建成功")
        
        # 创建测试图像
        test_image = create_test_image()
        depth_image = np.ones((480, 640), dtype=np.uint16) * 1000
        print("✅ 测试图像创建成功")
        
        # 执行管道追踪
        print("\n🔍 执行四象限管道检测...")
        line_params_list, global_axis, vis_image = tracker.track(test_image, depth_image)
        
        # 分析结果
        print("\n📊 检测结果分析:")
        if line_params_list:
            detected_count = len([p for p in line_params_list if p is not None])
            print(f"检测到的象限数量: {detected_count}/4")
            
            for i, params in enumerate(line_params_list):
                quadrant_names = ["Q1(右上)", "Q2(左上)", "Q3(左下)", "Q4(右下)"]
                if params is not None:
                    x1, y1, x2, y2 = params
                    length = np.sqrt((x2-x1)**2 + (y2-y1)**2)
                    print(f"  {quadrant_names[i]}: 长度={length:.1f}px")
                else:
                    print(f"  {quadrant_names[i]}: 未检测到")
        
        if global_axis is not None:
            print(f"全局轴线: {len(global_axis)}个点")
        
        # 保存结果
        if vis_image is not None:
            output_dir = os.path.join(project_root, 'output', 'images')
            os.makedirs(output_dir, exist_ok=True)
            output_path = os.path.join(output_dir, 'test_quadrant_detection.jpg')
            cv2.imwrite(output_path, vis_image)
            print(f"✅ 结果已保存: {output_path}")
        
        return True
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        return False

def create_test_image():
    """创建包含管道的测试图像"""
    img = np.zeros((480, 640, 3), dtype=np.uint8)
    img.fill(50)  # 深灰色背景
    
    # 在四个象限绘制模拟管道线条
    # Q1 (右上象限)
    cv2.line(img, (350, 50), (600, 200), (255, 255, 255), 5)
    # Q2 (左上象限)  
    cv2.line(img, (50, 50), (300, 200), (255, 255, 255), 5)
    # Q3 (左下象限)
    cv2.line(img, (50, 280), (300, 450), (255, 255, 255), 5)
    # Q4 (右下象限)
    cv2.line(img, (350, 280), (600, 450), (255, 255, 255), 5)
    
    return img

if __name__ == "__main__":
    success = test_quadrant_detection()
    if success:
        print("\n🎉 四象限检测测试通过!")
        sys.exit(0)
    else:
        print("\n💥 测试失败!")
        sys.exit(1)
