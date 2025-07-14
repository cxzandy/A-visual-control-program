import pyrealsense2 as rs
import numpy as np
import cv2

class RealSenseCapture:
    """RealSense D455 相机采集类"""
    
    def __init__(self, width=1280, height=720, fps=30):
        """
        初始化RealSense相机
        Args:
            width (int): 图像宽度
            height (int): 图像高度  
            fps (int): 帧率
        """
        self.pipeline = rs.pipeline()
        self.config = rs.config()
        
        # 配置深度和彩色流
        self.config.enable_stream(rs.stream.depth, width, height, rs.format.z16, fps)
        self.config.enable_stream(rs.stream.color, width, height, rs.format.bgr8, fps)
        
        # 启动管道
        self.pipeline.start(self.config)
        print(f"RealSense相机已启动: {width}x{height} @ {fps}fps")

    def get_frames(self):
        """
        获取深度和彩色图像帧
        Returns:
            tuple: (color_image, depth_image) 或 (None, None) 如果失败
        """
        try:
            # 等待帧
            frames = self.pipeline.wait_for_frames()
            depth_frame = frames.get_depth_frame()
            color_frame = frames.get_color_frame()
            
            if not depth_frame or not color_frame:
                return None, None
                
            # 转换为numpy数组
            depth_image = np.asanyarray(depth_frame.get_data())
            color_image = np.asanyarray(color_frame.get_data())
            
            return color_image, depth_image
            
        except Exception as e:
            print(f"获取帧失败: {e}")
            return None, None

    def stop(self):
        """停止相机"""
        try:
            self.pipeline.stop()
            print("RealSense相机已停止")
        except Exception as e:
            print(f"停止相机失败: {e}")
            
    def release(self):
        """释放资源 (兼容旧接口)"""
        self.stop()

# 保持向后兼容性
StereoCamera = RealSenseCapture