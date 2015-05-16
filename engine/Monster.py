from random import randint
from engine.IOwrappers import *
from engine.Item import *

class Monster:
   def __init__(self, monsterParms, imgFile=None):
      self.name = monsterParms[0]
      self.hp = int(monsterParms[1])
      self.maxAttack = int(monsterParms[2])
      self.attackType = monsterParms[3]
      self.expGiven = int(monsterParms[4])
      myItems = []
      if (monsterParms[5] != 'None'): 
         myItems = monsterParms[5] 
      self.itemsToDrop = myItems 
      self.gold = int(monsterParms[6])
      self.status = "Alive"
      self.imageFile = imgFile

# Example new Monster("Goblin", 12, 7, "swings club", 40, [club, boots], 25)

   def showMonsterImage(self):
      if self.imageFile:
         with open(self.imageFile, 'r') as fh:
            iowPrint (fh.read())

   def hasImage(self):
      if self.imageFile:
         return "True"
      return "False"

   def getAttackAmount(self):
      return randint(0,self.maxAttack)

   def getName(self):
      return self.name

   def subtractFromHP(self, hitAmount):
      self.hp -= hitAmount
      if (self.hp <= 0):
         iowPrint ("The " + self.name + " is vanquished!")
         self.status = "Dead"
         
   def getAttackType(self):
      return self.attackType

   def setStatus(self, status):
      self.status = status

   def getStatus(self):
      return self.status

   def getExperience(self):
      return randint(int(self.expGiven/2), int(self.expGiven))

   def getGold(self):
      return self.gold

   def addItems(self, itemList):
      self.itemsToDrop = itemList

   def dropItems(self,room):
      if self.itemsToDrop:
         for item in self.itemsToDrop:
            iowPrint ("A " + item.getName() + " has been dropped by the " + self.name +".")
            room.addItemToRoom(item)
