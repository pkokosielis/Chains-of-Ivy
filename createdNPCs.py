from engine.NPC import * 
from createdMonsters import *

#Jurvius the Pale
# NPC(name, experience, gold)
jurvius = NPC("Jurvius the Pale", 2000, 4500)
jurvius.addQuoteBeforeQuest("I am Jurvius the Pale. How do you do?") 
jurvius.addQuoteBeforeQuest("A sordid mob evicted me from the tower!")
jurvius.addQuoteBeforeQuest("Please recover my amulet from the evil lich inside!") 
jurvius.addQuoteAfterQuest("All hail to you mighty hero!")
jurvius.setThanksMessage("My precious amulet!! Thank you!! Your quest is fulfilled! Please accept a token of appreciation.")
#amulet.setQuestForNPC(jurvius)

# A random crow for decoration
crow = NPC("An ominous crow", 0, 0)

roxHorseE = NPC("A mechanical horse emanating steam", 0, 0)
roxHorseE.addQuoteBeforeQuest("I can take you west to the Rebel House on Yonge")
roxHorseE.addQuoteBeforeQuest("Are you going west? I will shuttle you along Roxborough street.")

roxHorseW = NPC("A mechanical horse emanating steam", 0, 0)
roxHorseW.addQuoteBeforeQuest("I can take you east to the Chorley Park mansion.")
roxHorseW.addQuoteBeforeQuest("Are you going east? I will shuttle you along Roxborough street.")
 
