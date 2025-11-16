from tools import *
import random

class SearchEngine():
    def __init__(self):
        self.m_board = None
        self.m_chess_type = None
        self.m_alphabeta_depth = None
        self.m_total_nodes = 0
        # Initialize weights
        self.weight_ch = 1.0
        self.weight_dir = 0.1
        self.weight_def = 200

        # Initialize Transposition table and Zobrist table
        self.TT = {}
        self.z_table = {}
        for x in range(Defines.GRID_NUM):
            for y in range(Defines.GRID_NUM):
                self.z_table[(x, y, Defines.BLACK)] = random.getrandbits(64)
                self.z_table[(x, y, Defines.WHITE)] = random.getrandbits(64)

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
            # else:
            #     return Defines.MININT
            
        if is_draw(board):
            return 0

        # Initialize evaluation scores and weights
        weights = {1: 10, 2: 100, 3: 1000, 4: 10000, 5: 100000}
        my_score = 0
        opp_score = 0
        my_dir_score = 0
        opp_dir_score = 0

        # define color
        our_stone = color
        opp_stone = Defines.BLACK if color == Defines.WHITE else Defines.WHITE

        # Counters for chains
        my_chains = {1: 0, 2: 0, 3: 0, 4: 0, 5: 0}
        opp_chains = {1: 0, 2: 0, 3: 0, 4: 0, 5: 0}

        # Loop through inside spaces (no edges)
        for i in range(1, len(board) - 1):
            for j in range(1, len(board[i]) - 1):
                # If no stone skip
                if board[i][j] == Defines.NOSTONE:
                    # Half move evaluation (Liu)
                    my_dir_score += half_move_evaluation(board, i, j, our_stone)
                    opp_dir_score += half_move_evaluation(board, i, j, opp_stone)
                    continue
                # Check stone color
                if board[i][j] == our_stone:
                    # Find longest line for our color
                    chain_length = longest_line(board, i, j, our_stone)
                    if chain_length > 5:
                        chain_length = 5
                    my_chains[chain_length] += 1

                elif board[i][j] == opp_stone:
                    # Find longest line for opponent color
                    chain_length = longest_line(board, i, j, opp_stone)
                    if chain_length > 5:
                        chain_length = 5
                    opp_chains[chain_length] += 1

        
        # Calculating weighted score
        my_score = sum(weights[c] * my_chains[c] for c in my_chains)
        opp_score = sum(weights[c] * opp_chains[c] for c in opp_chains)

        # Defensive threat score - Stones needed to defend
        stones_required = 0
        for chain, open_ends in find_live_threats(board, opp_stone):
            stones_required += open_ends

        # Change weights to allow for dynamic adaptation
        weight_chain = self.weight_ch
        weight_direction = self.weight_dir
        weight_defensive = self.weight_def

        # Final evaluation score
        evaluation_score = (weight_chain*(my_score - opp_score)
                            + weight_direction*(my_dir_score - opp_dir_score)
                            - weight_defensive*stones_required
        )
        return evaluation_score
   
       
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
            center = (10, 10)
            return [((center, center))]

        # define color
        our_stone = color
        opp_stone = Defines.BLACK if color == Defines.WHITE else Defines.WHITE

        # immediate threat
        # Use neighbor-based region instead of full board
        empty_cells = set()
        for x in range(1, len(board)-1):
            for y in range(1, len(board)-1):
                if board[x][y] != Defines.NOSTONE:
                    for dx in range(-1,2):
                        for dy in range(-1,2):
                            nx, ny = x+dx, y+dy
                            if isValidPos(nx,ny) and board[nx][ny] == Defines.NOSTONE:
                                empty_cells.add((nx,ny))

        empty_cells = list(empty_cells)

        opponent_forced_win_points = set()

        # check if opponent has any 2-stone forced win
        for i in range(len(empty_cells)):
            for j in range(i+1, len(empty_cells)):
                (x1, y1) = empty_cells[i]
                (x2, y2) = empty_cells[j]

                # simulate opponent placing two stones
                board[x1][y1] = opp_stone
                board[x2][y2] = opp_stone

                mv = StoneMove()
                mv.positions[0].x, mv.positions[0].y = x1, y1
                mv.positions[1].x, mv.positions[1].y = x2, y2

                if is_win_by_premove(board, mv):
                    opponent_forced_win_points.add((x1, y1))
                    opponent_forced_win_points.add((x2, y2))

                # undo
                board[x1][y1] = Defines.NOSTONE
                board[x2][y2] = Defines.NOSTONE

        # check if we have any 2-stone instant win
        for i in range(len(empty_cells)):
            for j in range(i+1, len(empty_cells)):
                (x1, y1) = empty_cells[i]
                (x2, y2) = empty_cells[j]

                # simulate
                board[x1][y1] = our_stone
                board[x2][y2] = our_stone

                mv = StoneMove()
                mv.positions[0].x, mv.positions[0].y = x1, y1
                mv.positions[1].x, mv.positions[1].y = x2, y2

                if is_win_by_premove(board, mv):
                    board[x1][y1] = board[x2][y2] = Defines.NOSTONE
                    return [((x1, y1), (x2, y2))]

                board[x1][y1] = board[x2][y2] = Defines.NOSTONE

        # after weve checked all pairs, handle opponent forced wins
        if len(opponent_forced_win_points) >= 2:
            threats = list(opponent_forced_win_points)
            defensive_pairs = []
            for i in range(len(threats)):
                for j in range(i+1, len(threats)):
                    defensive_pairs.append((threats[i], threats[j]))
            return defensive_pairs[:limit]

        # One threat block it with one stone + another anywhere
        if len(opponent_forced_win_points) == 1:
            t = list(opponent_forced_win_points)[0]  # the must-block coordinate

            # pair it with any empty cell
            for x2, y2 in empty_cells:
                if (x2, y2) != t:
                    return [(t, (x2, y2))]

            # fallback
            return [(t, t)]

        # ADD neighbour pruning
        neighbour_moves = set(empty_cells)  

        # fallback early in game
        if not neighbour_moves:
            neighbour_moves = {(10, 10)}

        # Initialize our defensive moves list
        critical_threats = []
        # Initialize scored moves list
        scored = []

        # For each empty position
        for (i, j) in neighbour_moves:
            # simulate 1 stone placement for both players
            board[i][j] = our_stone
            my_chain = longest_line(board, i, j, our_stone)
            board[i][j] = Defines.NOSTONE

            board[i][j] = opp_stone
            opp_chain = longest_line(board, i, j, opp_stone)
            board[i][j] = Defines.NOSTONE

            # Pre-score instant win check
            if my_chain >= 6:
                return [((i, j), (i, j))]

            # Pre-score instant loss check (collect if more than one)
            if opp_chain >= 6:
                critical_threats.append(((i, j), (i, j)))
                continue

            # Priority scoring system based on potential
            score = my_chain * 10 + opp_chain * 5
            # Ensuring moves that create chains of 4+ are prioritized
            if my_chain >= 4:
                score += 50

            scored.append(((i, j), score))

        # If there exists critical list use this for candidate pairs
        if critical_threats:
            return critical_threats[:limit]

        # Sort by score descending
        scored.sort(key=lambda x: x[1], reverse=True)
        # Select top max moves
        candidates = [pos for pos, score in scored[:limit]]

        # check if any pair of moves is an instant win
        for a in candidates:
            for b in candidates:
                if a == b:
                    continue

                # simulate pair
                ax, ay = a
                bx, by = b
                board[ax][ay] = our_stone
                board[bx][by] = our_stone

                # use StoneMove for checking win
                mv = StoneMove()
                mv.positions[0].x, mv.positions[0].y = ax, ay
                mv.positions[1].x, mv.positions[1].y = bx, by

                if is_win_by_premove(board, mv):
                    # undo simulation before returning
                    board[ax][ay] = board[bx][by] = Defines.NOSTONE
                    return [(a, b)]

                # undo simulation
                board[ax][ay] = board[bx][by] = Defines.NOSTONE

        candidate_pairs = []
        for i in range(len(candidates)):
            for j in range(i+1, len(candidates)):
                x1, y1 = candidates[i]
                x2, y2 = candidates[j]
                # check:
                if board[x1][y1] == Defines.NOSTONE and board[x2][y2] == Defines.NOSTONE and (x1, y1) != (x2, y2):
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

                if depth <= 0:
                    return self.evaluate_position(board_copy, color, dummy_move), None

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

        # Zobrist Hash lookup
        zob = self.compute_hash(board, color)
        if zob in self.TT:
            stored_depth, stored_value, stored_move = self.TT[zob]
            if stored_depth >= depth:
                return stored_value, stored_move
    
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

                if is_win_by_premove(board_copy, dummy_move):
                    return self.evaluate_position(board_copy, color, dummy_move), (move1, move2)               
                
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
                    # store before pruning
                    self.TT[zob] = (depth, best_value, best_move)
                    break

            self.TT[zob] = (depth, best_value, best_move)
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

                if is_win_by_premove(board_copy, dummy_move):
                    return self.evaluate_position(board_copy, color, dummy_move), (move1, move2)
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
                    # store before pruning
                    self.TT[zob] = (depth, best_value, best_move)
                    break
            self.TT[zob] = (depth, best_value, best_move)
            return best_value, best_move
    
    def compute_hash(self, board, color):
        h = 0
        for x in range(1, Defines.GRID_NUM - 1):
            for y in range(1, Defines.GRID_NUM - 1):
                c = board[x][y]
                if c == Defines.BLACK or c == Defines.WHITE:
                    h ^= self.z_table[(x, y, c)]
        h ^= (color * 1315423911)
        return h

def flush_output():
    import sys
    sys.stdout.flush()