from random import randint
from random import choice

from engine.IOwrappers import *
from engine.Item import *
from engine.Character import *

class StoreKeeper:
   def __init__(self, name, storeName):
      self.name = name
      self.storeName = storeName
      self.itemsToSell = []
      self.Welcome = ""
      self.Thanks = ""
   

   def getName(self):
      return self.name

   def setWelcomeMessage(self, msg):
      self.Welcome = msg

   def getWelcomeMessage(self):
      return self.Welcome

   def setThanksMessage(self, msg):
      self.Thanks = msg
 
   def getThanksMessage(self):
      return self.Thanks

   def getStoreName(self):
      return self.storeName

   def listStoreItems(self, character, room):
      iowWrapPrint (self.getWelcomeMessage())
      iowWrapPrint ("Avaiable for Sale at " + self.getStoreName())
      iowWrapPrint ("-------------------------------------------")
      for item in self.itemsToSell:
         iowWrapPrint(" * " + item.getName() + "  [" + str(item.getItemValue()) + " gold]")
      iowWrapPrint ("-------------------------------------------")

   def addItem(self, itemList):
      self.itemsToSell = itemList

   def existsItem(self, itemStr):
      for item in self.itemsToSell:
         if (item.getName() == itemStr):
            return item
      return None

   def sellItem(self, itemStr, character, room):
      item = self.existsItem(itemStr)
      if item in self.itemsToSell:
            if character.getGold() >= item.getItemValue():
               iowWrapPrint (self.getName() + " sells you a " + item.getName())
               character.decrementGold(item.getItemValue()) 
               character.addToInventory(item) 
               iowWrapPrint (self.getThanksMessage())
            else:
               iowPrint ("You can't afford a " + itemStr + " with only " + str(character.getGold()) + " gold pieces!" )
      else:
         iowPrint ("There is no " + itemStr + " available to buy!")

