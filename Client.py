import pygame
from Board import ChessBoard
from UserInterface import UserInterface, PonderThread
import socket
import sys

global time
global color
global surface
global UI

time = 0
color = None
move_number = 0  # Track move count for the log file
log_file = open("game_log.moves", "w", encoding="utf-8")
log_file.write("# Two Flags Game - Move Log\n")
log_file.write("# Format: Move | Color | Algebraic | Score | Depth\n")
log_file.write("-" * 55 + "\n")
log_file.flush()

socketObject = socket.socket()
socketObject.connect(("localhost", 9999))

pygame.init()
surface = pygame.display.set_mode([600, 600], 0, 0)
pygame.display.set_caption('Pawn Game')
Board = ChessBoard()
UI = UserInterface(surface, Board)
UI.human = False

def log_move(color_label, move_algebraic, score, depth):
    """Write a move to the game_log.moves file"""
    global move_number
    move_number += 1
    line = f"Move {move_number:>3} | {color_label:<6} | {move_algebraic:<5} | Score: {str(score):<8} | Depth: {depth}\n"
    log_file.write(line)
    log_file.flush()

def process_message(data):
    global time, color, surface, UI
    print("Processing:", data)

    if data == "Connected to the server":
        socketObject.send("OK\n".encode())

    elif data.startswith("Time"):
        parts = data.split()
        time = int(parts[1]) * 60
        UI.time = time
        UI.chessboard.round = int(time / 16)
        socketObject.send("OK\n".encode())

    elif data == "Begin":
        human = input("Do you want to play as a human(h) or AI (a)? ").strip().lower()
        UI.human = (human == "h")
        socketObject.send("OK\n".encode())

    elif data == "White":
        color = "W"
        UI.playercolor = color
        log_file.write("# Playing as: White\n")
        log_file.flush()

    elif data == "Black":
        color = "B"
        UI.playercolor = color
        log_file.write("# Playing as: Black\n")
        log_file.flush()

    elif data == "Classic":
        UI.chessboard.boardArray = [[" " for _ in range(8)] for _ in range(8)]
        UI.chessboard.boardArray[1] = ["p"] * 8
        UI.chessboard.boardArray[6] = ["P"] * 8
        if time > 0:
            UI.chessboard.round = int(time / 16)
        UI.drawComponent()
        log_file.write("# Setup: Classic\n")
        log_file.flush()

    elif data.startswith("Setup"):
        tokens = data.split()
        pawn_num = 0
        for row in range(8):
            for col in range(8):
                pygame.event.pump()
                UI.chessboard.boardArray[row][col] = " "
        for token in tokens[1:]:
            pygame.event.pump()
            side = token[0]
            pos = token[1:]
            row = 8 - int(pos[1])
            col = ord(pos[0].lower()) - ord('a')
            if side == "W":
                UI.chessboard.boardArray[row][col] = "P"
            else:
                UI.chessboard.boardArray[row][col] = "p"
            pawn_num += 1
        if pawn_num > 0 and time > 0:
            UI.chessboard.round = int(time / pawn_num)
        UI.drawComponent()
        log_file.write(f"# Setup: {data}\n")
        log_file.flush()

    elif data == "Your turn":
        move_data, flag = UI.clientMove()

        if flag == 1:
            msg = "Win\n"
            log_file.write("# Result: WIN\n")
            log_file.flush()
        elif flag == -1:
            msg = "Lost\n"
            log_file.write("# Result: LOST\n")
            log_file.flush()
        elif move_data == "exit":
            print("No best move found")
            msg = "exit\n"
        else:
            # Convert internal format → algebraic (e.g. e2e4)
            alg_move = ""
            alg_move += str(chr(97 + int(move_data[1])))
            alg_move += str(8 - int(move_data[0]))
            alg_move += str(chr(97 + int(move_data[3])))
            alg_move += str(8 - int(move_data[2]))
            msg = alg_move + "\n"

            # Log it — grab last depth/score from UI's last search
            color_label = "White" if UI.playercolor == "W" else "Black"
            log_move(color_label, alg_move, "our turn", UI.search_depth)

        socketObject.send(msg.encode())

    elif data in ["White's turn", "Black's turn"]:
        if UI.playercolor is not None:
            if ((UI.playercolor == "W" and data == "Black's turn") or
                    (UI.playercolor == "B" and data == "White's turn")):
                if UI.ponder_thread is None:
                    UI.ponder_thread = PonderThread(
                        UI, UI.chessboard, UI.playercolor, max_depth=10, time_limit=10)
                    UI.ponder_thread.start()

    elif data == "exit":
        print("Connection closed")
        log_file.write("# Game ended.\n")
        log_file.close()
        pygame.quit()
        socketObject.close()
        sys.exit(0)

    else:
        # Opponent move (e.g. "e2e4")
        if (len(data) == 4
                and data[0].isalpha() and data[1].isdigit()
                and data[2].isalpha() and data[3].isdigit()):

            # Log opponent move
            opp_label = "Black" if UI.playercolor == "W" else "White"
            log_move(opp_label, data, "opponent", "-")

            move = ""
            move += str(8 - int(data[1]))
            move += str(ord(data[0]) - 97)
            move += str(8 - int(data[3]))
            move += str(ord(data[2]) - 97)
            if abs(int(move[0]) - int(move[2])) == 2:
                UI.chessboard.enpassant = True
                UI.chessboard.enpassantCol = int(move[3])
            UI.chessboard.changePerspective()
            UI.chessboard.computeMove(move, "opponent")
            UI.chessboard.changePerspective()
            UI.drawComponent()
        else:
            print(f"Unknown message ignored: '{data}'")

# Main receive loop
buffer = ""
try:
    while True:
        received = socketObject.recv(1024)
        if not received:
            break
        received = received.decode()
        buffer += received
        while "\n" in buffer:
            message, buffer = buffer.split("\n", 1)
            message = message.strip()
            if message:
                process_message(message)

except KeyboardInterrupt:
    print("\nClient stopped.")
except Exception as e:
    print(f"Error: {e}")
finally:
    log_file.write("# Session ended.\n")
    log_file.close()
    pygame.quit()
    socketObject.close()