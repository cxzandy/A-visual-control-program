import cv2
import numpy as np
import glob
import os

def check_realsense_connection():
    """
    检查与RealSense相机的连接。
    Returns:
        bool: 如果连接成功则返回 True, 否则返回 False。
    """
    try:
        import pyrealsense2 as rs
    except ImportError:
        print("错误：未安装pyrealsense2库。")
        return False
        
    pipeline = rs.pipeline()
    try:
        print("正在尝试连接到RealSense相机...")
        config = rs.config()
        # 尝试配置并启动一个数据流来确认连接
        config.enable_stream(rs.stream.depth, 640, 480, rs.format.z16, 30)
        pipeline.start(config)
        print("成功连接到RealSense相机。")
        # 等待一帧以确保数据流正常
        pipeline.wait_for_frames()
        return True
    except RuntimeError as e:
        print(f"错误：无法连接到RealSense相机。")
        print(f"详细信息: {e}")
        return False
    finally:
        # 确保pipeline在任何情况下都能被停止
        pipeline.stop()
        print("相机连接测试完成。")

def calibrate_camera(images_dir, chessboard_size=(9, 6), square_size=0.025, save_path="config/d455_intrinsics.npz"):
    """
    使用棋盘格图片对相机进行标定。
    Args:
        images_dir (str): 存放棋盘格标定图片的文件夹路径。
        chessboard_size (tuple): 棋盘格内部角点的数量（列, 行）。
        square_size (float): 棋盘格方块的实际边长（单位：米）。
        save_path (str): 标定参数文件的保存路径。
    Returns:
        tuple: (camera_matrix, distortion_coeffs) 如果成功，否则返回 (None, None)
    """
    print("\n开始相机标定流程...")
    # 准备棋盘格角点的世界坐标 (0,0,0), (1,0,0), (2,0,0) ....,(8,5,0)
    objp = np.zeros((chessboard_size[0] * chessboard_size[1], 3), np.float32)
    objp[:, :2] = np.mgrid[0:chessboard_size[0], 0:chessboard_size[1]].T.reshape(-1, 2)
    objp *= square_size

    # 用于存储所有图像的世界坐标点和图像坐标点
    objpoints = []  # 3D点 (世界坐标系)
    imgpoints = []  # 2D点 (图像平面)

    # 检查图片路径是否存在
    if not os.path.isdir(images_dir):
        print(f"错误：图片文件夹不存在 -> {images_dir}")
        return None, None
        
    images = glob.glob(os.path.join(images_dir, '*.jpg'))
    if len(images) == 0:
        print(f"未在 '{images_dir}' 文件夹中找到 .jpg 格式的标定图片。")
        return None, None

    print(f"找到 {len(images)} 张图片用于标定。")

    for fname in images:
        img = cv2.imread(fname)
        if img is None:
            print(f"无法读取图片: {fname}")
            continue
            
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

        # 寻找棋盘格角点
        ret, corners = cv2.findChessboardCorners(gray, chessboard_size, None)

        if ret:
            objpoints.append(objp)
            # 提高角点检测精度
            corners2 = cv2.cornerSubPix(gray, corners, (11, 11), (-1, -1),
                                        criteria=(cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 30, 0.001))
            imgpoints.append(corners2)

            # 绘制并显示角点（可选）
            cv2.drawChessboardCorners(img, chessboard_size, corners2, ret)
            cv2.imshow('Corners Found', img)
            cv2.waitKey(500)  # 等待0.5秒
        else:
            print(f"在图片 {os.path.basename(fname)} 中未能检测到棋盘格角点。")

    cv2.destroyAllWindows()

    if len(objpoints) < 5: # 至少需要几张有效的图片才能得到可靠的结果
        print(f"错误：检测到角点的有效图片数量不足 ({len(objpoints)} 张)，无法进行标定。")
        return None, None

    print("\n正在计算相机内参和畸变系数...")
    # 执行相机标定
    ret, mtx, dist, rvecs, tvecs = cv2.calibrateCamera(
        objpoints, imgpoints, gray.shape[::-1], None, None)

    if not ret:
        print("相机标定失败。")
        return None, None

    print("相机标定成功！")
    print("相机内参矩阵 (mtx):")
    print(mtx)
    print("\n畸变系数 (dist):")
    print(dist)

    # 确保保存路径的文件夹存在
    save_dir = os.path.dirname(save_path)
    if save_dir and not os.path.exists(save_dir):
        os.makedirs(save_dir)
        print(f"已创建文件夹: {save_dir}")

    # 保存标定结果
    np.savez(save_path, mtx=mtx, dist=dist, rvecs=rvecs, tvecs=tvecs)
    print(f"\n标定参数已成功保存到: {save_path}")
    
    return mtx, dist
