import pyrealsense2 as rs
import numpy as np
import cv2

class StereoCamera:
    def __init__(self, width=640, height=480, fps=30):
        self.pipeline = rs.pipeline()
        config = rs.config()
        config.enable_stream(rs.stream.depth, width, height, rs.format.z16, fps)
        config.enable_stream(rs.stream.color, width, height, rs.format.bgr8, fps)
        self.pipeline.start(config)

    def get_frames(self):
        frames = self.pipeline.wait_for_frames()
        depth_frame = frames.get_depth_frame()
        color_frame = frames.get_color_frame()
        if not depth_frame or not color_frame:
            return None, None
        depth_image = np.asanyarray(depth_frame.get_data())
        color_image = np.asanyarray(color_frame.get_data())
        return color_image, depth_image

    def release(self):
        self.pipeline.stop()