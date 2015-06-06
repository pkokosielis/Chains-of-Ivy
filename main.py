#!/usr/bin/python
import sys, os

from engine.IOwrappers import *
from engine.PlayerAction import *
from createdMonsters import *
from createdNPCs import *
from createdRooms import *

def showBanner():
   with open("img/banner.img", 'r') as fh:
      iowPrint(fh.read())

def initSetting():
   me = Character("Professor Hugo Lockchain")
   me.setScrollText("The peaty taste of whiskey mystifies you.")

   watch = Item("Gold pocket watch", "Weapon", 9)
   jacket = Item("Tweed blazer", "Suit", 9)

   # Study
   roomObj = getRoomWithID(1) 
   roomObj.addItemToRoom(watch)
   roomObj.addItemToRoom(jacket)


   # Archive Library 
   scotchFlask = Item("Whiskey shot", "Scroll", 3)
   roomObj = getRoomWithID(2)
   roomObj.addItemToRoom(scotchFlask)

   # Return the starting room, and the initialized character
   return [getRoomWithID(1), me] 

def gameMenu():
   iowPrint ("\n\n")
   showBanner()
   iowPrint ("\n\n")
   iowPrint ("Welcome, your options are:\n")
   iowPrint ("1) Start new game")
   iowPrint ("2) Restore saved game")
   iowPrint ("3) Quit")
   iowPrint ("\nEnter 1, 2, or 3\n")
   response = iowInput(">>: ")
   if (response == "1" or
       response == "2" or
       response == "3"):
      return response
   else:
      iowPrint ("Invalid Choice. Try Again.")
      return gameMenu()

    

def main():

   # Start Game
 
   while 1:
      currentRoom = None
      player = Character("Init")
      nextAction = PlayerAction()

      menuChoice = gameMenu()

      if (menuChoice == "1"):
         initialSetting = initSetting()
         currentRoom = initialSetting[0]
         player = initialSetting[1]
         currentRoom.displayRoom()

      elif (menuChoice == "2"):
         nextAction.setRestoreRequested()
         
      else:
         iowPrint ("Thank you for playing. Good-bye!")
         return

      while not player.isDead():
         if (nextAction.getRestoreRequested() == "True"):
            savedState = nextAction.doRestore(currentRoom, player)
            currentRoom = savedState[0]
            player = savedState[1]
         action = None
         currentRoom = nextAction.doAction(currentRoom, player, action)
           
      # Player died. Restore or quit?
      
   return

main()
