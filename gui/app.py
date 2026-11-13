"""Main program for the chess GUI.

Opens the window and runs the pygame game loop:
handle events -> let an agent move if it's its turn -> draw -> show -> repeat.

Two screens:
  menu -- choose Human vs Attacking, Human vs Defensive, or Agent vs Agent
  game -- the board; humans click to move, agents move automatically
"""
import pygame
import chess

from gui.board_view import BoardView, WINDOW_SIZE, BOARD_SIZE
from agents.attacking_agent import AttackingAgent
from agents.random_agent import RandomAgent

# The defensive agent is built by the other partner. Until that file exists,
# the GUI still runs: the Defensive option is greyed out and Agent vs Agent
# uses the Random agent as the attacking agent's opponent.
try:
    from agents.defensive_agent import DefensiveAgent
except ImportError:
    DefensiveAgent = None

FPS = 30                 # frames per second
AGENT_DELAY_MS = 500     # pause before each agent move so humans can follow it
DEFAULT_DEPTH = 2        # search depth for the agents
BUTTON_WIDTH, BUTTON_HEIGHT = 380, 56


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


def status_message(board):
    """Return the status-bar text: checkmate, draw, check, or whose turn it is.

    Checkmate is tested first because a checkmate is also a check.
    """
    side = "White" if board.turn == chess.WHITE else "Black"

    if board.is_checkmate():
        winner = "Black" if board.turn == chess.WHITE else "White"   # side to move lost
        return f"Checkmate — {winner} wins"
    if board.is_game_over():
        reason = board.outcome().termination.name.replace("_", " ").lower()
        return f"Draw — {reason}"
    if board.is_check():
        return f"{side} to move — Check!"
    return f"{side} to move"


def make_agent(kind):
    """Create an agent by name: "attacking", "defensive" or "random"."""
    if kind == "attacking":
        return AttackingAgent(depth=DEFAULT_DEPTH)
    if kind == "defensive":
        return DefensiveAgent(depth=DEFAULT_DEPTH)
    return RandomAgent()


def create_players(choice, human_color):
    """Return {chess.WHITE: player, chess.BLACK: player} for a menu choice.

    A player is an agent object, or None for the human.
    choice -- "attacking" / "defensive" (human vs that agent) or "agents"
    """
    if choice == "agents":
        opponent = "defensive" if DefensiveAgent is not None else "random"
        return {chess.WHITE: make_agent("attacking"), chess.BLACK: make_agent(opponent)}
    return {human_color: None, (not human_color): make_agent(choice)}


def player_name(player):
    """Display name for a player (None = the human)."""
    return "You" if player is None else player.name


def build_menu_buttons(human_color):
    """Return the start-menu buttons as dicts: label, rect, enabled, action."""
    colour_name = "White" if human_color == chess.WHITE else "Black"
    agents_label = ("Attacking vs Defensive" if DefensiveAgent is not None
                    else "Attacking vs Random")
    defensive_label = ("Play vs Defensive agent" if DefensiveAgent is not None
                       else "Defensive agent (not added yet)")
    rows = [
        ("Play vs Attacking agent", True, "attacking"),
        (defensive_label, DefensiveAgent is not None, "defensive"),
        (f"Agent vs Agent: {agents_label}", True, "agents"),
        (f"You play: {colour_name}  (click to switch)", True, "toggle_colour"),
    ]

    buttons = []
    left = (BOARD_SIZE - BUTTON_WIDTH) // 2
    for i, (label, enabled, action) in enumerate(rows):
        rect = pygame.Rect(left, 180 + i * (BUTTON_HEIGHT + 20), BUTTON_WIDTH, BUTTON_HEIGHT)
        buttons.append({"label": label, "rect": rect, "enabled": enabled, "action": action})
    return buttons


def button_at(buttons, pos):
    """Return the action of the enabled button under pos, or None."""
    for button in buttons:
        if button["enabled"] and button["rect"].collidepoint(pos):
            return button["action"]
    return None


def main():
    """Open the window and run the GUI until the user closes it."""
    pygame.init()
    screen = pygame.display.set_mode(WINDOW_SIZE)
    pygame.display.set_caption("COMP3220 Chess AI")
    clock = pygame.time.Clock()
    view = BoardView(screen)

    screen_mode = "menu"       # "menu" or "game"
    human_color = chess.WHITE  # which side the human plays in human-vs-agent
    players = {}               # {colour: agent or None (human)}
    board = chess.Board()
    selected = None            # square of the piece the human has picked up
    last_move_time = 0         # when the last move was made (milliseconds)

    running = True
    while running:
        now = pygame.time.get_ticks()

        # 1. Handle events
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

            elif screen_mode == "menu":
                if event.type == pygame.MOUSEBUTTONDOWN:
                    action = button_at(build_menu_buttons(human_color), event.pos)
                    if action == "toggle_colour":
                        human_color = not human_color
                    elif action is not None:
                        players = create_players(action, human_color)
                        board = chess.Board()
                        selected = None
                        last_move_time = now
                        screen_mode = "game"
                        pygame.display.set_caption(
                            f"{player_name(players[chess.WHITE])} (White) vs "
                            f"{player_name(players[chess.BLACK])} (Black)")

            else:  # game screen
                human_turn = players[board.turn] is None
                if (event.type == pygame.MOUSEBUTTONDOWN and human_turn
                        and not board.is_game_over()):
                    square = view.pixel_to_square(*event.pos)
                    if square is not None:   # None = click on the status bar
                        before = len(board.move_stack)
                        selected = handle_click(board, selected, square)
                        if len(board.move_stack) > before:
                            last_move_time = now   # agent waits a moment before replying
                elif event.type == pygame.KEYDOWN and event.key == pygame.K_r:
                    board = chess.Board()          # R = restart the same match
                    selected = None
                    last_move_time = now
                elif event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                    screen_mode = "menu"           # Esc = back to the menu
                    pygame.display.set_caption("COMP3220 Chess AI")

        # 2. Let an agent move if it's its turn (after a short pause)
        if screen_mode == "game" and not board.is_game_over():
            agent = players[board.turn]
            if agent is not None and now - last_move_time >= AGENT_DELAY_MS:
                board.push(agent.choose_move(board))
                last_move_time = pygame.time.get_ticks()

        # 3. Draw everything for this frame
        if screen_mode == "menu":
            view.draw_menu("COMP3220 Chess AI", build_menu_buttons(human_color),
                           "In a game: R = restart, Esc = menu",
                           pygame.mouse.get_pos())
        else:
            targets = legal_targets(board, selected)
            view.draw(board, selected, targets)
            view.draw_status(status_message(board))

        # 4. Show the frame and wait so we run at FPS
        pygame.display.flip()
        clock.tick(FPS)

    pygame.quit()


if __name__ == "__main__":
    main()
