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
      self.Thanks = ""

   def getName(self):
      return self.name

   def setThanksMessage(self, msg):
      self.Thanks = msg

   def getStoreName(self):
      return self.storeName

   def listStoreItems(self, character, room):
      iowWrapPrint ("Avaiable for Sale at " + self.getStoreName())
      for item in itemsToSell:
         iowWrapPrint(item) 

   def addItem(self, itemList):
      self.itemsToSell = itemList

   def sellItem(self,item, room):
      if item in self.itemsToSell:
            iowWrapPrint (self.getName() + " places a " + item.getName() + "on the counter for you to take.")
            room.addItemToRoom(item)
