"""Integration tests that exercise the shipped game data (csv/*.csv) via the
real content modules, rather than hand-built Room/Character objects."""

from createdMonsters import drunkenLudwig
from createdNPCs import dorian, finius, ttcAutomaton
from createdRooms import getRoomWithID
from engine.IOwrappers import iowSetViewer
from engine.PlayerAction import PlayerAction
from tuimain import initSetting


def test_starting_room_matches_shipped_content():
   room = getRoomWithID(1)
   assert room.getTitle() == "Chorley Park Study"


def test_room_adjacency_matches_shipped_data():
   room1 = getRoomWithID(1)
   room2 = getRoomWithID(2)

   assert room1.down is room2
   assert room1.north is None


def test_blocked_room_has_expected_blocked_direction():
   room7 = getRoomWithID(7)
   assert "Down" in room7.blockedDirections


def test_npcs_placed_in_expected_rooms():
   assert dorian in getRoomWithID(9).npc
   assert ttcAutomaton in getRoomWithID(7).npc


def test_storekeeper_placed_in_expected_room():
   assert getRoomWithID(12).storeKeeper is finius


def test_boss_monster_placed_with_quest_item_to_drop():
   room10 = getRoomWithID(10)
   assert drunkenLudwig in room10.monsters
   assert drunkenLudwig.itemsToDrop


def test_full_playthrough_smoke(fake_viewer):
   """End-to-end regression covering the same command sequence used to
   manually verify tuimain.py after the tkinter-to-Textual frontend swap."""
   iowSetViewer(fake_viewer)

   room, player = initSetting()
   action = PlayerAction()

   for cmd in ("look", "take all", "inventory", "stats", "d", "help"):
      room = action.doAction(room, player, cmd)

   assert player.isDead() is False
   assert room.getTitle() == "Chorley Park Library Hall"
   assert any(item.getName() == "Gold pocket watch" for item in player.inventory)
   assert any(item.getName() == "Tweed blazer" for item in player.inventory)
