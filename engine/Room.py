from random import randint
from random import choice

from engine.IOwrappers import *
from engine.Monster import *

class Room:

   # description = text describing the location
   # items = list of items [] in the location
   # encounter = % chance of an encounter (benign or combative)

   def __init__(self, roomID, title, description, encounter, generatedMonsterList):
      self.ID = int(roomID)
      self.title = title
      self.description = description 
      self.items = []
      self.encounter = int(encounter) 
      self.blockedDirections = []
      self.north = None
      self.south = None
      self.east = None
      self.west = None
      self.up = None
      self.down = None
      self.monsters = []
      self.npc = []
      self.storeKeeper = None
      self.generatedMonsterList = generatedMonsterList


   def getID(self):
      return self.ID

   def getTitle(self):
      return self.title

   def generateMonsterInRoom(self):
      chance = randint(0,100)
      if (chance <= int(self.encounter)):
         monsterType = choice(self.generatedMonsterList)
         monster = Monster(monsterType)
         self.addMonsterToRoom(monster)

   def addMonsterToRoom(self, aMonster):
      self.monsters.append(aMonster)

   def getMonsters(self):
      return self.monsters

   def addItemToRoom(self, item):
      self.items.append(item)

   def addNPCtoRoom(self, npc):
      self.npc.append(npc)

   def addStoreKeeperToRoom(self, storeKeeper):
      self.storeKeeper = storeKeeper

   def existsItem(self, itemStr):
      for item in self.items:
         if (item.getName() == itemStr):
            return item 
      return None

   def takeItem(self, character, itemStr):
       item = self.existsItem(itemStr)
       if (item):
          self.items.remove(item)
          character.addToInventory(item)
          iowPrint ("You take the " + item.getName())
       else:
          iowPrint ("There is no " + itemStr + " here.")

   def takeAllItems(self, character):
       if self.items:
          for item in self.items:
             character.addToInventory(item)
             iowPrint ("You take the " + item.getName())
          self.items = []
       else:
          iowPrint ("There is nothing to take.")
 
   def displayRoom(self):
      iowPrint ("\n" + self.getTitle())
      iowPrint ("____________________________________")
      iowWrapPrint (self.description)
      if self.npc:
         for npc in self.npc:
            iowPrint (npc.getName() + " is here.")
      if self.storeKeeper:
         iowPrint (self.storeKeeper.getName() + " is here.")
      if self.monsters:
         showFirstImageOnly = 0
         for monster in self.monsters:
            if (monster.hasImage() == "True"):
               if (showFirstImageOnly == 0):
                  monster.showMonsterImage()
                  showFirstImageOnly += 1
            iowPrint ("A lurking " + monster.getName() + " eyes you fiercely.")
      if self.items:
         iowPrint ("You see the following items:") 
         for item in self.items:
            iowPrint (item.getName())
      self.getExits()

   def setAdjacentNorth(self, someRoom):
      self.north = someRoom

   def setAdjacentSouth(self, someRoom):
      self.south = someRoom

   def setAdjacentEast(self, someRoom):
      self.east = someRoom

   def setAdjacentWest(self, someRoom):
      self.west = someRoom

   def setAdjacentUp(self, someRoom):
      self.up = someRoom

   def setAdjacentDown(self, someRoom):
      self.down = someRoom

   def blockDirection(self, direction):
      self.blockedDirections.append(direction)

   def unBlockAllDirections(self):
      for passage in self.blockedDirections:
         iowPrint ("A passage " + passage + " has been unblocked.")
      self.blockedDirections = []


   def getExits(self):
      iowPrint ("Exits are:")
      if (self.north != None and not "North" in self.blockedDirections):
         iowPrint ("N")
      if (self.south != None and not "South" in self.blockedDirections):
         iowPrint ("S")
      if (self.east != None and not "East" in self.blockedDirections):
         iowPrint ("E")
      if (self.west != None and not "West" in self.blockedDirections):
         iowPrint ("W")
      if (self.up != None and not "Up" in self.blockedDirections):
         iowPrint ("U")
      if (self.down != None and not "Down" in self.blockedDirections):
         iowPrint ("D")
