#!/usr/bin/env python3
"""
快速Web API状态检查
"""

def check_web_server():
    """检查Web服务器状态"""
    try:
        import requests
        
        print("🔍 检查Web服务器状态...")
        
        # 检查主页
        response = requests.get("http://localhost:5000/", timeout=3)
        print(f"主页状态: {response.status_code}")
        
        # 检查API状态
        response = requests.get("http://localhost:5000/api/status", timeout=3)
        print(f"状态API: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"运行状态: {data.get('is_running', False)}")
        
        # 测试启动API (POST请求)
        response = requests.post("http://localhost:5000/api/start", 
                               json={"mode": "demo"}, 
                               timeout=3)
        print(f"启动API: {response.status_code}")
        
        if response.status_code == 200:
            print("✅ 所有API端点正常")
        else:
            print(f"❌ 启动API返回: {response.text}")
            
    except ImportError:
        print("❌ 需要安装requests库: pip install requests")
    except requests.exceptions.ConnectionError:
        print("❌ Web服务器未运行，请先启动:")
        print("   ./run_turn_control.sh")
        print("   选择 4 (仅Web控制界面)")
    except Exception as e:
        print(f"❌ 检查失败: {e}")

if __name__ == "__main__":
    check_web_server()
