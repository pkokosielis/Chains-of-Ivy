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

from tuimain import ChainsOfIvyApp, ConfirmScreen

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


def test_tuimain_restart_after_death_returns_to_playable_state():
   async def _play_then_kill_then_restart():
      app = ChainsOfIvyApp()
      async with app.run_test() as pilot:
         log = app.query_one("#log", RichLog)

         # Kill the player directly, mirroring death mid-battle, then confirm
         # every ordinary command is refused until "restart" is issued.
         app.player.hp = 0

         for command in ["look", "n", "attack", "inventory"]:
            await pilot.click("#command")
            await pilot.press(*tuple(command))
            await pilot.press("enter")
            await pilot.pause()

         stuck_output = "\n".join(strip.text for strip in log.lines)
         assert stuck_output.count("You have already perished") == 4
         assert app.player.isDead() is True

         await pilot.click("#command")
         await pilot.press(*tuple("restart"))
         await pilot.press("enter")
         await pilot.pause()

         return app, "\n".join(strip.text for strip in log.lines)

   app, output = asyncio.run(asyncio.wait_for(_play_then_kill_then_restart(), TIMEOUT))

   assert app.player.isDead() is False
   assert "Chorley Park Study" in output


def test_tuimain_quit_shows_dialog_and_no_cancels():
   async def _play_quit_then_cancel():
      app = ChainsOfIvyApp()
      async with app.run_test() as pilot:
         log = app.query_one("#log", RichLog)

         await pilot.click("#command")
         await pilot.press(*tuple("quit"))
         await pilot.press("enter")
         await pilot.pause()

         assert isinstance(app.screen, ConfirmScreen)

         await pilot.click("#confirm-no")
         await pilot.pause()

         assert app.is_running

         # Confirm the game is still fully playable after cancelling.
         await pilot.click("#command")
         await pilot.press(*tuple("look"))
         await pilot.press("enter")
         await pilot.pause()

         return app, "\n".join(strip.text for strip in log.lines)

   app, output = asyncio.run(asyncio.wait_for(_play_quit_then_cancel(), TIMEOUT))

   assert "Then onwards you go!" in output
   assert "Chorley Park Study" in output
   assert app.player.isDead() is False


def test_tuimain_quit_confirmed_exits_app():
   async def _play_quit_then_confirm():
      app = ChainsOfIvyApp()
      async with app.run_test() as pilot:
         await pilot.click("#command")
         await pilot.press(*tuple("quit"))
         await pilot.press("enter")
         await pilot.pause()

         assert isinstance(app.screen, ConfirmScreen)

         await pilot.click("#confirm-yes")
         await pilot.pause()

      return app

   app = asyncio.run(asyncio.wait_for(_play_quit_then_confirm(), TIMEOUT))

   assert app.is_running is False
   assert app.return_code == 0


def test_tuimain_restore_shows_dialog_and_no_cancels(tmp_path, monkeypatch):
   monkeypatch.chdir(tmp_path)

   async def _play_restore_then_cancel():
      app = ChainsOfIvyApp()
      async with app.run_test() as pilot:
         log = app.query_one("#log", RichLog)

         await pilot.click("#command")
         await pilot.press(*tuple("restore"))
         await pilot.press("enter")
         await pilot.pause()

         assert isinstance(app.screen, ConfirmScreen)

         await pilot.click("#confirm-no")
         await pilot.pause()

         assert app.is_running

         # Confirm the game is still fully playable after cancelling.
         await pilot.click("#command")
         await pilot.press(*tuple("look"))
         await pilot.press("enter")
         await pilot.pause()

         return app, "\n".join(strip.text for strip in log.lines)

   app, output = asyncio.run(asyncio.wait_for(_play_restore_then_cancel(), TIMEOUT))

   assert "restore is cancelled." in output
   assert "Chorley Park Study" in output
   assert app.player.isDead() is False


def test_tuimain_restore_confirmed_loads_saved_game(tmp_path, monkeypatch):
   monkeypatch.chdir(tmp_path)

   async def _play_save_then_move_then_restore():
      app = ChainsOfIvyApp()
      async with app.run_test() as pilot:
         log = app.query_one("#log", RichLog)

         for command in ["save", "d"]:
            await pilot.click("#command")
            await pilot.press(*tuple(command))
            await pilot.press("enter")
            await pilot.pause()

         assert app.currentRoom.getTitle() == "Chorley Park Library Hall"

         await pilot.click("#command")
         await pilot.press(*tuple("restore"))
         await pilot.press("enter")
         await pilot.pause()

         assert isinstance(app.screen, ConfirmScreen)

         await pilot.click("#confirm-yes")
         await pilot.pause()

         return app, "\n".join(strip.text for strip in log.lines)

   app, output = asyncio.run(asyncio.wait_for(_play_save_then_move_then_restore(), TIMEOUT))

   assert "Game Restored" in output
   assert app.currentRoom.getTitle() == "Chorley Park Study"
