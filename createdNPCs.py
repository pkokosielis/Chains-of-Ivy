from engine.NPC import * 
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

roxHorseE = NPC("A mechanical horse emanating steam", 0, 0)
roxHorseE.addQuoteBeforeQuest("I can take you west to the Rebellion House on Yonge")
roxHorseE.addQuoteBeforeQuest("Are you going west? I will shuttle you along Roxborough street.")

roxHorseW = NPC("A mechanical horse emanating steam", 0, 0)
roxHorseW.addQuoteBeforeQuest("I can take you east to the Chorley Park mansion.")
roxHorseW.addQuoteBeforeQuest("Are you going east? I will shuttle you along Roxborough street.")
 
