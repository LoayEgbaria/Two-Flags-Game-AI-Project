# Created and Developed by : Loay Egbaria

# server that will handle the communication between the two agents (clients).
# The server will wait for two clients to connect, then it will relay messages between them according to the protocol.

import socket
import tkinter as tk
from tkinter import ttk
import tkinter.messagebox
import pygame
from datetime import datetime

global time
global boardArray

clients = []

# CREATE ONE SHARED MOVES FILE
timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
moves_file = open(f"game_{timestamp}.moves", "w")
moves_file.write(f"Game started at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
moves_file.write("=" * 50 + "\n\n")
move_counter = 0

def write_move(player, move, score=None):
    global move_counter
    move_counter += 1
    moves_file.write(f"Move {move_counter}: {player} - {move}")
    if score is not None:
        moves_file.write(f" (Score: {score})")
    moves_file.write("\n")
    moves_file.flush()

# Create a server socket

serverSocket = socket.socket()

print("Server socket created")

# Associate the server socket with the IP and Port

ip = "127.0.0.1"

port = 9999

serverSocket.bind((ip, port))

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
    #DODIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIII
    data = clients[0].recv(1024)
    data.decode()
    data = clients[1].recv(1024)
    data.decode()

    # send Time x to clients
    time = input() + "\n"
    moves_file.write(f"Time: {time.strip()} minutes\n")
    time = str.encode(time)
    clients[0].send(time)
    clients[1].send(time)
    
    #DODIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIII
    data = clients[0].recv(1024)
    data.decode()
    data = clients[1].recv(1024)
    data.decode()


    # send Begin to clients
    msg = input() + "\n"
    msg = str.encode(msg)
    clients[0].send(msg)
    clients[1].send(msg)

    msg = str.encode("White\n")
    clients[0].send(msg)
    moves_file.write("White: Player 1\n")
    
    msg = str.encode("Black\n")
    clients[1].send(msg)
    moves_file.write("Black: Player 2\n")

    # Classic for normal board, SETUP (ends with either BLACK/WHITE) otherwise
    setup = input() + "\n"
    moves_file.write(f"Setup: {setup.strip()}\n\n")
    msg = str.encode(setup)
    clients[0].send(msg)
    clients[1].send(msg)

    msg = msg.decode()
    if msg.endswith("Black"):
        player_index = 1
        msg = msg.encode()
    elif msg.endswith("White"):
        player_index = 0
        msg = msg.encode()
    else:
        player_index = 0

    # read from client connection
    while (True):

       if player_index == 0:
           msg = str.encode("White's turn\n")
           clients[1].send(msg)
       else:
           msg = str.encode("Black's turn\n")
           clients[0].send(msg)

       msg = str.encode("Your turn\n")
       clients[player_index].send(msg)
       data = clients[player_index].recv(1024)

       if (data != b''):

            data = data.decode()
            if data == "exit\n":
                msg1Bytes = str.encode("exit\n")
                clients[0].send(msg1Bytes)
                clients[1].send(msg1Bytes)
                print("agent wants to end the game.")
                print("Connection closed")
                moves_file.write("\n" + "=" * 50 + "\n")
                moves_file.write(f"Game ended at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                moves_file.close()
                break

            if data == "Win\n":
                if player_index:
                    print("Black player won")
                    moves_file.write("\nBlack wins!\n")
                else:
                    print("White player won")
                    moves_file.write("\nWhite wins!\n")
                msg1Bytes = str.encode("exit\n")
                clients[0].send(msg1Bytes)
                clients[1].send(msg1Bytes)
                moves_file.write("\n" + "=" * 50 + "\n")
                moves_file.write(f"Game ended at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                moves_file.close()
                break

            if data == "Lost\n":
                if player_index:
                    print("Black player won")
                    moves_file.write("\nBlack wins!\n")
                else:
                    print("White player won")
                    moves_file.write("\nWhite wins!\n")
                msg1Bytes = str.encode("exit\n")
                clients[0].send(msg1Bytes)
                clients[1].send(msg1Bytes)
                moves_file.write("\n" + "=" * 50 + "\n")
                moves_file.write(f"Game ended at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                moves_file.close()
                break

            # LOG THE MOVE TO SHARED FILE
            player_name = "White" if player_index == 0 else "Black"
            write_move(player_name, data.strip())

            data = data.encode()
            msg = data
            if(player_index==0):
                player_index=1
            else:
                player_index=0
            clients[player_index].send(msg)
    break