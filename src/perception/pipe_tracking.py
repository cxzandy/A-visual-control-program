import cv2
import numpy as np
from typing import Tuple, Optional, List
import logging

# 添加配置导入
try:
    from config import RunModeConfig
except ImportError:
    # 如果导入失败，创建一个默认配置
    class RunModeConfig:
        VERBOSE_OUTPUT = False

class PipeTracker:
    """管道追踪器"""
    
    def __init__(self, depth_threshold: float = 2.0, camera_intrinsics: Optional[List[float]] = None):
        self.depth_threshold = depth_threshold
        self.camera_intrinsics = camera_intrinsics
        self.logger = logging.getLogger(__name__)
        
    def track(self, color_frame: np.ndarray, depth_frame: np.ndarray) -> Tuple[Optional[List], Optional[np.ndarray], Optional[np.ndarray]]:
        """
        追踪管道 - 四象限分析方法
        
        Args:
            color_frame: 彩色图像
            depth_frame: 深度图像
            
        Returns:
            line_params_list: 四个象限的直线参数列表 [[x1,y1,x2,y2], ...] 或 None
            global_axis: 拟合的全局管道轴线3D点
            vis_image: 可视化图像
        """
        try:
            # 创建可视化图像的副本
            vis_image = color_frame.copy()
            h, w = color_frame.shape[:2]
            
            # 1. 图像预处理
            gray = cv2.cvtColor(color_frame, cv2.COLOR_BGR2GRAY)
            
            # 2. 边缘检测
            edges = cv2.Canny(gray, 50, 150, apertureSize=3)
            
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
            
            return line_params_list, global_axis, vis_image
            
        except Exception as e:
            self.logger.error(f"管道追踪失败: {e}")
            return None, None, color_frame.copy()

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
    line_params_list, global_axis_points, vis = tracker.track(color_img_sim, depth_img_sim)
    
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