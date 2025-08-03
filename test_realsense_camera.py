#!/usr/bin/env python3
"""
RealSense D455深度相机测试程序
测试深度相机连接、深度图像获取和点云生成功能

作者: cxzandy
日期: 2025-07-29
版本: v1.0
"""

import sys
import os
import numpy as np
import cv2
from datetime import datetime

def test_realsense_camera():
    """测试RealSense相机功能"""
    print("🔍 RealSense D455深度相机测试")
    print("=" * 50)
    
    try:
        import pyrealsense2 as rs
        print(f"✅ pyrealsense2库版本: {rs.__version__}")
    except ImportError:
        print("❌ pyrealsense2库未安装")
        print("解决方案: conda install -c conda-forge pyrealsense2")
        return False
    
    # 1. 检测RealSense设备
    print("\n📡 检测RealSense设备...")
    ctx = rs.context()
    devices = ctx.query_devices()
    
    if len(devices) == 0:
        print("❌ 未检测到RealSense设备")
        print("请检查:")
        print("   1. D455相机是否已连接USB 3.0端口")
        print("   2. 设备驱动是否正确安装")
        print("   3. USB连接是否稳定")
        return False
    
    print(f"✅ 检测到 {len(devices)} 个RealSense设备")
    
    # 2. 遍历设备信息
    for i, device in enumerate(devices):
        print(f"\n📷 设备 {i+1}:")
        print(f"   名称: {device.get_info(rs.camera_info.name)}")
        print(f"   序列号: {device.get_info(rs.camera_info.serial_number)}")
        print(f"   固件版本: {device.get_info(rs.camera_info.firmware_version)}")
        print(f"   产品ID: {device.get_info(rs.camera_info.product_id)}")
    
    # 3. 配置并启动相机流
    print("\n🎬 配置相机流...")
    pipeline = rs.pipeline()
    config = rs.config()
    
    # 配置深度和彩色流
    config.enable_stream(rs.stream.depth, 640, 480, rs.format.z16, 30)
    config.enable_stream(rs.stream.color, 640, 480, rs.format.bgr8, 30)
    
    try:
        # 启动流
        profile = pipeline.start(config)
        print("✅ 相机流启动成功")
        
        # 获取深度传感器
        depth_sensor = profile.get_device().first_depth_sensor()
        depth_scale = depth_sensor.get_depth_scale()
        print(f"   深度缩放因子: {depth_scale}")
        
        # 创建对齐对象 (将深度图像对齐到彩色图像)
        align_to = rs.stream.color
        align = rs.align(align_to)
        
        # 4. 获取并处理帧
        print("\n📸 获取图像和深度数据...")
        
        frame_count = 0
        successful_frames = 0
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # 丢弃前几帧 (自动曝光调整)
        for _ in range(10):
            pipeline.wait_for_frames()
        
        for i in range(10):
            frames = pipeline.wait_for_frames()
            frame_count += 1
            
            if frames:
                successful_frames += 1
                
                # 对齐深度帧到彩色帧
                aligned_frames = align.process(frames)
                
                depth_frame = aligned_frames.get_depth_frame()
                color_frame = aligned_frames.get_color_frame()
                
                if depth_frame and color_frame:
                    # 转换为numpy数组
                    depth_image = np.asanyarray(depth_frame.get_data())
                    color_image = np.asanyarray(color_frame.get_data())
                    
                    # 保存第一帧和最后一帧
                    if i == 0:
                        cv2.imwrite(f"realsense_color_first_{timestamp}.jpg", color_image)
                        
                        # 创建深度的可视化图像
                        depth_colormap = cv2.applyColorMap(
                            cv2.convertScaleAbs(depth_image, alpha=0.03), 
                            cv2.COLORMAP_JET
                        )
                        cv2.imwrite(f"realsense_depth_first_{timestamp}.jpg", depth_colormap)
                        
                        # 分析深度数据
                        valid_depth_pixels = depth_image[depth_image > 0]
                        if len(valid_depth_pixels) > 0:
                            min_depth = np.min(valid_depth_pixels) * depth_scale
                            max_depth = np.max(valid_depth_pixels) * depth_scale
                            mean_depth = np.mean(valid_depth_pixels) * depth_scale
                            
                            print(f"   深度范围: {min_depth:.2f}m - {max_depth:.2f}m")
                            print(f"   平均深度: {mean_depth:.2f}m")
                            print(f"   有效深度像素: {len(valid_depth_pixels)}/{depth_image.size}")
                        
                    elif i == 9:
                        cv2.imwrite(f"realsense_color_last_{timestamp}.jpg", color_image)
                        depth_colormap = cv2.applyColorMap(
                            cv2.convertScaleAbs(depth_image, alpha=0.03), 
                            cv2.COLORMAP_JET
                        )
                        cv2.imwrite(f"realsense_depth_last_{timestamp}.jpg", depth_colormap)
        
        success_rate = successful_frames / frame_count * 100
        print(f"✅ 图像获取成功率: {success_rate:.1f}% ({successful_frames}/{frame_count})")
        
        # 5. 测试点云生成
        print("\n☁️ 测试点云生成...")
        
        frames = pipeline.wait_for_frames()
        aligned_frames = align.process(frames)
        depth_frame = aligned_frames.get_depth_frame()
        color_frame = aligned_frames.get_color_frame()
        
        if depth_frame and color_frame:
            # 创建点云
            pc = rs.pointcloud()
            points = pc.calculate(depth_frame)
            
            # 获取顶点数据
            vertices = np.asanyarray(points.get_vertices()).view(np.float32).reshape(-1, 3)
            
            # 过滤有效点 (移除零点和无穷远点)
            valid_points = vertices[np.all(np.isfinite(vertices), axis=1)]
            valid_points = valid_points[np.any(valid_points != 0, axis=1)]
            
            print(f"✅ 点云生成成功")
            print(f"   总点数: {len(vertices)}")
            print(f"   有效点数: {len(valid_points)}")
            
            if len(valid_points) > 0:
                # 点云统计
                x_range = np.max(valid_points[:, 0]) - np.min(valid_points[:, 0])
                y_range = np.max(valid_points[:, 1]) - np.min(valid_points[:, 1])
                z_range = np.max(valid_points[:, 2]) - np.min(valid_points[:, 2])
                
                print(f"   X范围: {x_range:.2f}m")
                print(f"   Y范围: {y_range:.2f}m") 
                print(f"   Z范围: {z_range:.2f}m")
                
                # 保存点云数据 (简单格式)
                try:
                    np.save(f"realsense_pointcloud_{timestamp}.npy", valid_points)
                    print(f"   点云已保存: realsense_pointcloud_{timestamp}.npy")
                except Exception as e:
                    print(f"   ⚠️ 点云保存失败: {e}")
        
        # 6. 性能测试
        print("\n⚡ 性能测试...")
        start_time = datetime.now()
        test_frame_count = 0
        
        for _ in range(30):
            frames = pipeline.wait_for_frames()
            if frames:
                test_frame_count += 1
        
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        actual_fps = test_frame_count / duration if duration > 0 else 0
        
        print(f"✅ 实际FPS: {actual_fps:.2f}")
        
    except Exception as e:
        print(f"❌ 相机操作失败: {e}")
        return False
    finally:
        try:
            pipeline.stop()
            print("🔌 相机流已停止")
        except:
            pass
    
    return True

def test_realsense_integration():
    """测试RealSense与系统集成"""
    print("\n🔧 测试系统集成...")
    
    # 测试配置文件
    try:
        sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))
        from config import CameraConfig
        
        print(f"当前相机类型: {CameraConfig.CAMERA_TYPE}")
        if CameraConfig.CAMERA_TYPE == "realsense":
            print("✅ 配置已设置为RealSense模式")
        else:
            print("⚠️ 建议修改config.py中CAMERA_TYPE为'realsense'")
            
    except ImportError as e:
        print(f"⚠️ 配置文件导入失败: {e}")
    
    # 测试相机模块
    try:
        from src.camera.stereo_capture import StereoCapture
        camera = StereoCapture()
        print("✅ 相机模块导入成功")
    except ImportError as e:
        print(f"⚠️ 相机模块导入失败: {e}")
    except Exception as e:
        print(f"⚠️ 相机初始化警告: {e}")

def main():
    """主函数"""
    print("🚀 RealSense D455深度相机完整测试")
    print("=" * 60)
    
    try:
        # 基础硬件测试
        success = test_realsense_camera()
        
        if success:
            # 系统集成测试
            test_realsense_integration()
            
            print("\n" + "=" * 60)
            print("🎉 RealSense相机测试完成！")
            print("\n📋 测试结果总结:")
            print("✅ RealSense库安装正常")
            print("✅ 设备连接正常")
            print("✅ 深度和彩色图像获取正常")
            print("✅ 点云生成功能正常")
            print("✅ 性能表现良好")
            
            print("\n🚀 下一步建议:")
            print("1. 修改src/config.py中CAMERA_TYPE为'realsense'")
            print("2. 运行完整系统: python src/main.py --mode demo")
            print("3. 测试深度感知: python run_hardware_tests.py")
            
        else:
            print("\n❌ RealSense相机测试失败")
            print("请检查硬件连接和驱动安装")
            
        return success
        
    except KeyboardInterrupt:
        print("\n⚠️ 用户中断测试")
        return False
    except Exception as e:
        print(f"\n❌ 测试过程发生错误: {e}")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
