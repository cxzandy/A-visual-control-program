"""
显示工具模块
处理OpenCV窗口显示和图像可视化
"""

import cv2
import numpy as np

def create_window(window_name: str, width: int = 640, height: int = 480):
    """
    创建OpenCV窗口
    
    Args:
        window_name: 窗口名称
        width: 窗口宽度
        height: 窗口高度
    """
    try:
        # 创建窗口并设置属性
        cv2.namedWindow(window_name, cv2.WINDOW_AUTOSIZE)
        cv2.resizeWindow(window_name, width, height)
        
        # 设置窗口位置（可选）
        cv2.moveWindow(window_name, 100, 100)
        
        return True
    except Exception as e:
        print(f"创建窗口失败: {e}")
        return False

def show_image(window_name: str, image, wait_key: int = 1):
    """
    在指定窗口显示图像
    
    Args:
        window_name: 窗口名称
        image: 要显示的图像
        wait_key: 等待按键时间(ms)
        
    Returns:
        按下的键值，如果返回 ord('q') 表示退出
    """
    try:
        if image is not None:
            cv2.imshow(window_name, image)
            return cv2.waitKey(wait_key) & 0xFF
        return -1
    except Exception as e:
        print(f"显示图像失败: {e}")
        return -1

def close_window(window_name: str = None):
    """
    关闭窗口
    
    Args:
        window_name: 窗口名称，如果为None则关闭所有窗口
    """
    try:
        if window_name:
            cv2.destroyWindow(window_name)
        else:
            cv2.destroyAllWindows()
    except Exception as e:
        print(f"关闭窗口失败: {e}")

def add_text_overlay(image, text: str, position: tuple = (10, 30), 
                    font_scale: float = 0.7, color: tuple = (0, 255, 0), 
                    thickness: int = 2):
    """
    在图像上添加文字覆盖
    
    Args:
        image: 输入图像
        text: 要添加的文字
        position: 文字位置 (x, y)
        font_scale: 字体大小
        color: 文字颜色 (B, G, R)
        thickness: 文字粗细
        
    Returns:
        添加文字后的图像
    """
    try:
        image_with_text = image.copy()
        cv2.putText(image_with_text, text, position, cv2.FONT_HERSHEY_SIMPLEX, 
                   font_scale, color, thickness, cv2.LINE_AA)
        return image_with_text
    except Exception as e:
        print(f"添加文字失败: {e}")
        return image

def add_fps_overlay(image, fps: float, position: tuple = (10, 30)):
    """
    在图像上添加FPS显示
    
    Args:
        image: 输入图像
        fps: FPS值
        position: 显示位置
        
    Returns:
        添加FPS显示的图像
    """
    try:
        fps_text = f"{fps:.1f}fps"
        return add_text_overlay(image, fps_text, position, color=(0, 255, 0), font_scale=0.6)
    except Exception as e:
        print(f"添加FPS显示失败: {e}")
        return image

def add_status_overlay(image, status_dict: dict, start_y: int = 30):
    """
    在图像上添加状态信息
    
    Args:
        image: 输入图像
        status_dict: 状态字典
        start_y: 起始Y位置
        
    Returns:
        添加状态信息的图像
    """
    try:
        result_image = image.copy()
        y_offset = start_y
        
        for key, value in status_dict.items():
            text = f"{key}: {value}"
            color = (0, 255, 0) if value == "OK" else (0, 0, 255)  # 绿色OK，红色ERROR
            result_image = add_text_overlay(result_image, text, (10, y_offset), 
                                          font_scale=0.5, color=color)
            y_offset += 20
            
        return result_image
    except Exception as e:
        print(f"添加状态信息失败: {e}")
        return image

class DisplayManager:
    """显示管理器"""
    
    def __init__(self):
        self.windows = {}
        self.enabled = True
    
    def create_window(self, name: str, width: int = 640, height: int = 480):
        """创建窗口"""
        if not self.enabled:
            return False
            
        if create_window(name, width, height):
            self.windows[name] = {"width": width, "height": height}
            return True
        return False
    
    def show_image(self, window_name: str, image, wait_key: int = 1):
        """显示图像"""
        if not self.enabled:
            return -1
            
        if window_name not in self.windows:
            self.create_window(window_name)
            
        return show_image(window_name, image, wait_key)
    
    def close_window(self, window_name: str = None):
        """关闭窗口"""
        if window_name and window_name in self.windows:
            close_window(window_name)
            del self.windows[window_name]
        else:
            close_window()
            self.windows.clear()
    
    def disable(self):
        """禁用显示"""
        self.enabled = False
        self.close_window()
    
    def enable(self):
        """启用显示"""
        self.enabled = True

# 全局显示管理器实例
display_manager = DisplayManager()
