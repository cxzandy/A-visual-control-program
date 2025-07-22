import os
import numpy as np
from camera.stereo_capture import StereoCamera

# Try to import Open3D, fallback if not available
try:
    import open3d as o3d
    OPEN3D_AVAILABLE = True
except ImportError as e:
    print(f"Warning: Open3D not available ({e}). Using fallback implementation.")
    OPEN3D_AVAILABLE = False

def save_point_cloud(points, colors, filename):
    """
    保存点云为PLY文件
    """
    if OPEN3D_AVAILABLE:
        # Use Open3D if available
        pc = o3d.geometry.PointCloud()
        pc.points = o3d.utility.Vector3dVector(points)
        pc.colors = o3d.utility.Vector3dVector(colors)
        o3d.io.write_point_cloud(filename, pc)
        print(f"点云已保存到: {filename}")
    else:
        # Fallback: save as simple PLY format
        save_point_cloud_fallback(points, colors, filename)

def save_point_cloud_fallback(points, colors, filename):
    """
    Fallback implementation to save point cloud without Open3D
    """
    try:
        with open(filename, 'w') as f:
            # PLY header
            f.write("ply\n")
            f.write("format ascii 1.0\n")
            f.write(f"element vertex {len(points)}\n")
            f.write("property float x\n")
            f.write("property float y\n")
            f.write("property float z\n")
            f.write("property uchar red\n")
            f.write("property uchar green\n")
            f.write("property uchar blue\n")
            f.write("end_header\n")
            
            # Write point data
            for point, color in zip(points, colors):
                r, g, b = (color * 255).astype(int)
                f.write(f"{point[0]:.6f} {point[1]:.6f} {point[2]:.6f} {r} {g} {b}\n")
        
        print(f"点云已保存到: {filename} (使用fallback实现)")
    except Exception as e:
        print(f"保存点云失败: {e}")

class PointCloudGenerator:
    """点云生成器类"""
    
    def __init__(self, intrinsics_path="data/calib/config/d455_intrinsics.npz"):
        """
        初始化点云生成器
        
        Args:
            intrinsics_path: 相机内参文件路径
        """
        self.intrinsics_path = intrinsics_path
        self.camera_matrix = None
        self.load_intrinsics()
        
    def load_intrinsics(self):
        """加载相机内参"""
        try:
            if os.path.exists(self.intrinsics_path):
                calib = np.load(self.intrinsics_path)
                self.camera_matrix = calib["camera_matrix"]
                print(f"成功加载相机内参: {self.intrinsics_path}")
            else:
                print(f"警告: 未找到相机内参文件: {self.intrinsics_path}")
                # 使用默认内参
                self.camera_matrix = np.array([[615.0, 0, 320.0],
                                             [0, 615.0, 240.0],
                                             [0, 0, 1.0]])
        except Exception as e:
            print(f"加载相机内参失败: {e}")
            # 使用默认内参
            self.camera_matrix = np.array([[615.0, 0, 320.0],
                                         [0, 615.0, 240.0],
                                         [0, 0, 1.0]])
    
    def generate_point_cloud(self, color_img, depth_img, save_path=None):
        """
        从彩色图像和深度图像生成点云
        
        Args:
            color_img: 彩色图像
            depth_img: 深度图像
            save_path: 保存路径（可选）
            
        Returns:
            points: 点云坐标
            colors: 点云颜色
        """
        if self.camera_matrix is None:
            print("相机内参未加载")
            return None, None
            
        fx = self.camera_matrix[0, 0]
        fy = self.camera_matrix[1, 1]
        cx = self.camera_matrix[0, 2]
        cy = self.camera_matrix[1, 2]
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
        
        if save_path:
            os.makedirs(os.path.dirname(save_path), exist_ok=True)
            save_point_cloud(points, colors, save_path)
            
        return points, colors

def generate_point_cloud(save_path="data/point_cloud.ply", intrinsics_path="data/camera_intrinsics.npz"):
    """向后兼容的函数版本"""
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

