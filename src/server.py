import threading
import socket

# global contants
host = 'localhost'
port = 7777
buffsz = 10240

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

    thread = threading.Thread(target=messagesTreatment, args=[client])
    thread.start()

def messagesTreatment(client):
  while True:
    try:
      # bypass to conflict between broadcast and print
      msg = message = client.recv(buffsz)

      if msg.decode('utf-8').startswith("NICK"):
        nickname = msg.decode('utf-8')[5:]

        nicknames.append(nickname)
        clients.append(client)

        print(f"Nickname of the client is {nickname}!")
        broadcast(f"{nickname} joined the chat!".encode('utf-8'))
        client.send("Connected to the server!".encode('utf-8'))

      elif msg.decode('utf-8').startswith("HELP"):
        help_message = msg.decode('utf-8')
        client.send(f"{help_message[5:]}".encode('utf-8'))

      elif msg.decode('utf-8').startswith("QUIT"):
        quitUser(nickname)

      else:
        broadcast(message)
    except:
      if client in clients:
        index = clients.index(client)
        clients.remove(client)
        client.close()
        nickname = nicknames[index]
        broadcast(f"{nickname} left the chat!".encode('utf-8'))
        nicknames.remove(nickname)
        break

def quitUser(name):
  if name in nicknames:
    name_index = nicknames.index(name)
    client_to_quit = clients[name_index]
    clients.remove(client_to_quit)
    client_to_quit.send("You have left the server!".encode('utf-8'))
    client_to_quit.close()
    nicknames.remove(name)
    broadcast(f"{name} left the chat!".encode('utf-8'))

print("[!] Server is listening...")
main()
