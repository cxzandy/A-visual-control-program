import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import numpy as np
import cv2
from src.perception.obstacle_detection import ObstacleDetector
from src.perception.pipe_tracking import PipeTracker

def test_obstacle_detector():
    # 构造一个简单的深度图，部分区域为障碍物
    depth_img = np.zeros((100, 100), dtype=np.uint16)
    depth_img[30:70, 30:70] = 500  # 设定障碍物区域，深度小于阈值
    detector = ObstacleDetector(depth_threshold=1000)
    mask = detector.detect(depth_img)
    # 检查掩码是否正确
    assert np.sum(mask == 255) > 0
    # 检查障碍物区域是否被检测
    assert np.all(mask[40:60, 40:60] == 255)
    # 检查非障碍物区域
    assert np.all(mask[:20, :20] == 0)

def test_pipe_tracker():
    # 构造模拟彩色图像和深度图
    H, W = 100, 100
    color_img = np.zeros((H, W, 3), dtype=np.uint8)
    depth_img = np.zeros((H, W), dtype=np.uint16)
    # 在中间画一条“管道”边缘
    for i in range(20, 80):
        color_img[i, 50] = [255, 255, 255]
        depth_img[i, 50] = 800
    tracker = PipeTracker(depth_threshold=1500, camera_intrinsics=[600.0, 600.0, W/2, H/2])
    line_params_list, global_axis_points, vis = tracker.track(color_img, depth_img)
    # 检查是否拟合出直线
    assert any([params is not None for params in line_params_list])
    # 检查全局轴线拟合结果
    if global_axis_points is not None:
        assert global_axis_points.shape[1] == 3

if __name__ == "__main__":
    test_obstacle_detector()
    test_pipe_tracker()
    print("感知模块测试通过！")
