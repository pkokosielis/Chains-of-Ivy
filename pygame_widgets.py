"""Small hand-rolled widget toolkit for the Pygame frontend.

Pygame provides no GUI widgets - just a canvas and an event queue - so this
module supplies the minimum needed to reproduce tuimain.py's UI: clickable
buttons, a single-line text input, a scrollable text log, and a modal
dialog stack that mirrors Textual's push_screen(...)/dismiss() pattern
closely enough that tuimain.py's dialog flows port over almost verbatim.
"""

import pygame

COLOR_BACKGROUND = (24, 26, 32)
COLOR_SURFACE = (36, 39, 48)
COLOR_ACCENT = (94, 176, 200)
COLOR_TEXT = (230, 230, 230)
COLOR_TEXT_DIM = (150, 155, 165)
COLOR_BUTTON = (52, 56, 68)
COLOR_BUTTON_HOVER = (68, 73, 88)
COLOR_BUTTON_DISABLED = (40, 42, 50)
COLOR_PRIMARY = (47, 99, 122)
COLOR_PRIMARY_HOVER = (60, 122, 148)
COLOR_ERROR = (150, 60, 60)
COLOR_ERROR_HOVER = (176, 74, 74)
COLOR_MODAL_OVERLAY = (0, 0, 0, 160)

_fontCache = {}


def getFont(size, bold=False):
   """Returns a cached monospace SysFont. Lazy so pygame.font doesn't need
   to be initialized until a widget actually draws."""
   key = (size, bold)
   if key not in _fontCache:
      _fontCache[key] = pygame.font.SysFont("dejavusansmono,monospace", size, bold=bold)
   return _fontCache[key]


def drawWrappedText(surface, text, rect, font, color, align="center"):
   """Draws word-wrapped, vertically-centered text inside rect. align is
   "center" or "left" for horizontal alignment of each line."""
   lines = []
   for rawLine in text.split("\n"):
      lines.extend(wrapText(rawLine, font, rect.width))

   lineHeight = font.get_linesize()
   y = rect.y + max(0, (rect.height - len(lines) * lineHeight) // 2)
   for line in lines:
      textSurf = font.render(line, True, color)
      x = rect.x + (rect.width - textSurf.get_width()) // 2 if align == "center" else rect.x
      surface.blit(textSurf, (x, y))
      y += lineHeight


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
   or "error", matching the styling vocabulary tuimain.py already uses for
   its Textual buttons."""

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
      textSurf = getFont(18).render(self.label, True, textColor)
      surface.blit(textSurf, textSurf.get_rect(center=self.rect.center))


class TextInput:
   """A single-line text box. Enter (or an explicit submit) calls
   on_submit(value) and clears the field, mirroring Textual's
   Input.Submitted behavior in tuimain.py."""

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
      pygame.draw.rect(surface, COLOR_ACCENT if self.focused else COLOR_TEXT_DIM, self.rect, width=1)

      font = getFont(18)
      showingPlaceholder = not self.value and not self.focused
      displayText = self.placeholder if showingPlaceholder else self.value
      textColor = COLOR_TEXT_DIM if showingPlaceholder else COLOR_TEXT
      textSurf = font.render(displayText, True, textColor)
      surface.blit(textSurf, (self.rect.x + 6, self.rect.y + (self.rect.height - textSurf.get_height()) // 2))

      if self.focused and self._cursorVisible:
         cursorX = self.rect.x + 6 + font.size(self.value)[0] + 1
         pygame.draw.line(surface, COLOR_TEXT, (cursorX, self.rect.y + 4), (cursorX, self.rect.bottom - 4))


class ScrollLog:
   """Scrollable text panel - the .write(msg) target handed to
   iowSetViewer, playing the same role tuimain.py's RichLogViewer/RichLog
   pairing does for the Textual frontend."""

   def __init__(self, rect):
      self.rect = pygame.Rect(rect)
      self._lines = []
      self._scrollOffset = 0

   def write(self, msg):
      font = getFont(16)
      maxWidth = self.rect.width - 12
      for rawLine in str(msg).split("\n"):
         self._lines.extend(wrapText(rawLine, font, maxWidth))
      self._scrollOffset = 0

   def getText(self):
      """Returns all logged text, newline-joined - mainly so tests can
      assert on log content without an OS-level rendering check."""
      return "\n".join(self._lines)

   def handle_event(self, event):
      if event.type == pygame.MOUSEWHEEL and self.rect.collidepoint(pygame.mouse.get_pos()):
         maxOffset = max(0, len(self._lines) - 1)
         self._scrollOffset = max(0, min(maxOffset, self._scrollOffset + event.y * 3))
         return True
      return False

   def draw(self, surface):
      pygame.draw.rect(surface, COLOR_SURFACE, self.rect)
      pygame.draw.rect(surface, COLOR_ACCENT, self.rect, width=1)

      font = getFont(16)
      lineHeight = font.get_linesize()
      visibleCount = max(1, (self.rect.height - 8) // lineHeight)

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
      """Subclasses override to dismiss on Escape; return True if handled.
      Default is no-op, matching dialogs in tuimain.py that have no escape
      binding (e.g. SaveNameScreen does, ConfirmScreen doesn't map escape
      to Yes - callers decide per dialog)."""
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
   is up, matching tuimain.py's screen-stack modality."""

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
