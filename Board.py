# Created and Developed by : Loay Egbaria

# ChessBoard class to represent the game board and handle moves
# The board is represented as an 8x8 array, with "P" for white pawns, "p" for black pawns, and " " for empty squares.


class ChessBoard:
    def __init__(self):
        self.boardArray = [[" " for _ in range(8)] for _ in range(8)] # creating 8x8 empty board
        self.boardArray[1] = ["p"] * 8   # black pawns starting row
        self.boardArray[6] = ["P"] * 8   # white pawns starting row
        self.enpassant = False  # flag to know if en passant is available
        self.enpassantCol = -1  # column of pawn that can be captured en passant
        self.round = 0  # round counter (game progress)

    def changePerspective(self):
        self.boardArray = self.boardArray[::-1]    # flip the board (used when opponent plays)

    def computeMove(self, move, mode):
        if len(move) != 4:
            print("Invalid move")
            return

        try:
            if mode == "opponent":
                self.changePerspective()  # look at board from opponent side

            src_row = int(move[0])
            src_col = int(move[1])
            dest_row = int(move[2])
            dest_col = int(move[3])
        
        except ValueError:
            print("Invalid digits")
            return
        
        piece = self.boardArray[src_row][src_col]  # the pawn we are moving

        if self.enpassant:
            if abs(src_col - dest_col) == 1 and abs(src_row - dest_row) >= 1:
                # pawn moved diagonally (possible capture)
                if self.boardArray[dest_row][dest_col] == " ":
                    # destination empty → possible en passant
                    if piece == "P" and dest_row == self.enpassantRow + 1:
                        # white captures black en passant
                        self.boardArray[dest_row][dest_col] = piece
                        self.boardArray[self.enpassantRow][self.enpassantCol] = " "
                        self.boardArray[src_row][src_col] = " "
                    elif piece == "p" and dest_row == self.enpassantRow - 1:
                        # black captures white en passant
                        self.boardArray[dest_row][dest_col] = piece
                        self.boardArray[self.enpassantRow][self.enpassantCol] = " "
                        self.boardArray[src_row][src_col] = " "
                    
                    # after en passant move we reset the flag
                    self.enpassant = False
                    self.enpassantCol = -1
                    return

        # regular move or capture
        self.boardArray[dest_row][dest_col] = piece
        self.boardArray[src_row][src_col] = " "

        if mode == "opponent":
            self.changePerspective()  # flip back to original view
