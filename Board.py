# Created and Developed by : Loay Egbaria

# ChessBoard class to represent the game board and handle moves
# The board is represented as an 8x8 array, with "P" for white pawns, "p" for black pawns, and " " for empty squares.

class ChessBoard:
    def __init__(self):
        self.boardArray = [[" " for _ in range(8)] for _ in range(8)]    # Creating an empty board
        self.boardArray[1] = ["p"] * 8
        self.boardArray[6] = ["P"] * 8
        self.enpassant = False  # Flag and col for enpassant
        self.enpassantCol = -1
        self.enpassantRow = -1  # Row of the pawn that can be captured en passant
        self.round = 0  # Round duration

    def changePerspective(self):
        self.boardArray = self.boardArray[::-1]    # Reversing rows

    def computeMove(self, move, mode):
        if len(move) != 4:
            print("Invalid move")
            return

        try:

            if mode == "opponent":
                self.changePerspective()
            src_row = int(move[0])
            src_col = int(move[1])
            dest_row = int(move[2])
            dest_col = int(move[3])
        
        except ValueError:
            print("Invalid digits")
            return
        
        piece = self.boardArray[src_row][src_col]

        if self.enpassant:
            if abs(src_col - dest_col) == 1 and abs(src_row - dest_row) >= 1:
                # The pawn is moving diagonally and must be capturing an opponent's pawn
                if self.boardArray[dest_row][dest_col] == " ":
                    # En passant capture
                    if piece == "P" and dest_row == self.enpassantRow + 1:
                        # White pawn capturing black pawn through en passant
                        self.boardArray[dest_row][dest_col] = piece
                        self.boardArray[self.enpassantRow][self.enpassantCol] = " "
                        self.boardArray[src_row][src_col] = " "
                    elif piece == "p" and dest_row == self.enpassantRow - 1:
                        # Black pawn capturing white pawn through en passant
                        self.boardArray[dest_row][dest_col] = piece
                        self.boardArray[self.enpassantRow][self.enpassantCol] = " "
                        self.boardArray[src_row][src_col] = " "
                    
                    # Reset en passant flag after the move is processed
                    self.enpassant = False
                    self.enpassantCol = -1
                    return

        self.boardArray[dest_row][dest_col] = piece
        self.boardArray[src_row][src_col] = " "
        if mode == "opponent":
            self.changePerspective()