# Created and Developed by : Loay Egbaria

# server that will handle the communication between the two agents (clients).
# The server will wait for two clients to connect, then it will relay messages between them according to the protocol.

import socket
import tkinter as tk
from tkinter import ttk
import tkinter.messagebox
import pygame
global time
global boardArray

clients = []  # list to store the two connected clients

# Create a server socket
serverSocket = socket.socket()
print("Server socket created")

# Associate the server socket with the IP and Port
ip = "127.0.0.1"
port = 9999
serverSocket.bind((ip, port))  # bind server to localhost and port 9999
print("Server socket bound with with ip {} port {}".format(ip, port))

# Make the server listen for incoming connections
serverSocket.listen()

# Server incoming connections "one by one"
count = 0

while (True):

    # wait for the two agents to connect
    (clientConnection, clientAddress) = serverSocket.accept()
    count = count + 1
    clients.append(clientConnection)

    (clientConnection, clientAddress) = serverSocket.accept()
    count = count + 1
    clients.append(clientConnection)

    print("Accepted {} connections".format(count))

    msg = str.encode("Connected to the server\n")

    clients[0].send(msg)
    clients[1].send(msg)

    # waiting for OK from both clients
    data = clients[0].recv(1024)
    data.decode()
    data = clients[1].recv(1024)
    data.decode()

    # send Time x to clients
    time = input() + "\n"  # server manually enters time command
    time = str.encode(time)
    clients[0].send(time)
    clients[1].send(time)
    
    # waiting again for OK from both clients
    data = clients[0].recv(1024)
    data.decode()
    data = clients[1].recv(1024)
    data.decode()

    # send Begin to clients
    msg = input() + "\n"  # usually "Begin"
    msg = str.encode(msg)
    clients[0].send(msg)
    clients[1].send(msg)

    # assign colors
    msg = str.encode("White\n")
    clients[0].send(msg)
    msg = str.encode("Black\n")
    clients[1].send(msg)

    # Classic for normal board, SETUP otherwise
    msg = input() + "\n"  # setup command if needed
    msg = str.encode(msg)
    clients[0].send(msg)
    clients[1].send(msg)

    msg = msg.decode()
    if msg.endswith("Black"):
        player_index = 1  # black starts
        msg = msg.encode()
    elif msg.endswith("White"):
        player_index = 0  # white starts
        msg = msg.encode()
    else:
        player_index = 0  # default white starts

    # main game loop
    while (True):

       if player_index == 0:
           msg = str.encode("White's turn\n")
           clients[1].send(msg)
       else:
           msg = str.encode("Black's turn\n")
           clients[0].send(msg)

       msg = str.encode("Your turn\n")
       clients[player_index].send(msg)

       data = clients[player_index].recv(1024)  # receive move from current player

       if (data != b''):

            data = data.decode()

            if data == "exit\n":  # player wants to quit
                msg1Bytes = str.encode("exit\n")
                clients[0].send(msg1Bytes)
                clients[1].send(msg1Bytes)
                print("agent wants to end the game.")
                print("Connection closed")
                break

            if data == "Win\n":  # player declares win
                if player_index:
                    print("Black player won")
                else:
                    print("White player won")
                msg1Bytes = str.encode("exit\n")
                clients[0].send(msg1Bytes)
                clients[1].send(msg1Bytes)
                break

            if data == "Lost\n":  # player declares loss
                if player_index:
                    print("Black player won")
                else:
                    print("White player won")
                msg1Bytes = str.encode("exit\n")
                clients[0].send(msg1Bytes)
                clients[1].send(msg1Bytes)
                break

            data = data.encode()
            msg = data  # forward move to opponent

            # switch turns
            if(player_index==0):
                player_index=1
            else:
                player_index=0

            clients[player_index].send(msg)  # send move to other player

    break  # end after one match
