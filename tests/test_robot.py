import sys
import os
import time
from time import sleep

# 添加项目根目录到路径
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from src.robot.communication import RoboMasterCSerial, recv_data, send_data, create_serial_connection

def test_robot_communication():
    """测试机器人通信功能"""
    com_port = 'COM8'
    baud_rate = 115200
    
    # 方法1: 使用类方式
    print("=== 测试方法1: 使用RoboMasterCSerial类 ===")
    try:
        with RoboMasterCSerial(com_port, baud_rate) as robot:
            # 读取初始信息
            print("\n--- 等待设备初始化信息 ---")
            initial_data = robot.recv(timeout_sec=2)
            if initial_data:
                print("设备初始信息:\n" + initial_data)
            
            # 发送测试命令
            robot.send("1")  # LED测试
            sleep(2)
            response = robot.recv()
            if response:
                print("设备响应:\n" + response)
                
    except Exception as e:
        print(f"类方式测试失败: {e}")
    
    print("\n" + "="*50)
    
    # 方法2: 使用函数方式
    print("=== 测试方法2: 使用独立函数 ===")
    ser = create_serial_connection(com_port, baud_rate)
    if ser:
        try:
            # 读取初始信息
            print("\n--- 等待设备初始化信息 ---")
            initial_data_bytes = recv_data(ser, timeout_sec=2)
            if initial_data_bytes:
                try:
                    initial_decoded_data = initial_data_bytes.decode('utf-8').strip()
                    print("设备初始信息:\n" + initial_decoded_data)
                except UnicodeDecodeError:
                    print(f"接收到无法解码的初始数据: {initial_data_bytes}")
            
            # 发送测试命令
            send_data("1", ser)  # LED测试
            sleep(2)
            received_data_bytes = recv_data(ser)
            if received_data_bytes:
                try:
                    decoded_data = received_data_bytes.decode('utf-8').strip()
                    print("设备响应:\n" + decoded_data)
                except UnicodeDecodeError:
                    print(f"接收到无法解码的数据: {received_data_bytes}")
                    
        finally:
            if ser and ser.isOpen():
                ser.close()
                print("\n串口已关闭。")
    
    print("机器人通信测试完成！")

def interactive_robot_test():
    """交互式机器人测试"""
    com_port = 'COM8'
    baud_rate = 115200
    
    try:
        with RoboMasterCSerial(com_port, baud_rate) as robot:
            # 读取初始信息
            print("\n--- 等待设备初始化信息 ---")
            initial_data = robot.recv(timeout_sec=2)
            if initial_data:
                print("设备初始信息:\n" + initial_data)
            else:
                print("未接收到设备初始信息。")
            print("--------------------------")

            # 主循环，用于用户交互和数据收发
            while True:
                user_input = input("\n输入要发送的数据 (如 '1' 进行LED TEST, 或 'exit' 退出): ")
                
                if user_input.lower() == 'exit':
                    print("用户请求退出。")
                    break

                robot.send(user_input)
                sleep(3)  # 给设备一点时间处理和响应

                print("--- 等待接收设备响应 ---")
                response = robot.recv(timeout_sec=5)
                if response:
                    print("接收数据:\n" + response)
                else:
                    print("未接收到设备响应数据或接收超时。")

    except Exception as e:
        print(f"交互式测试失败: {e}")

if __name__ == '__main__':
    print("选择测试模式：")
    print("1. 自动测试")
    print("2. 交互式测试")
    
    choice = input("请输入选择 (1/2): ").strip()
    
    if choice == "1":
        test_robot_communication()
    elif choice == "2":
        interactive_robot_test()
    else:
        print("无效选择，运行自动测试...")
        test_robot_communication()