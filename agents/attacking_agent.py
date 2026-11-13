"""Attacking agent evaluation.

Strategy: prioritise initiative, active pieces and pressure on the enemy king.
All scores are from White's point of view: positive favours White.
"""
import chess

# --- Piece values (centipawns: 1 pawn = 100) ---
PIECE_VALUES = {
    chess.PAWN: 100,
    chess.KNIGHT: 320,
    chess.BISHOP: 330,
    chess.ROOK: 500,
    chess.QUEEN: 900,
    chess.KING: 0,
}

# --- Feature weights (tune these later) ---
MOBILITY_WEIGHT = 10
CENTRE_WEIGHT = 15

# --- Feature settings ---
# Pieces whose mobility we count (pawns and king excluded on purpose)
MOBILITY_PIECES = [chess.KNIGHT, chess.BISHOP, chess.ROOK, chess.QUEEN]

# The four central squares
CENTRE_SQUARES = [chess.D4, chess.E4, chess.D5, chess.E5]


def material(board, color):
    """Return the total material value (in centipawns) of all pieces of the given color."""
    total_value = 0
    for piece_type, value in PIECE_VALUES.items():
        count = len(board.pieces(piece_type, color))
        total_value += count * value
    return total_value


def mobility(board, color):
    """Return how many squares the given color's knights, bishops, rooks and
    queens attack, excluding squares occupied by that color's own pieces.

    Pawns are skipped (they attack diagonally but move forward) and the king is
    skipped (we don't want to reward it for wandering out early).
    """
    own_pieces = board.occupied_co[color]
    total = 0
    for piece_type in MOBILITY_PIECES:
        for square in board.pieces(piece_type, color):
            reachable = board.attacks(square) & ~own_pieces
            total += len(reachable)
    return total


def centre_control(board, color):
    """Return how many times the given color's pieces (including pawns)
    attack the four central squares d4, e4, d5 and e5.

    A square attacked by two pieces counts twice.
    """
    total = 0
    for square in CENTRE_SQUARES:
        total += len(board.attackers(color, square))
    return total


def evaluate(board):
    """Score from White's point of view: positive favours White."""
    material_score = material(board, chess.WHITE) - material(board, chess.BLACK)
    mobility_score = mobility(board, chess.WHITE) - mobility(board, chess.BLACK)
    centre_score = centre_control(board, chess.WHITE) - centre_control(board, chess.BLACK)

    return (
        material_score
        + MOBILITY_WEIGHT * mobility_score
        + CENTRE_WEIGHT * centre_score
    )