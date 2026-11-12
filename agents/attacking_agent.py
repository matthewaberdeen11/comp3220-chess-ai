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

def evaluate(board):
    """Score from White’s point of view: positive favours White."""
    return (material(board, chess.WHITE) - material(board, chess.BLACK))
  

                    
    
        
        
        
    