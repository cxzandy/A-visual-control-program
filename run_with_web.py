#!/usr/bin/env python3
"""
Tiaozhanbei2.0 带Web界面的启动脚本
集成转向控制功能
"""

import sys
import os
import threading
import time
import signal
from flask import Flask

# 添加src目录到Python路径
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(project_root, 'src'))
sys.path.insert(0, os.path.join(project_root, 'web'))

# 导入主系统
from main import Tiaozhanbei2System
from web_simple import app, system_state

# 全局系统实例
main_system = None
web_thread = None
system_thread = None

def setup_system():
    """初始化主系统"""
    global main_system
    try:
        main_system = Tiaozhanbei2System()
        
        # 初始化硬件和算法组件
        if not main_system.initialize_hardware():
            print("❌ 硬件初始化失败")
            return False
            
        if not main_system.initialize_algorithms():
            print("❌ 算法组件初始化失败")
            return False
            
        print("✅ 系统初始化完成")
        return True
        
    except Exception as e:
        print(f"❌ 系统初始化失败: {e}")
        return False

def update_web_state():
    """定期更新Web状态"""
    global main_system
    while main_system and hasattr(main_system, 'running'):
        try:
            if main_system.turn_controller:
                # 更新系统状态
                state = main_system.get_system_state()
                system_state.system_stats.update({
                    'camera_status': '已连接' if state.get('camera_connected') else '未连接',
                    'robot_status': '已连接' if state.get('robot_connected') else '未连接',
                    'processing_fps': state.get('processing_fps', 0.0),
                    'frame_count': state.get('total_frames', 0)
                })
                
                # 更新转向控制状态
                system_state.turn_stats.update({
                    'direction': state.get('turn_direction', '直行'),
                    'confidence': state.get('turn_confidence', 0.0),
                    'mode': state.get('control_mode', 'auto'),
                    'stats': state.get('turn_statistics', {})
                })
                
                system_state.control_mode = state.get('control_mode', 'auto')
                
        except Exception as e:
            print(f"更新Web状态失败: {e}")
            
        time.sleep(0.5)  # 每0.5秒更新一次

def run_web_server():
    """运行Web服务器"""
    print("🌐 启动Web服务器...")
    app.run(host='0.0.0.0', port=5000, debug=False, threaded=True)

def run_tracking_system():
    """运行追踪系统"""
    global main_system
    if main_system:
        print("🎯 启动转向控制追踪系统...")
        system_state.is_running = True
        system_state.current_mode = "turn_tracking"
        
        success = main_system.run_tracking_mode()
        
        system_state.is_running = False
        system_state.current_mode = None
        
        if not success:
            print("❌ 追踪系统运行失败")

def signal_handler(signum, frame):
    """信号处理器"""
    print(f"\n🛑 接收到信号 {signum}，正在安全退出...")
    
    global main_system
    if main_system:
        main_system.emergency_stop = True
        main_system.running = False
    
    system_state.is_running = False
    
    print("✅ 系统已安全退出")
    sys.exit(0)

def main():
    """主函数"""
    print("🚀 Tiaozhanbei2.0 转向控制系统")
    print("=" * 50)
    
    # 注册信号处理器
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # 初始化系统
    if not setup_system():
        print("❌ 系统初始化失败，退出")
        return
    
    # 注入系统实例到Web应用
    app.main_system = main_system
    
    # 启动状态更新线程
    state_thread = threading.Thread(target=update_web_state, daemon=True)
    state_thread.start()
    
    # 启动Web服务器线程
    global web_thread
    web_thread = threading.Thread(target=run_web_server, daemon=True)
    web_thread.start()
    
    # 等待一下确保Web服务器启动
    time.sleep(2)
    
    print("📱 Web控制界面: http://localhost:5000")
    print("🎮 控制说明:")
    print("   - 按 'q' 退出")
    print("   - 按 'm' 切换自动/手动模式")
    print("   - Web界面可进行远程控制")
    print("⏹️  按Ctrl+C停止所有服务")
    
    # 运行主追踪系统
    try:
        run_tracking_system()
    except KeyboardInterrupt:
        signal_handler(signal.SIGINT, None)
    except Exception as e:
        print(f"❌ 系统运行错误: {e}")
        signal_handler(signal.SIGTERM, None)

if __name__ == "__main__":
    main()
