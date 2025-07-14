import cv2
import numpy as np
import glob
import os

def calibrate_camera(images_dir, chessboard_size=(9,6), square_size=1.0, save_path="calib_data.npz"):
    # 准备棋盘格角点的世界坐标
    objp = np.zeros((chessboard_size[0]*chessboard_size[1],3), np.float32)
    objp[:,:2] = np.mgrid[0:chessboard_size[0],0:chessboard_size[1]].T.reshape(-1,2)
    objp *= square_size

    objpoints = [] # 3d点
    imgpoints = [] # 2d点

    images = glob.glob(os.path.join(images_dir, '*.jpg'))
    if len(images) == 0:
        print("未找到标定图片")
        return

    for fname in images:
        img = cv2.imread(fname)
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        ret, corners = cv2.findChessboardCorners(gray, chessboard_size, None)
        if ret:
            objpoints.append(objp)
            corners2 = cv2.cornerSubPix(gray, corners, (11,11), (-1,-1),
                                        criteria=(cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 30, 0.001))
            imgpoints.append(corners2)
            cv2.drawChessboardCorners(img, chessboard_size, corners2, ret)
            cv2.imshow('Corners', img)
            cv2.waitKey(100)
    cv2.destroyAllWindows()

    if len(objpoints) < 1:
        print("未检测到足够的角点")
        return

    ret, mtx, dist, rvecs, tvecs = cv2.calibrateCamera(
        objpoints, imgpoints, gray.shape[::-1], None, None)
    print("相机内参矩阵：\n", mtx)
    print("畸变系数：\n", dist)

    np.savez(save_path, mtx=mtx, dist=dist, rvecs=rvecs, tvecs=tvecs)
    print(f"标定参数已保存到 {save_path}")
