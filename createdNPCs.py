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

# Finius the Potion Master at the Five Thieves apothecary
absynthe = Item("Absynthe", "Scroll", 8)
absynthe.setItemValue(25)
lagavul = Item("Lavagul", "Scroll", 16)
lagavul.setItemValue(5000)
finius = StoreKeeper("Finius", "All the Finest Potions")
finius.setWelcomeMessage("Welcome to my humble shop. I am Finius, how can I assist you?")
finius.setThanksMessage("Your business is most appreciated!")
finius.addItem([absynthe,lagavul])

# Asimenia the Harvest Metalworks proprietor
baton = Item("studded baton", "Weapon", 6)
baton.setItemValue(125)
silverDagger = Item("silver dagger", "Weapon", 12)
silverDagger.setItemValue(850)
goldDagger = Item("gold dagger", "Weapon", 20)
goldDagger.setItemValue(2500)
asimenia = StoreKeeper("Asimenia", "Harvest Metalworks")
asimenia.setWelcomeMessage("Welcome to the only place to buy works of fine metal. I am Asimenia. I am sure you will find the prices most... fair.")
asimenia.setThanksMessage("Thank you for your patronage. May this item serve you well.")
asimenia.addItem([baton,silverDagger,goldDagger])

# Cedric the Aries Haberdashery propietor
dusterCoat = Item("Duster Coat", "Suit", 1)
dusterCoat.setItemValue(285)
operaCoat = Item("Opera Coat", "Suit", 3)
operaCoat.setItemValue(585)
tweedCoat = Item("Tweed Coat", "Suit", 12)
tweedCoat.setItemValue(2450)
cedric = StoreKeeper("Cedric", "Aries Haberdashery")
cedric.setWelcomeMessage("The finest threads can only be found here. Welcome to my haberdashery. I am Cedric. How can I be of help?")
cedric.setThanksMessage("Wear it well! Godspeed my friend.")
cedric.addItem([dusterCoat,operaCoat,tweedCoat])

#Olaff the Milliner
newsBoyCap = Item("Tweed Newsboy Cap", "Helmet", 2)
newsBoyCap.setItemValue(135)
aviatorCap = Item("Leather Aviator Cap", "Helmet", 6)
aviatorCap.setItemValue(1250)
bronzeHelmet = Item("Bronze Helmet", "Helmet", 12)
bronzeHelmet.setItemValue(4500)
olaff = StoreKeeper("Olaff", "Olaff's Millinery")
olaff.setWelcomeMessage("Welcome to my millinery. I am Olaff purveyor of fine headgear. How can I be of help?")
olaff.setThanksMessage("Blessed be!")
olaff.addItem([newsBoyCap,aviatorCap,bronzeHelmet])
