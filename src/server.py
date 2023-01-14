from parser import parse_message
from socket import socket, AF_INET, SOCK_STREAM
from threading import Thread

host = 'localhost'
port = 7777
buffsz = 4096

channels = {}
client_channels = {}
nicknames = {}
client_nicknames = {}
users = {}


def main():
    server_socket = socket(AF_INET, SOCK_STREAM)
    server_socket.bind((host, port))
    server_socket.listen()

    try:
        while True:
            client_socket, _ = server_socket.accept()

            client_thread = Thread(target=handle_client, args=[client_socket])
            client_thread.start()
    except Exception as e:
        server_socket.close()
        print(e)
        exit(-1)


def handle_client(client_socket):
    try:
        while True:
            message = client_socket.recv(buffsz).decode('utf-8')
            interpret_message(message, client_socket)
    except Exception as e:
        client_socket.close()
        print(e)


def interpret_message(message, client_socket):
    prefix, command, middle, trailing = parse_message(message)

    if command == 'NICK':
        set_nickname(middle.copy(), client_socket)
    elif command == 'USER':
        create_user(middle.copy(), trailing, client_socket)
    elif command == 'QUIT':
        remove_user(trailing, client_socket)
    elif command == 'JOIN':
        join_channel(middle.copy(), client_socket)
    elif command == 'PART':
        part_channel(middle.copy(), client_socket)
    elif command == 'LIST':
        list_channels(client_socket)
    elif command == 'PRIVMSG':
        send_message(middle.copy(), trailing, client_socket)
    elif command == 'WHO':
        list_users(middle.copy(), client_socket)
    else:
        unknown_command(command, client_socket)


def set_nickname(middle, client_socket):
    if client_socket not in users:
        client_socket.send(f':{host} 451 :You have not registered'.encode('utf-8'))
        return
    if len(middle) < 1:
        client_socket.send(f':{host} 431 :No nickname given'.encode('utf-8'))
        return

    nickname = middle[0]

    if not valid_nickname(nickname):
        client_socket.send(f':{host} 432 :Erroneus nickname'.encode('utf-8'))
        return
    if nickname in nicknames:
        client_socket.send(f':{host} 433 :Nickname is already in use'.encode('utf-8'))
        return
    if client_socket in nicknames:
        pass  # TODO

    nicknames[nickname] = client_socket
    client_nicknames[client_socket] = nickname


def create_user(middle, trailing, client_socket):
    if len(middle) < 2 or trailing is None:
        client_socket.send(f':{host} 461 USER :Not enough parameters'.encode('utf-8'))
        return
    if client_socket in users:
        client_socket.send(f':{host} 462 :You may not reregister'.encode('utf-8'))
        return

    username, hostname = middle[:2]
    realname = trailing

    users[client_socket] = (username, hostname, realname)


def remove_user(trailing, client_socket):
    if client_socket not in users or client_socket not in client_nicknames:
        client_socket.send(f':{host} 451 :You have not registered'.encode('utf-8'))
        return

    reason = 'Client disconnected' if trailing is None else trailing
    users.pop(client_socket)
    nicknames.pop(client_nicknames[client_socket])
    client_nicknames.pop(client_socket)

    if client_socket in client_channels:
        client_channel = client_channels[client_socket]
        channels[client_channel].remove(client_socket)
        client_channels.pop(client_socket)
        identifier = f'{client_nicknames[client_socket]}!{users[client_socket][0]}@{users[client_socket[1]]}'
        broadcast(f':{identifier} QUIT :{reason}', client_channels[client_socket])

    # TODO: kill the client process


def join_channel(middle, client_socket):
    if client_socket not in users or client_socket not in client_nicknames:
        client_socket.send(f':{host} 451 :You have not registered'.encode('utf-8'))
        return
    if len(middle) < 1:
        client_socket.send(f':{host} 461 JOIN :Not enough parameters'.encode('utf-8'))
        return

    channel = middle[0]

    if channel[0] not in '#&':
        client_socket.send(f':{host} 403 {channel} :No such channel'.encode('utf-8'))
        return

    channels[channel] = []

    if client_socket in client_channels:
        part_channel(middle, client_socket)

    channels[channel].append(client_socket)
    client_channels[client_socket] = channel
    broadcast(f':{client_nicknames[client_socket]} JOIN {channel}', client_channels[client_socket])


def part_channel(middle, client_socket):
    if client_socket not in users or client_socket not in client_nicknames:
        client_socket.send(f':{host} 451 :You have not registered'.encode('utf-8'))
        return
    if len(middle) < 1:
        client_socket.send(f':{host} 461 PART :Not enough parameters'.encode('utf-8'))
        return

    channel = middle[0]

    if channel not in channels:
        client_socket.send(f':{host} 403 {channel} :No such channel'.encode('utf-8'))
        return
    if client_socket not in channels[channel]:
        client_socket.send(f':{host} 442 {channel} :You\'re not on that channel'.encode('utf-8'))
        return

    identifier = f'{client_nicknames[client_socket]}!{users[client_socket][0]}@{users[client_socket][1]}'
    broadcast(f':{identifier} QUIT :{client_nicknames[client_socket]} left the channel', channel)
    channels[channel].remove(client_socket)
    client_channels.pop(client_socket)

    if len(channels[channel]) == 0:
        channels.pop(channel)


def list_channels(client_socket):
    if client_socket not in users or client_socket not in client_nicknames:
        client_socket.send(f':{host} 451 :You have not registered'.encode('utf-8'))
        return

    client_socket.send(f':{host} 321 Channel :Users  Name'.encode('utf-8'))

    for channel in channels:
        user_count = len(channels[channel])
        client_socket.send(f':{host} 322 {channel} {user_count}'.encode('utf-8'))

    client_socket.send(f':{host} 323 :End of /LIST'.encode('utf-8'))


def send_message(middle, trailing, client_socket):
    if client_socket not in users or client_socket not in client_nicknames:
        client_socket.send(f':{host} 451 :You have not registered'.encode('utf-8'))
        return
    if len(middle) < 1:
        client_socket.send(f':{host} 411 :No recipient given (PRIVMSG)'.encode('utf-8'))
        return
    if trailing is None:
        client_socket.send(f':{host} 412 :No text to send'.encode('utf-8'))

    target = middle[0]
    text = trailing

    if target[0] in '#&':
        if target not in channels:
            client_socket.send(f':{host} 403 {target} :No such channel'.encode('utf-8'))
            return
        if client_socket not in channels[target]:
            client_socket.send(f':{host} 404 {target} :Cannot send to channel'.encode('utf-8'))
            return

        broadcast(f':{client_nicknames[client_socket]} PRIVMSG :{text}', target, tuple([client_socket]))
    else:
        if target not in nicknames:
            client_socket.send(f':{host} 401 {target} :No such nick'.encode('utf=8'))
            return

        respond(f':{client_nicknames[client_socket]} PRIVMSG :{text}', target)


def list_users(middle, client_socket):
    if client_socket not in users or client_socket not in client_nicknames:
        client_socket.send(f':{host} 451 :You have not registered'.encode('utf-8'))
        return
    if len(middle) < 1:
        client_socket.send(f':{host} 411 :No recipient given (PRIVMSG)'.encode('utf-8'))
        return

    target = middle[0]

    if target[0] in '#&':
        if target not in channels:
            client_socket.send(f':{host} 315 {target} :End of /WHO list'.encode('utf-8'))
            return
        for socket in channels[target]:
            if socket not in users or socket not in client_nicknames:
                continue

            username = users[socket][0]
            hostname = users[socket][1]
            realname = users[socket][2]
            nickname = client_nicknames[socket]

            client_socket.send(
                f':{host} 352 {target} {username} {hostname} {host} {nickname} :{realname}'.encode('utf-8'))
    else:
        if target not in nicknames:
            client_socket.send(f':{host} 315 {target} :End of /WHO list'.encode('utf-8'))
            return

        socket = nicknames[target]

        if socket in users:
            username = users[socket][0]
            hostname = users[socket][1]
            realname = users[socket][2]

            if socket in client_channels:
                channel = client_channels[socket]
                client_socket.send(
                    f':{host} 352 {channel} {username} {hostname} {host} {target} :{realname}'.encode('utf-8'))
            else:
                client_socket.send(f':{host} 352 {username} {hostname} {host} {target} :{realname}'.encode('utf-8'))

    client_socket.send(f':{host} 315 {target} :End of /WHO list'.encode('utf-8'))


def unknown_command(command, client_socket):
    if client_socket not in users:
        client_socket.send(f':{host} 451 :You have not registered'.encode('utf-8'))
        return

    client_socket.send(f':{host} 421 {command} :Unknown command'.encode('utf-8'))


def valid_nickname(nickname: str):
    valid_string = nickname[0].isalpha() and all(map(valid_character, nickname))
    return len(nickname) < 9 and valid_string


def valid_character(char: str):
    return char.isalnum() or char in '-[]\\`^{}'


def respond(message, nickname):
    if nickname not in nicknames:
        return  # TODO

    nicknames[nickname].send(message.encode('utf-8'))


def broadcast(message, channel, exclude=()):
    if channel not in channels:
        return  # TODO

    for client_socket in channels[channel]:
        if client_socket not in exclude:
            client_socket.send(message.encode('utf-8'))


main()
