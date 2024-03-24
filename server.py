import socket
import threading
import os

# Configuration
SERVICE_DISCOVERY_PORT = 30000
FILE_SHARING_PORT = 30001
SHARED_DIRECTORY = './shared_files'
SERVICE_NAME = "Bill's File Sharing Service"

if not os.path.exists(SHARED_DIRECTORY):
    os.makedirs(SHARED_DIRECTORY)

def handle_client_connection(client_socket):
    while True:
        try:
            command = client_socket.recv(1024)
            if not command:
                break
            
            if command == b'\x03':  # list command
                files = os.listdir(SHARED_DIRECTORY)
                files_list = '\n'.join(files).encode('utf-8')
                client_socket.sendall(files_list)
                print(f"List of files sent: {files_list}")

            elif command.startswith(b'\x02'):  # put command
                print(command)
                filename = command.strip(b'\x02').split(b'\x00', 1)[0]
                filename = filename.decode()
                print(f"Receiving file {filename}.")
                file_path = os.path.join(SHARED_DIRECTORY, filename)
                with open(file_path, 'wb') as f:
                    data = client_socket.recv(1024)
                    f.write(data)
                    while data:
                        data = client_socket.recv(1024)
                        f.write(data)
                        if data == b"package_end":
                            break

                print(f"File {filename} received.")

            elif command.startswith(b'\x01'):  # get command
                print(command)
                filename = command.strip(b'\x01').split(b'\x00', 1)[0]
                filename = filename.decode()
                file_path = os.path.join(SHARED_DIRECTORY, filename)
                with open(file_path, 'rb') as f:
                    data = f.read(1024)
                    print(data)
                    while data:
                        client_socket.send(data)
                        data = f.read(1024)
                client_socket.send(b"package_end")       
                print(f"File {filename} sent.")

        except Exception as e:
            print(f"Error handling command: {e}")
            if command.startswith(b'\x02'):
                # Remove the file if it was not received completely
                os.remove(file_path)
            break
    print("Connection closed.")
    client_socket.close()

def start_tcp_server():
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.bind(('', FILE_SHARING_PORT))
    server_socket.listen(5)
    print(f"Listening for file sharing connections on port {FILE_SHARING_PORT}.")
    
    while True:
        client_socket, addr = server_socket.accept()
        print(f"Connection received from {addr[0]} on port {addr[1]}.")
        client_thread = threading.Thread(target=handle_client_connection, args=(client_socket,))
        client_thread.start()

def start_udp_server():
    udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    udp_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    udp_socket.bind(('', SERVICE_DISCOVERY_PORT))
    print(f"Listening for service discovery messages on SDP port {SERVICE_DISCOVERY_PORT}.")
    
    while True:
        data, addr = udp_socket.recvfrom(1024)
        if data.decode('utf-8') == "SERVICE DISCOVERY":
            print(f"Service discovery request received from {addr[0]} on port {addr[1]}.")
            response = SERVICE_NAME.encode('utf-8')
            udp_socket.sendto(response, addr)

# Start UDP and TCP servers in parallel
udp_thread = threading.Thread(target=start_udp_server)
udp_thread.start()

start_tcp_server()
