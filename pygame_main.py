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
   COLOR_BORDER,
   COLOR_TEXT,
   COLOR_TEXT_DIM,
   COLOR_ERROR,
   COLOR_HP_OK,
   COLOR_BUTTON_DISABLED,
   drawWrappedText,
   drawTopAlignedText,
   wrapParagraphs,
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


def loadCoverImage(path, targetWidth, targetHeight):
   """Loads an image scaled to fill exactly targetWidth x targetHeight,
   cropping the overflow (rather than loadScaledImage's "fit inside and
   letterbox") - for the Scene pane's full-bleed background, where the
   image should reach every edge of the panel. Returns None on a missing
   or undecodable file, same as loadScaledImage."""
   cacheKey = ("cover", path, targetWidth, targetHeight)
   if cacheKey in _imageCache:
      return _imageCache[cacheKey]

   try:
      image = pygame.image.load(path).convert_alpha()
   except (pygame.error, FileNotFoundError):
      _imageCache[cacheKey] = None
      return None

   width, height = image.get_size()
   scale = max(targetWidth / width, targetHeight / height)
   scaledSize = (max(1, int(width * scale)), max(1, int(height * scale)))
   scaled = pygame.transform.smoothscale(image, scaledSize)

   cropRect = pygame.Rect(0, 0, targetWidth, targetHeight)
   cropRect.center = scaled.get_rect().center
   cropped = scaled.subsurface(cropRect).copy()
   _imageCache[cacheKey] = cropped
   return cropped


_scrimCache = {}


def getBottomScrim(width, height, maxAlpha=210):
   """A cached vertical gradient (transparent top -> dark bottom) sized to
   sit behind the Scene pane's title/description when they're overlaid on
   room art, so the text stays legible regardless of what's in the image
   underneath. Built once per distinct size and reused - it's an
   SRCALPHA surface where every row's alpha is set individually, not
   something to redo every frame."""
   cacheKey = (width, height, maxAlpha)
   if cacheKey in _scrimCache:
      return _scrimCache[cacheKey]

   scrim = pygame.Surface((width, height), pygame.SRCALPHA)
   for y in range(height):
      alpha = int(maxAlpha * (y / max(1, height - 1)))
      pygame.draw.line(scrim, (0, 0, 0, alpha), (0, y), (width, y))
   _scrimCache[cacheKey] = scrim
   return scrim


# (action char, Room attribute name, blockedDirections label, button label)
DIRECTION_INFO = [
   ("n", "north", "North", "N"),
   ("s", "south", "South", "S"),
   ("e", "east", "East", "E"),
   ("w", "west", "West", "W"),
   ("u", "up", "Up", "Up"),
   ("d", "down", "Down", "Down"),
]

# Grid position (col, row) for each direction button, laid out as a compass
# rose - N above, S below, W/E either side of center, Up/Down flanking the
# W/E row - rather than a left-to-right list, so the shape reads as a map.
DIRECTION_GRID = {
   "n": (2, 0),
   "u": (0, 1),
   "w": (1, 1),
   "e": (3, 1),
   "d": (4, 1),
   "s": (2, 2),
}

# (Character attribute, display label) for the four equip slots shown at
# the top of the Inventory pane, so "what am I wearing" doesn't collapse
# into a single Armor Class number.
EQUIP_SLOTS = [
   ("weapon", "Weapon"),
   ("helmet", "Helmet"),
   ("suit", "Suit"),
   ("boots", "Boots"),
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
      drawWrappedText(surface, self.question, self.questionRect, getFont(15, serif=True), COLOR_TEXT)


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
      drawWrappedText(surface, "What would you like to do?", self.titleRect, getFont(15, serif=True), COLOR_TEXT)


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
      drawWrappedText(surface, "Name this save:", self.titleRect, getFont(15, serif=True), COLOR_TEXT, align="left")
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
      drawWrappedText(surface, "Game saved! Continue playing?", self.questionRect, getFont(15, serif=True), COLOR_TEXT)


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
         drawWrappedText(surface, self.banner, self.bannerRect, getFont(19, bold=True, serif=True), COLOR_TEXT)


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
      drawWrappedText(surface, "Load which saved game?", self.titleRect, getFont(15, serif=True), COLOR_TEXT, align="left")
      if self.noSavesRect:
         drawWrappedText(surface, "No saved games found.", self.noSavesRect, getFont(14),
                          COLOR_TEXT_DIM, align="left")


class StoreScreen(Modal):
   """Storekeeper dialog: welcome message, store name, current gold, and
   every item for sale with a Buy button - opened by talking to a room's
   storekeeper, replacing the old behavior of dumping the price list into
   the log and requiring "buy <item>" to be typed blind. Stays open
   across purchases (StoreKeeper.sellItem() doesn't remove the item from
   stock, so it's still there to buy again) rather than closing after
   one purchase. Buy buttons disable themselves - and their price dims -
   the moment gold on hand can't cover them; both are recomputed from the
   live Character each frame, so a purchase made via the nested Confirm
   dialog is reflected the instant it closes."""

   ROW_HEIGHT = 34
   ROW_GAP = 8
   MAX_VISIBLE_ROWS = 6

   def __init__(self, storeKeeper, character, on_buy):
      self.storeKeeper = storeKeeper
      self.character = character
      self.on_buy = on_buy

      width, padding = 480, 20
      welcomeFont = getFont(14, serif=True)
      welcomeLines = wrapParagraphs(storeKeeper.getWelcomeMessage(), welcomeFont, width - padding * 2)
      welcomeHeight = max(1, len(welcomeLines)) * welcomeFont.get_linesize()
      storeLineHeight = getFont(12).get_linesize()
      headerHeight = 16 + welcomeHeight + 8 + storeLineHeight + 14

      items = storeKeeper.itemsToSell
      visibleCount = max(1, min(len(items), self.MAX_VISIBLE_ROWS))
      height = headerHeight + visibleCount * (self.ROW_HEIGHT + self.ROW_GAP) + 60
      rect = centeredRect(width, height)
      super().__init__(rect)

      self.welcomeRect = pygame.Rect(rect.x + padding, rect.y + 16, width - padding * 2, welcomeHeight)
      self.storeLineRect = pygame.Rect(rect.x + padding, self.welcomeRect.bottom + 8,
                                        width - padding * 2, storeLineHeight)

      y = self.storeLineRect.bottom + 14
      buyWidth = 80
      self.itemRows = []
      for item in items[:self.MAX_VISIBLE_ROWS]:
         buyButton = Button((rect.right - padding - buyWidth, y, buyWidth, self.ROW_HEIGHT), "Buy",
                             on_click=lambda it=item: self.on_buy(it))
         self.widgets.append(buyButton)
         self.itemRows.append((item, buyButton))
         y += self.ROW_HEIGHT + self.ROW_GAP

      closeY = rect.bottom - 50
      self.widgets.append(Button((rect.x + padding, closeY, width - padding * 2, 40), "Close",
                                  on_click=lambda: self.dismiss(None)))

   def on_escape(self):
      self.dismiss(None)
      return True

   def draw(self, surface):
      for item, buyButton in self.itemRows:
         buyButton.enabled = self.character.getGold() >= item.getItemValue()

      super().draw(surface)

      drawTopAlignedText(surface, self.storeKeeper.getWelcomeMessage(), self.welcomeRect,
                          getFont(14, serif=True), COLOR_TEXT)

      storeLine = (self.storeKeeper.getStoreName() + "   -   Your gold: "
                   + str(self.character.getGold()))
      storeLineSurf = getFont(12).render(storeLine, True, COLOR_TEXT_DIM)
      surface.blit(storeLineSurf, self.storeLineRect.topleft)

      priceFont = getFont(13)
      for item, buyButton in self.itemRows:
         label = item.getName() + "   [" + str(item.getItemValue()) + " gold]"
         color = COLOR_TEXT if buyButton.enabled else COLOR_TEXT_DIM
         labelSurf = priceFont.render(label, True, color)
         labelY = buyButton.rect.y + (buyButton.rect.height - labelSurf.get_height()) // 2
         surface.blit(labelSurf, (self.rect.x + 20, labelY))


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

      # Left column: the Scene pane (room title + art + description) always
      # has content, unlike the old image-only pane that sat empty for
      # every room without art. It's the dominant panel now that room
      # entry no longer dumps the description into the log too (see
      # drawScenePane) - the log only needs to hold combat/event history,
      # not be a second place to read where you are. Every action is
      # reachable by mouse (Move/Here/Inventory/Menu), so there's no typed
      # command input to make room for below it - the log runs to the
      # bottom of the column instead.
      self.scenePaneRect = pygame.Rect(20, 60, 650, 520)
      self.log = ScrollLog((20, 592, 650, 208))
      iowSetViewer(self.log)

      self.directionButtons = {}
      self._buildDirectionButtons()

      # Right column: who/what is in the room (with click-to-act buttons),
      # then inventory, then movement.
      self.herePaneRect = pygame.Rect(690, 60, 390, 250)
      self.hereRows = []

      self.inventoryPaneRect = pygame.Rect(690, 322, 390, 314)
      self.inventoryButtons = []
      self.inventoryNameWidth = self.inventoryPaneRect.width - 20 - 92 - 8 - 60 - 8

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
      """Lays out N/S/E/W/Up/Down as a compass rose (DIRECTION_GRID) rather
      than a left-to-right list of six buttons, so the shape reads as a
      map - N above, S below, W/E either side of center, Up/Down flanking
      that middle row."""
      self.directionPaneRect = pygame.Rect(690, 650, 390, 150)
      rect = self.directionPaneRect
      btnWidth, btnHeight, gap = 64, 28, 8
      columns = 5
      gridWidth = columns * btnWidth + (columns - 1) * gap
      startX = rect.x + (rect.width - gridWidth) // 2
      topY = rect.y + 34

      for actionChar, _attrName, _blockedLabel, label in DIRECTION_INFO:
         col, row = DIRECTION_GRID[actionChar]
         x = startX + col * (btnWidth + gap)
         y = topY + row * (btnHeight + gap)
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
      """Dispatches an action string from a button click - Here pane's
      Talk/Attack/Take (the only callers now that every action has a
      mouse path and there's no text input left to type anything else
      into). Save/Load/New Game/Quit go straight from the Menu to their
      own confirm* methods; Use/Drop/Buy go straight from their panel's
      button to onUseItem/confirmDrop/confirmBuy. Both bypass this
      dispatcher entirely, same as before it lost its typed-command role."""
      action = rawAction.strip()
      if not action:
         return
      iowPrint("\n>>: " + action)

      if action == "talk":
         pendingNpc = self.getPendingQuestNpc()
         if pendingNpc is not None:
            self.confirmTalk(pendingNpc)
            return
         # Mirrors doAdminAction's own npc-before-storekeeper precedence:
         # a room with both would still greet its NPC(s) via the normal
         # log-based talk, same as before this dialog existed.
         if self.currentRoom and self.currentRoom.storeKeeper and not self.currentRoom.npc:
            self.openStore(self.currentRoom.storeKeeper)
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

   def openStore(self, storeKeeper):
      self.modalStack.push(
         StoreScreen(storeKeeper, self.player, lambda item: self.confirmBuy(storeKeeper, item)))

   def refreshUI(self):
      self.refreshDirections()
      self.refreshInventory()
      self.refreshHere()

   def refreshDirections(self):
      room = self.currentRoom
      for actionChar, attrName, blockedLabel, _label in DIRECTION_INFO:
         button = self.directionButtons[actionChar]
         button.enabled = bool(room) and getattr(room, attrName) is not None \
            and blockedLabel not in room.blockedDirections

   def _inventoryItemsStartY(self):
      """Y where the item-row list begins, below the title and the four
      equip-slot lines drawInventoryPane() always renders above it - kept
      as one method so the two never drift apart."""
      return self.inventoryPaneRect.y + 32 + len(EQUIP_SLOTS) * 16 + 16

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
      # Stashed for drawInventoryPane(), which clips item-name text (a
      # quest item's name plus its "-> NPC" suffix can otherwise run into
      # the buttons) to exactly this width.
      self.inventoryNameWidth = nameWidth
      y = self._inventoryItemsStartY()

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

   def refreshHere(self):
      """Rebuilds the Here pane's rows: one per NPC/storekeeper/monster/item
      in the current room, each with a button for the verb that applies to
      it (Talk/Attack/Take). Talk and Attack route through handleCommand
      the same way the typed commands do, since those actions already
      apply to everyone/everything present at once (talk() greets every
      NPC in the room; attack() swings at every monster in it) - a button
      per row is about showing who's here, not a separate per-target
      action the engine doesn't support."""
      self.hereRows = []
      room = self.currentRoom
      if not room:
         return

      rowHeight, rowGap = 34, 8
      buttonWidth = 64
      buttonX = self.herePaneRect.right - 10 - buttonWidth
      y = self.herePaneRect.y + 40

      def addRow(label, buttonLabel, callback, hpFraction=None, hpText=None):
         nonlocal y
         button = Button((buttonX, y, buttonWidth, rowHeight - 8), buttonLabel, on_click=callback)
         self.hereRows.append((label, button, hpFraction, hpText))
         y += rowHeight + rowGap

      for npc in room.npc:
         addRow(npc.getName(), "Talk", lambda: self.handleCommand("talk"))
      if room.storeKeeper:
         addRow(room.storeKeeper.getName(), "Talk", lambda: self.handleCommand("talk"))
      for monster in room.monsters:
         maxHp = monster.getMaxHP()
         fraction = max(0.0, min(1.0, monster.hp / maxHp)) if maxHp else 0.0
         hpText = str(max(0, monster.hp)) + "/" + str(maxHp)
         addRow(monster.getName(), "Attack", lambda: self.handleCommand("attack"),
                hpFraction=fraction, hpText=hpText)
      for item in room.items:
         addRow(item.getName(), "Take", lambda it=item: self.handleCommand("take " + it.getName()))

   def onUseItem(self, item):
      iowPrint("\n>>: use " + item.getName())
      self.player.useItem(item.getName())
      self.refreshUI()

   def drawStatsBar(self):
      if not self.player:
         return
      player = self.player
      # Weapon is no longer repeated here - it's shown in the Inventory
      # pane's Equip Slots block alongside helmet/suit/boots.
      statsText = (
         "Level " + str(player.level) + "   XP " + str(player.experience)
         + "   HP " + str(player.hp) + "/" + str(player.hp_max)
         + "   Might " + str(player.might) + "   Magic " + str(player.magic)
         + "   Gold " + str(player.gold) + "   AC " + str(player.getArmorClass())
      )
      statsRect = pygame.Rect(20, 4, self.adminMenu.toggleButton.rect.x - 30, 52)

      # Name reads as a heading (serif, matching the Scene pane's room
      # title) on its own line above the numbers, rather than folded into
      # the same line as everything else.
      nameFont = getFont(16, bold=True, serif=True)
      nameSurf = nameFont.render(player.getName(), True, COLOR_TEXT)
      self.screen.blit(nameSurf, (statsRect.x, statsRect.y))

      statsLineRect = pygame.Rect(statsRect.x, statsRect.y + nameSurf.get_height() + 2,
                                   statsRect.width, statsRect.height - nameSurf.get_height() - 2)
      drawWrappedText(self.screen, statsText, statsLineRect, getFont(14, bold=True), COLOR_TEXT, align="left")

   def drawScenePane(self):
      """The room title, art (when this room has any), and description -
      always has content, unlike the old image-only pane that sat empty
      for every room without art. The title is drawn here (not just
      logged) so where you are never scrolls out of view.

      When the room has art, the image fills the pane edge to edge and
      title/description sit on a dark scrim over its bottom, so the image
      is the point rather than a small illustration squeezed above the
      text. Rooms without art (most of them, currently) fall back to a
      plain surface with the text laid out top to bottom - there's
      nothing to overlay text onto without an image."""
      rect = self.scenePaneRect
      pygame.draw.rect(self.screen, COLOR_SURFACE, rect)
      if not self.currentRoom:
         pygame.draw.rect(self.screen, COLOR_BORDER, rect, width=1)
         return

      title = self.currentRoom.getTitle()
      description = self.currentRoom.description.strip()
      imagePath = ROOM_IMAGES.get(self.currentRoom.getID())
      image = loadCoverImage(imagePath, rect.width, rect.height) if imagePath else None

      if image is not None:
         self.screen.blit(image, rect.topleft)
         self._drawSceneOverlay(rect, title, description)
      else:
         self._drawScenePlain(rect, title, description)

      pygame.draw.rect(self.screen, COLOR_BORDER, rect, width=1)

   def _drawScenePlain(self, rect, title, description):
      padding = 12
      titleRect = pygame.Rect(rect.x + padding, rect.y + padding, rect.width - padding * 2, 26)
      drawTopAlignedText(self.screen, title, titleRect, getFont(19, bold=True, serif=True), COLOR_TEXT)

      descRect = pygame.Rect(rect.x + padding, titleRect.bottom + 8, rect.width - padding * 2,
                              max(0, rect.bottom - titleRect.bottom - 8 - padding))
      drawTopAlignedText(self.screen, description, descRect, getFont(15, serif=True), COLOR_TEXT)

   def _drawSceneOverlay(self, rect, title, description):
      """Sizes the scrim to the description's actual wrapped line count
      (capped at 65% of the pane's height) so a short description barely
      dims the image and a long one never buries it - text beyond the cap
      clips, the same overflow rule used elsewhere in this frontend,
      rather than shrinking the image further to make room."""
      padding, gap = 14, 6
      titleFont = getFont(20, bold=True, serif=True)
      descFont = getFont(15, serif=True)
      textWidth = rect.width - padding * 2
      titleHeight = titleFont.get_linesize()
      lineHeight = descFont.get_linesize()
      lineCount = len(wrapParagraphs(description, descFont, textWidth))

      maxScrimHeight = int(rect.height * 0.65)
      wantedHeight = padding * 2 + titleHeight + gap + lineCount * lineHeight
      scrimHeight = min(maxScrimHeight, wantedHeight)

      scrimRect = pygame.Rect(rect.x, rect.bottom - scrimHeight, rect.width, scrimHeight)
      self.screen.blit(getBottomScrim(scrimRect.width, scrimRect.height), scrimRect.topleft)

      titleRect = pygame.Rect(scrimRect.x + padding, scrimRect.y + padding, textWidth, titleHeight)
      drawTopAlignedText(self.screen, title, titleRect, titleFont, COLOR_TEXT,
                          shadowColor=COLOR_BACKGROUND)

      descRect = pygame.Rect(scrimRect.x + padding, titleRect.bottom + gap, textWidth,
                              max(0, scrimRect.bottom - padding - titleRect.bottom - gap))
      drawTopAlignedText(self.screen, description, descRect, descFont, COLOR_TEXT,
                          shadowColor=COLOR_BACKGROUND)

   def drawHerePane(self):
      """Lists NPCs, the storekeeper, monsters (with an HP bar), and items
      in the current room, each with a button for the applicable verb -
      so combat, conversation, and picking things up all have a mouse
      path, not just movement and inventory management."""
      rect = self.herePaneRect
      pygame.draw.rect(self.screen, COLOR_BACKGROUND, rect)
      pygame.draw.rect(self.screen, COLOR_BORDER, rect, width=1, border_radius=4)
      titleSurf = getFont(14, bold=True).render("Here", True, COLOR_TEXT)
      self.screen.blit(titleSurf, (rect.x + 10, rect.y + 8))

      if not self.hereRows:
         emptySurf = getFont(13).render("Nothing else here.", True, COLOR_TEXT_DIM)
         self.screen.blit(emptySurf, (rect.x + 10, rect.y + 40))
         return

      previousClip = self.screen.get_clip()
      self.screen.set_clip(rect)
      nameFont = getFont(13)
      hpFont = getFont(11)
      for label, button, hpFraction, hpText in self.hereRows:
         nameSurf = nameFont.render(label, True, COLOR_TEXT)
         nameY = button.rect.y + (button.rect.height - nameSurf.get_height()) // 2 \
            if hpFraction is None else button.rect.y - 2
         self.screen.blit(nameSurf, (rect.x + 10, nameY))

         if hpFraction is not None:
            # Fixed width (not "fill the gap up to the button") so the HP
            # number drawn after it never runs into the button regardless
            # of how long the button-adjacent gap happens to be.
            barRect = pygame.Rect(rect.x + 10, button.rect.bottom - 6, 70, 6)
            pygame.draw.rect(self.screen, COLOR_BUTTON_DISABLED, barRect, border_radius=3)
            fillRect = pygame.Rect(barRect.x, barRect.y, int(barRect.width * hpFraction), barRect.height)
            barColor = COLOR_ERROR if hpFraction < 0.3 else COLOR_HP_OK
            if fillRect.width > 0:
               pygame.draw.rect(self.screen, barColor, fillRect, border_radius=3)
            hpSurf = hpFont.render(hpText, True, COLOR_TEXT_DIM)
            self.screen.blit(hpSurf, (barRect.right + 6, barRect.y - 3))

         button.draw(self.screen)
      self.screen.set_clip(previousClip)

   def drawInventoryPane(self):
      rect = self.inventoryPaneRect
      pygame.draw.rect(self.screen, COLOR_BACKGROUND, rect)
      pygame.draw.rect(self.screen, COLOR_BORDER, rect, width=1, border_radius=4)
      titleSurf = getFont(14, bold=True).render("Inventory", True, COLOR_TEXT)
      self.screen.blit(titleSurf, (rect.x + 10, rect.y + 8))

      # Equip slots always show, even with nothing carried, since "what am
      # I wearing" is meaningful on its own rather than collapsing into a
      # single Armor Class number.
      equipFont = getFont(12)
      equipY = rect.y + 32
      player = self.player
      for attrName, label in EQUIP_SLOTS:
         equipped = getattr(player, attrName) if player else None
         text = label + ": " + (equipped.getName() if equipped else "-")
         color = COLOR_TEXT if equipped else COLOR_TEXT_DIM
         equipSurf = equipFont.render(text, True, color)
         self.screen.blit(equipSurf, (rect.x + 10, equipY))
         equipY += 16

      dividerY = equipY + 6
      pygame.draw.line(self.screen, COLOR_BORDER, (rect.x + 10, dividerY), (rect.right - 10, dividerY))

      if not self.inventoryButtons:
         emptySurf = getFont(13).render("Nothing else carried.", True, COLOR_TEXT_DIM)
         self.screen.blit(emptySurf, (rect.x + 10, self._inventoryItemsStartY()))
         return

      nameFont = getFont(13)
      nameRect = pygame.Rect(rect.x + 10, 0, self.inventoryNameWidth, 20)
      previousClip = self.screen.get_clip()
      for item, useButton, dropButton in self.inventoryButtons:
         # Quest items (still awaiting turn-in) are called out in accent
         # color with who they're for, so carrying one reads as an open
         # task rather than just another line in the pack.
         requestor = item.npcRequestor
         pendingQuest = requestor is not None and requestor.getQuestFulfilledStatus() == "Pending"
         nameText = item.getName() + ("  -> " + requestor.getName() if pendingQuest else "")
         nameColor = COLOR_ACCENT if pendingQuest else COLOR_TEXT

         nameSurf = nameFont.render(nameText, True, nameColor)
         nameY = useButton.rect.y + (useButton.rect.height - nameSurf.get_height()) // 2
         nameRect.y = nameY
         self.screen.set_clip(nameRect)
         self.screen.blit(nameSurf, (rect.x + 10, nameY))
         self.screen.set_clip(previousClip)

         useButton.draw(self.screen)
         dropButton.draw(self.screen)

   def drawDirectionPane(self):
      rect = self.directionPaneRect
      pygame.draw.rect(self.screen, COLOR_BACKGROUND, rect)
      pygame.draw.rect(self.screen, COLOR_BORDER, rect, width=1, border_radius=4)
      titleSurf = getFont(14, bold=True).render("Move", True, COLOR_TEXT)
      self.screen.blit(titleSurf, (rect.x + 10, rect.y + 8))
      for button in self.directionButtons.values():
         button.draw(self.screen)

   def draw(self):
      self.screen.fill(COLOR_BACKGROUND)
      self.drawStatsBar()
      self.drawScenePane()
      self.log.draw(self.screen)
      self.drawHerePane()
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

      self.log.handle_event(event)
      for button in self.directionButtons.values():
         button.handle_event(event)
      for _item, useButton, dropButton in self.inventoryButtons:
         useButton.handle_event(event)
         dropButton.handle_event(event)
      for _label, button, _hpFraction, _hpText in self.hereRows:
         button.handle_event(event)

   def run(self):
      while self.running:
         dt = self.clock.tick(60) / 1000.0
         for event in pygame.event.get():
            self.handleEvent(event)
         self.modalStack.update(dt)
         self.draw()
      pygame.quit()


def main():
   ChainsOfIvyPygameApp().run()


if __name__ == "__main__":
   main()
