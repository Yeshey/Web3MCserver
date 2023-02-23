from utils import *
import socket

def client_program():
    host = "mean-street.at.ply.gg"  # as both code is running on same pc
    port = 62026  # socket server port number
    
    client_socket = socket.socket()  # instantiate
    client_socket.connect((host, port))  # connect to the server

    client_socket.send(secret.encode())  # send secret


    client_socket.close()  # close the connection


if __name__ == '__main__':
    global secret
    secret = secret()

    client_program()