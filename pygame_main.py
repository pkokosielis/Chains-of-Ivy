#!/usr/bin/python
"""Pygame frontend for Chains of Ivy - the native frontend.

A desktop window built with a small hand-rolled widget toolkit
(pygame_widgets.py), so real images (room art, banner) can be shown
without fighting terminal graphics protocols or character-cell
resolution limits. The engine (engine/*.py) is untouched and
frontend-agnostic: everything routes through iowPrint/iowWrapPrint,
which just needs an object exposing write(msg) - here, a ScrollLog.
"""
import re
import sys

if (sys.version_info < (3, 8)):
   print("Chains of Ivy requires Python 3.8 or higher.")
   sys.exit(1)

import pygame

from pygame_widgets import (
   Button,
   DropdownMenu,
   TextInput,
   ScrollLog,
   Modal,
   ModalStack,
   COLOR_BACKGROUND,
   COLOR_SURFACE,
   COLOR_ACCENT,
   COLOR_TEXT,
   COLOR_TEXT_DIM,
   COLOR_ERROR,
   drawWrappedText,
   getFont,
)

from engine.IOwrappers import *
from engine.PlayerAction import *
from createdMonsters import *
from createdNPCs import *
from createdRooms import *

WINDOW_WIDTH = 1100
WINDOW_HEIGHT = 820

BANNER_IMAGE_PATH = ".images/game_banner.png"
# Maps a Room's numeric ID to the art shown for it on the main screen.
# Not every room has art yet; rooms missing from this dict simply show no
# image. Lives here, not in the engine, so engine/Room.py stays
# frontend-agnostic.
ROOM_IMAGES = {
   1: ".images/room1.png",
   2: ".images/room2.png",
}

_imageCache = {}


def loadScaledImage(path, maxWidth, maxHeight):
   """Loads an image scaled to fit within maxWidth x maxHeight, preserving
   aspect ratio. Returns None if the file is missing or can't be decoded,
   so callers can fall back to a plain panel instead of crashing - the
   same "never let a missing asset break the game" spirit as the rest of
   this frontend. Results are cached since StartScreen/room panels are
   rebuilt often (e.g. every death) but the source images don't change."""
   cacheKey = (path, maxWidth, maxHeight)
   if cacheKey in _imageCache:
      return _imageCache[cacheKey]

   try:
      image = pygame.image.load(path).convert_alpha()
   except (pygame.error, FileNotFoundError):
      _imageCache[cacheKey] = None
      return None

   width, height = image.get_size()
   scale = min(maxWidth / width, maxHeight / height)
   scaledSize = (max(1, int(width * scale)), max(1, int(height * scale)))
   scaled = pygame.transform.smoothscale(image, scaledSize)
   _imageCache[cacheKey] = scaled
   return scaled


# (action char, Room attribute name, blockedDirections label, button label)
DIRECTION_INFO = [
   ("n", "north", "North", "N"),
   ("s", "south", "South", "S"),
   ("e", "east", "East", "E"),
   ("w", "west", "West", "W"),
   ("u", "up", "Up", "Up"),
   ("d", "down", "Down", "Down"),
]


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


def centeredRect(width, height):
   return pygame.Rect((WINDOW_WIDTH - width) // 2, (WINDOW_HEIGHT - height) // 2, width, height)


class ConfirmScreen(Modal):
   """Generic Yes/No confirmation modal dialog."""

   def __init__(self, question):
      rect = centeredRect(480, 180)
      super().__init__(rect)
      self.question = question
      self.questionRect = pygame.Rect(rect.x + 20, rect.y + 16, rect.width - 40, 74)

      buttonWidth = (rect.width - 60) // 2
      buttonY = rect.bottom - 56
      self.widgets.append(Button((rect.x + 20, buttonY, buttonWidth, 40), "Yes",
                                  on_click=lambda: self.dismiss(True), variant="error"))
      self.widgets.append(Button((rect.x + 40 + buttonWidth, buttonY, buttonWidth, 40), "No",
                                  on_click=lambda: self.dismiss(False), variant="primary"))

   def on_escape(self):
      self.dismiss(False)
      return True

   def draw(self, surface):
      super().draw(surface)
      drawWrappedText(surface, self.question, self.questionRect, getFont(15), COLOR_TEXT)


class ExitScreen(Modal):
   """Exit dialog offering Save Game / Exit without saving / Cancel."""

   def __init__(self):
      rect = centeredRect(420, 240)
      super().__init__(rect)
      self.titleRect = pygame.Rect(rect.x + 20, rect.y + 16, rect.width - 40, 28)

      buttonWidth = rect.width - 40
      y = rect.y + 56
      self.widgets.append(Button((rect.x + 20, y, buttonWidth, 40), "Save Game",
                                  on_click=lambda: self.dismiss("exit-save"), variant="primary"))
      y += 50
      self.widgets.append(Button((rect.x + 20, y, buttonWidth, 40), "Exit without saving",
                                  on_click=lambda: self.dismiss("exit-discard"), variant="error"))
      y += 50
      self.widgets.append(Button((rect.x + 20, y, buttonWidth, 40), "Cancel",
                                  on_click=lambda: self.dismiss("exit-cancel")))

   def on_escape(self):
      self.dismiss("exit-cancel")
      return True

   def draw(self, surface):
      super().draw(surface)
      drawWrappedText(surface, "What would you like to do?", self.titleRect, getFont(15), COLOR_TEXT)


class SaveNameScreen(Modal):
   """Prompts for a name to save the game under. default, when given, is
   pre-filled into the name field (e.g. an auto-incrementing "saved.N" so
   saving never requires typing anything, but the name can still be
   edited first)."""

   def __init__(self, default=""):
      rect = centeredRect(460, 220)
      super().__init__(rect)
      self.titleRect = pygame.Rect(rect.x + 20, rect.y + 16, rect.width - 40, 24)
      self.errorRect = pygame.Rect(rect.x + 20, rect.y + 94, rect.width - 40, 22)
      self.showError = False

      inputRect = (rect.x + 20, rect.y + 50, rect.width - 40, 34)
      self.nameInput = TextInput(inputRect, placeholder="e.g. before-the-boss", on_submit=self._trySubmit)
      self.nameInput.value = default
      self.widgets.append(self.nameInput)

      buttonWidth = (rect.width - 60) // 2
      buttonY = rect.bottom - 56
      self.widgets.append(Button((rect.x + 20, buttonY, buttonWidth, 40), "Save",
                                  on_click=lambda: self._trySubmit(self.nameInput.value), variant="primary"))
      self.widgets.append(Button((rect.x + 40 + buttonWidth, buttonY, buttonWidth, 40), "Cancel",
                                  on_click=lambda: self.dismiss(None)))

   def _trySubmit(self, value):
      cleanName = sanitizeSaveName(value)
      if not cleanName:
         self.showError = True
         return
      self.dismiss(cleanName)

   def on_escape(self):
      self.dismiss(None)
      return True

   def draw(self, surface):
      super().draw(surface)
      drawWrappedText(surface, "Name this save:", self.titleRect, getFont(15), COLOR_TEXT, align="left")
      if self.showError:
         drawWrappedText(surface, "Please enter a valid name.", self.errorRect, getFont(12),
                          COLOR_ERROR, align="left")


class PostSaveScreen(Modal):
   """After saving, offers to continue playing or exit."""

   def __init__(self):
      rect = centeredRect(420, 160)
      super().__init__(rect)
      self.questionRect = pygame.Rect(rect.x + 20, rect.y + 16, rect.width - 40, 56)

      buttonWidth = (rect.width - 60) // 2
      buttonY = rect.bottom - 56
      self.widgets.append(Button((rect.x + 20, buttonY, buttonWidth, 40), "Continue",
                                  on_click=lambda: self.dismiss(True), variant="primary"))
      self.widgets.append(Button((rect.x + 40 + buttonWidth, buttonY, buttonWidth, 40), "Exit",
                                  on_click=lambda: self.dismiss(False), variant="error"))

   def on_escape(self):
      self.dismiss(True)
      return True

   def draw(self, surface):
      super().draw(surface)
      drawWrappedText(surface, "Game saved! Continue playing?", self.questionRect, getFont(15), COLOR_TEXT)


DEFAULT_BANNER_TEXT = "Chains of Ivy"


class StartScreen(Modal):
   """Launch/game-over dialog: choose New Game, Restore Saved Game, or Exit.

   Reused both at app startup and whenever the player dies, with the
   banner text swapped to fit the occasion. The launch screen's default
   banner renders .images/game_banner.png as a real image when it can be
   loaded, falling back to plain text otherwise; the game-over banner is
   always plain text - there's no "you died" art."""

   BUTTON_HEIGHT = 40
   BUTTON_GAP = 10

   def __init__(self, banner=DEFAULT_BANNER_TEXT):
      self.banner = banner
      self.bannerImage = loadScaledImage(BANNER_IMAGE_PATH, 440, 260) \
         if banner == DEFAULT_BANNER_TEXT else None
      bannerHeight = self.bannerImage.get_height() if self.bannerImage is not None else 90

      buttonsHeight = self.BUTTON_HEIGHT * 3 + self.BUTTON_GAP * 2
      dialogHeight = 16 + bannerHeight + 20 + buttonsHeight + 20
      rect = centeredRect(480, dialogHeight)
      super().__init__(rect)

      self.bannerRect = pygame.Rect(rect.x + 20, rect.y + 16, rect.width - 40, bannerHeight)

      buttonWidth = rect.width - 40
      y = self.bannerRect.bottom + 20
      self.widgets.append(Button((rect.x + 20, y, buttonWidth, self.BUTTON_HEIGHT), "New Game",
                                  on_click=lambda: self.dismiss("start-new"), variant="primary"))
      y += self.BUTTON_HEIGHT + self.BUTTON_GAP
      self.widgets.append(Button((rect.x + 20, y, buttonWidth, self.BUTTON_HEIGHT), "Restore Saved Game",
                                  on_click=lambda: self.dismiss("start-restore")))
      y += self.BUTTON_HEIGHT + self.BUTTON_GAP
      self.widgets.append(Button((rect.x + 20, y, buttonWidth, self.BUTTON_HEIGHT), "Exit",
                                  on_click=lambda: self.dismiss("start-exit"), variant="error"))

   def on_escape(self):
      self.dismiss("start-new")
      return True

   def draw(self, surface):
      super().draw(surface)
      if self.bannerImage is not None:
         surface.blit(self.bannerImage, self.bannerImage.get_rect(center=self.bannerRect.center))
      else:
         drawWrappedText(surface, self.banner, self.bannerRect, getFont(17, bold=True), COLOR_TEXT)


class LoadPickerScreen(Modal):
   """Lists named saves for the player to choose from."""

   MAX_VISIBLE_ROWS = 6

   def __init__(self, saveNames):
      rowHeight = 40
      visibleCount = max(1, min(len(saveNames), self.MAX_VISIBLE_ROWS))
      height = 96 + visibleCount * (rowHeight + 8) + 50
      rect = centeredRect(460, height)
      super().__init__(rect)
      self.titleRect = pygame.Rect(rect.x + 20, rect.y + 16, rect.width - 40, 24)
      self.noSavesRect = None

      y = rect.y + 50
      if not saveNames:
         self.noSavesRect = pygame.Rect(rect.x + 20, y, rect.width - 40, 24)
         y += rowHeight
      else:
         for name in saveNames[:self.MAX_VISIBLE_ROWS]:
            self.widgets.append(Button((rect.x + 20, y, rect.width - 40, rowHeight), name,
                                        on_click=lambda n=name: self.dismiss(n)))
            y += rowHeight + 8

      cancelY = rect.bottom - 50
      self.widgets.append(Button((rect.x + 20, cancelY, rect.width - 40, 40), "Cancel",
                                  on_click=lambda: self.dismiss(None)))

   def on_escape(self):
      self.dismiss(None)
      return True

   def draw(self, surface):
      super().draw(surface)
      drawWrappedText(surface, "Load which saved game?", self.titleRect, getFont(15), COLOR_TEXT, align="left")
      if self.noSavesRect:
         drawWrappedText(surface, "No saved games found.", self.noSavesRect, getFont(14),
                          COLOR_TEXT_DIM, align="left")


class ChainsOfIvyPygameApp:

   def __init__(self):
      pygame.init()
      pygame.display.set_caption("Chains of Ivy")
      self.screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
      self.clock = pygame.time.Clock()
      self.running = True

      self.nextAction = PlayerAction()
      self.currentRoom = None
      self.player = None

      self.modalStack = ModalStack()

      self.roomImagePaneRect = pygame.Rect(20, 60, 650, 440)
      self.log = ScrollLog((20, 510, 650, 244))
      iowSetViewer(self.log)

      self.commandInput = TextInput((20, 764, 650, 36), placeholder="What do you do?",
                                     on_submit=self.handleCommand)

      self.directionButtons = {}
      self._buildDirectionButtons()

      self.inventoryPaneRect = pygame.Rect(690, 60, 390, 580)
      self.inventoryButtons = []

      self.adminMenu = DropdownMenu(
         (WINDOW_WIDTH - 110, 14, 90, 34), "Menu",
         [
            ("New Game", self.confirmNewGame),
            ("Save Game", self.confirmSaveAs),
            ("Load Game", self.confirmLoad),
            ("Quit", self.confirmExit),
         ])
      self.refreshDirections()

      self.modalStack.push(StartScreen(), self.handleStartChoice)

   def _buildDirectionButtons(self):
      self.directionPaneRect = pygame.Rect(690, 650, 390, 150)
      btnWidth, btnHeight, gap = 80, 32, 8
      startX = self.directionPaneRect.x + 10
      compassY = self.directionPaneRect.y + 34
      updownY = compassY + btnHeight + gap

      for index, (actionChar, _attrName, _blockedLabel, label) in enumerate(DIRECTION_INFO):
         row, col = divmod(index, 4)
         x = startX + col * (btnWidth + gap)
         y = compassY if row == 0 else updownY
         button = Button((x, y, btnWidth, btnHeight), label,
                          on_click=lambda a=actionChar: self.onDirectionClick(a))
         self.directionButtons[actionChar] = button

   def onDirectionClick(self, actionChar):
      iowPrint("\n>>: " + actionChar)
      self.performAction(actionChar)

   def startNewGame(self):
      self.nextAction = PlayerAction()
      initialSetting = initSetting()
      self.currentRoom = initialSetting[0]
      self.player = initialSetting[1]
      self.currentRoom.displayRoom()
      self.refreshUI()

   def handleCommand(self, rawAction):
      action = rawAction.strip()
      if not action:
         return
      iowPrint("\n>>: " + action)

      if action == "quit":
         self.confirmExit()
         return

      if action in ("restore", "load"):
         self.confirmLoad()
         return

      if action == "save":
         self.confirmSaveAs()
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

      self.performAction(action)

   def performAction(self, action):
      self.currentRoom = self.nextAction.doAction(self.currentRoom, self.player, action)
      self.refreshUI()

      if self.player.isDead():
         iowPrint("\nYou have perished in battle! GAME OVER.")
         self.showGameOver()

   def finishStartup(self):
      self.refreshUI()
      self.commandInput.focused = True

   def handleStartChoice(self, choice):
      if choice == "start-restore":
         self.modalStack.push(
            LoadPickerScreen(self.nextAction.listNamedSaves()), self.handleStartRestorePick)
      elif choice == "start-exit":
         self.running = False
      else:
         self.startNewGame()
         self.finishStartup()

   def handleStartRestorePick(self, name):
      if name:
         restored = self.tryRestore(self.nextAction.doNamedRestore, None, None, name)
         if restored is not None:
            self.currentRoom, self.player = restored
      if not name or self.currentRoom is None:
         self.startNewGame()
      self.finishStartup()

   def showGameOver(self):
      self.modalStack.push(
         StartScreen("You have perished in battle!\nGAME OVER"), self.handleGameOverChoice)

   def handleGameOverChoice(self, choice):
      if choice == "start-restore":
         self.modalStack.push(
            LoadPickerScreen(self.nextAction.listNamedSaves()), self.handleGameOverRestorePick)
      elif choice == "start-exit":
         iowPrint("You are vapourized into the next plane of existence... So long!")
         self.running = False
      else:
         iowPrint("You feel your soul yanked back into your body. A new adventure begins!\n")
         self.startNewGame()
         self.finishStartup()

   def handleGameOverRestorePick(self, name):
      if not name:
         self.showGameOver()
         return
      restored = self.tryRestore(self.nextAction.doNamedRestore, self.currentRoom, self.player, name)
      if restored is None:
         self.showGameOver()
         return
      self.currentRoom, self.player = restored
      self.finishStartup()

   def tryRestore(self, restoreFn, *args):
      """Runs a PlayerAction restore/load call, reporting failure (a
      missing, corrupted, or unreadable save file) instead of letting the
      exception crash the app. Returns the [room, character] pair on
      success, or None on failure."""
      try:
         return restoreFn(*args)
      except Exception as exc:
         iowPrint("That saved game could not be loaded (" + str(exc) + ").")
         return None

   def trySave(self, saveFn, *args):
      """Runs a PlayerAction save call, reporting failure (e.g. disk full,
      permission denied, an invalid filename) instead of letting the
      exception crash the app. Returns True on success."""
      try:
         saveFn(*args)
         return True
      except Exception as exc:
         iowPrint("The game could not be saved (" + str(exc) + ").")
         return False

   def confirmExit(self):
      def handle_choice(choice):
         if choice == "exit-save":
            self.promptSaveThenExit()
         elif choice == "exit-discard":
            iowPrint("You are vapourized into the next plane of existence... So long!")
            self.running = False
         else:
            iowPrint("Then onwards you go!")

      self.modalStack.push(ExitScreen(), handle_choice)

   def promptSaveThenExit(self):
      def handle_name(name):
         if not name:
            iowPrint("Then onwards you go!")
            return

         if not self.trySave(self.nextAction.doNamedSave, self.currentRoom, self.player, name):
            return

         def handle_continue(continuePlaying):
            if not continuePlaying:
               self.running = False

         self.modalStack.push(PostSaveScreen(), handle_continue)

      self.modalStack.push(SaveNameScreen(default=self.nextDefaultSaveName()), handle_name)

   def confirmLoad(self):
      def handle_pick(name):
         if not name:
            iowPrint("load is cancelled.")
            return

         def handle_response(confirmed):
            if confirmed:
               restored = self.tryRestore(
                  self.nextAction.doNamedRestore, self.currentRoom, self.player, name)
               if restored is not None:
                  self.currentRoom, self.player = restored
               self.refreshUI()
            else:
               iowPrint("load is cancelled.")

         self.modalStack.push(
            ConfirmScreen("Load the saved game \"" + name + "\"?\nCurrent progress will be lost."),
            handle_response)

      self.modalStack.push(LoadPickerScreen(self.nextAction.listNamedSaves()), handle_pick)

   def nextDefaultSaveName(self):
      """Suggests the next "saved-N" name that isn't already taken, so
      Save Game never requires typing anything - just Enter - while still
      letting the name be edited first. Uses a hyphen rather than a dot
      since sanitizeSaveName() strips dots - a dot-based default would
      silently turn into "saved1" on disk, no longer matching what was
      shown or what this method looks for next time."""
      existingNumbers = []
      for name in self.nextAction.listNamedSaves():
         match = re.match(r"^saved-(\d+)$", name)
         if match:
            existingNumbers.append(int(match.group(1)))
      return "saved-" + str(max(existingNumbers, default=0) + 1)

   def confirmSaveAs(self):
      def handle_name(name):
         if not name:
            iowPrint("save is cancelled.")
            return
         self.trySave(self.nextAction.doNamedSave, self.currentRoom, self.player, name)

      self.modalStack.push(SaveNameScreen(default=self.nextDefaultSaveName()), handle_name)

   def confirmNewGame(self):
      def handle_response(confirmed):
         if confirmed:
            iowPrint("You feel your soul yanked back into your body. A new adventure begins!\n")
            self.startNewGame()
            self.finishStartup()
         else:
            iowPrint("new game is cancelled.")

      self.modalStack.push(
         ConfirmScreen("Are you sure you want to start a new game?\nCurrent progress will be lost."),
         handle_response)

   def getPendingQuestNpc(self):
      if not self.currentRoom or not self.currentRoom.npc:
         return None
      for npc in self.currentRoom.npc:
         if npc.getQuestFulfilledStatus() == "Pending":
            return npc
      return None

   def confirmTalk(self, npc):
      def handle_response(confirmed):
         if confirmed:
            self.currentRoom = self.nextAction.doAction(self.currentRoom, self.player, "talk")
            self.refreshUI()
         else:
            iowPrint("You decide to keep your business to yourself for now.")

      self.modalStack.push(
         ConfirmScreen(
            "Turn in your quest item(s) to " + npc.getName() + " for "
            + str(npc.getExpToGive()) + " experience and " + str(npc.getGoldToGive()) + " gold?"
         ),
         handle_response)

   def confirmDrop(self, item):
      def handle_response(confirmed):
         if confirmed:
            self.player.dropItem(self.currentRoom, item.getName())
            self.refreshUI()
         else:
            iowPrint("You decide to hold onto the " + item.getName() + " after all.")

      self.modalStack.push(
         ConfirmScreen("Are you sure you want to drop the " + item.getName() + "?"), handle_response)

   def confirmBuy(self, storeKeeper, item):
      def handle_response(confirmed):
         if confirmed:
            storeKeeper.sellItem(item.getName(), self.player, self.currentRoom)
            self.refreshUI()
         else:
            iowPrint("You decide not to buy the " + item.getName() + " after all.")

      self.modalStack.push(
         ConfirmScreen("Buy the " + item.getName() + " for " + str(item.getItemValue()) + " gold?"),
         handle_response)

   def refreshUI(self):
      self.refreshDirections()
      self.refreshInventory()

   def refreshDirections(self):
      room = self.currentRoom
      for actionChar, attrName, blockedLabel, _label in DIRECTION_INFO:
         button = self.directionButtons[actionChar]
         button.enabled = bool(room) and getattr(room, attrName) is not None \
            and blockedLabel not in room.blockedDirections

   def refreshInventory(self):
      self.inventoryButtons = []
      if not self.player or not self.player.inventory:
         return

      rowHeight, rowGap = 32, 8
      # useWidth needs to fit the longest label that button shows -
      # "Equipped", not just "Use".
      useWidth, dropWidth, buttonGap = 92, 60, 8
      x = self.inventoryPaneRect.x + 10
      nameWidth = self.inventoryPaneRect.width - 20 - useWidth - buttonGap - dropWidth - buttonGap
      y = self.inventoryPaneRect.y + 40

      for item in self.player.inventory:
         equipped = item is self.player.weapon or item is self.player.helmet \
            or item is self.player.suit or item is self.player.boots
         useX = x + nameWidth + buttonGap
         dropX = useX + useWidth + buttonGap
         useButton = Button((useX, y, useWidth, rowHeight), "Equipped" if equipped else "Use",
                             on_click=(None if equipped else (lambda it=item: self.onUseItem(it))),
                             enabled=not equipped)
         dropButton = Button((dropX, y, dropWidth, rowHeight), "Drop",
                              on_click=lambda it=item: self.confirmDrop(it))
         self.inventoryButtons.append((item, useButton, dropButton))
         y += rowHeight + rowGap

   def onUseItem(self, item):
      iowPrint("\n>>: use " + item.getName())
      self.player.useItem(item.getName())
      self.refreshUI()

   def drawStatsBar(self):
      if not self.player:
         return
      player = self.player
      weaponName = player.weapon.getName() if player.weapon else "Bare Hands"
      statsText = (
         player.getName() + "   Level " + str(player.level) + "   XP " + str(player.experience)
         + "   HP " + str(player.hp) + "/" + str(player.hp_max)
         + "   Might " + str(player.might) + "   Magic " + str(player.magic)
         + "   Gold " + str(player.gold) + "   AC " + str(player.getArmorClass())
         + "   Weapon: " + weaponName
      )
      # Wraps (rather than a fixed single-line blit) since this can run
      # longer than the space left before the admin menu button - e.g. a
      # long weapon name - and the whole top bar (y 0-60) is reserved for it.
      statsRect = pygame.Rect(20, 4, self.adminMenu.toggleButton.rect.x - 30, 52)
      drawWrappedText(self.screen, statsText, statsRect, getFont(13, bold=True), COLOR_TEXT, align="left")

   def drawRoomImagePane(self):
      rect = self.roomImagePaneRect
      pygame.draw.rect(self.screen, COLOR_SURFACE, rect)
      pygame.draw.rect(self.screen, COLOR_ACCENT, rect, width=1)

      imagePath = ROOM_IMAGES.get(self.currentRoom.getID()) if self.currentRoom else None
      if not imagePath:
         return
      image = loadScaledImage(imagePath, rect.width - 8, rect.height - 8)
      if image is not None:
         self.screen.blit(image, image.get_rect(center=rect.center))

   def drawInventoryPane(self):
      rect = self.inventoryPaneRect
      pygame.draw.rect(self.screen, COLOR_BACKGROUND, rect)
      pygame.draw.rect(self.screen, COLOR_TEXT, rect, width=1, border_radius=4)
      titleSurf = getFont(14, bold=True).render("Inventory", True, COLOR_TEXT)
      self.screen.blit(titleSurf, (rect.x + 10, rect.y + 8))

      if not self.inventoryButtons:
         emptySurf = getFont(13).render("Nothing carried.", True, COLOR_TEXT_DIM)
         self.screen.blit(emptySurf, (rect.x + 10, rect.y + 40))
         return

      nameFont = getFont(13)
      for item, useButton, dropButton in self.inventoryButtons:
         nameSurf = nameFont.render(item.getName(), True, COLOR_TEXT)
         nameY = useButton.rect.y + (useButton.rect.height - nameSurf.get_height()) // 2
         self.screen.blit(nameSurf, (rect.x + 10, nameY))
         useButton.draw(self.screen)
         dropButton.draw(self.screen)

   def drawDirectionPane(self):
      rect = self.directionPaneRect
      pygame.draw.rect(self.screen, COLOR_BACKGROUND, rect)
      pygame.draw.rect(self.screen, COLOR_TEXT, rect, width=1, border_radius=4)
      titleSurf = getFont(14, bold=True).render("Move", True, COLOR_TEXT)
      self.screen.blit(titleSurf, (rect.x + 10, rect.y + 8))
      for button in self.directionButtons.values():
         button.draw(self.screen)

   def draw(self):
      self.screen.fill(COLOR_BACKGROUND)
      self.drawStatsBar()
      self.drawRoomImagePane()
      self.log.draw(self.screen)
      self.commandInput.draw(self.screen)
      self.drawInventoryPane()
      self.drawDirectionPane()
      # Drawn last (and handled first, below) so its dropdown panel - when
      # open - visually sits on top of, and captures clicks before, the
      # rest of the main screen.
      self.adminMenu.draw(self.screen)
      self.modalStack.draw(self.screen)
      pygame.display.flip()

   def handleEvent(self, event):
      if event.type == pygame.QUIT:
         self.running = False
         return

      if self.modalStack.active:
         self.modalStack.handle_event(event)
         return

      if self.adminMenu.handle_event(event):
         return

      self.commandInput.handle_event(event)
      self.log.handle_event(event)
      for button in self.directionButtons.values():
         button.handle_event(event)
      for _item, useButton, dropButton in self.inventoryButtons:
         useButton.handle_event(event)
         dropButton.handle_event(event)

   def run(self):
      while self.running:
         dt = self.clock.tick(60) / 1000.0
         for event in pygame.event.get():
            self.handleEvent(event)
         self.commandInput.update(dt)
         self.modalStack.update(dt)
         self.draw()
      pygame.quit()


def main():
   ChainsOfIvyPygameApp().run()


if __name__ == "__main__":
   main()
