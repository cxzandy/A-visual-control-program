#!/usr/bin/env python3
"""
Tiaozhanbei2.0 简化Web控制界面
简单的Flask前端页面，用于控制和监控管道追踪系统
"""

from flask import Flask, render_template, request, jsonify
import subprocess
import threading
import time
import os
import sys
import json
from datetime import datetime
import base64

app = Flask(__name__)

# 全局状态管理
class SystemState:
    def __init__(self):
        self.is_running = False
        self.current_mode = None
        self.current_process = None
        self.system_stats = {
            'camera_status': '未连接',
            'robot_status': '未连接',
            'processing_fps': 0.0,
            'frame_count': 0,
            'quadrants_detected': 0
        }
        
    def update_stats(self, **kwargs):
        self.system_stats.update(kwargs)

# 创建全局状态实例
system_state = SystemState()

@app.route('/')
def index():
    """主页面"""
    return render_template('index.html')

@app.route('/api/status')
def get_status():
    """获取系统状态API"""
    return jsonify({
        'is_running': system_state.is_running,
        'current_mode': system_state.current_mode,
        'stats': system_state.system_stats,
        'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    })

@app.route('/api/start', methods=['POST'])
def start_system():
    """启动系统API"""
    data = request.get_json()
    mode = data.get('mode', 'demo')
    
    try:
        # 构建命令
        cmd = [
            'conda', 'run', '-n', 'tiao', 
            'python', '-m', 'src.main', 
            '--mode', mode, 
            '--display'
        ]
        
        # 启动子进程
        system_state.current_process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            cwd=os.path.dirname(os.path.abspath(__file__))
        )
        
        system_state.is_running = True
        system_state.current_mode = mode
        
        # 启动监控线程
        monitor_thread = threading.Thread(target=monitor_process)
        monitor_thread.daemon = True
        monitor_thread.start()
        
        # 模拟更新状态
        system_state.update_stats(
            camera_status='已连接',
            processing_fps=25.0,
            quadrants_detected=4
        )
        
        return jsonify({'success': True, 'message': f'系统已启动 - {mode}模式'})
        
    except Exception as e:
        return jsonify({'success': False, 'message': f'启动失败: {str(e)}'})

@app.route('/api/stop', methods=['POST'])
def stop_system():
    """停止系统API"""
    try:
        if system_state.current_process:
            system_state.current_process.terminate()
            system_state.current_process.wait(timeout=5)
            system_state.current_process = None
        
        system_state.is_running = False
        system_state.current_mode = None
        
        system_state.update_stats(
            camera_status='未连接',
            processing_fps=0.0,
            quadrants_detected=0,
            frame_count=0
        )
        
        return jsonify({'success': True, 'message': '系统已停止'})
        
    except Exception as e:
        return jsonify({'success': False, 'message': f'停止失败: {str(e)}'})

@app.route('/api/image')
def get_latest_image():
    """获取最新图像API"""
    # 简化版本：返回一个占位图像
    if system_state.is_running:
        # 生成简单的状态图
        import numpy as np
        try:
            import cv2
            # 创建一个简单的状态显示图像
            img = np.zeros((480, 640, 3), dtype=np.uint8)
            img.fill(50)  # 深灰色背景
            
            # 绘制象限分割线
            cv2.line(img, (320, 0), (320, 480), (255, 255, 255), 2)
            cv2.line(img, (0, 240), (640, 240), (255, 255, 255), 2)
            
            # 添加文本
            cv2.putText(img, f"Mode: {system_state.current_mode}", 
                       (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 2)
            cv2.putText(img, f"FPS: {system_state.system_stats['processing_fps']}", 
                       (10, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 2)
            cv2.putText(img, f"Quadrants: {system_state.system_stats['quadrants_detected']}/4", 
                       (10, 90), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 2)
            
            # 在各象限绘制模拟管道
            colors = [(255, 0, 0), (0, 255, 0), (0, 0, 255), (255, 255, 0)]
            for i in range(4):
                x_start = 160 if i % 2 == 0 else 480
                y_start = 120 if i < 2 else 360
                x_end = x_start + 160
                y_end = y_start + 120
                
                cv2.line(img, (x_start, y_start), (x_end, y_end), colors[i], 3)
                cv2.circle(img, (x_start, y_start), 5, colors[i], -1)
                cv2.circle(img, (x_end, y_end), 5, colors[i], -1)
            
            # 转换为base64
            _, buffer = cv2.imencode('.jpg', img)
            img_base64 = base64.b64encode(buffer).decode('utf-8')
            
            return jsonify({
                'success': True,
                'image': f'data:image/jpeg;base64,{img_base64}'
            })
        except ImportError:
            # 如果没有OpenCV，返回无图像
            pass
    
    return jsonify({'success': False, 'message': '无图像数据'})

@app.route('/api/config', methods=['GET', 'POST'])
def handle_config():
    """配置管理API"""
    if request.method == 'GET':
        # 返回默认配置
        config_data = {
            'camera_resolution': '640x480',
            'camera_fps': 30,
            'depth_threshold': 2.0,
            'serial_port': '/dev/ttyUSB0'
        }
        return jsonify({'success': True, 'config': config_data})
    
    else:  # POST
        # 更新配置
        return jsonify({'success': True, 'message': '配置已更新'})

def monitor_process():
    """监控子进程状态"""
    frame_count = 0
    while system_state.is_running and system_state.current_process:
        try:
            # 检查进程是否还在运行
            if system_state.current_process.poll() is not None:
                # 进程已结束
                system_state.is_running = False
                system_state.current_mode = None
                break
            
            # 模拟更新统计信息
            frame_count += 1
            system_state.update_stats(
                frame_count=frame_count,
                processing_fps=round(25.0 + (frame_count % 10) * 0.5, 1)
            )
            
            time.sleep(0.1)
            
        except Exception as e:
            print(f"监控进程错误: {e}")
            break

if __name__ == '__main__':
    # 设置项目根目录和模板目录
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    sys.path.insert(0, project_root)
    
    # 设置模板目录为当前web目录下的templates
    app.template_folder = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'templates')
    
    print("🚀 启动Tiaozhanbei2.0 Web控制界面...")
    print("📱 访问地址: http://localhost:5000")
    print("🌐 局域网访问: http://$(hostname -I | awk '{print $1}'):5000")
    print("⏹️  按Ctrl+C停止服务")
    
    app.run(host='0.0.0.0', port=5000, debug=False, threaded=True)
