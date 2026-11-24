import chess
import chess.pgn
from datetime import datetime, timezone
from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class GameRecord:

    game_id: int
    white_name: str
    black_name: str
    result: str = "*"
    termination: str = "In Progress"
    moves_san: list[str] = field(default_factory=list)
    moves_uci: list[str] = field(default_factory=list)
    ply_count: int = 0

    def record_move(self, board_before,move):
        san = board_before.san(move)
        self.moves_san.append(san)
        self.moves_uci.append(move.uci())
        self.ply_count += 1
        return san

    def finalize(self, board):
        outcome = board.outcome(claim_draw = True)
        if outcome is None:
            self.result = board.result(claim_draw=True)
            self.termination = "Draw/Unfinished"
            return

        if outcome.winner is True:
            self.result = "1-0"
        elif outcome.winner is False:
            self.result = "0-1"
        else:
            self.result = "1/2-1/2"

        self.termination = outcome.termination.name.replace("_", " ").title()

class MatchLogger:

    def __init__(self, output_dir):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok = True)
        self.records: list[GameRecord] = []

    def start_game(self, game_id, white_name, black_name):
        record = GameRecord(game_id = game_id, white_name = white_name, black_name = black_name)
        self.records.append(record)
        return record
    
    def to_pgn_game(self, record, initial_board=None):
        game = chess.pgn.Game()
        game.headers["Event"] = "Chess AI Match Series"
        game.headers["Site"] = "Local Match Runner"
        game.headers["Date"] = datetime.now(timezone.utc).strftime("%Y.%m.%d")
        game.headers["Round"] = str(record.game_id)
        game.headers["White"] = record.white_name
        game.headers["Black"] = record.black_name
        game.headers["Result"] = record.result
        game.headers["Termination"] = record.termination

        board = initial_board.copy() if initial_board else chess.Board()
        node = game
        for uci in record.moves_uci:
            move = chess.Move.from_uci(uci)
            if move in board.legal_moves:
                node = node.add_variation(move)
                board.push(move)

        return game

    def save_game_pgn(self, record, filename):
        game = self.to_pgn_game(record)
        target = self.output_dir / filename
        with target.open("w", encoding="utf-8") as fh:
            game.accept(chess.pgn.FileExporter(fh))

        return target

    def save_all_pgn(self, filename):
        target = self.output_dir / filename
        with target.open("w", encoding="utf-8") as fh:
            for record in self.records:
                game = self.to_pgn_game(record)
                print(game, file=fh, end="\n\n")

        return target

    def save_game_text(self, record, filename):
        target = self.output_dir / filename
        lines = [
            f"Game #{record.game_id}: {record.white_name} (White) vs {record.black_name} (Black)",
            f"Result: {record.result} ({record.termination})",
            f"Total Plies: {record.ply_count}", "_" * 50
        ]

        for idx in range(0, len(record.moves_san), 2):
            move_num = (idx // 2) + 1
            white_move = record.moves_san[idx]
            black_move = record.moves_san[idx + 1] if idx + 1 < len(record.moves_san) else ""

            if black_move:
                lines.append(f'{move_num}. {white_move:<10} {black_move}')
            else:
                lines.append(f'{move_num}. {white_move}')

        target.write_text("\n".join(lines) + "\n", encoding = "utf-8")
        return target
