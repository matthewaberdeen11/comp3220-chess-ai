import random
import chess


class RandomAgent:
    name = "Random"

    def choose_move(self, board):
        """Return a random legal move for the side to move. Does not modify the board."""
        #take a list of all moves 
        moves = list(board.legal_moves)
        move = random.choice(moves)
        
        return move

if __name__ == "__main__":
    from engine.game import new_board, display_board

    board = new_board()
    agent = RandomAgent()

    while not board.is_game_over():
        move = agent.choose_move(board)
        print(move)
        board.push(move)

    display_board(board)
    print("Result:", board.result())
    print("Reason:", board.outcome().termination)
    print("Moves played:", len(board.move_stack))
