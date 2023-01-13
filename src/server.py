import threading
import socket
import select

# global contants
host = 'localhost'
port = 7777
buffsz = 10240

# socket configuration
s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.bind((host,port))
s.listen()

# global variables
clients = [s]
nicknames = list()

channelDict = dict([("", "")])
connectedClients = []
dictClients = {}
clientIsInChannel = {}
clientChannel = {}

def main():
  while True:
    l, a, b = select.select(clients, [], [])

    for socket in l:
      # new client connected
      if socket is s:
        client, address = socket.accept()
        clients.append(client)

        address, port = client.getpeername()
        clientId = formatAdresse(address, port)
        print(f"[CONNECTION] {clientId} connected to the server")

        dictClients[client] = clientId
        channelDict[""] = dictClients
        clientIsInChannel[client] = False
        clientChannel[client] = ""
      # new data received
      else:
        messagesTreatment(socket)

def formatAdresse(adress, port):
  ip_address = "\"127.0.0.1:"+ str(port) + "\""
  return ip_address

# This function allows sending messages between
# clients connected to the server
def broadcast(message):
  for e in range(len(dictClients)):
    client = [key for key in dictClients.keys()][e]
    client.send(message)

# This function allows sending message between channels
def broadcast_channel(message, channel, client):
  for cl in clients:
    if cl is not client and cl is not s and cl in channelDict[channel]:
      cl.send(message)

# This function allows the user to choose a nickname.
def nickname(name, client):
  dictClients[client] = name
  connectedClients.append(name)
  print(f"Nickname of the client is {name}!")
  client.send(f"Connected to the server!".encode('utf-8'))

# This function allows the user to exit the server.
def quitServer(client):
  nickname = dictClients[client]
  connectedClients.remove(nickname)
  clients.remove(client)
  del dictClients[client]
  client.send("You have left the server!".encode('utf-8'))
  client.close()
  broadcast(f"{nickname} left the chat!".encode('utf-8'))

# This function sends the user a help message.
def helpMessage(help_msg, client):
  client.send(help_msg.encode('utf-8'))

# This function creates a channel and add client on it.
def join(channel, client):
  if clientIsInChannel[client] == False:
    nickname = dictClients[client]

    if channel not in channelDict:
      channelDict[channel] = dict([(client, nickname)])
    else:
      channelDict[channel][client] = nickname

    clientIsInChannel[client] = True
    clientChannel[client] = channel

    broadcast_channel((f"{nickname} joined {channel}!".encode('utf-8')), channel, client)
  else:
    client.send("You're already in a channel".encode('utf-8'))

# This function allows the user to see all
# active channels on the server.
def listChannels(client):
  len_channels = len(channelDict.items())-1
  channels_list= "[CHANNEL] "

  if len_channels > 1:
    channels_list= "[CHANNELS] "

  for key, value in channelDict.items():
    if key != "":
      channels_list += f'{str(key)} '

  client.send(channels_list.encode('utf-8'))

# This function allows the user to leave a channel
def partChannel(channel, client):
  if channel in channelDict:
    nickname = dictClients[client]

    broadcast_channel((f"{nickname} left the {channel} channel!".encode('utf-8')), channel, client)
    client.send(f"You left the {channel} channel".encode('utf-8'))

    if client in channelDict[channel]:
      del channelDict[channel][client]
      if len(channelDict[channel]) == 0:
        del channelDict[channel]

    clientIsInChannel[client] = False
    clientChannel[client] = ""

  elif channel == "":
    broadcast("You're not in a channel")

# This function handles messages sent by the user.
def messagesTreatment(client):
  try:
    msg = message = client.recv(buffsz)

    if len(msg) != 0:
      if msg.decode('utf-8').startswith("NICK"):
        name = msg.decode('utf-8')[5:]
        nickname(name, client)

      elif msg.decode('utf-8').startswith("QUIT"):
        quitServer(client)

      elif msg.decode('utf-8').startswith("HELP"):
        help_message = msg.decode('utf-8')[5:]
        helpMessage(help_message, client)

      elif msg.decode('utf-8').startswith("JOIN"):
        channel_to_join = msg.decode('utf-8')[5:]
        join(channel_to_join, client)

      elif msg.decode('utf-8').startswith("LIST"):
        listChannels(client)

      elif msg.decode('utf-8').startswith("PART"):
        partChannel(clientChannel[client], client)

      else:
        if clientIsInChannel[client] == True:
          broadcast_channel(message, clientChannel[client], client)
  except:
      clients.remove(client)
      client.close()

print("[!] Server is listening...")
main()
