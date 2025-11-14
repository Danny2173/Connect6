from tools import *

class SearchEngine():
    def __init__(self):
        self.m_board = None
        self.m_chess_type = None
        self.m_alphabeta_depth = None
        self.m_total_nodes = 0

    def before_search(self, board, color, alphabeta_depth):
        self.m_board = [row[:] for row in board]
        self.m_chess_type = color          # MAX PLAYER COLOR (important)
        self.m_alphabeta_depth = alphabeta_depth
        self.m_total_nodes = 0

    # ------------------------------------------------------------
    # POSITION EVALUATION
    # ------------------------------------------------------------
    def evaluate_position(self, board, color, bestMove):

        # Terminal wins
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

        # ---------- MAIN BOARD LOOP ----------
        for i in range(1, rows - 1):
            for j in range(1, rows - 1):

                cell = board[i][j]

                if cell == Defines.NOSTONE:
                    # Mobility search
                    my_dir = half_move_evaluation(board, i, j, our_stone)
                    opp_dir = half_move_evaluation(board, i, j, opp_stone)
                    mobility_score += (my_dir - opp_dir)
                    continue

                # Stones
                if cell == our_stone:
                    chain = min(longest_line(board, i, j, our_stone), 5)
                    my_chain_score += chain_weights.get(chain, 0)

                elif cell == opp_stone:
                    chain = min(longest_line(board, i, j, opp_stone), 5)
                    opp_chain_score += chain_weights.get(chain, 0)

        # ---------- THREAT EVALUATION ----------
        max_threat_value = 0.0
        threat_list = find_live_threats(board, opp_stone)

        if isinstance(threat_list, list):
            for t in threat_list:
                if isinstance(t, (list, tuple)) and len(t) == 2:
                    try:
                        chain = int(t[0])
                        open_ends = int(t[1])
                        max_threat_value = max(max_threat_value, chain * open_ends)
                    except:
                        pass

        threat_penalty = DEFENSE_WEIGHT * max_threat_value

        # ---------- FINAL SCORE ----------
        base_score = my_chain_score - opp_chain_score
        mobility_component = MOBILITY_WEIGHT * mobility_score

        return base_score + mobility_component - threat_penalty


    # ------------------------------------------------------------
    # UTILS
    # ------------------------------------------------------------
    def check_first_move(self):
        for i in range(1, len(self.m_board)-1):
            for j in range(1, len(self.m_board[i])-1):
                if self.m_board[i][j] != Defines.NOSTONE:
                    return False
        return True

    def find_possible_move(self):
        for i in range(1, len(self.m_board)-1):
            for j in range(1, len(self.m_board[i])-1):
                if self.m_board[i][j] == Defines.NOSTONE:
                    return (i, j)
        return (-1, -1)



    # ------------------------------------------------------------
    # POSSIBLE MOVES
    # ------------------------------------------------------------
    def possible_moves(self, board, color, limit=6):

        # KEEPING EXACTLY AS YOU WANT:
        if self.check_first_move():
            return [((10, 10), (10, 10))]      # untouched

        our = color
        opp = Defines.BLACK if color == Defines.WHITE else Defines.WHITE

        rows = len(board)

        # find stones
        stones = []
        for i in range(1, rows - 1):
            for j in range(1, rows - 1):
                if board[i][j] != Defines.NOSTONE:
                    stones.append((i, j))

        if not stones:
            return [((10, 10), (10, 10))]

        # radius = 2 neighborhood
        candidates = set()
        for (sx, sy) in stones:
            for dx in range(-2, 3):
                for dy in range(-2, 3):
                    x, y = sx+dx, sy+dy
                    if 1 <= x < rows-1 and 1 <= y < rows-1:
                        if board[x][y] == Defines.NOSTONE:
                            candidates.add((x, y))

        candidates = list(candidates)

        winning = []
        defending = []
        scored = []

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

        if winning:
            return winning[:limit]

        if defending:
            return defending[:limit]

        scored.sort(key=lambda x: x[1], reverse=True)
        top = [pos for pos, _ in scored[:limit]]

        pairs = []
        for a in range(len(top)):
            for b in range(a+1, len(top)):
                pairs.append((top[a], top[b]))

        if not pairs:
            return [(top[0], None)]

        return pairs



    # ------------------------------------------------------------
    # ALPHABETA (FIXED)
    # ------------------------------------------------------------
    def alphabeta(self, board, depth, alpha, beta, color, maxi_player):

        if is_win_by_premove(board, StoneMove()):
            return self.evaluate_position(board, color, StoneMove()), None

        if is_draw(board):
            return self.evaluate_position(board, color, StoneMove()), None

        if depth <= 0:
            return self.evaluate_position(board, color, StoneMove()), None

        candidate_pairs = self.possible_moves(board, color)

        if not candidate_pairs:
            fallback = self.ensure_two_moves(None)
            return self.evaluate_position(board, color, StoneMove()), fallback

        # MAX
        if maxi_player:
            best_move = None
            best_value = Defines.MININT

            for m1, m2 in candidate_pairs:

                board_copy = [row[:] for row in board]

                dummy = StoneMove()
                dummy.positions[0].x, dummy.positions[0].y = m1

                if m2 is not None:
                    dummy.positions[1].x, dummy.positions[1].y = m2
                else:
                    dummy.positions[1].x, dummy.positions[1].y = -1, -1

                make_move(board_copy, dummy, color)

                next_color = Defines.WHITE if color == Defines.BLACK else Defines.BLACK

                value, _ = self.alphabeta(board_copy, depth-1, alpha, beta, next_color, False)

                if value > best_value:
                    best_value = value
                    best_move = (m1, m2)

                alpha = max(alpha, best_value)
                if alpha >= beta:
                    break

            return best_value, self.ensure_two_moves(best_move)

        # MIN
        else:
            best_move = None
            best_value = Defines.MAXINT

            for m1, m2 in candidate_pairs:

                board_copy = [row[:] for row in board]

                dummy = StoneMove()
                dummy.positions[0].x, dummy.positions[0].y = m1

                if m2 is not None:
                    dummy.positions[1].x, dummy.positions[1].y = m2
                else:
                    dummy.positions[1].x, dummy.positions[1].y = -1, -1

                make_move(board_copy, dummy, color)

                next_color = Defines.WHITE if color == Defines.BLACK else Defines.BLACK

                value, _ = self.alphabeta(board_copy, depth-1, alpha, beta, next_color, True)

                if value < best_value:
                    best_value = value
                    best_move = (m1, m2)

                beta = min(beta, best_value)
                if alpha >= beta:
                    break

            return best_value, self.ensure_two_moves(best_move)



    # ------------------------------------------------------------
    # NORMALIZER — ALWAYS MAKES VALID 2 MOVES
    # ------------------------------------------------------------
    def ensure_two_moves(self, move_pair):

        if move_pair is None:
            p1 = self.find_possible_move()
            p2 = self.find_second_empty(p1)
            return (p1, p2)

        m1, m2 = move_pair

        if m1 is None:
            p1 = self.find_possible_move()
            p2 = self.find_second_empty(p1)
            return (p1, p2)

        if m2 is None:
            m2 = self.find_second_empty(m1)

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
