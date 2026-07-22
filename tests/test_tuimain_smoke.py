"""Headless smoke tests for the Textual frontend, driven via Textual's Pilot.

These exist mainly to catch regressions like the one found while building
tuimain.py: doSave/doRestore/doQuit used to call the blocking iowInput(),
which would hang the whole app once a viewer/event-driven frontend was
active. Every test here runs with a timeout so a reintroduced hang fails
fast instead of stalling the suite.
"""

import asyncio

import pytest
from textual.widgets import Button, RichLog, Static

from engine.Item import Item
from engine.NPC import NPC
from engine.Room import Room
from engine.StoreKeeper import StoreKeeper
from tuimain import (
   ChainsOfIvyApp,
   ConfirmScreen,
   ExitScreen,
   LoadPickerScreen,
   PostSaveScreen,
   SaveNameScreen,
   StartScreen,
)

TIMEOUT = 15


async def _startNewGame(pilot):
   """Dismiss the launch dialog (New Game / Restore Saved Game) that now
   appears on mount, so tests land in the same playable state they did
   before the dialog was added."""
   await pilot.click("#start-new")
   await pilot.pause()


async def _play(commands):
   app = ChainsOfIvyApp()
   async with app.run_test() as pilot:
      await _startNewGame(pilot)
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


def test_tuimain_save_shows_dialog_and_no_cancels(tmp_path, monkeypatch):
   monkeypatch.chdir(tmp_path)

   async def _play_save_then_cancel():
      app = ChainsOfIvyApp()
      async with app.run_test() as pilot:
         await _startNewGame(pilot)
         log = app.query_one("#log", RichLog)

         await pilot.click("#command")
         await pilot.press(*tuple("save"))
         await pilot.press("enter")
         await pilot.pause()

         assert isinstance(app.screen, ConfirmScreen)

         await pilot.click("#confirm-no")
         await pilot.pause()

         return app, "\n".join(strip.text for strip in log.lines)

   app, output = asyncio.run(asyncio.wait_for(_play_save_then_cancel(), TIMEOUT))

   assert "save is cancelled." in output
   assert not (tmp_path / "game.dat").exists()
   assert not (tmp_path / "player.dat").exists()


def test_tuimain_save_confirmed_does_not_hang(tmp_path, monkeypatch):
   monkeypatch.chdir(tmp_path)

   async def _play_save_then_confirm():
      app = ChainsOfIvyApp()
      async with app.run_test() as pilot:
         await _startNewGame(pilot)
         await pilot.click("#command")
         await pilot.press(*tuple("save"))
         await pilot.press("enter")
         await pilot.pause()

         assert isinstance(app.screen, ConfirmScreen)

         await pilot.click("#confirm-yes")
         await pilot.pause()

   asyncio.run(asyncio.wait_for(_play_save_then_confirm(), TIMEOUT))

   assert (tmp_path / "game.dat").exists()
   assert (tmp_path / "player.dat").exists()


def test_tuimain_unknown_command_reports_error():
   app, output = asyncio.run(asyncio.wait_for(_play(["asdfgh"]), TIMEOUT))

   assert "I don't understand your command" in output


def test_tuimain_restart_after_death_returns_to_playable_state():
   async def _play_then_kill_then_restart():
      app = ChainsOfIvyApp()
      async with app.run_test() as pilot:
         await _startNewGame(pilot)
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


def test_tuimain_quit_shows_exit_dialog_and_cancel_resumes_play():
   async def _play_quit_then_cancel():
      app = ChainsOfIvyApp()
      async with app.run_test() as pilot:
         await _startNewGame(pilot)
         log = app.query_one("#log", RichLog)

         await pilot.click("#command")
         await pilot.press(*tuple("quit"))
         await pilot.press("enter")
         await pilot.pause()

         assert isinstance(app.screen, ExitScreen)

         await pilot.click("#exit-cancel")
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


def test_tuimain_quit_exit_without_saving_exits_app():
   async def _play_quit_then_discard():
      app = ChainsOfIvyApp()
      async with app.run_test() as pilot:
         await _startNewGame(pilot)
         await pilot.click("#command")
         await pilot.press(*tuple("quit"))
         await pilot.press("enter")
         await pilot.pause()

         assert isinstance(app.screen, ExitScreen)

         await pilot.click("#exit-discard")
         await pilot.pause()

      return app

   app = asyncio.run(asyncio.wait_for(_play_quit_then_discard(), TIMEOUT))

   assert app.is_running is False
   assert app.return_code == 0


def test_tuimain_exit_button_opens_same_exit_dialog_as_typed_quit():
   async def _click_exit_button():
      app = ChainsOfIvyApp()
      async with app.run_test() as pilot:
         await _startNewGame(pilot)

         await pilot.click("#exit-button")
         await pilot.pause()

         screenType = type(app.screen).__name__

         await pilot.click("#exit-cancel")
         await pilot.pause()

         return screenType, app.is_running

   screenType, isRunning = asyncio.run(asyncio.wait_for(_click_exit_button(), TIMEOUT))

   assert screenType == "ExitScreen"
   assert isRunning


def test_tuimain_quit_save_game_prompts_name_then_continue_keeps_playing(tmp_path, monkeypatch):
   monkeypatch.chdir(tmp_path)

   async def _play_quit_save_then_continue():
      app = ChainsOfIvyApp()
      async with app.run_test() as pilot:
         await _startNewGame(pilot)

         await pilot.click("#command")
         await pilot.press(*tuple("quit"))
         await pilot.press("enter")
         await pilot.pause()

         assert isinstance(app.screen, ExitScreen)
         await pilot.click("#exit-save")
         await pilot.pause()

         assert isinstance(app.screen, SaveNameScreen)
         await pilot.click("#save-name-input")
         await pilot.press(*tuple("My Save"))
         await pilot.press("enter")
         await pilot.pause()

         assert isinstance(app.screen, PostSaveScreen)
         await pilot.click("#post-save-continue")
         await pilot.pause()

         # Check while still inside run_test(): exiting the context manager
         # itself shuts the test harness down, so is_running would read
         # False here regardless of whether "Continue" actually kept the
         # app alive.
         return app.is_running

   isRunning = asyncio.run(asyncio.wait_for(_play_quit_save_then_continue(), TIMEOUT))

   assert isRunning
   assert (tmp_path / "saves" / "My Save.dat").exists()


def test_tuimain_quit_save_game_then_exit_stops_app(tmp_path, monkeypatch):
   monkeypatch.chdir(tmp_path)

   async def _play_quit_save_then_exit():
      app = ChainsOfIvyApp()
      async with app.run_test() as pilot:
         await _startNewGame(pilot)

         await pilot.click("#command")
         await pilot.press(*tuple("quit"))
         await pilot.press("enter")
         await pilot.pause()

         await pilot.click("#exit-save")
         await pilot.pause()

         await pilot.click("#save-name-input")
         await pilot.press(*tuple("Before Boss"))
         await pilot.press("enter")
         await pilot.pause()

         assert isinstance(app.screen, PostSaveScreen)
         await pilot.click("#post-save-exit")
         await pilot.pause()

      return app

   app = asyncio.run(asyncio.wait_for(_play_quit_save_then_exit(), TIMEOUT))

   assert app.is_running is False
   assert (tmp_path / "saves" / "Before Boss.dat").exists()


def test_tuimain_save_name_screen_rejects_blank_name(tmp_path, monkeypatch):
   monkeypatch.chdir(tmp_path)

   async def _submit_blank_name():
      app = ChainsOfIvyApp()
      async with app.run_test() as pilot:
         await _startNewGame(pilot)

         await pilot.click("#command")
         await pilot.press(*tuple("quit"))
         await pilot.press("enter")
         await pilot.pause()

         await pilot.click("#exit-save")
         await pilot.pause()

         await pilot.click("#save-name-input")
         await pilot.press("enter")
         await pilot.pause()

         errorVisible = "visible" in app.screen.query_one("#save-name-error").classes
         stillOnSaveNameScreen = isinstance(app.screen, SaveNameScreen)
         return errorVisible, stillOnSaveNameScreen

   errorVisible, stillOnSaveNameScreen = asyncio.run(asyncio.wait_for(_submit_blank_name(), TIMEOUT))

   assert errorVisible
   assert stillOnSaveNameScreen
   assert not (tmp_path / "saves").exists()


def test_tuimain_load_command_with_no_saves_shows_empty_picker(tmp_path, monkeypatch):
   monkeypatch.chdir(tmp_path)

   async def _play_load_with_no_saves():
      app = ChainsOfIvyApp()
      async with app.run_test() as pilot:
         await _startNewGame(pilot)
         log = app.query_one("#log", RichLog)

         await pilot.click("#command")
         await pilot.press(*tuple("load"))
         await pilot.press("enter")
         await pilot.pause()

         assert isinstance(app.screen, LoadPickerScreen)
         noSavesShown = len(app.screen.query("#load-picker-list Label")) == 1

         await pilot.click("#load-picker-cancel")
         await pilot.pause()

         return noSavesShown, "\n".join(strip.text for strip in log.lines)

   noSavesShown, output = asyncio.run(asyncio.wait_for(_play_load_with_no_saves(), TIMEOUT))

   assert noSavesShown
   assert "load is cancelled." in output


def test_tuimain_load_command_with_corrupted_save_reports_error_instead_of_crashing(tmp_path, monkeypatch):
   """Regression test: doNamedRestore's UnpicklingError used to propagate
   straight out of the dismiss callback and crash the whole app."""
   monkeypatch.chdir(tmp_path)
   savesDir = tmp_path / "saves"
   savesDir.mkdir()
   (savesDir / "Broken.dat").write_text("not a valid pickle file")

   async def _play_load_corrupted_save():
      app = ChainsOfIvyApp()
      async with app.run_test() as pilot:
         await _startNewGame(pilot)
         log = app.query_one("#log", RichLog)

         await pilot.click("#command")
         await pilot.press(*tuple("load"))
         await pilot.press("enter")
         await pilot.pause()

         assert isinstance(app.screen, LoadPickerScreen)
         await pilot.click("#load-pick-0")
         await pilot.pause()

         assert isinstance(app.screen, ConfirmScreen)
         await pilot.click("#confirm-yes")
         await pilot.pause()

         return app.is_running, "\n".join(strip.text for strip in log.lines)

   isRunning, output = asyncio.run(asyncio.wait_for(_play_load_corrupted_save(), TIMEOUT))

   assert isRunning
   assert "could not be loaded" in output


def test_tuimain_start_screen_restore_with_corrupted_save_falls_back_to_new_game(tmp_path, monkeypatch):
   monkeypatch.chdir(tmp_path)
   savesDir = tmp_path / "saves"
   savesDir.mkdir()
   (savesDir / "Broken.dat").write_text("not a valid pickle file")

   async def _restore_corrupted_save():
      app = ChainsOfIvyApp()
      async with app.run_test() as pilot:
         assert isinstance(app.screen, StartScreen)

         await pilot.click("#start-restore")
         await pilot.pause()

         assert isinstance(app.screen, LoadPickerScreen)
         await pilot.click("#load-pick-0")
         await pilot.pause()

         return app

   app = asyncio.run(asyncio.wait_for(_restore_corrupted_save(), TIMEOUT))

   assert app.player is not None
   assert app.currentRoom.getTitle() == "Chorley Park Study"


def test_tuimain_start_screen_escape_starts_new_game():
   async def _press_escape_at_launch():
      app = ChainsOfIvyApp()
      async with app.run_test() as pilot:
         await pilot.press("escape")
         await pilot.pause()
         return app.player is not None, app.currentRoom

   hasPlayer, room = asyncio.run(asyncio.wait_for(_press_escape_at_launch(), TIMEOUT))

   assert hasPlayer
   assert room.getTitle() == "Chorley Park Study"


def test_tuimain_load_command_picks_and_restores_named_save(tmp_path, monkeypatch):
   monkeypatch.chdir(tmp_path)

   async def _save_move_then_load():
      app = ChainsOfIvyApp()
      async with app.run_test() as pilot:
         await _startNewGame(pilot)

         # Save the starting room under a name.
         await pilot.click("#command")
         await pilot.press(*tuple("quit"))
         await pilot.press("enter")
         await pilot.pause()
         await pilot.click("#exit-save")
         await pilot.pause()
         await pilot.click("#save-name-input")
         await pilot.press(*tuple("Study Snapshot"))
         await pilot.press("enter")
         await pilot.pause()
         await pilot.click("#post-save-continue")
         await pilot.pause()

         # Move away from the saved room.
         await pilot.click("#command")
         await pilot.press(*tuple("d"))
         await pilot.press("enter")
         await pilot.pause()
         assert app.currentRoom.getTitle() == "Chorley Park Library Hall"

         # Load the named save back.
         await pilot.click("#command")
         await pilot.press(*tuple("load"))
         await pilot.press("enter")
         await pilot.pause()

         assert isinstance(app.screen, LoadPickerScreen)
         await pilot.click("#load-pick-0")
         await pilot.pause()

         assert isinstance(app.screen, ConfirmScreen)
         await pilot.click("#confirm-yes")
         await pilot.pause()

         return app

   app = asyncio.run(asyncio.wait_for(_save_move_then_load(), TIMEOUT))

   assert app.currentRoom.getTitle() == "Chorley Park Study"


def test_tuimain_start_screen_shows_banner_and_new_game_starts_playable():
   """The banner shows the rendered game_banner.png as half-block art when
   Pillow is available, or falls back to plain "Chains of Ivy" text
   otherwise - either way it must be non-empty and New Game must work."""
   async def _check_start_screen():
      app = ChainsOfIvyApp()
      async with app.run_test() as pilot:
         assert isinstance(app.screen, StartScreen)
         bannerText = str(app.screen.query_one("#start-banner").renderable)

         await pilot.click("#start-new")
         await pilot.pause()

         return bannerText, app.player is not None, app.currentRoom is not None

   bannerText, hasPlayer, hasRoom = asyncio.run(asyncio.wait_for(_check_start_screen(), TIMEOUT))

   assert bannerText.strip()
   assert "Chains of Ivy" in bannerText or "▀" in bannerText
   assert hasPlayer
   assert hasRoom


def test_tuimain_render_banner_image_produces_rendered_art_or_none():
   """renderBannerImage must either return usable Rich Text art sized to
   the requested column count, or None (so callers can fall back to
   plain text) - it must never raise."""
   from tuimain import renderBannerImage, BANNER_IMAGE_PATH

   art = renderBannerImage(BANNER_IMAGE_PATH, 20)

   assert art is None or art.plain.count("\n") + 1 <= 20
   assert renderBannerImage("does/not/exist.png", 20) is None


def test_tuimain_start_screen_restore_saved_game_loads_named_save(tmp_path, monkeypatch):
   monkeypatch.chdir(tmp_path)

   async def _save_then_relaunch():
      firstApp = ChainsOfIvyApp()
      async with firstApp.run_test() as pilot:
         await _startNewGame(pilot)

         await pilot.click("#command")
         await pilot.press(*tuple("d"))
         await pilot.press("enter")
         await pilot.pause()

         firstApp.nextAction.doNamedSave(firstApp.currentRoom, firstApp.player, "Launch Save")

      secondApp = ChainsOfIvyApp()
      async with secondApp.run_test() as pilot:
         assert isinstance(secondApp.screen, StartScreen)

         await pilot.click("#start-restore")
         await pilot.pause()

         assert isinstance(secondApp.screen, LoadPickerScreen)
         await pilot.click("#load-pick-0")
         await pilot.pause()

         return secondApp

   app = asyncio.run(asyncio.wait_for(_save_then_relaunch(), TIMEOUT))

   assert app.currentRoom.getTitle() == "Chorley Park Library Hall"


def test_tuimain_start_screen_restore_with_no_saves_falls_back_to_new_game(tmp_path, monkeypatch):
   monkeypatch.chdir(tmp_path)

   async def _restore_with_no_saves():
      app = ChainsOfIvyApp()
      async with app.run_test() as pilot:
         assert isinstance(app.screen, StartScreen)

         await pilot.click("#start-restore")
         await pilot.pause()

         assert isinstance(app.screen, LoadPickerScreen)
         await pilot.click("#load-picker-cancel")
         await pilot.pause()

         return app

   app = asyncio.run(asyncio.wait_for(_restore_with_no_saves(), TIMEOUT))

   assert app.player is not None
   assert app.currentRoom.getTitle() == "Chorley Park Study"


def test_tuimain_restore_shows_dialog_and_no_cancels(tmp_path, monkeypatch):
   monkeypatch.chdir(tmp_path)

   async def _play_restore_then_cancel():
      app = ChainsOfIvyApp()
      async with app.run_test() as pilot:
         await _startNewGame(pilot)
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
         await _startNewGame(pilot)
         log = app.query_one("#log", RichLog)

         await pilot.click("#command")
         await pilot.press(*tuple("save"))
         await pilot.press("enter")
         await pilot.pause()

         assert isinstance(app.screen, ConfirmScreen)
         await pilot.click("#confirm-yes")
         await pilot.pause()

         await pilot.click("#command")
         await pilot.press(*tuple("d"))
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


def _build_pending_quest_room():
   npc = NPC("Test Quest Giver", 50, 10)
   npc.setThanksMessage("Much obliged!")
   questItem = Item("Test Trinket", "Trinket", 0)
   questItem.setQuestForNPC(npc)
   room = Room(999, "Test Quest Room", "A room for testing quests.", 0, [])
   room.addNPCtoRoom(npc)
   return room, npc, questItem


def test_tuimain_talk_quest_turn_in_shows_dialog_and_no_cancels():
   async def _play_talk_then_cancel():
      app = ChainsOfIvyApp()
      async with app.run_test() as pilot:
         await _startNewGame(pilot)
         log = app.query_one("#log", RichLog)

         room, npc, questItem = _build_pending_quest_room()
         app.currentRoom = room
         app.player.addToInventory(questItem)
         assert npc.getQuestFulfilledStatus() == "Pending"

         await pilot.click("#command")
         await pilot.press(*tuple("talk"))
         await pilot.press("enter")
         await pilot.pause()

         assert isinstance(app.screen, ConfirmScreen)

         await pilot.click("#confirm-no")
         await pilot.pause()

         return app, npc, questItem, "\n".join(strip.text for strip in log.lines)

   app, npc, questItem, output = asyncio.run(asyncio.wait_for(_play_talk_then_cancel(), TIMEOUT))

   assert "keep your business to yourself" in output
   assert npc.getQuestFulfilledStatus() == "Pending"
   assert questItem in app.player.inventory


def test_tuimain_talk_quest_turn_in_confirmed_completes_quest():
   async def _play_talk_then_confirm():
      app = ChainsOfIvyApp()
      async with app.run_test() as pilot:
         await _startNewGame(pilot)
         room, npc, questItem = _build_pending_quest_room()
         app.currentRoom = room
         app.player.addToInventory(questItem)

         await pilot.click("#command")
         await pilot.press(*tuple("talk"))
         await pilot.press("enter")
         await pilot.pause()

         assert isinstance(app.screen, ConfirmScreen)

         await pilot.click("#confirm-yes")
         await pilot.pause()

         return app, npc, questItem

   app, npc, questItem = asyncio.run(asyncio.wait_for(_play_talk_then_confirm(), TIMEOUT))

   assert npc.getQuestFulfilledStatus() == "True"
   assert questItem not in app.player.inventory
   assert app.player.experience == 50
   assert app.player.gold == 10


def test_tuimain_talk_without_pending_quest_skips_dialog():
   # If "talk" were routed through the quest confirmation dialog, this
   # message (produced deep inside doAction) would never be reached.
   app, output = asyncio.run(asyncio.wait_for(_play(["talk"]), TIMEOUT))

   assert "mutter to yourself bitterly" in output


def test_tuimain_drop_shows_dialog_and_no_cancels():
   async def _play_drop_then_cancel():
      app = ChainsOfIvyApp()
      async with app.run_test() as pilot:
         await _startNewGame(pilot)
         log = app.query_one("#log", RichLog)

         for command in ["take all", "drop Gold pocket watch"]:
            await pilot.click("#command")
            await pilot.press(*tuple(command))
            await pilot.press("enter")
            await pilot.pause()

         assert isinstance(app.screen, ConfirmScreen)

         await pilot.click("#confirm-no")
         await pilot.pause()

         return app, "\n".join(strip.text for strip in log.lines)

   app, output = asyncio.run(asyncio.wait_for(_play_drop_then_cancel(), TIMEOUT))

   assert "hold onto the Gold pocket watch" in output
   assert any(item.getName() == "Gold pocket watch" for item in app.player.inventory)
   assert app.currentRoom.existsItem("Gold pocket watch") is None


def test_tuimain_drop_confirmed_removes_item():
   async def _play_drop_then_confirm():
      app = ChainsOfIvyApp()
      async with app.run_test() as pilot:
         await _startNewGame(pilot)
         log = app.query_one("#log", RichLog)

         for command in ["take all", "drop Gold pocket watch"]:
            await pilot.click("#command")
            await pilot.press(*tuple(command))
            await pilot.press("enter")
            await pilot.pause()

         assert isinstance(app.screen, ConfirmScreen)

         await pilot.click("#confirm-yes")
         await pilot.pause()

         return app, "\n".join(strip.text for strip in log.lines)

   app, output = asyncio.run(asyncio.wait_for(_play_drop_then_confirm(), TIMEOUT))

   assert "You have dropped the Gold pocket watch" in output
   assert not any(item.getName() == "Gold pocket watch" for item in app.player.inventory)
   assert app.currentRoom.existsItem("Gold pocket watch") is not None


def test_tuimain_drop_unknown_item_skips_dialog():
   # If an unowned item name were routed through the confirmation dialog,
   # this message (produced deep inside doAction) would never be reached.
   app, output = asyncio.run(asyncio.wait_for(_play(["drop nonexistent item"]), TIMEOUT))

   assert "I don't have a nonexistent item" in output


def _build_store_room():
   item = Item("Test Tonic", "Scroll", 3)
   item.setItemValue(10)
   storeKeeper = StoreKeeper("Test Merchant", "Test Shop")
   storeKeeper.setThanksMessage("Much obliged!")
   storeKeeper.addItem([item])
   room = Room(998, "Test Store Room", "A room for testing purchases.", 0, [])
   room.addStoreKeeperToRoom(storeKeeper)
   return room, storeKeeper, item


def test_tuimain_buy_shows_dialog_and_no_cancels():
   async def _play_buy_then_cancel():
      app = ChainsOfIvyApp()
      async with app.run_test() as pilot:
         await _startNewGame(pilot)
         log = app.query_one("#log", RichLog)

         room, storeKeeper, item = _build_store_room()
         app.currentRoom = room
         app.player.incrementGold(100)

         await pilot.click("#command")
         await pilot.press(*tuple("buy Test Tonic"))
         await pilot.press("enter")
         await pilot.pause()

         assert isinstance(app.screen, ConfirmScreen)

         await pilot.click("#confirm-no")
         await pilot.pause()

         return app, "\n".join(strip.text for strip in log.lines)

   app, output = asyncio.run(asyncio.wait_for(_play_buy_then_cancel(), TIMEOUT))

   assert "decide not to buy" in output
   assert app.player.getGold() == 100
   assert not any(item.getName() == "Test Tonic" for item in app.player.inventory)


def test_tuimain_buy_confirmed_completes_purchase():
   async def _play_buy_then_confirm():
      app = ChainsOfIvyApp()
      async with app.run_test() as pilot:
         await _startNewGame(pilot)
         log = app.query_one("#log", RichLog)

         room, storeKeeper, item = _build_store_room()
         app.currentRoom = room
         app.player.incrementGold(100)

         await pilot.click("#command")
         await pilot.press(*tuple("buy Test Tonic"))
         await pilot.press("enter")
         await pilot.pause()

         assert isinstance(app.screen, ConfirmScreen)

         await pilot.click("#confirm-yes")
         await pilot.pause()

         return app, "\n".join(strip.text for strip in log.lines)

   app, output = asyncio.run(asyncio.wait_for(_play_buy_then_confirm(), TIMEOUT))

   assert "sells you a Test Tonic" in output
   assert app.player.getGold() == 90
   assert any(item.getName() == "Test Tonic" for item in app.player.inventory)


def test_tuimain_buy_unknown_item_skips_dialog():
   async def _play_buy_unknown():
      app = ChainsOfIvyApp()
      async with app.run_test() as pilot:
         await _startNewGame(pilot)
         log = app.query_one("#log", RichLog)

         room, storeKeeper, item = _build_store_room()
         app.currentRoom = room

         await pilot.click("#command")
         await pilot.press(*tuple("buy nonexistent item"))
         await pilot.press("enter")
         await pilot.pause()

         return "\n".join(strip.text for strip in log.lines)

   output = asyncio.run(asyncio.wait_for(_play_buy_unknown(), TIMEOUT))

   assert "There is no nonexistent item available to buy!" in output


def test_tuimain_buy_insufficient_gold_skips_dialog():
   async def _play_buy_too_poor():
      app = ChainsOfIvyApp()
      async with app.run_test() as pilot:
         await _startNewGame(pilot)
         log = app.query_one("#log", RichLog)

         room, storeKeeper, item = _build_store_room()
         app.currentRoom = room

         await pilot.click("#command")
         await pilot.press(*tuple("buy Test Tonic"))
         await pilot.press("enter")
         await pilot.pause()

         return "\n".join(strip.text for strip in log.lines)

   output = asyncio.run(asyncio.wait_for(_play_buy_too_poor(), TIMEOUT))

   assert "You can't afford a Test Tonic with only 0 gold pieces!" in output


def _build_two_item_room():
   # A dedicated Room/Item set, rather than the shared global Study room,
   # since that singleton persists across the whole test session and
   # accumulates leftover items from earlier tests.
   weapon = Item("Test Weapon", "Weapon", 9)
   suit = Item("Test Suit", "Suit", 9)
   room = Room(996, "Test Take Room", "A room for testing the inventory panel.", 0, [])
   room.addItemToRoom(weapon)
   room.addItemToRoom(suit)
   return room, weapon, suit


def test_tuimain_inventory_panel_starts_empty():
   async def _check_empty_panel():
      app = ChainsOfIvyApp()
      async with app.run_test() as pilot:
         await _startNewGame(pilot)
         await pilot.pause()
         assert len(app.query("#inventory-empty")) == 1
         assert len(app.query(".inventory-row")) == 0

   asyncio.run(asyncio.wait_for(_check_empty_panel(), TIMEOUT))


def test_tuimain_inventory_panel_lists_items_after_take():
   async def _take_and_inspect_panel():
      app = ChainsOfIvyApp()
      async with app.run_test() as pilot:
         await _startNewGame(pilot)
         room, weapon, suit = _build_two_item_room()
         app.currentRoom = room

         await pilot.click("#command")
         await pilot.press(*tuple("take all"))
         await pilot.press("enter")
         await pilot.pause()

         rowCount = len(app.query(".inventory-row"))
         emptyCount = len(app.query("#inventory-empty"))
         useLabels = [b.label.plain for b in app.query(".inventory-item-use")]
         return rowCount, emptyCount, useLabels

   rowCount, emptyCount, useLabels = asyncio.run(asyncio.wait_for(_take_and_inspect_panel(), TIMEOUT))

   assert rowCount == 2
   assert emptyCount == 0
   assert useLabels == ["Use", "Use"]


def test_tuimain_inventory_use_button_equips_and_disables():
   async def _use_via_panel():
      app = ChainsOfIvyApp()
      async with app.run_test() as pilot:
         await _startNewGame(pilot)
         room, weapon, suit = _build_two_item_room()
         app.currentRoom = room

         await pilot.click("#command")
         await pilot.press(*tuple("take all"))
         await pilot.press("enter")
         await pilot.pause()

         # Inventory order matches take order: Test Weapon, Test Suit.
         await pilot.click("#inv-use-0")
         await pilot.pause()

         weaponName = app.player.weapon.getName() if app.player.weapon else None
         labels = [(b.label.plain, b.disabled) for b in app.query(".inventory-item-use")]
         return weaponName, labels

   weaponName, labels = asyncio.run(asyncio.wait_for(_use_via_panel(), TIMEOUT))

   assert weaponName == "Test Weapon"
   assert ("Equipped", True) in labels


def test_tuimain_inventory_drop_button_shows_dialog_and_no_cancels():
   async def _drop_via_panel_then_cancel():
      app = ChainsOfIvyApp()
      async with app.run_test() as pilot:
         await _startNewGame(pilot)
         log = app.query_one("#log", RichLog)
         room, weapon, suit = _build_two_item_room()
         app.currentRoom = room

         await pilot.click("#command")
         await pilot.press(*tuple("take all"))
         await pilot.press("enter")
         await pilot.pause()

         await pilot.click("#inv-drop-0")
         await pilot.pause()

         assert isinstance(app.screen, ConfirmScreen)

         await pilot.click("#confirm-no")
         await pilot.pause()

         hasWeapon = weapon in app.player.inventory
         rowCount = len(app.query(".inventory-row"))
         return "\n".join(strip.text for strip in log.lines), hasWeapon, rowCount

   output, hasWeapon, rowCount = asyncio.run(asyncio.wait_for(_drop_via_panel_then_cancel(), TIMEOUT))

   assert "hold onto the Test Weapon" in output
   assert hasWeapon
   assert rowCount == 2


def test_tuimain_inventory_drop_button_confirmed_clears_equipped_slot():
   async def _use_then_drop_via_panel():
      app = ChainsOfIvyApp()
      async with app.run_test() as pilot:
         await _startNewGame(pilot)
         room, weapon, suit = _build_two_item_room()
         app.currentRoom = room

         await pilot.click("#command")
         await pilot.press(*tuple("take all"))
         await pilot.press("enter")
         await pilot.pause()

         await pilot.click("#inv-use-0")
         await pilot.pause()

         await pilot.click("#inv-drop-0")
         await pilot.pause()

         assert isinstance(app.screen, ConfirmScreen)

         await pilot.click("#confirm-yes")
         await pilot.pause()

         weaponIsNone = app.player.weapon is None
         hasWeapon = weapon in app.player.inventory
         rowCount = len(app.query(".inventory-row"))
         return weaponIsNone, hasWeapon, rowCount

   weaponIsNone, hasWeapon, rowCount = asyncio.run(asyncio.wait_for(_use_then_drop_via_panel(), TIMEOUT))

   assert weaponIsNone
   assert not hasWeapon
   assert rowCount == 1


def test_tuimain_inventory_drop_button_stays_clickable_with_long_item_name():
   """Regression test: equipping an item with a long enough name wraps
   the stats pane onto an extra line, which used to squeeze the
   inventory list's visible viewport down to nothing and make its
   buttons unclickable in the default terminal size."""
   async def _use_then_drop_long_named_item():
      app = ChainsOfIvyApp()
      async with app.run_test() as pilot:
         await _startNewGame(pilot)
         weapon = Item("An Absurdly Long Ceremonial Weapon Name", "Weapon", 9)
         room = Room(995, "Test Long Name Room", "A room for testing long item names.", 0, [])
         room.addItemToRoom(weapon)
         app.currentRoom = room

         await pilot.click("#command")
         await pilot.press(*tuple("take all"))
         await pilot.press("enter")
         await pilot.pause()

         await pilot.click("#inv-use-0")
         await pilot.pause()

         clicked = await pilot.click("#inv-drop-0")
         await pilot.pause()

         return clicked, isinstance(app.screen, ConfirmScreen)

   clicked, showsConfirm = asyncio.run(asyncio.wait_for(_use_then_drop_long_named_item(), TIMEOUT))

   assert clicked
   assert showsConfirm


def test_tuimain_stats_pane_shows_and_updates_character_stats():
   async def _check_stats_pane():
      app = ChainsOfIvyApp()
      async with app.run_test() as pilot:
         await _startNewGame(pilot)
         statsPane = app.query_one("#stats-pane", Static)
         initialText = str(statsPane.renderable)

         app.player.incrementGold(25)
         app.player.hp -= 5
         app.refreshStats()
         await pilot.pause()

         updatedText = str(statsPane.renderable)
         return initialText, updatedText

   initialText, updatedText = asyncio.run(asyncio.wait_for(_check_stats_pane(), TIMEOUT))

   assert "Professor Hugo Lockchain" in initialText
   assert "Gold 0" in initialText
   assert "HP 30/30" in initialText
   assert "Gold 25" in updatedText
   assert "HP 25/30" in updatedText


def test_tuimain_direction_buttons_reflect_room_exits():
   async def _check_direction_buttons():
      app = ChainsOfIvyApp()
      async with app.run_test() as pilot:
         await _startNewGame(pilot)
         await pilot.pause()
         disabledById = {
            buttonId: app.query_one("#" + buttonId, Button).disabled
            for buttonId in ["dir-n", "dir-s", "dir-e", "dir-w", "dir-u", "dir-d"]
         }
         return disabledById

   disabledById = asyncio.run(asyncio.wait_for(_check_direction_buttons(), TIMEOUT))

   # Chorley Park Study only has a Down exit at game start.
   assert disabledById["dir-d"] is False
   assert disabledById["dir-n"] is True
   assert disabledById["dir-s"] is True
   assert disabledById["dir-e"] is True
   assert disabledById["dir-w"] is True
   assert disabledById["dir-u"] is True


def test_tuimain_direction_button_click_moves_player():
   async def _click_down():
      app = ChainsOfIvyApp()
      async with app.run_test() as pilot:
         await _startNewGame(pilot)
         log = app.query_one("#log", RichLog)

         await pilot.click("#dir-d")
         await pilot.pause()

         return app, "\n".join(strip.text for strip in log.lines)

   app, output = asyncio.run(asyncio.wait_for(_click_down(), TIMEOUT))

   assert app.currentRoom.getTitle() == "Chorley Park Library Hall"
   assert "Chorley Park Library Hall" in output


def test_tuimain_direction_button_disabled_after_dead():
   async def _kill_then_click():
      app = ChainsOfIvyApp()
      async with app.run_test() as pilot:
         await _startNewGame(pilot)
         log = app.query_one("#log", RichLog)
         app.player.hp = 0

         await pilot.click("#dir-d")
         await pilot.pause()

         return app, "\n".join(strip.text for strip in log.lines)

   app, output = asyncio.run(asyncio.wait_for(_kill_then_click(), TIMEOUT))

   assert app.currentRoom.getTitle() == "Chorley Park Study"
   assert "You have already perished" in output
