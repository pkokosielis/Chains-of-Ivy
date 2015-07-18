from engine.IOwrappers import *
from engine.Room import *
from createdMonsters import *
from createdNPCs import *

# Room Descriptions are of this format:
# <room>Desc = [ textDesc, (int) % encounter, StockMonsterList]


debugRooms = 0 
RoomArray = []

# format = Clock Bug;2;1;'nibbles';5;None;5


def readRoomDesc():
   with open('csv/roomList.csv','r') as f:
      for rLine in f:
        room = rLine.split(';')
        room[1] = room[1].replace('\\n','\n')
        roomObj = Room(room[0], room[1], room[2], room[3], StockMonsterList)
        RoomArray.append(roomObj)      

        iowDebugPrint (debugRooms, room)
        iowDebugPrint (debugRooms, room[1])
        if debugRooms:
           roomObj.displayRoom() 

def getRoomWithID(id):
   for roomObj in RoomArray:
      iowDebugPrint (debugRooms, roomObj.getID())
      if roomObj.getID() == int(id):
         return roomObj
   iowDebugPrint ("Error -- room with ID = " + str(id) + " not found.")
   return None

def connectRooms(thisRoom, roomNorth, roomSouth, roomEast, roomWest, roomUp, roomDown):
   thisRoomObj = getRoomWithID(thisRoom)
   if roomNorth != 'None':
      thisRoomObj.setAdjacentNorth(getRoomWithID(roomNorth))
   if roomSouth != 'None':
      thisRoomObj.setAdjacentSouth(getRoomWithID(roomSouth))
   if roomEast != 'None':
      thisRoomObj.setAdjacentEast(getRoomWithID(roomEast))
   if roomWest != 'None':
      thisRoomObj.setAdjacentWest(getRoomWithID(roomWest))
   if roomUp != 'None':
      thisRoomObj.setAdjacentUp(getRoomWithID(roomUp))
   if roomDown != 'None':
      thisRoomObj.setAdjacentDown(getRoomWithID(roomDown))

def readRoomAdjacency():
   with open('csv/roomAdjList.csv','r') as f:
      for line in f:
        rLine = line.strip('\n')
        room = rLine.split(';')
        connectRooms(room[0],room[1],room[2],room[3],room[4],room[5],room[6])


readRoomDesc()
readRoomAdjacency()

iowDebugPrint (debugRooms, "[DEBUG_ROOMS]")
iowDebugPrint (debugRooms, RoomArray)

# NPCs
(getRoomWithID(5)).addNPCtoRoom(roxHorseE)
(getRoomWithID(6)).addNPCtoRoom(roxHorseW)
(getRoomWithID(7)).addNPCtoRoom(ttcAutomaton)
(getRoomWithID(7)).blockDirection("Down")
(getRoomWithID(9)).addNPCtoRoom(dorian)

#Storekeepers
(getRoomWithID(12)).addStoreKeeperToRoom(finius)

#Monsters
drunkenLudwig.addItems([dorianCoatOfArms])
(getRoomWithID(10)).addMonsterToRoom(drunkenLudwig)

