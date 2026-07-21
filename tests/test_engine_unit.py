from engine.Character import Character
from engine.IOwrappers import iowPrint, iowSetViewer
from engine.Item import Item
from engine.Monster import Monster
from engine.NPC import NPC
from engine.Room import Room


def make_room(room_id=1, title="Test Room", desc="A plain room.", encounter=0):
   return Room(room_id, title, desc, encounter, generatedMonsterList=[])


def test_iowprint_uses_stdout_when_no_viewer(capsys):
   iowPrint("hello")
   assert "hello" in capsys.readouterr().out


def test_iowprint_routes_to_viewer_when_set(fake_viewer):
   iowSetViewer(fake_viewer)
   iowPrint("hello")
   assert fake_viewer.lines == ["hello"]


def test_room_take_item_moves_item_to_inventory():
   room = make_room()
   character = Character("Tester")
   watch = Item("Gold pocket watch", "Weapon", 9)
   room.addItemToRoom(watch)

   room.takeItem(character, "Gold pocket watch")

   assert watch not in room.items
   assert watch in character.inventory


def test_room_take_missing_item_is_noop():
   room = make_room()
   character = Character("Tester")

   room.takeItem(character, "Nonexistent")

   assert character.inventory == []


def test_room_take_all_items():
   room = make_room()
   character = Character("Tester")
   room.addItemToRoom(Item("A", "Weapon", 1))
   room.addItemToRoom(Item("B", "Suit", 1))

   room.takeAllItems(character)

   assert room.items == []
   assert len(character.inventory) == 2


def test_room_adjacency_and_blocked_directions():
   room = make_room(1, "Middle Room")
   north = make_room(2, "North Room")
   room.setAdjacentNorth(north)
   room.blockDirection("North")

   assert room.north is north
   assert "North" in room.blockedDirections

   room.unBlockAllDirections()

   assert room.blockedDirections == []


def test_character_use_weapon_equips_it():
   character = Character("Tester")
   sword = Item("Sword", "Weapon", 5)
   character.addToInventory(sword)

   character.useItem("Sword")

   assert character.weapon is sword


def test_character_armor_class_sums_equipped_modifiers():
   character = Character("Tester")
   helmet = Item("Helmet", "Helmet", 3)
   suit = Item("Suit", "Suit", 4)
   character.addToInventory(helmet)
   character.addToInventory(suit)
   character.useItem("Helmet")
   character.useItem("Suit")

   assert character.getArmorClass() == 7


def test_character_hit_points_capped_at_max():
   character = Character("Tester")
   character.hp = character.hp_max - 1

   character.incrementHitPoints(5)

   assert character.hp == character.hp_max


def test_character_is_dead_when_hp_zero():
   character = Character("Tester")
   character.hp = 0

   assert character.isDead() is True


def test_monster_dies_when_hp_drops_to_zero_or_below():
   monster = Monster(["Test Monster", 5, 3, "bites", 10, None, 5])

   monster.subtractFromHP(10)

   assert monster.getStatus() == "Dead"


def test_npc_give_items_gives_every_reward_item(fake_viewer):
   """Regression test: giveItems used to iterate self.itemsToGive while
   removing from it, silently dropping every other reward item."""
   iowSetViewer(fake_viewer)
   npc = NPC("Rewarder", 0, 0)
   items = [Item("A", "Trinket", 0), Item("B", "Trinket", 0), Item("C", "Trinket", 0)]
   npc.addItems(items)
   room = make_room()

   npc.giveItems(room)

   assert sorted(item.getName() for item in room.items) == ["A", "B", "C"]
   assert npc.itemsToGive == []


def test_npc_say_quote_removes_every_matching_quest_item(fake_viewer):
   """Regression test: sayQuote used to iterate character.inventory while
   removing matching items from it, silently leaving some behind whenever
   a quest required 2+ items from the same NPC."""
   iowSetViewer(fake_viewer)
   npc = NPC("Quester", 10, 10)
   npc.setThanksMessage("Thanks!")
   items = [Item("A", "Trinket", 0), Item("B", "Trinket", 0), Item("C", "Trinket", 0)]
   for item in items:
      item.setQuestForNPC(npc)
   npc.setQuestPending()
   character = Character("Tester")
   for item in items:
      character.addToInventory(item)
   room = make_room()

   npc.sayQuote(character, room)

   assert character.inventory == []
   assert npc.getQuestFulfilledStatus() == "True"
