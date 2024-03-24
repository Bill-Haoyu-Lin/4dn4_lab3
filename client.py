import socket
import os
import sys

# Configuration
SDP_PORT = 30000
FSP_PORT = 30001
BROADCAST_ADDRESS = '255.255.255.255'
LOCAL_DIRECTORY = './local_shared_files'

if not os.path.exists(LOCAL_DIRECTORY):
    os.makedirs(LOCAL_DIRECTORY)

def discover_services():
    udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    udp_socket.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
    udp_socket.sendto(b"SERVICE DISCOVERY", (BROADCAST_ADDRESS, SDP_PORT))
    udp_socket.settimeout(2.0)
    try:
        while True:
            data, addr = udp_socket.recvfrom(1024)
            print(f"Service found at IP address/port {addr[0]}:{addr[1]} - {data.decode(encoding='UTF-8',errors='strict')}")
    except socket.timeout:
        print("No service found.")

def connect_to_server(ip, port):
    tcp_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    tcp_socket.connect((ip, port))
    return tcp_socket

def list_files(tcp_socket):
    tcp_socket.sendall(b'\x03')  # Send list command
    data = tcp_socket.recv(1024).decode(encoding='UTF-8',errors='strict')
    print(data)

def upload_file(tcp_socket, filename):
    print(f"Uploading file {filename}.")
    tcp_socket.sendall(b'\x02' + filename.encode()+ b'\x00')
    file_path = os.path.join(LOCAL_DIRECTORY, filename)
    with open(file_path, 'rb') as f:
        data = f.read(1024)
        print(data)
        while data:
            tcp_socket.sendall(data)
            data = f.read(1024)

    tcp_socket.sendall(b"package_end")

    print("File Sent.")

def download_file(tcp_socket, filename):
    try:
        tcp_socket.sendall(b'\x01' + filename.encode(encoding='UTF-8') + b'\x00')
        file_path = os.path.join(LOCAL_DIRECTORY, filename)
        with open(file_path, 'wb') as f:
            while True:
                data = tcp_socket.recv(1024)
                if data == b"package_end":
                    break
                f.write(data)

        print(f"File {filename} downloaded.")

    except Exception as e:
        print(f"Error downloading file: {e}")
        # Remove the file if it was not received completely
        os.remove(file_path)
        

def main():
    while True:
        command = input("Enter command: ")
        args = command.split()

        if args[0] == "scan":
            discover_services()
        elif args[0] == "connect":
            ip, port = args[1], int(args[2])
            tcp_socket = connect_to_server(ip, port)
        elif args[0] == "rlist":
            list_files(tcp_socket)
        elif args[0] == "put":
            filename = args[1]
            upload_file(tcp_socket, filename)
        elif args[0] == "get":
            filename = args[1]
            download_file(tcp_socket, filename)
        elif args[0] == "llist":
            files = os.listdir(LOCAL_DIRECTORY)
            print('\n'.join(files))

        elif args[0] == "bye":
            tcp_socket.close()
            break

if __name__ == "__main__":
    main()
