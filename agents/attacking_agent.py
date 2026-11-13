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


MOBILITY_WEIGHT = 10
CENTRE_WEIGHT = 15
KING_ZONE_WEIGHT = 20       # per square attacked in the enemy king's zone
KING_ATTACKER_WEIGHT = 10   # per piece aiming at the enemy king's zone
CHECK_WEIGHT = 30           # bonus when we have the enemy king in check
PAWN_STORM_WEIGHT = 5       # per rank a pawn has advanced near the enemy king
PROMOTION_WEIGHT = 40       # per promotion-threat point


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


def king_zone(board, color):
    """Return a SquareSet of color's king square plus every square next to it.
    Returns an empty SquareSet if color has no king (test positions)."""
    king_square = board.king(color)
    if king_square is None:
        return chess.SquareSet()
    zone = board.attacks(king_square)   # the squares around the king
    zone.add(king_square)               # plus the king's own square
    return zone

def relative_rank(square, color):
    """Return how far up the board a square is from color's own side (0-7).

    White counts from rank 1 upward; Black counts from rank 8 downward, so
    both colours' pawns start on relative rank 1 and promote on relative rank 7.
    """
    rank = chess.square_rank(square)
    if color == chess.WHITE:
        return rank
    return 7 - rank

def king_zone_control(board, color):
    """Return how many squares in the ENEMY king's zone are attacked by color."""
    enemy = not color
    count = 0
    for square in king_zone(board, enemy):
        if board.is_attacked_by(color, square):
            count += 1
    return count


def king_attackers(board, color):
    """Return how many DIFFERENT pieces of color attack at least one square
    in the enemy king's zone. A piece hitting several zone squares counts once."""
    enemy = not color
    attackers = chess.SquareSet()
    for square in king_zone(board, enemy):
        attackers |= board.attackers(color, square)   # union: no duplicates
    own_king = board.king(color)
    if own_king is not None:
        attackers.discard(own_king)   # our king next to theirs isn't an attack
    return len(attackers)

def gives_check(board, color):
    """Return 1 if color currently has the enemy king in check, else 0.

    Only the side to move can be in check, so the enemy is in check when it
    is the enemy's turn and board.is_check() is True.
    """
    enemy = not color
    return int(board.turn == enemy and board.is_check())
def pawn_storm(board, color):
    """Return how many ranks color's pawns have advanced, counting only pawns
    on the enemy king's file or the files next to it (a pawn storm)."""
    enemy_king = board.king(not color)
    if enemy_king is None:
        return 0
    king_file = chess.square_file(enemy_king)

    total = 0
    for square in board.pieces(chess.PAWN, color):
        if abs(chess.square_file(square) - king_file) <= 1:
            total += relative_rank(square, color) - 1   # 0 on its starting square
    return total


def promotion_threat(board, color):
    """Return promotion-threat points for color's pawns:
    2 for a pawn on the 7th rank (one step from promoting),
    1 for a pawn on the 6th rank (two steps away)."""
    total = 0
    for square in board.pieces(chess.PAWN, color):
        rel = relative_rank(square, color)
        if rel == 6:
            total += 2
        elif rel == 5:
            total += 1
    return total

def pawn_storm(board, color):
    """Return how many ranks color's pawns have advanced, counting only pawns
    on the enemy king's file or the files next to it (a pawn storm)."""
    enemy_king = board.king(not color)
    if enemy_king is None:
        return 0
    king_file = chess.square_file(enemy_king)

    total = 0
    for square in board.pieces(chess.PAWN, color):
        if abs(chess.square_file(square) - king_file) <= 1:
            total += relative_rank(square, color) - 1   # 0 on its starting square
    return total


def promotion_threat(board, color):
    """Return promotion-threat points for color's pawns:
    2 for a pawn on the 7th rank (one step from promoting),
    1 for a pawn on the 6th rank (two steps away)."""
    total = 0
    for square in board.pieces(chess.PAWN, color):
        rel = relative_rank(square, color)
        if rel == 6:
            total += 2
        elif rel == 5:
            total += 1
    return total