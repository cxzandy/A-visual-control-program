#!/usr/bin/env python3
"""
管道偏转方向预测器
基于历史轨迹数据预测管道的偏转方向和角度
"""

import numpy as np
import cv2
import time
import logging
from collections import deque
from typing import List, Tuple, Optional, Dict, Any

# 导入配置
try:
    from config import PredictionConfig
except ImportError:
    try:
        from ..config import PredictionConfig
    except ImportError:
        # 如果无法导入配置，使用默认值
        class PredictionConfig:
            HISTORY_SIZE = 15
        MIN_HISTORY_FOR_PREDICTION = 5
        PREDICTION_STEPS = 8
        CONFIDENCE_THRESHOLD = 0.5
        CURVATURE_WINDOW = 3
        CURVE_THRESHOLD = 0.1
        DIRECTION_ANGLE_THRESHOLD = 30
        MOVEMENT_THRESHOLD = 5.0
        TREND_WINDOW = 5
        TREND_THRESHOLD = 0.3
        PREDICTION_ARROW_LENGTH = 50
        PREDICTION_COLORS = {
            'left': (0, 255, 255), 'right': (0, 255, 255),
            'up': (255, 0, 255), 'down': (255, 0, 255),
            'unknown': (128, 128, 128)
        }

class PipeDirectionPredictor:
    """管道偏转方向预测器"""
    
    def __init__(self, history_size: int = None, prediction_steps: int = None):
        """
        初始化预测器
        
        Args:
            history_size: 历史数据保存帧数
            prediction_steps: 预测步数（帧数）
        """
        # 使用配置参数或默认值
        self.history_size = history_size or PredictionConfig.HISTORY_SIZE
        self.prediction_steps = prediction_steps or PredictionConfig.PREDICTION_STEPS
        
        # 历史数据存储
        self.axis_history = deque(maxlen=self.history_size)
        self.direction_history = deque(maxlen=self.history_size)
        self.curvature_history = deque(maxlen=self.history_size)
        
        # 预测状态
        self.last_prediction = None
        self.prediction_confidence = 0.0
        
        self.logger = logging.getLogger(__name__)
        
    def add_frame_data(self, center_point: Tuple[float, float] = None, 
                      angle: float = None, axis_points: np.ndarray = None, 
                      timestamp: float = None):
        """
        添加当前帧的管道数据（兼容性方法）
        
        Args:
            center_point: 管道中心点 (x, y)
            angle: 管道角度 (度)
            axis_points: 管道轴线点坐标 (N, 2) - 可选
            timestamp: 时间戳
        """
        if timestamp is None:
            timestamp = time.time()
        
        # 如果有轴线点，使用它们
        if axis_points is not None and len(axis_points) >= 2:
            direction = self._calculate_direction(axis_points)
            curvature = self._calculate_curvature(axis_points)
            points = axis_points.copy()
        elif center_point is not None:
            # 否则使用中心点和角度创建简单的方向向量
            if angle is not None:
                angle_rad = np.radians(angle)
                direction = np.array([np.cos(angle_rad), np.sin(angle_rad)])
            else:
                direction = np.array([1.0, 0.0])  # 默认水平方向
            
            curvature = 0.0  # 无法计算曲率
            points = np.array([center_point])
        else:
            return  # 没有有效数据
        
        frame_data = {
            'points': points,
            'center': center_point,
            'angle': angle,
            'timestamp': timestamp,
            'direction': direction,
            'curvature': curvature
        }
        
        self.axis_history.append(frame_data)
        
        # 记录调试信息
        self.logger.debug(f"添加帧数据: 中心={center_point}, 角度={angle}, "
                        f"方向={direction}, 曲率={curvature:.4f}")
    
    def add_axis_data(self, axis_points: np.ndarray, timestamp: float = None):
        """
        添加当前帧的管道轴线数据（原有方法）
        
        Args:
            axis_points: 管道轴线点坐标 (N, 2)
            timestamp: 时间戳
        """
        if timestamp is None:
            timestamp = time.time()
            
        if len(axis_points) >= 2:
            # 计算管道方向向量和曲率
            direction = self._calculate_direction(axis_points)
            curvature = self._calculate_curvature(axis_points)
            center_point = np.mean(axis_points, axis=0)
            
            frame_data = {
                'points': axis_points.copy(),
                'center': tuple(center_point),
                'timestamp': timestamp,
                'direction': direction,
                'curvature': curvature
            }
            
            self.axis_history.append(frame_data)
            
            # 记录调试信息
            self.logger.debug(f"添加轴线数据: 点数={len(axis_points)}, "
                            f"方向={direction}, 曲率={curvature:.4f}")
            
    def _calculate_direction(self, points: np.ndarray) -> np.ndarray:
        """计算管道主方向向量"""
        if len(points) < 2:
            return np.array([0.0, 0.0])
        
        try:
            # 使用主成分分析找到主方向
            center = np.mean(points, axis=0)
            centered_points = points - center
            
            # 计算协方差矩阵
            cov_matrix = np.cov(centered_points.T)
            eigenvalues, eigenvectors = np.linalg.eig(cov_matrix)
            
            # 主方向是最大特征值对应的特征向量
            main_direction = eigenvectors[:, np.argmax(eigenvalues)]
            
            # 确保方向向量的一致性（朝向图像下方）
            if main_direction[1] < 0:
                main_direction = -main_direction
                
            return main_direction.astype(np.float64)
            
        except Exception as e:
            self.logger.warning(f"方向计算失败: {e}")
            return np.array([0.0, 1.0])  # 默认向下
    
    def _calculate_curvature(self, points: np.ndarray) -> float:
        """计算管道曲率"""
        if len(points) < 3:
            return 0.0
        
        try:
            # 使用三点法计算曲率
            curvatures = []
            for i in range(1, len(points) - 1):
                p1, p2, p3 = points[i-1], points[i], points[i+1]
                
                # 计算三点的曲率
                a = np.linalg.norm(p2 - p1)
                b = np.linalg.norm(p3 - p2)
                c = np.linalg.norm(p3 - p1)
                
                if a > 1e-6 and b > 1e-6 and c > 1e-6:
                    # 海伦公式计算三角形面积
                    s = (a + b + c) / 2
                    area_squared = s * (s - a) * (s - b) * (s - c)
                    if area_squared > 0:
                        area = np.sqrt(area_squared)
                        curvature = 4 * area / (a * b * c)
                        curvatures.append(curvature)
            
            return np.mean(curvatures) if curvatures else 0.0
            
        except Exception as e:
            self.logger.warning(f"曲率计算失败: {e}")
            return 0.0
    
    def predict_direction(self) -> Dict[str, Any]:
        """
        预测管道偏转方向
        
        Returns:
            预测结果字典
        """
        if len(self.axis_history) < PredictionConfig.MIN_HISTORY_FOR_PREDICTION:
            return {
                'direction': 'unknown',
                'confidence': 0.0,
                'turn_angle': 0.0,
                'curvature': 0.0,
                'status': 'insufficient_data'
            }
        
        try:
            # 分析最近的轨迹变化
            recent_data = list(self.axis_history)[-PredictionConfig.TREND_WINDOW:]
            
            if len(recent_data) < 2:
                return {'direction': 'unknown', 'confidence': 0.0}
            
            # 计算中心点的移动趋势
            centers = []
            for frame in recent_data:
                if 'center' in frame and frame['center']:
                    centers.append(frame['center'])
                elif len(frame['points']) > 0:
                    center = np.mean(frame['points'], axis=0)
                    centers.append(tuple(center))
            
            if len(centers) < 2:
                return {'direction': 'unknown', 'confidence': 0.0}
            
            # 计算移动方向
            start_center = np.array(centers[0])
            end_center = np.array(centers[-1])
            movement_vector = end_center - start_center
            movement_magnitude = np.linalg.norm(movement_vector)
            
            if movement_magnitude < PredictionConfig.MOVEMENT_THRESHOLD:
                return {'direction': 'straight', 'confidence': 0.8}
            
            # 归一化移动向量
            movement_direction = movement_vector / movement_magnitude
            
            # 计算移动角度
            angle_rad = np.arctan2(movement_direction[1], movement_direction[0])
            angle_deg = np.degrees(angle_rad)
            
            # 确定方向
            direction, confidence = self._classify_direction(angle_deg, movement_magnitude)
            
            # 计算平均曲率
            curvatures = [frame.get('curvature', 0.0) for frame in recent_data]
            avg_curvature = np.mean(curvatures) if curvatures else 0.0
            
            result = {
                'direction': direction,
                'confidence': confidence,
                'turn_angle': angle_deg,
                'curvature': avg_curvature,
                'movement_magnitude': movement_magnitude,
                'status': 'predicted'
            }
            
            self.last_prediction = result
            self.prediction_confidence = confidence
            
            return result
            
        except Exception as e:
            self.logger.error(f"方向预测失败: {e}")
            return {
                'direction': 'unknown',
                'confidence': 0.0,
                'turn_angle': 0.0,
                'curvature': 0.0,
                'status': 'error'
            }
    
    def _classify_direction(self, angle_deg: float, magnitude: float) -> Tuple[str, float]:
        """根据角度分类方向"""
        # 标准化角度到 [-180, 180]
        angle_deg = (angle_deg + 180) % 360 - 180
        
        # 计算置信度（基于移动距离）
        base_confidence = min(magnitude / 50.0, 1.0)  # 移动越大置信度越高
        
        # 方向分类
        angle_threshold = PredictionConfig.DIRECTION_ANGLE_THRESHOLD
        
        if -angle_threshold <= angle_deg <= angle_threshold:
            direction = 'right'
            confidence = base_confidence * 0.9  # 水平移动置信度稍高
        elif 180 - angle_threshold <= angle_deg or angle_deg <= -180 + angle_threshold:
            direction = 'left'
            confidence = base_confidence * 0.9
        elif 90 - angle_threshold <= angle_deg <= 90 + angle_threshold:
            direction = 'down'
            confidence = base_confidence * 0.8  # 垂直移动置信度稍低
        elif -90 - angle_threshold <= angle_deg <= -90 + angle_threshold:
            direction = 'up'
            confidence = base_confidence * 0.8
        else:
            # 对角线移动，选择主要方向
            if abs(angle_deg) < 90:
                direction = 'right' if angle_deg > 0 else 'down' if angle_deg > -45 else 'up'
            else:
                direction = 'left' if angle_deg > 0 else 'down' if angle_deg < -135 else 'up'
            confidence = base_confidence * 0.6
        
        return direction, min(confidence, 1.0)
    
    def _analyze_direction_trend(self, directions: List[np.ndarray]) -> Dict[str, float]:
        """分析方向变化趋势"""
        if len(directions) < 2:
            return {'trend': 'stable', 'angle_change': 0.0, 'magnitude': 0.0}
        
        try:
            angle_changes = []
            for i in range(1, len(directions)):
                prev_dir = directions[i-1]
                curr_dir = directions[i]
                
                # 计算角度变化
                dot_product = np.clip(np.dot(prev_dir, curr_dir), -1.0, 1.0)
                angle_change = np.arccos(dot_product)
                
                # 判断左转还是右转（使用叉积）
                cross_product = np.cross(prev_dir, curr_dir)
                if cross_product > 0:
                    angle_change = -angle_change  # 左转为负
                
                angle_changes.append(angle_change)
            
            avg_change = np.mean(angle_changes)
            change_magnitude = abs(avg_change)
            
            # 分类趋势
            if change_magnitude < 0.05:  # 约3度
                trend = 'straight'
            elif avg_change > 0:
                trend = 'turning_right'
            else:
                trend = 'turning_left'
            
            return {
                'trend': trend,
                'angle_change': avg_change,
                'magnitude': change_magnitude
            }
            
        except Exception as e:
            self.logger.warning(f"趋势分析失败: {e}")
            return {'trend': 'stable', 'angle_change': 0.0, 'magnitude': 0.0}
    
    def _make_prediction(self, direction_change: Dict[str, Any], curvature: float) -> Dict[str, Any]:
        """生成最终预测结果"""
        trend = direction_change['trend']
        angle_change = direction_change['angle_change']
        magnitude = direction_change['magnitude']
        
        # 基于趋势和曲率计算置信度
        base_confidence = min(1.0, magnitude * 20 + curvature * 10)
        data_confidence = min(1.0, len(self.axis_history) / self.history_size)
        confidence = base_confidence * data_confidence
        
        # 估算转弯角度
        predicted_angle = angle_change * self.prediction_steps
        
        # 估算到转弯点的距离（基于当前曲率）
        if curvature > 0.001:
            estimated_distance = min(1000.0, 1.0 / curvature)  # 限制最大距离
        else:
            estimated_distance = 1000.0  # 直线，距离很远
        
        # 确定偏转方向
        if trend == 'straight':
            direction = 'straight'
            status = 'going_straight'
        elif trend == 'turning_left':
            direction = 'left'
            status = 'turning_left'
        elif trend == 'turning_right':
            direction = 'right'
            status = 'turning_right'
        else:
            direction = 'unknown'
            status = 'analyzing'
        
        return {
            'prediction': trend,
            'confidence': confidence,
            'direction': direction,
            'turn_angle': np.degrees(predicted_angle),
            'estimated_distance': estimated_distance,
            'curvature': curvature,
            'status': status
        }
    
    def get_direction_visualization(self, image: np.ndarray) -> np.ndarray:
        """在图像上绘制方向预测结果"""
        vis_image = image.copy()
        
        if len(self.axis_history) == 0:
            return vis_image
        
        try:
            prediction = self.predict_direction()
            
            # 图像尺寸
            h, w = image.shape[:2]
            center_x, center_y = w // 2, h // 2
            
            # 根据预测方向绘制箭头和信息
            if prediction['direction'] == 'left':
                arrow_end = (center_x - 80, center_y)
                color = (0, 255, 255)  # 黄色
                text = f"LEFT TURN"
                confidence_text = f"Confidence: {prediction['confidence']:.2f}"
            elif prediction['direction'] == 'right':
                arrow_end = (center_x + 80, center_y)
                color = (255, 0, 255)  # 紫色
                text = f"RIGHT TURN"
                confidence_text = f"Confidence: {prediction['confidence']:.2f}"
            elif prediction['direction'] == 'straight':
                arrow_end = (center_x, center_y - 80)
                color = (0, 255, 0)   # 绿色
                text = f"STRAIGHT"
                confidence_text = f"Confidence: {prediction['confidence']:.2f}"
            else:
                # 未知状态，显示分析中
                cv2.putText(vis_image, "ANALYZING...", (10, 150), 
                           cv2.FONT_HERSHEY_SIMPLEX, 0.8, (128, 128, 128), 2)
                return vis_image
            
            # 绘制预测箭头
            if prediction['confidence'] > 0.3:  # 只有足够置信度才显示箭头
                cv2.arrowedLine(vis_image, (center_x, center_y), arrow_end, 
                               color, 4, tipLength=0.3)
            
            # 绘制预测信息
            cv2.putText(vis_image, text, (10, 150), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.8, color, 2)
            cv2.putText(vis_image, confidence_text, (10, 180), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2)
            
            # 显示转弯角度
            if abs(prediction['turn_angle']) > 1.0:
                angle_text = f"Turn Angle: {prediction['turn_angle']:.1f}°"
                cv2.putText(vis_image, angle_text, (10, 210), 
                           cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 1)
            
            # 显示距离估计
            if prediction['estimated_distance'] < 500:
                dist_text = f"Distance: {prediction['estimated_distance']:.0f}px"
                cv2.putText(vis_image, dist_text, (10, 230), 
                           cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 1)
            
            # 显示历史数据点数
            history_text = f"History: {len(self.axis_history)}/{self.history_size}"
            cv2.putText(vis_image, history_text, (10, 250), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.4, (200, 200, 200), 1)
            
        except Exception as e:
            self.logger.error(f"可视化绘制失败: {e}")
            cv2.putText(vis_image, "PREDICTION ERROR", (10, 150), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 255), 2)
        
        return vis_image
    
    def reset(self):
        """重置预测器状态"""
        self.axis_history.clear()
        self.direction_history.clear()
        self.curvature_history.clear()
        self.last_prediction = None
        self.prediction_confidence = 0.0
        self.logger.info("预测器状态已重置")
    
    def get_prediction_summary(self) -> Dict[str, Any]:
        """获取预测摘要信息"""
        if self.last_prediction is None:
            return {'status': 'no_prediction', 'message': '暂无预测数据'}
        
        return {
            'status': 'active',
            'direction': self.last_prediction['direction'],
            'confidence': self.last_prediction['confidence'],
            'turn_angle': self.last_prediction['turn_angle'],
            'data_points': len(self.axis_history),
            'prediction_quality': 'high' if self.prediction_confidence > 0.7 else 
                                 'medium' if self.prediction_confidence > 0.4 else 'low'
        }

if __name__ == "__main__":
    # 测试代码
    predictor = PipeDirectionPredictor()
    
    # 模拟一些测试数据
    print("🧪 测试管道方向预测器...")
    
    # 直线管道
    for i in range(10):
        points = np.array([[100 + i*10, 200 + i*2], [200 + i*10, 300 + i*2]])
        predictor.add_frame_data(points)
    
    result = predictor.predict_direction()
    print(f"直线预测: {result['direction']}, 置信度: {result['confidence']:.2f}")
    
    # 右转管道
    predictor.reset()
    for i in range(10):
        x_offset = i * 5
        y_offset = i * i * 0.5  # 二次曲线模拟转弯
        points = np.array([[100 + x_offset, 200 + y_offset], 
                          [200 + x_offset, 300 + y_offset]])
        predictor.add_frame_data(points)
    
    result = predictor.predict_direction()
    print(f"右转预测: {result['direction']}, 置信度: {result['confidence']:.2f}, "
          f"角度: {result['turn_angle']:.1f}°")
    
    print("✅ 预测器测试完成")
