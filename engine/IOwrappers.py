import sys
from tkinter import *

iField = None
viewer = None 

def py34orLater():
   return sys.hexversion >= 0x03040000   

def iowSetInput(iObject):
   global iField 
   iField = iObject

def iowGetViewer():
   return viewer

def iowSetViewer(vObject):
   global viewer
   viewer = vObject

def iowPrint(msg):
   if (viewer != None):
   	iowPrintViewer(msg)
   else:
      print (msg)

def iowPrintViewer(msg):
   global viewer
   viewer['state'] = 'normal'
   viewer.insert(END, "\n" + msg)
   viewer.see(END)
   viewer['state'] = 'disabled'
   iField.focus_set()

def iowDebugPrint(debug, msg):
   if (debug):
      iowPrint(msg)

def iowInput(cmd):
   if (py34orLater()):
      return input(cmd)
   else:
      return raw_input(cmd)        
