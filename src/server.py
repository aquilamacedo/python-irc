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
allChannels = []
connectedClients = []
dictClients = {}
clientIsInChannel = {}
clientChannel = {}
dictWho = {}
dictCredential = {}

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
  if name not in connectedClients:
    dictClients[client] = name
    connectedClients.append(name)
    print(f"Nickname of the client is {name}!")
    client.send(f"Connected to the server!".encode('utf-8'))
  else:
    client.send(f"[ERROR] Nickname {name} is already in use.".encode('utf-8'))

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
    dictWho.setdefault(channel, []).append(nickname)

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
  channelMsg = "[CHANNEL]\n"

  if len_channels > 1:
    channelMsg = "[CHANNELS]\n"

  channelsList = list(channelDict.keys())
  print_channels = '\n'.join(map(str,channelsList[1:]))

  client.send(channelMsg.encode('utf-8'))
  client.send(print_channels.encode('utf-8'))

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

# This function shows all active users in a channel
# using the command:
# /WHO <#channel_name>
def whoChannel(who_channel, client):
  if who_channel in channelDict:
    usersChannel = dictWho[who_channel]
    print_users = '\n'.join(map(str,usersChannel))

    client.send(f"Online users on {who_channel} channel:\n".encode('utf-8'))
    client.send(print_users.encode('utf-8'))


def privMessage(channel_or_username, message, client):
  if channel_or_username[0] == "#":
    # Allows a user outside a channel to direct a message
    # to the channel using the command:
    # /PRIVMSG <#channel_name> <msg>
    channel = channel_or_username

    if clientIsInChannel[client] == False:
      nickname = dictClients[client]
      dictWho.setdefault(channel, []).append(nickname)

      if channel not in channelDict:
        channelDict[channel] = dict([(client, nickname)])
      else:
        channelDict[channel][client] = nickname

      clientIsInChannel[client] = True
      clientChannel[client] = channel

      broadcast_channel(message.encode('utf-8'), channel, client)

    if client in channelDict[channel]:
      del channelDict[channel][client]
      if len(channelDict[channel]) == 0:
        del channelDict[channel]

    clientIsInChannel[client] = False
    clientChannel[client] = ""
  else:
    # Allows a user to send a private message to another
    # user who is active on the server, using the command:
    # /PRIVMSG <target_username> <msg>
    target_username = channel_or_username
    current_username = dictClients[client]

    x = list(dictClients.items())

    for i in range(len(x)):
      if target_username in x[i]:
        valueREAL = x[i]

    for cl in clients:
      if cl is not client and cl is not s and cl in valueREAL:
        cl.send(f"{current_username} sent you a private message".encode('utf-8'))
        cl.send(message.encode('utf-8'))

def userCredentials(user_credentials, client):
  handle_credentials = user_credentials.split()

  username = handle_credentials[0]
  hostname = handle_credentials[1]
  realname_list = handle_credentials[2:]
  realname = ' '.join(realname_list)

  for credential in [client, hostname, realname]:
    dictCredential.setdefault(username, []).append(credential)

def whoIsUser(user, client):
  if user in dictCredential:
    credentials = dictCredential[user]
    client_target = credentials[0]
    hostname_target = credentials[1]
    realname_target = credentials[2]

    client.send(f"realname : {realname_target}\n".encode('utf-8'))
    client.send(f"hostname : {hostname_target}\n".encode('utf-8'))
    client.send(f"server   : {host}".encode('utf-8'))
  else:
    client.send(f"[ERROR] The user {user} does not exist".encode('utf-8'))

# This function handles messages sent by the user.
def messagesTreatment(client):
  try:
    msg = message = client.recv(buffsz)

    if len(msg) != 0:
      if msg.decode('utf-8').startswith("NICK"):
        name = msg.decode('utf-8')[5:]
        nickname(name, client)

      elif msg.decode('utf-8').startswith("JOIN"):
        channel_to_join = msg.decode('utf-8')[5:]
        join(channel_to_join, client)

      elif msg.decode('utf-8').startswith("WHOIS"):
        username = msg.decode('utf-8')[6:]
        whoIsUser(username, client)

      elif msg.decode('utf-8').startswith("WHO"):
        who_channel = msg.decode('utf-8')[4:]
        whoChannel(who_channel, client)

      elif msg.decode('utf-8').startswith("LIST"):
        listChannels(client)

      elif msg.decode('utf-8').startswith("USER"):
        user_credentials = msg.decode('utf-8')[5:]
        userCredentials(user_credentials,client)

      elif msg.decode('utf-8').startswith("PRIVMSG"):
        priv_treatment = msg.decode('utf-8')[8:]
        priv_treatment = priv_treatment.split()
        channel_or_user = priv_treatment[1]
        priv_message = priv_treatment[2:]
        priv_str = ' '.join(priv_message)
        privMessage(channel_or_user, priv_str, client)

      elif msg.decode('utf-8').startswith("PART"):
        partChannel(clientChannel[client], client)

      elif msg.decode('utf-8').startswith("QUIT"):
        quitServer(client)

      elif msg.decode('utf-8').startswith("HELP"):
        help_message = msg.decode('utf-8')[5:]
        helpMessage(help_message, client)

      else:
        if clientIsInChannel[client] == True:
          broadcast_channel(message, clientChannel[client], client)
  except:
      clients.remove(client)
      client.close()

print("[!] Server is listening...")
main()
