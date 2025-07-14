import os
import numpy as np
import open3d as o3d
from camera.stereo_capture import StereoCamera

def save_point_cloud(points, colors, filename):
    """
    保存点云为PLY文件
    """
    pc = o3d.geometry.PointCloud()
    pc.points = o3d.utility.Vector3dVector(points)
    pc.colors = o3d.utility.Vector3dVector(colors)
    o3d.io.write_point_cloud(filename, pc)
    print(f"点云已保存到: {filename}")

def generate_point_cloud(save_path="data/point_cloud.ply", intrinsics_path="data/camera_intrinsics.npz"):
    cam = StereoCamera()
    color_img, depth_img = cam.get_frames()
    cam.release()
    if color_img is None or depth_img is None:
        print("未获取到图像")
        return

    # 从标定文件读取相机内参
    if not os.path.exists(intrinsics_path):
        print(f"未找到相机内参文件: {intrinsics_path}")
        return
    calib = np.load(intrinsics_path)
    mtx = calib["camera_matrix"]
    fx = mtx[0, 0]
    fy = mtx[1, 1]
    cx = mtx[0, 2]
    cy = mtx[1, 2]
    scale = 1000.0  # 深度缩放（如单位为mm则为1000）

    points = []
    colors = []
    for v in range(depth_img.shape[0]):
        for u in range(depth_img.shape[1]):
            d = depth_img[v, u]
            if d == 0:
                continue
            z = d / scale
            x = (u - cx) * z / fx
            y = (v - cy) * z / fy
            points.append([x, y, z])
            colors.append(color_img[v, u] / 255.0)
    points = np.array(points)
    colors = np.array(colors)

    os.makedirs(os.path.dirname(save_path), exist_ok=True)
    save_point_cloud(points, colors, save_path)

