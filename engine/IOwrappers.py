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
      # Deliberately not hard-wrapped to a fixed column count here (that
      # used to assume an 80-column terminal) - the viewer wraps by its
      # own actual pixel width. Pre-wrapping to 80 columns and letting
      # the viewer wrap *again* at a narrower width routinely orphaned a
      # short trailing word or number onto its own line.
      dedented_text = textwrap.dedent(msg).strip()
      iowPrint (dedented_text)
      iowPrint ("\n")

   else:
      print (msg)

def iowDebugPrint(debug, msg):
   if (debug):
      iowPrint(msg)
