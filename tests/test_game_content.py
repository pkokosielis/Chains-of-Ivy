"""Integration tests that exercise the shipped game data (csv/*.csv) via the
real content modules, rather than hand-built Room/Character objects."""

from createdMonsters import drunkenLudwig
from createdNPCs import crow, dorian, finius, ttcAutomaton
from createdRooms import RoomArray, getRoomWithID
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


def test_crow_is_placed_somewhere():
   """Regression test: the crow NPC used to be defined in createdNPCs.py
   but never actually placed in any room via addNPCtoRoom."""
   assert any(crow in room.npc for room in RoomArray)


def test_every_room_is_reachable_from_the_starting_room():
   visited = set()
   queue = [getRoomWithID(1)]
   while queue:
      room = queue.pop()
      if room.getID() in visited:
         continue
      visited.add(room.getID())
      for direction in ("north", "south", "east", "west", "up", "down"):
         neighbour = getattr(room, direction)
         if neighbour is not None and neighbour.getID() not in visited:
            queue.append(neighbour)

   allRoomIds = {room.getID() for room in RoomArray}
   assert visited == allRoomIds


def test_room_titles_have_no_stray_whitespace():
   """Regression test: a stray leading space in roomList.csv's title
   field for room 10 used to print as " Rebellion House (upper floor)"
   since titles (unlike descriptions) aren't stripped before display."""
   for room in RoomArray:
      assert room.getTitle() == room.getTitle().strip(), room.getTitle()


def test_room_descriptions_do_not_promise_missing_exits():
   """Regression test: rooms 8 and 19 used to describe north/south exits
   (a subway platform's "northbound or southbound train", and boilerplate
   "Five Thieves" strip text) that didn't actually exist in the room
   graph. Room 19 is exempted here since its corrected text legitimately
   says "north" while explicitly describing that direction as a dead end."""
   exemptRoomIds = {19}
   for room in RoomArray:
      if room.getID() in exemptRoomIds:
         continue
      desc = room.description.lower()
      exists = {
         "north": room.north is not None,
         "south": room.south is not None,
         "east": room.east is not None,
         "west": room.west is not None,
      }
      for direction, hasExit in exists.items():
         if not hasExit:
            assert direction not in desc, \
               "Room %d description mentions %s but has no such exit" % (room.getID(), direction)


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
