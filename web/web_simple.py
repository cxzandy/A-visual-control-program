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
        
        # 控制相关状态
        self.control_mode = 'auto'  # auto/manual
        self.turn_controller = None
        self.manual_command = None
        self.last_command_time = 0
        
        self.system_stats = {
            'camera_status': '未连接',
            'robot_status': '未连接',
            'processing_fps': 0.0,
            'frame_count': 0,
            'quadrants_detected': 0,
            'prediction_direction': '未知',
            'prediction_confidence': 0.0,
            'prediction_accuracy': 0.0,
            'prediction_count': 0
        }
        
        # 转向控制状态
        self.turn_stats = {
            'direction': '直行',
            'confidence': 0.0,
            'mode': 'auto',
            'stats': {
                'left_turns': 0,
                'right_turns': 0,
                'straight_segments': 0
            }
        }
        
    def update_stats(self, **kwargs):
        self.system_stats.update(kwargs)
        
    def update_turn_stats(self, **kwargs):
        self.turn_stats.update(kwargs)

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
        'turn_control': system_state.turn_stats,  # 添加转向控制状态
        'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    })

@app.route('/api/start', methods=['POST'])
def start_system_generic():
    """启动系统API (通用端点)"""
    global system_state
    
    if system_state.is_running:
        return jsonify({'success': False, 'message': '系统已在运行中'})
    
    try:
        data = request.get_json()
        mode = data.get('mode', 'demo') if data else 'demo'
        
        # 调用具体的启动函数
        return start_system(mode)
        
    except Exception as e:
        return jsonify({'success': False, 'message': f'启动失败: {str(e)}'})

@app.route('/api/start/<mode>', methods=['GET', 'POST'])
def start_system(mode):
    """启动系统API"""
    global system_state
    
    if system_state.is_running:
        return jsonify({'success': False, 'message': '系统已在运行中'})
    
    try:
        # 构建命令
        script_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        if mode == 'demo':
            cmd = ["conda", "run", "-n", "tiao", "python", "-m", "src.main", "--mode", "demo", "--display", "--save"]
        elif mode == 'track':
            cmd = ["conda", "run", "-n", "tiao", "python", "-m", "src.main", "--mode", "track", "--display", "--save"]
        elif mode == 'calib':
            cmd = ["conda", "run", "-n", "tiao", "python", "-m", "src.main", "--mode", "calib", "--display", "--save"]
        elif mode == 'test':
            cmd = ["conda", "run", "-n", "tiao", "python", "-m", "src.main", "--mode", "test", "--display", "--save"]
        else:
            return jsonify({'success': False, 'message': f'不支持的模式: {mode}'})
        
        # 启动后台进程
        system_state.current_process = subprocess.Popen(
            cmd, 
            cwd=script_dir,
            stdout=subprocess.PIPE, 
            stderr=subprocess.PIPE,
            text=True
        )
        
        system_state.is_running = True
        system_state.current_mode = mode
        
        # 启动状态监控线程
        def monitor_process():
            while system_state.is_running and system_state.current_process:
                try:
                    # 检查进程是否还在运行
                    if system_state.current_process.poll() is not None:
                        # 进程已结束
                        system_state.is_running = False
                        system_state.current_mode = None
                        system_state.update_stats(
                            camera_status='未连接',
                            robot_status='未连接',
                            processing_fps=0.0,
                            quadrants_detected=0
                        )
                        break
                        
                    time.sleep(1)
                except:
                    break
        
        monitor_thread = threading.Thread(target=monitor_process, daemon=True)
        monitor_thread.start()
        
        # 更新状态
        system_state.update_stats(
            camera_status='已连接',
            robot_status='已连接' if mode == 'track' else '演示模式',
            processing_fps=25.5,
            frame_count=0,
            quadrants_detected=4,
            prediction_direction='初始化中',
            prediction_confidence=0.0,
            prediction_accuracy=0.0,
            prediction_count=0
        )
        
        return jsonify({'success': True, 'message': f'{mode} 模式启动成功'})
        
    except Exception as e:
        return jsonify({'success': False, 'message': f'启动失败: {str(e)}'})

@app.route('/api/stop')
def stop_system():
    """停止系统API"""
    global system_state
    
    if not system_state.is_running:
        return jsonify({'success': False, 'message': '系统未在运行'})
    
    try:
        if system_state.current_process:
            system_state.current_process.terminate()
            system_state.current_process.wait(timeout=5)
        
        system_state.is_running = False
        system_state.current_mode = None
        system_state.current_process = None
        
        # 重置状态
        system_state.update_stats(
            camera_status='未连接',
            robot_status='未连接',
            processing_fps=0.0,
            frame_count=0,
            quadrants_detected=0,
            prediction_direction='未知',
            prediction_confidence=0.0,
            prediction_accuracy=0.0,
            prediction_count=0
        )
        
        return jsonify({'success': True, 'message': '系统已停止'})
        
    except Exception as e:
        return jsonify({'success': False, 'message': f'停止失败: {str(e)}'})

@app.route('/api/image')
def get_latest_image():
    """获取最新图像API"""
    if system_state.is_running:
        # 尝试从输出目录读取最新图像
        try:
            script_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            output_dir = os.path.join(script_dir, 'output', 'images')
            
            # 查找最新的图像文件
            if os.path.exists(output_dir):
                image_files = [f for f in os.listdir(output_dir) if f.endswith(('.jpg', '.png', '.jpeg'))]
                if image_files:
                    # 按修改时间排序，获取最新的
                    latest_file = max(image_files, key=lambda f: os.path.getmtime(os.path.join(output_dir, f)))
                    latest_path = os.path.join(output_dir, latest_file)
                    
                    # 读取图像并转换为base64
                    with open(latest_path, 'rb') as f:
                        img_data = f.read()
                        img_base64 = base64.b64encode(img_data).decode('utf-8')
                        
                        return jsonify({
                            'success': True,
                            'image': f'data:image/jpeg;base64,{img_base64}',
                            'timestamp': os.path.getmtime(latest_path)
                        })
            
            # 如果没有保存的图像文件，生成实时模拟图像
            import numpy as np
            import cv2
            
            # 创建一个更真实的状态显示图像
            img = np.zeros((480, 640, 3), dtype=np.uint8)
            img.fill(30)  # 深色背景
            
            # 绘制象限分割线
            cv2.line(img, (320, 0), (320, 480), (255, 255, 255), 1)
            cv2.line(img, (0, 240), (640, 240), (255, 255, 255), 1)
            
            # 添加系统信息
            cv2.putText(img, f"Mode: {system_state.current_mode or 'None'}", 
                       (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
            cv2.putText(img, f"FPS: {system_state.system_stats['processing_fps']}", 
                       (10, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
            cv2.putText(img, f"Quadrants: {system_state.system_stats['quadrants_detected']}/4", 
                       (10, 90), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
            
            # 添加方向预测信息
            prediction_dir = system_state.system_stats.get('prediction_direction', '未知')
            prediction_conf = system_state.system_stats.get('prediction_confidence', 0.0)
            cv2.putText(img, f"Prediction: {prediction_dir} ({prediction_conf:.2f})", 
                       (10, 120), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 0, 255), 2)
            
            if system_state.current_mode == 'track':
                # 绘制模拟的管道检测线
                colors = [(255, 0, 0), (0, 255, 0), (0, 0, 255), (255, 255, 0)]
                line_positions = [
                    [(450, 120), (600, 200)],  # Q1 右上
                    [(40, 120), (280, 200)],   # Q2 左上
                    [(40, 280), (280, 360)],   # Q3 左下
                    [(450, 280), (600, 360)]   # Q4 右下
                ]
                
                for i, (start, end) in enumerate(line_positions):
                    if i < system_state.system_stats['quadrants_detected']:
                        cv2.line(img, start, end, colors[i], 3)
                        cv2.circle(img, start, 5, colors[i], -1)
                        cv2.circle(img, end, 5, colors[i], -1)
                
                # 绘制中心轴线（如果检测到足够的象限）
                if system_state.system_stats['quadrants_detected'] >= 2:
                    cv2.line(img, (50, 160), (590, 320), (0, 255, 255), 2)
                    cv2.putText(img, "Pipe Axis Fitted", (10, 150), 
                               cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 255), 1)
                    
                    # 绘制方向预测箭头
                    if prediction_dir in ['left', 'right', 'up', 'down'] and prediction_conf > 0.5:
                        center_x, center_y = 320, 240
                        arrow_length = 60
                        
                        if prediction_dir == 'left':
                            end_x, end_y = center_x - arrow_length, center_y
                            color = (0, 255, 255)  # 黄色
                        elif prediction_dir == 'right':
                            end_x, end_y = center_x + arrow_length, center_y
                            color = (0, 255, 255)
                        elif prediction_dir == 'up':
                            end_x, end_y = center_x, center_y - arrow_length
                            color = (255, 0, 255)  # 紫色
                        elif prediction_dir == 'down':
                            end_x, end_y = center_x, center_y + arrow_length
                            color = (255, 0, 255)
                        
                        cv2.arrowedLine(img, (center_x, center_y), (end_x, end_y), 
                                       color, 4, tipLength=0.3)
            
            # 添加时间戳
            cv2.putText(img, f"Real-time: {datetime.now().strftime('%H:%M:%S')}", 
                       (10, 460), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (128, 128, 128), 1)
            
            # 转换为base64
            _, buffer = cv2.imencode('.jpg', img, [cv2.IMWRITE_JPEG_QUALITY, 85])
            img_base64 = base64.b64encode(buffer).decode('utf-8')
            
            return jsonify({
                'success': True,
                'image': f'data:image/jpeg;base64,{img_base64}',
                'timestamp': time.time()
            })
            
        except Exception as e:
            print(f"图像获取错误: {e}")
            pass
    
    # 返回空白状态图像
    try:
        import numpy as np
        import cv2
        img = np.zeros((480, 640, 3), dtype=np.uint8)
        img.fill(20)
        cv2.putText(img, "System Offline", (200, 240), 
                   cv2.FONT_HERSHEY_SIMPLEX, 1.0, (0, 0, 255), 2)
        
        _, buffer = cv2.imencode('.jpg', img)
        img_base64 = base64.b64encode(buffer).decode('utf-8')
        
        return jsonify({
            'success': True,
            'image': f'data:image/jpeg;base64,{img_base64}'
        })
    except:
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

@app.route('/api/control_mode', methods=['POST'])
def set_control_mode():
    """设置控制模式（自动/手动）"""
    try:
        data = request.get_json()
        mode = data.get('mode', 'auto')
        
        if mode not in ['auto', 'manual']:
            return jsonify({'status': 'error', 'message': '无效的控制模式'}), 400
        
        # 更新本地状态
        global system_state
        system_state.control_mode = mode
        
        # 如果有主系统实例，也更新主系统
        if hasattr(app, 'main_system') and app.main_system:
            app.main_system.set_control_mode(mode)
        
        print(f"💡 控制模式切换为: {mode}")
        
        return jsonify({
            'status': 'success',
            'message': f'控制模式已切换为{mode}',
            'mode': mode
        })
        
    except Exception as e:
        print(f"❌ 设置控制模式错误: {e}")
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/api/manual_command', methods=['POST'])
def manual_command():
    """手动控制命令"""
    try:
        data = request.get_json()
        command = data.get('command', '')
        
        if not command:
            return jsonify({'status': 'error', 'message': '缺少控制命令'}), 400
            
        global system_state
        
        # 只在手动模式下执行
        if system_state.control_mode != 'manual':
            return jsonify({'status': 'error', 'message': '当前不在手动模式'}), 400
        
        # 如果有主系统实例，发送命令到主系统
        if hasattr(app, 'main_system') and app.main_system:
            success = app.main_system.send_manual_command(command)
            if not success:
                return jsonify({'status': 'error', 'message': '命令发送失败'}), 500
        else:
            # 没有主系统时，直接记录命令（用于测试）
            print(f"📝 记录手动命令: {command}")
        
        # 设置手动命令和时间戳
        system_state.manual_command = command
        system_state.last_command_time = time.time()
        
        print(f"🎮 手动控制命令: {command}")
        
        # 返回包含机器人命令码的响应
        try:
            # 添加src目录到路径
            import sys
            import os
            project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            sys.path.insert(0, os.path.join(project_root, 'src'))
            
            from config import ControlConfig, RobotConfig
            robot_cmd = None
            if command in ControlConfig.MANUAL_COMMANDS:
                cmd_name = ControlConfig.MANUAL_COMMANDS[command]
                if cmd_name in RobotConfig.COMMANDS:
                    robot_cmd = RobotConfig.COMMANDS[cmd_name]
        except ImportError:
            robot_cmd = None
        
        return jsonify({
            'status': 'success',
            'message': f'执行手动命令: {command}',
            'command': command,
            'robot_command': robot_cmd
        })
        
    except Exception as e:
        print(f"❌ 手动控制错误: {e}")
        return jsonify({'status': 'error', 'message': str(e)}), 500

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
