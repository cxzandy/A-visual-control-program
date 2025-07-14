import serial
import time
from time import sleep

def recv(ser_obj, timeout_sec=5):
    ser_obj.timeout = timeout_sec # 设置串口对象的读取超时
    try:
        # 尝试读取一行，直到遇到换行符或超时
        data = ser_obj.readline()
        if data:
            return data
    except serial.SerialException as e:
        print(f"串口读取错误: {e}")
    return b''

def send(send_data, ser_obj):
    """
    向串口发送数据，并附加换行符，以便设备识别命令结束。
    :param send_data: 要发送的字符串数据
    :param ser_obj: 串口对象
    """
    if ser_obj.isOpen():
        # 通常，嵌入式设备期望命令以换行符结束。
        # 尝试使用 '\n' (LF) 或 '\r\n' (CRLF)。
        # 如果设备没有响应，可以尝试将 '\n' 改为 '\r\n'。
        formatted_data = send_data + '\n' # 添加换行符
        try:
            ser_obj.write(formatted_data.encode('utf-8')) # 编码并发送
            ser_obj.flushInput()  # 清空输入缓冲区
            ser_obj.flushOutput() # 清空输出缓冲区 (通常在发送前清空输出缓冲区以避免延迟)
            print(f"发送成功: '{formatted_data.strip()}'") # 打印发送内容，去除换行符
        except serial.SerialException as e:
            print(f"串口写入错误: {e}")
            print("发送失败！可能串口连接已断开或设备无响应。")
    else:
        print("串口未打开，发送失败！")

if __name__ == '__main__':
    ser = None # 初始化串口对象为None
    com_port = 'COM8' # 定义串口号，方便修改
    baud_rate = 115200 # 定义波特率

    try:
        # 尝试打开串口
        ser = serial.Serial(com_port, baud_rate, timeout=0.5)
        if ser.isOpen():
            print(f"成功连接到 {com_port}！")
            
            # 在程序开始时，读取可能存在的初始菜单信息
            print("\n--- 等待设备初始化信息 ---")
            initial_data_bytes = recv(ser)
            if initial_data_bytes:
                try:
                    initial_decoded_data = initial_data_bytes.decode('utf-8').strip()
                    print("设备初始信息:\n" + initial_decoded_data)
                except UnicodeDecodeError:
                    print(f"接收到无法解码的初始数据: {initial_data_bytes}")
            else:
                print("未接收到设备初始信息。")
            print("--------------------------")

            # 主循环，用于用户交互和数据收发
            while True:
                user_input = input("\n输入要发送的数据 (如 '1' 进行LED TEST, 或 'exit' 退出): ")
                
                if user_input.lower() == 'exit':
                    print("用户请求退出。")
                    break # 退出循环

                send(user_input, ser) # 发送用户输入的数据

                sleep(3) # 给设备一点时间处理和响应

                print("--- 等待接收设备响应 ---")
                received_data_bytes = recv(ser) # 接收数据

                if received_data_bytes:
                    try:
                        decoded_data = received_data_bytes.decode('utf-8').strip() # 解码并去除首尾空白符
                        print("接收数据:\n" + decoded_data)
                    except UnicodeDecodeError:
                        print(f"接收到无法解码的数据: {received_data_bytes}")
                        decoded_data = "" # 如果解码失败，清空以便后续逻辑处理
                else:
                    print("未接收到设备响应数据或接收超时。")
                    decoded_data = "" # 确保decoded_data始终有值

                # 如果设备返回了特定的'exit'信号，也可以中断
                # 这取决于你的设备是否会发送'exit'来指示断开
                # if decoded_data.lower() == 'exit':
                #     print("设备指示断开连接。")
                #     break

        else:
            print(f"连接失败到 {com_port}！请检查串口是否被占用或COM端口设置。")

    except serial.SerialException as e:
        # 捕获串口相关的异常，如串口不存在、权限不足等
        print(f"串口连接错误: {e}")
        print(f"请检查 COM 端口 '{com_port}' 是否正确，驱动是否安装，或串口是否被其他程序占用。")
    except Exception as e:
        # 捕获其他未知异常
        print(f"发生未知错误: {e}")
    finally:
        # 无论程序如何结束，都尝试关闭串口，释放资源
        if ser and ser.isOpen():
            ser.close()
            print("\n串口已关闭。")