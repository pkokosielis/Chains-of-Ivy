#!/usr/bin/python
import sys, os
from tkinter import *
from tkinter import ttk
import tkinter.scrolledtext as tkst
from tkinter.filedialog import askopenfilename
from tkinter.filedialog import asksaveasfilename
from tkinter.messagebox import askquestion 

from engine.IOwrappers import *
from engine.PlayerAction import *
from createdMonsters import *
from createdNPCs import *
from createdRooms import *

def quitGame():
   if (askquestion("Quit?", "Are you sure?") == 'yes'):
      sys.exit(0)    

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

currentRoom = None
currentPlayer = None
nextAction = None

def restoreGame():
   global currentRoom
   global currentPlayer
   global nextAction
   filename = askopenfilename()
   if filename:
      savedState = nextAction.doRestoreTk(currentRoom, currentPlayer, filename)
      currentRoom = savedState[0]
      currentPlayer = savedState[1]

def saveGame():
   global currentRoom
   global currentPlayer
   global nextAction 
   filename = asksaveasfilename()
   if filename:
      nextAction.doSaveTk(currentRoom, currentPlayer, filename)

def doNextAction(iField):
   global currentRoom
   global currentPlayer
   global nextAction
   action = iField.get()
   iowPrintViewer("[ACTION]: " + action)
   currentRoom = nextAction.doAction(currentRoom, currentPlayer, action)
   iField.delete(0, END)

def main():
 
   global currentRoom
   global currentPlayer
   global nextAction
 
   root = Tk()
   root.title("Chains of Ivy")

   mainframe = ttk.Frame(root, padding = "3 3 12 12")
   mainframe.grid(column=0, row =0, sticky=(N, W, E, S))
   mainframe.columnconfigure(0, weight=1)
   mainframe.rowconfigure(0, weight=1)

   #top level menu
   menubar = Menu(root, tearoff=0)
   
   #file menu
   filemenu = Menu(menubar, tearoff=0)
   filemenu.add_command(label="Open", command=restoreGame)
   filemenu.add_command(label="Save", command=saveGame)
   filemenu.add_separator()
   filemenu.add_command(label="Exit", command=quitGame)
   menubar.add_cascade(label="File", menu=filemenu)

   #help menu
   helpmenu = Menu(menubar, tearoff=0)
   helpmenu.add_command(label="About", command=showBanner)
   menubar.add_cascade(label="Help", menu=helpmenu)
   
   # display the menu
   root.config(menu=menubar)

   #viewer
   actionViewer = tkst.ScrolledText(mainframe, state='normal', width=85, height=24, wrap='none')
   actionViewer.grid(column=2, row=1, sticky=(W,E))
   actionViewer.vbar.config(command=actionViewer.yview)
   actionViewer['state'] = 'disabled'
   iowSetViewer(actionViewer)

   #input box
   userAction = StringVar()
   userInput = ttk.Entry(mainframe, width=32, textvariable=userAction)
   userInput.grid(column=2, row=2, sticky=(W,E))
   userInput.bind("<Return>",(lambda event: doNextAction(userInput)))
   iowSetInput(userInput)

   #reserved
   inputAction = "This space intentionally left blank"
   actionLabel = ttk.Label(mainframe, text=inputAction)
   actionLabel.grid(column=1, row=2, sticky=(W,E))

   #graphics viewer
   bannerLabel = ttk.Label(mainframe, text="")
   banner = PhotoImage(file="img/chainsOfIvy.gif")
   bannerLabel['image'] = banner
   bannerLabel.grid(column=1, row=1, sticky=(W,E))

   # Start Game
 
   nextAction = PlayerAction()
   initialSetting = initSetting()
   currentRoom = initialSetting[0]
   currentPlayer = initialSetting[1]
   currentRoom.displayRoom()

   root.mainloop()  
   return

main()
