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

from engine.Item import Item
from engine.NPC import NPC
from engine.Room import Room
from engine.StoreKeeper import StoreKeeper
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


def test_tuimain_save_shows_dialog_and_no_cancels(tmp_path, monkeypatch):
   monkeypatch.chdir(tmp_path)

   async def _play_save_then_cancel():
      app = ChainsOfIvyApp()
      async with app.run_test() as pilot:
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
