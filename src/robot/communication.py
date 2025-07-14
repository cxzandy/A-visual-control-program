import serial
import time

def recv_data(ser_obj, timeout_sec=5):
    """
    从串口接收数据的通用函数
    Args:
        ser_obj: 串口对象
        timeout_sec: 超时时间（秒）
    Returns:
        bytes: 接收到的原始数据
    """
    ser_obj.timeout = timeout_sec
    try:
        data = ser_obj.readline()
        if data:
            return data
    except serial.SerialException as e:
        print(f"串口读取错误: {e}")
    return b''

def send_data(send_data, ser_obj):
    """
    向串口发送数据，并附加换行符
    Args:
        send_data (str): 要发送的字符串数据
        ser_obj: 串口对象
    """
    if ser_obj.isOpen():
        formatted_data = send_data + '\n'
        try:
            ser_obj.write(formatted_data.encode('utf-8'))
            ser_obj.flushInput()
            ser_obj.flushOutput()
            print(f"发送成功: '{formatted_data.strip()}'")
        except serial.SerialException as e:
            print(f"串口写入错误: {e}")
            print("发送失败！可能串口连接已断开或设备无响应。")
    else:
        print("串口未打开，发送失败！")

def create_serial_connection(com_port='COM8', baud_rate=115200, timeout=0.5):
    """
    创建串口连接
    Args:
        com_port (str): 串口号
        baud_rate (int): 波特率
        timeout (float): 超时时间
    Returns:
        serial.Serial: 串口对象，如果连接失败返回None
    """
    try:
        ser = serial.Serial(com_port, baud_rate, timeout=timeout)
        if ser.isOpen():
            print(f"成功连接到 {com_port}！")
            return ser
        else:
            print(f"连接失败到 {com_port}！请检查串口是否被占用或COM端口设置。")
            return None
    except serial.SerialException as e:
        print(f"串口连接错误: {e}")
        print(f"请检查 COM 端口 '{com_port}' 是否正确，驱动是否安装，或串口是否被其他程序占用。")
        return None

class RoboMasterCSerial:
    def __init__(self, port='COM8', baudrate=115200, timeout=0.5):
        """
        初始化RoboMaster C板串口通信类
        Args:
            port (str): 串口号
            baudrate (int): 波特率  
            timeout (float): 超时时间
        """
        self.port = port
        self.baudrate = baudrate
        self.timeout = timeout
        self.ser = None
        self.connect()

    def connect(self):
        """建立串口连接"""
        self.ser = create_serial_connection(self.port, self.baudrate, self.timeout)
        if self.ser is None:
            raise Exception(f"无法连接到串口 {self.port}")

    def send(self, cmd: str):
        """
        发送指令到开发板C，自动添加换行符
        Args:
            cmd (str): 要发送的命令
        """
        if self.ser and self.ser.isOpen():
            send_data(cmd, self.ser)
        else:
            raise Exception('串口未打开')

    def recv(self, timeout_sec=5) -> str:
        """
        接收开发板C返回的数据
        Args:
            timeout_sec (int): 超时时间（秒）
        Returns:
            str: 解码后的接收数据
        """
        if self.ser and self.ser.isOpen():
            data = recv_data(self.ser, timeout_sec)
            try:
                return data.decode('utf-8').strip() if data else ''
            except UnicodeDecodeError:
                print(f"接收到无法解码的数据: {data}")
                return ''
        else:
            raise Exception('串口未打开')

    def close(self):
        """关闭串口连接"""
        if self.ser and self.ser.isOpen():
            self.ser.close()
            print("串口已关闭。")

    def __enter__(self):
        """支持with语句的上下文管理器"""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """退出时自动关闭串口"""
        self.close()


