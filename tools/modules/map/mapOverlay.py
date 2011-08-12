#!/usr/bin/env python
""" 
 Provides MapOverlay - the class used for generating any type of overlays on
 a map (as of now points, polygon, filled polygon and tracks)

 Provides MapOverlayListModel - a class representing collections of map
 overlays sub classing GenericTreeModel.

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

import gloclib.algorithms as algorithms
import map.mapUtils as mapUtils
from mapConst import *
import cairo
from math import pi
import pygtk
import gtk
from gloclib.CellRendererButton import CellRendererButton

class MapOverlay:
    """ 
    A class representing overlays on a map. As of now supports points, polygons
    filled polygons and tracks.

    @author: Brendan Johan Lee
    @contact: brendajl@simula.no
    @version: 1.0
    """

    overlaytype = TYPE_POINTS

    def __init__(self,name,foundation,dataset,zoomlevel,mapcenter,overlaytype=TYPE_POINTS, color=(1,0,0,0.35), hulls=False):
        """ 
        Initialize MapOverlay

        @author: Brendan Johan Lee
        @contact: brendajl@simula.no
        @version: 1.0

        @param name: human readable name of overlay
        @type name: str
        @param foundation: id of foundation type (see mapConst.py for foundation types)
        @type foundation: int
        @param dataset: dataset representing the points of the overlay
        @type dataset: dict or list
        @param zoomlevel: the zoom level of the map
        @type zoomlevel: int
        @param mapcenter: the center position of the map
        @type mapcenter: tupple
        @param overlaytype: type of overlay (see mapConst.py for types)
        @type overlaytype: int
        @param color: rgba color of overlay
        @type color: tupple
        @param hulls: render a convex hull of the dataset instead of the dataset itself
        @type hulls: bool
        
        @todo: The see mapConst.py should be an actual link to the static variable
        """

        self.dataset = dataset
        if hulls:
            if type(self.dataset[0]).__name__=='DictRow' or type(self.dataset[0]).__name__=='dict':
                self.dataset = algorithms.hulls([(x['latitude'],x['longitude']) for x in self.dataset])
            else:
                self.dataset = algorithms.hulls(self.dataset)
        self.color = color
        if self.color[0] > 1 or self.color[1] > 1 or self.color[2] > 1 or self.color[3] > 1:
            self.color = [float(x)/65535 for x in self.color]
        self.render(zoomlevel,mapcenter)
        self.overlaytype = overlaytype
        self.name = name
        self.visible = True
        self.foundation = foundation
        self.area = None

    def __calculate_buffer_size__(self,zoomlevel,mapcenter):
        """ 
        Calculate the needed buffer image size. Calculates and sets the bounds, width
        and hight values of the MapOverlay

        @author: Brendan Johan Lee
        @contact: brendajl@simula.no
        @version: 1.0

        @param zoomlevel: zoom level of map
        @type zoomlevel: int
        @param mapcenter: center point of the map
        @type mapcenter: tupple
        """

        self.bounds = (mapcenter[0][0]-(LAYER_BUFFER_TILES/2),mapcenter[0][1]-(LAYER_BUFFER_TILES/2),
                      mapcenter[0][0]+(LAYER_BUFFER_TILES/2),mapcenter[0][1]+(LAYER_BUFFER_TILES/2))
        self.width = (LAYER_BUFFER_TILES+1)*TILES_WIDTH
        self.height = (LAYER_BUFFER_TILES+1)*TILES_HEIGHT

    def render(self,zoomlevel,mapcenter):
        """ 
        Renders the overlay on the buffer image.

        @author: Brendan Johan Lee
        @contact: brendajl@simula.no
        @version: 1.0

        @param zoomlevel: zoom level of map
        @type zoomlevel: int
        @param mapcenter: center point of the map
        @type mapcenter: tupple
        """

        self.zoomlevel = zoomlevel
        self.affectedtiles = {}
        self.affectednotrendered = {}
        self.__calculate_buffer_size__(zoomlevel,mapcenter)
        self.surface = cairo.ImageSurface(cairo.FORMAT_ARGB32, self.width, self.height)
        self.context = cairo.Context(self.surface)

        affected = []
        self.area = []

        self.prevpoint = None

        print "color: ", self.color
        self.context.set_source_rgba(*self.color)
        if self.overlaytype == TYPE_POLYGON or self.overlaytype == TYPE_FILLEDPOLYGON:
            self.context.set_line_width(3)

        for point in self.dataset:
            if type(point).__name__=='DictRow' or type(point).__name__=='dict':
                if not point['latitude'] or not point['longitude']: 
                    continue
                dp = mapUtils.coord_to_tile((point['latitude'],point['longitude'],zoomlevel))
                self.area.append((point['latitude'],point['longitude']))
            elif type(point).__name__=='tuple':
                dp = mapUtils.coord_to_tile((point[0],point[1],zoomlevel))
                self.area.append((point[0],point[1]))
            else:
                return

            x = ((dp[0][0]-self.bounds[0])*TILES_WIDTH)+dp[1][0]
            y = ((dp[0][1]-self.bounds[1])*TILES_HEIGHT)+dp[1][1]

            if self.overlaytype == TYPE_POLYGON or self.overlaytype == TYPE_FILLEDPOLYGON:
                self.context.line_to(x,y)

            if dp[0][0] > self.bounds[0] and dp[0][0] < self.bounds[2] and dp[0][1] > self.bounds[1] and dp[0][1] < self.bounds[3]:
                if not(self.overlaytype == TYPE_POLYGON or self.overlaytype == TYPE_FILLEDPOLYGON):
                    if len(point) > 2:
                        try: 
                            self.context.set_source_rgba(*point[2])
                        except:
                            pass
                    self.context.arc(x,y,3-zoomlevel if 3 - zoomlevel > 0 else 3,0,2*pi)
                    self.context.fill()
                    if self.overlaytype == TYPE_PATH and self.prevpoint:
                        self.context.move_to(*self.prevpoint)
                        self.context.line_to(x, y)
                        self.context.stroke()
                        self.context.close_path()
                    self.prevpoint = (x, y)
            else: 
                self.affectednotrendered[dp[0][0],dp[0][1]] = True

            affected.append((dp[0][0],dp[0][1]))
            # mark tiles that point overlaps into as "dirty"
            dx = ((x-(15-zoomlevel))/TILES_WIDTH, x/TILES_WIDTH, (x+(15-zoomlevel))/TILES_WIDTH)
            dy = ((y-(15-zoomlevel))/TILES_HEIGHT, y/TILES_HEIGHT, (y+(15-zoomlevel))/TILES_HEIGHT)
            tx = x/TILES_WIDTH;
            ty = y/TILES_HEIGHT;
            for a in dx:
                for b in dy:
                    if not a==tx or not b==ty:
                        #TODO: This will not work if the tile happens to be just at the edge of the buffer
                        affected.append((dp[0][0]+(a-tx),dp[0][1]+(b-ty)))

        
        if self.overlaytype == TYPE_POLYGON:
            self.context.stroke()
        elif self.overlaytype == TYPE_FILLEDPOLYGON:
            self.context.close_path()
            self.context.fill()
        
        if self.overlaytype == TYPE_POLYGON or self.overlaytype == TYPE_FILLEDPOLYGON or self.overlaytype == TYPE_PATH:
            minx = sorted(affected, key=lambda x:(x[0]))[0][0]
            maxx = sorted(affected, key=lambda x:(x[0]))[-1][0]
            miny = sorted(affected, key=lambda x:(x[1]))[0][1]
            maxy = sorted(affected, key=lambda x:(x[1]))[-1][1]
            for a in range(minx,maxx+1):
                for b in range(miny,maxy+1):
                    self.affectedtiles[(a,b)] = True
                    if not(a > self.bounds[0] and a < self.bounds[2] and b > self.bounds[1] and b < self.bounds[3]):
                        self.affectednotrendered[a,b] = True

        else:
            for tile in affected:
                if tile not in self.affectedtiles:
                    self.affectedtiles[tile] = True

    def get_area(self):
        """ 
        Get the area this overlay extends over.

        @author: Brendan Johan Lee
        @contact: brendajl@simula.no
        @version: 1.0

        @return: vertical minimum, maximum, horizontal minimum, maximum
        @rtype: tupple
        """

        minx = sorted(self.area, key=lambda x:(x[0]))[0][0]
        maxx = sorted(self.area, key=lambda x:(x[0]))[-1][0]
        miny = sorted(self.area, key=lambda x:(x[1]))[0][1]
        maxy = sorted(self.area, key=lambda x:(x[1]))[-1][1]
        return (minx,maxx,miny,maxy)
 
    def gettilecoord(self,coord,region,mapcenter):
        """ 
        Return the coordinates of a tile

        @author: Brendan Johan Lee
        @contact: brendajl@simula.no
        @version: 1.0

        @param coord: coordinate
        @type coord: list
        @param region: region
        @type region: list
        @param mapcenter: center of map
        @type mapcenter: tupple

        @return: vertical coordinate, horizontal coordinate
        @rtype: tupple
        """

        if (coord[0],coord[1]) in self.affectednotrendered:
            self.render(self.zoomlevel,mapcenter)
        if (coord[0],coord[1]) not in self.affectedtiles:
            return None
        xdiff = self.bounds[0]-region[0]
        ydiff = self.bounds[1]-region[2]
        return (xdiff,ydiff)

    def set_color(self,r,g,b,a=0.35):
        """ 
        Change the color of this overlay

        @author: Brendan Johan Lee
        @contact: brendajl@simula.no
        @version: 1.0

        @param r: red component
        @type r: float
        @param g: green component
        @type g: float
        @param b: blue component
        @type b: float
        @param a: alpha component
        @type a: float
        """

        self.color = (r,g,b,a)

def getbounds(points):
    """ 
    Calculates boundaries around a set of points given by
    latitude and longitude. In other words, calculate the smallest box
    that surrounds all of the points.

    @author: Brendan Johan Lee
    @contact: brendajl@simula.no

    @version: 1.0

    @param points: points to calculate boundaries around
    @type points: list of tupples containing at least latitude and longitude (eg. return value of getcellobservations())

    @return: (longitudemin, latitudemin, longitudemax, latitudemax)
    @rtype: tupple
    @todo: Should be moved to an algorithm module
    """

    latmin = lonmin = 1000
    latmax = lonmax = 0
    for entry in points:
        if entry['latitude'] < latmin: latmin = entry['latitude']
        if entry['latitude'] > latmax: latmax = entry['latitude']
        if entry['longitude'] < lonmin: lonmin = entry['longitude']
        if entry['longitude'] > lonmax: lonmax = entry['longitude']
    return (lonmin, latmin, lonmax, latmax)

class MapOverlayListModel(gtk.GenericTreeModel):
    """ 
    Class representing a collection of MapOverlays,  sub classes GenericTreeModel
    so that a list of the map overlays can be rendered directly in a list widget.

    @author: Brendan Johan Lee
    @contact: brendajl@simula.no
    @version: 1.0
    
    @todo: Need delete methods, move methods, etc see http://www.pygtk.org/pygtk2tutorial/sec-GenericTreeModel.html for moving
    """

    column_types = [bool, str, str, str, gtk.gdk.Pixbuf, str, object, str, object]
    column_names = ['Visible', 'Name', 'Foundation', 'Type', 'Color', 'Zoom button', 'Zoom button function', 'Delete button', 'Delete button function']
    overlays = []

    def __init__(self, button1callback, button2callback):
        """ 
        Initialize the MapOverlayListModel

        @author: Brendan Johan Lee
        @contact: brendajl@simula.no
        @version: 1.0

        @param button1callback: callback function for the first button
        @type button1callback: function
        @param button2callback: callback function for the second button
        @type button2callback: function
        """

        gtk.GenericTreeModel.__init__(self)
        self.button1callback = button1callback
        self.button2callback = button2callback

    def add(self, overlay):
        """ 
        Add a new overlay to the overlay store.

        @author: Brendan Johan Lee
        @contact: brendajl@simula.no
        @version: 1.0

        @param overlay: overlay to be added
        @type overlay: MapOverlay
        """

        self.overlays.append(overlay)
        path = self.overlays.index(overlay)
        iter = self.get_iter(path)
        self.row_inserted(path, iter)

    def remove(self, overlay):
        """ 
        Remove an overlay from the overlay store

        @author: Brendan Johan Lee
        @contact: brendajl@simula.no
        @version: 1.0

        @param overlay: id / path of overlay to be removed
        @type overlay: castable to int
        """

        del self.overlays[int(overlay)]
        self.row_deleted(int(overlay))

    def toggle(self, overlay):
         """ 
         Toggle the visibility of an overlay

         @author: Brendan Johan Lee
         @contact: brendajl@simula.no
         @version: 1.0

         @param overlay: id / path of overlay to be toggled
         @type overlay: castable to int
         """

         self.overlays[int(overlay)].visible = not self.overlays[int(overlay)].visible

    def get_area(self, overlay):
        """ 
        Return the area an overlay resides within

        @author: Brendan Johan Lee
        @contact: brendajl@simula.no
        @version: 1.0

        @param overlay: id / path of overlay to retrieve area from
        @type overlay: castable to in

        @return: vertical minimum, maximum, horizontal minimum, maximum
        @rtype: tupple
        """
        return self.overlays[int(overlay)].get_area()

    def get_column_names(self):
        """ 
        Return a list of the column names.

        @author: Brendan Johan Lee
        @contact: brendajl@simula.no
        @version: 1.0

        @return: column names
        @rtype: list
        """
        return self.column_names[:]

    def on_get_flags(self):
        """ 
        Return flags

        @author: Brendan Johan Lee
        @contact: brendajl@simula.no
        @version: 1.0

        @return: flags
        @rtype: gtk.TreeModelFlags
        """
        return gtk.TREE_MODEL_LIST_ONLY|gtk.TREE_MODEL_ITERS_PERSIST

    def on_get_n_columns(self):
        """ 
        Return number of columns

        @author: Brendan Johan Lee
        @contact: brendajl@simula.no
        @version: 1.0

        @return: number of columns
        @rtype: int
        """

        return len(self.column_types)

    def on_get_column_type(self, n):
        """ 
        Return type of column

        @author: Brendan Johan Lee
        @contact: brendajl@simula.no
        @version: 1.0

        @param n: number of column
        @type n: int

        @return: type of column
        @rtype: type
        """
        return self.column_types[n]

    def on_get_iter(self, path):
        """ 
        Return iteration instance

        @author: Brendan Johan Lee
        @contact: brendajl@simula.no
        @version: 1.0

        @param path: path
        @type path: tupple

        @return: iteration instance
        @rtype: instance
        """
        if len(self.overlays)>path[0]:
            return self.overlays[path[0]]

    def on_get_path(self, rowref):
        """ 
        Return path based on rowref

        @author: Brendan Johan Lee
        @contact: brendajl@simula.no
        @version: 1.0

        @param rowref: rowref pointing to row
        @type rowref: gtk.TreeRowReference

        @return: path
        @rtype: int
        """
        print type(rowref).__name__
        print type(self.overlays.index(rowref)).__name__
        return self.overlays.index(rowref)

    def on_get_value(self, rowref, column):
        """ 
        Get the value of a cell.

        @author: Brendan Johan Lee
        @contact: brendajl@simula.no
        @version: 1.0

        @param rowref: rowref pointing to row
        @type rowref: gtk.TreeRowReference
        @param column: number of column 
        @type column: int

        @return: value of cell
        @rtype: any type
        """

        if column == 0:
            return rowref.visible
        elif column == 1:
            return rowref.name
        elif column == 2:
            return FOUNDATIONS[rowref.foundation]
        elif column == 3:
            return TYPES[rowref.overlaytype]
        elif column == 4:
            color = rowref.color
            pb = gtk.gdk.Pixbuf(gtk.gdk.COLORSPACE_RGB,True,8,50,20)
            fcol = int((int(color[0]*255)<<24)+(int(color[1]*255)<<16)+(int(color[2]*255)<<8)+(color[3]*255))
            pb.fill(fcol)
            return pb
        elif column == 5:
            return "Zoom to" #TODO: These txt should be set in init method
        elif column == 6:
            return self.button1callback
        elif column == 7:
            return "Delete"
        elif column == 8:
            return self.button2callback


    def on_iter_next(self, rowref):
        try:
            i = self.overlays.index(rowref)+1
            return self.overlays[i]
        except IndexError:
            return None

    def on_iter_children(self, rowref):
        if rowref:
            return None
        return self.overlays[0]

    def on_iter_has_child(self, rowref):
        return False

    def on_iter_n_children(self, rowref):
        if rowref:
            return 0
        return len(self.overlays)

    def on_iter_nth_child(self, rowref, n):
        if rowref:
            return None
        try:
            return self.overlays[n]
        except IndexError:
            return None

    def on_iter_parent(child):
        return None
