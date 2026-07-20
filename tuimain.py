#!/usr/bin/python
import sys

if (sys.version_info < (3, 4)):
   print ("\n*******************************************************************\n\n")
   print ("Error starting up Chains of Ivy!!!\n\n")
   print ("Your python interpreter is too old. Retry with python version 3.4 or higher")
   print ("\n*******************************************************************\n\n")
   sys.exit(1)

from textual.app import App, ComposeResult
from textual.containers import Grid
from textual.screen import ModalScreen
from textual.widgets import Header, Footer, RichLog, Input, Label, Button

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
   """

   def __init__(self):
      super().__init__()
      self.nextAction = PlayerAction()
      self.currentRoom = None
      self.player = None

   def compose(self) -> ComposeResult:
      yield Header()
      yield RichLog(id="log", wrap=True, markup=False, highlight=False)
      yield Input(placeholder="What do you do?", id="command")
      yield Footer()

   def on_mount(self) -> None:
      log = self.query_one("#log", RichLog)
      command = self.query_one("#command", Input)
      iowSetViewer(RichLogViewer(log, command))

      iowPrint("Chains of Ivy\n")
      self.startNewGame()
      command.focus()

   def startNewGame(self) -> None:
      self.nextAction = PlayerAction()
      initialSetting = initSetting()
      self.currentRoom = initialSetting[0]
      self.player = initialSetting[1]
      self.currentRoom.displayRoom()

   def on_input_submitted(self, event: Input.Submitted) -> None:
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

      self.currentRoom = self.nextAction.doAction(self.currentRoom, self.player, action)

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
      def handle_response(confirmed: bool) -> None:
         if confirmed:
            self.currentRoom, self.player = self.nextAction.doRestore(self.currentRoom, self.player)
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
      def handle_response(confirmed: bool) -> None:
         if confirmed:
            self.currentRoom = self.nextAction.doAction(self.currentRoom, self.player, "talk")
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
      def handle_response(confirmed: bool) -> None:
         if confirmed:
            self.player.dropItem(self.currentRoom, item.getName())
         else:
            iowPrint("You decide to hold onto the " + item.getName() + " after all.")

      self.push_screen(
         ConfirmScreen("Are you sure you want to drop the " + item.getName() + "?"),
         handle_response,
      )

   def confirmBuy(self, storeKeeper, item) -> None:
      def handle_response(confirmed: bool) -> None:
         if confirmed:
            storeKeeper.sellItem(item.getName(), self.player, self.currentRoom)
         else:
            iowPrint("You decide not to buy the " + item.getName() + " after all.")

      self.push_screen(
         ConfirmScreen("Buy the " + item.getName() + " for " + str(item.getItemValue()) + " gold?"),
         handle_response,
      )


def main():
   ChainsOfIvyApp().run()


if __name__ == "__main__":
   main()
