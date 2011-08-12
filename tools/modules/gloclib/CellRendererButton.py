#!/usr/bin/env python
""" 
 A pushbutton widget that issues a signal when clicked. For use
 within a CellRenderer. Subclasses gtk.CellRendererText

 @author: Brendan Johan Lee
 @contact: brendajl@simula.no
 @version: 1.0
"""

import gtk
import gobject

class CellRendererButton( gtk.CellRendererText ):
    """ 
    A pushbutton widget that issues a signal when clicked. For use
    within a CellRenderer. Subclasses gtk.CellRendererText

    @author: Brendan Johan Lee
    @contact: brendajl@simula.no
    @version: 1.0
    """

    __gproperties__ = { "callable": ( gobject.TYPE_PYOBJECT,
                                      "callable property",
                                      "callable property",
                                      gobject.PARAM_READWRITE ) }
    _button_width = 40
    _button_height = 30

    def __init__( self , width, height):
        """ 
        Initialize the CellRendererButton class.

        @author: Brendan Johan Lee
        @contact: brendajl@simula.no
        @version: 1.0

        @param width: requested width of the button (defaults to 40 px)
        @type width: int
        @param height: requested height of the button (defaults to 20 px)
        @type height: int
        """

        self.__gobject_init__()
        gtk.CellRendererText.__init__( self )
        self._button_width = width
        self._button_height = height
        self.set_property( "xalign", 0.5 )
        self.set_property( "mode", gtk.CELL_RENDERER_MODE_ACTIVATABLE )
        self.callable = None
        self.table = None

    def do_set_property( self, pspec, value ):
        """ 
        Set a property of the button.

        @author: Brendan Johan Lee
        @contact: brendajl@simula.no
        @version: 1.0

        @param pspec: property to be set
        @type pspec: gtk.GParamSpec
        @param value: value to set the property to
        @type value: instancemethod

        @raise TypeError:  a callable property must be callable
        @raise AttributeError:  you tried to set a non-existing property
        """

        if pspec.name == "callable":
            if callable( value ):
                self.callable = value
            else:
                raise TypeError( "callable property must be callable!" )
        else:
            raise AttributeError( "Unknown property %s" % pspec.name )
        
    def do_get_property( self, pspec ):
        """ 
        Returns a property of the button.

        @author: Brendan Johan Lee
        @contact: brendajl@simula.no
        @version: 1.0

        @param pspec: property to be gotten
        @type pspec: gtk.GParamSpec

        @return: property of button
        @rtype: instancemethod

        @raise AttributeError: supplied property is non-existing
        """

        if pspec.name == "callable":
            return self.callable
        else:
            try: 
                return getattr(self,  pspec.name)
            except:
                raise AttributeError( "Unknown property %s" % pspec.name )

    def do_get_size( self, wid, cell_area ):
        """ 
        Get thesize of the button

        @author: Brendan Johan Lee
        @contact: brendajl@simula.no
        @version: 1.0

        @param wid: widget
        @type wid: gtk.Widget
        @param cell_area: cell area
        @type cell_area: gtk.gdk.Rectangle

        @return: horizontal position, vertical position, width, height
        @rtype: tupple
        """
        
        xpad = self.get_property( "xpad" )
        ypad = self.get_property( "ypad" )

        if not cell_area:
            x, y = 0, 0
            w = 2 * xpad + self._button_width
            h = 2 * ypad + self._button_height
        else:
            w = 2 * xpad + cell_area.width
            h = 2 * ypad + cell_area.height

            xalign = self.get_property( "xalign" )
            yalign = self.get_property( "yalign" )

            x = max( 0, xalign * ( cell_area.width - w ) )
            y = max( 0, yalign * ( cell_area.height - h ) )

        return ( x, y, w, h )

    def do_render( self, window, wid, bg_area, cell_area, expose_area, flags ):
        """ 
        Render the button

        @author: Brendan Johan Lee
        @contact: brendajl@simula.no
        @version: 1.0

        @param window: window to render in
        @type window: gtk.Window
        @param wid: widget to render in
        @type wid: gtk.Widget
        @param bg_area: background area
        @type bg_area: gtk.gdk.Rectangle
        @param cell_area: cell area
        @type cell_area: gtk.gdk.Rectangle
        @param expose_area: expose area
        @type expose_area: gtk.gdk.Rectangle
        @param flags: flags
        @type flags: gtk.CellRendererState
        """

        if not window:
            return

        xpad = self.get_property( "xpad" )
        ypad = self.get_property( "ypad" )

        x, y, w, h = self.get_size( wid, cell_area )

        state = gtk.STATE_NORMAL
        shadow = gtk.SHADOW_OUT
        wid.get_style().paint_box( window, state, shadow, cell_area,
                                   wid, "button",
                                   cell_area.x + x + xpad,
                                   cell_area.y + y + ypad,
                                   w - 6, h - 6 )
        flags = flags & ~gtk.STATE_SELECTED
        gtk.CellRendererText.do_render( self, window, wid, bg_area,
                                        (cell_area[0], cell_area[1] + ypad, cell_area[2],cell_area[3]), expose_area, flags )

    def do_activate( self, event, wid, path, bg_area, cell_area, flags ):
        """ 
        Activate the button

        @author: Brendan Johan Lee
        @contact: brendajl@simula.no
        @version: 1.0

        @param event: event that caused this callback
        @type event: gtk.Event
        @param wid: widget that caused this callback
        @type wid: gtk.Widget
        @param path: path
        @type path: str
        @param bg_area: background area
        @type bg_area: gtk.gdk.Rectangle
        @param cell_area: cell area 
        @type cell_area: gtk.gdk.Rectangle
        @param flags: flags
        @type flags: gtk.CellRendererState

        @return: success
        @rtype: bool
        """
        cb = self.get_property( "callable" )
        if cb != None :
            cb (path)
        return True

gobject.type_register( CellRendererButton )
