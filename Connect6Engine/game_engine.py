from defines import *
from tools import *
import sys
from search_engine import SearchEngine
import time

class GameEngine:
    def __init__(self, name=Defines.ENGINE_NAME):
        if name and len(name) > 0:
            if len(name) < Defines.MSG_LENGTH:
                self.m_engine_name = name
            else:
                print(f"Too long Engine Name: {name}, should be less than: {Defines.MSG_LENGTH}")
        self.m_alphabeta_depth = 6
        self.m_board = [[0]*Defines.GRID_NUM for _ in range(Defines.GRID_NUM)]
        self.init_game()
        self.m_search_engine = SearchEngine()
        self.m_best_move = StoneMove()

    def init_game(self):
        init_board(self.m_board)

    def on_help(self):
        print(
            f"On help for GameEngine {self.m_engine_name}\n"
            " name        - print the name of the Game Engine.\n"
            " print       - print the board.\n"
            " exit/quit   - quit the game.\n"
            " black XXXX  - place the black stone on the position XXXX.\n"
            " white XXXX  - place the white stone on the position XXXX.\n"
            " next        - engine will search next move.\n"
            " move XXXX   - opponent played XXXX, engine replies.\n"
            " new black   - restart game, engine plays black.\n"
            " new white   - restart game, engine plays white.\n"
            " depth d     - set alphabeta depth.\n"
            " vcf / unvcf - enable or disable vcf search.\n"
            " help        - show this help.\n"
        )

    def run(self):
        # Print help ONLY if run manually (not GUI)
        if sys.stdin.isatty():
            self.on_help()

        while True:
            try:
                msg = input().strip()
            except EOFError:
                return 0  # prevent PyInstaller crash

            log_to_file(msg)

            if msg == "name":
                print(f"name {self.m_engine_name}")

            elif msg in ("exit", "quit"):
                break

            elif msg == "print":
                print_board(self.m_board, self.m_best_move)

            elif msg == "vcf":
                self.m_vcf = True

            elif msg == "unvcf":
                self.m_vcf = False

            elif msg.startswith("black"):
                self.m_best_move = msg2move(msg[6:])
                make_move(self.m_board, self.m_best_move, Defines.BLACK)
                self.m_chess_type = Defines.BLACK

            elif msg.startswith("white"):
                self.m_best_move = msg2move(msg[6:])
                make_move(self.m_board, self.m_best_move, Defines.WHITE)
                self.m_chess_type = Defines.WHITE

            elif msg == "next":
                self.m_chess_type = self.m_chess_type ^ 3
                if self.search_a_move(self.m_chess_type, self.m_best_move):
                    make_move(self.m_board, self.m_best_move, self.m_chess_type)
                    print(f"move {move2msg(self.m_best_move)}")
                    flush_output()

            elif msg.startswith("new"):
                self.init_game()
                if msg[4:] == "black":
                    self.m_best_move = msg2move("JJ")
                    make_move(self.m_board, self.m_best_move, Defines.BLACK)
                    self.m_chess_type = Defines.BLACK
                    print("move JJ")
                    flush_output()
                else:
                    self.m_chess_type = Defines.WHITE

            elif msg.startswith("move"):
                self.m_best_move = msg2move(msg[5:])
                make_move(self.m_board, self.m_best_move, self.m_chess_type ^ 3)
                if is_win_by_premove(self.m_board, self.m_best_move):
                    print("We lost!")
                if self.search_a_move(self.m_chess_type, self.m_best_move):
                    print(f"move {move2msg(self.m_best_move)}")
                    make_move(self.m_board, self.m_best_move, self.m_chess_type)
                    flush_output()

            elif msg.startswith("depth"):
                d = int(msg[6:])
                if 0 < d < 10:
                    self.m_alphabeta_depth = d
                print(f"Set the search depth to {self.m_alphabeta_depth}.")

            elif msg == "help":
                self.on_help()

        return 0

    def search_a_move(self, ourColor, bestMove):
        start = time.perf_counter()

        self.m_search_engine.before_search(self.m_board, ourColor, self.m_alphabeta_depth)

        score, best_move = self.m_search_engine.min_max(
            self.m_board, self.m_alphabeta_depth, ourColor, True
        )

        if best_move is not None:
            bestMove.positions[0].x, bestMove.positions[0].y = best_move[0]
            bestMove.positions[1].x, bestMove.positions[1].y = best_move[1]

        end = time.perf_counter()

        print(f"AB Time:\t{end - start:.3f}")
        print(f"Score:\t{score:.3f}")
        return True


def flush_output():
    sys.stdout.flush()


if __name__ == "__main__":
    game_engine = GameEngine()
    game_engine.run()
