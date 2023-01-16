from parser import parse_message
from socket import socket, AF_INET, SOCK_STREAM, gethostname
from threading import Thread

# Server's IP address and port number
host = None  # TODO
port = 7777

buffsz = 4096

# Client socket configuration
client_socket = socket(AF_INET, SOCK_STREAM)
client_socket.connect((host, port))

close_requested = False


# Main logic
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

            interpret_response(response)
    except:
        client_socket.close()
        exit(-1)


# Waits for keyboard input and sends it to server
def handle_input():
    global close_requested

    try:
        while not close_requested:
            message = input()

            if message.startswith('/'):
                message = message[1:]

            client_socket.send(message.encode('utf-8'))
    except:
        client_socket.close()
        exit(-1)


# Converts IRC responses to more readable messages
def interpret_response(response):
    prefix, command, middle, trailing = parse_message(response)

    if command == 'NICK':
        nickname = prefix
        new_nickname = middle[0]
        print(f'{nickname} changed their nickname to {new_nickname}')
    elif command == 'QUIT':
        nickname = prefix
        reason = trailing
        print(f'{nickname} quit: {reason}')
    elif command == 'JOIN':
        nickname = prefix
        channel = middle[0]
        print(f'{nickname} joined {channel}')
    elif command == 'PRIVMSG':
        nickname = prefix
        message = trailing
        print(f'[{nickname}] {message}')
    elif command == '321':  # RPL_LISTSTART
        print(f'{middle[0]} {trailing}')
    elif command == '322':  # RPL_LIST
        channel = middle[0]
        user_count = middle[1]
        print(f'{channel} - {user_count}')
    elif command == '323':  # RPL_LISTEND
        print(trailing)
    elif command == '352':  # RPL_WHOREPLY
        channel = None

        if len(middle) == 5:
            channel = middle[0]
            middle = middle[1:]

        username = middle[0]
        hostname = middle[1]
        servername = middle[2]
        nickname = middle[3]
        realname = trailing

        print(f'Nickname: {nickname}')
        print(f'Username: {username}')
        print(f'Hostname: {hostname}')
        print(f'Server: {servername}')
        print(f'Real name: {realname}')
        print(f'Channel: {channel}')
        print()
    elif command == '315':  # RPL_ENDOFWHO
        print(f'{trailing} ({middle[0]})')
    else:
        print(response)


main()
