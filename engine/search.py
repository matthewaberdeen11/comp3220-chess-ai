"""Shared search engine: minimax for both agents.

Both the attacking and defensive agents use these functions. Each agent passes
in its OWN evaluation function, so the search is shared but the strategy isn't.

Convention: scores are from White's point of view (positive favours White).
White is the maximising player, Black is the minimising player.
"""
import math

import chess

# Bigger than any possible evaluation, so checkmate always outranks material.
MATE_SCORE = 100_000


def terminal_score(board, depth):
    """Return the score of a finished game (checkmate or draw).

    Checkmate: the side to move has lost. We add the remaining depth so that
    a mate found sooner (more depth left) scores higher; the agent prefers
    mate in 1 over mate in 3.
    Draws (stalemate, repetition, insufficient material, ...) score 0.
    """
    if board.is_checkmate():
        if board.turn == chess.WHITE:
            return -(MATE_SCORE + depth)   # White is mated: great for Black
        return MATE_SCORE + depth          # Black is mated: great for White
    return 0


def minimax(board, depth, evaluate, maximizing):
    """Return the minimax score of the position, searching `depth` moves ahead.

    board      -- position to search (pushed/popped in place, left unchanged)
    depth      -- how many more half-moves to look ahead
    evaluate   -- function(board) -> score from White's point of view
    maximizing -- True if it's White's turn (pick the highest score),
                  False if it's Black's turn (pick the lowest score)
    """
    if board.is_game_over():
        return terminal_score(board, depth)
    if depth == 0:
        return evaluate(board)

    if maximizing:
        best = -math.inf
        for move in board.legal_moves:
            board.push(move)
            score = minimax(board, depth - 1, evaluate, False)
            board.pop()
            best = max(best, score)
        return best
    else:
        best = math.inf
        for move in board.legal_moves:
            board.push(move)
            score = minimax(board, depth - 1, evaluate, True)
            board.pop()
            best = min(best, score)
        return best


def best_move(board, depth, evaluate):
    """Return the best move for the side to move, searching `depth` half-moves
    with alpha-beta pruning.

    This is what agents call. It runs the top level of the search itself so it
    can remember WHICH move produced the best score, and it tightens the
    alpha/beta window after each root move so later moves get pruned too.
    """
    maximizing = board.turn == chess.WHITE
    best_score = -math.inf if maximizing else math.inf
    chosen = None
    alpha, beta = -math.inf, math.inf

    for move in board.legal_moves:
        board.push(move)
        score = alphabeta(board, depth - 1, evaluate, alpha, beta, not maximizing)
        board.pop()

        if maximizing:
            if score > best_score:
                best_score, chosen = score, move
            alpha = max(alpha, best_score)
        else:
            if score < best_score:
                best_score, chosen = score, move
            beta = min(beta, best_score)

    return chosen

def alphabeta(board, depth, evaluate, alpha, beta, maximizing):
    """Minimax with alpha-beta pruning. Returns the same score as minimax,
    but skips branches that cannot change the final decision.

    alpha -- the best score White (maximiser) is already guaranteed elsewhere
    beta  -- the best score Black (minimiser) is already guaranteed elsewhere

    If beta <= alpha, the opponent would never allow this position to be
    reached (they already have a better option), so we stop searching it.
    """
    if board.is_game_over():
        return terminal_score(board, depth)
    if depth == 0:
        return evaluate(board)

    if maximizing:
        best = -math.inf
        for move in board.legal_moves:
            board.push(move)
            score = alphabeta(board, depth - 1, evaluate, alpha, beta, False)
            board.pop()
            best = max(best, score)
            alpha = max(alpha, best)        # White's guarantee improves
            if beta <= alpha:
                break                       # Black won't allow this line: prune
        return best
    else:
        best = math.inf
        for move in board.legal_moves:
            board.push(move)
            score = alphabeta(board, depth - 1, evaluate, alpha, beta, True)
            board.pop()
            best = min(best, score)
            beta = min(beta, best)          # Black's guarantee improves
            if beta <= alpha:
                break                       # White won't allow this line: prune
        return best