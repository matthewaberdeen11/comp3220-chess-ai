"""Main program for the chess GUI.

Opens the window and runs the pygame game loop:
handle events -> draw everything -> show it -> repeat.
"""
import pygame
import chess

from gui.board_view import BoardView, BOARD_SIZE

FPS = 30   # frames per second


def main():
    """Open the window and run the GUI until the user closes it."""
    pygame.init()
    screen = pygame.display.set_mode((BOARD_SIZE, BOARD_SIZE))
    pygame.display.set_caption("COMP3220 Chess AI")
    clock = pygame.time.Clock()

    view = BoardView(screen)
    board = chess.Board()

    running = True
    while running:
        # 1. Handle events (window close, later: mouse clicks)
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

        # 2. Draw everything for this frame
        view.draw(board)

        # 3. Show the frame and wait so we run at FPS
        pygame.display.flip()
        clock.tick(FPS)

    pygame.quit()


if __name__ == "__main__":
    main()