import pyrealsense2 as rs
import numpy as np
import cv2

class DepthEstimator:
    def __init__(self, camera_instance=None, width=640, height=480, fps=30):
        """
        初始化深度估计器
        Args:
            camera_instance: 可选的RealSenseCapture实例，如果提供则共享使用
            width, height, fps: 当camera_instance为None时使用的配置
        """
        self.camera_instance = camera_instance
        self.align = rs.align(rs.stream.color)
        
        if camera_instance is None:
            # 独立模式：创建自己的管道
            self.pipeline = rs.pipeline()
            config = rs.config()
            config.enable_stream(rs.stream.depth, width, height, rs.format.z16, fps)
            config.enable_stream(rs.stream.color, width, height, rs.format.bgr8, fps)
            self.pipeline.start(config)
            self.owns_pipeline = True
        else:
            # 共享模式：使用传入的相机实例
            self.pipeline = camera_instance.pipeline
            self.owns_pipeline = False

    def get_aligned_frames(self):
        """获取对齐的帧"""
        try:
            frames = self.pipeline.wait_for_frames()
            aligned_frames = self.align.process(frames)
            depth_frame = aligned_frames.get_depth_frame()
            color_frame = aligned_frames.get_color_frame()
            if not depth_frame or not color_frame:
                return None, None, None
            depth_image = np.asanyarray(depth_frame.get_data())
            color_image = np.asanyarray(color_frame.get_data())
            return color_image, depth_image, depth_frame
        except Exception as e:
            print(f"获取对齐帧失败: {e}")
            return None, None, None

    def get_distance(self, depth_frame, x, y):
        """获取像素点(x, y)的深度（单位：米）"""
        try:
            return depth_frame.get_distance(x, y)
        except Exception as e:
            print(f"获取距离失败: {e}")
            return 0.0

    def release(self):
        """释放资源"""
        if self.owns_pipeline:
            try:
                self.pipeline.stop()
            except Exception as e:
                print(f"停止管道失败: {e}")
