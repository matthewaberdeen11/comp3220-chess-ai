import chess

def new_board():
    """ Returns a fresh board at the starting position. """
    board = chess.Board()
    return board

def display_board(board):
    """ Prints the board in the terminal """
    print(board)

    #Player turn
    if board.turn:
        print("White to move")
    else:
        print("Black to move") 

    #return check if its a check
    if board.is_check():
        print("Check!")


def make_move(board, move_text):
    """ Takes a move as text, such as "e2e4", checks that it’s legal, and plays it if so. """
    try:
        #takes text and converts move object
        move = chess.Move.from_uci(move_text)
    except ValueError:
        print("Illegal Move")
        return False
    if(move not in board.legal_moves):
        return False

    board.push(move)
    return True


if __name__ == "__main__":
    board = new_board()
    while not board.is_game_over():
        display_board(board)
        text = input("Your move: ")
        if not make_move(board, text):
            print("Illegal move")
    display_board(board)
    print(board.result())