import pytest

from engine.Character import Character
from engine.IOwrappers import iowSetViewer
from engine.Monster import Monster
from engine.PlayerAction import PlayerAction
from engine.Room import Room


def make_room(room_id=1, title="Test Room", desc="A plain room.", encounter=0):
   return Room(room_id, title, desc, encounter, generatedMonsterList=[])


def test_get_action_type_classification(fake_viewer):
   iowSetViewer(fake_viewer)
   action = PlayerAction()

   for cmd, expected in [
      ("n", "Move"), ("s", "Move"), ("e", "Move"), ("w", "Move"),
      ("u", "Move"), ("d", "Move"),
      ("look", "Admin"), ("take sword", "Admin"), ("drop sword", "Admin"),
      ("inventory", "Admin"), ("stats", "Admin"), ("use sword", "Admin"),
      ("buy sword", "Admin"), ("save", "Admin"), ("restore", "Admin"),
      ("quit", "Admin"), ("help", "Admin"), ("talk", "Admin"),
      ("attack", "Attack"),
      ("gibberish", "Bad"),
   ]:
      action.action = cmd
      assert action.getActionType() == expected, cmd


def test_move_action_succeeds_and_returns_new_room(fake_viewer):
   iowSetViewer(fake_viewer)
   room = make_room(1, "Start")
   north = make_room(2, "North Room")
   room.setAdjacentNorth(north)
   character = Character("Tester")
   action = PlayerAction()

   newRoom = action.doAction(room, character, "n")

   assert newRoom is north


def test_move_action_blocked_direction_reports_cant_go(fake_viewer):
   iowSetViewer(fake_viewer)
   room = make_room(1, "Start")
   north = make_room(2, "North Room")
   room.setAdjacentNorth(north)
   room.blockDirection("North")
   character = Character("Tester")
   action = PlayerAction()

   newRoom = action.doAction(room, character, "n")

   assert newRoom is room
   assert "You can't go that way!" in fake_viewer.lines


def test_move_action_missing_exit_reports_cant_go(fake_viewer):
   iowSetViewer(fake_viewer)
   room = make_room(1, "Start")
   character = Character("Tester")
   action = PlayerAction()

   newRoom = action.doAction(room, character, "n")

   assert newRoom is room
   assert "You can't go that way!" in fake_viewer.lines


def test_attack_with_no_monsters_reports_nothing_to_attack(fake_viewer):
   iowSetViewer(fake_viewer)
   room = make_room(1, "Empty Arena")
   character = Character("Tester")
   action = PlayerAction()

   action.doAction(room, character, "attack")

   assert "There is nothing to attack!" in fake_viewer.lines


def test_attack_defeats_monster_and_awards_rewards(fake_viewer, monkeypatch):
   iowSetViewer(fake_viewer)
   # Deterministic damage/experience rolls so the outcome isn't flaky.
   monkeypatch.setattr("engine.PlayerAction.randint", lambda a, b: b)
   monkeypatch.setattr("engine.Monster.randint", lambda a, b: b)

   room = make_room(1, "Arena")
   character = Character("Tester")
   monster = Monster(["Training Dummy", 1, 3, "flails", 10, None, 7])
   room.addMonsterToRoom(monster)
   action = PlayerAction()

   action.doAction(room, character, "attack")

   assert monster.getStatus() == "Dead"
   assert monster not in room.monsters
   assert character.gold == 7
   assert character.experience == 10


def test_do_save_prompts_in_cli_mode_and_writes_files(tmp_path, monkeypatch):
   monkeypatch.chdir(tmp_path)
   monkeypatch.setattr("engine.PlayerAction.iowInput", lambda prompt: "y")

   action = PlayerAction()
   action.doSave(make_room(1, "Start"), Character("Tester"))

   assert (tmp_path / "game.dat").exists()
   assert (tmp_path / "player.dat").exists()


def test_do_save_cli_mode_declines_without_confirmation(tmp_path, monkeypatch):
   monkeypatch.chdir(tmp_path)
   monkeypatch.setattr("engine.PlayerAction.iowInput", lambda prompt: "n")

   action = PlayerAction()
   action.doSave(make_room(1, "Start"), Character("Tester"))

   assert not (tmp_path / "game.dat").exists()


def test_do_save_under_viewer_auto_confirms_without_blocking(fake_viewer, tmp_path, monkeypatch):
   """Regression test: once a viewer/event-driven frontend (tkmain.py,
   tuimain.py) is active, doSave must not call the blocking iowInput(),
   or it hangs the whole GUI/TUI app waiting on real terminal input."""
   monkeypatch.chdir(tmp_path)
   iowSetViewer(fake_viewer)

   def boom(prompt):
      raise AssertionError("iowInput must not be called when a viewer is active")
   monkeypatch.setattr("engine.PlayerAction.iowInput", boom)

   action = PlayerAction()
   action.doSave(make_room(1, "Start"), Character("Tester"))

   assert (tmp_path / "game.dat").exists()
   assert (tmp_path / "player.dat").exists()


def test_do_restore_round_trips_saved_state(tmp_path, monkeypatch):
   monkeypatch.chdir(tmp_path)
   monkeypatch.setattr("engine.PlayerAction.iowInput", lambda prompt: "y")

   savedRoom = make_room(5, "Saved Room")
   savedCharacter = Character("Saved Hero")
   savedCharacter.incrementGold(42)
   PlayerAction().doSave(savedRoom, savedCharacter)

   restoredRoom, restoredCharacter = PlayerAction().doRestore(
      make_room(1, "Different Room"), Character("Someone Else"))

   assert restoredRoom.getID() == 5
   assert restoredCharacter.getName() == "Saved Hero"
   assert restoredCharacter.gold == 42


def test_do_restore_under_viewer_auto_confirms_without_blocking(fake_viewer, tmp_path, monkeypatch):
   monkeypatch.chdir(tmp_path)
   monkeypatch.setattr("engine.PlayerAction.iowInput", lambda prompt: "y")
   PlayerAction().doSave(make_room(9, "To Restore"), Character("Hero"))

   iowSetViewer(fake_viewer)

   def boom(prompt):
      raise AssertionError("iowInput must not be called when a viewer is active")
   monkeypatch.setattr("engine.PlayerAction.iowInput", boom)

   restoredRoom, restoredCharacter = PlayerAction().doRestore(
      make_room(1, "Other"), Character("Other"))

   assert restoredRoom.getID() == 9
   assert restoredCharacter.getName() == "Hero"


def test_do_quit_declines_in_cli_mode_without_exiting(monkeypatch):
   monkeypatch.setattr("engine.PlayerAction.iowInput", lambda prompt: "n")

   PlayerAction().doQuit()  # "n" response should not raise SystemExit


def test_do_quit_under_viewer_auto_confirms_without_blocking(fake_viewer, monkeypatch):
   iowSetViewer(fake_viewer)

   def boom(prompt):
      raise AssertionError("iowInput must not be called when a viewer is active")
   monkeypatch.setattr("engine.PlayerAction.iowInput", boom)

   with pytest.raises(SystemExit):
      PlayerAction().doQuit()
