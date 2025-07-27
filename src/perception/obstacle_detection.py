import numpy as np
import cv2

class ObstacleDetector:
    def __init__(self, depth_threshold=1000, center_region_width=0.3, critical_distance=500, warning_distance=1500):
        """
        障碍物检测器
        
        Args:
            depth_threshold: 深度阈值（单位mm），小于该深度视为障碍物
            center_region_width: 中央检测区域宽度比例（0-1）
            critical_distance: 紧急停车距离（单位mm）
            warning_distance: 警告距离（单位mm）
        """
        self.depth_threshold = depth_threshold
        self.center_region_width = center_region_width
        self.critical_distance = critical_distance
        self.warning_distance = warning_distance
        
        # 滤波器内核
        self.morphology_kernel = np.ones((5, 5), np.uint8)
        self.erosion_kernel = np.ones((3, 3), np.uint8)

    def detect(self, depth_img):
        """
        检测障碍物并返回掩码
        
        Args:
            depth_img: 深度图像（单位mm的np.ndarray）
            
        Returns:
            mask: 障碍物区域的二值掩码
        """
        if depth_img is None or depth_img.size == 0:
            return np.zeros((480, 640), dtype=np.uint8)
            
        # 生成基础障碍物掩码
        mask = (depth_img > 0) & (depth_img < self.depth_threshold)
        mask = mask.astype(np.uint8) * 255
        
        # 形态学操作去噪
        mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, self.morphology_kernel)
        mask = cv2.erode(mask, self.erosion_kernel, iterations=1)
        mask = cv2.dilate(mask, self.morphology_kernel, iterations=1)
        
        return mask
    
    def analyze_obstacle_threat(self, depth_img, mask=None):
        """
        分析障碍物威胁等级
        
        Args:
            depth_img: 深度图像
            mask: 障碍物掩码（可选）
            
        Returns:
            dict: 威胁分析结果
        """
        if mask is None:
            mask = self.detect(depth_img)
            
        height, width = depth_img.shape
        
        # 定义中央检测区域
        center_start = int(width * (0.5 - self.center_region_width / 2))
        center_end = int(width * (0.5 + self.center_region_width / 2))
        center_mask = mask[:, center_start:center_end]
        
        # 计算障碍物统计信息
        total_obstacle_pixels = np.sum(mask > 0)
        center_obstacle_pixels = np.sum(center_mask > 0)
        
        # 查找最近的障碍物距离
        min_distance = float('inf')
        if total_obstacle_pixels > 0:
            obstacle_coords = np.where(mask > 0)
            obstacle_depths = depth_img[obstacle_coords]
            min_distance = np.min(obstacle_depths[obstacle_depths > 0])
        
        # 确定威胁等级
        threat_level = "none"
        if min_distance < self.critical_distance:
            threat_level = "critical"
        elif min_distance < self.warning_distance:
            threat_level = "warning"
        elif center_obstacle_pixels > 50:
            threat_level = "caution"
            
        return {
            "threat_level": threat_level,
            "min_distance": min_distance,
            "total_obstacle_pixels": total_obstacle_pixels,
            "center_obstacle_pixels": center_obstacle_pixels,
            "obstacle_density": total_obstacle_pixels / (height * width),
            "center_obstacle_density": center_obstacle_pixels / (center_mask.shape[0] * center_mask.shape[1])
        }
    
    def should_avoid(self, depth_img, min_area=100):
        """
        判断是否需要避障
        
        Args:
            depth_img: 深度图像
            min_area: 最小障碍物面积阈值
            
        Returns:
            bool: 是否需要避障
        """
        mask = self.detect(depth_img)
        analysis = self.analyze_obstacle_threat(depth_img, mask)
        
        # 基于威胁等级和面积判断
        return (analysis["threat_level"] in ["critical", "warning"] or 
                analysis["total_obstacle_pixels"] > min_area)

    def draw_obstacles(self, color_img, mask, analysis=None):
        """
        在彩色图像上绘制障碍物检测结果
        
        Args:
            color_img: 彩色图像
            mask: 障碍物掩码
            analysis: 威胁分析结果（可选）
            
        Returns:
            result: 标注后的图像
        """
        result = color_img.copy()
        
        # 根据威胁等级选择颜色
        if analysis:
            if analysis["threat_level"] == "critical":
                color = [0, 0, 255]  # 红色
            elif analysis["threat_level"] == "warning":
                color = [0, 165, 255]  # 橙色
            elif analysis["threat_level"] == "caution":
                color = [0, 255, 255]  # 黄色
            else:
                color = [0, 255, 0]  # 绿色
        else:
            color = [0, 0, 255]  # 默认红色
            
        # 高亮障碍物区域
        result[mask == 255] = color
        
        # 绘制中央检测区域
        height, width = mask.shape
        center_start = int(width * (0.5 - self.center_region_width / 2))
        center_end = int(width * (0.5 + self.center_region_width / 2))
        cv2.rectangle(result, (center_start, 0), (center_end, height), (255, 255, 255), 2)
        
        # 添加威胁信息文本
        if analysis:
            info_text = f"Threat: {analysis['threat_level'].upper()}"
            distance_text = f"Min Dist: {analysis['min_distance']:.0f}mm"
            cv2.putText(result, info_text, (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
            cv2.putText(result, distance_text, (10, 70), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
        
        return result

if __name__ == "__main__":
    # 示例用法
    color_img = cv2.imread("test_color.jpg")
    depth_img = cv2.imread("test_depth.png", cv2.IMREAD_UNCHANGED)  # 假设为16位深度图
    detector = ObstacleDetector(depth_threshold=1000)
    mask = detector.detect(depth_img)
    result = detector.draw_obstacles(color_img, mask)
    cv2.imshow("Obstacle Mask", mask)
    cv2.imshow("Obstacle Detection", result)
    cv2.waitKey(0)