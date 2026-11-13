import chess

PIECE_VALUES = {
    chess.PAWN: 100,
    chess.KNIGHT: 320,
    chess.BISHOP: 330,
    chess.ROOK: 500,
    chess.QUEEN: 900,
    chess.KING: 0
}

def material(board, color):
    """Return the total material value (in centipawns) of all pieces of the given color."""
    total_value = 0
    for piece_type, value in PIECE_VALUES.items():
        count = len(board.pieces(piece_type, color))
        total_value = count * value + total_value
        
    return total_value

  
MOBILITY_WEIGHT = 10

# Pieces whose mobility we count (pawns and king excluded on purpose)
MOBILITY_PIECES = [chess.KNIGHT, chess.BISHOP, chess.ROOK, chess.QUEEN]


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

def evaluate(board):
    """Score from White’s point of view: positive favours White."""
    material_score = material(board, chess.WHITE) - material(board, chess.BLACK)
    mobility_score = mobility(board, chess.WHITE) - mobility(board, chess.BLACK)

    return material_score + MOBILITY_WEIGHT * mobility_score 
    
        
        
        
    