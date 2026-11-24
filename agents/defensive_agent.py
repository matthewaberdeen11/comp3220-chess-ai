""" Defensive Agent Evaluation

Strategy: Prioritzes survival, king protection, material preservation, 
and reducing the opponent's opportunities
"""

import chess
from engine.search import best_move

# --- Piece values: (1 pawn = 100) ---
PIECE_VALUES = {
    chess.PAWN: 100,
    chess.KNIGHT: 320,
    chess.BISHOP: 330,
    chess.ROOK: 500,
    chess.QUEEN: 900,
    chess.KING: 0,
}

# --- Feature weights ---
KING_SAFETY = 25
PROTECTED_PIECES =  15
PAWN_STRUCTURE = 15
EXPOSED_PIECE_PENALTY = 25
OPPONENT_MOBILITY = 15
ENEMY_KING_PRESSURE = 20

KING_SHIELD_FILES = (-1, 0, 1)



def king_safety_score(board, color):
    """ Evaluate castling status, pawn shield, and king exposure."""

    king_sq = board.king(color)
    if king_sq is None:
        return -10
    score = 0

    has_castled = (color == chess.WHITE and king_sq in(chess.G1, chess.C1)) or (color == chess.BLACK and king_sq in(chess.G8, chess.C8))

    if has_castled: score += 3
    elif board.has_castling_rights(color):
        score += 1
    else: score -= 2

    king_file = chess.square_file(king_sq)
    king_rank = chess.square_rank(king_sq)
    shield_rank = king_rank + (1 if color == chess.WHITE else -1)

    for df in KING_SHIELD_FILES:
        f = king_file + df
        if (0 <= f <= 7):
            # No shield square when the king is on the far edge (rank 8 for White, rank 1 for Black)
            if 0 <= shield_rank <= 7:
                sq = chess.square(f, shield_rank)
                piece = board.piece_at(sq)
                if piece and piece.piece_type == chess.PAWN and piece.color == color:
                    score += 1
                else:
                    score -= 1

            has_own_pawn = any(
                board.piece_at(chess.square(f, r)) == chess.Piece(chess.PAWN, color) for r in range(8))
            if not has_own_pawn:
                score -= 1

    if king_file in (3,4) and len(board.piece_map()) > 12:
        score -= 2

    return score

def protected_pieces_score(board, color):
    """Reward friendly non-pawn pieces that are defended by friendly pieces."""
    score = 0

    for sq, piece in board.piece_map().items():
        if piece.color == color and piece.piece_type not in (chess.PAWN, chess.KING):
            defenders =  len(board.attackers(color, sq))
            if defenders > 0:
                score += 1 * min(defenders - 1, 2)
    
    return score

def pawn_structure_score(board, color):
    """Reward solid pawn chains and penalize double or isolated pawns."""
    pawn_squares = [sq 
                   for sq, piece in board.piece_map().items()
                   if piece.color == color and piece.piece_type == chess.PAWN
                   ]
    if not pawn_squares:
        return 0

    files =  [chess.square_file(sq) for sq in pawn_squares]
    score = 0

    for f in range(8):
        count_in_file = files.count(f)
        if count_in_file > 1:
            score -= 1 *(count_in_file - 1)

        if count_in_file > 0:
            has_neighbour = (f > 0 and files.count(f -1) > 0) or (f < 7 and files.count(f +1) > 0)
            if not has_neighbour:
                score -= 1 * count_in_file

    score += sum(1 for sq in pawn_squares if board.attackers(color, sq))
    return score

def expose_piece_penalty(board, color):
    """Penalize hanging pieces under enemy attack."""
    enemy = not color
    penalty = 0

    for sq, piece in board.piece_map().items():
        if piece.color == color and piece.piece_type != chess.KING:
            attackers = list(board.attackers(enemy, sq))
            if not attackers:
                continue

            defenders = list(board.attackers(color, sq))
            piece_val =  PIECE_VALUES[piece.piece_type]/100
            min_attacker_val = min(PIECE_VALUES[board.piece_at(a).piece_type]/100
                            for a in attackers if board.piece_at(a))

            if not defenders:
                penalty += piece_val * 2
            elif min_attacker_val < piece_val:
                penalty += (piece_val - min_attacker_val) * 1
            elif len(attackers) > len(defenders):
                penalty += piece_val * 1

    return penalty

def opponent_mobility_penalty(board, color):
    """Penalize high opponent pseudo-legal/ legal move count(restricting options)"""
    enemy = not color
    if board.turn == enemy:
        opp_moves = board.legal_moves.count()
    else:
        copy_board = board.copy(stack = False)
        copy_board.turn = enemy
        opp_moves = sum(1 for k in copy_board.generate_legal_moves())

    return opp_moves * 1

def enemy_king_pressure_penalty(board, color):
    """Measure enemy attackers near king and checks against us."""
    king_sq = board.king(color)
    if king_sq is None:
        return 10

    enemy = not color
    king_file = chess.square_file(king_sq)
    king_rank = chess.square_rank(king_sq)
    penalty = 0

    for df in KING_SHIELD_FILES:
        for dr in KING_SHIELD_FILES:
            if df == 0 and dr == 0:
                continue

            f, r =  king_file + df, king_rank + dr 
            if (0 <= f <= 7) and (0 <= r <= 7):
                adj_sq = chess.square(f,r)
                attackers = board.attackers(enemy, adj_sq)
                if attackers:
                    penalty += 1 * len(attackers)

    # Checked once, after all 8 squares around the king have been counted
    if board.is_check() and board.turn == color:
        penalty += 3

    return penalty

def enemy_promotion_threat_penalty(board, enemy):
    """Penalize advanced enemy pawns close to promotion."""
    penalty = 0
    for sq, piece in board.piece_map().items():
        if piece.color == enemy and piece.piece_type == chess.PAWN:
            rank = chess.square_rank(sq)
            advancement = (7-rank) if enemy == chess.WHITE else rank
            if advancement >= 5:
                penalty += (advancement-4) * 2

    return penalty


def material_diff(board, color):
    """Returns the material value left(in centipawns) of pieces of a given color"""
    enemy = not color
    own_material = sum(
        PIECE_VALUES[p.piece_type]
        for p in board.piece_map().values()
        if p.color == color
    )
    opp_material = sum(
        PIECE_VALUES[p.piece_type]
        for p in board.piece_map().values()
        if p.color == enemy
    )

    return own_material - opp_material

def trade_when_ahead_bonus(board, mat_diff):
    """Reward simplifying/trading pieces when ahead in material"""

    if mat_diff <= 150:
        return 0

    total_non_king = sum(
        PIECE_VALUES[p.piece_type]
        for p in board.piece_map().values()
        if p.piece_type != chess.KING
    )


    max_starting_non_king =  2*(8 * 100 + 2 * 320 + 2 * 330 + 2 * 500 + 900)
    exchanged_ratio = max(0, (max_starting_non_king) - total_non_king)
    return exchanged_ratio * min(mat_diff * 1, 150)


def side_score(board, color):
    """Calculates defensive evaluation for color's perspective"""
    mat_diff = material_diff(board, color)
    trading_bonus = trade_when_ahead_bonus(board, mat_diff)
    king_safety = king_safety_score(board, color)
    enemy_king_pressure = enemy_king_pressure_penalty(board, color)
    protected_pieces = protected_pieces_score(board, color)
    exposed_pieces = expose_piece_penalty(board, color)
    pawn_structure = pawn_structure_score(board, color)
    opponent_mobility = opponent_mobility_penalty(board, color)
    promotion_threat_penalty = enemy_promotion_threat_penalty(board, color)

    score = (
        mat_diff
        + trading_bonus
        + 25 * king_safety
        + 15 * protected_pieces
        + 15 * pawn_structure
        - 25 * exposed_pieces
        - 15 * opponent_mobility
        - 20 * enemy_king_pressure
        - 20 * promotion_threat_penalty 
    )

    return score


def evaluate(board):
    """Score from White's point of view: positive favours White.

    engine.search.best_move calls evaluate(board) with only the board, so we
    score each side from its own perspective and subtract Black from White.
    """
    return side_score(board, chess.WHITE) - side_score(board, chess.BLACK)


class DefensiveAgent:
    """Defensive Chess Agent
    
    Strategy: Prioritizes survival, king protection, material preservation,
    and reducing the opponent's opportunities. The evaluation rewards material advantage,
    king safety, castling, pawn protection around the king, protected pieces, solid pawn structure,
    reduced opponent mobility, blocking checks and threats, avoiding hanging pieces, trading pieces when 
    ahead and preventing enemy promotion. It should penalize exposed kings, undefended pieces, doubled
    or isolated pawns, and enemy attackers near the king.

    Moves are chosen using the minimax + alpha-beta pruning(engin.search) to a configurable depth.
    """

    name = "Defending"

    def __init__(self, depth=2):
        self.depth = depth
    
    def choose_move(self, board):
        return best_move(board, self.depth, evaluate)

if __name__ == "__main__":
    from agents.random_agent import RandomAgent
    from engine.game import display_board

    white = DefensiveAgent()
    black = RandomAgent()
    board = chess.board()

    while not board.is_game_over():
        agent = white if board.turn == chess.WHITE else black
        move = agent.choose_move(board)
        print(agent.name, move)
        board.push(move)
    
    display_board(board)
    print("Results: ", board.result())
    print("Reason: ", board.outcome().termination)
    print("Moves played: ", len(board.move_stack))
