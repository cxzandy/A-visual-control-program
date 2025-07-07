import cv2
import numpy as np
from sklearn.linear_model import RANSACRegressor

class PipeTracker:
    def __init__(self, depth_threshold=1000):
        self.depth_threshold = depth_threshold  # mm

    def fit_line_3d(self, xs, ys, ds):
        """
        用PCA在3D空间中拟合一条直线，返回直线的点和方向向量
        """
        if len(xs) < 2:
            return None
        points = np.stack([xs, ys, ds], axis=1)
        mean = np.mean(points, axis=0)
        _, _, vh = np.linalg.svd(points - mean)
        direction = vh[0]
        return (mean, direction)

    def track(self, color_img, depth_img):
        """
        输入:
            color_img: 彩色图像 (H, W, 3)
            depth_img: 深度图像 (H, W)
        输出:
            line_params_list: 每个象限的3D直线参数 [(point, direction), ...]
            vis: 可视化结果
        """
        H, W = color_img.shape[:2]
        vis = color_img.copy()

        # 绘制象限分割线
        cv2.line(vis, (W // 2, 0), (W // 2, H), (255, 255, 0), 2)
        cv2.line(vis, (0, H // 2), (W, H // 2), (255, 255, 0), 2)

        # 在每个象限中心标注编号（顺序与line_params_list一致）
        quadrant_centers = [
            (W // 4, H // 4),         # 1 左上
            (W // 4, 3 * H // 4),     # 2 左下
            (3 * W // 4, H // 4),     # 3 右上
            (3 * W // 4, 3 * H // 4)  # 4 右下
        ]
        for idx, center in enumerate(quadrant_centers):
            cv2.putText(vis, f"{idx+1}", center, cv2.FONT_HERSHEY_SIMPLEX, 2, (255, 255, 0), 4)

        # 1. 边缘检测
        gray = cv2.cvtColor(color_img, cv2.COLOR_BGR2GRAY)
        blurred = cv2.GaussianBlur(gray, (7, 7), 0)
        edges = cv2.Canny(blurred, 50, 150)

        # 2. 获取边缘点的xy和深度D
        ys, xs = np.where(edges > 0)
        ds = depth_img[ys, xs]
        valid = (ds > 0) & (ds < self.depth_threshold)
        xs, ys, ds = xs[valid], ys[valid], ds[valid]

        # 3. 按象限分组并拟合3D直线（先y后x，顺序与编号一致）
        line_params_list = []
        for j in range(2):  # y方向
            for i in range(2):  # x方向
                x_min = 0 if i == 0 else W // 2
                x_max = W // 2 if i == 0 else W
                y_min = 0 if j == 0 else H // 2
                y_max = H // 2 if j == 0 else H
                mask = (xs >= x_min) & (xs < x_max) & (ys >= y_min) & (ys < y_max)
                xs_q, ys_q, ds_q = xs[mask], ys[mask], ds[mask]
                line_params = None
                if len(xs_q) > 20:
                    # 3D直线拟合
                    result = self.fit_line_3d(xs_q, ys_q, ds_q)
                    if result is not None:
                        point, direction = result
                        line_params = (point, direction)
                        # 用RANSAC判断内点（正确点）和外点（故障点）
                        X = np.stack([xs_q, ys_q, ds_q], axis=1)
                        # 这里用2D投影做RANSAC，实际可用3D RANSAC更鲁棒
                        ransac = RANSACRegressor()
                        ransac.fit(xs_q.reshape(-1, 1), ys_q)
                        inlier_mask = ransac.inlier_mask_
                        # 可视化正确点（绿色）和故障点（黑色）
                        for idx in range(len(xs_q)):
                            color = (0, 255, 0) if inlier_mask[idx] else (0, 0, 0)
                            cv2.circle(vis, (int(xs_q[idx]), int(ys_q[idx])), 2, color, -1)
                        # 可视化拟合直线（红色，投影到2D）
                        t = np.linspace(-100, 100, 2)
                        x_line = point[0] + t * direction[0]
                        y_line = point[1] + t * direction[1]
                        pts = np.stack([x_line, y_line], axis=1).astype(np.int32)
                        pts = np.clip(pts, [0, 0], [W-1, H-1])
                        cv2.line(vis, tuple(pts[0]), tuple(pts[1]), (0, 0, 255), 2)
                line_params_list.append(line_params)
        # 4. 计算并可视化中间线（黄色）
        def avg_line(line1, line2):
            if line1 is None or line2 is None:
                return None
            point = (line1[0] + line2[0]) / 2
            direction = (line1[1] + line2[1]) / 2
            norm = np.linalg.norm(direction)
            if norm > 1e-6:
                direction = direction / norm
                return point, direction
            return None

        # 上半区中间线（1、2区）
        if line_params_list[0] is not None and line_params_list[1] is not None:
            mid = avg_line(line_params_list[0], line_params_list[1])
            if mid is not None:
                mid_point, mid_dir = mid
                t = np.linspace(-100, 100, 2)
                x_line = mid_point[0] + t * mid_dir[0]
                y_line = mid_point[1] + t * mid_dir[1]
                pts = np.stack([x_line, y_line], axis=1).astype(np.int32)
                pts = np.clip(pts, [0, 0], [W-1, H-1])
                cv2.line(vis, tuple(pts[0]), tuple(pts[1]), (0, 255, 255), 3)  # 黄色

        # 下半区中间线（3、4区）
        if line_params_list[2] is not None and line_params_list[3] is not None:
            mid = avg_line(line_params_list[2], line_params_list[3])
            if mid is not None:
                mid_point, mid_dir = mid
                t = np.linspace(-100, 100, 2)
                x_line = mid_point[0] + t * mid_dir[0]
                y_line = mid_point[1] + t * mid_dir[1]
                pts = np.stack([x_line, y_line], axis=1).astype(np.int32)
                pts = np.clip(pts, [0, 0], [W-1, H-1])
                cv2.line(vis, tuple(pts[0]), tuple(pts[1]), (0, 255, 255), 3)  # 黄色

        return line_params_list, vis

if __name__ == "__main__":
    # 示例：假设有彩色图像和深度图像
    color_img = cv2.imread("test_pipe.jpg")
    depth_img = cv2.imread("test_pipe_depth.png", cv2.IMREAD_UNCHANGED)
    tracker = PipeTracker(depth_threshold=2000)
    line_params_list, vis = tracker.track(color_img, depth_img)
    print("各象限3D直线参数:", line_params_list)
    cv2.imshow("Pipe 3D Line Fitting (Quadrants)", vis)
    cv2.waitKey(0)
    cv2.destroyAllWindows()