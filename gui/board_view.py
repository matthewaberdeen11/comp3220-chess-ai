"""Board drawing for the chess GUI.

This module only DRAWS things (board, pieces) and converts between chess
squares and screen pixels. All game logic lives in gui/app.py.
"""
import pygame
import chess

# --- Sizes ---
SQUARE_SIZE = 80                 # pixels per square
BOARD_SIZE = 8 * SQUARE_SIZE     # 640 x 640
STATUS_HEIGHT = 40               # pixels for the status strip under the board
WINDOW_SIZE = (BOARD_SIZE, BOARD_SIZE + STATUS_HEIGHT)

# --- Colours (RGB) ---
LIGHT = (240, 217, 181)          # light squares
DARK = (181, 136, 99)            # dark squares
WHITE_PIECE = (255, 255, 255)
BLACK_PIECE = (0, 0, 0)
SELECTED = (246, 246, 105)       # yellow tint for the picked-up piece
TARGET = (100, 110, 64)          # dots on legal destination squares
STATUS_BG = (40, 40, 40)         # dark grey status strip
STATUS_TEXT = (255, 255, 255)
MENU_BG = (30, 30, 30)           # start-menu background
BUTTON = (70, 110, 160)
BUTTON_HOVER = (95, 140, 195)
BUTTON_DISABLED = (80, 80, 80)
HINT_TEXT = (170, 170, 170)

# Fonts that contain the Unicode chess symbols (macOS first, then Windows).
PIECE_FONTS = "applesymbols,segoeuisymbol"


class BoardView:
    """Draws a python-chess board onto a pygame screen."""

    def __init__(self, screen):
        """screen -- the pygame surface to draw on."""
        self.screen = screen
        self.font = pygame.font.SysFont(PIECE_FONTS, SQUARE_SIZE - 10)
        self.text_font = pygame.font.SysFont(None, 28)   # default font for messages
        self.title_font = pygame.font.SysFont(None, 52)  # menu title

    def square_to_pixel(self, square):
        """Return the (x, y) pixel of a square's top-left corner.

        Files (a-h) run left to right. Ranks are flipped so rank 8 is at the
        top of the window and rank 1 at the bottom (White's side).
        """
        file = chess.square_file(square)
        rank = chess.square_rank(square)
        x = file * SQUARE_SIZE
        y = (7 - rank) * SQUARE_SIZE
        return x, y

    def pixel_to_square(self, x, y):
        """Return the chess square under pixel (x, y), or None if the click
        is outside the board. The reverse of square_to_pixel."""
        file = x // SQUARE_SIZE
        rank = 7 - (y // SQUARE_SIZE)
        if not (0 <= file <= 7 and 0 <= rank <= 7):
            return None
        return chess.square(file, rank)

    def draw_highlights(self, selected, targets):
        """Tint the selected square and put a dot on each legal target square."""
        if selected is not None:
            x, y = self.square_to_pixel(selected)
            pygame.draw.rect(self.screen, SELECTED, (x, y, SQUARE_SIZE, SQUARE_SIZE))
        for square in targets:
            x, y = self.square_to_pixel(square)
            centre = (x + SQUARE_SIZE // 2, y + SQUARE_SIZE // 2)
            pygame.draw.circle(self.screen, TARGET, centre, SQUARE_SIZE // 6)

    def draw_board(self):
        """Draw the 64 light and dark squares (a1 is dark)."""
        for square in chess.SQUARES:
            file = chess.square_file(square)
            rank = chess.square_rank(square)
            colour = DARK if (file + rank) % 2 == 0 else LIGHT
            x, y = self.square_to_pixel(square)
            pygame.draw.rect(self.screen, colour, (x, y, SQUARE_SIZE, SQUARE_SIZE))

    def draw_pieces(self, board):
        """Draw every piece on the board using Unicode chess symbols.

        Every piece is drawn with the FILLED symbol. White pieces are filled
        white and then given a black outline (the hollow symbol drawn on top),
        so they stay visible on light squares.
        """
        for square in chess.SQUARES:
            piece = board.piece_at(square)
            if piece is None:
                continue

            x, y = self.square_to_pixel(square)
            centre = (x + SQUARE_SIZE // 2, y + SQUARE_SIZE // 2)

            filled_symbol = chess.Piece(piece.piece_type, chess.BLACK).unicode_symbol()
            colour = WHITE_PIECE if piece.color == chess.WHITE else BLACK_PIECE
            image = self.font.render(filled_symbol, True, colour)
            self.screen.blit(image, image.get_rect(center=centre))

            if piece.color == chess.WHITE:
                outline = self.font.render(piece.unicode_symbol(), True, BLACK_PIECE)
                self.screen.blit(outline, outline.get_rect(center=centre))

    def draw(self, board, selected=None, targets=()):
        """Draw the whole board: squares, then highlights, then pieces on top."""
        self.draw_board()
        self.draw_highlights(selected, targets)
        self.draw_pieces(board)

    def draw_status(self, message):
        """Draw the status strip under the board with `message` centred in it."""
        pygame.draw.rect(self.screen, STATUS_BG, (0, BOARD_SIZE, BOARD_SIZE, STATUS_HEIGHT))
        image = self.text_font.render(message, True, STATUS_TEXT)
        centre = (BOARD_SIZE // 2, BOARD_SIZE + STATUS_HEIGHT // 2)
        self.screen.blit(image, image.get_rect(center=centre))

    def draw_text(self, text, font, colour, centre):
        """Draw `text` centred on the pixel `centre`."""
        image = font.render(text, True, colour)
        self.screen.blit(image, image.get_rect(center=centre))

    def draw_menu(self, title, buttons, hint, mouse_pos):
        """Draw the start menu.

        buttons   -- list of dicts with "label", "rect" (pygame.Rect) and "enabled"
        hint      -- small help text shown at the bottom
        mouse_pos -- current mouse position, used to highlight the hovered button
        """
        self.screen.fill(MENU_BG)
        width, height = self.screen.get_size()
        self.draw_text(title, self.title_font, STATUS_TEXT, (width // 2, 90))

        for button in buttons:
            if not button["enabled"]:
                colour = BUTTON_DISABLED
            elif button["rect"].collidepoint(mouse_pos):
                colour = BUTTON_HOVER
            else:
                colour = BUTTON
            pygame.draw.rect(self.screen, colour, button["rect"], border_radius=8)
            self.draw_text(button["label"], self.text_font, STATUS_TEXT, button["rect"].center)

        self.draw_text(hint, self.text_font, HINT_TEXT, (width // 2, height - 40))