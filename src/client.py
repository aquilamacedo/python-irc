import socket
import threading

# global constants and variables
host = 'localhost'
port = 7777
buffsz = 10240
nickname = ''

HELP_MESSAGE = """The list of commands available are:
    /NICK - Give the user a nickname or change the previous one.
    /USER - Specify a user's username, hostname, and real name.
    /QUIT - log out of the client session.
    /JOIN - Start listening to a specific channel.
    /PART - Leave a specific channel.
    /LIST - List all existing channels only on the local server.
    /WHO - Query information about customers or channels.
    /PRIVMSG – Send messages to users. The target can be a nickname or a channel. if the destination is a channel, the message must be broadcast to all users on the specified channel except message originator. If the target is a nickname, the message will be sent only to that user."""

client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
client.connect((host, port))

def receiveMessages():
  while True:
    try:
      message = client.recv(buffsz).decode('utf-8')
      print(message)
    except:
      client.close()
      break

def sendMessages(nickname):
  while True:
    if nickname == '':
      message = input('> ')
    else:
      message = f'<{nickname}> {input("")}'

    if message.startswith('/'):

        if message.startswith('/NICK'):
          nickname = message[6:]
          client.send(f"NICK {nickname}".encode('utf-8'))

        elif message.startswith("/HELP"):
          client.send(f"HELP {HELP_MESSAGE}".encode('utf-8'))

        elif message.startswith("/QUIT"):
          client.send(f"QUIT".encode('utf-8'))
          client.close()
          break
    else:
      client.send(message.encode('utf-8'))

thread1 = threading.Thread(target=receiveMessages)
thread1.start()

thread2 = threading.Thread(target=sendMessages, args=[nickname])
thread2.start()
