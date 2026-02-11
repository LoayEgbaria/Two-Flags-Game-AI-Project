import pygame
import random
import math
import time
import threading


ZOBRIST_TABLE = {}
for row in range(8):
    for col in range(8):
        for piece in ['P', 'p']:
            ZOBRIST_TABLE[(row, col, piece)] = random.getrandbits(64)

def compute_zobrist_hash(board):
    h = 0
    for row in range(8):
        for col in range(8):
            piece = board.boardArray[row][col]           
            if piece in ['P', 'p']:
                h ^= ZOBRIST_TABLE[(row, col, piece)]
    return h
 
class UserInterface:
    def __init__(self, surface, chessboard):
        self.surface = surface
        self.chessboard = chessboard
        self.time = 0
        self.firstgame = False
        self.playercolor = None
        self.transposition_table = {}
        self.search_depth = 10
        self.max_moves = 20
        self.human = False
        self.ponder_thread = None

    def humanMove(self):
        move_input = input("Enter your move: ").strip().lower()
        if len(move_input) != 4:
            print("Invalid move format. Please try again.")
            return self.humanMove()
        move = ""
        move += str(8 - int(move_input[1]))
        move += str(ord(move_input[0]) - 97)
        move += str(8 - int(move_input[3]))
        move += str(ord(move_input[2]) - 97)
        if int(move[1]) - int(move[3]) in (2, -2):
            self.chessboard.enpassant = True
            self.chessboard.enpassantCol = int(move[0])
        self.chessboard.changePerspective()
        self.chessboard.computeMove(move, "opponent")
        self.chessboard.changePerspective()
        self.drawComponent()
        return move, 0


    def drawComponent(self): 
        self.surface.fill((255, 255, 255))  # Clear the screen with white
        square_size = self.surface.get_width() // 8
        light = (240, 217, 181)
        dark = (181, 136, 99)

        # Draw the chessboard squares
        for row in range(8):
            for col in range(8):
                pygame.event.pump()
                color = light if (row + col) % 2 == 0 else dark
                rect = pygame.Rect(col * square_size, row * square_size, square_size, square_size)
                pygame.draw.rect(self.surface, color, rect)
        
        font = pygame.font.SysFont(None, square_size // 2)
        
        # Draw the pieces
        for row in range(8):
            for col in range(8):
                piece = self.chessboard.boardArray[row][col]
                if piece != " ":
                    text = font.render(piece, True, (0, 0, 0))
                    text_rect = text.get_rect(center=(col * square_size + square_size / 2, 
                                                      row * square_size + square_size / 2))
                    self.surface.blit(text, text_rect)

        pygame.display.flip()  # Update the display

    def heuristic(self, board, color):
        own, enemy = 0, 0
        advancement_bonus = 0
        mobility = 0
        capture_bonus = 0
        center_bonus = 0
        stuck_penalty_total = 0
        stuck_penalty = 30  # penalty for each stuck pawn

        for row in range(8):
            for col in range(8):
                pygame.event.pump()
                piece = board.boardArray[row][col]
                # For White pawns:
                if piece == "P":
                    own += 1
                    # Advancement: the closer to row 0, the better.
                    advancement_bonus += (7 - row)
                    # Mobility: if the square directly ahead is empty, add mobility.
                    if row > 0 and board.boardArray[row - 1][col] == " ":
                        mobility += 1
                    # Capture potential: if diagonal squares contain an enemy pawn, add bonus.
                    if row > 0 and col > 0 and board.boardArray[row - 1][col - 1] == "p":
                        capture_bonus += 20
                    if row > 0 and col < 7 and board.boardArray[row - 1][col + 1] == "p":
                        capture_bonus += 20
                    # Center control: if in central files (columns 2 to 5)
                    if 2 <= col <= 5:
                        center_bonus += 5
                    # Stuck penalty: if the square directly ahead is occupied by an enemy pawn, subtract penalty.
                    if row > 0 and board.boardArray[row - 1][col] == "p":
                        stuck_penalty_total += stuck_penalty

                # For Black pawns:
                elif piece == "p":
                    enemy += 1
                    # Advancement: the closer to row 7, the better.
                    advancement_bonus -= row
                    if row < 7 and board.boardArray[row + 1][col] == " ":
                        mobility -= 1
                    if row < 7 and col > 0 and board.boardArray[row + 1][col - 1] == "P":
                        capture_bonus -= 20
                    if row < 7 and col < 7 and board.boardArray[row + 1][col + 1] == "P":
                        capture_bonus -= 20
                    if 2 <= col <= 5:
                        center_bonus -= 5
                    # Stuck penalty for black: if the square directly ahead is occupied by an enemy pawn, subtract penalty.
                    if row < 7 and board.boardArray[row + 1][col] == "P":
                        stuck_penalty_total += stuck_penalty

        # Material difference: each pawn difference counts 100 points.
        material_score = (own - enemy) * 100

        score = (7 * material_score) + (advancement_bonus * 5) + (mobility * 20) + (capture_bonus * 15) + center_bonus - (5 *stuck_penalty_total)

        # Return the score from the perspective of the moving color.
        return score if color == 'W' else -score



    def is_capture(self, board, move, color):
        """
        Determines if the given move is a capture move.
        """
        dest_row = int(move[2])
        dest_col = int(move[3])
        # Define the opponent piece:
        opponent = "p" if color == "W" else "P"
        return board.boardArray[dest_row][dest_col] == opponent

    def quiescence(self, board, alpha, beta, color):
        """
        Extend the search at leaf nodes by searching capture moves until a quiet position is reached.
        """
        stand_pat = self.heuristic(board, color)
        if stand_pat >= beta:
            return beta
        if stand_pat > alpha:
            alpha = stand_pat

        # Generate only capture moves
        capture_moves = [move for move in self.get_legal_moves(board, color)
                         if self.is_capture(board, move, color)]
        for move in capture_moves:
            new_board = self.clone_board(board)
            new_board.computeMove(move, 0)
            # Note the negation and switching the color (similar to negamax)
            score = -self.quiescence(new_board, -beta, -alpha, "B" if color == "W" else "W")
            if score >= beta:
                return beta
            if score > alpha:
                alpha = score
        return alpha


    def minimax(self, board, depth, alpha, beta, maximizingPlayer, color):
        key = compute_zobrist_hash(board)
        if key in self.transposition_table and self.transposition_table[key][1] >= depth:
            return self.transposition_table[key][0]
        
        winner = self.check_winner(board)
        if winner is not None:   # Terminal state- assign high pos or neg score
            if winner == color:
                return (10000 + depth, None)
            else:
                return (-10000 - depth, None)
        if depth == 0:
            return (self.quiescence(board, alpha, beta, color), None)
        
        
        legal_moves = self.get_legal_moves(board, color if maximizingPlayer
                                        else ("B" if color == "W" else "W"))
        legal_moves = self.order_moves(board, legal_moves, color, maximizingPlayer)
        # Forward pruning: restrict expansion to the top self.max_moves moves.
        legal_moves = legal_moves[:self.max_moves]

        if not legal_moves:  # No legal moves- assign loss for the side
            return (-10000 - depth, None) if maximizingPlayer else (10000 + depth, None)
        
        best_move = None
        if maximizingPlayer:
            maxEval = -math.inf
            for move in legal_moves:
                pygame.event.pump()
                new_board = self.clone_board(board)
                new_board.computeMove(move, 0)
                eval_score, _ = self.minimax(new_board, depth - 1, alpha, beta, False, color)
                if isinstance(eval_score, tuple):
                    eval_score = eval_score[0]
                if eval_score > maxEval:
                    maxEval = eval_score
                    best_move = move
                alpha = max(alpha, eval_score)
                if beta <= alpha:
                    break  # Beta cut-off
            score = maxEval
        else:
            minEval = math.inf
            for move in legal_moves:
                pygame.event.pump()
                new_board = self.clone_board(board)
                new_board.computeMove(move, 0)
                eval_score, _ = self.minimax(new_board, depth - 1, alpha, beta, True, color)
                if isinstance(eval_score, tuple):
                    eval_score = eval_score[0]                
                if eval_score < minEval:
                    minEval = eval_score
                    best_move = move
                beta = min(beta, eval_score)
                if beta <= alpha:
                    break  # Alpha cut-off
            score = minEval

        self.transposition_table[key] = ((score, best_move), depth)
        return score, best_move

    def get_legal_moves(self, board, color):
        moves = []
        d = -1 if color == 'W' else 1
        starting_row = 6 if color == 'W' else 1
        piece = 'P' if color == 'W' else 'p'
        enemy_piece = 'p' if color == 'W' else 'P'

        for row in range(8):
            for col in range(8):
                if board.boardArray[row][col] == piece:     # Forward
                    new_row = row + d
                    if 0 <= new_row < 8:
                        if board.boardArray[new_row][col] == " ":
                            move = f"{row}{col}{new_row}{col}"
                            moves.append(move)

                        for dc in [-1, 1]:      # Diag captures
                            new_col = col + dc
                            if 0 <= new_col < 8:
                                if board.boardArray[new_row][new_col] == enemy_piece:
                                    move = f"{row}{col}{new_row}{new_col}"
                                    moves.append(move)

                    if row == starting_row:    # 2 steps
                        new_row = row + 2 * d
                        mid_row = row + d
                        if 0 <= mid_row < 8 and 0 <= new_row < 8:
                            if board.boardArray[mid_row][col] == " " and board.boardArray[new_row][col] == " ":
                                move = f"{row}{col}{new_row}{col}"
                                moves.append(move)
        return moves

    def clone_board(self, board):
        new_board = type(board)()
        new_board.boardArray = [row[:] for row in board.boardArray]
        new_board.enpassant = board.enpassant
        new_board.enpassantCol = board.enpassantCol
        new_board.round = board.round
        return new_board

    def check_winner(self, board):
        "checks if one color reached the end or there are no enemy pawns left"
        for col in range(8):
            if board.boardArray[0][col] == 'P':
                return 'W'
            if board.boardArray[7][col] == 'p':
                return 'B'
        
        white_count = sum(row.count('P') for row in board.boardArray)
        black_count = sum(row.count('p') for row in board.boardArray)
        if white_count == 0:
            return 'B'
        if black_count == 0:
            return 'W'
        
        if not self.get_legal_moves(board, 'W'):
            return 'B'
        if not self.get_legal_moves(board, 'B'):
            return 'W'
        
        return None
        

    def iterative_deepening(self, board, color, max_depth, time_limit):
        "Using iterative deepening with time and depth limits to search for best moves"
        best_move = None
        start_time = time.time()
        for depth in range(1, max_depth + 1):
            pygame.event.pump()
            if time.time() - start_time > time_limit:
                print("Time limit reached at depth", depth)
                break
            score, move = self.minimax(board, depth, -math.inf, math.inf, True, color)
            if move is not None:
                best_move = move
            print(f"Depth {depth} complete, best move so far: {best_move}, score: {score}")
        return best_move

    def order_moves(self, board, moves, color, maximizing):
        scored_moves = []
        for move in moves:
            new_board = self.clone_board(board)
            new_board.computeMove(move, 0)
            score = self.heuristic(new_board, color)
            scored_moves.append((score, move))
        scored_moves.sort(key=lambda x: x[0], reverse=maximizing)
        return [m for score, m in scored_moves]


    def clientMove(self):
        if self.human:
            return self.humanMove()
        else:
            best_move = None
            # If a pondering thread is running, stop it and get its best move.
            if self.ponder_thread is not None:
                self.ponder_thread.stop()
                self.ponder_thread.join()
                pondered_move = self.ponder_thread.best_move
                self.ponder_thread = None
                # First, check that the pondered move is legal.
                legal_moves = self.get_legal_moves(self.chessboard, self.playercolor)
                if pondered_move in legal_moves:
                    # Evaluate the pondered move on a clone of the current board.
                    board_clone = self.clone_board(self.chessboard)
                    board_clone.computeMove(pondered_move, self.playercolor)
                    pondered_eval = self.heuristic(board_clone, self.playercolor)
                    
                    # Run a shallow iterative deepening search on the current board.
                    candidate_move = self.iterative_deepening(self.chessboard, self.playercolor, max_depth=5, time_limit=2)
                    if candidate_move is not None:
                        candidate_clone = self.clone_board(self.chessboard)
                        candidate_clone.computeMove(candidate_move, self.playercolor)
                        candidate_eval = self.heuristic(candidate_clone, self.playercolor)
                        # Define a threshold delta.
                        delta = 20  
                        if candidate_eval > pondered_eval + delta:
                            best_move = candidate_move
                        else:
                            best_move = pondered_move
                    else:
                        best_move = pondered_move
            
            # If no valid pondered move was found, run iterative deepening on the current board.
            if best_move is None:
                max_depth = 10
                time_limit = self.time / 40     # Assuming every game will end in maximum 40 moves
                best_move = self.iterative_deepening(self.chessboard, self.playercolor, max_depth, time_limit)
            
            if best_move is None:
                return ("exit", -1)
            
            # Apply the chosen move and update the board.
            self.chessboard.computeMove(best_move, self.playercolor)
            self.drawComponent()
            return (best_move, 0)


        

class PonderThread(threading.Thread):
    def __init__(self, ui, board, color, max_depth=10, time_limit=10):
        threading.Thread.__init__(self)
        self.ui = ui
        # Make a clone of the board state so that pondering isn’t affected by changes.
        self.board = ui.clone_board(board)
        self.color = color
        self.max_depth = max_depth
        self.time_limit = time_limit
        self.best_move = None
        self.running = True

    def run(self):
        start_time = time.time()
        for depth in range(1, self.max_depth + 1):
            if not self.running or (time.time() - start_time) > self.time_limit:
                break
            score, move = self.ui.minimax(self.board, depth, -math.inf, math.inf, True, self.color)
            if move is not None:
                self.best_move = move

    def stop(self):
        self.running = False

