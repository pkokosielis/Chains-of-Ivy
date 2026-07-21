import os
import pickle
import re

from random import randint
from engine.IOwrappers import *
from engine.Character import *
from engine.Room import *

gSavedSettingFileName = "game.dat"
gSavedPlayerFileName = "player.dat"
gSavesDirectory = "saves"

def sanitizeSaveName(name):
   return re.sub(r'[^A-Za-z0-9 _-]', '', name).strip()

class PlayerAction:

   # actions can be of "Move", "Admin", or "Attack" types
   def __init__(self):
      self.action = None
      self.type = None

   def getAction(self, action):
      self.action = action

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
            self.action == "load" or self.action == "quit" or
            self.action[:4] == "use " or self.action[:4] == "buy " or
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
      iowPrint ("buy <item> - buy item from storekeeper")
      iowPrint ("talk - talk to someone in the room")
      iowPrint ("attack - attack all enemies")
      iowPrint ("save - save current game")
      iowPrint ("restore - restore the saved game")
      iowPrint ("load - load a named saved game")
      iowPrint ("quit - quit the game (with the option to save under a name first)")
      iowPrint ("help - Print this message") 

   def doSave(self, room, character):
      with open(gSavedSettingFileName, 'wb') as output:
        pickle.dump(room, output, pickle.HIGHEST_PROTOCOL)
      with open(gSavedPlayerFileName, 'wb') as output:
        pickle.dump(character, output, pickle.HIGHEST_PROTOCOL)
      iowPrint ("Game successfully saved!")

   def doRestore(self, room, character):
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

   def namedSavePath(self, name):
      return os.path.join(gSavesDirectory, name + ".dat")

   def doNamedSave(self, room, character, name):
      os.makedirs(gSavesDirectory, exist_ok=True)
      with open(self.namedSavePath(name), 'wb') as output:
         pickle.dump(room, output, pickle.HIGHEST_PROTOCOL)
         pickle.dump(character, output, pickle.HIGHEST_PROTOCOL)
      iowPrint ("Game saved as \"" + name + "\".")

   def doNamedRestore(self, room, character, name):
      path = self.namedSavePath(name)
      if os.path.exists(path):
         with open(path, 'rb') as fh:
            room = pickle.load(fh)
            character = pickle.load(fh)
         iowPrint ("You find your being transported through time and space! Game Restored.\n")
         room.displayRoom()
      else:
         iowPrint ("Sorry, there isn't a saved game named \"" + name + "\".")
      return [room, character]

   def listNamedSaves(self):
      if not os.path.isdir(gSavesDirectory):
         return []
      return sorted(fileName[:-len(".dat")] for fileName in os.listdir(gSavesDirectory)
                     if fileName.endswith(".dat"))

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

      elif self.action[:4] == "buy ":
         itemDesc = self.action[4:]
         room.storeKeeper.sellItem(itemDesc,character,room)

      elif self.action == "save":
         self.doSave(room, character)

      elif self.action[:5] == "drop ":
         dropItem = self.action[5:]
         character.dropItem(room,dropItem) 

      elif self.action == "help":
         self.doHelp()     
 
      elif self.action == "talk":
         if room.npc:
            for npc in room.npc:
               npc.sayQuote(character, room)
         elif room.storeKeeper:
            room.storeKeeper.listStoreItems(character, room)
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
