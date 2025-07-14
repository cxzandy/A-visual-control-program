import pyrealsense2 as rs
import numpy as np
import cv2

class DepthEstimator:
    def __init__(self, width=640, height=480, fps=30):
        self.pipeline = rs.pipeline()
        config = rs.config()
        config.enable_stream(rs.stream.depth, width, height, rs.format.z16, fps)
        config.enable_stream(rs.stream.color, width, height, rs.format.bgr8, fps)
        self.pipeline.start(config)
        self.align = rs.align(rs.stream.color)

    def get_aligned_frames(self):
        frames = self.pipeline.wait_for_frames()
        aligned_frames = self.align.process(frames)
        depth_frame = aligned_frames.get_depth_frame()
        color_frame = aligned_frames.get_color_frame()
        if not depth_frame or not color_frame:
            return None, None
        depth_image = np.asanyarray(depth_frame.get_data())
        color_image = np.asanyarray(color_frame.get_data())
        return color_image, depth_image, depth_frame

    def get_distance(self, depth_frame, x, y):
        # 获取像素点(x, y)的深度（单位：米）
        return depth_frame.get_distance(x, y)

    def release(self):
        self.pipeline.stop()
