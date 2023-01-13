from parser import parse_message
from socket import socket, AF_INET, SOCK_STREAM
from threading import Thread

host = 'localhost'
port = 7777
buffsz = 4096
nickname = ''

client_socket = socket(AF_INET, SOCK_STREAM)
client_socket.connect((host, port))


def main():
    input_thread = Thread(target=handle_input)
    input_thread.start()

    try:
        while True:
            response = client_socket.recv(buffsz).decode('utf-8')
            print(response)
    except Exception as e:
        client_socket.close()
        print(e)
        exit(-1)


def handle_input():
    try:
        while True:
            message = input()
            client_socket.send(message.encode('utf-8'))
    except Exception as e:
        client_socket.close()
        print(e)
        exit(-1)


def interpret_message(message):
    prefix, command, middle, trailing = parse_message(message)

    if command == 'NICK':
        pass
    elif command == 'QUIT':
        pass
    elif command == 'JOIN':
        pass
    elif command == 'PRIVMSG':
        pass
    else:
        print(message)


main()
