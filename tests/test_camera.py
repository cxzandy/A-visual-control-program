import sys
import os

# 添加项目根目录到路径
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from src.camera.calibration import calibrate_camera, check_realsense_connection

def main():
    """主函数，执行连接检查和标定。"""
    
    # --- 请在此处配置您的路径和参数 ---
    # 存放棋盘格图片的文件夹路径
    IMAGES_DIRECTORY = "data\\calib"
    # 标定结果的保存路径
    CALIBRATION_FILE_PATH = "data\\calib\\config\\d455_intrinsics.npz"
    # 棋盘格内部角点的数量 (corners_per_row, corners_per_col)
    CHESSBOARD_SIZE = (11, 8)
    # 棋盘格方块的实际边长（单位：米）
    SQUARE_SIZE_METERS = 0.02
    # --- 配置结束 ---

    # 步骤1: 检查与RealSense相机的连接
    if check_realsense_connection():
        # 步骤2: 如果连接成功，则从图片进行标定
        camera_matrix, distortion_coeffs = calibrate_camera(
            images_dir=IMAGES_DIRECTORY,
            chessboard_size=CHESSBOARD_SIZE,
            square_size=SQUARE_SIZE_METERS,
            save_path=CALIBRATION_FILE_PATH
        )
        
        if camera_matrix is not None:
            print("\n相机标定测试成功完成！")
        else:
            print("\n相机标定失败。")
    else:
        print("\n由于相机未连接，标定程序已终止。")
        print("请确保相机已连接并重试。")

if __name__ == "__main__":
    main()