import textwrap

viewer = None

# A viewer is any object exposing write(msg). Frontends (tuimain.py, ...)
# supply their own adapter around whatever widget they use.

def iowGetViewer():
   return viewer

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

def iowInput(cmd):
   return input(cmd)
