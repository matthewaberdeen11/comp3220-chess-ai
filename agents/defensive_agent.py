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
            if 0 <= f <= 7:
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

    score = 0

    for sq, piece in board.piece_map().items():
        if piece.color == color and piece.piece_type not in (chess.PAWN, chess.KING):
            defenders =  len(board.attackers(color, sq))
            if defenders > 0:
                score += 0.5 + 0.25 * min(defenders - 1, 2)
    
    return score

def pawn_structure_score(board, color):
    pawn_squares = [sq 
                   for sq, piece in board.piece_map().items()
                   if piece.color == color and piece.piece_type == chess.PAWN
                   ]
    if not pawn_squares:
        return 0.0

    files =  [chess.square_file(sq) for sq in pawn_squares]
    score = 0.0

    for f in range(8):
        count_in_file = files.count(f)
        if count_in_file > 1:
            score -= 0.8 *(count_in_file - 1)

        if count_in_file > 0:
            has_neighbour = (f > 0 and files.count(f -1) > 0) or (f < 0 and files.count(f +1) > 0)
            if not has_neighbour:
                score -= 0.7 * count_in_file

    score += (0.25 for sq in pawn_squares if board.attackers(color, sq))
    return score

def expose_piece_penalty(board, color):

    enemy = not color
    penalty = 0.0

    for sq, piece in board.piece_map().items():
        if piece.color == color and piece.piece_type != chess.KING:
            attackers = list(board.atteackers(enemy, sq))
            if not attackers:
                continue

            defenders = list(board.attackers(color, sq))
            piece_val =  PIECE_VALUES[piece.piece_type]/100.0
            min_attacker_val = min(PIECE_VALUES[board.piece_at(a).piece_type]/100.0
                            for a in attackers if board.piece_at(a))

            if not defenders:
                penalty += piece_val * 1.5
            elif min_attacker_val < piece_val:
                penalty += (piece_val - min_attacker_val) * 1.2
            elif len(attackers) > len(defenders):
                penalty += piece_val * 0.75

    return penalty

def opponent_mobility_penalty(board, color):

    enemy = not color
    if board.turn == enemy:
        opp_moves = board.legal_moves.count()
    else:
        copy_board = board.copy(stack = False)
        copy_board.turn = enemy
        opp_moves = sum(1 for k in copy_board.generate_legal_moves())

    return opp_moves * 0.08

def enemy_king_pressure_penalty(board, color):

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
                    penalty += 0.6 * len(attackers)

            if board.is_check() and board.turn == color:
                penalty += 2.5


            return penalty

def enemy_promotion_threat_penalty(board, color):

    penalty = 0.0
    enemy = not color
    for sq, piece in board.piece_map().items():
        if piece.color == enemy and piece.piece_type == chess.PAWN:
            rank = chess.square_rank(sq)
            advancement = (7-rank) if enemy == chess.WHITE else rank
            if advancement >= 5:
                penalty += (advancement-4) *1.5

    return penalty


def material_diff(board, color):

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

def trade_when_ahead_bonus(board, color,mat_diff):

    if mat_diff <= 150:
        return 0.0

    total_non_king = sum(
        PIECE_VALUES[p.piece_type]
        for p in board.piece_map().values()
        if p.piece_type != chess.KING
    )


    max_starting_non_king =  2*(8*100+2*320 + 2 * 330 + 2 * 500 + 900)
    exchanged_ratio = max(0.0, (max_starting_non_king) - total_non_king)
    return exchanged_ratio * min(mat_diff * 0.25, 150.0)


def evaluate(board, color):

    mat_diff = material_diff(board, color)
    trading_bonus = trade_when_ahead_bonus(board, color)
    king_safety = king_safety_score(board, color)
    enemy_king_pressure = enemy_king_pressure_penalty(board, color)
    protected_pieces = protected_pieces_score(board, color)
    expose_piece_penalty = expose_piece_penalty(board, color)
    pawn_structure = pawn_structure_score(board, color)
    opponent_mobility = opponent_mobility_penalty(board, color)
    promotion_threat_penalty = enemy_promotion_threat_penalty(board, color)

    score = (
        mat_diff
        + trading_bonus
        + 25.0 * king_safety
        + 15.0 * protected_pieces
        + 15.0 * pawn_structure
        - 25.0 * expose_piece_penalty
        - 15.0 * opponent_mobility
        - 20.0 * enemy_king_pressure
        - 20.0 * promotion_threat_penalty 
    )

    return score


class DefensiveAgent:

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

    while not board.is_game_game_over():
        agent = white if board.turn == chess.WHITE else black
        move = agent.choose_move(board)
        print(agent.name, move)
        board.push(move)
    
    display_board(board)
    print("Results: ", board.result())
    print("Reason: ", board.outcome().termination)
    print("Moves played: ", len(board.move_stack))
