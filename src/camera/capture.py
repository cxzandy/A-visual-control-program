"""
相机模块 - 统一相机接口
Camera Module - Unified Camera Interface

整合RealSense相机、USB相机和相关功能
"""

import os
import cv2
import numpy as np
import pyrealsense2 as rs
from typing import Optional, Tuple, Union
import logging

# 尝试导入Open3D，如果没有则使用fallback实现
try:
    import open3d as o3d
    OPEN3D_AVAILABLE = True
except ImportError:
    OPEN3D_AVAILABLE = False

logger = logging.getLogger(__name__)

class CameraInterface:
    """相机接口基类"""
    
    def __init__(self):
        self.width = 640
        self.height = 480
        self.fps = 30
    
    def get_frames(self) -> Tuple[Optional[np.ndarray], Optional[np.ndarray]]:
        """获取彩色图像和深度图像"""
        raise NotImplementedError
    
    def stop(self):
        """停止相机"""
        raise NotImplementedError
    
    def is_opened(self) -> bool:
        """检查相机是否打开"""
        raise NotImplementedError

class RealSenseCapture(CameraInterface):
    """RealSense D455 相机采集类"""
    
    def __init__(self, width=640, height=480, fps=30):
        super().__init__()
        self.pipeline = rs.pipeline()
        self.config = rs.config()
        self.align = None
        
        # 尝试不同的配置
        configs_to_try = [
            (width, height, fps),
            (640, 480, 30),  # 备用配置1
            (1280, 720, 15), # 备用配置2
            (848, 480, 30),  # 备用配置3
        ]
        
        for w, h, f in configs_to_try:
            try:
                # 清除之前的配置
                self.config = rs.config()
                
                # 配置深度和彩色流
                self.config.enable_stream(rs.stream.depth, w, h, rs.format.z16, f)
                self.config.enable_stream(rs.stream.color, w, h, rs.format.bgr8, f)
                
                # 启动管道
                profile = self.pipeline.start(self.config)
                
                # 创建对齐对象（深度对齐到彩色）
                align_to = rs.stream.color
                self.align = rs.align(align_to)
                
                self.width = w
                self.height = h
                self.fps = f
                logger.info(f"RealSense相机已启动: {w}x{h} @ {f}fps")
                return
                
            except Exception as e:
                logger.warning(f"尝试配置 {w}x{h}@{f}fps 失败: {e}")
                try:
                    self.pipeline.stop()
                except:
                    pass
                continue
        
        raise RuntimeError("无法启动RealSense相机，请检查连接")
    
    def get_frames(self) -> Tuple[Optional[np.ndarray], Optional[np.ndarray]]:
        """获取对齐的彩色和深度图像"""
        try:
            frames = self.pipeline.wait_for_frames()
            
            # 对齐深度到彩色
            if self.align:
                aligned_frames = self.align.process(frames)
                color_frame = aligned_frames.get_color_frame()
                depth_frame = aligned_frames.get_depth_frame()
            else:
                color_frame = frames.get_color_frame()
                depth_frame = frames.get_depth_frame()
            
            if not color_frame or not depth_frame:
                return None, None
            
            # 转换为numpy数组
            color_image = np.asanyarray(color_frame.get_data())
            depth_image = np.asanyarray(depth_frame.get_data())
            
            return color_image, depth_image
            
        except Exception as e:
            logger.error(f"获取RealSense帧失败: {e}")
            return None, None
    
    def stop(self):
        """停止相机"""
        try:
            self.pipeline.stop()
            logger.info("RealSense相机已停止")
        except Exception as e:
            logger.error(f"停止RealSense相机失败: {e}")
    
    def is_opened(self) -> bool:
        """检查相机是否打开"""
        try:
            # 尝试获取一帧来检查状态
            frames = self.pipeline.wait_for_frames(timeout_ms=100)
            return frames is not None
        except:
            return False

class USBCapture(CameraInterface):
    """USB相机采集类"""
    
    def __init__(self, camera_index=0, width=640, height=480):
        super().__init__()
        self.camera_index = camera_index
        self.width = width
        self.height = height
        
        self.cap = cv2.VideoCapture(camera_index)
        
        if not self.cap.isOpened():
            raise RuntimeError(f"无法打开USB相机 {camera_index}")
        
        # 设置分辨率
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, width)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, height)
        
        # 获取实际分辨率
        actual_width = int(self.cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        actual_height = int(self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        actual_fps = self.cap.get(cv2.CAP_PROP_FPS)
        
        self.width = actual_width
        self.height = actual_height
        self.fps = actual_fps
        
        logger.info(f"USB相机已启动: {actual_width}x{actual_height} @ {actual_fps}fps")
    
    def get_frames(self) -> Tuple[Optional[np.ndarray], Optional[np.ndarray]]:
        """获取彩色图像（USB相机没有深度）"""
        try:
            ret, frame = self.cap.read()
            if ret:
                # USB相机没有深度图像，返回None作为深度
                return frame, None
            else:
                return None, None
        except Exception as e:
            logger.error(f"获取USB相机帧失败: {e}")
            return None, None
    
    def stop(self):
        """停止相机"""
        try:
            self.cap.release()
            logger.info("USB相机已停止")
        except Exception as e:
            logger.error(f"停止USB相机失败: {e}")
    
    def is_opened(self) -> bool:
        """检查相机是否打开"""
        return self.cap.isOpened()

class PointCloudGenerator:
    """点云生成器"""
    
    def __init__(self, camera_intrinsics=None):
        """
        初始化点云生成器
        
        Args:
            camera_intrinsics: 相机内参 [fx, fy, cx, cy]
        """
        self.camera_intrinsics = camera_intrinsics or [600.0, 600.0, 320.0, 240.0]
    
    def generate_point_cloud(self, color_image: np.ndarray, depth_image: np.ndarray, 
                           depth_scale: float = 0.001) -> Tuple[np.ndarray, np.ndarray]:
        """
        从RGB-D图像生成点云
        
        Args:
            color_image: 彩色图像
            depth_image: 深度图像
            depth_scale: 深度缩放因子
            
        Returns:
            points: 点云坐标 (N, 3)
            colors: 点云颜色 (N, 3)
        """
        fx, fy, cx, cy = self.camera_intrinsics
        
        # 获取有效深度点
        h, w = depth_image.shape
        
        # 创建坐标网格
        u, v = np.meshgrid(np.arange(w), np.arange(h))
        
        # 获取有效深度点的掩码
        valid_mask = depth_image > 0
        
        # 提取有效点
        u_valid = u[valid_mask]
        v_valid = v[valid_mask]
        z_valid = depth_image[valid_mask] * depth_scale
        
        # 计算3D坐标
        x_valid = (u_valid - cx) * z_valid / fx
        y_valid = (v_valid - cy) * z_valid / fy
        
        # 组合点云坐标
        points = np.column_stack((x_valid, y_valid, z_valid))
        
        # 获取对应的颜色
        colors = color_image[valid_mask] / 255.0  # 归一化到[0,1]
        
        return points, colors
    
    def save_point_cloud(self, points: np.ndarray, colors: np.ndarray, filename: str):
        """保存点云为PLY文件"""
        if OPEN3D_AVAILABLE:
            # 使用Open3D保存
            pcd = o3d.geometry.PointCloud()
            pcd.points = o3d.utility.Vector3dVector(points)
            pcd.colors = o3d.utility.Vector3dVector(colors)
            o3d.io.write_point_cloud(filename, pcd)
            logger.info(f"点云已保存到: {filename}")
        else:
            # Fallback实现
            self._save_point_cloud_fallback(points, colors, filename)
    
    def _save_point_cloud_fallback(self, points: np.ndarray, colors: np.ndarray, filename: str):
        """不使用Open3D的PLY文件保存"""
        os.makedirs(os.path.dirname(filename), exist_ok=True)
        
        with open(filename, 'w') as f:
            # PLY文件头
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
            
            # 写入点数据
            for i in range(len(points)):
                x, y, z = points[i]
                r, g, b = (colors[i] * 255).astype(int)
                f.write(f"{x} {y} {z} {r} {g} {b}\n")
        
        logger.info(f"点云已保存到: {filename} (使用fallback方法)")

def check_realsense_connection() -> bool:
    """检查RealSense相机连接"""
    try:
        ctx = rs.context()
        devices = ctx.query_devices()
        return len(devices) > 0
    except:
        return False

def check_usb_cameras() -> list:
    """检查可用的USB相机"""
    available_cameras = []
    for i in range(6):  # 检查前6个索引
        cap = cv2.VideoCapture(i)
        if cap.isOpened():
            ret, frame = cap.read()
            if ret and frame is not None:
                available_cameras.append(i)
            cap.release()
    return available_cameras

# 向后兼容的别名
StereoCamera = RealSenseCapture
