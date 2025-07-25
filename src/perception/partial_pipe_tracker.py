#!/usr/bin/env python3
"""
针对近距离管道跟踪的改进算法
处理只能看到部分管道外壁的情况
"""

import cv2
import numpy as np
from typing import Tuple, Optional, List, Dict
import logging
import time

class PartialPipeTracker:
    """
    部分管道追踪器
    专门处理近距离只能看到部分管道外壁的情况
    """
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        
        # 算法参数
        self.edge_threshold_low = 30
        self.edge_threshold_high = 100
        self.line_min_length = 20
        self.line_max_gap = 15
        self.curve_detection_enabled = True
        
        # 历史信息
        self.last_pipe_center = None
        self.last_pipe_direction = None
        self.tracking_confidence = 0.0
        
    def track_partial_pipe(self, color_image: np.ndarray, depth_image: Optional[np.ndarray] = None) -> Dict:
        """
        追踪部分可见的管道
        
        Args:
            color_image: 彩色图像
            depth_image: 深度图像(可选)
            
        Returns:
            包含追踪结果的字典
        """
        h, w = color_image.shape[:2]
        result = {
            'success': False,
            'pipe_edges': [],
            'estimated_center': None,
            'pipe_direction': None,
            'curvature': 0.0,
            'confidence': 0.0,
            'tracking_method': 'none'
        }
        
        try:
            # 1. 预处理和边缘检测
            gray = cv2.cvtColor(color_image, cv2.COLOR_BGR2GRAY)
            
            # 增强对比度（对于管道表面很重要）
            gray = cv2.equalizeHist(gray)
            
            # 多尺度边缘检测
            edges1 = cv2.Canny(gray, self.edge_threshold_low, self.edge_threshold_high)
            edges2 = cv2.Canny(gray, self.edge_threshold_low//2, self.edge_threshold_high//2)
            edges = cv2.bitwise_or(edges1, edges2)
            
            # 2. 尝试不同的追踪策略
            strategies = [
                self._detect_single_edge_method,
                self._detect_texture_gradient_method,
                self._detect_depth_discontinuity_method,
                self._detect_curved_surface_method
            ]
            
            best_result = result.copy()
            best_confidence = 0.0
            
            for strategy in strategies:
                strategy_result = strategy(edges, color_image, depth_image)
                if strategy_result['confidence'] > best_confidence:
                    best_confidence = strategy_result['confidence']
                    best_result = strategy_result
                    
            # 3. 后处理和轨迹平滑
            if best_result['success']:
                best_result = self._smooth_tracking_result(best_result)
                
            return best_result
            
        except Exception as e:
            self.logger.error(f"部分管道追踪失败: {e}")
            return result
    
    def _detect_single_edge_method(self, edges: np.ndarray, color_image: np.ndarray, 
                                  depth_image: Optional[np.ndarray]) -> Dict:
        """
        单边缘检测方法 - 当只能看到管道的一条边缘时
        """
        h, w = edges.shape
        result = {
            'success': False,
            'pipe_edges': [],
            'estimated_center': None,
            'pipe_direction': None,
            'confidence': 0.0,
            'tracking_method': 'single_edge'
        }
        
        try:
            # 检测长直线段
            lines = cv2.HoughLinesP(
                edges,
                rho=1,
                theta=np.pi/180,
                threshold=30,
                minLineLength=self.line_min_length,
                maxLineGap=self.line_max_gap
            )
            
            if lines is None or len(lines) == 0:
                return result
                
            # 找到最长的直线
            best_line = None
            max_length = 0
            
            for line in lines:
                x1, y1, x2, y2 = line[0]
                length = np.sqrt((x2-x1)**2 + (y2-y1)**2)
                
                # 过滤太短或太接近边界的线
                if (length > max_length and 
                    length > h * 0.3 and  # 至少占图像高度的30%
                    min(x1, x2) > 10 and max(x1, x2) < w-10):
                    
                    max_length = length
                    best_line = line[0]
            
            if best_line is not None:
                x1, y1, x2, y2 = best_line
                
                # 估算管道中心（假设管道有一定宽度）
                line_angle = np.arctan2(y2-y1, x2-x1)
                perpendicular_angle = line_angle + np.pi/2
                
                # 假设管道半径（需要根据实际情况调整）
                estimated_radius = 30  # 像素
                
                # 计算可能的管道中心
                mid_x = (x1 + x2) / 2
                mid_y = (y1 + y2) / 2
                
                center_x1 = mid_x + estimated_radius * np.cos(perpendicular_angle)
                center_y1 = mid_y + estimated_radius * np.sin(perpendicular_angle)
                center_x2 = mid_x - estimated_radius * np.cos(perpendicular_angle)
                center_y2 = mid_y - estimated_radius * np.sin(perpendicular_angle)
                
                # 选择更合理的中心点（基于历史信息或深度信息）
                if self.last_pipe_center is not None:
                    # 选择距离上次中心更近的点
                    dist1 = np.sqrt((center_x1 - self.last_pipe_center[0])**2 + 
                                  (center_y1 - self.last_pipe_center[1])**2)
                    dist2 = np.sqrt((center_x2 - self.last_pipe_center[0])**2 + 
                                  (center_y2 - self.last_pipe_center[1])**2)
                    
                    if dist1 < dist2:
                        estimated_center = (center_x1, center_y1)
                    else:
                        estimated_center = (center_x2, center_y2)
                else:
                    # 默认选择更靠近图像中心的点
                    if abs(center_x1 - w/2) < abs(center_x2 - w/2):
                        estimated_center = (center_x1, center_y1)
                    else:
                        estimated_center = (center_x2, center_y2)
                
                result.update({
                    'success': True,
                    'pipe_edges': [best_line],
                    'estimated_center': estimated_center,
                    'pipe_direction': np.degrees(line_angle),
                    'confidence': min(max_length / (h * 0.8), 1.0),  # 基于线段长度的置信度
                })
                
        except Exception as e:
            self.logger.warning(f"单边缘检测失败: {e}")
            
        return result
    
    def _detect_texture_gradient_method(self, edges: np.ndarray, color_image: np.ndarray,
                                       depth_image: Optional[np.ndarray]) -> Dict:
        """
        纹理梯度检测方法 - 基于管道表面纹理变化
        """
        result = {
            'success': False,
            'confidence': 0.0,
            'tracking_method': 'texture_gradient'
        }
        
        try:
            gray = cv2.cvtColor(color_image, cv2.COLOR_BGR2GRAY)
            
            # 计算纹理梯度
            grad_x = cv2.Sobel(gray, cv2.CV_32F, 1, 0, ksize=3)
            grad_y = cv2.Sobel(gray, cv2.CV_32F, 0, 1, ksize=3)
            
            # 梯度幅值
            gradient_magnitude = np.sqrt(grad_x**2 + grad_y**2)
            
            # 寻找梯度变化剧烈的区域（可能是管道边缘）
            _, grad_thresh = cv2.threshold(gradient_magnitude.astype(np.uint8), 
                                         0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
            
            # 形态学操作连接断开的边缘
            kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (3, 3))
            grad_thresh = cv2.morphologyEx(grad_thresh, cv2.MORPH_CLOSE, kernel)
            
            # 检测轮廓
            contours, _ = cv2.findContours(grad_thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            
            if contours:
                # 找到最大的轮廓
                largest_contour = max(contours, key=cv2.contourArea)
                
                if cv2.contourArea(largest_contour) > 100:  # 面积阈值
                    # 拟合椭圆或直线
                    if len(largest_contour) >= 5:
                        ellipse = cv2.fitEllipse(largest_contour)
                        center = ellipse[0]
                        
                        result.update({
                            'success': True,
                            'estimated_center': center,
                            'pipe_direction': ellipse[2],  # 椭圆的旋转角度
                            'confidence': 0.6,  # 中等置信度
                        })
                        
        except Exception as e:
            self.logger.warning(f"纹理梯度检测失败: {e}")
            
        return result
    
    def _detect_depth_discontinuity_method(self, edges: np.ndarray, color_image: np.ndarray,
                                          depth_image: Optional[np.ndarray]) -> Dict:
        """
        深度不连续性检测方法 - 利用深度信息检测管道边缘
        """
        result = {
            'success': False,
            'confidence': 0.0,
            'tracking_method': 'depth_discontinuity'
        }
        
        if depth_image is None:
            return result
            
        try:
            # 深度梯度计算
            depth_float = depth_image.astype(np.float32)
            depth_float[depth_float == 0] = np.nan  # 处理无效深度值
            
            # 检查是否有有效的深度数据
            valid_depth = depth_float[~np.isnan(depth_float)]
            if len(valid_depth) < 100:  # 如果有效深度点太少
                return result
            
            # 计算深度梯度
            grad_x = cv2.Sobel(depth_float, cv2.CV_32F, 1, 0, ksize=3)
            grad_y = cv2.Sobel(depth_float, cv2.CV_32F, 0, 1, ksize=3)
            
            # 忽略NaN值
            grad_x = np.nan_to_num(grad_x)
            grad_y = np.nan_to_num(grad_y)
            
            depth_gradient = np.sqrt(grad_x**2 + grad_y**2)
            
            # 检查梯度是否有效
            valid_gradients = depth_gradient[depth_gradient > 0]
            if len(valid_gradients) == 0:
                return result
                
            # 阈值化找到深度变化剧烈的区域
            threshold = np.percentile(valid_gradients, 90)
            depth_edges = (depth_gradient > threshold).astype(np.uint8) * 255
            
            # 形态学操作
            kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (3, 3))
            depth_edges = cv2.morphologyEx(depth_edges, cv2.MORPH_CLOSE, kernel)
            
            # 检测线段
            lines = cv2.HoughLinesP(
                depth_edges,
                rho=1,
                theta=np.pi/180,
                threshold=20,
                minLineLength=30,
                maxLineGap=20
            )
            
            if lines is not None and len(lines) > 0:
                # 找到最长的线段
                best_line = max(lines, key=lambda line: 
                               np.sqrt((line[0][2]-line[0][0])**2 + (line[0][3]-line[0][1])**2))
                
                x1, y1, x2, y2 = best_line[0]
                center_x = (x1 + x2) / 2
                center_y = (y1 + y2) / 2
                
                result.update({
                    'success': True,
                    'estimated_center': (center_x, center_y),
                    'pipe_direction': np.degrees(np.arctan2(y2-y1, x2-x1)),
                    'confidence': 0.8,  # 深度信息通常比较可靠
                })
                
        except Exception as e:
            self.logger.warning(f"深度不连续性检测失败: {e}")
            
        return result
    
    def _detect_curved_surface_method(self, edges: np.ndarray, color_image: np.ndarray,
                                     depth_image: Optional[np.ndarray]) -> Dict:
        """
        曲面检测方法 - 检测管道的弯曲表面
        """
        result = {
            'success': False,
            'confidence': 0.0,
            'tracking_method': 'curved_surface'
        }
        
        if not self.curve_detection_enabled:
            return result
            
        try:
            gray = cv2.cvtColor(color_image, cv2.COLOR_BGR2GRAY)
            
            # 使用高斯拉普拉斯算子检测曲面特征
            blurred = cv2.GaussianBlur(gray, (5, 5), 1.0)
            laplacian = cv2.Laplacian(blurred, cv2.CV_32F, ksize=3)
            
            # 寻找二阶导数的零交叉点（曲面特征）
            zero_crossings = np.zeros_like(laplacian)
            
            # 检测零交叉
            for i in range(1, laplacian.shape[0]-1):
                for j in range(1, laplacian.shape[1]-1):
                    if (laplacian[i, j] * laplacian[i-1, j] < 0 or
                        laplacian[i, j] * laplacian[i+1, j] < 0 or
                        laplacian[i, j] * laplacian[i, j-1] < 0 or
                        laplacian[i, j] * laplacian[i, j+1] < 0):
                        zero_crossings[i, j] = 255
            
            # 连接零交叉点形成曲线
            kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3))
            zero_crossings = cv2.morphologyEx(zero_crossings.astype(np.uint8), 
                                            cv2.MORPH_CLOSE, kernel)
            
            # 检测轮廓
            contours, _ = cv2.findContours(zero_crossings, cv2.RETR_EXTERNAL, 
                                         cv2.CHAIN_APPROX_SIMPLE)
            
            if contours:
                # 找到最大的轮廓
                largest_contour = max(contours, key=cv2.contourArea)
                
                if len(largest_contour) >= 5:
                    # 拟合椭圆
                    ellipse = cv2.fitEllipse(largest_contour)
                    center = ellipse[0]
                    
                    # 计算曲率
                    moments = cv2.moments(largest_contour)
                    if moments['m00'] != 0:
                        cx = moments['m10'] / moments['m00']
                        cy = moments['m01'] / moments['m00']
                        
                        result.update({
                            'success': True,
                            'estimated_center': (cx, cy),
                            'curvature': 1.0 / max(ellipse[1]),  # 简化的曲率计算
                            'pipe_direction': ellipse[2],  # 椭圆的旋转角度
                            'confidence': 0.5,
                        })
                        
        except Exception as e:
            self.logger.warning(f"曲面检测失败: {e}")
            
        return result
    
    def _smooth_tracking_result(self, result: Dict) -> Dict:
        """
        平滑追踪结果，利用历史信息
        """
        if not result['success']:
            return result
            
        # 时间平滑
        alpha = 0.7  # 平滑系数
        
        if self.last_pipe_center is not None and result['estimated_center'] is not None:
            # 平滑中心点
            current_center = result['estimated_center']
            smoothed_center = (
                alpha * current_center[0] + (1-alpha) * self.last_pipe_center[0],
                alpha * current_center[1] + (1-alpha) * self.last_pipe_center[1]
            )
            result['estimated_center'] = smoothed_center
            
        if self.last_pipe_direction is not None and result['pipe_direction'] is not None:
            # 平滑方向角度
            current_dir = result['pipe_direction']
            smoothed_dir = alpha * current_dir + (1-alpha) * self.last_pipe_direction
            result['pipe_direction'] = smoothed_dir
            
        # 更新历史信息
        if result['estimated_center'] is not None:
            self.last_pipe_center = result['estimated_center']
        if result['pipe_direction'] is not None:
            self.last_pipe_direction = result['pipe_direction']
            
        return result
    
    def visualize_result(self, image: np.ndarray, result: Dict) -> np.ndarray:
        """
        可视化追踪结果
        """
        vis_image = image.copy()
        
        if not result['success']:
            cv2.putText(vis_image, "No pipe detected", (10, 30),
                       cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)
            return vis_image
            
        # 绘制检测到的边缘
        if result['pipe_edges']:
            for edge in result['pipe_edges']:
                x1, y1, x2, y2 = edge
                cv2.line(vis_image, (x1, y1), (x2, y2), (0, 255, 0), 3)
                
        # 绘制估算的中心点
        if result['estimated_center'] is not None:
            center = (int(result['estimated_center'][0]), int(result['estimated_center'][1]))
            cv2.circle(vis_image, center, 8, (255, 0, 0), -1)
            cv2.circle(vis_image, center, 15, (255, 0, 0), 2)
            
        # 绘制方向指示
        if result['pipe_direction'] is not None and result['estimated_center'] is not None:
            center = result['estimated_center']
            angle_rad = np.radians(result['pipe_direction'])
            length = 50
            
            end_x = int(center[0] + length * np.cos(angle_rad))
            end_y = int(center[1] + length * np.sin(angle_rad))
            
            cv2.arrowedLine(vis_image, 
                          (int(center[0]), int(center[1])), 
                          (end_x, end_y), 
                          (0, 255, 255), 3, tipLength=0.3)
            
        # 添加信息文本
        cv2.putText(vis_image, f"Method: {result['tracking_method']}", 
                   (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
        cv2.putText(vis_image, f"Confidence: {result['confidence']:.2f}", 
                   (10, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
        
        if result.get('curvature', 0) > 0:
            cv2.putText(vis_image, f"Curvature: {result['curvature']:.3f}", 
                       (10, 90), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
            
        return vis_image


if __name__ == "__main__":
    # 测试代码
    import os
    
    tracker = PartialPipeTracker()
    
    # 创建测试图像
    test_image = np.zeros((480, 640, 3), dtype=np.uint8)
    test_image.fill(50)  # 深灰色背景
    
    # 模拟部分管道边缘
    cv2.line(test_image, (100, 50), (120, 450), (255, 255, 255), 3)  # 一条白色边缘
    
    # 测试追踪
    result = tracker.track_partial_pipe(test_image)
    
    print("追踪结果:")
    for key, value in result.items():
        print(f"  {key}: {value}")
    
    # 可视化
    vis = tracker.visualize_result(test_image, result)
    
    # 保存结果
    os.makedirs("output", exist_ok=True)
    cv2.imwrite("output/partial_pipe_test.jpg", vis)
    print("可视化结果保存至: output/partial_pipe_test.jpg")
