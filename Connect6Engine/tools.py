from defines import *
import time

# Point (x, y) if in the valid position of the board.
def isValidPos(x,y):
    return x>0 and x<Defines.GRID_NUM-1 and y>0 and y<Defines.GRID_NUM-1
    
def init_board(board):
    for i in range(21):
        board[i][0] = board[0][i] = board[i][Defines.GRID_NUM - 1] = board[Defines.GRID_NUM - 1][i] = Defines.BORDER
    for i in range(1, Defines.GRID_NUM - 1):
        for j in range(1, Defines.GRID_NUM - 1):
            board[i][j] = Defines.NOSTONE
            
def make_move(board, move, color):
    board[move.positions[0].x][move.positions[0].y] = color
    board[move.positions[1].x][move.positions[1].y] = color

def unmake_move(board, move):
    board[move.positions[0].x][move.positions[0].y] = Defines.NOSTONE
    board[move.positions[1].x][move.positions[1].y] = Defines.NOSTONE

def is_win_by_premove(board, preMove):
    directions = [(1, 0), (0, 1), (1, 1), (1, -1)]

    for direction in directions:
        for i in range(len(preMove.positions)):
            count = 0
            position = preMove.positions[i]
            n = x = position.x
            m = y = position.y
            movStone = board[n][m]
            
            if (movStone == Defines.BORDER or movStone == Defines.NOSTONE):
                return False;
                
            while board[x][y] == movStone:
                x += direction[0]
                y += direction[1]
                count += 1
            x = n - direction[0]
            y = m - direction[1]
            while board[x][y] == movStone:
                x -= direction[0]
                y -= direction[1]
                count += 1
            if count >= 6:
                return True
    return False

# CHECK FOR DRAW
def is_draw(board):
        for row in board:
            for value in row:
                if value == Defines.NOSTONE:
                    return False
        return True



def get_msg(max_len):
    buf = input().strip()
    return buf[:max_len]

def log_to_file(msg):
    g_log_file_name = Defines.LOG_FILE
    try:
        with open(g_log_file_name, "a") as file:
            tm = time.time()
            ptr = time.ctime(tm)
            ptr = ptr[:-1]
            file.write(f"[{ptr}] - {msg}\n")
        return 0
    except Exception as e:
        print(f"Error: Can't open log file - {g_log_file_name}")
        return -1

def move2msg(move):
    if move.positions[0].x == move.positions[1].x and move.positions[0].y == move.positions[1].y:
        msg = f"{chr(ord('S') - move.positions[0].x + 1)}{chr(move.positions[0].y + ord('A') - 1)}"
        return msg
    else:
        msg = f"{chr(move.positions[0].y + ord('A') - 1)}{chr(ord('S') - move.positions[0].x + 1)}" \
              f"{chr(move.positions[1].y + ord('A') - 1)}{chr(ord('S') - move.positions[1].x + 1)}"
        return msg

def msg2move(msg):
    move = StoneMove()
    if len(msg) == 2:
        move.positions[0].x = move.positions[1].x = ord('S') - ord(msg[1]) + 1
        move.positions[0].y = move.positions[1].y = ord(msg[0]) - ord('A') + 1
        move.score = 0
        return move
    else:
        move.positions[0].x = ord('S') - ord(msg[1]) + 1
        move.positions[0].y = ord(msg[0]) - ord('A') + 1
        move.positions[1].x = ord('S') - ord(msg[3]) + 1
        move.positions[1].y = ord(msg[2]) - ord('A') + 1
        move.score = 0
        return move

def print_board(board, preMove=None):
    print("   " + "".join([chr(i + ord('A') - 1)+" " for i in range(1, Defines.GRID_NUM - 1)]))
    for i in range(1, Defines.GRID_NUM - 1):
        print(f"{chr(ord('A') - 1 + i)}", end=" ")
        for j in range(1, Defines.GRID_NUM - 1):
            x = Defines.GRID_NUM - 1 - j
            y = i
            stone = board[x][y]
            if stone == Defines.NOSTONE:
                print(" -", end="")
            elif stone == Defines.BLACK:
                print(" O", end="")
            elif stone == Defines.WHITE:
                print(" *", end="")
        print(" ", end="")        
        print(f"{chr(ord('A') - 1 + i)}", end="\n")
    print("   " + "".join([chr(i + ord('A') - 1)+" " for i in range(1, Defines.GRID_NUM - 1)]))

def print_score(move_list, n):
    board = [[0] * Defines.GRID_NUM for _ in range(Defines.GRID_NUM)]
    for move in move_list:
        board[move.x][move.y] = move.score

    print("  " + "".join([f"{i:4}" for i in range(1, Defines.GRID_NUM - 1)]))
    for i in range(1, Defines.GRID_NUM - 1):
        print(f"{i:2}", end="")
        for j in range(1, Defines.GRID_NUM - 1):
            score = board[i][j]
            if score == 0:
                print("   -", end="")
            else:
                print(f"{score:4}", end="")
        print()

## Finding the longest line

def longest_line(board, x, y, color):
    # Define each direction
    directions = [(1, 0), (0, 1), (1, 1), (1, -1)]
    # initialize length
    length = 0
    # For each direction, count the number of consecutive stones
    for direction_x, direction_y in directions:
        count = 1
        i, j = x + direction_x, y + direction_y
        # Check for valid position and ove in the positive direction
        while isValidPos(i, j) and board[i][j] == color:
            count += 1
            i += direction_x
            j += direction_y
        i, j = x - direction_x, y - direction_y
        # Check for valid position and move in the negative direction
        while isValidPos(i, j) and board[i][j] == color:
            count += 1
            i -= direction_x
            j -= direction_y
        # Update maximum length
        length = max(length, count)
    return length

def half_move_evaluation(board, i, j, color):

    ## Liu's half-move evaluation
    directions = [(1, 0), (0, 1), (1, 1), (1, -1)]  # directions
    our_stone = color
    opp_stone = Defines.BLACK if color == Defines.WHITE else Defines.WHITE
    epsilon = 0.2   # decay
    w_self = 3.0    # multiplier for own stone
    score = 0.0

    for direction_x, direction_y in directions:
        # Forward and backward
        for sign in [1, -1]:
            value = 1.0
            x, y = i + direction_x*sign, j + direction_y*sign
            # 5 steps outward 
            for step in range(1, 6):
                if not isValidPos(x, y):
                    break
                    # If cell empty multiple by small decay
                if board[x][y] == Defines.NOSTONE:
                        value *= epsilon
                    # If contains players own stone multiply by higher weight
                elif board[x][y] == our_stone:
                        value *= w_self
                else:  # opp stone 
                    break
                x += direction_x*sign
                y += direction_y*sign
            # Total score
            score += value
    return score

    # Finding how many open ends in threat
def count_open_ends(board, chain, color):

    # Base case
    if not chain:
        return 0
    
    # Coordinates of start and end of the chain
    chain = sorted(chain)
    (x1, y1), (x2, y2) = chain[0], chain[-1]

    # Direction vector
    direction_x = x2 - x1
    direction_y = y2 - y1

    # Normalize
    direction_x = 0 if direction_x == 0 else int(direction_x / abs(direction_x))
    direction_y = 0 if direction_y == 0 else int(direction_y / abs(direction_y))

    # Initialize count
    open_ends = 0

    # Forward (same direction)
    forward_x, forward_y = x2 + direction_x, y2 + direction_y
    if board[forward_x][forward_y] == Defines.NOSTONE:
        open_ends += 1

    # Backward (opposite direction)
    backward_x, backward_y = x1 - direction_x, y1 - direction_y
    if board[backward_x][backward_y] == Defines.NOSTONE:
        open_ends += 1

    return open_ends

# Find live threats (chains with open ends)

def find_live_threats(board, color, min_length = 3):

    # Initialize 
    open_threats = []
    visited = set()
    directions = [(1, 0), (0, 1), (1, 1), (1, -1)]

    # For each position
    for i in range(1, len(board) - 1):
        for j in range(1, len(board[i]) - 1):
            # If position not visited 
            if board[i][j] != color or (i, j) in visited:
                continue

            # explore each direction, starting a chain
            for direction_x, direction_y in directions:
                chain = [(i, j)]
                x, y = i + direction_x, j + direction_y

                # Extend while stones continue in this direction
                while board[x][y] == color:
                    chain.append((x, y))
                    visited.add((x, y))
                    x += direction_x
                    y += direction_y

                # If length of chain satisfies min length and has open end
                if len(chain) >= min_length:
                    open_ends = count_open_ends(board, chain, color)
                    if open_ends > 0:
                        open_threats.append((chain, open_ends))
    return open_threats