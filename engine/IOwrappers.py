import textwrap
import sys
from tkinter import *

iField = None
viewer = None 

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

def iowWrapPrint(msg):
   if (viewer != None):
      dedented_text = textwrap.dedent(msg).strip()
      iowPrint (textwrap.fill(dedented_text, 80))
      iowPrint ("\n")
 
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
   return input(cmd)
