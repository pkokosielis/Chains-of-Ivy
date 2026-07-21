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


def test_attack_defeats_every_monster_in_a_multi_monster_room(fake_viewer, monkeypatch):
   """Regression test: doAttackAction used to iterate room.monsters while
   removing dead monsters from that same list, silently skipping whichever
   monster ended up shifted into the just-vacated index."""
   iowSetViewer(fake_viewer)
   monkeypatch.setattr("engine.PlayerAction.randint", lambda a, b: b)

   room = make_room(1, "Arena")
   character = Character("Tester")
   character.might = 99
   monsters = [Monster(["M" + str(i), 1, 0, "flails", 1, None, 0]) for i in range(3)]
   for monster in monsters:
      room.addMonsterToRoom(monster)
   action = PlayerAction()

   action.doAction(room, character, "attack")

   assert all(monster.getStatus() == "Dead" for monster in monsters)
   assert room.monsters == []


def test_buy_in_room_without_storekeeper_reports_error_instead_of_crashing(fake_viewer):
   """Regression test: doAdminAction's "buy " handler used to call
   room.storeKeeper.sellItem() unconditionally, crashing with an
   AttributeError in any room without a storekeeper."""
   iowSetViewer(fake_viewer)
   room = make_room(1, "Empty Room")
   character = Character("Tester")
   action = PlayerAction()

   action.doAction(room, character, "buy sword")

   assert "There is no storekeeper here to buy from." in fake_viewer.lines


def test_generate_monster_in_room_does_not_crash_with_empty_monster_list(fake_viewer):
   """Regression test: choice() on an empty generatedMonsterList raised
   IndexError whenever the encounter roll succeeded."""
   iowSetViewer(fake_viewer)
   room = Room(1, "Empty Room", "desc", 100, generatedMonsterList=[])

   for _ in range(500):
      room.generateMonsterInRoom()

   assert room.monsters == []


def test_do_save_writes_files(tmp_path, monkeypatch):
   monkeypatch.chdir(tmp_path)

   action = PlayerAction()
   action.doSave(make_room(1, "Start"), Character("Tester"))

   assert (tmp_path / "game.dat").exists()
   assert (tmp_path / "player.dat").exists()


def test_do_restore_round_trips_saved_state(tmp_path, monkeypatch):
   monkeypatch.chdir(tmp_path)

   savedRoom = make_room(5, "Saved Room")
   savedCharacter = Character("Saved Hero")
   savedCharacter.incrementGold(42)
   PlayerAction().doSave(savedRoom, savedCharacter)

   restoredRoom, restoredCharacter = PlayerAction().doRestore(
      make_room(1, "Different Room"), Character("Someone Else"))

   assert restoredRoom.getID() == 5
   assert restoredCharacter.getName() == "Saved Hero"
   assert restoredCharacter.gold == 42


def test_do_restore_without_saved_game_reports_error(fake_viewer):
   iowSetViewer(fake_viewer)

   room, character = PlayerAction().doRestore(
      make_room(1, "Other"), Character("Other"))

   assert room.getID() == 1
   assert "Sorry, there isn't a saved game to restore." in fake_viewer.lines
