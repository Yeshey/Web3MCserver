from utils import *
import socket

def client_program():
    host = "127.0.0.1"  # as both code is running on same pc
    port = 6323  # socket server port number
    
    client_socket = socket.socket()  # instantiate
    client_socket.connect((host, port))  # connect to the server

    client_socket.send(secret.encode())  # send secret


    client_socket.close()  # close the connection


if __name__ == '__main__':
    global secret
    secret = secret()

    client_program()