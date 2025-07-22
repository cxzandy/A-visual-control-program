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
                self.pipeline.start(self.config)
                print(f"RealSense相机已启动: {w}x{h} @ {f}fps")
                self.width = w
                self.height = h
                self.fps = f
                return
                
            except Exception as e:
                print(f"尝试配置 {w}x{h}@{f}fps 失败: {e}")
                try:
                    self.pipeline.stop()
                except:
                    pass
                continue
        
        # 如果所有配置都失败，抛出异常
        raise Exception("无法启动RealSense相机，已尝试所有可用配置")

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