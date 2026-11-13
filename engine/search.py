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
    """Return the best move for the side to move, searching `depth` half-moves.

    This is what agents call. It runs the top level of minimax itself so it
    can remember WHICH move produced the best score.
    """
    maximizing = board.turn == chess.WHITE
    best_score = -math.inf if maximizing else math.inf
    chosen = None

    for move in board.legal_moves:
        board.push(move)
        score = minimax(board, depth - 1, evaluate, not maximizing)
        board.pop()

        if maximizing and score > best_score:
            best_score, chosen = score, move
        elif not maximizing and score < best_score:
            best_score, chosen = score, move

    return chosen