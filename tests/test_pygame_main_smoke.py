"""Headless smoke tests for the Pygame frontend.

Pygame has no OS-level input simulator like Textual's Pilot, so these
drive the app directly at the Python-call level instead: calling
app.handleCommand(...)/app.onDirectionClick(...) the same way the real
event loop would, and invoking a dialog's button on_click callbacks
directly rather than synthesizing real mouse clicks. Runs against a dummy
SDL video driver so no real window is needed - see pygame_main.py and
pygame_widgets.py for the frontend these exercise.
"""
import os

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

import pygame

from engine.Item import Item
from engine.Monster import Monster
from engine.NPC import NPC
from engine.Room import Room
from engine.StoreKeeper import StoreKeeper

from pygame_main import (
   ChainsOfIvyPygameApp,
   ConfirmScreen,
   ExitScreen,
   LoadPickerScreen,
   PostSaveScreen,
   SaveNameScreen,
   StartScreen,
)


def _startNewGame(app):
   """Dismisses the launch dialog with New Game, landing in a fresh
   playable state."""
   app.modalStack.top.widgets[0].on_click()


def _play(commands):
   app = ChainsOfIvyPygameApp()
   _startNewGame(app)
   for command in commands:
      app.handleCommand(command)
   return app, app.log.getText()


def _build_store_room():
   item = Item("Test Tonic", "Scroll", 3)
   item.setItemValue(10)
   storeKeeper = StoreKeeper("Test Merchant", "Test Shop")
   storeKeeper.setThanksMessage("Much obliged!")
   storeKeeper.addItem([item])
   room = Room(998, "Test Store Room", "A room for testing purchases.", 0, [])
   room.addStoreKeeperToRoom(storeKeeper)
   return room, storeKeeper, item


def _build_pending_quest_room():
   npc = NPC("Test Quest Giver", 50, 10)
   npc.setThanksMessage("Much obliged!")
   questItem = Item("Test Trinket", "Trinket", 0)
   questItem.setQuestForNPC(npc)
   room = Room(999, "Test Quest Room", "A room for testing quests.", 0, [])
   room.addNPCtoRoom(npc)
   return room, npc, questItem


# -- Launch / new game ---------------------------------------------------

def test_pygame_start_screen_shows_banner_and_new_game_starts_playable():
   app = ChainsOfIvyPygameApp()
   assert isinstance(app.modalStack.top, StartScreen)
   assert app.modalStack.top.banner == "Chains of Ivy"

   _startNewGame(app)

   assert not app.modalStack.active
   assert app.player is not None
   assert app.currentRoom.getTitle() == "Chorley Park Study"


def test_pygame_start_screen_escape_starts_new_game():
   app = ChainsOfIvyPygameApp()
   assert app.modalStack.top.on_escape() is True
   assert not app.modalStack.active
   assert app.player is not None


def test_pygame_start_screen_restore_with_no_saves_falls_back_to_new_game(tmp_path, monkeypatch):
   monkeypatch.chdir(tmp_path)
   app = ChainsOfIvyPygameApp()

   app.modalStack.top.widgets[1].on_click()  # Restore Saved Game
   assert isinstance(app.modalStack.top, LoadPickerScreen)
   app.modalStack.top.widgets[-1].on_click()  # Cancel (no saves listed)

   assert not app.modalStack.active
   assert app.player is not None
   assert app.currentRoom.getTitle() == "Chorley Park Study"


def test_pygame_start_screen_restore_saved_game_loads_named_save(tmp_path, monkeypatch):
   monkeypatch.chdir(tmp_path)
   firstApp = ChainsOfIvyPygameApp()
   _startNewGame(firstApp)
   firstApp.onDirectionClick("d")
   firstApp.nextAction.doNamedSave(firstApp.currentRoom, firstApp.player, "Launch Save")

   secondApp = ChainsOfIvyPygameApp()
   assert isinstance(secondApp.modalStack.top, StartScreen)
   secondApp.modalStack.top.widgets[1].on_click()  # Restore Saved Game
   assert isinstance(secondApp.modalStack.top, LoadPickerScreen)
   secondApp.modalStack.top.widgets[0].on_click()  # pick the only save

   assert not secondApp.modalStack.active
   assert secondApp.currentRoom.getTitle() == "Chorley Park Library Hall"


# -- Core loop ------------------------------------------------------------

def test_pygame_unknown_command_reports_error():
   app, output = _play(["asdfgh"])
   assert "I don't understand your command" in output


def test_pygame_direction_click_moves_player():
   app = ChainsOfIvyPygameApp()
   _startNewGame(app)
   app.onDirectionClick("d")
   assert app.currentRoom.getTitle() == "Chorley Park Library Hall"


def test_pygame_direction_buttons_reflect_room_exits():
   app = ChainsOfIvyPygameApp()
   _startNewGame(app)
   disabledById = {actionChar: not btn.enabled for actionChar, btn in app.directionButtons.items()}
   assert disabledById["n"] is True
   assert disabledById["e"] is True
   assert disabledById["w"] is True
   assert disabledById["u"] is True
   assert disabledById["d"] is False


def test_pygame_stats_bar_updates_after_action():
   app = ChainsOfIvyPygameApp()
   _startNewGame(app)
   app.player.hp = 10  # below hp_max, so the move's +1 heal is observable
   app.onDirectionClick("d")
   assert app.player.hp == 11  # incrementHitPoints(1) on move


# -- Inventory --------------------------------------------------------------

def test_pygame_inventory_panel_starts_empty():
   app = ChainsOfIvyPygameApp()
   _startNewGame(app)
   assert app.inventoryButtons == []


def test_pygame_inventory_panel_lists_items_after_take():
   app = ChainsOfIvyPygameApp()
   _startNewGame(app)
   app.handleCommand("take all")
   names = [item.getName() for item, _use, _drop in app.inventoryButtons]
   assert "Gold pocket watch" in names
   assert "Tweed blazer" in names


def test_pygame_inventory_use_button_equips_and_disables():
   app = ChainsOfIvyPygameApp()
   _startNewGame(app)
   app.handleCommand("take all")

   item, useButton, _drop = next(e for e in app.inventoryButtons if e[0].getName() == "Gold pocket watch")
   useButton.on_click()

   assert app.player.weapon is item
   _item2, useButton2, _drop2 = next(
      e for e in app.inventoryButtons if e[0].getName() == "Gold pocket watch")
   assert useButton2.enabled is False
   assert useButton2.label == "Equipped"


def test_pygame_inventory_drop_button_shows_dialog_and_no_cancels():
   app = ChainsOfIvyPygameApp()
   _startNewGame(app)
   app.handleCommand("take all")

   item, _use, dropButton = next(e for e in app.inventoryButtons if e[0].getName() == "Tweed blazer")
   dropButton.on_click()

   assert isinstance(app.modalStack.top, ConfirmScreen)
   app.modalStack.top.widgets[1].on_click()  # No

   assert not app.modalStack.active
   assert item in app.player.inventory


def test_pygame_inventory_drop_button_confirmed_removes_item():
   app = ChainsOfIvyPygameApp()
   _startNewGame(app)
   app.handleCommand("take all")

   item, _use, dropButton = next(e for e in app.inventoryButtons if e[0].getName() == "Tweed blazer")
   dropButton.on_click()
   app.modalStack.top.widgets[0].on_click()  # Yes

   assert not app.modalStack.active
   assert item not in app.player.inventory
   assert not any(i.getName() == "Tweed blazer" for i, *_ in app.inventoryButtons)


# -- Save / restore / load / quit -------------------------------------------
#
# Save Game and Load Game are the only save mechanic - there's no separate
# unnamed quick-save slot. "save" always prompts for a name (pre-filled
# with an auto-incrementing "saved-N" default so Enter alone works), and
# both "restore" and "load" open the same named-save picker.

def test_pygame_save_shows_prefilled_name_dialog_and_cancel_skips_it():
   app = ChainsOfIvyPygameApp()
   _startNewGame(app)
   app.handleCommand("save")
   top = app.modalStack.top
   assert isinstance(top, SaveNameScreen)
   assert top.nameInput.value == "saved-1"

   top.widgets[2].on_click()  # Cancel
   assert not app.modalStack.active
   assert app.nextAction.listNamedSaves() == []


def test_pygame_save_confirmed_writes_named_file(tmp_path, monkeypatch):
   monkeypatch.chdir(tmp_path)
   app = ChainsOfIvyPygameApp()
   _startNewGame(app)
   app.handleCommand("save")
   app.modalStack.top.widgets[1].on_click()  # Save, using the prefilled name
   assert (tmp_path / "saves" / "saved-1.dat").exists()


def test_pygame_save_default_name_increments_and_ignores_custom_names(tmp_path, monkeypatch):
   monkeypatch.chdir(tmp_path)
   app = ChainsOfIvyPygameApp()
   _startNewGame(app)

   app.handleCommand("save")
   app.modalStack.top.widgets[1].on_click()  # -> saved-1
   app.handleCommand("save")
   assert app.modalStack.top.nameInput.value == "saved-2"
   app.modalStack.top.widgets[1].on_click()  # -> saved-2

   app.nextAction.doNamedSave(app.currentRoom, app.player, "before-boss")

   app.handleCommand("save")
   assert app.modalStack.top.nameInput.value == "saved-3"


def test_pygame_restore_and_load_commands_both_open_the_named_picker(tmp_path, monkeypatch):
   monkeypatch.chdir(tmp_path)
   app = ChainsOfIvyPygameApp()
   _startNewGame(app)
   app.handleCommand("save")
   app.modalStack.top.widgets[1].on_click()  # -> saved-1

   app.onDirectionClick("d")
   assert app.currentRoom.getTitle() == "Chorley Park Library Hall"

   app.handleCommand("restore")
   assert isinstance(app.modalStack.top, LoadPickerScreen)
   app.modalStack.top.widgets[0].on_click()  # pick "saved-1"
   assert isinstance(app.modalStack.top, ConfirmScreen)
   app.modalStack.top.widgets[0].on_click()  # Yes

   assert app.currentRoom.getTitle() == "Chorley Park Study"


def test_pygame_quit_shows_exit_dialog_and_cancel_resumes_play():
   app = ChainsOfIvyPygameApp()
   _startNewGame(app)
   app.handleCommand("quit")
   assert isinstance(app.modalStack.top, ExitScreen)
   app.modalStack.top.widgets[2].on_click()  # Cancel
   assert not app.modalStack.active
   assert app.running is True


def test_pygame_quit_exit_without_saving_exits_app():
   app = ChainsOfIvyPygameApp()
   _startNewGame(app)
   app.handleCommand("quit")
   app.modalStack.top.widgets[1].on_click()  # Exit without saving
   assert app.running is False


def _clickMenuItem(app, label):
   app.adminMenu.toggleButton.on_click()
   button = next(b for b in app.adminMenu.itemButtons if b.label == label)
   button.on_click()


def test_pygame_admin_menu_quit_opens_same_exit_dialog_as_typed_quit():
   app = ChainsOfIvyPygameApp()
   _startNewGame(app)
   _clickMenuItem(app, "Quit")
   assert isinstance(app.modalStack.top, ExitScreen)


def test_pygame_admin_menu_toggle_opens_and_closes():
   app = ChainsOfIvyPygameApp()
   _startNewGame(app)
   assert app.adminMenu.open is False

   app.adminMenu.toggleButton.on_click()
   assert app.adminMenu.open is True

   app.adminMenu.toggleButton.on_click()
   assert app.adminMenu.open is False


def test_pygame_admin_menu_outside_click_closes_without_side_effects():
   app = ChainsOfIvyPygameApp()
   _startNewGame(app)
   app.adminMenu.toggleButton.on_click()
   assert app.adminMenu.open is True

   outsideClick = pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=1, pos=(20, 20))
   consumed = app.adminMenu.handle_event(outsideClick)

   assert consumed is True
   assert app.adminMenu.open is False
   assert not app.modalStack.active


def test_pygame_admin_menu_has_no_separate_restore_item():
   app = ChainsOfIvyPygameApp()
   _startNewGame(app)
   labels = [b.label for b in app.adminMenu.itemButtons]
   assert labels == ["New Game", "Save Game", "Load Game", "Quit"]


def test_pygame_admin_menu_save_and_load_open_expected_dialogs():
   app = ChainsOfIvyPygameApp()
   _startNewGame(app)

   _clickMenuItem(app, "Save Game")
   assert isinstance(app.modalStack.top, SaveNameScreen)
   assert app.modalStack.top.nameInput.value == "saved-1"
   app.modalStack.top.widgets[2].on_click()  # Cancel, close it
   assert not app.modalStack.active

   _clickMenuItem(app, "Load Game")
   assert isinstance(app.modalStack.top, LoadPickerScreen)


def test_pygame_admin_menu_new_game_shows_dialog_and_no_cancels():
   app = ChainsOfIvyPygameApp()
   _startNewGame(app)
   app.onDirectionClick("d")
   roomBeforeCancel = app.currentRoom.getTitle()

   _clickMenuItem(app, "New Game")
   assert isinstance(app.modalStack.top, ConfirmScreen)
   app.modalStack.top.widgets[1].on_click()  # No

   assert not app.modalStack.active
   assert app.currentRoom.getTitle() == roomBeforeCancel


def test_pygame_admin_menu_new_game_confirmed_resets_state():
   app = ChainsOfIvyPygameApp()
   _startNewGame(app)
   app.handleCommand("take all")
   app.onDirectionClick("d")
   assert app.player.inventory  # something to lose

   _clickMenuItem(app, "New Game")
   app.modalStack.top.widgets[0].on_click()  # Yes

   assert not app.modalStack.active
   assert app.player.inventory == []
   assert app.currentRoom.getTitle() == "Chorley Park Study"


def test_pygame_quit_save_game_prompts_name_then_continue_keeps_playing(tmp_path, monkeypatch):
   monkeypatch.chdir(tmp_path)
   app = ChainsOfIvyPygameApp()
   _startNewGame(app)

   app.handleCommand("quit")
   app.modalStack.top.widgets[0].on_click()  # Save Game
   assert isinstance(app.modalStack.top, SaveNameScreen)

   app.modalStack.top._trySubmit("before-the-boss")
   assert isinstance(app.modalStack.top, PostSaveScreen)

   app.modalStack.top.widgets[0].on_click()  # Continue
   assert not app.modalStack.active
   assert app.running is True
   assert (tmp_path / "saves" / "before-the-boss.dat").exists()


def test_pygame_quit_save_game_then_exit_stops_app(tmp_path, monkeypatch):
   monkeypatch.chdir(tmp_path)
   app = ChainsOfIvyPygameApp()
   _startNewGame(app)

   app.handleCommand("quit")
   app.modalStack.top.widgets[0].on_click()  # Save Game
   app.modalStack.top._trySubmit("before-the-boss")
   app.modalStack.top.widgets[1].on_click()  # Exit

   assert app.running is False


def test_pygame_save_name_screen_rejects_blank_name(tmp_path, monkeypatch):
   monkeypatch.chdir(tmp_path)
   app = ChainsOfIvyPygameApp()
   _startNewGame(app)

   app.handleCommand("quit")
   app.modalStack.top.widgets[0].on_click()
   saveScreen = app.modalStack.top
   assert isinstance(saveScreen, SaveNameScreen)

   saveScreen._trySubmit("   ")
   assert app.modalStack.top is saveScreen  # still up, rejected
   assert saveScreen.showError is True


def test_pygame_load_command_with_no_saves_shows_empty_picker(tmp_path, monkeypatch):
   monkeypatch.chdir(tmp_path)
   app = ChainsOfIvyPygameApp()
   _startNewGame(app)
   app.handleCommand("load")
   assert isinstance(app.modalStack.top, LoadPickerScreen)
   assert app.modalStack.top.noSavesRect is not None


def test_pygame_load_command_with_corrupted_save_reports_error(tmp_path, monkeypatch):
   monkeypatch.chdir(tmp_path)
   savesDir = tmp_path / "saves"
   savesDir.mkdir()
   (savesDir / "Broken.dat").write_text("not a valid pickle file")

   app = ChainsOfIvyPygameApp()
   _startNewGame(app)
   app.handleCommand("load")
   assert isinstance(app.modalStack.top, LoadPickerScreen)
   app.modalStack.top.widgets[0].on_click()  # pick "Broken"
   assert isinstance(app.modalStack.top, ConfirmScreen)
   app.modalStack.top.widgets[0].on_click()  # Yes

   assert not app.modalStack.active
   assert "could not be loaded" in app.log.getText()


def test_pygame_load_command_picks_and_restores_named_save(tmp_path, monkeypatch):
   monkeypatch.chdir(tmp_path)
   app = ChainsOfIvyPygameApp()
   _startNewGame(app)

   app.handleCommand("quit")
   app.modalStack.top.widgets[0].on_click()
   app.modalStack.top._trySubmit("Study Snapshot")
   app.modalStack.top.widgets[0].on_click()  # Continue

   app.onDirectionClick("d")
   assert app.currentRoom.getTitle() == "Chorley Park Library Hall"

   app.handleCommand("load")
   assert isinstance(app.modalStack.top, LoadPickerScreen)
   app.modalStack.top.widgets[0].on_click()
   assert isinstance(app.modalStack.top, ConfirmScreen)
   app.modalStack.top.widgets[0].on_click()

   assert app.currentRoom.getTitle() == "Chorley Park Study"


# -- Death / game over -------------------------------------------------------

def test_pygame_death_shows_game_over_dialog_and_new_game_returns_to_playable_state():
   app = ChainsOfIvyPygameApp()
   _startNewGame(app)
   app.player.hp = -5
   app.onDirectionClick("d")

   assert isinstance(app.modalStack.top, StartScreen)
   assert "GAME OVER" in app.modalStack.top.banner
   assert app.player.isDead() is True

   app.modalStack.top.widgets[0].on_click()  # New Game
   assert not app.modalStack.active
   assert app.player.isDead() is False
   assert app.currentRoom.getTitle() == "Chorley Park Study"


def test_pygame_death_dialog_exit_quits_app():
   app = ChainsOfIvyPygameApp()
   _startNewGame(app)
   app.player.hp = -5
   app.onDirectionClick("d")
   app.modalStack.top.widgets[2].on_click()  # Exit
   assert app.running is False


def test_pygame_death_dialog_restore_loads_named_save(tmp_path, monkeypatch):
   monkeypatch.chdir(tmp_path)
   app = ChainsOfIvyPygameApp()
   _startNewGame(app)
   app.nextAction.doNamedSave(app.currentRoom, app.player, "Before Death")

   app.player.hp = -5
   app.onDirectionClick("d")
   assert isinstance(app.modalStack.top, StartScreen)

   app.modalStack.top.widgets[1].on_click()  # Restore Saved Game
   assert isinstance(app.modalStack.top, LoadPickerScreen)
   app.modalStack.top.widgets[0].on_click()

   assert not app.modalStack.active
   assert app.player.isDead() is False


def test_pygame_direction_button_triggers_game_over_dialog_when_dead():
   app = ChainsOfIvyPygameApp()
   _startNewGame(app)
   app.player.hp = -5
   app.onDirectionClick("d")
   assert isinstance(app.modalStack.top, StartScreen)
   assert "GAME OVER" in app.modalStack.top.banner


# -- Talk / drop / buy --------------------------------------------------------

def test_pygame_talk_quest_turn_in_shows_dialog_and_no_cancels():
   app = ChainsOfIvyPygameApp()
   _startNewGame(app)
   room, npc, questItem = _build_pending_quest_room()
   app.currentRoom = room
   app.player.addToInventory(questItem)

   app.handleCommand("talk")
   assert isinstance(app.modalStack.top, ConfirmScreen)
   app.modalStack.top.widgets[1].on_click()  # No

   assert "keep your business to yourself" in app.log.getText()
   assert npc.getQuestFulfilledStatus() == "Pending"
   assert questItem in app.player.inventory


def test_pygame_talk_quest_turn_in_confirmed_completes_quest():
   app = ChainsOfIvyPygameApp()
   _startNewGame(app)
   room, npc, questItem = _build_pending_quest_room()
   app.currentRoom = room
   app.player.addToInventory(questItem)

   app.handleCommand("talk")
   app.modalStack.top.widgets[0].on_click()  # Yes

   assert npc.getQuestFulfilledStatus() == "True"
   assert questItem not in app.player.inventory
   assert app.player.experience == 50
   assert app.player.gold == 10


def test_pygame_talk_without_pending_quest_skips_dialog():
   app, output = _play(["talk"])
   assert "mutter to yourself bitterly" in output


def test_pygame_drop_shows_dialog_and_no_cancels():
   app = ChainsOfIvyPygameApp()
   _startNewGame(app)
   app.handleCommand("take all")

   app.handleCommand("drop Gold pocket watch")
   assert isinstance(app.modalStack.top, ConfirmScreen)
   app.modalStack.top.widgets[1].on_click()  # No

   assert "hold onto the Gold pocket watch" in app.log.getText()
   assert any(item.getName() == "Gold pocket watch" for item in app.player.inventory)


def test_pygame_drop_confirmed_removes_item():
   app = ChainsOfIvyPygameApp()
   _startNewGame(app)
   app.handleCommand("take all")

   app.handleCommand("drop Gold pocket watch")
   app.modalStack.top.widgets[0].on_click()  # Yes

   assert not any(item.getName() == "Gold pocket watch" for item in app.player.inventory)


def test_pygame_drop_unknown_item_skips_dialog():
   app, output = _play(["drop nonexistent item"])
   assert "I don't have a nonexistent item" in output


def test_pygame_buy_shows_dialog_and_no_cancels():
   app = ChainsOfIvyPygameApp()
   _startNewGame(app)
   room, storeKeeper, item = _build_store_room()
   app.currentRoom = room
   app.player.incrementGold(100)

   app.handleCommand("buy Test Tonic")
   assert isinstance(app.modalStack.top, ConfirmScreen)
   app.modalStack.top.widgets[1].on_click()  # No

   assert "decide not to buy" in app.log.getText()
   assert app.player.getGold() == 100
   assert not any(i.getName() == "Test Tonic" for i in app.player.inventory)


def test_pygame_buy_confirmed_completes_purchase():
   app = ChainsOfIvyPygameApp()
   _startNewGame(app)
   room, storeKeeper, item = _build_store_room()
   app.currentRoom = room
   app.player.incrementGold(100)

   app.handleCommand("buy Test Tonic")
   app.modalStack.top.widgets[0].on_click()  # Yes

   assert app.player.getGold() == 90
   assert any(i.getName() == "Test Tonic" for i in app.player.inventory)


def test_pygame_buy_unknown_item_skips_dialog():
   app = ChainsOfIvyPygameApp()
   _startNewGame(app)
   room, storeKeeper, item = _build_store_room()
   app.currentRoom = room

   app.handleCommand("buy nonexistent item")
   assert "There is no nonexistent item available to buy!" in app.log.getText()


def test_pygame_buy_insufficient_gold_skips_dialog():
   app = ChainsOfIvyPygameApp()
   _startNewGame(app)
   room, storeKeeper, item = _build_store_room()
   app.currentRoom = room

   app.handleCommand("buy Test Tonic")
   assert not app.modalStack.active


# -- Text wrapping ------------------------------------------------------------

def test_pygame_attack_messages_do_not_leave_orphan_short_lines():
   """Regression test: iowWrapPrint used to hard-wrap combat messages to
   80 character columns, and ScrollLog then re-wrapped that at the
   panel's actual (narrower) pixel width, routinely leaving a short
   trailing word or number alone on its own line."""
   app = ChainsOfIvyPygameApp()
   _startNewGame(app)

   room = Room(997, "Test Arena", "A room for testing combat.", 0, [])
   monster = Monster(
      ["A ferociously snarling three-headed hound", 500, 3, "snaps viciously", 10, None, 5])
   room.addMonsterToRoom(monster)
   app.currentRoom = room

   # Direction letters ("D" etc) legitimately print one-per-line, so only
   # inspect lines produced by the attacks themselves, not the exits list
   # from the starting room's earlier display.
   linesBeforeCombat = len(app.log._lines)
   for _ in range(5):
      app.handleCommand("attack")

   orphanLines = [line for line in app.log._lines[linesBeforeCombat:] if 0 < len(line) <= 3]
   assert orphanLines == []
