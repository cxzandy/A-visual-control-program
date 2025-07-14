import cv2
import numpy as np
import open3d as o3d
from scipy.interpolate import splprep, splev

class PipeTracker:
    def __init__(self, depth_threshold=1000, camera_intrinsics=None):
        self.depth_threshold = depth_threshold  # mm
        # 相机内参：[fx, fy, cx, cy]
        # fx, fy: 焦距 (像素)
        # cx, cy: 光心 (像素)
        # 这是进行像素坐标到3D点转换的关键。
        # 如果不提供，将使用默认值，但这会导致3D坐标不准确。
        if camera_intrinsics is None:
            print("警告: 未提供相机内参。3D点转换可能不准确。")
            # 默认内参，需要根据你的相机实际参数进行设置
            self.fx = 600.0  # 示例焦距
            self.fy = 600.0
            self.cx = 320.0  # 示例光心 (图像宽度/2)
            self.cy = 240.0  # 示例光心 (图像高度/2)
        else:
            self.fx, self.fy, self.cx, self.cy = camera_intrinsics


    def _pixel_to_3d(self, u, v, depth):
        """
        将像素坐标(u, v)和深度值转换为相机坐标系下的3D点(X, Y, Z)。
        Args:
            u (np.array): 像素列坐标 (x)
            v (np.array): 像素行坐标 (y)
            depth (np.array): 深度值 (mm)
        Returns:
            np.array: 转换后的3D点 (N, 3)
        """
        Z = depth / 1000.0  # 转换为米
        X = (u - self.cx) * Z / self.fx
        Y = (v - self.cy) * Z / self.fy
        return np.stack([X, Y, Z], axis=1)

    def fit_line_3d_ransac_o3d(self, points_3d, distance_threshold=0.01, ransac_n=3, num_iterations=1000):
        """
        使用Open3D的RANSAC算法在3D点集中拟合一条直线。
        Args:
            points_3d (np.array): Nx3的3D点数组。
            distance_threshold (float): 内点到模型的最大距离 (米)。
            ransac_n (int): 用于拟合模型的最小样本点数。
            num_iterations (int): RANSAC迭代次数。
        Returns:
            tuple: (best_line_point, best_line_direction, inlier_mask)
                   如果拟合失败，返回 (None, None, None)。
        """
        if len(points_3d) < ransac_n:
            return None, None, None

        # 将numpy数组转换为Open3D的Vector3dVector
        pcd = o3d.geometry.PointCloud()
        pcd.points = o3d.utility.Vector3dVector(points_3d)

        # 使用Open3D的segment_lines方法进行RANSAC直线拟合
        # 注意: Open3D的segment_lines更适合分割多条线段，这里我们用它做单条线拟合
        # 实际更直接的是用Open3D的sample_points_uniformly选择点，然后自己实现RANSAC for line
        # 或者使用PCL的接口（如果可以引入的话）
        # 这里为了简化，我们假设Open3D的平面拟合可以找到近似线。
        # Open3D没有直接的3D点集到3D直线的RANSAC拟合函数。
        # 我们可以通过拟合一个平面，然后投影所有点到这个平面，再在该平面上拟合直线。
        # 或者，更简单的，仍然用SVD/PCA进行拟合，但先用RANSAC来筛选内点。

        # 方案一：手动RANSAC for 3D Line (更符合您的需求，但需更多代码)
        # 这里为了简化和利用Open3D结构，我们先用一个临时的平面模型作为RANSAC的“间接”模型
        # 更直接的做法是：
        # 从点云中随机选择两个点 (p1, p2)
        # direction = p2 - p1
        # point = p1
        # 计算所有点到这条线的距离
        # 统计内点
        # 循环，找到最优
        # 鉴于此函数已经有了PCA拟合，我们可以在PCA拟合后，用RANSAC来验证并剔除离群点

        # 方案二：利用PCA拟合，并用RANSAC筛选内点
        # 这里的RANSACRegressor是针对2D的，我们不能直接用于3D拟合。
        # 最直接的实现RANSAC 3D Line 拟合会是这样：
        # 1. 随机选择两个点
        # 2. 计算它们确定的直线
        # 3. 统计内点
        # 4. 循环迭代

        # 为了避免重新实现整个3D RANSAC，这里我们继续使用您原有的PCA拟合，
        # 并假设您会根据RANSACRegressor的内点/外点信息在外部进行更准确的过滤。
        # **重要的更新：此处不再使用sklearn的RANSACRegressor，因为它不直接用于3D直线。**
        # 而是提供一个简化的RANSAC框架思路，实际需要您根据需要实现或引入更专业的库。

        # 替代方案: 我们可以用Open3D的segment_plane来找到主要平面，如果管道是直的，这可能有用
        # 或者，如果主要目的是获取inlier_mask，可以自己实现一个简化的RANSAC for line
        best_inlier_mask = np.zeros(len(points_3d), dtype=bool)
        best_num_inliers = -1
        best_line_point = None
        best_line_direction = None

        for _ in range(num_iterations):
            # 随机选择2个点
            indices = np.random.choice(len(points_3d), 2, replace=False)
            p1, p2 = points_3d[indices[0]], points_3d[indices[1]]

            # 定义直线：点p1，方向向量d
            current_direction = p2 - p1
            if np.linalg.norm(current_direction) < 1e-6: # 避免点重合
                continue
            current_direction = current_direction / np.linalg.norm(current_direction) # 归一化方向向量

            # 计算所有点到直线的距离
            # 点 P 到直线 (A, d) 的距离公式: ||(P-A) x d|| / ||d||
            # 由于d已归一化，简化为 ||(P-A) x d||
            vecs = points_3d - p1
            cross_products = np.cross(vecs, current_direction)
            distances = np.linalg.norm(cross_products, axis=1)

            inlier_mask = distances < distance_threshold
            num_inliers = np.sum(inlier_mask)

            if num_inliers > best_num_inliers:
                best_num_inliers = num_inliers
                best_inlier_mask = inlier_mask
                # 用所有内点重新拟合直线（PCA）以获得更精确的模型
                inlier_points = points_3d[inlier_mask]
                if len(inlier_points) >= 2:
                    mean_inlier = np.mean(inlier_points, axis=0)
                    _, _, vh = np.linalg.svd(inlier_points - mean_inlier)
                    best_line_direction = vh[0]
                    best_line_point = mean_inlier
                else:
                    best_line_point = None
                    best_line_direction = None

        return best_line_point, best_line_direction, best_inlier_mask


    def track(self, color_img, depth_img):
        """
        输入:
            color_img: 彩色图像 (H, W, 3)
            depth_img: 深度图像 (H, W) (单位: mm)
        输出:
            line_params_list: 每个象限的3D直线参数 [(point, direction), ...]
            global_pipe_axis_points: 拟合的全局管道轴线点 (N, 3)
            vis: 可视化结果
        """
        H, W = color_img.shape[:2]
        vis = color_img.copy()

        # 绘制象限分割线
        cv2.line(vis, (W // 2, 0), (W // 2, H), (255, 255, 0), 2)
        cv2.line(vis, (0, H // 2), (W, H // 2), (255, 255, 0), 2)

        # 在每个象限中心标注编号（顺序与line_params_list一致）
        # 调整顺序以匹配您的象限遍历 (j then i: 00, 01, 10, 11)
        # 也就是 (左上, 右上, 左下, 右下)
        quadrant_centers_vis = [
            (W // 4, H // 4),         # 1 左上
            (3 * W // 4, H // 4),     # 2 右上
            (W // 4, 3 * H // 4),     # 3 左下
            (3 * W // 4, 3 * H // 4)  # 4 右下
        ]
        for idx, center in enumerate(quadrant_centers_vis):
            cv2.putText(vis, f"{idx+1}", center, cv2.FONT_HERSHEY_SIMPLEX, 2, (255, 255, 0), 4)


        # 1. 边缘检测
        gray = cv2.cvtColor(color_img, cv2.COLOR_BGR2GRAY)
        blurred = cv2.GaussianBlur(gray, (7, 7), 0)
        edges = cv2.Canny(blurred, 50, 150)

        # 2. 获取边缘点的xy和深度D
        ys_px, xs_px = np.where(edges > 0)
        ds = depth_img[ys_px, xs_px] # 深度值，单位mm

        # 转换为3D点
        valid_mask = (ds > 0) & (ds < self.depth_threshold)
        xs_px, ys_px, ds = xs_px[valid_mask], ys_px[valid_mask], ds[valid_mask]
        
        # 将像素坐标和深度转换为相机坐标系下的3D点
        points_3d_all = self._pixel_to_3d(xs_px, ys_px, ds)


        # 3. 按象限分组并拟合3D直线
        line_params_list = []
        quadrant_center_points_3d = [] # 用于全局曲线拟合
        
        # 遍历象限的顺序：左上(0,0), 右上(0,1), 左下(1,0), 右下(1,1)
        for j in range(2):  # y方向 (行)
            for i in range(2):  # x方向 (列)
                x_min_px = 0 if i == 0 else W // 2
                x_max_px = W // 2 if i == 0 else W
                y_min_px = 0 if j == 0 else H // 2
                y_max_px = H // 2 if j == 0 else H

                # 筛选当前象限的像素点
                mask_px = (xs_px >= x_min_px) & (xs_px < x_max_px) & \
                          (ys_px >= y_min_px) & (ys_px < y_max_px)
                
                points_3d_q = points_3d_all[mask_px]
                xs_q_px, ys_q_px = xs_px[mask_px], ys_px[mask_px]


                line_params = None
                if len(points_3d_q) > 20: # 至少需要一些点才能拟合
                    # RANSAC 3D直线拟合
                    point_3d, direction_3d, inlier_mask_3d = self.fit_line_3d_ransac_o3d(
                        points_3d_q, distance_threshold=0.02, ransac_n=2, num_iterations=2000
                    ) # distance_threshold 调整为米

                    if point_3d is not None and direction_3d is not None:
                        line_params = (point_3d, direction_3d)
                        quadrant_center_points_3d.append(point_3d) # 收集拟合出的直线上的点

                        # 可视化内点（绿色）和外点（黑色）
                        for idx in range(len(xs_q_px)):
                            # 如果inlier_mask_3d是所有点的，直接用
                            # 如果fit_line_3d_ransac_o3d返回的是inlier_mask_3d for points_3d_q
                            # 则需要映射回原始索引
                            color = (0, 255, 0) if inlier_mask_3d[idx] else (0, 0, 0)
                            cv2.circle(vis, (int(xs_q_px[idx]), int(ys_q_px[idx])), 2, color, -1)

                        # 可视化拟合直线（红色，投影到2D）
                        # 将3D直线投影回图像平面
                        t = np.linspace(-0.2, 0.2, 10) # 沿直线方向取一些点，单位米
                        line_3d_pts = point_3d + t[:, np.newaxis] * direction_3d
                        
                        # 3D点到像素坐标的转换 (X, Y, Z -> u, v)
                        # u = X * fx / Z + cx
                        # v = Y * fy / Z + cy
                        valid_z = line_3d_pts[:, 2] > 1e-6 # 避免除以零或负深度
                        if np.any(valid_z):
                            u_line = (line_3d_pts[valid_z, 0] * self.fx / line_3d_pts[valid_z, 2] + self.cx).astype(int)
                            v_line = (line_3d_pts[valid_z, 1] * self.fy / line_3d_pts[valid_z, 2] + self.cy).astype(int)
                            
                            pts_2d = np.stack([u_line, v_line], axis=1)
                            
                            # 过滤掉超出图像范围的点，但保留线段的连贯性
                            pts_2d = np.clip(pts_2d, [0, 0], [W-1, H-1])

                            if len(pts_2d) >= 2:
                                for k in range(len(pts_2d) - 1):
                                    cv2.line(vis, tuple(pts_2d[k]), tuple(pts_2d[k+1]), (0, 0, 255), 2) # 红色

                line_params_list.append(line_params)

        # --- 4. 全局管道轴线拟合 (使用样条曲线) ---
        global_pipe_axis_points = None
        if len(quadrant_center_points_3d) >= 2:
            # 将这些拟合出的局部中心点作为全局曲线拟合的控制点
            quadrant_center_points_3d = np.array(quadrant_center_points_3d)

            # 假设管道主要沿某一轴线延伸，我们选择那个轴作为参数化基准
            # 例如，如果管道主要沿Z轴延伸，我们用Z作为参数，拟合 (X, Y) = f(Z)
            # 或者，如果主要沿X轴，用X作为参数，拟合 (Y, Z) = f(X)
            # 找到变化范围最大的轴作为主轴
            ranges = np.max(quadrant_center_points_3d, axis=0) - np.min(quadrant_center_points_3d, axis=0)
            main_axis_idx = np.argmax(ranges)

            # 提取主轴坐标作为曲线的参数 t，并对其他轴进行拟合
            # 为了拟合效果更好，通常需要对这些点进行排序
            sort_indices = np.argsort(quadrant_center_points_3d[:, main_axis_idx])
            sorted_points = quadrant_center_points_3d[sort_indices]

            t_param = sorted_points[:, main_axis_idx]
            x_coords = sorted_points[:, 0]
            y_coords = sorted_points[:, 1]
            z_coords = sorted_points[:, 2]

            # 根据主轴索引，拟合另外两个轴
            if main_axis_idx == 0: # 主轴是X
                p_y, u_y = splprep([y_coords], u=t_param, s=0) # s=0 表示严格通过所有点
                p_z, u_z = splprep([z_coords], u=t_param, s=0)
                # 生成更多点
                t_new = np.linspace(t_param.min(), t_param.max(), 100)
                y_new = splev(t_new, p_y[0])
                z_new = splev(t_new, p_z[0])
                global_pipe_axis_points = np.vstack((t_new, y_new[0], z_new[0])).T
            elif main_axis_idx == 1: # 主轴是Y
                p_x, u_x = splprep([x_coords], u=t_param, s=0)
                p_z, u_z = splprep([z_coords], u=t_param, s=0)
                t_new = np.linspace(t_param.min(), t_param.max(), 100)
                x_new = splev(t_new, p_x[0])
                z_new = splev(t_new, p_z[0])
                global_pipe_axis_points = np.vstack((x_new[0], t_new, z_new[0])).T
            else: # 主轴是Z
                p_x, u_x = splprep([x_coords], u=t_param, s=0)
                p_y, u_y = splprep([y_coords], u=t_param, s=0)
                t_new = np.linspace(t_param.min(), t_param.max(), 100)
                x_new = splev(t_new, p_x[0])
                y_new = splev(t_new, p_y[0])
                global_pipe_axis_points = np.vstack((x_new[0], y_new[0], t_new)).T
            
            # 可视化全局拟合的曲线 (黄色)
            if global_pipe_axis_points is not None and len(global_pipe_axis_points) >= 2:
                # 将3D曲线投影回图像平面
                # u = X * fx / Z + cx
                # v = Y * fy / Z + cy
                valid_z = global_pipe_axis_points[:, 2] > 1e-6
                if np.any(valid_z):
                    u_curve = (global_pipe_axis_points[valid_z, 0] * self.fx / global_pipe_axis_points[valid_z, 2] + self.cx).astype(int)
                    v_curve = (global_pipe_axis_points[valid_z, 1] * self.fy / global_pipe_axis_points[valid_z, 2] + self.cy).astype(int)

                    pts_2d_curve = np.stack([u_curve, v_curve], axis=1)
                    pts_2d_curve = np.clip(pts_2d_curve, [0, 0], [W-1, H-1])

                    if len(pts_2d_curve) >= 2:
                        for k in range(len(pts_2d_curve) - 1):
                            cv2.line(vis, tuple(pts_2d_curve[k]), tuple(pts_2d_curve[k+1]), (0, 255, 255), 3) # 黄色
        
        # 原有的中间线计算（如果需要，可以保留，但全局曲线拟合通常会取代它）
        # 这里为了保持代码简洁，将原有的avg_line函数移除，因为全局曲线更全面
        # 如果需要显示局部平均线，可以在这里重新添加。

        return line_params_list, global_pipe_axis_points, vis

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