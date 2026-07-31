"""Small hand-rolled widget toolkit for the Pygame frontend.

Pygame provides no GUI widgets - just a canvas and an event queue - so this
module supplies what pygame_main.py needs: clickable buttons, a
single-line text input, a scrollable text log, and a modal dialog stack
(push_modal(modal, on_dismiss) / modal.dismiss(result)) modeled on
Textual's push_screen(...)/dismiss() pattern.
"""

import pygame

COLOR_BACKGROUND = (24, 26, 32)
COLOR_SURFACE = (36, 39, 48)
# Warm brass/amber rather than the previous cool cyan, to sit alongside the
# art (lamplight, brass, mahogany) instead of fighting it. Reserved for
# focus/active state - the one thing on screen that should currently draw
# the eye - not used as a default idle-panel border; see COLOR_BORDER.
COLOR_ACCENT = (196, 154, 82)
# Idle-panel border: visible against the background without competing with
# COLOR_ACCENT's "this is focused/active" meaning.
COLOR_BORDER = (72, 76, 90)
COLOR_TEXT = (230, 230, 230)
COLOR_TEXT_DIM = (150, 155, 165)
COLOR_BUTTON = (52, 56, 68)
COLOR_BUTTON_HOVER = (68, 73, 88)
COLOR_BUTTON_DISABLED = (40, 42, 50)
COLOR_PRIMARY = (47, 99, 122)
COLOR_PRIMARY_HOVER = (60, 122, 148)
COLOR_ERROR = (150, 60, 60)
COLOR_ERROR_HOVER = (176, 74, 74)
# A healthy HP bar reads as "fine", not "this is the focused thing" - its
# own semantic color, decoupled from COLOR_ACCENT.
COLOR_HP_OK = (108, 168, 118)
COLOR_MODAL_OVERLAY = (0, 0, 0, 160)

_fontCache = {}


def getFont(size, bold=False, serif=False):
   """Returns a cached SysFont: monospace by default (for the log, stats,
   and anything tabular), or a serif face when serif=True (for room
   titles/descriptions, which read as prose rather than terminal output).
   Lazy so pygame.font doesn't need to be initialized until a widget
   actually draws."""
   key = (size, bold, serif)
   if key not in _fontCache:
      family = "georgia,garamond,dejavuserif,serif" if serif else "dejavusansmono,monospace"
      _fontCache[key] = pygame.font.SysFont(family, size, bold=bold)
   return _fontCache[key]


def wrapParagraphs(text, font, maxWidth):
   """Wraps text (which may contain literal newlines as paragraph breaks)
   to maxWidth pixels, returning the flat list of wrapped lines. Shared by
   drawWrappedText/drawTopAlignedText, and usable standalone by callers
   that need the line count before deciding how much space to give the
   text - e.g. sizing a scrim behind it."""
   lines = []
   for rawLine in text.split("\n"):
      lines.extend(wrapText(rawLine, font, maxWidth))
   return lines


def drawWrappedText(surface, text, rect, font, color, align="center"):
   """Draws word-wrapped, vertically-centered text inside rect. align is
   "center" or "left" for horizontal alignment of each line."""
   lines = wrapParagraphs(text, font, rect.width)

   lineHeight = font.get_linesize()
   y = rect.y + max(0, (rect.height - len(lines) * lineHeight) // 2)
   for line in lines:
      textSurf = font.render(line, True, color)
      x = rect.x + (rect.width - textSurf.get_width()) // 2 if align == "center" else rect.x
      surface.blit(textSurf, (x, y))
      y += lineHeight


def drawTopAlignedText(surface, text, rect, font, color, align="left", shadowColor=None):
   """Draws word-wrapped text starting at the top of rect, clipped to it,
   rather than drawWrappedText's vertical centering - for prose that
   should begin right below a heading/image rather than float in the
   middle of its box. Overflow is clipped, not scrolled. shadowColor, when
   given, draws each line offset by (1, 1) first - for text overlaid on a
   photo, where a plain flat color can vanish into a bright patch of it."""
   lines = wrapParagraphs(text, font, rect.width)

   previousClip = surface.get_clip()
   surface.set_clip(rect)
   lineHeight = font.get_linesize()
   y = rect.y
   for line in lines:
      if line:
         x = rect.x + (rect.width - font.size(line)[0]) // 2 if align == "center" else rect.x
         if shadowColor is not None:
            shadowSurf = font.render(line, True, shadowColor)
            surface.blit(shadowSurf, (x + 1, y + 1))
         textSurf = font.render(line, True, color)
         surface.blit(textSurf, (x, y))
      y += lineHeight
   surface.set_clip(previousClip)


def wrapText(text, font, maxWidth):
   """Wraps a single logical line of text to fit maxWidth pixels, breaking
   on spaces. An empty string wraps to itself (a blank line)."""
   if not text:
      return [""]

   wrapped = []
   words = text.split(" ")
   current = ""
   for word in words:
      candidate = word if not current else current + " " + word
      if font.size(candidate)[0] <= maxWidth or not current:
         current = candidate
      else:
         wrapped.append(current)
         current = word
   wrapped.append(current)
   return wrapped


class Button:
   """A clickable rectangle with a label. variant is "default", "primary",
   or "error"."""

   def __init__(self, rect, label, on_click=None, variant="default", enabled=True):
      self.rect = pygame.Rect(rect)
      self.label = label
      self.on_click = on_click
      self.variant = variant
      self.enabled = enabled
      self.hovered = False

   def handle_event(self, event):
      if not self.enabled:
         return False
      if event.type == pygame.MOUSEMOTION:
         self.hovered = self.rect.collidepoint(event.pos)
         return False
      if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
         if self.rect.collidepoint(event.pos):
            if self.on_click:
               self.on_click()
            return True
      return False

   def draw(self, surface):
      if not self.enabled:
         bgColor, textColor = COLOR_BUTTON_DISABLED, COLOR_TEXT_DIM
      elif self.variant == "primary":
         bgColor, textColor = (COLOR_PRIMARY_HOVER if self.hovered else COLOR_PRIMARY), COLOR_TEXT
      elif self.variant == "error":
         bgColor, textColor = (COLOR_ERROR_HOVER if self.hovered else COLOR_ERROR), COLOR_TEXT
      else:
         bgColor, textColor = (COLOR_BUTTON_HOVER if self.hovered else COLOR_BUTTON), COLOR_TEXT

      pygame.draw.rect(surface, bgColor, self.rect, border_radius=4)
      pygame.draw.rect(surface, COLOR_ACCENT, self.rect, width=1, border_radius=4)

      textSurf = getFont(15).render(self.label, True, textColor)
      # Clip so an unusually long label (a long save name, "Equipped",
      # etc.) can never visually bleed into whatever's drawn next to
      # this button, even though it isn't wrapped/shrunk to fit.
      previousClip = surface.get_clip()
      surface.set_clip(self.rect)
      surface.blit(textSurf, textSurf.get_rect(center=self.rect.center))
      surface.set_clip(previousClip)


class DropdownMenu:
   """A toggle button that opens a small right-aligned list of item
   buttons below it - for a handful of admin actions (new game, save,
   restore, quit) that don't warrant a full dialog of their own to pick
   between. Unlike Modal, this doesn't dim the screen or block input to
   the rest of the app; it just closes itself on an outside click, an
   item click, or Escape."""

   ITEM_HEIGHT = 32
   ITEM_GAP = 4

   def __init__(self, rect, label, items):
      """items is a list of (item_label, callback) pairs."""
      self.toggleButton = Button(rect, label, on_click=self._toggle)
      self.open = False
      self.itemButtons = []

      font = getFont(15)
      width = max(self.toggleButton.rect.width,
                  max(font.size(itemLabel)[0] for itemLabel, _cb in items) + 24)
      x = self.toggleButton.rect.right - width
      y = self.toggleButton.rect.bottom + DropdownMenu.ITEM_GAP
      for itemLabel, callback in items:
         itemRect = (x, y, width, DropdownMenu.ITEM_HEIGHT)
         self.itemButtons.append(Button(itemRect, itemLabel, on_click=self._pick(callback)))
         y += DropdownMenu.ITEM_HEIGHT + DropdownMenu.ITEM_GAP

   def _toggle(self):
      self.open = not self.open

   def _pick(self, callback):
      def onClick():
         self.open = False
         callback()
      return onClick

   def _panelRect(self):
      panel = self.itemButtons[0].rect.unionall([b.rect for b in self.itemButtons[1:]])
      return panel.inflate(8, 8)

   def handle_event(self, event):
      if self.toggleButton.handle_event(event):
         return True

      if not self.open:
         return False

      if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
         self.open = False
         return True

      for button in self.itemButtons:
         if button.handle_event(event):
            return True

      if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
         # Swallow the click either way: inside the panel but not on a
         # button, or fully outside it - neither should reach whatever's
         # drawn underneath.
         self.open = False
         return True

      return False

   def draw(self, surface):
      self.toggleButton.draw(surface)
      if not self.open:
         return
      pygame.draw.rect(surface, COLOR_SURFACE, self._panelRect(), border_radius=4)
      pygame.draw.rect(surface, COLOR_ACCENT, self._panelRect(), width=1, border_radius=4)
      for button in self.itemButtons:
         button.draw(surface)


class TextInput:
   """A single-line text box. Enter (or an explicit submit) calls
   on_submit(value) and clears the field."""

   def __init__(self, rect, placeholder="", on_submit=None):
      self.rect = pygame.Rect(rect)
      self.placeholder = placeholder
      self.on_submit = on_submit
      self.value = ""
      self.focused = True
      self._cursorVisible = True
      self._cursorTimer = 0.0

   def handle_event(self, event):
      if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
         self.focused = self.rect.collidepoint(event.pos)
         return False
      if not self.focused:
         return False
      if event.type == pygame.TEXTINPUT:
         self.value += event.text
         return True
      if event.type == pygame.KEYDOWN:
         if event.key == pygame.K_BACKSPACE:
            self.value = self.value[:-1]
            return True
         if event.key in (pygame.K_RETURN, pygame.K_KP_ENTER):
            submitted = self.value
            self.value = ""
            if self.on_submit:
               self.on_submit(submitted)
            return True
      return False

   def update(self, dt):
      self._cursorTimer += dt
      if self._cursorTimer >= 0.5:
         self._cursorTimer = 0.0
         self._cursorVisible = not self._cursorVisible

   def draw(self, surface):
      pygame.draw.rect(surface, COLOR_SURFACE, self.rect)
      pygame.draw.rect(surface, COLOR_ACCENT if self.focused else COLOR_BORDER, self.rect, width=1)

      font = getFont(15)
      showingPlaceholder = not self.value and not self.focused
      displayText = self.placeholder if showingPlaceholder else self.value
      textColor = COLOR_TEXT_DIM if showingPlaceholder else COLOR_TEXT
      textSurf = font.render(displayText, True, textColor)
      surface.blit(textSurf, (self.rect.x + 6, self.rect.y + (self.rect.height - textSurf.get_height()) // 2))

      if self.focused and self._cursorVisible:
         cursorX = self.rect.x + 6 + font.size(self.value)[0] + 1
         pygame.draw.line(surface, COLOR_TEXT, (cursorX, self.rect.y + 4), (cursorX, self.rect.bottom - 4))


SCROLLBAR_WIDTH = 10
SCROLLBAR_MARGIN = 4
SCROLLBAR_MIN_THUMB = 24


class ScrollLog:
   """Scrollable text panel with a draggable scrollbar - the .write(msg)
   target handed to iowSetViewer so the engine's output lands here."""

   def __init__(self, rect):
      self.rect = pygame.Rect(rect)
      self._lines = []
      # Lines scrolled up from the bottom: 0 = viewing the latest content.
      self._scrollOffset = 0
      self._dragging = False

   def write(self, msg):
      font = getFont(14)
      maxWidth = self.rect.width - 12 - SCROLLBAR_WIDTH - SCROLLBAR_MARGIN
      for rawLine in str(msg).split("\n"):
         self._lines.extend(wrapText(rawLine, font, maxWidth))
      self._scrollOffset = 0

   def getText(self):
      """Returns all logged text, newline-joined - mainly so tests can
      assert on log content without an OS-level rendering check."""
      return "\n".join(self._lines)

   def _visibleCount(self):
      lineHeight = getFont(14).get_linesize()
      return max(1, (self.rect.height - 8) // lineHeight)

   def _maxOffset(self):
      return max(0, len(self._lines) - self._visibleCount())

   def _trackRect(self):
      return pygame.Rect(self.rect.right - SCROLLBAR_WIDTH - SCROLLBAR_MARGIN, self.rect.y + 4,
                          SCROLLBAR_WIDTH, self.rect.height - 8)

   def _thumbRect(self):
      track = self._trackRect()
      maxOffset = self._maxOffset()
      if maxOffset <= 0:
         return None

      thumbHeight = max(SCROLLBAR_MIN_THUMB,
                         int(track.height * self._visibleCount() / len(self._lines)))
      travel = track.height - thumbHeight
      fractionScrolledUp = self._scrollOffset / maxOffset
      thumbY = track.bottom - thumbHeight - int(travel * fractionScrolledUp)
      return pygame.Rect(track.x, thumbY, track.width, thumbHeight)

   def _setScrollFraction(self, fractionScrolledUp):
      maxOffset = self._maxOffset()
      self._scrollOffset = max(0, min(maxOffset, round(maxOffset * fractionScrolledUp)))

   def handle_event(self, event):
      if event.type == pygame.MOUSEWHEEL and self.rect.collidepoint(pygame.mouse.get_pos()):
         maxOffset = self._maxOffset()
         self._scrollOffset = max(0, min(maxOffset, self._scrollOffset + event.y * 3))
         return True

      if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
         thumb = self._thumbRect()
         if thumb is not None and thumb.collidepoint(event.pos):
            self._dragging = True
            return True
         track = self._trackRect()
         if track.collidepoint(event.pos):
            # Clicked the track above/below the thumb: jump straight there.
            fractionScrolledUp = 1 - (event.pos[1] - track.y) / track.height
            self._setScrollFraction(fractionScrolledUp)
            return True

      elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
         if self._dragging:
            self._dragging = False
            return True

      elif event.type == pygame.MOUSEMOTION and self._dragging:
         track = self._trackRect()
         fractionScrolledUp = 1 - (event.pos[1] - track.y) / max(1, track.height)
         self._setScrollFraction(fractionScrolledUp)
         return True

      return False

   def draw(self, surface):
      pygame.draw.rect(surface, COLOR_SURFACE, self.rect)
      pygame.draw.rect(surface, COLOR_BORDER, self.rect, width=1)

      font = getFont(14)
      lineHeight = font.get_linesize()
      visibleCount = self._visibleCount()

      endIndex = len(self._lines) - self._scrollOffset
      startIndex = max(0, endIndex - visibleCount)
      visibleLines = self._lines[startIndex:endIndex]

      previousClip = surface.get_clip()
      surface.set_clip(self.rect)
      y = self.rect.y + 4
      for line in visibleLines:
         if line:
            textSurf = font.render(line, True, COLOR_TEXT)
            surface.blit(textSurf, (self.rect.x + 6, y))
         y += lineHeight
      surface.set_clip(previousClip)

      pygame.draw.rect(surface, COLOR_BUTTON, self._trackRect(), border_radius=4)
      thumb = self._thumbRect()
      if thumb is not None:
         pygame.draw.rect(surface, COLOR_ACCENT, thumb, border_radius=4)


class ScrollFrame:
   """Tracks a pixel scrollOffset (0 = top) and draggable scrollbar for a
   viewport of pixel-positioned child widgets - unlike ScrollLog, which
   owns and lays out its own text lines, this just does the scroll
   bookkeeping/scrollbar for content (e.g. buttons) the caller positions
   and draws itself, offsetting each by .scrollOffset."""

   def __init__(self, rect):
      self.rect = pygame.Rect(rect)
      self.scrollOffset = 0
      self.contentHeight = 0
      self._dragging = False

   def setContentHeight(self, contentHeight):
      """Call after the content's size changes (e.g. items added/removed)
      so maxOffset() - and the clamped scrollOffset - stay correct."""
      self.contentHeight = contentHeight
      self.scrollOffset = max(0, min(self.maxOffset(), self.scrollOffset))

   def maxOffset(self):
      return max(0, self.contentHeight - self.rect.height)

   def _trackRect(self):
      return pygame.Rect(self.rect.right - SCROLLBAR_WIDTH - SCROLLBAR_MARGIN, self.rect.y + 4,
                          SCROLLBAR_WIDTH, self.rect.height - 8)

   def _thumbRect(self):
      track = self._trackRect()
      maxOffset = self.maxOffset()
      if maxOffset <= 0:
         return None

      thumbHeight = max(SCROLLBAR_MIN_THUMB,
                         int(track.height * self.rect.height / self.contentHeight))
      travel = track.height - thumbHeight
      thumbY = track.y + int(travel * self.scrollOffset / maxOffset)
      return pygame.Rect(track.x, thumbY, track.width, thumbHeight)

   def _setScrollFraction(self, fraction):
      maxOffset = self.maxOffset()
      self.scrollOffset = max(0, min(maxOffset, round(maxOffset * fraction)))

   def handle_event(self, event):
      """Returns True if the event was consumed (offset may have changed) -
      callers should reposition their content by .scrollOffset afterwards."""
      if event.type == pygame.MOUSEWHEEL and self.rect.collidepoint(pygame.mouse.get_pos()):
         maxOffset = self.maxOffset()
         self.scrollOffset = max(0, min(maxOffset, self.scrollOffset - event.y * 40))
         return True

      if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
         thumb = self._thumbRect()
         if thumb is not None and thumb.collidepoint(event.pos):
            self._dragging = True
            return True
         track = self._trackRect()
         if track.collidepoint(event.pos):
            fraction = (event.pos[1] - track.y) / track.height
            self._setScrollFraction(fraction)
            return True

      elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
         if self._dragging:
            self._dragging = False
            return True

      elif event.type == pygame.MOUSEMOTION and self._dragging:
         track = self._trackRect()
         fraction = (event.pos[1] - track.y) / max(1, track.height)
         self._setScrollFraction(fraction)
         return True

      return False

   def draw_scrollbar(self, surface):
      if self.maxOffset() <= 0:
         return
      pygame.draw.rect(surface, COLOR_BUTTON, self._trackRect(), border_radius=4)
      pygame.draw.rect(surface, COLOR_ACCENT, self._thumbRect(), border_radius=4)


class Modal:
   """Base class for modal dialogs. Subclasses build self.widgets in
   __init__ and call self.dismiss(result) from a button callback; the
   owning ModalStack pops the modal and invokes the on_dismiss callback
   registered when it was pushed - the pygame equivalent of Textual's
   push_screen(screen, callback)/screen.dismiss(result)."""

   def __init__(self, rect):
      self.rect = pygame.Rect(rect)
      self.widgets = []
      self._stack = None

   def dismiss(self, result=None):
      self._stack._dismissTop(result)

   def handle_event(self, event):
      if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
         if self.on_escape():
            return True
      for widget in self.widgets:
         if widget.handle_event(event):
            return True
      return False

   def on_escape(self):
      """Subclasses override to dismiss on Escape (with whatever result
      counts as "cancel" for that dialog); return True if handled. Default
      is no-op."""
      return False

   def update(self, dt):
      for widget in self.widgets:
         if hasattr(widget, "update"):
            widget.update(dt)

   def draw(self, surface):
      pygame.draw.rect(surface, COLOR_SURFACE, self.rect, border_radius=6)
      pygame.draw.rect(surface, COLOR_ACCENT, self.rect, width=2, border_radius=6)
      for widget in self.widgets:
         widget.draw(surface)


class ModalStack:
   """Tracks the currently pushed modal dialogs. Only the top modal
   receives input; the game screen underneath is blocked while any modal
   is up."""

   def __init__(self):
      self._stack = []

   @property
   def active(self):
      return bool(self._stack)

   @property
   def top(self):
      return self._stack[-1][0] if self._stack else None

   def push(self, modal, on_dismiss=None):
      modal._stack = self
      self._stack.append((modal, on_dismiss))

   def _dismissTop(self, result):
      if not self._stack:
         return
      _modal, on_dismiss = self._stack.pop()
      if on_dismiss:
         on_dismiss(result)

   def handle_event(self, event):
      if self.top:
         return self.top.handle_event(event)
      return False

   def update(self, dt):
      if self.top:
         self.top.update(dt)

   def draw(self, surface):
      if not self._stack:
         return
      overlay = pygame.Surface(surface.get_size(), pygame.SRCALPHA)
      overlay.fill(COLOR_MODAL_OVERLAY)
      surface.blit(overlay, (0, 0))
      for modal, _on_dismiss in self._stack:
         modal.draw(surface)
