# https://stackoverflow.com/questions/18616226/how-to-get-a-python-script-to-listen-for-inputs-from-another-script

import socket
s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.connect(("localhost", 6323))
s.sendall('My parameters that I want to share with the server')
s.close()