"""Headless smoke tests for the Textual frontend, driven via Textual's Pilot.

These exist mainly to catch regressions like the one found while building
tuimain.py: doSave/doRestore/doQuit used to call the blocking iowInput(),
which would hang the whole app once a viewer/event-driven frontend was
active. Every test here runs with a timeout so a reintroduced hang fails
fast instead of stalling the suite.
"""

import asyncio

import pytest
from textual.widgets import RichLog

from tuimain import ChainsOfIvyApp

TIMEOUT = 15


async def _play(commands):
   app = ChainsOfIvyApp()
   async with app.run_test() as pilot:
      log = app.query_one("#log", RichLog)
      for command in commands:
         await pilot.click("#command")
         await pilot.press(*tuple(command))
         await pilot.press("enter")
         await pilot.pause()
      return app, "\n".join(strip.text for strip in log.lines)


def test_tuimain_full_session_smoke():
   app, output = asyncio.run(asyncio.wait_for(
      _play(["look", "take all", "inventory", "stats", "d", "help"]), TIMEOUT))

   assert "Chorley Park Study" in output
   assert "You take the Gold pocket watch" in output
   assert "Chorley Park Library Hall" in output
   assert app.player.isDead() is False
   assert app.currentRoom.getTitle() == "Chorley Park Library Hall"


def test_tuimain_save_command_does_not_hang(tmp_path, monkeypatch):
   monkeypatch.chdir(tmp_path)

   asyncio.run(asyncio.wait_for(_play(["save"]), TIMEOUT))

   assert (tmp_path / "game.dat").exists()
   assert (tmp_path / "player.dat").exists()


def test_tuimain_unknown_command_reports_error():
   app, output = asyncio.run(asyncio.wait_for(_play(["asdfgh"]), TIMEOUT))

   assert "I don't understand your command" in output
