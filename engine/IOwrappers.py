import textwrap

viewer = None

# A viewer is any object exposing write(msg). The Pygame frontend
# (pygame_main.py) passes its ScrollLog widget directly, since it already
# exposes write(msg).

def iowSetViewer(vObject):
   global viewer
   viewer = vObject

def iowPrint(msg):
   if (viewer != None):
      viewer.write(msg)
   else:
      print (msg)

def iowWrapPrint(msg):
   if (viewer != None):
      dedented_text = textwrap.dedent(msg).strip()
      iowPrint (textwrap.fill(dedented_text, 80))
      iowPrint ("\n")

   else:
      print (msg)

def iowDebugPrint(debug, msg):
   if (debug):
      iowPrint(msg)
