#!/usr/bin/env python3
"""
USB相机测试程序
专门测试USB相机的连接和图像获取功能

功能：
- 检测可用的USB相机
- 测试图像获取
- 保存测试图像
- 验证图像质量

作者: cxzandy
日期: 2025-07-29
"""

import sys
import os
import cv2
import numpy as np
from datetime import datetime

# 添加项目根目录到路径
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

def test_usb_cameras():
    """测试所有可用的USB相机"""
    print("📷 USB相机连接测试")
    print("=" * 40)
    
    available_cameras = []
    
    # 检测相机 (索引0-5)
    for i in range(6):
        print(f"\n🔍 测试相机索引 {i}...")
        
        cap = cv2.VideoCapture(i)
        if cap.isOpened():
            # 设置分辨率
            cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
            cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
            
            # 尝试获取图像
            ret, frame = cap.read()
            if ret and frame is not None:
                h, w = frame.shape[:2]
                print(f"✅ 相机 {i} 可用 - 分辨率: {w}x{h}")
                
                # 保存测试图像
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"usb_camera_{i}_test_{timestamp}.jpg"
                cv2.imwrite(filename, frame)
                print(f"   📸 测试图像已保存: {filename}")
                
                # 获取相机属性
                fps = cap.get(cv2.CAP_PROP_FPS)
                print(f"   📊 FPS: {fps}")
                
                available_cameras.append({
                    'index': i,
                    'resolution': (w, h),
                    'fps': fps,
                    'test_image': filename
                })
            else:
                print(f"❌ 相机 {i} 无法获取图像")
        else:
            print(f"❌ 相机 {i} 无法打开")
            
        cap.release()
    
    return available_cameras

def test_camera_streaming(camera_index=0, duration=10):
    """测试相机实时流"""
    print(f"\n📹 测试相机 {camera_index} 实时流 ({duration}秒)...")
    
    cap = cv2.VideoCapture(camera_index)
    if not cap.isOpened():
        print(f"❌ 无法打开相机 {camera_index}")
        return False
    
    # 设置分辨率
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
    
    frame_count = 0
    start_time = datetime.now()
    
    try:
        print("🎬 开始视频流测试 (按 'q' 退出)...")
        
        while True:
            ret, frame = cap.read()
            if not ret:
                print("❌ 无法获取图像帧")
                break
            
            frame_count += 1
            
            # 添加信息到图像
            cv2.putText(frame, f"Camera {camera_index}", (10, 30), 
                       cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
            cv2.putText(frame, f"Frame: {frame_count}", (10, 60), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
            
            # 计算FPS
            elapsed = (datetime.now() - start_time).total_seconds()
            if elapsed > 0:
                current_fps = frame_count / elapsed
                cv2.putText(frame, f"FPS: {current_fps:.1f}", (10, 90), 
                           cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
            
            # 显示图像
            cv2.imshow(f'USB Camera {camera_index} Test', frame)
            
            # 检查按键
            key = cv2.waitKey(1) & 0xFF
            if key == ord('q'):
                print("👍 用户退出测试")
                break
            
            # 时间限制
            if elapsed > duration:
                print(f"⏰ {duration}秒测试完成")
                break
    
    except Exception as e:
        print(f"❌ 视频流测试失败: {e}")
        return False
    
    finally:
        cap.release()
        cv2.destroyAllWindows()
    
    # 计算统计信息
    total_time = (datetime.now() - start_time).total_seconds()
    avg_fps = frame_count / total_time if total_time > 0 else 0
    
    print(f"✅ 视频流测试完成")
    print(f"   总帧数: {frame_count}")
    print(f"   总时间: {total_time:.2f}秒")
    print(f"   平均FPS: {avg_fps:.2f}")
    
    return True

def test_image_processing(camera_index=0):
    """测试图像处理功能"""
    print(f"\n🖼️ 测试相机 {camera_index} 图像处理...")
    
    cap = cv2.VideoCapture(camera_index)
    if not cap.isOpened():
        print(f"❌ 无法打开相机 {camera_index}")
        return False
    
    # 获取一帧用于处理
    ret, frame = cap.read()
    cap.release()
    
    if not ret or frame is None:
        print("❌ 无法获取图像帧")
        return False
    
    print(f"✅ 原始图像: {frame.shape}")
    
    try:
        # 转换为灰度图
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        print(f"✅ 灰度转换: {gray.shape}")
        
        # 边缘检测
        edges = cv2.Canny(gray, 50, 150)
        print(f"✅ 边缘检测: {edges.shape}")
        
        # 模糊处理
        blurred = cv2.GaussianBlur(frame, (15, 15), 0)
        print(f"✅ 模糊处理: {blurred.shape}")
        
        # 保存处理结果
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        cv2.imwrite(f"usb_camera_{camera_index}_original_{timestamp}.jpg", frame)
        cv2.imwrite(f"usb_camera_{camera_index}_gray_{timestamp}.jpg", gray)
        cv2.imwrite(f"usb_camera_{camera_index}_edges_{timestamp}.jpg", edges)
        cv2.imwrite(f"usb_camera_{camera_index}_blurred_{timestamp}.jpg", blurred)
        
        print(f"✅ 处理结果已保存")
        return True
        
    except Exception as e:
        print(f"❌ 图像处理失败: {e}")
        return False

def main():
    """主函数"""
    print("🔧 USB相机测试工具")
    print("适用于挑战杯2.0系统")
    print("=" * 50)
    
    # 1. 检测可用相机
    cameras = test_usb_cameras()
    
    if not cameras:
        print("\n❌ 未找到可用的USB相机")
        print("💡 请检查:")
        print("   1. USB相机是否正确连接")
        print("   2. 相机驱动是否安装")
        print("   3. 相机是否被其他程序占用")
        return False
    
    print(f"\n🎉 找到 {len(cameras)} 个可用相机:")
    for cam in cameras:
        print(f"   📷 相机 {cam['index']}: {cam['resolution']} @ {cam['fps']} FPS")
    
    # 2. 选择主相机进行详细测试
    primary_camera = cameras[0]['index']
    print(f"\n🎯 使用相机 {primary_camera} 进行详细测试...")
    
    # 3. 图像处理测试
    if not test_image_processing(primary_camera):
        print("❌ 图像处理测试失败")
        return False
    
    # 4. 询问是否进行实时流测试
    try:
        choice = input(f"\n是否测试相机 {primary_camera} 的实时视频流? (y/n): ").lower()
        if choice in ['y', 'yes']:
            if not test_camera_streaming(primary_camera, duration=10):
                print("❌ 视频流测试失败")
                return False
    except KeyboardInterrupt:
        print("\n⚠️ 用户跳过视频流测试")
    
    # 5. 生成测试报告
    print("\n" + "="*50)
    print("📊 USB相机测试报告")
    print("="*50)
    print(f"测试时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"可用相机数量: {len(cameras)}")
    print(f"推荐使用: 相机 {primary_camera}")
    print()
    print("📋 配置建议:")
    print(f"   在 src/config.py 中设置:")
    print(f"   CAMERA_TYPE = 'usb'")
    print(f"   USB_CAMERA_INDEX = {primary_camera}")
    print()
    print("🚀 下一步:")
    print("   1. 运行完整系统: python src/main.py --mode demo")
    print("   2. 测试障碍物检测: python test_obstacle_avoidance.py")
    print("   3. 启动Web界面: python web/web_simple.py")
    
    return True

if __name__ == "__main__":
    try:
        success = main()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n⚠️ 用户中断测试")
        sys.exit(0)
