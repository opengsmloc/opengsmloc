## @package src.gtkThread
# ---

import sys
import pygtk
pygtk.require('2.0')
import gtk, gobject
from threading import Timer

gtk.gdk.threads_init()
do_gui_operation=gobject.idle_add

## may be used as decorator
def gui_callback(function):
    def cb(inGuiThread, *args, **kwargs):
        if inGuiThread:
            function(*args, **kwargs)
        else:
            do_gui_operation(function, *args, **kwargs)
    return cb

## Open the given page in a browser
def webbrowser_open(strPage):
    def openThread():
        import webbrowser
        webbrowser.open(strPage)
    try:
        oThread = Timer(0, openThread)
        oThread.start()
    except:
        pass
