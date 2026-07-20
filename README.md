# Chains of Ivy

A text-adventure RPG: explore rooms, fight monsters, talk to NPCs, shop at
stores, and manage an inventory and stats.

Author: Peter Kokosielis

## Frontends

The game ships two frontends on top of the same engine. The **Textual TUI**
(`tuimain.py`) is the primary, actively developed frontend; the **CLI**
(`main.py`) is kept for compatibility but is not a priority for new features.

- Textual TUI: a scrollable output log plus a command input, with modal
  dialogs to confirm destructive actions (quit, restore).
- CLI: a minimal blocking `input()`-driven command loop in a plain terminal.

Run the TUI:

    python3 tuimain.py

Run the CLI:

    python3 main.py

## Game engine

The `engine/` package holds all game logic and is frontend-agnostic — it
never touches the terminal directly. Instead it writes through a `viewer`
object registered via `engine/IOwrappers.py`'s `iowSetViewer()`; each
frontend supplies its own adapter (`tuimain.py`'s `RichLogViewer` writes to a
Textual `RichLog` widget, while the CLI leaves no viewer set and falls back
to plain `print`/`input`). This is also why engine code must never block on
`input()` directly — doing so would hang the Textual event loop.

Key pieces:

- `PlayerAction` — parses a typed command into a move, admin, or attack
  action and applies it. Commands: `n`/`s`/`e`/`w`/`u`/`d` (move), `look`,
  `inventory`, `stats`, `take <item>`/`take all`, `drop <item>`,
  `use <item>`, `buy <item>`, `talk`, `attack`, `save`, `restore`, `quit`,
  `help`.
- `Room` — a node in the map, connected N/S/E/W/U/D to other rooms, holding
  items, NPCs, an optional storekeeper, and a per-room chance to spawn a
  monster when entered.
- `Character` — the player: HP, level, experience, gold, equipped
  weapon/armor, and inventory.
- `Monster` — a combat encounter with HP, attack range, and
  loot/experience/gold dropped on death.
- `NPC` — a quest-giver with before/after-quest dialogue and rewards.
- `StoreKeeper` — sells items for gold.
- `IOwrappers` — the output/input abstraction described above.

Game content (which rooms, monsters, and NPCs exist, and how they're wired
together) is assembled in `createdRooms.py`, `createdMonsters.py`, and
`createdNPCs.py`. Rooms and monsters are loaded from semicolon-delimited CSV
files in `csv/` (see `csv/README.md` for the exact column formats); NPCs,
storekeepers, and their placement into specific rooms are defined directly
in `createdNPCs.py`/`createdRooms.py`.

The `save`/`restore` commands pickle the current `Room` graph and `Character`
to `game.dat`/`player.dat` in the working directory.

## Requirements

- Python 3.8+
- [Textual](https://github.com/Textualize/textual) 4.x
- pytest, to run the test suite

Dependencies (Fedora):

    sudo dnf install python3-textual python3-pytest

Dependencies (other platforms, via pip):

    pip install textual pytest

Test:

    python3 -m pytest
