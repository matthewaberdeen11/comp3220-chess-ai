# COMP3220 Chess-Playing AI

Two chess agents with different strategies (one attacking, one defensive) that choose their moves with
**Minimax and Alpha-Beta pruning**. The project also includes a **pygame GUI** to play against either
agent or watch them play each other, and a **match runner** that plays a logged series between them.

---

## Requirements

- Python 3.10 or newer (developed on Python 3.15)
- [python-chess](https://python-chess.readthedocs.io/): board, move generation and rules
- [pygame-ce](https://pyga.me/): the GUI. This is the community edition of pygame, used because
  standard `pygame` has no build for recent Python versions.

## Setup

```bash
git clone https://github.com/matthewaberdeen11/comp3220-chess-ai.git
cd comp3220-chess-ai
python3 -m venv venv
source venv/bin/activate          # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

Run every command below from the project root (the folder that contains `agents/`, `engine/` and so on)
with the venv active. Each one uses `python -m`, so the package imports resolve.

---

## How to run

### GUI: play against an agent, or watch agent vs agent

```bash
python -m gui.app
```

The start menu offers:

| Button | What it does |
| --- | --- |
| Play vs Attacking agent | You against the attacking agent |
| Play vs Defensive agent | You against the defensive agent |
| Agent vs Agent: Attacking vs Defensive | Watch the two agents play each other live (Attacking plays White) |
| You play: White / Black | Choose your colour before starting a game against an agent |

**In a game:**

- Click a piece to select it. Its legal moves are shown as dots. Click a dot to move.
- Pawns promote to a queen automatically.
- The status bar shows whose turn it is, check, checkmate, or the reason for a draw.
- Press **R** to restart the game, or **Esc** to return to the menu.
- Agents wait 0.5 s before each move, so you can follow the game.

### Match series: Attacking vs Defensive

```bash
python -m matches.match_runner
```

This plays **10 games**, alternating colours each game, with a limit of 120 half-moves per game. The
random seed is fixed, so the series is repeatable. It writes:

- `matches/logs/game_N.pgn` and `game_N.txt`: each game as PGN and as a readable move list
- `matches/logs/match_series.pgn`: all games in one PGN file
- `docs/match_report.md`: the standings table, a series overview and a game-by-game results table

The runner prints the final standings when it finishes (about 40 s at depth 2).

### Quick single-game tests (agent vs random mover)

```bash
python -m agents.attacking_agent     # Attacking (White) vs Random
python -m agents.defensive_agent     # Defensive (White) vs Random
python -m agents.random_agent        # Random vs Random
python -m engine.game                # play by typing UCI moves (e.g. e2e4) in the terminal
```

---

## How it works

### Search: `engine/search.py`

Both agents share one search. Each agent passes in its **own evaluation function**, so the search
algorithm is the same for both and only the strategy differs.

- `minimax`: plain minimax, kept for reference and for comparing node counts.
- `alphabeta`: minimax with alpha-beta pruning. It returns the same score as minimax but skips branches
  that cannot change the decision.
- `best_move(board, depth, evaluate)`: what the agents call. It searches each root move with alpha-beta,
  narrowing the window after each one. The root moves are shuffled first, so ties are broken randomly and
  repeated games differ.
- Scores are always **from White's point of view**: White maximises and Black minimises. Checkmate scores
  ±(100000 + remaining depth), so a faster mate is preferred. Draws score 0.
- **Depth control:** each agent takes a `depth` argument (half-moves to search). The default is 2.

At depth 3 from the start position, alpha-beta evaluated 1,273 positions where plain minimax evaluated
8,902 (about 7× fewer), and both chose the same move.

### Attacking agent: `agents/attacking_agent.py`

Plays for initiative and pressure on the enemy king. Its evaluation adds the following to material:

- **Mobility:** squares attacked by knights, bishops, rooks and queens
- **Centre control:** attacks on d4, e4, d5 and e5
- **King-zone attacks:** squares around the enemy king that it attacks, and how many different pieces
  join the attack
- **Checks:** a bonus when the enemy king is in check
- **Pawn storms:** pawns advancing on or next to the enemy king's file
- **Promotion threats:** pawns on the 6th and 7th ranks
- **Piece activity:** piece-square tables that reward knights, bishops and rooks placed in the enemy half

### Defensive agent: `agents/defensive_agent.py`

Plays for safety and material preservation. Its evaluation adds the following to material:

- **King safety:** castling, the pawn shield in front of the king, open files near the king
- **Protected pieces:** pieces defended by their own side
- **Pawn structure:** penalties for doubled and isolated pawns, a bonus for protected pawns
- **Exposed-piece penalty:** pieces that are attacked and not defended
- **Restricting the opponent:** a penalty for each opponent legal move
- **Enemy king pressure:** a penalty for enemy attacks near its own king, and for being in check
- **Enemy promotion threats:** a penalty for advanced enemy pawns
- **Trading when ahead:** a bonus for exchanging pieces when it is up material

### Match harness: `matches/match_runner.py`, `matches/logger.py`

`MatchRunner` plays a series between two agents, alternating colours, and records wins, losses, draws and
points. `MatchLogger` stores each game's moves and saves them as PGN and text files.

---

## Project structure

```
comp3220-chess-ai/
├── agents/
│   ├── attacking_agent.py   # Attacking evaluation + AttackingAgent
│   ├── defensive_agent.py   # Defensive evaluation + DefensiveAgent
│   └── random_agent.py      # Reference agent: random legal moves
├── engine/
│   ├── search.py            # Minimax, alpha-beta, best_move (shared by both agents)
│   └── game.py              # Board helpers + terminal play
├── gui/
│   ├── app.py               # Menu, game loop, human input, agent turns
│   ├── board_view.py        # Drawing the board, pieces, highlights, status bar and menu
│   └── assets/
├── matches/
│   ├── match_runner.py      # Plays and scores a series of games
│   ├── logger.py            # Game records, PGN and text logs
│   └── logs/                # Output of the last match series
├── docs/
│   └── match_report.md      # Generated match report
└── requirements.txt
```

Every agent has the same interface: a `name` attribute and `choose_move(board)`, which returns a
`chess.Move` without changing the board. This lets the GUI and the match runner use any agent.

---

## Who built what

| Member | Built |
| --- | --- |
| **Matthew Aberdeen** (Member 1) | Attacking agent (`agents/attacking_agent.py`), shared search (`engine/search.py`), board helpers (`engine/game.py`), random reference agent, GUI (`gui/app.py`, `gui/board_view.py`) |
| **Samuel** (Member 2) | Defensive agent (`agents/defensive_agent.py`), match runner (`matches/match_runner.py`), logger (`matches/logger.py`), match report (`docs/match_report.md`) |

Matthew also fixed the remaining bugs in the defensive agent, match runner and logger, so that the
match series runs from start to finish.
