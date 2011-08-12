""" 
 Threaded map tile downloader for fast tile downloading in background
 for the glocalizer (gloc map GUI) project.

 @author: Brendan Johan Lee
 @contact: brendajl@simula.no
 @version: 1.0

 Based on work by pi3orama@gmail.com, HelderSepu@gmail.com, Maxim.Razin@gmail.com,
 and standa31415@gmail.com (http://code.google.com/p/gmapcatcher/)
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

from __future__ import division
from mapConst import TILES_HEIGHT
from threading import Thread
from Queue import Queue
from traceback import print_exc

from map import mapUtils
from mapConst import *
from math import floor,ceil


class DownloadTask:
    """ 
    Represents a single download task

    @author: Brendan Johan Lee
    @contact: brendajl@simula.no
    @version: 1.0
    """
    def __init__(self, coord, layer, callback=None, force_update=False, mapServ=MAP_SERVERS[GOOGLE], styleID=1):
        """ 
        Initialize DownloadTask

        @author: Brendan Johan Lee
        @contact: brendajl@simula.no
        @version: 1.0

        @param coord: tile coordinates
        @type coord: tupple
        @param layer: layer tile belongs to
        @type layer: int
        @param callback: callback to call when download task finished
        @type callback: function
        @param force_update: will force the tile to be downloaded even if it exists in cache
        @type force_update: bool
        @param mapServ: name of mapserver
        @type mapServ: str
        @param styleID: id of mapstyle to use (map, satellite,  etc)
        @type styleID: int
        """
        self.coord = coord
        self.layer = layer
        self.callback = callback
        self.force_update = force_update
        self.mapServ = mapServ
        self.styleID = styleID

    def __str__(self):
        """ 
        Return string representation of DownloadTask

        @author: Brendan Johan Lee
        @contact: brendajl@simula.no
        @version: 1.0

        @return: string representation
        @rtype: str
        """

        return "DownloadTask(%s,%s,%s,%s)" % \
                (self.coord, self.layer, self.mapServ, self.styleID)

class DownloaderThread(Thread):
    """ 
    Thread that downloads tiles from the web.

    @author: Brendan Johan Lee
    @contact: brendajl@simula.no
    @version: 1.0
    """

    def __init__(self, ctx_map, inq):
        """ 
        Initialize DownloaderThread

        @author: Brendan Johan Lee
        @contact: brendajl@simula.no
        @version: 1.0

        @param ctx_map: mapserver
        @type ctx_map: MapServ
        @param inq: task queue
        @type inq: Queue
        """
        
        Thread.__init__(self)
        self.ctx_map = ctx_map
        self.inq = inq

    def run(self):
        """ 
        Run the download thread.

        @author: Brendan Johan Lee
        @contact: brendajl@simula.no
        @version: 1.0
        """

        while True:
            task = self.inq.get()
            if (task is None):
                return
            try:
                self.process_task(task)
            except:
                print_exc() # but don't die
            self.inq.task_done()

    def process_task(self, task):
        """ 
        Process a task, and trigger callback if specified when done

        @author: Brendan Johan Lee
        @contact: brendajl@simula.no
        @version: 1.0

        @param task: task to perform
        @type task: instance
        """
        filename = self.ctx_map.get_file(
            task.coord, task.layer, True,
            task.force_update, task.mapServ, task.styleID
        )
        if task.callback:
            task.callback(False, task.coord, task.layer, task.mapServ)

class MapDownloader:
    """ 
    Main class used for downloading map tiles.

    @author: Brendan Johan Lee
    @contact: brendajl@simula.no
    @version: 1.0
    """

    def __init__(self, ctx_map, numthreads=4):
        """ 
        Initialize MapDownloader.

        @author: Brendan Johan Lee
        @contact: brendajl@simula.no
        @version: 1.0

        @param ctx_map: mapserver
        @type ctx_map: MapServ
        @param numthreads: number of threads to use (for simultaneous downloading)
        @type numthreads: int
        """

        self.ctx_map=ctx_map
        self.threads=[]
        self.taskq=Queue(0)
        for i in xrange(numthreads):
            t=DownloaderThread(self.ctx_map,self.taskq)
            self.threads.append(t)
            t.start()

    def __del__(self):
        """ 
        Stop all downloads before a MapDownloader is 'killed'

        @author: Brendan Johan Lee
        @contact: brendajl@simula.no
        @version: 1.0
        """

        self.stop_all()

    def wait_all(self):
        """ 
        Wait until all tasks have been processed.

        @author: Brendan Johan Lee
        @contact: brendajl@simula.no
        @version: 1.0
        """

        self.taskq.join()

    def stop_all(self):
        """ 
        Stop all downloads.

        @author: Brendan Johan Lee
        @contact: brendajl@simula.no
        @version: 1.0
        """

        while not self.taskq.empty():
            self.taskq.get_nowait() # clear the queue
        for i in xrange(len(self.threads)):
            self.taskq.put(None) # put sentinels for threads
        for t in self.threads:
            print ".",
            t.join(5)
        self.threads=[]

    def qsize(self):
        """ 
        Return the approximate size of the task queue.

        @author: Brendan Johan Lee
        @contact: brendajl@simula.no
        @version: 1.0
        """

        return self.taskq.qsize()

    def query_tile(self, coord, layer, callback, online=True, force_update=False, mapServ=MAP_SERVERS[GOOGLE], styleID=1):
        """ 
        Tell the MapDownloader to retrieve a map tile. Tile will be retrieved from
        cache if the tile resides there and has not expired, else from web.

        @author: Brendan Johan Lee
        @contact: brendajl@simula.no
        @version: 1.0

        @param coord: tile coordinates
        @type coord: tupple
        @param layer: map layer tile belongs to
        @type layer: int
        @param callback: function to be called when tile download completes
        @type callback: function
        @param online: indicates if the system is online, in other words has access to the net
        @type online: bool
        @param force_update: force the system to download the tile even if it exists in cache
        @type force_update: bool
        @param mapServ: map server to use
        @type mapServ: str
        @param styleID: map style to use (map, satellite, etc)
        @type styleID: int
        """
        
        world_tiles = mapUtils.tiles_on_level(coord[2])
        coord = (mapUtils.mod(coord[0], world_tiles),
                 mapUtils.mod(coord[1], world_tiles), coord[2])

        # try to get a tile offline
        fn = self.ctx_map.get_file(coord, layer, False, False, mapServ=mapServ)

        if fn!=None or (not online):
            deleted = False
            if (force_update and online):
                deleted = fileUtils.delete_old(fn)
            if not deleted:
                callback(True, coord, layer, mapServ)
                return 

        self.taskq.put(
            DownloadTask(
                coord, layer, callback, force_update, mapServ, styleID
            )
        )

    def query_region(self, xmin, xmax, ymin, ymax, zoom, *args, **kwargs):
        """ 
        Ask the MapDownloader to get all tiles within a given region

        @author: Brendan Johan Lee
        @contact: brendajl@simula.no
        @version: 1.0

        @param xmin: lowest horizontal tile coordinate
        @type xmin: int
        @param xmax: highest horizontal tile coordinate
        @type xmax: int
        @param ymin: lowest vertical tile coordinate
        @type ymin: int
        @param ymax: highest vertical tile coordinate
        @type ymax: int
        @param zoom: zoom level of tiles to retrieve
        @type zoom: int
        
        @todo: Rewrite so takes a tupple instead of xmin,  xmax,  etc
        """

        world_tiles = mapUtils.tiles_on_level(zoom)
        if xmax-xmin >= world_tiles:
            xmin,xmax = 0,world_tiles-1
        if ymax-ymin >= world_tiles:
            ymin,ymax = 0,world_tiles-1
        
        for i in xrange((xmax-xmin+world_tiles)%world_tiles+1):
            x = (xmin+i)%world_tiles
            for j in xrange((ymax-ymin+world_tiles)%world_tiles+1):
                y = (ymin+j)%world_tiles
                self.query_tile((x,y,zoom), *args, **kwargs)
        
    def get_cache_size(self, center, size, zoom):
        """ 
        Get the size needed for the tile cache image.

        @author: Brendan Johan Lee
        @contact: brendajl@simula.no
        @version: 1.0

        @param center: map center
        @type center: list
        @param size: size of map
        @type size: list
        @param zoom: zoom level of map
        @type zoom: int

        @return: size needed for tile cache image
        @rtype: tupple
         
        @todo: Heaps of duplicates in this and function below. Make separate method
        """

        x0, y0 = center[0][0], center[0][1]
        dx0, dy0 = int(center[1][0] - size[0]/2), int(center[1][1] - size[1]/2)
        dx1, dy1 = dx0+size[0], dy0+size[1]
        xmin = int(x0 + floor(dx0/TILES_WIDTH))
        xmax = int(x0 + ceil(dx1/TILES_WIDTH)) - 1
        ymin = int(y0 + floor(dy0/TILES_HEIGHT))
        ymax = int(y0 + ceil(dy1/TILES_HEIGHT)) - 1        
        return ((xmax-xmin)*TILES_WIDTH,(ymax-ymin)*TILES_HEIGHT)

    def get_region_around_point(self, center, size, zoom):
        """ 
        Calculate the tile coordinates to create a map of size around center
        with the given zoom level.

        @author: Brendan Johan Lee
        @contact: brendajl@simula.no
        @version: 1.0

        @param center: center of region to create map around
        @type center: list
        @param size: size of region to create map around
        @type size: list
        @param zoom: zoom level of map
        @type zoom: int

        @return: horizontal minimum, maximum, vertical minimum, maximum
        @rtype: list
        """

        x0, y0 = center[0][0], center[0][1]
        dx0, dy0 = int(center[1][0] - size[0]/2), int(center[1][1] - size[1]/2)
        dx1, dy1 = dx0+size[0], dy0+size[1]
        xmin = int(x0 + floor(dx0/TILES_WIDTH))
        xmax = int(x0 + ceil(dx1/TILES_WIDTH)) - 1
        ymin = int(y0 + floor(dy0/TILES_HEIGHT))
        ymax = int(y0 + ceil(dy1/TILES_HEIGHT)) - 1
        return [xmin,xmax,ymin,ymax]
