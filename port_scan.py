import threadpool
import socket
 
ip = input("Enter the ip address you want to scan: ")
print("start port scan...")
 
def scanner(host, port):
    # 尝试连接指定端口，连接成功说明该端口开放
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.connect((host, port))
        print(str(port), "is open")
    except:
        pass
 
host_port = []
# 需要遍历的端口数
port_range = 65536
for port in range(port_range):
    host_port.append(([ip,port],None))
 
# 创建线程池,50指50个线程
pool = threadpool.ThreadPool(50)
# 指定线程池执行的任务
tasks = threadpool.makeRequests(scanner, host_port)	
# 将要执行的任务放入线程池中
[pool.putRequest(req) for req in tasks]	
# 等待所有子线程执行完毕后退出
pool.wait()	
 
print("Done!")