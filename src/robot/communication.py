import serial 
import time 
from time import sleep 
def recv(serial): 
    while True: 
        start_time = time.time() 
        data = serial.read_all() 
        if data != b'': # 判断字节空数据 
            return data 
        if time.time() - start_time > 5: # 超时5秒 
            return b'' 
        sleep(0.02) 
def send(send_data): 
    if (serial.isOpen()): 
        serial.write(send_data.encode('utf-8')) # 编码 
        print("发送成功", send_data) 
    else: 
        print("发送失败！")

if __name__ == '__main__': 
    serial = serial.Serial('COM4', 115200, timeout=0.5) 
    if serial.isOpen() : 
        print("成功连接！") 
    else : print("连接失败！") 
    #这里如果不加上一个while True，程序执行一次就自动跳出了 
    while True: 
        a = input("输入要发送的数据：") 
        send(a) 
        sleep(0.5) # 起到一个延时的效果 
        data =recv(serial) 
        if data != b'' : 
            decoded_data = data.decode('utf-8') # 解码 
            print("接收数据:", decoded_data) 
        if decoded_data.strip() == 'exit' : # 去除首尾空白符后比较 print("已断开连接") 
                break