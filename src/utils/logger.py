import numpy as np
import cv2

class ObstacleDetector:
    def __init__(self, depth_threshold=1000):
        """
        depth_threshold: 小于该深度（单位mm）的区域视为障碍物
        """
        self.depth_threshold = depth_threshold

    def detect(self, depth_img):
        """
        输入：depth_img（单位mm的深度图，np.ndarray）
        输出：mask（障碍物区域的二值掩码）
        """
        # 生成障碍物掩码
        mask = (depth_img > 0) & (depth_img < self.depth_threshold)
        mask = mask.astype(np.uint8) * 255
        # 可选：形态学操作去噪
        kernel = np.ones((5, 5), np.uint8)
        mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)
        return mask

    def draw_obstacles(self, color_img, mask):
        """
        在彩色图像上用红色高亮障碍物区域
        """
        result = color_img.copy()
        result[mask == 255] = [0, 0, 255]
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