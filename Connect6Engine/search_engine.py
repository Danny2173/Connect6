from tools import *

class SearchEngine():
    def __init__(self):
        self.m_board = None
        self.m_chess_type = None
        self.m_alphabeta_depth = None
        self.m_total_nodes = 0

    def before_search(self, board, color, alphabeta_depth):
        self.m_board = [row[:] for row in board]
        self.m_chess_type = color
        self.m_alphabeta_depth = alphabeta_depth
        self.m_total_nodes = 0

    def evaluate_position(self, board, color, bestMove):
        #Check game result
        if is_win_by_premove(board, bestMove):
            if color == self.m_chess_type:
                return Defines.MAXINT
            else:
                return Defines.MININT
            
        if is_draw(board):
            return 0

        # Initialize evaluation scores
        my_open = 0
        opp_open = 0

        # Loop through inside spaces (no edges)
        for i in range(1, len(board) - 1):
            for j in range(1, len(board[i]) - 1):
                value = board[i][j]
                # If no stone skip
                if value == Defines.NOSTONE:
                    continue
                
                # List neighbors
                neighbors = [
                    board[i+1][j],
                    board[i-1][j],
                    board[i][j+1],
                    board[i][j-1],
                    board[i+1][j+1],
                    board[i-1][j-1],
                    board[i+1][j-1],
                    board[i-1][j+1],
                ]

                # If any neighbor has no stone then add point
                if any(n == Defines.NOSTONE for n in neighbors):
                    if value == self.m_chess_type:
                        my_open += 1
                    else:
                        opp_open += 1
        return my_open - opp_open
        # color_name = "Black" if self.m_chess_type == Defines.BLACK else "White"
        # if my_open > opp_open:
        #     return f"Engine winning! - {color_name} score: {my_open} | opponent score: {opp_open}"
        # elif opp_open > my_open:
        #     return f"Opponent winning! - {color_name} score: {my_open} | opponent score: {opp_open}"
        # else:
        #     return f"{color_name} score: {my_open} | opponent score: {opp_open}"
    
   
    def alpha_beta_search(self, depth, alpha, beta, ourColor, bestMove, preMove):
    
        #Check game result
        if (is_win_by_premove(self.m_board, preMove)):
            if (ourColor == self.m_chess_type):
                #Opponent wins.
                return Defines.MININT
            else:
                #Self wins.
                return Defines.MAXINT
        # DRAW CHECK
        if is_draw(self.m_board):
            return 0
        
        alpha = 0
        if(self.check_first_move()):
            bestMove.positions[0].x = 10
            bestMove.positions[0].y = 10
            bestMove.positions[1].x = 10
            bestMove.positions[1].y = 10
        else:
            
            pairs = self.possible_moves()
            if not pairs:
                return 0
            move1, move2 = pairs[0]
            bestMove.positions[0].x = move1[0]
            bestMove.positions[0].y = move1[1]
            bestMove.positions[1].x = move1[0]
            bestMove.positions[1].y = move1[1]
            make_move(self.m_board,bestMove,ourColor)
            
            if is_win_by_premove(self.m_board, bestMove):
                # Self wins — return a high score
                return +1
            
            bestMove.positions[1].x = move2[0]
            bestMove.positions[1].y = move2[1]
            make_move(self.m_board,bestMove,ourColor)

        score = self.evaluate_position(self.m_board, ourColor, bestMove)
        return score
        
    def check_first_move(self):
        for i in range(1,len(self.m_board)-1):
            for j in range(1, len(self.m_board[i])-1):
                if(self.m_board[i][j] != Defines.NOSTONE):
                    return False
        return True
        
    def find_possible_move(self):
        for i in range(1,len(self.m_board)-1):
            for j in range(1, len(self.m_board[i])-1):
                if(self.m_board[i][j] == Defines.NOSTONE):
                    return (i,j)
        return (-1,-1)
    
    ## POSSIBLE MOVES (NAIVE - Subset of 30)
    def possible_moves(self, board, max=2):
        # List of empty cells
        empty_list = []
        for i, row in enumerate(board):
            for j, value in enumerate(row):
                if value == Defines.NOSTONE:
                    empty_list.append((i,j))

        # CHECK IF FIRST MOVE
        if self.check_first_move():
            center = (9, 9)
            return [((center), None)]
        # Select subset
        candidates = empty_list[:max]

        # Create move pairs
        candidate_pairs = []
        for i in range(len(candidates)):
            for j in range(i+1, len(candidates)):
                candidate_pairs.append((candidates[i], candidates[j]))
        return candidate_pairs

    # MIN-MAX ALGO
    def min_max(self, board, depth, color, maxi_player):
        # Check game result
        if (is_win_by_premove(board, StoneMove())):
            return self.evaluate_position(board, color, StoneMove()), None
        # DRAW CHECK
        if is_draw(board):
            return self.evaluate_position(board, color, StoneMove()), None
        # Max depth reached
        if depth <= 0:
            return self.evaluate_position(board, color, StoneMove()), None
        
        # CANDIDATE PAIRS 
        candidate_pairs = self.possible_moves(board)
        if not candidate_pairs:
            return self.evaluate_position(board, color, StoneMove()), None

        # FOR MAXIMISING PLAYER
        if maxi_player:
            best_move = None
            best_value = Defines.MININT
            for move1, move2 in candidate_pairs:
                # COPY BOARD
                board_copy = [row[:] for row in board]

                # CREATE DUMMY MOVES
                dummy_move = StoneMove()
                dummy_move.positions[0].x, dummy_move.positions[0].y = move1
                if move2 is not None:
                    dummy_move.positions[1].x, dummy_move.positions[1].y = move2
                else:
                    # IF FIRST MOVE
                    dummy_move.positions[1].x, dummy_move.positions[1].y = -1, -1

                # MAKE MOVE
                make_move(board_copy,dummy_move, color)

                # SWITCH COLOR
                if color == Defines.BLACK:
                    next_color = Defines.WHITE
                else: 
                    next_color = Defines.BLACK
                
                # NEXT MOVE
                value, _ = self.min_max(board_copy, depth - 1, next_color, maxi_player=False)

                # STORE BEST VALUE
                if value > best_value:
                    best_move = (move1, move2)
                    best_value = value
            return best_value, best_move
        
        # FOR MINIMIZING PLAYER
        else:
            best_move = None
            best_value = Defines.MAXINT
            for move1, move2 in candidate_pairs:
                # COPY BOARD
                board_copy = [row[:] for row in board]

                # CREATE DUMMY MOVES
                dummy_move = StoneMove()
                dummy_move.positions[0].x, dummy_move.positions[0].y = move1
                if move2 is not None:
                    dummy_move.positions[1].x, dummy_move.positions[1].y = move2
                else:
                    # IF FIRST MOVE
                    dummy_move.positions[1].x, dummy_move.positions[1].y = -1, -1

                # MAKE MOVE
                make_move(board_copy,dummy_move, color)

                # SWITCH COLOR
                if color == Defines.BLACK:
                    next_color = Defines.WHITE
                else: 
                    next_color = Defines.BLACK

                # NEXT MOVE
                value, _ = self.min_max(board_copy, depth - 1, next_color, maxi_player=True)

                # STORE BEST VALUE
                if value < best_value:
                    best_move = (move1, move2)
                    best_value = value
            
            return best_value, best_move
        

def flush_output():
    import sys
    sys.stdout.flush()
