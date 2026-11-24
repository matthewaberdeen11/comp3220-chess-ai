import chess
from dataclasses import dataclass
from typing import Protocol
from pathlib import Path

from matches.logger import GameRecord, MatchLogger

class ChessAgent(Protocol):
    name:str

    def choose_move(self, board):
        ...

@dataclass
class AgentStats:
    name: str
    wins: int = 0
    losses: int = 0
    draws: int = 0
    games_played: int = 0

    @property
    def points(self):
        return self.wins + 0.5 * self.draws

class MatchRunner:

    def __init__(self, agent_a: ChessAgent, agent_b: ChessAgent, max_plies: int = 200,
                 log_dir: str | Path = "matches/logs",
                 report_path: str | Path = "docs/match_report.md"):

        self.agent_a = agent_a
        self.agent_b = agent_b
        self.max_plies = max_plies
        self.logger = MatchLogger(output_dir = log_dir)
        self.report_path = Path(report_path)
        self.stats: dict[str, AgentStats] = {
            agent_a.name: AgentStats(name=agent_a.name),
            agent_b.name: AgentStats(name=agent_b.name)
        }

    def runsingle_game(self, game_id, white_agent, black_agent):

        board = chess.Board()
        record = self.logger.start_game(
            game_id = game_id,
            white_name = white_agent.name,
            black_name = black_agent.name,
        )

        while not board.is_game_over(claim_draw=True) and record.ply_count < self.max_plies:
            active_agent = white_agent if board.turn == chess.WHITE else black_agent
            move = active_agent.choose_move(board)
            if move not in board.legal_moves:
                raise RuntimeError(f"Illegal move {move.uci()} attempted by {active_agent.name} on game {game_id}")

            board_before = board.copy(stack=False)
            record.record_move(board_before, move)
            board.push(move)

        if board.is_game_over(claim_draw = True):
            record.finalize(board)
        else:
            record.result ="1/2-1/2"
            record.termination = f" Move Limit ({self.max_plies} Plies)"

        self.update_stats(record)
        self.logger.save_game_pgn(record, f"game_{game_id}.pgn")
        self.logger.save_game_text(record, f"game_{game_id}.txt")

        return record    

    def update_stats(self, record):
        white_stats = self.stats[record.white_name]
        black_stats = self.stats[record.black_name]
        white_stats.games_played += 1
        black_stats.games_played += 1

        if record.result == "1-0":
            white_stats.wins += 1
            black_stats.losses += 1
        elif record.result == "0-1":
            black_stats.wins += 1
            white_stats.losses += 1
        else:
            white_stats.draws += 1
            black_stats.draws += 1

    def run_series(self, num_games):
        records: list[GameRecord] = []
        for game_idx in range(1, num_games + 1):
            if game_idx % 2 ==1:
                white_agent, black_agent = self.agent_a, self.agent_b
            else:
                white_agent, black_agent = self.agent_b, self.agent_a

            record = self.runsingle_game(game_idx, white_agent, black_agent)
            records.append(record)

        self.logger.save_all_pgn("match_series.pgn")
        self.write_match_report(records)
        return records

    def format_results_table(self):
        headers = ["Agent", "Games", "Wins", "Losses", "Draws", "Points"]
        rows = []

        for agent_name, st in self.stats.items():
            rows.append([
                agent_name,
                str(st.games_played),
                str(st.wins),
                str(st.losses),
                str(st.draws),
                f"{st.points:.1f}"
            ])

        col_widths = [
            max(len(headers[i]), * (len(r[i]) for r in rows)) for i in range(len(headers))
        ]

        def fmt_row(items):
            return "| " + " | ".join(items[i].ljust(col_widths[i]) for i in range(len(items))) + " |"

        sep = "| " + " | ".join("-" * w for w in col_widths) + " |"
        return "\n".join([fmt_row(headers), sep, *(fmt_row(r) for r in rows)])

    def write_match_report(self, records):
        self.report_path.parent.mkdir(parents=True, exist_ok=True)
        total_games = len(records)
        decisive_games = sum(1 for r in records if r.result in ("1-0", "0-1"))
        draw_games = sum(1 for r in records if r.result == "1/2-1/2")
        avg_plies = (sum(r.ply_count for r in records) / total_games if total_games > 0 else 0.0)

        game_lines = [
            "| Game | White | Black | Result | Plies | Termination |",
            "| --- | --- | --- | --- | --- | --- |"
        ]

        for r in records:
            game_lines.append(
                f"| {r.game_id} | {r.white_name} | {r.black_name} | {r.result} | {r.ply_count} | {r.termination} |"
            )
        
        report_content = "\n".join([
            "# Match Report - Defensive vs. Attacking Agent",
            "",
            '## Summary Standings',
            "",
            self.format_results_table(),
            "",
            "## Series Overview",
            "",
            f"- **Total Games Played:** {total_games}",
            f"- **Decisive Games:** {decisive_games}",
            f"- **Draw Games:** {draw_games}",
            f"- **Average Game Length:** {avg_plies:.1f} plies",
            "",
            "## Game-by-Game Log",
            "",
            *game_lines
        ])

        self.report_path.write_text(report_content, encoding= 'utf-8')
        return self.report_path

if __name__ == "__main__":
    from agents.defensive_agent import DefensiveAgent
    from agents.attacking_agent import AttackingAgent

    defender = DefensiveAgent(depth=2)
    attacker = AttackingAgent(depth=2)
    runner = MatchRunner(agent_a=defender, agent_b=attacker, max_plies=120)
    runner.run_series(num_games=10)   # alternates colours each game
    print(runner.format_results_table())    