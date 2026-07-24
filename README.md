# Chains of Ivy

![Chains of Ivy banner](.images/game_banner.png)

A text-adventure RPG: explore rooms, fight monsters, talk to NPCs, shop at
stores, and manage an inventory and stats.

Author: Peter Kokosielis

## Frontends

Two frontends share the same `engine/` package and save files, so a game
saved in one can be restored in the other.

**Textual TUI** (`tuimain.py`) — a scrollable output log plus a command
input, with modal dialogs to confirm destructive actions (quit, save,
restore, drop, buy, quest turn-in). Runs in the terminal; character-cell
only, so it can't display real images.

    python3 tuimain.py

**Pygame frontend** (`pygame_main.py`) — a desktop window with the same
command input, direction buttons, and inventory/dialog flows as the TUI,
plus real image rendering (the launch banner and per-room art). Its
widgets (buttons, text input, scrollable log, modal dialogs) are a small
hand-rolled toolkit in `pygame_widgets.py`, since no GUI toolkit is
packaged for pygame on Fedora.

    python3 pygame_main.py

## Game engine

The `engine/` package holds all game logic and is frontend-agnostic — it
never touches the terminal or a window directly. Instead it writes through
a `viewer` object registered via `engine/IOwrappers.py`'s `iowSetViewer()`,
which each frontend adapts to its own output: `tuimain.py`'s
`RichLogViewer` writes into a Textual `RichLog` widget, and
`pygame_main.py` hands the engine its `ScrollLog` widget directly (it
already exposes `write(msg)`). This is also why engine code must never
block on `input()` directly — doing so would hang either frontend's event
loop.

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
- [Textual](https://github.com/Textualize/textual) 4.x, for the TUI
- [Pygame](https://www.pygame.org/) 2.x, for the Pygame frontend
- pytest, to run the test suite

You only need Textual or Pygame installed if you plan to run that
particular frontend; the test suite exercises both, so both are needed to
run `python3 -m pytest` cleanly.

Dependencies (Fedora):

    sudo dnf install python3-textual python3-pygame python3-pytest

Dependencies (other platforms, via pip):

    pip install textual pygame pytest

Test (runs both frontends' suites headlessly - the Pygame tests set
`SDL_VIDEODRIVER=dummy` themselves, so no display is required):

    python3 -m pytest
