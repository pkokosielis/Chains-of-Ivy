from random import randint
from random import choice

from engine.IOwrappers import *
from engine.Item import *
from engine.Character import *

class NPC:
   def __init__(self, name, experience, gold):
      self.name = name
      self.questFulfilled = "False"
      self.beforeQuestComm = []
      self.afterQuestComm = []
      self.expToGive = experience
      self.goldToGive = gold
      self.itemsToGive = []
      self.Thanks = ""

   def getName(self):
      return self.name

   def setThanksMessage(self, msg):
      self.Thanks = msg

   def setQuestFulfilled(self):
      self.questFulfilled = "True"

   def setQuestPending(self):
      self.questFulfilled = "Pending"

   def getQuestFulfilledStatus(self):
      return self.questFulfilled

   def addQuoteBeforeQuest(self, quote):
      self.beforeQuestComm.append(quote)

   def addQuoteAfterQuest(self, quote):
      self.afterQuestComm.append(quote)

   def sayQuote(self, character, room):
      if (self.getQuestFulfilledStatus() == "Pending"):
         for item in character.inventory:
            if item.npcRequestor == self:
               character.removeItem(item)
         iowWrapPrint (self.Thanks)
         self.setQuestFulfilled()
         iowWrapPrint ("For helping " + self.getName() + " you gain:")
         iowWrapPrint ("Experience +" + str(self.getExpToGive()))
         iowWrapPrint ("Gold +" + str(self.getGoldToGive()))
         self.giveItems(room) 
         character.incrementExperience(self.getExpToGive())
         character.incrementGold(self.getGoldToGive())
         room.unBlockAllDirections()

      elif (self.getQuestFulfilledStatus() == "True"):
         if self.afterQuestComm:
            iowWrapPrint (choice(self.afterQuestComm))
         else:
            iowWrapPrint (self.getName() + "'s silence is deafening.")
      else:
         if self.beforeQuestComm:
            iowWrapPrint (choice(self.beforeQuestComm))
         else:
            iowWrapPrint (self.getName() + "'s silence is deafening.")

   def getGoldToGive(self):
      return self.goldToGive

   def getExpToGive(self):
      return self.expToGive

   def addItems(self, itemList):
      self.itemsToGive = itemList

   def giveItems(self,room):
      if self.itemsToGive:
         for item in self.itemsToGive:
            self.itemsToGive.remove(item)
            iowWrapPrint (self.getName() + " presents to you a " + item.getName() + ".")
            room.addItemToRoom(item)
