""" 
 Collection of general methods for drawing maps

 @author: Brendan Johan Lee
 @contact: brendajl@simula.no
 @version: 1.0
"""
## GNU General Public Licence (GPL)
 
## This program is free software; you can redistribute it and / or modify it under
## the terms of the GNU General Public License as published by the Free Software
## Foundation; either version 2 of the License,  or (at your option) any later
## version.
## This program is distributed in the hope that it will be useful,  but WITHOUT
## ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
## FOR A PARTICULAR PURPOSE.  See the GNU General Public License for more
## details.
## You should have received a copy of the GNU General Public License along with
## this program; if not,  write to the Free Software Foundation,  Inc.,  59 Temple
## Place,  Suite 330,  Boston,  MA  02111 - 1307  USA

import cairo
import gtk
from mapConst import *

def add_tile(overlays,mapcontext,x,y,img,tile_coord,region,mapcenter, debug = False):
    """ 
    Add a tile to an image and draw any active overlays on top of it.

    @author: Brendan Johan Lee
    @contact: brendajl@simula.no
    @version: 1.0

    @param overlays: overlays to be possibly be drawn on top of tile
    @type overlays: MapOverlayListModel
    @param mapcontext: context to draw tile on
    @type mapcontext: gtk.gdk.CairoContext
    @param x: horizontal position to draw tile
    @type x: int
    @param y: vertical position to draw tile
    @type y: int
    @param img: tile to draw on image
    @type img: gtk.gdk.Pixbuf
    @param tile_coord: tile coordinates
    @type tile_coord: list
    @param region: region of map
    @type region: list
    @param mapcenter: center position of map
    @type mapcenter: tupple
    @param debug: draw a black rectangle around tile (so we can distinguish where tiles are placed on image)
    @type debug: bool
    """
    
    mapcontext.set_source_pixbuf(img,x,y)
    mapcontext.paint()

    for overlay in overlays:
        if overlay.visible:
            pos = overlay.gettilecoord(tile_coord,region,mapcenter)
            if pos:
                mapcontext.set_source_surface(overlay.surface,pos[0]*TILES_WIDTH,pos[1]*TILES_HEIGHT)
                mapcontext.rectangle(x,y,TILES_WIDTH,TILES_HEIGHT)
                mapcontext.fill()

    if debug: 
        mapcontext.rectangle(x,y,255,255)             
        mapcontext.set_source_rgb(0, 0, 0)           
        mapcontext.set_line_width(2.0)
        mapcontext.stroke()
