import socket
import threading

nickname = input()

# global constants
host = 'localhost'
port = 7777
buffsz = 1024

# global variables

client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
client.connect((host, port))

def receiveMessages():
  while True:
    try:
      message = client.recv(buffsz).decode('ascii')
      if message == 'NICK':
        client.send(nickname.encode('ascii'))
      else:
        print(message)
    except Exception as e:
      print("[EXCEPTION]", e)
      client.close()
      break

def sendMessages():
  while True:
    message = f'<{nickname}> {input("")}'
    client.send(message.encode('ascii'))

thread1 = threading.Thread(target=receiveMessages)
thread2 = threading.Thread(target=sendMessages)

thread1.start()
thread2.start()
