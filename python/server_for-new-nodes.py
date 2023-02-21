# https://stackoverflow.com/questions/18616226/how-to-get-a-python-script-to-listen-for-inputs-from-another-script

import socket
s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.bind(("localhost", 6323))
s.listen(1)

while True:
    conn, addr = s.accept()
    data = conn.recv(1024)
    conn.close()
    my_function_that_handles_data(data)