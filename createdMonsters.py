from engine.IOwrappers import *
from engine.Monster import *

# Monster Descriptions are of this format:
# <monster>Desc = [ monsterName, hitPoints, maxDamagePoints, attackDescription, ExperiencePoints, List of items held, Gold]

# Let's create some stock monsters

StockMonsterList = []

# format = Clock Bug;2;1;'nibbles';5;None;5

debugMonster = 0

def readMonsters():
   with open('csv/monsterList.csv','r') as f:
      for line in f:
        mLine = line.strip('\n') 
        monster = mLine.split(';')
        StockMonsterList.append(monster)      
        iowDebugPrint (debugMonster, monster)
readMonsters()

iowDebugPrint(debugMonster, "[DEBUG_MONSTERS]")
iowDebugPrint(debugMonster, StockMonsterList)
