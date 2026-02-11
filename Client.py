# import the socket module
import pygame
from board import ChessBoard
from UserInterface import UserInterface, PonderThread
import chess
import socket

global time
global color
global surface
global UI

# Create a socket instance

socketObject = socket.socket()

# Using the socket connect to a server...in this case localhost

socketObject.connect(("localhost",9999))

# Send a message to the web server to supply a page as given by Host param of GET request

def process_message(data):
    global time, color, surface, UI, role
    print("Processing:", data)

    if data.startswith("Time"):
        time = int(data[4:]) * 60
        socketObject.send("OK\n".encode())

    elif data.startswith("Setup"):
        tokens = data.split()  # Split the string into tokens by spaces.
        # tokens[0] will be "Setup", and tokens[1:] are the individual piece placements.
        pawn_num = 4
        UI.firstgame = False
        for i in range(64):
            pygame.event.pump()
            UI.chessboard.boardArray[i // 8][i % 8] = " "
        for token in tokens[1:]:
            pygame.event.pump()
            side = token[0]          # 'W' or 'B'
            pos = token[1:]          # e.g., "a2" or "a7"
            row = 8 - int(pos[1])    # Use the same conversion for both colors.
            col = ord(pos[0].lower()) - ord('a')
            if side == "W":
                UI.chessboard.boardArray[row][col] = "P"
                pawn_num += 1
            else:
                UI.chessboard.boardArray[row][col] = "p"
        UI.chessboard.round = int(time/pawn_num)
        UI.drawComponent()

    elif data == "White":
        color = "W"
        UI.playercolor = color
    
    elif data == "Black":
        color = "B"
        UI.playercolor = color
    
    elif data == "exit":
        print("Connection closed")
        socketObject.send("exit\n".encode())
        exit(0)
    
    elif data == "Your turn":
        move_data, flag = UI.clientMove()
        if flag == 1:
            msg = "Win\n"
        elif flag == -1:
            msg = "Lost\n"

        elif move_data == "exit":
            print("No best move")
            msg = "exit\n"
        else:
            move = ""
            move += str(chr(97 + int(move_data[1])))
            move += str(8 - int(move_data[0]))
            move += str(chr(97 + int(move_data[3])))
            move += str(8 - int(move_data[2]))
            msg = move + "\n"
        socketObject.send(msg.encode())
    elif data == "Begin":
        pygame.init()

        surface = pygame.display.set_mode([600, 600], 0, 0)
        pygame.display.set_caption('Pawn Game')
        Board = ChessBoard()
        UI = UserInterface(surface, Board)
        UI.time = time
        UI.chessboard.round = int(time / 14)
        human = input("Do you want to play as a human(h) or AI (a)?").strip().lower()
        if human == "h":
            UI.human = True
        
    elif data == "Classic":
        UI.drawComponent()
    elif data in ["White's turn", "Black's turn"]:
        # If the message indicates that it's the opponent's turn,
        # then start pondering if we’re not already pondering.
        # (Assume that if our playercolor is "W", then "Black's turn" means opponent.)
        if ((UI.playercolor == "W" and data == "Black's turn") or 
            (UI.playercolor == "B" and data == "White's turn")):

            if UI.ponder_thread is None:
                # Start a new ponder thread on the current board position.
                UI.ponder_thread = PonderThread(UI, UI.chessboard, UI.playercolor, max_depth=10, time_limit=10)
                UI.ponder_thread.start()
        pass

    elif data == "Connected to the server":
        socketObject.send("OK\n".encode())

    else:
        move = ""
        move += str(8 - int(data[1]))
        move += str(ord(data[0]) - 97)
        move += str(8 - int(data[3]))
        move += str(ord(data[2]) - 97)
        if int(move[1]) - int(move[3]) in (2, -2):
            UI.chessboard.enpassant = True
            UI.chessboard.enpassantCol = int(move[0])
        UI.chessboard.changePerspective()
        UI.chessboard.computeMove(move, "opponent")
        UI.chessboard.changePerspective()
        UI.drawComponent()

# Main loop for client
buffer = ""
while True:
    received = socketObject.recv(1024)
    if not received:
        break
    received=received.decode()
    buffer += received
    while "\n" in buffer:
        message, buffer = buffer.split("\n", 1)
        message = message.strip()
        if message:
            process_message(message)

pygame.quit()
socketObject.close()