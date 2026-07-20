#!/usr/bin/python
import sys

if (sys.version_info < (3, 4)):
   print ("\n*******************************************************************\n\n")
   print ("Error starting up Chains of Ivy!!!\n\n")
   print ("Your python interpreter is too old. Retry with python version 3.4 or higher")
   print ("\n*******************************************************************\n\n")
   sys.exit(1)

from textual.app import App, ComposeResult
from textual.widgets import Header, Footer, RichLog, Input

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

      if self.player.isDead():
         if action == "restart":
            iowPrint("You feel your soul yanked back into your body. A new adventure begins!\n")
            self.startNewGame()
         elif action == "restore":
            self.currentRoom, self.player = self.nextAction.doRestore(self.currentRoom, self.player)
         elif action == "quit":
            self.nextAction.doQuit()
         else:
            iowPrint("You have already perished. Type 'restart' for a new game, "
                     "'restore' to load a saved game, or 'quit' to exit.")
         return

      self.currentRoom = self.nextAction.doAction(self.currentRoom, self.player, action)

      if self.player.isDead():
         iowPrint("\nYou have perished in battle! GAME OVER.")
         iowPrint("Type 'restart' for a new game, 'restore' to load a saved game, or 'quit' to exit.")


def main():
   ChainsOfIvyApp().run()


if __name__ == "__main__":
   main()
