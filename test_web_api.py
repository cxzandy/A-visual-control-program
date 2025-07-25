#!/usr/bin/env python3
"""
Web API测试脚本
测试所有Web界面的API端点
"""

import requests
import json
import time

def test_web_api(base_url="http://localhost:5000"):
    """测试Web API端点"""
    print("🌐 测试Web API端点")
    print("=" * 40)
    
    # 测试状态API
    print("1. 测试状态API...")
    try:
        response = requests.get(f"{base_url}/api/status")
        if response.status_code == 200:
            print("✅ /api/status - 正常")
            data = response.json()
            print(f"   运行状态: {data.get('is_running', False)}")
            print(f"   当前模式: {data.get('current_mode', 'None')}")
        else:
            print(f"❌ /api/status - 错误 {response.status_code}")
    except Exception as e:
        print(f"❌ /api/status - 异常: {e}")
    
    # 测试控制模式API
    print("\n2. 测试控制模式API...")
    try:
        # 切换到手动模式
        response = requests.post(f"{base_url}/api/control_mode", 
                               json={"mode": "manual"})
        if response.status_code == 200:
            print("✅ /api/control_mode (manual) - 正常")
            data = response.json()
            print(f"   响应: {data.get('message', '')}")
        else:
            print(f"❌ /api/control_mode - 错误 {response.status_code}")
            
        # 切换回自动模式
        response = requests.post(f"{base_url}/api/control_mode", 
                               json={"mode": "auto"})
        if response.status_code == 200:
            print("✅ /api/control_mode (auto) - 正常")
        else:
            print(f"❌ /api/control_mode (auto) - 错误 {response.status_code}")
    except Exception as e:
        print(f"❌ /api/control_mode - 异常: {e}")
    
    # 测试手动控制API
    print("\n3. 测试手动控制API...")
    try:
        # 先切换到手动模式
        requests.post(f"{base_url}/api/control_mode", json={"mode": "manual"})
        
        commands = ["forward", "left", "right", "stop"]
        for cmd in commands:
            response = requests.post(f"{base_url}/api/manual_command", 
                                   json={"command": cmd})
            if response.status_code == 200:
                print(f"✅ /api/manual_command ({cmd}) - 正常")
                data = response.json()
                robot_cmd = data.get('robot_command', 'N/A')
                print(f"   机器人命令: {robot_cmd}")
            else:
                print(f"❌ /api/manual_command ({cmd}) - 错误 {response.status_code}")
                
    except Exception as e:
        print(f"❌ /api/manual_command - 异常: {e}")
    
    # 测试启动API
    print("\n4. 测试启动API...")
    try:
        response = requests.post(f"{base_url}/api/start", 
                               json={"mode": "demo"})
        if response.status_code == 200:
            data = response.json()
            if data.get('success'):
                print("✅ /api/start - 正常")
                print(f"   消息: {data.get('message', '')}")
                
                # 等待一下然后停止
                time.sleep(2)
                
                # 测试停止API
                print("\n5. 测试停止API...")
                response = requests.post(f"{base_url}/api/stop")
                if response.status_code == 200:
                    data = response.json()
                    print("✅ /api/stop - 正常")
                    print(f"   消息: {data.get('message', '')}")
                else:
                    print(f"❌ /api/stop - 错误 {response.status_code}")
            else:
                print(f"⚠️ /api/start - 启动失败: {data.get('message', '')}")
        else:
            print(f"❌ /api/start - 错误 {response.status_code}")
            print(f"   响应: {response.text}")
    except Exception as e:
        print(f"❌ /api/start - 异常: {e}")
    
    # 测试图像API
    print("\n6. 测试图像API...")
    try:
        response = requests.get(f"{base_url}/api/image")
        if response.status_code == 200:
            print("✅ /api/image - 正常")
            print(f"   内容类型: {response.headers.get('Content-Type', 'unknown')}")
        else:
            print(f"❌ /api/image - 错误 {response.status_code}")
    except Exception as e:
        print(f"❌ /api/image - 异常: {e}")

def test_web_interface():
    """测试Web界面是否可访问"""
    print("🖥️ 测试Web界面")
    print("=" * 40)
    
    try:
        response = requests.get("http://localhost:5000/")
        if response.status_code == 200:
            print("✅ 主页面 - 正常")
            print(f"   页面大小: {len(response.content)} bytes")
        else:
            print(f"❌ 主页面 - 错误 {response.status_code}")
    except Exception as e:
        print(f"❌ 主页面 - 异常: {e}")

def main():
    """主函数"""
    print("🔧 Tiaozhanbei2.0 Web API 测试程序")
    print("请确保Web服务器正在运行 (http://localhost:5000)")
    print()
    
    # 检查服务器是否运行
    try:
        response = requests.get("http://localhost:5000/", timeout=5)
        if response.status_code != 200:
            print("❌ Web服务器未运行或无法访问")
            return
    except Exception as e:
        print("❌ Web服务器未运行或无法访问")
        print(f"错误: {e}")
        return
    
    # 运行测试
    test_web_interface()
    print()
    test_web_api()
    
    print("\n📊 测试完成")
    print("如果有错误，请检查Web服务器日志")

if __name__ == "__main__":
    main()
