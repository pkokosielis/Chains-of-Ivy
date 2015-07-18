from engine.NPC import * 
from engine.StoreKeeper import *
from createdMonsters import *

# TTC Automaton 
# NPC(name, experience, gold)
ttcPass = Item("TTC pass", "Pass", 1)
ttcAutomaton = NPC("TTC Automaton", 5000, 0)
ttcAutomaton.addQuoteBeforeQuest("Hello sir. I need you to show me a valid TTC pass.") 
ttcAutomaton.addQuoteBeforeQuest("The Yonge subway line is just downstairs.")
ttcAutomaton.addQuoteBeforeQuest("You can't cross the turnstyle gate without a pass.") 
ttcAutomaton.addQuoteAfterQuest("The Yonge subway line is just downstairs. Summerhill to the north, Bloor to the south.")
ttcAutomaton.setThanksMessage("Thank you sir. You may now travel the subway. Please make your way downstairs to the platform.")
ttcPass.setQuestForNPC(ttcAutomaton)

# A random crow for decoration
crow = NPC("An ominous crow", 0, 0)

# The mechanical horse on Roxborough st
roxHorseE = NPC("A mechanical horse emanating steam", 0, 0)
roxHorseE.addQuoteBeforeQuest("I can take you west to the Rebellion House on Yonge")
roxHorseE.addQuoteBeforeQuest("Are you going west? I will shuttle you along Roxborough street.")

roxHorseW = NPC("A mechanical horse emanating steam", 0, 0)
roxHorseW.addQuoteBeforeQuest("I can take you east to the Chorley Park mansion.")
roxHorseW.addQuoteBeforeQuest("Are you going east? I will shuttle you along Roxborough street.")

# Dorian the Rebellion House propietor
dorianCoatOfArms = Item("coat of arms", "coat of arms", 1)
dorian = NPC("Dorian the fine fare merchant", 6000, 0)
dorian.addQuoteBeforeQuest("Hello fine sir, I am Dorian Blythe the owner of this establishment.")
dorian.addQuoteBeforeQuest("That drunken scallywag Ludwig Ironfeld took my family's coat of arms that was displayed by the entrance.")
dorian.addQuoteBeforeQuest("Ludwig is terrorizing my patrons upstairs! Curse he!")
dorian.addQuoteBeforeQuest("If only I could get my coat of arms back!")
dorian.setThanksMessage("Praise be on to ye!! My coat of arms!! Please accept this TTC pass as a token of my gratitude. It will give you unlimited access to the TTC subway system.")
dorian.addQuoteAfterQuest("Hello Hugo! You are always welcome in my establishment!")
dorian.addQuoteAfterQuest("Things have been much smoother here since you did away with that ruffneck Ludwig!")
dorian.addItems([ttcPass])
dorianCoatOfArms.setQuestForNPC(dorian) 

# Finius the Potion Master at the Five Thieves
absynthe = Item("Absynthe", "Scroll", 8)
absynthe.setItemValue(25)
lagavul = Item("Lavagul", "Scroll", 16)
lagavul.setItemValue(5000)
finius = StoreKeeper("Finius", "All the Finest Potions")
finius.setWelcomeMessage("Welcome to my humble shop. I am Finius, how can I assist you?")
finius.setThanksMessage("Your business is most appreciated!")
finius.addItem([absynthe,lagavul])
