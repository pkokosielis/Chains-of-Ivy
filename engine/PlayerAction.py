import os
import pickle

from random import randint
from engine.IOwrappers import *
from engine.Character import *
from engine.Room import *

gSavedSettingFileName = "game.dat"
gSavedPlayerFileName = "player.dat"

class PlayerAction:

   # actions can be of "Move", "Admin", or "Attack" types
   def __init__(self):
      self.action = None 
      self.type = None
      self.restoreRequested = "False"

   def getRestoreRequested(self):
      return self.restoreRequested

   def setRestoreRequested(self):
      self.restoreRequested = "True"

   def getAction(self, action):
      if (iowGetViewer() != None):
         self.action = action 
      else:
         self.action = iowInput(">>: ")
      
   def getActionType(self):
      self.type = "Bad" 

      if (self.action == "n" or self.action == "s" or 
          self.action == "e" or self.action == "w" or 
          self.action == "u" or self.action == "d"):
         self.type = "Move"

      elif (self.action == "look" or self.action[:5] == "take " or 
            self.action[:5] == "drop " or self.action == "inventory" or
            self.action == "stats" or self.action == "talk" or
            self.action == "save" or self.action == "restore" or 
            self.action == "quit" or self.action[:4] == "use " or
            self.action == "help"):
         self.type = "Admin"

      elif (self.action == "attack"):
            self.type = "Attack"

      return self.type

   def doMoveAction(self, room):
      success = room
      if self.action == "n" and room.north != None and not "North" in room.blockedDirections:
         success = room.north
      elif self.action == "s" and room.south != None and not "South" in room.blockedDirections:
         success = room.south
      elif self.action == "e" and room.east != None and not "East" in room.blockedDirections:
         success = room.east
      elif self.action == "w" and room.west != None and not "West" in room.blockedDirections:
         success = room.west
      elif self.action == "u" and room.up != None and not "Up" in room.blockedDirections:
         success = room.up
      elif self.action == "d" and room.down != None and not "Down" in room.blockedDirections:
         success = room.down
      return success

   def doHelp(self):
      iowPrint ("Valid commands are:")
      iowPrint ("n - move North")
      iowPrint ("s - move South")
      iowPrint ("e - move East")
      iowPrint ("w - move West")
      iowPrint ("u - move Up")
      iowPrint ("d - move Down")
      iowPrint ("look - Look at current room")
      iowPrint ("stats - Show character statistics")
      iowPrint ("inventory - Show character's inventory")
      iowPrint ("take [all | <item>] - take a specific item")
      iowPrint ("use <item> - use a specific item")
      iowPrint ("drop <item> - drop a specific item")
      iowPrint ("talk - talk to someone in the room")
      iowPrint ("attack - attack all enemies")
      iowPrint ("save - save current game")
      iowPrint ("restore - restore the saved game")
      iowPrint ("quit - quit the game")
      iowPrint ("help - Print this message") 

   def doSaveTk(self, room, character, fileName):
      with open(fileName, 'wb') as output:
           pickle.dump(room, output, pickle.HIGHEST_PROTOCOL)
           pickle.dump(character, output, pickle.HIGHEST_PROTOCOL)

   def doSave(self, room, character):
      iowPrint ("Are you sure you want to save the current game? [y/n]")
      response = iowInput(">>: ")
      if (response == "y"):
         with open(gSavedSettingFileName, 'wb') as output:
           pickle.dump(room, output, pickle.HIGHEST_PROTOCOL)
         with open(gSavedPlayerFileName, 'wb') as output:
           pickle.dump(character, output, pickle.HIGHEST_PROTOCOL)
         iowPrint ("Game successfully saved!")
      elif (response == "n"):
        iowPrint ("save is cancelled.")
      else:
        iowPrint ("Invalid response, try again")
        return self.doSave(room, character)

   def doRestoreTk(self, room, character, fileName):
      fh = open(fileName, 'rb')
      savedRoom = pickle.load(fh)
      savedCharacter = pickle.load(fh)
      fh.close()
      return [savedRoom, savedCharacter]

   def doRestore(self, room, character):
      self.restoreRequested = "False"
      iowPrint ("Are you sure you want to restore to the last saved game? [y/n]")
      response = iowInput(">>: ")      
      if (response == "y"):
        if (os.path.exists(gSavedSettingFileName) and
            os.path.exists(gSavedPlayerFileName)):
           gfh = open(gSavedSettingFileName, 'rb')
           pfh = open(gSavedPlayerFileName, 'rb')
           room = pickle.load(gfh)
           character = pickle.load(pfh)
           gfh.close()
           pfh.close()
           iowPrint ("You find your being transported through time and space! Game Restored.\n")
           room.displayRoom()
        else:
           iowPrint ("Sorry, there isn't a saved game to restore.")
        return [room, character]
      elif (response == "n"):
        iowPrint ("restore is cancelled.")
        return [room, character]
      else:
        iowPrint ("Invalid response, try again")
        return self.doRestore(room, character)

   def doQuit(self):
      iowPrint ("Are you sure you want to quit this game? [y/n]")
      response = iowInput(">>: ")
      if (response == "y"):
         iowPrint ("You are vapourized into the next plane of existence... So long!")
         exit(0)
      elif (response == "n"):
        iowPrint ("Then onwards you go!")
      else:
         return self.doQuit() 
 

   def doAdminAction(self, room, character):
      if self.action == "look":
         room.displayRoom()

      elif self.action[:5] == "take ":
         takeItem = self.action[5:]
         if (takeItem == "all"):
            room.takeAllItems(character)
         else:
            room.takeItem(character,takeItem)

      elif self.action == "inventory":
         character.getInventory()

      elif self.action == "stats":
         character.getStats()

      elif self.action[:4] == "use ":
         itemDesc = self.action[4:]
         character.useItem(itemDesc)

      elif self.action == "quit":
         self.doQuit()

      elif self.action == "save":
         self.doSave(room, character) 

      elif self.action == "restore":
         self.restoreRequested = "True"

      elif self.action[:5] == "drop ":
         dropItem = self.action[5:]
         character.dropItem(room,dropItem) 

      elif self.action == "help":
         self.doHelp()     
 
      elif self.action == "talk":
         if room.npc:
            for npc in room.npc:
               npc.sayQuote(character, room)
         else:
            iowPrint ("You mutter to yourself bitterly.")

   def doAttackAction(self, room, character):
      if self.action == "attack":
         targetList = room.getMonsters()
         if not targetList:
            iowPrint ("There is nothing to attack!")
            return

         weaponModifier = 0
         if character.weapon:
            weaponModifier = character.weapon.getModifier()
         characterAttackRangeMax = ((character.might + character.magic + weaponModifier) * (character.level + 1))

         for target in targetList:
            characterAttack = randint(0, characterAttackRangeMax)
            weaponStr = "bare hands"
            if character.weapon != None:
               weaponStr = character.weapon.getName() 
            iowWrapPrint ("You attack the " + target.getName() + " with your " + weaponStr \
                  + " and inflict " + str(characterAttack) + " damage points.") 
            target.subtractFromHP(characterAttack)
            if (target.getStatus() == "Dead"):
               target.dropItems(room)
               expTaken = target.getExperience()
               iowPrint ("You gain " + str(expTaken) + " experience and " + str(target.getGold()) + " gold pieces.")
               character.incrementGold(target.getGold())
               character.incrementExperience(expTaken)
               room.monsters.remove(target)
            else:
               amountAttacked = target.getAttackAmount() - character.getArmorClass()
               if (amountAttacked <= 0):
                  iowWrapPrint ("The " + target.getName() + " missed!")
               else:
                  iowWrapPrint ("The " + target.getName() + " " + target.getAttackType() + " and causes " + str(amountAttacked) + " damage points!")
                  character.hp -= amountAttacked
                  if (character.hp <= 0):
                     iowPrint ("You have perished in battle!")

      if not room.getMonsters():
         room.unBlockAllDirections()

   def doAction(self, room, character, action):
      self.getAction(action)
      self.getActionType()

      if self.type == "Bad":
         iowPrint ("I don't understand your command. Try Again.")

      elif self.type == "Move":
         newRoom = self.doMoveAction(room)
         if newRoom != room:
            newRoom.generateMonsterInRoom()
            character.incrementHitPoints(1)
            newRoom.displayRoom()
            return newRoom
         else:
            iowPrint ("You can't go that way!")

      elif self.type == "Admin":
         self.doAdminAction(room, character)

      elif self.type == "Attack":
         self.doAttackAction(room, character)

      return room
