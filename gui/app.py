"""Main program for the chess GUI.

Opens the window and runs the pygame game loop:
handle events -> draw everything -> show it -> repeat.
"""
import pygame
import chess

from gui.board_view import BoardView, BOARD_SIZE

FPS = 30   # frames per second


def make_move(board, from_square, to_square):
    """Build the Move for a click from one square to another.

    A pawn reaching the last rank is automatically promoted to a queen.
    """
    piece = board.piece_at(from_square)
    if (piece is not None and piece.piece_type == chess.PAWN
            and chess.square_rank(to_square) in (0, 7)):
        return chess.Move(from_square, to_square, promotion=chess.QUEEN)
    return chess.Move(from_square, to_square)


def handle_click(board, selected, square):
    """Process a click on `square` and return the new selected square (or None).

    - Nothing selected: select the square if it holds a piece of the side to move.
    - Something selected: play the move if it's legal; otherwise switch to
      another own piece, or cancel the selection.
    """
    piece = board.piece_at(square)
    own_piece = piece is not None and piece.color == board.turn

    if selected is None:
        return square if own_piece else None

    move = make_move(board, selected, square)
    if move in board.legal_moves:
        board.push(move)
        return None

    return square if own_piece else None


def legal_targets(board, selected):
    """Return the squares the selected piece can legally move to."""
    if selected is None:
        return []
    return [m.to_square for m in board.legal_moves if m.from_square == selected]


def main():
    """Open the window and run the GUI until the user closes it."""
    pygame.init()
    screen = pygame.display.set_mode((BOARD_SIZE, BOARD_SIZE))
    pygame.display.set_caption("COMP3220 Chess AI")
    clock = pygame.time.Clock()

    view = BoardView(screen)
    board = chess.Board()
    selected = None   # square of the piece the human has picked up

    running = True
    while running:
        # 1. Handle events
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.MOUSEBUTTONDOWN:
                square = view.pixel_to_square(*event.pos)
                if square is not None:
                    selected = handle_click(board, selected, square)

        # 2. Draw everything for this frame
        targets = legal_targets(board, selected)
        view.draw(board, selected, targets)

        # 3. Show the frame and wait so we run at FPS
        pygame.display.flip()
        clock.tick(FPS)

    pygame.quit()


if __name__ == "__main__":
    main()
