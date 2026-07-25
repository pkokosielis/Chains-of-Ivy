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
dorian.addQuoteBeforeQuest("That drunken scallywag Ludwig Bastille took my family's coat of arms that was displayed by the entrance.")
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

#Henriette of Versailles
JLWatch = Item("JL Watch", "Watch", 5)
JLWatch.setItemValue(25000)
VCWatch = Item("VC Watch", "Watch", 8)
VCWatch.setItemValue(85000)
mysticRing = Item("Mystic Ring", "Ring", 10)
mysticRing.setItemValue(135000)
henriette = StoreKeeper("Henriette", "Patachou of Versailles")
henriette.setWelcomeMessage("Welcome to Patachou's treasures of Versailles. Please have a look around.")
henriette.setThanksMessage("An excellent choice, fit for a king!")
henriette.addItem([JLWatch,VCWatch,mysticRing])

# The Summerhill chain. Corvin Slake robs the tower and the station, and
# carries both the winding crank and the signal staff. Ambrose pays out in
# the gauge glass, which is itself Ezra's quest item, so the three link up
# the same way Dorian's TTC pass feeds the turnstile automaton.
windingCrank = Item("winding crank", "crank", 1)
signalStaff = Item("signal staff", "staff", 1)
gaugeGlass = Item("gauge glass", "glass", 1)

# Wilhelmina Roke, keeper of the North Toronto clock tower
keeperBoots = Item("Keeper's Climbing Boots", "Boots", 6)
keeperBoots.setItemValue(900)
wilhelmina = NPC("Wilhelmina Roke the tower keeper", 1200, 150)
wilhelmina.addQuoteBeforeQuest("I am Wilhelmina Roke. Ninety-one years my family has wound this clock, and it had never once stopped.")
wilhelmina.addQuoteBeforeQuest("It has stopped now. A thief took the winding crank three days past, and I heard him go down the stair two at a time.")
wilhelmina.addQuoteBeforeQuest("Without the crank the going train runs down, and half of Rosedale loses the quarter hours.")
wilhelmina.addQuoteBeforeQuest("Bring me that crank and I will see you properly shod.")
wilhelmina.setThanksMessage("Bless you! The crank, and the tower keeps time again. Take these boots - I have climbed this stair sixty years and I know what it does to a pair. They will serve you better than they serve me now.")
wilhelmina.addQuoteAfterQuest("Listen to that. The quarter hours, right on the dial. That is your doing.")
wilhelmina.addQuoteAfterQuest("Mind the louvres if the wind gets up. It has taken the hat off better men than you.")
wilhelmina.addItems([keeperBoots])
windingCrank.setQuestForNPC(wilhelmina)

# Ezra Vance, engineer of the Rosehill pumping house
pumpSpanner = Item("brass pump spanner", "Weapon", 14)
pumpSpanner.setItemValue(1400)
ezra = NPC("Ezra Vance the reservoir engineer", 2500, 500)
ezra.addQuoteBeforeQuest("Ezra Vance. I keep the beam engine, and the beam engine keeps the water above the city.")
ezra.addQuoteBeforeQuest("She has been running blind a fortnight. The gauge glass cracked and the replacement sits in the parcels office at the station.")
ezra.addQuoteBeforeQuest("Quill will not send a boy up the hill with it. Too busy, he says, with that precious Montreal train of his.")
ezra.addQuoteBeforeQuest("Bring me a gauge glass and you will not find me ungrateful.")
ezra.setThanksMessage("Now that is a handsome piece of glass. She will hold pressure honestly again. Here, take the spanner - eleven pounds of brass and it has never yet rounded a nut. You will find it useful for more than nuts.")
ezra.addQuoteAfterQuest("Steady as a heartbeat, listen to her. Forty strokes to the minute and not one of them wasted.")
ezra.addQuoteAfterQuest("The Vale runs black below the far parapet. I would not go down there after dark.")
ezra.addItems([pumpSpanner])
gaugeGlass.setQuestForNPC(ezra)

# Ambrose Quill, stationmaster of the North Toronto railway station
ambrose = NPC("Ambrose Quill the stationmaster", 2000, 300)
ambrose.addQuoteBeforeQuest("Ambrose Quill, stationmaster, and I am in a very great deal of trouble.")
ambrose.addQuoteBeforeQuest("The boat train for Montreal has stood at the platform two days. I cannot dispatch her without the signal staff.")
ambrose.addQuoteBeforeQuest("No staff, no train on the single line. That is the rule, and the rule is all that keeps them from meeting head-on in the dark.")
ambrose.addQuoteBeforeQuest("The same wretch who robbed the tower took it. He is somewhere about the shed, I am certain of it.")
ambrose.setThanksMessage("The staff! Oh, well done. She can move at last. Here - take this gauge glass from the parcels office. It came up on the mail for Vance at the reservoir and he has badgered me for it a fortnight. Carry it to him and spare me the letters.")
ambrose.addQuoteAfterQuest("The Montreal train got away clean on Tuesday. First time in a month.")
ambrose.addQuoteAfterQuest("If you are going up the hill to the reservoir, Vance will be glad of that glass.")
ambrose.addItems([gaugeGlass])
signalStaff.setQuestForNPC(ambrose)  
