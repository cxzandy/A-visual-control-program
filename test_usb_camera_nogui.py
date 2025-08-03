#!/usr/bin/env python3
"""
无GUI的USB相机功能测试
专门为服务器环境设计，不需要图形界面

功能：
- 测试USB相机连接和图像获取
- 图像处理功能验证  
- 保存测试结果
- 生成完整报告

作者: cxzandy
日期: 2025-07-29
"""

import sys
import os
import cv2
import numpy as np
from datetime import datetime

def test_usb_camera_complete():
    """完整的USB相机功能测试 (无GUI)"""
    print("🔧 USB相机功能验证测试")
    print("=" * 50)
    
    available_cameras = []
    
    # 1. 检测可用相机
    print("\n📷 检测可用USB相机...")
    for i in range(6):
        cap = cv2.VideoCapture(i)
        if cap.isOpened():
            cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
            cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
            
            ret, frame = cap.read()
            if ret and frame is not None:
                h, w = frame.shape[:2]
                fps = cap.get(cv2.CAP_PROP_FPS)
                
                available_cameras.append({
                    'index': i,
                    'resolution': (w, h),
                    'fps': fps
                })
                
                print(f"✅ 相机 {i}: {w}x{h} @ {fps} FPS")
            cap.release()
    
    if not available_cameras:
        print("❌ 未找到可用的USB相机")
        return False
    
    # 2. 选择主相机进行测试
    primary_cam = available_cameras[0]['index']
    print(f"\n🎯 使用相机 {primary_cam} 进行功能测试...")
    
    # 3. 图像获取和处理测试
    cap = cv2.VideoCapture(primary_cam)
    if not cap.isOpened():
        print(f"❌ 无法打开相机 {primary_cam}")
        return False
    
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    test_results = {}
    
    try:
        # 获取多帧测试
        frames_tested = 0
        successful_frames = 0
        
        print("📸 测试连续图像获取...")
        for i in range(10):
            ret, frame = cap.read()
            frames_tested += 1
            
            if ret and frame is not None:
                successful_frames += 1
                
                # 保存第一帧和最后一帧
                if i == 0:
                    cv2.imwrite(f"usb_test_frame_first_{timestamp}.jpg", frame)
                elif i == 9:
                    cv2.imwrite(f"usb_test_frame_last_{timestamp}.jpg", frame)
        
        success_rate = successful_frames / frames_tested * 100
        print(f"✅ 图像获取成功率: {success_rate:.1f}% ({successful_frames}/{frames_tested})")
        test_results['frame_acquisition'] = {
            'success_rate': success_rate,
            'frames_tested': frames_tested,
            'successful_frames': successful_frames
        }
        
        # 图像处理功能测试
        if successful_frames > 0:
            print("🖼️ 测试图像处理功能...")
            
            ret, test_frame = cap.read()
            if ret and test_frame is not None:
                # 各种图像处理测试
                processing_tests = {
                    'grayscale': lambda img: cv2.cvtColor(img, cv2.COLOR_BGR2GRAY),
                    'gaussian_blur': lambda img: cv2.GaussianBlur(img, (15, 15), 0),
                    'edge_detection': lambda img: cv2.Canny(cv2.cvtColor(img, cv2.COLOR_BGR2GRAY), 50, 150),
                    'resize': lambda img: cv2.resize(img, (320, 240)),
                    'histogram_equalization': lambda img: cv2.equalizeHist(cv2.cvtColor(img, cv2.COLOR_BGR2GRAY))
                }
                
                processing_results = {}
                for test_name, process_func in processing_tests.items():
                    try:
                        result = process_func(test_frame)
                        if result is not None:
                            # 保存处理结果
                            cv2.imwrite(f"usb_test_{test_name}_{timestamp}.jpg", result)
                            processing_results[test_name] = {
                                'success': True,
                                'shape': result.shape,
                                'dtype': str(result.dtype)
                            }
                            print(f"   ✅ {test_name}: {result.shape}")
                        else:
                            processing_results[test_name] = {'success': False, 'error': 'None result'}
                    except Exception as e:
                        processing_results[test_name] = {'success': False, 'error': str(e)}
                        print(f"   ❌ {test_name}: {e}")
                
                test_results['image_processing'] = processing_results
        
        # 4. 性能测试
        print("⚡ 测试图像获取性能...")
        start_time = datetime.now()
        frame_count = 0
        
        # 测试30帧的获取速度
        for i in range(30):
            ret, frame = cap.read()
            if ret and frame is not None:
                frame_count += 1
        
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        actual_fps = frame_count / duration if duration > 0 else 0
        
        print(f"✅ 实际FPS: {actual_fps:.2f} (理论: {available_cameras[0]['fps']})")
        test_results['performance'] = {
            'actual_fps': actual_fps,
            'theoretical_fps': available_cameras[0]['fps'],
            'test_duration': duration,
            'frames_captured': frame_count
        }
        
    except Exception as e:
        print(f"❌ 测试过程中出现错误: {e}")
        return False
    finally:
        cap.release()
    
    # 5. 生成详细报告
    print("\n" + "="*50)
    print("📊 USB相机功能测试报告")
    print("="*50)
    print(f"测试时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"可用相机数量: {len(available_cameras)}")
    
    for cam in available_cameras:
        print(f"   📷 相机 {cam['index']}: {cam['resolution']} @ {cam['fps']} FPS")
    
    print(f"\n主测试相机: {primary_cam}")
    print(f"图像获取成功率: {test_results.get('frame_acquisition', {}).get('success_rate', 0):.1f}%")
    print(f"实际FPS: {test_results.get('performance', {}).get('actual_fps', 0):.2f}")
    
    # 图像处理功能总结
    if 'image_processing' in test_results:
        processing_success = sum(1 for result in test_results['image_processing'].values() if result.get('success', False))
        processing_total = len(test_results['image_processing'])
        print(f"图像处理功能: {processing_success}/{processing_total} 通过")
    
    # 保存测试报告
    try:
        import json
        report_file = f"usb_camera_test_report_{timestamp}.json"
        with open(report_file, 'w') as f:
            json.dump({
                'timestamp': timestamp,
                'available_cameras': available_cameras,
                'primary_camera': primary_cam,
                'test_results': test_results
            }, f, indent=2, default=str)
        print(f"\n💾 详细报告已保存: {report_file}")
    except Exception as e:
        print(f"⚠️ 报告保存失败: {e}")
    
    # 6. 系统配置建议
    print("\n🔧 系统配置建议:")
    print("   在 src/config.py 中确认:")
    print(f"   CAMERA_TYPE = 'usb'")
    print(f"   USB_CAMERA_INDEX = {primary_cam}")
    
    print("\n🚀 下一步测试:")
    print("   1. 使用USB相机运行演示: python src/main.py --mode demo")
    print("   2. 测试障碍物检测: python test_obstacle_avoidance.py") 
    print("   3. 启动Web界面: python web/web_simple.py")
    print("   4. 运行完整硬件测试: python run_hardware_tests.py")
    
    return True

def main():
    """主函数"""
    try:
        success = test_usb_camera_complete()
        if success:
            print("\n🎉 USB相机功能测试全部通过！")
            print("相机已准备好用于挑战杯2.0系统！")
        return success
    except KeyboardInterrupt:
        print("\n⚠️ 用户中断测试")
        return False
    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
