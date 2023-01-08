import threading
import socket

# global contants
host = 'localhost'
port = 7777
buffsz = 1024

# global variables
clients = list()
nicknames = list()

socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
socket.bind((host,port))
socket.listen()

def broadcast(message):
  for client in clients:
    client.send(message)

def main():
  while True:
    client, address = socket.accept()
    print(f"[CONNECTION] {address} connected to the server")

    client.send("NICK".encode('ascii'))

    nickname = client.recv(buffsz).decode('ascii')
    nicknames.append(nickname)
    clients.append(client)

    print(f"Nickname of the client is {nickname}!")
    broadcast(f"{nickname} joined the chat!".encode('ascii'))
    client.send("Connected to the server!".encode('ascii'))

    thread = threading.Thread(target=messagesTreatment, args=[client])
    thread.start()


def messagesTreatment(client):
  while True:
    try:
      message = client.recv(buffsz)
      broadcast(message)
    except:
      deleteUser(client)
      break

def deleteUser(client):
  index = clients.index(client)
  clients.remove(client)
  client.close()
  nickname = nicknames[index]
  broadcast(f'{nickname} left the chat!'.encode('ascii'))
  nicknames.remove(nickname)


print("[!] Server is listening...")
main()
