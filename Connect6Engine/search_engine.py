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

        # Initialize evaluation scores and weights
        weights = {1: 10, 2: 100, 3: 1000, 4: 10000, 5: 100000}
        my_score = 0
        opp_score = 0
        # define color
        our_stone = color
        opp_stone = Defines.BLACK if color == Defines.WHITE else Defines.WHITE

        # Loop through inside spaces (no edges)
        for i in range(1, len(board) - 1):
            for j in range(1, len(board[i]) - 1):
                # If no stone skip
                if board[i][j] == Defines.NOSTONE:
                    continue
                # Check stone color
                if board[i][j] == our_stone:
                    # Find longest line for our color
                    chain_length = longest_line(board, i, j, our_stone)
                    if chain_length in weights:
                        my_score += weights[chain_length]
                elif board[i][j] == opp_stone:
                    # Find longest line for opponent color
                    chain_length = longest_line(board, i, j, opp_stone)
                    if chain_length in weights:
                        opp_score += weights[chain_length] 
        return my_score - opp_score
   
       
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
    

    ## POSSIBLE MOVES (Improved next moves - Subset of 6)
    def possible_moves(self, board, color, limit=6):

        # CHECK IF FIRST MOVE
        if self.check_first_move():
            center = (9, 9)
            return [((center), None)]
        
        # define color
        our_stone = color
        opp_stone = Defines.BLACK if color == Defines.WHITE else Defines.WHITE

        # Initialize scored moves list
        scored = []

        # For each empty position
        for i in range(1, len(board) - 1):
            for j in range(1, len(board[i]) - 1):
                if board[i][j] == Defines.NOSTONE:
                    # Find longest line for both players
                    my_chain = longest_line(board, i, j, our_stone)
                    opp_chain = longest_line(board, i, j, opp_stone)
                    # Score is the max of both
                    score = max(my_chain, opp_chain)
                    # Append to scored list
                    scored.append(((i, j), score))

        # Sort by score descending
        scored.sort(key=lambda x: x[1], reverse=True)
        # Select top max moves
        candidates = [pos for pos, score in scored[:limit]]                 

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
        candidate_pairs = self.possible_moves(board, color)
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
        
    # Include two new parameters alpha and beta
    def alphabeta(self, board, depth, alpha, beta, color, maxi_player):
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
        candidate_pairs = self.possible_moves(board, color)
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
                
                # NEXT MOVE - Update to include alpha and beta
                value, _ = self.alphabeta(board_copy, depth - 1, alpha, beta, next_color, maxi_player=False)

                # STORE BEST VALUE
                if value > best_value:
                    best_move = (move1, move2)
                    best_value = value

                # Update alpha then prune if necessary
                alpha = max(alpha, best_value)
                if alpha >= beta:
                    break
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

                # NEXT MOVE - Update to include alpha and beta
                value, _ = self.alphabeta(board_copy, depth - 1, alpha, beta, next_color, maxi_player=True)

                # STORE BEST VALUE
                if value < best_value:
                    best_move = (move1, move2)
                    best_value = value

                # Update beta and prune if necessary
                beta = min(beta, best_value)
                if alpha >= beta:
                    break
            return best_value, best_move
        
def flush_output():
    import sys
    sys.stdout.flush()
