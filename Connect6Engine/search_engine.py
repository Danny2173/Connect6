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
        # 1. Terminal check first (same as before)
        if is_win_by_premove(board, bestMove):
            if color == self.m_chess_type:
                return Defines.MAXINT
            else:
                return Defines.MININT

        if is_draw(board):
            return 0

        # ---------- PARAMETERS / WEIGHTS ----------
        chain_weights = {
            1: 5,
            2: 30,
            3: 150,
            4: 1000,
            5: 20000
        }

        MOBILITY_WEIGHT = 0.5
        DEFENSE_WEIGHT = 15

        my_chain_score = 0
        opp_chain_score = 0
        mobility_score = 0.0

        our_stone = color
        opp_stone = Defines.BLACK if color == Defines.WHITE else Defines.WHITE

        rows = len(board)
        cols = len(board[0]) if rows > 0 else 0

        # ---------- MAIN BOARD LOOP ----------
        for i in range(1, rows - 1):
            for j in range(1, cols - 1):

                cell = board[i][j]

                # Empty → half-move mobility
                if cell == Defines.NOSTONE:
                    my_dir = half_move_evaluation(board, i, j, our_stone)
                    opp_dir = half_move_evaluation(board, i, j, opp_stone)
                    mobility_score += (my_dir - opp_dir)
                    continue

                # Stones
                if cell == our_stone:
                    chain_len = min(longest_line(board, i, j, our_stone), 5)
                    if chain_len >= 1:
                        my_chain_score += chain_weights.get(chain_len, 0)

                elif cell == opp_stone:
                    chain_len = min(longest_line(board, i, j, opp_stone), 5)
                    if chain_len >= 1:
                        opp_chain_score += chain_weights.get(chain_len, 0)

        # ---------- THREAT EVALUATION (SAFE) ----------
        max_threat_value = 0.0

        threat_list = find_live_threats(board, opp_stone)

        if isinstance(threat_list, list):
            for item in threat_list:
                # Ensure it is a 2-item tuple/list of ints
                if (isinstance(item, (list, tuple)) 
                        and len(item) == 2):

                    try:
                        chain = int(item[0])
                        open_ends = int(item[1])
                        threat_value = chain * open_ends
                        if threat_value > max_threat_value:
                            max_threat_value = threat_value
                    except:
                        # malformed entry, skip
                        continue

        threat_penalty = DEFENSE_WEIGHT * max_threat_value

        # ---------- FINAL SCORE ----------
        base_score = my_chain_score - opp_chain_score
        mobility_component = MOBILITY_WEIGHT * mobility_score

        final_score = base_score + mobility_component - threat_penalty
        return final_score


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
    

    #     ## POSSIBLE MOVES (Improved next moves - Subset of 6)
    # def possible_moves(self, board, color, limit=8):
    #     """
    #     Stronger generator:
    #     1. Always include critical defensive blocks
    #     2. Always include immediate winning moves
    #     3. Then add top-scoring candidates
    #     """

    #     # First move → special rule
    #     if self.check_first_move():
    #         return [((9, 9), None)]

    #     our_stone = color
    #     opp_stone = Defines.BLACK if color == Defines.WHITE else Defines.WHITE

    #     winning_moves = []
    #     defensive_moves = []
    #     scored = []

    #     # Scan whole board
    #     for i in range(1, len(board)-1):
    #         for j in range(1, len(board[i])-1):
    #             if board[i][j] != Defines.NOSTONE:
    #                 continue

    #             # check our potential
    #             my_chain = longest_line(board, i, j, our_stone)
    #             if my_chain >= 5:
    #                 # we can win instantly
    #                 winning_moves.append(((i, j), None))
    #                 continue

    #             # check opponent threats
    #             opp_chain = longest_line(board, i, j, opp_stone)
    #             if opp_chain >= 5:
    #                 # opponent is threatening win; must block
    #                 defensive_moves.append(((i, j), None))
    #                 continue

    #             # scoring
    #             score = (my_chain * 12) + (opp_chain * 20)
    #             # give more priority to defense (opp threats)
    #             if opp_chain >= 4:
    #                 score += 200
    #             if my_chain >= 4:
    #                 score += 80

    #             scored.append(((i, j), score))

    #     # If we can win, return only winning moves
    #     if winning_moves:
    #         return winning_moves[:limit]

    #     # If opponent can win, return only defensive moves
    #     if defensive_moves:
    #         return defensive_moves[:limit]

    #     # sort candidates
    #     scored.sort(key=lambda x: x[1], reverse=True)
    #     top = [pos for pos, _ in scored[:limit]]

    #     # generate pairs
    #     pairs = []
    #     for a in range(len(top)):
    #         for b in range(a+1, len(top)):
    #             pairs.append((top[a], top[b]))

    #     if not pairs:
    #         # fallback single
    #         return [(top[0], None)]

    #     return pairs

    def possible_moves(self, board, color, limit=6):
        """
        Fast + safe move generator:
        - Only consider empty cells near existing stones (radius=2)
        - Prioritize immediate wins and forced defenses
        - Hard cap to 'limit' moves so alpha-beta never explodes
        - Always returns list of (pos1, pos2) pairs OR [(pos, None)]
        """

        # First move
        if self.check_first_move():
            return [((9, 9), None)]

        our = color
        opp = Defines.BLACK if color == Defines.WHITE else Defines.WHITE

        rows = len(board)

        # --- STEP 1: find all existing stones ---
        stones = []
        for i in range(1, rows - 1):
            for j in range(1, rows - 1):
                if board[i][j] != Defines.NOSTONE:
                    stones.append((i, j))

        if not stones:
            return [((9, 9), None)]

        # --- STEP 2: generate candidates near stones (radius=2) ---
        candidates = set()
        for (sx, sy) in stones:
            for dx in range(-2, 3):
                for dy in range(-2, 3):
                    x, y = sx + dx, sy + dy
                    if 1 <= x < rows - 1 and 1 <= y < rows - 1:
                        if board[x][y] == Defines.NOSTONE:
                            candidates.add((x, y))

        candidates = list(candidates)

        winning = []
        defending = []
        scored = []

        # --- STEP 3: classify candidates ---
        for (i, j) in candidates:

            myL = longest_line(board, i, j, our)
            if myL >= 5:
                winning.append(((i, j), None))
                continue

            oppL = longest_line(board, i, j, opp)
            if oppL >= 5:
                defending.append(((i, j), None))
                continue

            score = myL * 12 + oppL * 20
            if oppL >= 4:
                score += 200
            if myL >= 4:
                score += 80

            scored.append(((i, j), score))

        # --- STEP 4: forced wins take priority ---
        if winning:
            return winning[:limit]

        # --- STEP 5: forced defenses next ---
        if defending:
            return defending[:limit]

        # --- STEP 6: best heuristic moves ---
        scored.sort(key=lambda x: x[1], reverse=True)
        top = [pos for pos, _ in scored[:limit]]

        # --- STEP 7: generate pairs ---
        pairs = []
        for a in range(len(top)):
            for b in range(a + 1, len(top)):
                pairs.append((top[a], top[b]))

        if not pairs:
            return [(top[0], None)]

        return pairs


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
                board_copy = [row[:] for row in board]

                dummy_move = StoneMove()
                dummy_move.positions[0].x, dummy_move.positions[0].y = move1
                if move2 is not None:
                    dummy_move.positions[1].x, dummy_move.positions[1].y = move2
                else:
                    dummy_move.positions[1].x, dummy_move.positions[1].y = -1, -1

                make_move(board_copy,dummy_move, color)

                if color == Defines.BLACK:
                    next_color = Defines.WHITE
                else: 
                    next_color = Defines.BLACK
                
                value, _ = self.min_max(board_copy, depth - 1, next_color, maxi_player=False)

                if value > best_value:
                    best_move = (move1, move2)
                    best_value = value
            return best_value, best_move
        
        # FOR MINIMIZING PLAYER
        else:
            best_move = None
            best_value = Defines.MAXINT
            for move1, move2 in candidate_pairs:
                board_copy = [row[:] for row in board]

                dummy_move = StoneMove()
                dummy_move.positions[0].x, dummy_move.positions[0].y = move1
                if move2 is not None:
                    dummy_move.positions[1].x, dummy_move.positions[1].y = move2
                else:
                    dummy_move.positions[1].x, dummy_move.positions[1].y = -1, -1

                make_move(board_copy,dummy_move, color)

                if color == Defines.BLACK:
                    next_color = Defines.WHITE
                else: 
                    next_color = Defines.BLACK

                value, _ = self.min_max(board_copy, depth - 1, next_color, maxi_player=True)

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

        # FIX: possible_moves returning None
        if not candidate_pairs or candidate_pairs is None:
            p1 = self.find_possible_move()
            p2 = self.find_possible_move()
            if p1 == p2:
                p2 = (-1, -1)
            return self.evaluate_position(board, color, StoneMove()), (p1, p2)

        # FOR MAXIMISING PLAYER
        if maxi_player:
            best_move = None
            best_value = Defines.MININT
            for move1, move2 in candidate_pairs:
                board_copy = [row[:] for row in board]

                dummy_move = StoneMove()
                dummy_move.positions[0].x, dummy_move.positions[0].y = move1
                if move2 is not None:
                    dummy_move.positions[1].x, dummy_move.positions[1].y = move2
                else:
                    dummy_move.positions[1].x, dummy_move.positions[1].y = -1, -1

                make_move(board_copy,dummy_move, color)

                if color == Defines.BLACK:
                    next_color = Defines.WHITE
                else: 
                    next_color = Defines.BLACK
                
                value, _ = self.alphabeta(board_copy, depth - 1, alpha, beta, next_color, maxi_player=False)

                if value > best_value:
                    best_move = (move1, move2)
                    best_value = value

                alpha = max(alpha, best_value)
                if alpha >= beta:
                    break

            if not candidate_pairs:
                fallback = self.ensure_two_moves(None)
                return self.evaluate_position(board, color, StoneMove()), fallback

            return best_value, self.ensure_two_moves(best_move)
        
        # FOR MINIMIZING PLAYER
        else:
            best_move = None
            best_value = Defines.MAXINT
            for move1, move2 in candidate_pairs:
                board_copy = [row[:] for row in board]

                dummy_move = StoneMove()
                dummy_move.positions[0].x, dummy_move.positions[0].y = move1
                if move2 is not None:
                    dummy_move.positions[1].x, dummy_move.positions[1].y = move2
                else:
                    dummy_move.positions[1].x, dummy_move.positions[1].y = -1, -1

                make_move(board_copy,dummy_move, color)

                if color == Defines.BLACK:
                    next_color = Defines.WHITE
                else: 
                    next_color = Defines.BLACK

                value, _ = self.alphabeta(board_copy, depth - 1, alpha, beta, next_color, maxi_player=True)

                if value < best_value:
                    best_move = (move1, move2)
                    best_value = value

                beta = min(beta, best_value)
                if alpha >= beta:
                    break
            
            if not candidate_pairs:
                fallback = self.ensure_two_moves(None)
                return self.evaluate_position(board, color, StoneMove()), fallback

            return best_value, self.ensure_two_moves(best_move)
        
    def ensure_two_moves(self, move_pair):
        """Ensure returned move has two valid, distinct positions."""

        # If no move found → return ANY legal 2-stone move
        if move_pair is None:
            p1 = self.find_possible_move()
            p2 = self.find_second_empty(p1)
            return (p1, p2)

        (m1, m2) = move_pair

        # If m1 is None → fallback
        if m1 is None:
            p1 = self.find_possible_move()
            p2 = self.find_second_empty(p1)
            return (p1, p2)

        # If m2 is None → pick second empty
        if m2 is None:
            m2 = self.find_second_empty(m1)

        # If both are same → pick a new second
        if m1 == m2:
            m2 = self.find_second_empty(m1)

        return (m1, m2)

    def find_second_empty(self, avoid):
        ax, ay = avoid
        for i in range(1, 19):
            for j in range(1, 19):
                if (i, j) != avoid and self.m_board[i][j] == Defines.NOSTONE:
                    return (i, j)
        return (-1, -1)

def flush_output():
    import sys
    sys.stdout.flush()
