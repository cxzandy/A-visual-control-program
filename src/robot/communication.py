import serial

class RoboMasterCSerial:
    def __init__(self, port='COM8', baudrate=115200, timeout=0.5):
        self.ser = serial.Serial(port, baudrate, timeout=timeout)

    def send(self, cmd: str):
        """
        发送指令到开发板C，自动添加换行符
        """
        if self.ser.isOpen():
            self.ser.write((cmd + '\n').encode('utf-8'))
        else:
            raise Exception('串口未打开')

    def recv(self) -> str:
        """
        接收开发板C返回的数据
        """
        if self.ser.isOpen():
            data = self.ser.readline()
            return data.decode('utf-8').strip() if data else ''
        else:
            raise Exception('串口未打开')

    def close(self):
        if self.ser.isOpen():
            self.ser.close()


