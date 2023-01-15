from socket import socket, AF_INET, SOCK_STREAM, gethostname
from threading import Thread

host = gethostname()
port = 7777
buffsz = 4096

client_socket = socket(AF_INET, SOCK_STREAM)
client_socket.connect((host, port))

close_requested = False


def main():
    global close_requested

    input_thread = Thread(target=handle_input)
    input_thread.start()

    try:
        while not close_requested:
            response = client_socket.recv(buffsz).decode('utf-8')

            if not response:
                close_requested = True
                break

            print(response)
    except:
        client_socket.close()
        exit(-1)


def handle_input():
    global close_requested

    try:
        while not close_requested:
            message = input()
            client_socket.send(message.encode('utf-8'))
    except:
        client_socket.close()
        exit(-1)


main()
