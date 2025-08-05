import cv2
import numpy as np
from typing import Tuple, Optional, List, Dict
import logging
import time

# 添加配置导入
try:
    from config import RunModeConfig
except ImportError:
    # 如果导入失败，创建一个默认配置
    class RunModeConfig:
        VERBOSE_OUTPUT = False

# 内置方向预测和部分追踪功能

class PipeDirectionPredictor:
    """内置方向预测器"""
    def __init__(self, history_size=15, prediction_steps=8):
        self.history_size = history_size
        self.prediction_steps = prediction_steps
        self.history = []
        
    def add_frame_data(self, center_point, direction_vector, timestamp=None):
        """添加帧数据"""
        if len(self.history) >= self.history_size:
            self.history.pop(0)
        self.history.append({
            'center': center_point,
            'direction': direction_vector,
            'timestamp': timestamp or time.time()
        })
    
    def predict_direction(self):
        """预测方向"""
        if len(self.history) < 3:
            return {'direction': 'unknown', 'confidence': 0.0}
        
        # 简单的方向预测基于历史数据
        recent_directions = [frame['direction'] for frame in self.history[-3:]]
        
        # 计算平均方向
        if recent_directions:
            avg_direction = np.mean(recent_directions, axis=0)
            
            # 判断左转还是右转
            if avg_direction[0] > 10:  # 向右
                direction = 'right'
                confidence = min(abs(avg_direction[0]) / 50.0, 1.0)
            elif avg_direction[0] < -10:  # 向左
                direction = 'left'
                confidence = min(abs(avg_direction[0]) / 50.0, 1.0)
            else:
                direction = 'straight'
                confidence = 0.7
            
            return {'direction': direction, 'confidence': confidence}
        
        return {'direction': 'unknown', 'confidence': 0.0}
    
    def get_direction_visualization(self, image):
        """获取方向可视化"""
        return image

class PartialPipeTracker:
    """内置部分管道追踪器"""
    def __init__(self):
        self.last_center = None
        
    def track_partial_pipe(self, color_image, depth_image=None):
        """追踪部分可见管道"""
        # 简化的部分追踪实现
        gray = cv2.cvtColor(color_image, cv2.COLOR_BGR2GRAY)
        edges = cv2.Canny(gray, 50, 150)
        
        # 查找轮廓
        contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        if contours:
            # 找到最大轮廓
            largest_contour = max(contours, key=cv2.contourArea)
            
            # 计算轮廓中心
            M = cv2.moments(largest_contour)
            if M["m00"] != 0:
                cx = int(M["m10"] / M["m00"])
                cy = int(M["m01"] / M["m00"])
                
                return {
                    'success': True,
                    'pipe_edges': [largest_contour],
                    'estimated_center': (cx, cy),
                    'pipe_direction': 0,
                    'tracking_method': 'contour',
                    'confidence': 0.6
                }
        
        return {'success': False}
    
    def visualize_result(self, image, result):
        """可视化结果"""
        if result.get('success', False) and result.get('estimated_center'):
            cx, cy = result['estimated_center']
            cv2.circle(image, (cx, cy), 5, (0, 255, 0), -1)
        return image

class PipeTracker:
    """管道追踪器 - 增强版本支持方向预测"""
    
    def __init__(self, depth_threshold: float = 2.0, camera_intrinsics: Optional[List[float]] = None):
        self.depth_threshold = depth_threshold
        self.camera_intrinsics = camera_intrinsics
        self.logger = logging.getLogger(__name__)
        
        # 添加方向预测器
        self.direction_predictor = PipeDirectionPredictor(history_size=15, prediction_steps=8)
        
        # 添加部分视角追踪器
        self.partial_tracker = PartialPipeTracker()
        
        # 追踪模式
        self.tracking_mode = "auto"  # auto, full_quadrant, partial_view
        self.quadrant_failure_count = 0
        self.max_failures_before_switch = 3
        
        # 预测统计
        self.prediction_stats = {
            'total_predictions': 0,
            'successful_predictions': 0,
            'last_prediction': None,
            'prediction_accuracy': 0.0
        }
        
    def track(self, color_frame: np.ndarray, depth_frame: np.ndarray) -> Tuple[Optional[List], Optional[np.ndarray], Optional[np.ndarray], Optional[dict]]:
        """
        追踪管道 - 自适应四象限分析 + 部分视角处理 + 方向预测
        
        Args:
            color_frame: 彩色图像
            depth_frame: 深度图像
            
        Returns:
            line_params_list: 四个象限的直线参数列表 [[x1,y1,x2,y2], ...] 或 None
            global_axis: 拟合的全局管道轴线3D点
            vis_image: 可视化图像
            prediction_info: 方向预测信息
        """
        try:
            # 创建可视化图像的副本
            vis_image = color_frame.copy()
            h, w = color_frame.shape[:2]
            
            # 1. 首先尝试四象限检测
            if self.tracking_mode in ["auto", "full_quadrant"]:
                line_params_list, global_axis, quadrant_success = self._try_quadrant_detection(
                    color_frame, depth_frame, vis_image)
                
                if quadrant_success:
                    # 四象限检测成功
                    self.quadrant_failure_count = 0
                    detected_count = len([p for p in line_params_list if p is not None])
                    
                    self.logger.debug(f"四象限检测成功，检测到{detected_count}个象限")
                    
                    # 执行方向预测
                    prediction_info = self._perform_direction_prediction(
                        global_axis, vis_image)
                    
                    return line_params_list, global_axis, vis_image, prediction_info
                else:
                    # 四象限检测失败
                    self.quadrant_failure_count += 1
                    self.logger.warning(f"四象限检测失败，失败次数: {self.quadrant_failure_count}")
            
            # 2. 如果四象限检测失败或模式设置为部分视角，尝试部分视角检测
            if (self.tracking_mode in ["auto", "partial_view"] and 
                (self.quadrant_failure_count >= self.max_failures_before_switch or 
                 self.tracking_mode == "partial_view")):
                
                self.logger.info("切换到部分视角检测模式")
                
                partial_result = self.partial_tracker.track_partial_pipe(color_frame, depth_frame)
                
                if partial_result['success']:
                    # 部分视角检测成功
                    self.logger.info(f"部分视角检测成功，方法: {partial_result['tracking_method']}")
                    
                    # 转换为标准格式
                    line_params_list = self._convert_partial_to_standard_format(partial_result)
                    global_axis = self._estimate_axis_from_partial(partial_result)
                    
                    # 可视化部分视角结果
                    vis_image = self.partial_tracker.visualize_result(vis_image, partial_result)
                    
                    # 执行方向预测
                    prediction_info = self._perform_direction_prediction_from_partial(
                        partial_result, vis_image)
                    
                    # 重置失败计数
                    if self.tracking_mode == "auto":
                        self.quadrant_failure_count = max(0, self.quadrant_failure_count - 1)
                    
                    return line_params_list, global_axis, vis_image, prediction_info
            
            # 3. 所有检测方法都失败
            self.logger.warning("所有管道检测方法都失败")
            
            # 在图像上显示失败信息
            cv2.putText(vis_image, "No pipe detected - trying multiple methods", 
                       (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
            cv2.putText(vis_image, f"Quadrant failures: {self.quadrant_failure_count}", 
                       (10, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 255), 2)
            cv2.putText(vis_image, f"Current mode: {self.tracking_mode}", 
                       (10, 90), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
            
            return None, None, vis_image, None
            
        except Exception as e:
            self.logger.error(f"管道追踪失败: {e}")
            return None, None, color_frame.copy(), None
            
            # 3. 将图像分成四个象限
            mid_x, mid_y = w // 2, h // 2
            quadrants = [
                ("Q1", edges[0:mid_y, mid_x:w]),        # 右上
                ("Q2", edges[0:mid_y, 0:mid_x]),        # 左上  
                ("Q3", edges[mid_y:h, 0:mid_x]),        # 左下
                ("Q4", edges[mid_y:h, mid_x:w])         # 右下
            ]
            
            # 4. 在每个象限中检测直线
            line_params_list = []
            quadrant_colors = [(255, 0, 0), (0, 255, 0), (0, 0, 255), (255, 255, 0)]  # 不同颜色
            
            for i, (q_name, quad_edges) in enumerate(quadrants):
                # 在象限中检测直线
                lines = cv2.HoughLinesP(
                    quad_edges,
                    rho=1,
                    theta=np.pi/180,
                    threshold=50,  # 降低阈值，因为象限图像更小
                    minLineLength=30,
                    maxLineGap=20
                )
                
                best_line = None
                max_length = 0
                
                if lines is not None and len(lines) > 0:
                    # 找到最长的直线
                    for line in lines:
                        x1, y1, x2, y2 = line[0]
                        length = np.sqrt((x2-x1)**2 + (y2-y1)**2)
                        if length > max_length:
                            max_length = length
                            best_line = line[0]
                    
                    if best_line is not None:
                        # 将象限坐标转换回全图坐标
                        x1, y1, x2, y2 = best_line
                        if i == 0:  # Q1 (右上)
                            x1, x2 = x1 + mid_x, x2 + mid_x
                        elif i == 1:  # Q2 (左上)
                            pass  # 坐标不变
                        elif i == 2:  # Q3 (左下)
                            y1, y2 = y1 + mid_y, y2 + mid_y
                        elif i == 3:  # Q4 (右下)
                            x1, x2 = x1 + mid_x, x2 + mid_x
                            y1, y2 = y1 + mid_y, y2 + mid_y
                        
                        line_params_list.append([x1, y1, x2, y2])
                        
                        # 在可视化图像上绘制象限直线
                        color = quadrant_colors[i]
                        cv2.line(vis_image, (x1, y1), (x2, y2), color, 2)
                        cv2.circle(vis_image, (x1, y1), 3, color, -1)
                        cv2.circle(vis_image, (x2, y2), 3, color, -1)
                        
                        # 添加象限标签
                        label_x = mid_x + (10 if i in [0, 3] else -50)
                        label_y = (10 if i in [0, 1] else h - 10)
                        cv2.putText(vis_image, f"{q_name}:L={max_length:.0f}", 
                                   (label_x, label_y), cv2.FONT_HERSHEY_SIMPLEX, 0.4, color, 1)
                        
                        self.logger.debug(f"{q_name} 检测到直线: ({x1},{y1})-({x2},{y2}), 长度: {max_length:.1f}")
                else:
                    line_params_list.append(None)
                    self.logger.debug(f"{q_name} 未检测到直线")
            
            # 5. 绘制象限分割线
            cv2.line(vis_image, (mid_x, 0), (mid_x, h), (255, 255, 255), 1)  # 垂直线
            cv2.line(vis_image, (0, mid_y), (w, mid_y), (255, 255, 255), 1)  # 水平线
            
            # 6. 计算管道中心轴线
            valid_lines = [line for line in line_params_list if line is not None]
            global_axis = None
            
            if len(valid_lines) >= 2:  # 至少需要2个象限有检测结果
                try:
                    # 计算所有有效直线的中点
                    center_points = []
                    for line in valid_lines:
                        x1, y1, x2, y2 = line
                        center_x = (x1 + x2) / 2
                        center_y = (y1 + y2) / 2
                        center_points.append([center_x, center_y])
                    
                    center_points = np.array(center_points)
                    
                    # 使用最小二乘法拟合中心轴线
                    if len(center_points) >= 2:
                        # 拟合直线 y = ax + b
                        A = np.vstack([center_points[:, 0], np.ones(len(center_points))]).T
                        a, b = np.linalg.lstsq(A, center_points[:, 1], rcond=None)[0]
                        
                        # 生成轴线上的点
                        x_line = np.linspace(0, w, 100)
                        y_line = a * x_line + b
                        
                        # 过滤在图像范围内的点
                        valid_mask = (y_line >= 0) & (y_line < h)
                        x_line = x_line[valid_mask]
                        y_line = y_line[valid_mask]
                        
                        if len(x_line) > 0:
                            global_axis = np.column_stack([x_line, y_line])
                            
                            # 绘制拟合的中心轴线
                            for i in range(len(x_line)-1):
                                pt1 = (int(x_line[i]), int(y_line[i]))
                                pt2 = (int(x_line[i+1]), int(y_line[i+1]))
                                cv2.line(vis_image, pt1, pt2, (0, 255, 255), 2)  # 黄色轴线
                            
                            # 绘制中心点
                            for point in center_points:
                                cv2.circle(vis_image, (int(point[0]), int(point[1])), 4, (255, 0, 255), -1)
                            
                            cv2.putText(vis_image, f"Pipe Axis: {len(valid_lines)} quadrants", 
                                       (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 255), 2)
                            
                            self.logger.debug(f"成功拟合管道轴线，使用{len(valid_lines)}个象限的数据")
                        
                except Exception as e:
                    self.logger.warning(f"轴线拟合失败: {e}")
            
            # 7. 显示检测状态
            detected_count = len(valid_lines)
            status_text = f"Quadrants: {detected_count}/4"
            status_color = (0, 255, 0) if detected_count >= 2 else (0, 0, 255)
            cv2.putText(vis_image, status_text, (10, h-20), cv2.FONT_HERSHEY_SIMPLEX, 0.6, status_color, 2)
            
            if detected_count == 0:
                cv2.putText(vis_image, "No pipe detected in any quadrant", 
                           (10, 50), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 255), 2)
            
            # 8. 可选：显示边缘检测结果
            try:
                verbose_mode = RunModeConfig.VERBOSE_OUTPUT
            except (AttributeError, NameError):
                verbose_mode = False
                
            if verbose_mode:
                # 将边缘检测结果叠加到可视化图像上
                edges_colored = cv2.cvtColor(edges, cv2.COLOR_GRAY2BGR)
                vis_image = cv2.addWeighted(vis_image, 0.7, edges_colored, 0.3, 0)
            
            # 9. 方向预测处理
            prediction_info = None
            if detected_count >= 2 and global_axis is not None and len(global_axis) > 0:
                try:
                    # 计算管道中心点（轴线的中心）
                    center_point = np.mean(global_axis, axis=0)[:2]  # 取x,y坐标
                    
                    # 计算管道角度（基于轴线的主方向）
                    if len(global_axis) >= 2:
                        axis_vector = global_axis[-1][:2] - global_axis[0][:2]
                        angle = np.degrees(np.arctan2(axis_vector[1], axis_vector[0]))
                    else:
                        angle = 0.0
                    
                    # 更新方向预测器
                    self.direction_predictor.add_frame_data(
                        center_point=tuple(center_point),
                        direction_vector=[angle, 0],  # 转换为方向向量
                        timestamp=time.time()
                    )
                    
                    # 获取方向预测
                    prediction = self.direction_predictor.predict_direction()
                    prediction_info = prediction
                    
                    # 更新统计信息
                    self._update_prediction_stats(prediction)
                    
                    # 在可视化图像上添加预测信息
                    vis_image = self._add_prediction_visualization(vis_image, prediction, center_point)
                    
                except Exception as e:
                    self.logger.warning(f"方向预测处理失败: {e}")
            
            return line_params_list, global_axis, vis_image, prediction_info
            
        except Exception as e:
            self.logger.error(f"管道追踪失败: {e}")
            return None, None, color_frame.copy(), None
    
    def _update_prediction_stats(self, prediction: dict):
        """更新预测统计信息"""
        try:
            self.prediction_stats['total_predictions'] += 1
            self.prediction_stats['last_prediction'] = prediction
            
            # 简单的成功判断：如果置信度大于阈值就认为是成功预测
            if prediction.get('confidence', 0) > 0.5:
                self.prediction_stats['successful_predictions'] += 1
            
            # 计算准确率
            if self.prediction_stats['total_predictions'] > 0:
                self.prediction_stats['prediction_accuracy'] = (
                    self.prediction_stats['successful_predictions'] / 
                    self.prediction_stats['total_predictions']
                )
        except Exception as e:
            self.logger.warning(f"更新预测统计失败: {e}")
    
    def _add_prediction_visualization(self, image: np.ndarray, prediction: dict, center_point: np.ndarray) -> np.ndarray:
        """在图像上添加方向预测可视化"""
        try:
            direction = prediction.get('direction', 'unknown')
            confidence = prediction.get('confidence', 0.0)
            
            # 方向箭头配置
            arrow_length = 50
            arrow_thickness = 3
            
            # 根据方向确定箭头终点
            center_x, center_y = int(center_point[0]), int(center_point[1])
            
            if direction == 'left':
                end_x, end_y = center_x - arrow_length, center_y
                color = (0, 255, 255)  # 黄色
            elif direction == 'right':
                end_x, end_y = center_x + arrow_length, center_y
                color = (0, 255, 255)  # 黄色
            elif direction == 'up':
                end_x, end_y = center_x, center_y - arrow_length
                color = (255, 0, 255)  # 紫色
            elif direction == 'down':
                end_x, end_y = center_x, center_y + arrow_length
                color = (255, 0, 255)  # 紫色
            else:
                end_x, end_y = center_x, center_y
                color = (128, 128, 128)  # 灰色
            
            # 绘制箭头
            if direction != 'unknown':
                cv2.arrowedLine(image, (center_x, center_y), (end_x, end_y), 
                               color, arrow_thickness, tipLength=0.3)
            
            # 添加文本信息
            text = f"Dir: {direction.upper()} ({confidence:.2f})"
            text_size = cv2.getTextSize(text, cv2.FONT_HERSHEY_SIMPLEX, 0.6, 2)[0]
            
            # 确保文本在图像范围内
            text_x = max(10, min(center_x - text_size[0]//2, image.shape[1] - text_size[0] - 10))
            text_y = max(text_size[1] + 10, center_y - 30)
            
            # 绘制背景矩形
            cv2.rectangle(image, 
                         (text_x - 5, text_y - text_size[1] - 5),
                         (text_x + text_size[0] + 5, text_y + 5),
                         (0, 0, 0), -1)
            
            # 绘制文本
            cv2.putText(image, text, (text_x, text_y),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2)
            
            return image
            
        except Exception as e:
            self.logger.warning(f"预测可视化失败: {e}")
            return image
    
    def get_prediction_stats(self) -> dict:
        """获取预测统计信息"""
        return self.prediction_stats.copy()
    
    def _try_quadrant_detection(self, color_frame: np.ndarray, depth_frame: np.ndarray, 
                               vis_image: np.ndarray) -> Tuple[Optional[List], Optional[np.ndarray], bool]:
        """
        尝试四象限检测方法
        
        Returns:
            line_params_list, global_axis, success
        """
        try:
            # 1. 图像预处理
            gray = cv2.cvtColor(color_frame, cv2.COLOR_BGR2GRAY)
            h, w = color_frame.shape[:2]
            
            # 2. 边缘检测
            edges = cv2.Canny(gray, 50, 150, apertureSize=3)
            
            # 3. 四象限分析（原有代码逻辑）
            mid_x, mid_y = w // 2, h // 2
            quadrants = [
                ("Q1", edges[0:mid_y, mid_x:w]),        # 右上
                ("Q2", edges[0:mid_y, 0:mid_x]),        # 左上  
                ("Q3", edges[mid_y:h, 0:mid_x]),        # 左下
                ("Q4", edges[mid_y:h, mid_x:w])         # 右下
            ]
            
            line_params_list = []
            valid_lines = []
            quadrant_colors = [(255, 0, 0), (0, 255, 0), (0, 0, 255), (255, 255, 0)]
            
            for i, (q_name, quad_edges) in enumerate(quadrants):
                # 在象限中检测直线
                lines = cv2.HoughLinesP(
                    quad_edges,
                    rho=1,
                    theta=np.pi/180,
                    threshold=50,
                    minLineLength=30,
                    maxLineGap=20
                )
                
                if lines is not None and len(lines) > 0:
                    # 找到最长的直线
                    best_line = None
                    max_length = 0
                    
                    for line in lines:
                        x1, y1, x2, y2 = line[0]
                        length = np.sqrt((x2-x1)**2 + (y2-y1)**2)
                        if length > max_length:
                            max_length = length
                            best_line = line[0]
                    
                    if best_line is not None and max_length > 30:
                        # 转换坐标到全图
                        x1, y1, x2, y2 = best_line
                        if i == 0:  # Q1 右上
                            x1, x2 = x1 + mid_x, x2 + mid_x
                        elif i == 1:  # Q2 左上
                            pass
                        elif i == 2:  # Q3 左下
                            y1, y2 = y1 + mid_y, y2 + mid_y
                        elif i == 3:  # Q4 右下
                            x1, x2 = x1 + mid_x, x2 + mid_x
                            y1, y2 = y1 + mid_y, y2 + mid_y
                        
                        line_params_list.append([x1, y1, x2, y2])
                        valid_lines.append([x1, y1, x2, y2])
                        
                        # 可视化
                        color = quadrant_colors[i]
                        cv2.line(vis_image, (x1, y1), (x2, y2), color, 2)
                        cv2.circle(vis_image, (x1, y1), 3, color, -1)
                        cv2.circle(vis_image, (x2, y2), 3, color, -1)
                else:
                    line_params_list.append(None)
            
            # 检查检测成功的象限数量
            detected_count = len(valid_lines)
            
            if detected_count >= 2:
                # 尝试拟合轴线
                global_axis = self._fit_global_axis(valid_lines)
                
                # 在可视化图像上绘制轴线
                if global_axis is not None and len(global_axis) > 1:
                    for i in range(len(global_axis)-1):
                        pt1 = (int(global_axis[i][0]), int(global_axis[i][1]))
                        pt2 = (int(global_axis[i+1][0]), int(global_axis[i+1][1]))
                        cv2.line(vis_image, pt1, pt2, (0, 255, 255), 2)
                
                cv2.putText(vis_image, f"Quadrants: {detected_count}/4", 
                           (10, h-20), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
                
                return line_params_list, global_axis, True
            else:
                cv2.putText(vis_image, "Insufficient quadrant detection", 
                           (10, h-20), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 255), 2)
                return line_params_list, None, False
                
        except Exception as e:
            self.logger.warning(f"四象限检测异常: {e}")
            return None, None, False
    
    def _fit_global_axis(self, valid_lines: List) -> Optional[np.ndarray]:
        """拟合全局管道轴线"""
        try:
            if len(valid_lines) < 2:
                return None
                
            # 计算每条线的中点
            center_points = []
            for line in valid_lines:
                x1, y1, x2, y2 = line
                cx = (x1 + x2) / 2
                cy = (y1 + y2) / 2
                center_points.append([cx, cy])
            
            center_points = np.array(center_points)
            
            # 使用线性回归拟合轴线
            if len(center_points) >= 2:
                # 计算主方向
                mean_point = np.mean(center_points, axis=0)
                centered_points = center_points - mean_point
                
                # SVD分解得到主方向
                U, S, Vt = np.linalg.svd(centered_points.T)
                direction = U[:, 0]
                
                # 生成轴线点
                t_values = np.linspace(-50, 50, 10)
                axis_points = []
                for t in t_values:
                    point = mean_point + t * direction
                    axis_points.append([point[0], point[1], 0])  # 添加Z坐标
                
                return np.array(axis_points)
            
        except Exception as e:
            self.logger.warning(f"轴线拟合失败: {e}")
            
        return None
    
    def _convert_partial_to_standard_format(self, partial_result: Dict) -> List:
        """将部分视角结果转换为标准格式"""
        line_params_list = [None, None, None, None]  # 四个象限
        
        if partial_result['pipe_edges']:
            # 取第一条边缘作为主要检测结果
            line_params_list[0] = partial_result['pipe_edges'][0]
            
        return line_params_list
    
    def _estimate_axis_from_partial(self, partial_result: Dict) -> Optional[np.ndarray]:
        """从部分视角结果估算轴线"""
        if partial_result['estimated_center'] is None:
            return None
            
        try:
            center = partial_result['estimated_center']
            direction = partial_result.get('pipe_direction', 0)
            
            # 生成简单的轴线
            angle_rad = np.radians(direction) if direction is not None else 0
            
            axis_points = []
            for t in range(-30, 31, 10):
                x = center[0] + t * np.cos(angle_rad)
                y = center[1] + t * np.sin(angle_rad)
                axis_points.append([x, y, 0])
                
            return np.array(axis_points)
            
        except Exception as e:
            self.logger.warning(f"轴线估算失败: {e}")
            return None
    
    def _perform_direction_prediction(self, global_axis: Optional[np.ndarray], 
                                    vis_image: np.ndarray) -> Optional[dict]:
        """执行方向预测（四象限模式）"""
        prediction_info = None
        
        try:
            if global_axis is not None and len(global_axis) > 0:
                # 计算管道中心点
                center_point = np.mean(global_axis, axis=0)[:2]
                
                # 计算管道角度
                if len(global_axis) >= 2:
                    axis_vector = global_axis[-1][:2] - global_axis[0][:2]
                    angle = np.degrees(np.arctan2(axis_vector[1], axis_vector[0]))
                else:
                    angle = 0.0
                
                # 更新方向预测器
                self.direction_predictor.add_frame_data(
                    center_point=tuple(center_point),
                    direction_vector=[angle, 0],  # 转换为方向向量
                    timestamp=time.time()
                )
                
                # 获取方向预测
                prediction = self.direction_predictor.predict_direction()
                prediction_info = prediction
                
                # 更新统计信息
                self._update_prediction_stats(prediction)
                
                # 在可视化图像上添加预测信息
                vis_image = self._add_prediction_visualization(vis_image, prediction, center_point)
                
        except Exception as e:
            self.logger.warning(f"方向预测处理失败: {e}")
            
        return prediction_info
    
    def _perform_direction_prediction_from_partial(self, partial_result: Dict, 
                                                 vis_image: np.ndarray) -> Optional[dict]:
        """执行方向预测（部分视角模式）"""
        prediction_info = None
        
        try:
            if partial_result['estimated_center'] is not None:
                center_point = partial_result['estimated_center']
                angle = partial_result.get('pipe_direction', 0.0)
                
                # 更新方向预测器
                self.direction_predictor.add_frame_data(
                    center_point=center_point,
                    direction_vector=[angle, 0],  # 转换为方向向量
                    timestamp=time.time()
                )
                
                # 获取方向预测
                prediction = self.direction_predictor.predict_direction()
                prediction_info = prediction
                
                # 更新统计信息
                self._update_prediction_stats(prediction)
                
                # 添加预测可视化（如果部分追踪器没有添加的话）
                if 'prediction' not in str(type(vis_image)):
                    vis_image = self._add_prediction_visualization(vis_image, prediction, center_point)
                
        except Exception as e:
            self.logger.warning(f"部分视角方向预测失败: {e}")
            
        return prediction_info
    
    def set_tracking_mode(self, mode: str):
        """设置追踪模式"""
        if mode in ["auto", "full_quadrant", "partial_view"]:
            self.tracking_mode = mode
            self.logger.info(f"追踪模式设置为: {mode}")
        else:
            self.logger.warning(f"不支持的追踪模式: {mode}")
    
    def get_tracking_stats(self) -> dict:
        """获取追踪统计信息"""
        return {
            'tracking_mode': self.tracking_mode,
            'quadrant_failure_count': self.quadrant_failure_count,
            'prediction_stats': self.prediction_stats.copy()
        }

if __name__ == "__main__":
    # 示例：假设有彩色图像和深度图像
    # 创建一个模拟的彩色图像和深度图像
    H, W = 480, 640
    color_img_sim = np.zeros((H, W, 3), dtype=np.uint8)
    depth_img_sim = np.zeros((H, W), dtype=np.uint16) # 深度通常是uint16，单位mm

    # 模拟一个弯曲的管道（上半部分）
    # 假设管道从左下到右上弯曲
    pipe_center_x = np.linspace(W // 4, 3 * W // 4, 100)
    pipe_center_y = np.sin(np.linspace(0, np.pi, 100)) * (H // 8) + H // 4 # Y方向先增加后减小，形成弯曲
    pipe_depth = np.linspace(1000, 1500, 100) # 深度从1米到1.5米

    # 模拟管道半径和厚度
    pipe_radius_px = 20 # 像素半径
    depth_variation = 50 # 深度噪声 (mm)

    for i in range(len(pipe_center_x)):
        cx, cy, d = int(pipe_center_x[i]), int(pipe_center_y[i]), int(pipe_depth[i])
        
        # 绘制半圆边缘
        for angle_deg in range(0, 180): # 0到180度表示上半部分
            angle_rad = np.deg2rad(angle_deg)
            
            # 在图像上绘制边缘点
            ex = int(cx + pipe_radius_px * np.cos(angle_rad))
            ey = int(cy - pipe_radius_px * np.sin(angle_rad)) # 减号是为了让上半部分朝上

            if 0 <= ex < W and 0 <= ey < H:
                # 模拟深度值，边缘点的深度和中心点深度相同，加上少量噪声
                depth_img_sim[ey, ex] = d + np.random.randint(-depth_variation, depth_variation)
                color_img_sim[ey, ex] = (255, 255, 255) # 白色边缘

    # 为了更好的边缘检测，可以画一些填充区域，但Canny通常需要细线
    # 也可以模拟为直接在深度图上生成一个半圆柱的点，然后投影到2D
    # 这里只是一个简化的模拟，确保能有边缘点和深度值

    # 如果有真实的图像和深度图，请取消注释下面两行并修改路径
    # color_img_path = "path/to/your/color_image.jpg"
    # depth_img_path = "path/to/your/depth_image.png" # 确保是单通道或灰度，且深度值正确
    # color_img = cv2.imread(color_img_path)
    # depth_img = cv2.imread(depth_img_path, cv2.IMREAD_UNCHANGED)

    # 确保深度图是 uint16 类型（OpenCV的IMREAD_UNCHANGED可能读成uint8或float）
    # 如果深度图是float32/64，需要乘以1000转换为mm并转为uint16
    # 例如: depth_img = (depth_img * 1000).astype(np.uint16)

    # 假设相机内参 (fx, fy, cx, cy) - 这些需要根据你的相机实际校准结果填写
    # 示例值：对于一个640x480的图像，焦距通常在500-800之间
    my_camera_intrinsics = [600.0, 600.0, W / 2, H / 2]

    tracker = PipeTracker(depth_threshold=2000, camera_intrinsics=my_camera_intrinsics)
    
    # 使用模拟图像进行测试
    line_params_list, global_axis_points, vis, prediction_info = tracker.track(color_img_sim, depth_img_sim)
    
    print("各象限3D直线参数:", line_params_list)
    if global_axis_points is not None:
        print("\n全局管道轴线拟合成功！")
        print("拟合轴线的前5个点 (米):")
        print(global_axis_points[:5])
        print(f"拟合轴线总共 {len(global_axis_points)} 个点。")
    else:
        print("\n全局管道轴线拟合失败。")


    cv2.imshow("Pipe 3D Line and Curve Fitting", vis)
    cv2.waitKey(0)
    cv2.destroyAllWindows()