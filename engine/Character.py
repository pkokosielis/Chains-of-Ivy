from random import randint
from engine.IOwrappers import *
from engine.Item import *

class Character:
   def __init__(self,name):
      self.name = name
      self.inventory = []
      self.hp_max = 30
      self.hp = self.hp_max
      self.might = 2
      self.magic = 0
      self.weapon = None
      self.helmet = None
      self.suit = None
      self.boots = None
      self.experience = 0
      self.level = 0
      self.gold = 0
      self.armor = [self.helmet, self.suit, self.boots]
      self.inBattle = "False"
      self.scrollText = "The scroll burns up as you commit the mystics to memory."

   def isDead(self):
      return (self.hp <= 0)

   def addToInventory(self,item):
      self.inventory.append(item)
      if item.npcRequestor:
         item.npcRequestor.setQuestPending()

   def getName(self):
      return self.name

   def setInBattleTrue(self):
      self.inBattle = "True"

   def setInBattleFalse(self):
      self.inBattle = "False"

   def getInBattleStatus(self):
      return self.inBattle

   def updateLevel(self):
      if (self.experience >= (100 * (2**self.level))):
         self.level += 1
         self.hp_max += randint(5,25)
         iowPrint ("You have graduated to level: " + str(self.level) + ". Congratulations!")

   def incrementHitPoints(self, amount):
      self.hp += amount
      if self.hp > self.hp_max:
         self.hp = self.hp_max

   def incrementExperience(self, amount):
      self.experience += amount
      self.updateLevel()

   def incrementGold(self, amount):
      self.gold += amount

   def decrementGold(self, amount):
      self.gold -= amount

   def getGold(self):
      return self.gold

   def getInventory(self):
      if self.inventory:
         iowPrint ("You are currently carrying:")
         for item in self.inventory:
            iowPrint (item.getName())
      else:
         iowPrint ("You are carrying nothing.")
  
   def getItemFromDescription(self,itemDesc):
      for item in self.inventory:
         if item.getName() == itemDesc:
            return item

   def removeItem(self, item):
      if item == self.weapon:
         self.Weapon = None
      elif item == self.helmet:
         self.helmet = None
      elif item == self.suit:
         self.suit = None
      elif item == self.boots:
         self.boots = None
      self.updateArmorList()
      self.inventory.remove(item)
      iowPrint ("You relinquish the " + item.getName())

   def dropItem(self,room, itemDesc):
      item = self.getItemFromDescription(itemDesc)

      if not item:
         iowPrint ("I don't have a " + itemDesc)
         return
    
      if item == self.weapon:
         self.Weapon = None
      elif item in self.helmet:
         self.helmet = None 
      elif item == self.suit:
         self.suit = None
      elif item == self.boots:
         self.boots = None
      self.updateArmorList() 

      self.inventory.remove(item)
      room.addItemToRoom(item)
      iowPrint ("You have dropped the " + item.getName()) 


   def setScrollText(self,text):
      self.scrollText = text

   def getScrollText(self):
      return self.scrollText

   def useItem(self,itemDesc):
      item = self.getItemFromDescription(itemDesc)

      if not item:
         iowPrint ("I don't have a " + itemDesc)
         return

      if (item.type == "Weapon"):
         self.weapon = item
         iowPrint ("You are now wielding the " + self.weapon.getName())
      elif (item.type == "Helmet"):
         self.helmet = item
         iowPrint ("You are now wearing the " + self.helmet.getName())
      elif (item.type == "Suit"):
         self.suit = item
         iowPrint ("You are now wearing the " + self.suit.getName())
      elif (item.type == "Boots"):
         self.boots = item
         iowPrint ("You are now wearing the " + self.boots.getName())
      elif (item.type == "Scroll"):
         self.magic += item.modifier
         iowPrint (self.getScrollText()) 
         self.inventory.remove(item)
      else:
         iowPrint ("I don't know how to use the " + item.getName())

      self.updateArmorList()

   def updateArmorList(self):
      self.armor = [self.helmet, self.suit, self.boots]

   def getArmorClass(self):
      armorClass = 0
      for equip in self.armor:
         if equip:
            armorClass += equip.modifier
      return armorClass

   def getStats(self):
      iowPrint ("Statistics for " + self.name)
      iowPrint ("================================")
      iowPrint ("Level: " +  str(self.level)) 
      iowPrint ("Experience: " + str(self.experience))
      iowPrint ("HitPoints: " + str(self.hp) + "/" + str(self.hp_max))
      iowPrint ("Might: " + str(self.might))
      iowPrint ("Magic: " + str(self.magic))
      iowPrint ("Gold: " + str(self.gold))
      if self.weapon:
         iowPrint ("Wielding: " + self.weapon.getName())
      else:
         iowPrint ("Wielding: Bare Hands")
      iowPrint ("Armor Class: " + str(self.getArmorClass()))
      iowPrint ("\nYou are wearing:")
      iowPrint ("---------------")
      for item in self.armor:
         if item:
            iowPrint ("-> " + item.getName())
      iowPrint ("\nYou are carrying:")
      iowPrint ("------------------")
      for item in self.inventory:
         iowPrint ("-> " + item.getName())
