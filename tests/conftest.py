import os
import sys

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(ROOT)
if ROOT not in sys.path:
   sys.path.insert(0, ROOT)

from engine import IOwrappers


class FakeViewer:
   """Captures iowPrint output the way a real GUI/TUI frontend would."""

   def __init__(self):
      self.lines = []

   def write(self, msg):
      self.lines.append(msg)

   def text(self):
      return "\n".join(self.lines)


@pytest.fixture
def fake_viewer():
   return FakeViewer()


@pytest.fixture(autouse=True)
def reset_viewer():
   IOwrappers.iowSetViewer(None)
   yield
   IOwrappers.iowSetViewer(None)
