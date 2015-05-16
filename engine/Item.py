from engine.NPC import *

class Item:
   def __init__(self,name,type, modifier):
      self.name = name
      self.type = type
      self.modifier = modifier
      self.npcRequestor = None

   def getName(self):
      return self.name

   def getType(self):
      return self.type

   def getModifier(self):
      return self.modifier

   def setQuestForNPC(self, npc):
      self.npcRequestor = npc

