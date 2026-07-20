#!/usr/bin/python
import sys

if (sys.version_info < (3, 4)):
   print ("\n*******************************************************************\n\n")
   print ("Error starting up Chains of Ivy!!!\n\n")
   print ("Your python interpreter is too old. Retry with python version 3.4 or higher")
   print ("\n*******************************************************************\n\n")
   sys.exit(1)

from textual.app import App, ComposeResult
from textual.containers import Grid, Horizontal, Vertical, VerticalScroll
from textual.screen import ModalScreen
from textual.widgets import Header, Footer, RichLog, Input, Label, Button, Static

from engine.IOwrappers import *
from engine.PlayerAction import *
from createdMonsters import *
from createdNPCs import *
from createdRooms import *


class RichLogViewer:
   """Adapts a Textual RichLog/Input pair to the iowPrint viewer.write(msg) interface."""

   def __init__(self, logWidget, inputWidget):
      self.logWidget = logWidget
      self.inputWidget = inputWidget

   def write(self, msg):
      self.logWidget.write(msg)
      self.inputWidget.focus()


def initSetting():
   me = Character("Professor Hugo Lockchain")
   me.setScrollText("The drink of elixir mystifies you.")

   watch = Item("Gold pocket watch", "Weapon", 9)
   jacket = Item("Tweed blazer", "Suit", 9)

   # Study
   roomObj = getRoomWithID(1)
   roomObj.addItemToRoom(watch)
   roomObj.addItemToRoom(jacket)

   # Archive Library
   scotchFlask = Item("Whiskey shot", "Scroll", 3)
   roomObj = getRoomWithID(2)
   roomObj.addItemToRoom(scotchFlask)

   # Return the starting room, and the initialized character
   return [getRoomWithID(1), me]


class ConfirmScreen(ModalScreen[bool]):
   """Generic Yes/No confirmation modal dialog."""

   BINDINGS = [("escape", "cancel", "Cancel")]

   CSS = """
   ConfirmScreen {
      align: center middle;
   }

   #confirm-dialog {
      grid-size: 2;
      grid-gutter: 1 2;
      grid-rows: 1fr 3;
      padding: 1 2;
      width: 50;
      height: 9;
      border: thick $accent;
      background: $surface;
   }

   #confirm-question {
      column-span: 2;
      content-align: center middle;
   }

   ConfirmScreen Button {
      width: 100%;
   }
   """

   def __init__(self, question: str) -> None:
      super().__init__()
      self.question = question

   def compose(self) -> ComposeResult:
      yield Grid(
         Label(self.question, id="confirm-question"),
         Button("Yes", variant="error", id="confirm-yes"),
         Button("No", variant="primary", id="confirm-no"),
         id="confirm-dialog",
      )

   def on_button_pressed(self, event: Button.Pressed) -> None:
      self.dismiss(event.button.id == "confirm-yes")

   def action_cancel(self) -> None:
      self.dismiss(False)


class ChainsOfIvyApp(App):

   TITLE = "Chains of Ivy"

   CSS = """
   RichLog {
      border: round $accent;
      background: $surface;
   }

   #stats-pane {
      height: auto;
      border: round $accent;
      background: $surface;
      padding: 0 1;
      margin: 0 0 1 0;
   }

   #game-pane {
      width: 1fr;
   }

   #side-pane {
      width: 38;
   }

   #inventory-pane {
      height: 1fr;
      border: round $accent;
      background: $surface;
      padding: 0 1;
   }

   #inventory-title {
      text-style: bold;
      padding: 0 0 1 0;
   }

   #inventory-list {
      height: 1fr;
   }

   .inventory-row {
      height: auto;
      margin: 0 0 1 0;
   }

   .inventory-item-name {
      width: 1fr;
      content-align: left middle;
   }

   .inventory-item-use, .inventory-item-drop {
      width: auto;
      min-width: 7;
   }

   #direction-pane {
      height: auto;
      border: round $accent;
      background: $surface;
      padding: 0 1;
      margin: 1 0 0 0;
   }

   #direction-title {
      text-style: bold;
      padding: 0 0 1 0;
   }

   #direction-compass {
      height: auto;
   }

   #direction-updown {
      height: auto;
      margin: 1 0 0 0;
   }

   .direction-btn {
      width: 1fr;
      min-width: 5;
      margin: 0 1 0 0;
   }
   """

   # (button id, action char, Room attribute name, blockedDirections label, button label)
   DIRECTION_INFO = [
      ("dir-n", "n", "north", "North", "N"),
      ("dir-s", "s", "south", "South", "S"),
      ("dir-e", "e", "east", "East", "E"),
      ("dir-w", "w", "west", "West", "W"),
      ("dir-u", "u", "up", "Up", "Up"),
      ("dir-d", "d", "down", "Down", "Down"),
   ]

   def __init__(self):
      super().__init__()
      self.nextAction = PlayerAction()
      self.currentRoom = None
      self.player = None
      self.inventoryButtonItems = {}

   def compose(self) -> ComposeResult:
      yield Header()
      with Vertical(id="app-body"):
         yield Static(id="stats-pane")
         with Horizontal(id="main-pane"):
            with Vertical(id="game-pane"):
               yield RichLog(id="log", wrap=True, markup=False, highlight=False)
               yield Input(placeholder="What do you do?", id="command")
            with Vertical(id="side-pane"):
               with Vertical(id="inventory-pane"):
                  yield Label("Inventory", id="inventory-title")
                  yield VerticalScroll(id="inventory-list")
               with Vertical(id="direction-pane"):
                  yield Label("Move", id="direction-title")
                  with Horizontal(id="direction-compass"):
                     yield Button("N", id="dir-n", classes="direction-btn")
                     yield Button("S", id="dir-s", classes="direction-btn")
                     yield Button("E", id="dir-e", classes="direction-btn")
                     yield Button("W", id="dir-w", classes="direction-btn")
                  with Horizontal(id="direction-updown"):
                     yield Button("Up", id="dir-u", classes="direction-btn")
                     yield Button("Down", id="dir-d", classes="direction-btn")
      yield Footer()

   async def on_mount(self) -> None:
      log = self.query_one("#log", RichLog)
      command = self.query_one("#command", Input)
      iowSetViewer(RichLogViewer(log, command))

      iowPrint("Chains of Ivy\n")
      self.startNewGame()
      await self.refreshUI()
      command.focus()

   def startNewGame(self) -> None:
      self.nextAction = PlayerAction()
      initialSetting = initSetting()
      self.currentRoom = initialSetting[0]
      self.player = initialSetting[1]
      self.currentRoom.displayRoom()

   async def on_input_submitted(self, event: Input.Submitted) -> None:
      action = event.value.strip()
      event.input.value = ""
      if not action:
         return

      iowPrint("\n>>: " + action)

      if action == "quit":
         self.confirmQuit()
         return

      if action == "restore":
         self.confirmRestore()
         return

      if self.player.isDead():
         if action == "restart":
            iowPrint("You feel your soul yanked back into your body. A new adventure begins!\n")
            self.startNewGame()
            await self.refreshUI()
         else:
            iowPrint("You have already perished. Type 'restart' for a new game, "
                     "'restore' to load a saved game, or 'quit' to exit.")
         return

      if action == "save":
         self.confirmSave()
         return

      if action == "talk":
         pendingNpc = self.getPendingQuestNpc()
         if pendingNpc is not None:
            self.confirmTalk(pendingNpc)
            return

      if action[:5] == "drop ":
         item = self.player.getItemFromDescription(action[5:])
         if item is not None:
            self.confirmDrop(item)
            return

      if action[:4] == "buy ":
         storeKeeper = self.currentRoom.storeKeeper if self.currentRoom else None
         if storeKeeper is not None:
            item = storeKeeper.existsItem(action[4:])
            if item is not None and self.player.getGold() >= item.getItemValue():
               self.confirmBuy(storeKeeper, item)
               return

      await self.performAction(action)

   async def performAction(self, action: str) -> None:
      self.currentRoom = self.nextAction.doAction(self.currentRoom, self.player, action)
      await self.refreshUI()

      if self.player.isDead():
         iowPrint("\nYou have perished in battle! GAME OVER.")
         iowPrint("Type 'restart' for a new game, 'restore' to load a saved game, or 'quit' to exit.")

   def confirmQuit(self) -> None:
      def handle_response(confirmed: bool) -> None:
         if confirmed:
            iowPrint("You are vapourized into the next plane of existence... So long!")
            self.exit()
         else:
            iowPrint("Then onwards you go!")

      self.push_screen(ConfirmScreen("Are you sure you want to quit this game?"), handle_response)

   def confirmRestore(self) -> None:
      async def handle_response(confirmed: bool) -> None:
         if confirmed:
            self.currentRoom, self.player = self.nextAction.doRestore(self.currentRoom, self.player)
            await self.refreshUI()
         else:
            iowPrint("restore is cancelled.")

      self.push_screen(
         ConfirmScreen("Are you sure you want to restore the last saved game?\nCurrent progress will be lost."),
         handle_response,
      )

   def confirmSave(self) -> None:
      def handle_response(confirmed: bool) -> None:
         if confirmed:
            self.nextAction.doSave(self.currentRoom, self.player)
         else:
            iowPrint("save is cancelled.")

      self.push_screen(
         ConfirmScreen("Are you sure you want to save the current game?"),
         handle_response,
      )

   def getPendingQuestNpc(self):
      if not self.currentRoom or not self.currentRoom.npc:
         return None
      for npc in self.currentRoom.npc:
         if npc.getQuestFulfilledStatus() == "Pending":
            return npc
      return None

   def confirmTalk(self, npc) -> None:
      async def handle_response(confirmed: bool) -> None:
         if confirmed:
            self.currentRoom = self.nextAction.doAction(self.currentRoom, self.player, "talk")
            await self.refreshUI()
         else:
            iowPrint("You decide to keep your business to yourself for now.")

      self.push_screen(
         ConfirmScreen(
            "Turn in your quest item(s) to " + npc.getName() + " for "
            + str(npc.getExpToGive()) + " experience and " + str(npc.getGoldToGive()) + " gold?"
         ),
         handle_response,
      )

   def confirmDrop(self, item) -> None:
      async def handle_response(confirmed: bool) -> None:
         if confirmed:
            self.player.dropItem(self.currentRoom, item.getName())
            await self.refreshUI()
         else:
            iowPrint("You decide to hold onto the " + item.getName() + " after all.")

      self.push_screen(
         ConfirmScreen("Are you sure you want to drop the " + item.getName() + "?"),
         handle_response,
      )

   def confirmBuy(self, storeKeeper, item) -> None:
      async def handle_response(confirmed: bool) -> None:
         if confirmed:
            storeKeeper.sellItem(item.getName(), self.player, self.currentRoom)
            await self.refreshUI()
         else:
            iowPrint("You decide not to buy the " + item.getName() + " after all.")

      self.push_screen(
         ConfirmScreen("Buy the " + item.getName() + " for " + str(item.getItemValue()) + " gold?"),
         handle_response,
      )

   async def refreshInventory(self) -> None:
      container = self.query_one("#inventory-list", VerticalScroll)
      await container.remove_children()
      self.inventoryButtonItems = {}

      if not self.player or not self.player.inventory:
         await container.mount(Label("Nothing carried.", id="inventory-empty"))
         return

      rows = []
      for index, item in enumerate(self.player.inventory):
         equipped = item is self.player.weapon or item is self.player.helmet \
            or item is self.player.suit or item is self.player.boots
         useId = "inv-use-" + str(index)
         dropId = "inv-drop-" + str(index)
         self.inventoryButtonItems[useId] = item
         self.inventoryButtonItems[dropId] = item
         rows.append(Horizontal(
            Label(item.getName(), classes="inventory-item-name"),
            Button("Equipped" if equipped else "Use", id=useId, disabled=equipped,
                   classes="inventory-item-use"),
            Button("Drop", id=dropId, classes="inventory-item-drop"),
            classes="inventory-row",
         ))
      await container.mount_all(rows)

   def refreshStats(self) -> None:
      statsPane = self.query_one("#stats-pane", Static)
      if not self.player:
         statsPane.update("")
         return

      player = self.player
      weaponName = player.weapon.getName() if player.weapon else "Bare Hands"
      statsPane.update(
         "[b]" + player.getName() + "[/b]   Level " + str(player.level)
         + "   XP " + str(player.experience) + "\n"
         + "HP " + str(player.hp) + "/" + str(player.hp_max)
         + "   Might " + str(player.might) + "   Magic " + str(player.magic)
         + "   Gold " + str(player.gold) + "   AC " + str(player.getArmorClass())
         + "   Weapon: " + weaponName
      )

   def refreshDirections(self) -> None:
      room = self.currentRoom
      for buttonId, actionChar, attrName, blockedLabel, label in self.DIRECTION_INFO:
         button = self.query_one("#" + buttonId, Button)
         available = bool(room) and getattr(room, attrName) is not None \
            and blockedLabel not in room.blockedDirections
         button.disabled = not available

   async def refreshUI(self) -> None:
      await self.refreshInventory()
      self.refreshStats()
      self.refreshDirections()

   async def on_button_pressed(self, event: Button.Pressed) -> None:
      buttonId = event.button.id or ""

      if buttonId.startswith("dir-"):
         if self.player.isDead():
            iowPrint("You have already perished. Type 'restart' for a new game, "
                     "'restore' to load a saved game, or 'quit' to exit.")
            return
         directionAction = next(
            (actionChar for bId, actionChar, _, _, _ in self.DIRECTION_INFO if bId == buttonId), None
         )
         if directionAction is not None:
            iowPrint("\n>>: " + directionAction)
            await self.performAction(directionAction)
         return

      item = self.inventoryButtonItems.get(buttonId)
      if item is None:
         return

      if self.player.isDead():
         iowPrint("You have already perished. Type 'restart' for a new game, "
                  "'restore' to load a saved game, or 'quit' to exit.")
         return

      if buttonId.startswith("inv-use-"):
         iowPrint("\n>>: use " + item.getName())
         self.player.useItem(item.getName())
         await self.refreshUI()
      elif buttonId.startswith("inv-drop-"):
         self.confirmDrop(item)


def main():
   ChainsOfIvyApp().run()


if __name__ == "__main__":
   main()
