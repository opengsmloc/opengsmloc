#!/usr/bin/env python
""" 
 Main map - application for the gloc project.

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

import pygtk  
pygtk.require("2.0")  
import gtk
import gtk.glade  
import gobject
from map.mapDrawing import *
from gtkThread import *
from map.mapServices import MapServ
from map.mapConf import MapConf
from map.mapConst import *
from map.mapDownloader import MapDownloader
import map.mapUtils as mapUtils
import glocdb
from map.mapOverlay import MapOverlay, MapOverlayListModel
from CellRendererButton import CellRendererButton
import itertools
import pickle

"""
A UNIX saleslady, Lenore,
Enjoys work, but she likes the beach more.
She found a good way
To combine work and play:
She sells C shells by the seashore.
"""

# PRIORITY 1
# ----------
#TODO: In the toolbox, have button for sorting overlay, etc
#TODO: In the toolbox, when adding overlays, have an option when rendering observations to add three overlays (one for each signal strength level) instead of one
#TODO: Make sql-box editable for the sql statment query

#TODO: Tidy code, and remember to use list unpacking (*) to make things easier when passing arguments
#TODO: decide what should go in mapdrawing.py and what should go here, a lot of the drawing stuff should be moved to more general methods in mapDrawing.py
#TODO: Make UI for selecting stuff from database, and showing/hiding as layers
#TODO: Make the database interface very general, so that it's easy to implement new stuff
#TODO: Tidy up, fix and clean tileRepoFS.py
#TODO: tidy up, fix and clean mapConf.py
#TODO: tidy up, fix and clean mapUtils.py
#TODO: tidy up, fix and clean mapPixbuf.py
#TODO: tidy up, fix and clean mapDownloader.py
#TODO: tidy up, fix and clean gtkThread.py
#TODO: Look at, and perhaps re-write openanything.py and lrucache.py (due to license)

#TODO: Include posibility of rendering norwegiancells

# PRIORITY 2
#-----------
#TODO: Include reverse-geocoding method, to give names to cells
#TODO: Implement possibility to click on cells (or other stuff rendered) to get information about them
#TODO: Need to have a right click context menu
#TODO: Save current view to file option
#TODO: Save current view to png option
#TODO: Fix the menu
#TODO: Put a list of mouse and keyboard shortcuts in the help menu
#TODO: Make sure that we update the statusbar whenever we do something cool
#TODO: Can come out of sync when resizing the window in certain instanses
#TODO: Make a list of all keypreses and mousestuff and keypresses+mousestuff
"""
kb esc        - exit menu or overlay tool
kb t          - show overlay tool
kb m          - show menu
kb +          - zoom in
kb -          - zoom out
kb up         - move map up
kb down       - move map down
kb left       - move map left
kb right      - move map right
ms rclk       - show context menu (not implemented yet)
ms dblclick   - zoom in to point
ms Alt+dblclk - zoom out to point
ms Ctrl+click - move to point
"""

class PyCairo:
    pixmap = None
    """ 
    Main class for the glocalizer GUI. Represents the Canvas that maps are painted on.

    @author: Brendan Johan Lee
    @contact: brendajl@simula.no
    @version: 1.0
    """

    mapcontext = None
    width = 0
    height = 0
    mapcenter = ((542, 297), (139, 219))
    mapcachesize = None
    region = None
    xoffset = 1
    yoffset = 1
    cachedtiles = {}
    layer = 0
    lastkey = 0
    mot = False
    draging_start = (0,0)
    firstrun = True
    db = None
    
    def __init__(self):
        """ 
        Initialize PyCairo

        @author: Brendan Johan Lee
        @contact: brendajl@simula.no
        @version: 1.0
        """
        
        self.wTree = gtk.glade.XML("glocalizer.glade", "MainWindow")  

        self.wTree.signal_autoconnect({
            "on_quit_activate" : self.closewindow,
            "on_MainWindow_delete_event" : self.closewindow,
            "on_MainWindow_key_press_event" : self.keypress,
            "on_MainWindow_key_release_event" : self.keyrelease,
            "on_about_activate" : self.help_about
            })

        self.conf = MapConf()
        self.db = glocdb.GlocDB(self.conf)
        self.map = MapServ(self.conf.init_path)
        self.downloader = MapDownloader(self.map)
        self.zoomlevel = self.conf.init_zoom
        self.mapservice = self.conf.map_service

        self.drawing_area =  self.wTree.get_widget("drawingarea")
        self.drawing_area.connect("expose-event", self.do_expose)
        self.drawing_area.add_events(gtk.gdk.EXPOSURE_MASK)
        self.drawing_area.connect('motion-notify-event', self.motion)
        self.drawing_area.add_events(gtk.gdk.BUTTON1_MOTION_MASK)
        self.drawing_area.connect('button-press-event', self.button_press)
        self.drawing_area.add_events(gtk.gdk.BUTTON_PRESS_MASK)
        self.drawing_area.connect('button-release-event', self.button_release)
        self.drawing_area.add_events(gtk.gdk.BUTTON_RELEASE_MASK)
        self.drawing_area.connect('event', self.click)

        self.searchbox = self.wTree.get_widget("searchbox")
        self.searchbox.connect("key-press-event", self.search)

        self.statusbar = self.wTree.get_widget("statusbar")
        self.statusbar_context = self.statusbar.get_context_id("pycairodemo")

        #TODO: a lot of the crap below should be in separate methods?

        self.layerbox = self.wTree.get_widget("layercombo")
        self.layerbox.connect("changed", self.change_layer)
        self.layerstore=gtk.ListStore(str)
        for d in LAYER_NAMES:
            self.layerstore.append([d])
        self.layerbox.set_model(self.layerstore)
        cellrenderer = gtk.CellRendererText()
        self.layerbox.pack_start(cellrenderer)
        self.layerbox.add_attribute(cellrenderer, 'text', 0) 
        self.layerbox.set_active(0)

        self.providerbox = self.wTree.get_widget("providercombo")
        self.providerbox.connect("changed", self.change_provider)
        self.providerstore=gtk.ListStore(str)
        for d in MAP_SERVERS:
            self.providerstore.append([d])
        self.providerbox.set_model(self.providerstore)
        cellrenderer2 = gtk.CellRendererText()
        self.providerbox.pack_start(cellrenderer2)
        self.providerbox.add_attribute(cellrenderer2, 'text', 0) 
        self.providerbox.set_active(MAP_SERVERS.index(self.mapservice))

        self.menu = self.wTree.get_widget("vbox2")

        self.toolbox =  self.wTree.get_widget("toolbox")

        self.overlaylist =  self.wTree.get_widget("treeview1")
        self.overlaystore = MapOverlayListModel(self.overlay_zoom,self.overlay_delete)
        
        column_names = self.overlaystore.get_column_names()
        self.tvcolumn = [None] * len(column_names)

        cellc = gtk.CellRendererPixbuf()
        self.tvcolumn[len(column_names)-5] = gtk.TreeViewColumn(column_names[len(column_names)-5],cellc,pixbuf=len(column_names)-5)
        self.overlaylist.append_column(self.tvcolumn[len(column_names)-5])

        celltb = gtk.CellRendererToggle()
        celltb.connect("toggled", self.toggle_overlay)
        self.tvcolumn[0] = gtk.TreeViewColumn(column_names[0],celltb,active=0)
        self.overlaylist.append_column(self.tvcolumn[0])

        for n in range(1, len(column_names)-5):
            cell = gtk.CellRendererText()
            self.tvcolumn[n] = gtk.TreeViewColumn(column_names[n], cell, text=n)
            self.overlaylist.append_column(self.tvcolumn[n])

        cellb = CellRendererButton(20,20)
        self.tvcolumn[len(column_names)-4] = gtk.TreeViewColumn(column_names[len(column_names)-4],cellb,text=len(column_names)-4,callable=len(column_names)-3)
        self.overlaylist.append_column(self.tvcolumn[len(column_names)-4])

        cellb = CellRendererButton(20,20)
        self.tvcolumn[len(column_names)-2] = gtk.TreeViewColumn(column_names[len(column_names)-2],cellb,text=len(column_names)-2,callable=len(column_names)-1)
        self.overlaylist.append_column(self.tvcolumn[len(column_names)-2])


        self.overlaylist.set_model(self.overlaystore)

        self.stores = []
        self.stores.append(self.create_store(
                ["Name","MCC"],
                (str,str),
                ["mccorig0","mccinlist0"], 
                [["mccadd0",self.store_add_clicked, [self.update_mnc,0]], 
                 ["mccremove0",self.store_remove_clicked, [self.update_mnc,0]]]))
        self.stores.append(self.create_store(
                ["Name","MCC","MNC"],
                (str,str,str),
                ["mncorig0","mncinlist0"],
                [["mncadd0",self.store_add_clicked, [self.update_la,0]],
                 ["mncremove0",self.store_remove_clicked, [self.update_la,0]]]))
        self.stores.append(self.create_store(
                ["Name","MCC"],
                (str,str),
                ["mccorig1","mccinlist1"], 
                [["mccadd1",self.store_add_clicked, [self.update_mnc,1]], 
                 ["mccremove1",self.store_remove_clicked, [self.update_mnc,1]]]))
        self.stores.append(self.create_store(
                ["Name","MCC","MNC"],
                (str,str,str),
                ["mncorig1","mncinlist1"],
                [["mncadd1",self.store_add_clicked, [self.update_la, 1]],
                 ["mncremove1",self.store_remove_clicked, [self.update_la, 1]]]))
        self.stores.append(self.create_store(
                ["Name","MCC","MNC", "LA"],
                (str,str,str, str),
                ["laorig0","lainlist0"],
                [["laadd0",self.store_add_clicked, [self.update_cid]],
                 ["laremove0",self.store_remove_clicked, [self.update_cid]]]))
        self.stores.append(self.create_store(
                ["Name","MCC","MNC", "LA"],
                (str,str,str, str),
                ["laorig1","lainlist1"],
                [["laadd1",self.store_add_clicked, [self.update_cid]],
                 ["laremove1",self.store_remove_clicked, [self.update_cid]]]))
        self.stores.append(self.create_store(
                ["Name","CID","MCC","MNC","LA"],
                (str,str,str,str,str),
                ["cidorig1","cidinlist1"],
                [["cidadd1",self.store_add_clicked, None],
                 ["cidremove1",self.store_remove_clicked, None]]))
        self.stores.append(self.create_store(
                ["IMEI","Equipment"],
                (str,str),
                ["observorig1","observinlist1"],
                [["observadd1",self.store_add_clicked, None],
                 ["observremove1",self.store_remove_clicked, None]]))
        self.stores.append(self.create_store(
                ["IMEI","Equipment"],
                (str,str),
                ["observorig3","observinlist3"],
                [["observadd3",self.store_add_clicked, None],
                 ["observremove3",self.store_remove_clicked, None]]))
        self.stores.append(self.create_store(
                ["mode","wcid"],
                (str,str),
                ["coorig2","coinlist2"],
                [["coadd2",self.store_add_clicked, None],
                 ["coremove2",self.store_remove_clicked, None]]))
        self.stores.append(self.create_store(
                ["mode","wcid"],
                (str,str),
                ["coorig3","coinlist3"],
                [["coadd3",self.store_add_clicked, None],
                 ["coremove3",self.store_remove_clicked, None]]))
        self.stores.append(self.create_store(
                ["mode","wsid"],
                (str,str),
                ["seorig2","seinlist2"],
                [["seadd2",self.store_add_clicked, None],
                 ["seremove2",self.store_remove_clicked, None]]))
        self.stores.append(self.create_store(
                ["mode","wsid"],
                (str,str),
                ["seorig3","seinlist3"],
                [["seadd3",self.store_add_clicked, None],
                 ["seremove3",self.store_remove_clicked, None]]))
        self.stores.append(self.create_store(
                ["capabilities"],
                [str],
                ["caorig2","cainlist2"],
                [["caadd2",self.store_add_clicked, None],
                 ["caremove2",self.store_remove_clicked, None]]))
        self.stores.append(self.create_store(
                ["capabilities"],
                [str],
                ["caorig3","cainlist3"],
                [["caadd3",self.store_add_clicked, None],
                 ["caremove3",self.store_remove_clicked, None]]))
        self.stores.append(self.create_store(
                ["beaconinterval"],
                [str],
                ["beorig2","beinlist2"],
                [["beadd2",self.store_add_clicked, None],
                 ["beremove2",self.store_remove_clicked, None]]))
        self.stores.append(self.create_store(
                ["beaconinterval"],
                [str],
                ["beorig3","beinlist3"],
                [["beadd3",self.store_add_clicked, None],
                 ["caremove3",self.store_remove_clicked, None]]))

        for mcc in self.db.getmccs():
            self.stores[0][0][0][0].append(None, [mcc['name'],mcc['mcc']])
            self.stores[2][0][0][0].append(None, [mcc['name'],mcc['mcc']])

        for imei in self.db.getimeis():
            self.stores[7][0][0][0].append(None, [imei['imei'],imei['string']])
            self.stores[8][0][0][0].append(None, [imei['imei'],imei['string']])

        for co in self.db.getwlanconnectionmodes():
            self.stores[9][0][0][0].append(None, [co['mode'],co['wcid']])
            self.stores[10][0][0][0].append(None, [co['mode'],co['wcid']])

        for se in self.db.getwlansecuritymodes():
            self.stores[11][0][0][0].append(None, [se['mode'],se['wsid']])
            self.stores[12][0][0][0].append(None, [se['mode'],se['wsid']])

        for ca in self.db.getcapabilities():
            self.stores[13][0][0][0].append(None, [ca['capabilities']])
            self.stores[14][0][0][0].append(None, [ca['capabilities']])

        for be in self.db.getbeaconintervals():
            self.stores[15][0][0][0].append(None, [be['beaconinterval']])
            self.stores[16][0][0][0].append(None, [be['beaconinterval']])

        self.wTree.get_widget("generatebtn0").connect("clicked", self.generate_overlay)
        self.wTree.get_widget("generatebtn1").connect("clicked", self.generate_overlay)
        self.wTree.get_widget("generatebtn2").connect("clicked", self.generate_overlay)
        self.wTree.get_widget("generatebtn3").connect("clicked", self.generate_overlay)
        self.wTree.get_widget("generatebtn4").connect("clicked", self.load_file)

        self.wTree.get_widget("eventbox0").connect("map-event",self.set_original_background)
        
        cnt = 0
        for stat in self.db.getstats():
            self.wTree.get_widget("stat%s"%cnt).set_text("%s"%stat)
            cnt += 1
        
        self.set_original_background(None, None)
            
#        location = self.map.search_location("oslo")
 #       coord = self.map.get_locations()[location]
  #      self.mapcenter = mapUtils.coord_to_tile(coord)
#        self.zoomlevel = coord[2]
        self.init_layers(self.drawing_area)
        self.rendermap()

        #TODO: Something is still fucked up with the size... moving down from stavanger or kirkenes on my home computer doesn't work properly

    def set_original_background(self, w, event):
        """ 
        Saves the original background color of the eventbox1 widget. Should
        be called after initializing and before setting the color of a
        status bar.

        @param w: object generating event
        @type w: gtk.Object
        @param event: event that invoked this callback
        @type event: gtk.gdk.Event

        @author: Brendan Johan Lee
        @contact: brendajl@simula.no
        @version: 1.0
        """
        self.original_background = self.wTree.get_widget("eventbox1").style.bg[gtk.STATE_NORMAL]

    def load_file(self, button):
        """
        Invoced when a user hits the generate-button in the load from file tab
        
        @author: Brendan Johan Lee
        @contact: brendajl@simula.no
        @version: 1.0
        
        @param button: button object 
        @type button: gtk.Button
        """
        filename = self.wTree.get_widget("filechooser").get_filename()
        gen = int(button.get_name()[-1:])
        if not self.check_name_given(gen): return False
        try:
            inp = open(filename, 'rb')
            content = pickle.load(inp)
        except:
            self.set_status_bar("Error opening file or not a valid file type!", gen, True)
            return False

        if type(content).__name__ != 'list':
            self.set_status_bar("Not a valid input file!", gen, True)
            return False

        active = [r for r in self.wTree.get_widget("TYPE_POLYGON%s"%gen).get_group() if r.get_active()][0].get_name()
        color = self.wTree.get_widget("colselbutton%s"%gen).get_color()
        col = (color.red, color.green, color.blue, self.wTree.get_widget("colselbutton%s"%gen).get_alpha())
        self.overlaystore.add(MapOverlay(self.wTree.get_widget("name-txt%s"%gen).get_text(),gen,content,self.zoomlevel,self.mapcenter,eval(active[:-1]),col,False if active[:-1]=='TYPE_POINTS' or active[:-1] == 'TYPE_PATH' else True))

        self.init_layers(self.drawing_area)
        self.rendermap()

    def check_name_given(self, gen):
        """
        Checks if the user has entered a name,  and if not give an error message
        
        @author: Brendan Johan Lee
        @contact: brendajl@simula.no
        @version: 1.0
        
        @param ben: number of button pressed
        @type buttons: int
        
        @return: True if name entered,  False if not
        @rtype: bool
        """
        #TODO: Should have all of the get_widget stuff global once and for all (here and other places)
        if not self.wTree.get_widget("name-txt%s"%gen).get_text():
            self.set_status_bar("An overlay must have a name", gen, True)
            return False

        self.wTree.get_widget("eventbox%s"%gen).modify_bg(gtk.STATE_NORMAL,self.original_background)
        return True

    def set_status_bar(self, message, gen, warning = False):
        """
        Write a message in a status bar (choosen by the number in gen)
        
        @author: Brendan Johan Lee
        @contact: brendajl@simula.no
        @version: 1.0
        
        @param message: message to be shown on statusbar
        @type message: str
        @param gen: number of statusbar to display message on
        @type gen: int
        @param warning: if True the statusbar will turn red
        @type warning: bool
        """
        if warning: self.wTree.get_widget("eventbox%s"%gen).modify_bg(gtk.STATE_NORMAL,gtk.gdk.Color(65535,0,0))
        else: self.wTree.get_widget("eventbox%s"%gen).modify_bg(gtk.STATE_NORMAL,self.original_background)
        self.wTree.get_widget("cell-status%s"%gen).push(0, message)
        
    def generate_overlay(self, button):
        """ 
        Generates SQL for selecting a collection of positions from the database,
        queries the database, creates a MapOverlay based on the result, adds
        it to the overlaystore and re-draws the map with the new overlay.

        @author: Brendan Johan Lee
        @contact: brendajl@simula.no
        @version: 1.0

        @param button: The button clicked to invoke this function call
        @type button: gtk.Button
        """

        gen = int(button.get_name()[-1:])
        if not self.check_name_given(gen): return False

        join = False
        limits = []

        #TODO: Need to do some checking to make sure values are legal
        if self.wTree.get_widget("rx-level-below%s"%gen).get_text():
            limits.append("rxlev < %s"%self.wTree.get_widget("rx-level-below%s"%gen).get_text())
        if self.wTree.get_widget("rx-level-above%s"%gen).get_text():
            limits.append("rxlev > %s"%self.wTree.get_widget("rx-level-above%s"%gen).get_text())
        if self.wTree.get_widget("position-below-longitude%s"%gen).get_text():
            limits.append("longitude < %s"%self.wTree.get_widget("position-below-longitude%s"%gen).get_text())
        if self.wTree.get_widget("position-above-longitude%s"%gen).get_text():
            limits.append("longitude > %s"%self.wTree.get_widget("position-above-longitude%s"%gen).get_text())
        if self.wTree.get_widget("position-below-latitude%s"%gen).get_text():
            limits.append("latitude < %s"%self.wTree.get_widget("position-below-latitude%s"%gen).get_text())
        if self.wTree.get_widget("position-above-latitude%s"%gen).get_text():
            limits.append("latitude > %s"%self.wTree.get_widget("position-above-latitude%s"%gen).get_text())

        #TODO: We also need to include ripped cells

        mccs = []
        self.stores[gen*2][0][1][0].foreach(self.gather_values,[mccs,[1]])
        mccs = self.flatten(mccs)
        mncs = []
        self.stores[1+(gen*2)][0][1][0].foreach(self.gather_values,[mncs,[1,2]])
        las = []
        self.stores[4+(gen*1)][0][1][0].foreach(self.gather_values,[las,[1,2,3]])
        cids = []
        imeis = []
        if gen==1:
            self.stores[6][0][1][0].foreach(self.gather_values,[cids,[1,2,3,4]])
        if gen==1 or gen==3:
            self.stores[8 if gen==3 else 7][0][1][0].foreach(self.gather_values,[imeis,[0]])
            imeis = self.flatten(imeis)

        if len(imeis)>0:
            limits.append("imei IN (%s)"%','.join(imeis))

        if len(cids)>0:
            join = True
            cidlimits = []
            for cid in cids:
                cidlimits.append("(cellid=%s AND mcc=%s AND mnc=%s AND la=%s)"%(cid[0],cid[1],cid[2],cid[3]))
            limits.append("(%s)"%' OR '.join(cidlimits))
        elif len(las)>0:
            join = True
            lalimits = []
            for la in las:
                lalimits.append("(mcc=%s AND mnc=%s AND la=%s)"%(la[0],la[1],la[2]))
            limits.append("(%s)"%' OR '.join(lalimits))
        elif len(mncs)>0:
            join = True
            mnclimits = []
            for mnc in mncs:
                mnclimits.append("(mcc=%s AND mnc=%s)"%(mnc[0],mnc[1]))
            limits.append("(%s)"%' OR '.join(mnclimits))
        elif len(mccs)>0:
            join = True
            limits.append("mcc IN (%s)"%','.join(mccs))

        if gen!=0 and join:
            limits.append("a.cid=b.cid")

        sql = " FROM %s"%VIEWS[gen]
        if gen==1 and join:
            sql += " AS a, cells AS b"

        if len(limits)>0:
            sql += " WHERE %s"%' AND '.join(limits)

        self.wTree.get_widget("sqltest%s"%gen).get_buffer().set_text("SELECT * %s"%sql)

        count = self.db.sql("SELECT COUNT(*) %s"%sql) 
        if count[0][0] < 1:
            self.set_status_bar("Nothing matches this query!", gen, True)
            return False

        #TODO: Should give warning if too many points
        self.set_status_bar("Adding overlay with %s points"%count[0][0], gen, False)
        result = self.db.sql("SELECT * %s"%sql)
        active = [r for r in self.wTree.get_widget("TYPE_POLYGON%s"%gen).get_group() if r.get_active()][0].get_name()
        color = self.wTree.get_widget("colselbutton%s"%gen).get_color()
        col = (color.red, color.green, color.blue, self.wTree.get_widget("colselbutton%s"%gen).get_alpha())
        print "col: ", col
        self.overlaystore.add(MapOverlay(self.wTree.get_widget("name-txt%s"%gen).get_text(),gen,result,self.zoomlevel,self.mapcenter,eval(active[:-1]),col,False if active[:-1]=='TYPE_POINTS' else True))
        #TODO: Should fix so that we get convex hull or not (should hava a switch to MapOverlay() ?)

        self.wTree.get_widget("rx-level-below%s"%gen).set_text('')
        self.wTree.get_widget("rx-level-above%s"%gen).set_text('')
        self.wTree.get_widget("position-below-latitude%s"%gen).set_text('')
        self.wTree.get_widget("position-below-longitude%s"%gen).set_text('')
        self.wTree.get_widget("position-above-longitude%s"%gen).set_text('')
        self.wTree.get_widget("position-above-latitude%s"%gen).set_text('')
        self.wTree.get_widget("name-txt%s"%gen).set_text('')
        self.clear_stores(gen)

        self.init_layers(self.drawing_area)
        self.rendermap()

    def gather_values(self,model, path, iter, user_data):
        """ 
        Helper method to gather values from a TreeStore. The value will
        be appended to user_data[0]

        @author: Brendan Johan Lee
        @contact: brendajl@simula.no
        @version: 1.0

        @param model: datastore
        @type model: TreeModel
        @param path: tree path of the row
        @type path: TreeStore
        @param iter: TreeIter pointing at path
        @type iter: TreeIter
        @param user_data: List to append the value to
        @type user_data: List
        """
        res = []
        for ud in user_data[1]:
            res.append(model.get_value(iter,ud))
        user_data[0].append(res)

    def create_store(self, columns, types, widgets, buttons):
        """ 
        Creates a 'store object'.

        @author: Brendan Johan Lee
        @contact: brendajl@simula.no
        @version: 1.0

        @param columns: Name of columns
        @type columns: list
        @param types: Type of columns
        @type types: tupple
        @param widgets: widgets to be used
        @type widgets: list
        @param buttons: buttons to be used, name, callback, additional callback
        @type buttons: list

        @return: store object
        @rtype: tupple
        
        @todo: Should probably rewrite the whole store object thing so that it's a class instead
        """

        retval = []
        for widget in widgets:
            store = gtk.TreeStore(*types)
            list =  self.wTree.get_widget(widget)
            cnum = 0
            for col in columns:
                column = gtk.TreeViewColumn(col)
                list.append_column(column)
                cell = gtk.CellRendererText()
                column.pack_start(cell,True)
                column.add_attribute(cell, 'text', cnum)
                cnum += 1
            list.set_model(store)
            list.get_selection().set_mode(gtk.SELECTION_MULTIPLE)
            retval.append((store,list))
        bnames = []
        bfunc = []
        for button in buttons:
            self.wTree.get_widget(button[0]).connect('clicked', button[1], button[0])
            bnames.append(button[0])
            bfunc.append(button[2])
        return (retval,bnames,bfunc)

    def swap_store(self, dir, buttonname):
        """ 
        Swap selected values from one side of a store to the other.

        @author: Brendan Johan Lee
        @contact: brendajl@simula.no
        @version: 1.0

        @param dir: direction to swap
        @type dir: int
        @param buttonname: name of button invoking this method
        @type buttonname: str
        """

        for store in self.stores:
            bcnt = 0
            for bname in store[1]:
                if bname == buttonname:
                    rows = []
                    sel = store[0][dir][1].get_selection().get_selected_rows()
                    
                    for selection in sel[1]:
                        row = store[0][dir][0].get_iter(selection)
                        add = []
                        for i in range(0,store[0][dir][0].get_n_columns()):
                            add.append(store[0][dir][0].get_value(row,i))
                        store[0][abs(dir-1)][0].append(None,add)
                        rows.append(row)

                    for row in rows:
                        store[0][dir][0].remove(row)

                    if store[2][bcnt]:
                        store[2][bcnt][0](*(store[2][bcnt][1:]))
                bcnt += 1
    
    def clear_stores(self, num):
        """ 
        Resets a store to it's original. In other words moves all
        selections back to the left side.

        @author: Brendan Johan Lee
        @contact: brendajl@simula.no
        @version: 1.0

        @param num: store number
        @type num: int
        """

        self.stores[0+(num*2)][0][1][1].get_selection().select_all()
        self.swap_store(1,"mccremove%s"%num)
        if num==1:
            self.stores[7][0][1][1].get_selection().select_all()
            self.swap_store(1,"observremove1")

    def store_add_clicked(self, button, buttonname):
        """ 
        Callback to be used when an add button is clicked in a store.

        @author: Brendan Johan Lee
        @contact: brendajl@simula.no
        @version: 1.0

        @param button: the button invoking this callback
        @type button: gtk.Button
        @param buttonname: the name of the button invoking this callback
        @type buttonname: str
        """

        self.swap_store(0,buttonname)

    def store_remove_clicked(self, button, buttonname):
        """ 
        Callback to be used when a remove button is clicked in a store.

        @author: Brendan Johan Lee
        @contact: brendajl@simula.no
        @version: 1.0

        @param button: the button invoking this callback
        @type button: gtk.Button
        @param buttonname: the name of the button invoking this callback
        @type buttonname: str
        """

        self.swap_store(1,buttonname)

    def update_rows(self,num):
        """ 
        Will remove any selected entries in a store that no longer are
        part of the store.

        @author: Brendan Johan Lee
        @contact: brendajl@simula.no
        @version: 1.0

        @param num: number of store to update
        @type num: int
        """

        rows = []
        self.stores[num][0][0][0].foreach(self.gather_values,[rows,[2]])
        remove = []
        self.stores[num][0][1][0].foreach(self.removerow,[rows,remove])
        for row in remove:
            row[1].remove(row[0])

    def update_la(self,num):
        """ 
        Update the content of an la store based on what mcc and mnc
        are selected in other stores.

        @author: Brendan Johan Lee
        @contact: brendajl@simula.no
        @version: 1.0

        @param num: number of store to update
        @type num: int
        """

        self.stores[4+(num*1)][0][0][0].clear()
        self.stores[1+(num*2)][0][1][0].foreach(self.addla,num)
        self.update_rows(4+(num*1))
        if num==1:
            self.update_cid()

    def update_cid(self):
        """ 
        Update the content of a cell id store based on what mcc,  mnc
        and la are selected in other stores.

        @author: Brendan Johan Lee
        @contact: brendajl@simula.no
        @version: 1.0
        """

        self.stores[6][0][0][0].clear()
        self.stores[5][0][1][0].foreach(self.addcid)
        self.update_rows(6)

    def update_mnc(self, num):
        """ 
        Update the content of a mnc store based on what mcc are selected
        in a other stores.

        @author: Brendan Johan Lee
        @contact: brendajl@simula.no
        @version: 1.0

        @param num: number of store to update
        @type num: int
        """

        self.stores[1+(num*2)][0][0][0].clear()
        self.stores[num*2][0][1][0].foreach(self.addmnc,num)
        self.update_rows(1+(num*2))
        self.update_la(num)
        
    def addmnc(self,model, path, iter, user_data):
        """ 
        Add all mncs belonging to a given mcc to a store.

        @author: Brendan Johan Lee
        @contact: brendajl@simula.no
        @version: 1.0

        @param model: Model containing the mcc
        @type model: gtk.TreeModel
        @param path: path
        @type path: tuple
        @param iter: pointer to path
        @type iter: gtk.TreeIter
        @param user_data: number of store
        @type user_data: int
        """
        for mnc in self.db.getmncs(model.get_value(iter,1)):
            self.stores[1+(user_data*2)][0][0][0].append(None, [mnc['name'],mnc['mcc'],mnc['mnc']])

    def addcid(self, model, path, iter):
        """ 
        Add all cells belonging to a given la to a store.

        @author: Brendan Johan Lee
        @contact: brendajl@simula.no
        @version: 1.0

        @param model: Model containing the la
        @type model: gtk.TreeModel
        @param path: path
        @type path: tuple
        @param iter: pointer to path
        @type iter: gtk.TreeIter
        """

        for cid in self.db.getcids(model.get_value(iter,1),model.get_value(iter,2),model.get_value(iter,3)): 
            self.stores[6][0][0][0].append(None, [cid['name'],cid['cellid'],cid['mcc'],cid['mnc'],cid['la']]) 

    def addla(self, model, path, iter, user_data):
        """ 
        Add all las belonging to a given mnc to a store.

        @author: Brendan Johan Lee
        @contact: brendajl@simula.no
        @version: 1.0

        @param model: Model containing mnc
        @type model: gtk.TreeModel
        @param path: path
        @type path: tuple
        @param iter: pointer to path
        @type iter: gtk.TreeIter
        @param user_data: number of store
        @type user_data: int
        """

        for la in self.db.getlas(model.get_value(iter,1),model.get_value(iter,2)):
            self.stores[4+(user_data*1)][0][0][0].append(None, [la['name'],la['mcc'],la['mnc'],la['la']])

    def flatten(self, aList):
        """ 
        Flatten a list.

        @author: Brendan Johan Lee
        @contact: brendajl@simula.no
        @version: 1.0

        @param aList: List to be flattened
        @type aList: list

        @return: Flattened list
        @rtype: list
        """

        return list( itertools.chain(*aList) )


    def removerow(self,model, path, iter, user_data):
        """ 
        Check if a value in a model exists in a list. If not the value
        is appended to a second list.

        @author: Brendan Johan Lee
        @contact: brendajl@simula.no
        @version: 1.0

        @param model: Model containing the value to be checked
        @type model: gtk.TreeModel
        @param path: path
        @type path: tuple
        @param iter: pointer to path
        @type iter: gtk.TreeIter        
        @param user_data: list of lists, first list containing the values to be checked against, the second will have values to be deleted appended
        @type user_data: list
        """

        if model.get_value(iter,2) not in self.flatten(user_data[0]):
            user_data[1].append((iter,model))

    def overlay_zoom(self, path):
        """ 
        Callback to zoom the map to a given overlay.

        @author: Brendan Johan Lee
        @contact: brendajl@simula.no
        @version: 1.0

        @param path: overlaystore id of overlay to zoom to
        @type path: str
        """

        rect = self.drawing_area.get_allocation()
        self.toolbox.set_property("visible",False)
        self.toolbox.set_property("sensitive",False) # Hack to avoid it stealing focus when not visible
        (newloc,newmapcenter) = mapUtils.zoom_to_area(self.overlaystore.get_area(path),(rect.width*2,rect.height))
        self.mapcenter = newmapcenter
        self.zoomlevel = newloc[2]
        self.init_layers(self.drawing_area)
        self.rendermap()

    def overlay_delete(self, path):
        """ 
        Callback to delete a given overlay from the overlaystore.

        @author: Brendan Johan Lee
        @contact: brendajl@simula.no
        @version: 1.0

        @param path: overlaystore id of overlay to be deleted
        @type path: str
        """

        self.overlaystore.remove(path)
        self.init_layers(self.drawing_area)
        self.rendermap()

    def toggle_overlay(self, cell, path):
        """ 
        Toggle the visibility of a given overlay.

        @author: Brendan Johan Lee
        @contact: brendajl@simula.no
        @version: 1.0

        @param cell: cell clicked (ignored)
        @type cell: CellRenderToggle
        @param path: overlaystore id of overlay to be deleted
        @type path: str
        """
        self.overlaystore.toggle(path)
        self.init_layers(self.drawing_area)
        self.rendermap()


    def re_render_overlays(self):
        """ 
        Re-render all of the overlays in the overlaystore.

        @author: Brendan Johan Lee
        @contact: brendajl@simula.no
        @version: 1.0
        """

        for overlay in self.overlaystore.overlays:
            overlay.render(self.zoomlevel,self.mapcenter)

    def click(self, w, event):
        """ 
        Callback that handles mouse-click events

        @author: Brendan Johan Lee
        @contact: brendajl@simula.no
        @version: 1.0

        @param w: object generating event
        @type w: gtk.Object
        @param event: event that invoked this callback
        @type event: gtk.gdk.Event
        """

        if (event.type == gtk.gdk.BUTTON_PRESS):
            # Right-Click event shows the popUp menu
            if (event.button != 1):
                print "TODO: right click menu"
            #    self.myPointer = (event.x, event.y)
            #    w.popup(None, None, None, event.button, event.time)
        elif (event.type == gtk.gdk.BUTTON_RELEASE):
            if self.mot:
                self.mot = False
            elif (gtk.gdk.keyval_name(self.lastkey)=="Control_L" or gtk.gdk.keyval_name(self.lastkey)=="Control_R"):
                self.motion(w, clevent=event)
        elif (event.type == gtk.gdk._2BUTTON_PRESS):
            print gtk.gdk.keyval_name(self.lastkey)
            if (gtk.gdk.keyval_name(self.lastkey)=="Alt_L" or gtk.gdk.keyval_name(self.lastkey)=="ISO_Level3_Shift"):
                self.zoom_out(event)
            else:
                self.zoom_in(event)

    def closewindow(self,obj,event=None):
        """ 
        Callback called when application is deleted. Ensures that the mapdownloader
        is shut off before exiting the GUI.

        @author: Brendan Johan Lee
        @contact: brendajl@simula.no
        @version: 1.0

        @param obj: object generating event
        @type obj: gtk.Object
        @param event: event that invoked this callback
        @type event: gtk.gdk.Event
        """
        self.downloader.stop_all()
        gtk.main_quit()

    def keypress(self,obj,event):
        """ 
        Callback handling keypress events

        @author: Brendan Johan Lee
        @contact: brendajl@simula.no
        @version: 1.0

        @param obj: object generating event
        @type obj: gtk.Object
        @param event: event that invoked this callback
        @type event: gtk.gdk.Event
        """

        self.lastkey = event.keyval
        return

    def keyrelease(self,obj,event):
        """ 
        Callback handling keyrelease events

        @author: Brendan Johan Lee
        @contact: brendajl@simula.no
        @version: 1.0

        @param obj: object generating event
        @type obj: gtk.Object
        @param event: event that invoked this callback
        @type event: gtk.gdk.Event
        """

        self.lastkey = 0
        if not self.searchbox.get_property("is_focus"):
            if gtk.gdk.keyval_name(event.keyval)=="m":
                self.menu.set_property("visible", True)
                self.searchbox.grab_focus()
            elif gtk.gdk.keyval_name(event.keyval)=="t":
                self.toolbox.set_property("visible",True)
                self.toolbox.set_property("sensitive",True)
            elif gtk.gdk.keyval_name(event.keyval)=="plus":
                self.zoom_in()
            elif gtk.gdk.keyval_name(event.keyval)=="minus":
                self.zoom_out()
            elif gtk.gdk.keyval_name(event.keyval)=="Left":
                self.motion(None,nav=(-TILES_WIDTH,0))
            elif gtk.gdk.keyval_name(event.keyval)=="Right":
                self.motion(None,nav=(TILES_WIDTH,0))
            elif gtk.gdk.keyval_name(event.keyval)=="Up":
                self.motion(None,nav=(0,-TILES_HEIGHT))
            elif gtk.gdk.keyval_name(event.keyval)=="Down":
                self.motion(None,nav=(0,TILES_HEIGHT))
            elif gtk.gdk.keyval_name(event.keyval)=="Escape":
                self.menu.set_property("visible",False)
                self.toolbox.set_property("visible",False)
                self.toolbox.set_property("sensitive",False)
            else:
                print gtk.gdk.keyval_name(event.keyval)

    def change_layer(self,cbox):
        """ 
        Callback that handles changing map layer type

        @author: Brendan Johan Lee
        @contact: brendajl@simula.no
        @version: 1.0

        @param cbox: combobox containing layer types
        @type cbox: gtk.ComboBox
        """
        if not self.layer == cbox.get_active():
            self.layer = cbox.get_active()
            self.init_layers(self.drawing_area)
            self.rendermap()

    def change_provider(self,cbox):
        """ 
        Callback that handles changing map service provider

        @author: Brendan Johan Lee
        @contact: brendajl@simula.no
        @version: 1.0

        @param cbox: combobox containing map providers
        @type cbox: gtk.ComboBox
        """

        if not cbox.get_active() == MAP_SERVERS.index(self.mapservice):
            self.mapservice = MAP_SERVERS[cbox.get_active()]
            self.init_layers(self.drawing_area)
            self.rendermap()
    
    def zoom_in(self,pointer=None):
        """ 
        Zoom the map in by one scale.

        @author: Brendan Johan Lee
        @contact: brendajl@simula.no
        @version: 1.0

        @param pointer: optional mouse click event if map should be moved in addition to zooming
        @type pointer: gtk.gdk.Event
        """
        self.zoom(self.zoomlevel-1,pointer)

    def zoom_out(self,pointer=None):
        """ 
        Zoom the map out by one scale

        @author: Brendan Johan Lee
        @contact: brendajl@simula.no
        @version: 1.0

        @param pointer: optional mouse click event if map should be moved in addition to zooming
        @type pointer: gtk.gdk.Event
        """

        self.zoom(self.zoomlevel+1,pointer)

    def new_mapcenter(self,zoom,pointer=None):
        """ 
        Move the map to a new position, based on the point that should be the new center of the
        map.

        @author: Brendan Johan Lee
        @contact: brendajl@simula.no
        @version: 1.0

        @param zoom: zoomlevel of map
        @type zoom: int
        @param pointer: optional mouse click event containing the new center position to be used
        @type pointer: gtk.gdk.Event
        """
        rect = self.drawing_area.get_allocation()
        if pointer:
            fix_tile, fix_offset = mapUtils.pointer_to_tile(
                rect, (pointer.x,pointer.y), self.mapcenter, self.zoomlevel
                )
        else:
            fix_tile, fix_offset = self.mapcenter
        scala = 2 ** (self.zoomlevel - zoom)
        x = int((fix_tile[0] * TILES_WIDTH  + fix_offset[0]) * scala)
        y = int((fix_tile[1] * TILES_HEIGHT + fix_offset[1]) * scala)
        self.mapcenter = (x / TILES_WIDTH, y / TILES_HEIGHT), (x % TILES_WIDTH, y % TILES_HEIGHT)

    def zoom(self,zoom,pointer=None):
        """ 
        Zoom the map to a new zoom level

        @author: Brendan Johan Lee
        @contact: brendajl@simula.no
        @version: 1.0

        @param zoom: zoomlevel to zoom to
        @type zoom: int
        @param pointer: optional mouse click event containing a new center position to move the map to 
        @type pointer: gtk.gdk.Event
        """

        if (MAP_MIN_ZOOM_LEVEL <= zoom <= MAP_MAX_ZOOM_LEVEL):
            self.new_mapcenter(zoom,pointer)
            self.zoomlevel = zoom
            self.init_layers(self.drawing_area)
            self.rendermap()

    def set_cursor(self, dCursor = gtk.gdk.HAND1):
        """ 
        Set the mouse cursor to a given cursor. If no cursor specified default back to the
        gtk.gdk.HAND1 cursor.

        @author: Brendan Johan Lee
        @contact: brendajl@simula.no
        @version: 1.0

        @param dCursor: cursor to use
        @type dCursor: gtk.gdk.Cursor
        """

        cursor = gtk.gdk.Cursor(dCursor)
        self.drawing_area.window.set_cursor(cursor)

    def button_press(self, w, event):
        """ 
        Callback that handles mouse button press events.

        @author: Brendan Johan Lee
        @contact: brendajl@simula.no
        @version: 1.0

        @param w: object generating event
        @type w: gtk.Object
        @param event: event that invoked this callback
        @type event: gtk.gdk.Event
        """

        if (event.button == 1):
            self.draging_start = (event.x, event.y)
            self.set_cursor(gtk.gdk.FLEUR)

    def button_release(self, w, event):
        """ 
        Callback that handles mouse button release events.

        @author: Brendan Johan Lee
        @contact: brendajl@simula.no
        @version: 1.0

        @param w: object generating event
        @type w: gtk.Object
        @param event: event that invoked this callback
        @type event: gtk.gdk.Event
        """

        if (event.button == 1):
            self.set_cursor()

    def addtobuffer(self, motionx=0,motiony=0):
        """ 
        Expands the map buffer size.

        @author: Brendan Johan Lee
        @contact: brendajl@simula.no
        @version: 1.0

        @param motionx: optional horizontal motion that caused the need for the buffer to be increased
        @type motionx: int
        @param motiony: optional vertical motion that caused the need for the buffer to be increased
        @type motiony: 
        """

        buffersize = gtk.gdk.Rectangle(width=self.buffersize.width+(TILES_WIDTH*abs(motionx)),height=self.buffersize.height+(TILES_HEIGHT*abs(motiony)))
        pixmap = gtk.gdk.Pixmap(self.drawing_area.window, buffersize.width, buffersize.height)
        mapcontext = pixmap.cairo_create()
        if motionx < 0:
            mapcontext.set_source_pixmap(self.pixmap,(TILES_WIDTH*-motionx),0)
        elif motionx > 0:
            mapcontext.set_source_pixmap(self.pixmap,0,0)
        if motiony < 0:
            mapcontext.set_source_pixmap(self.pixmap,0,(TILES_HEIGHT*-motiony))
        elif motiony > 0:
            mapcontext.set_source_pixmap(self.pixmap,0,0)

        mapcontext.paint()
        self.pixmap = pixmap
        self.mapcontext = mapcontext
        self.buffersize = buffersize

        if motionx < 0:
            self.region[0] += motionx
        elif motionx > 0:
            self.region[1] += motionx 
        if motiony < 0:
            self.region[2] += motiony
        elif motiony > 0:
            self.region[3] += motiony
        

    def motion(self, w, event=None, nav=None, clevent=None):
        """ 
        Move the map.

        @author: Brendan Johan Lee
        @contact: brendajl@simula.no
        @version: 1.0

        @param w: object that invoked this callback
        @type w: gtk.Object
        @param event: optional mouse event containing new x, y coordinates, use when dragging map
        @type event: gtk.gdk.Event
        @param nav: optional list containing new coordinates, use when moving the map by keyboard
        @type nav: list
        @param clevent: optional mouse event containing new x, y coordinates, use when double clicking map
        @type clevent: gtk.gdk.Event
        """
        
        rect = self.drawing_area.get_allocation()
        if event:
            self.mot = True
            offset = [self.mapcenter[1][0] + (self.draging_start[0] - event.x),
                      self.mapcenter[1][1] + (self.draging_start[1] - event.y)]
        elif nav:
            offset = [self.mapcenter[1][0] + nav[0],
                      self.mapcenter[1][1] + nav[1]]
        else:
            offset = [self.mapcenter[1][0] + clevent.x-(rect.width/2),
                      self.mapcenter[1][1] + clevent.y-(rect.height/2)]

        previoustopleft = mapUtils.tile_adjustEx(self.zoomlevel,self.mapcenter[0],(-(rect.width//2),-(rect.height//2)))
        self.mapcenter = mapUtils.tile_adjustEx(self.zoomlevel, self.mapcenter[0], offset)
        topleft = mapUtils.tile_adjustEx(self.zoomlevel,self.mapcenter[0],(-(rect.width//2),-(rect.height//2)))
        topright = mapUtils.tile_adjustEx(self.zoomlevel,self.mapcenter[0],((rect.width//2)+(TILES_WIDTH*2),(rect.height//2)))
        bottomleft = mapUtils.tile_adjustEx(self.zoomlevel,self.mapcenter[0],((rect.width//2),(rect.height//2)+(TILES_HEIGHT*2)))

        if previoustopleft[0][0]>topleft[0][0] or previoustopleft[0][0]<topleft[0][0]:
            if topleft[0][0]<self.region[0]: #need more tiles on left
                self.addtobuffer(motionx=-(self.region[0]-topleft[0][0]))
            elif topright[0][0]>self.region[1]: #need more tiles on right
                self.addtobuffer(motionx=topright[0][0]-self.region[1])
                self.xoffset -= previoustopleft[0][0]-topleft[0][0]
            else: #allready have tile to right or left, just update offset
                self.xoffset -= previoustopleft[0][0]-topleft[0][0]
        if previoustopleft[0][1]>topleft[0][1] or previoustopleft[0][1]<topleft[0][1]:
            if topleft[0][1]<self.region[2]:
                self.addtobuffer(motiony=-(self.region[2]-topleft[0][1]))
            elif bottomleft[0][1]>self.region[3]:
                self.addtobuffer(motiony=bottomleft[0][1]-self.region[3])
                self.yoffset -= previoustopleft[0][1]-topleft[0][1]
            else:
                self.yoffset -= previoustopleft[0][1]-topleft[0][1]

        inview = (topleft[0][0],topright[0][0]-1,topleft[0][1],bottomleft[0][1])
        for x in range(inview[0],inview[1]):
            for y in range(inview[2],inview[3]):
                if (x,y) not in self.cachedtiles:
                    self.cachedtiles[x,y] = True
                    self.downloader.query_tile((x,y,self.zoomlevel),self.layer,
                                               gui_callback(self.tile_received),
                                               mapServ=self.mapservice,
                                               styleID=self.conf.cloudMade_styleID)

        gc = self.drawing_area.window.new_gc()
        self.drawing_area.window.draw_drawable(gc, self.pixmap, self.mapcenter[1][0]+(self.xoffset*TILES_WIDTH), 
                                               self.mapcenter[1][1]+(self.yoffset*TILES_HEIGHT), 0, 0, rect.width, rect.height)
        if event:
            self.draging_start = (event.x, event.y)
        else:
            self.draging_start = (0, 0)
        
    def rendermap(self):
        """ 
        Render the map in view and the overlays on top of it

        @author: Brendan Johan Lee
        @contact: brendajl@simula.no
        @version: 1.0
        """

        self.re_render_overlays()
        self.mapcachesize = self.downloader.get_cache_size(self.mapcenter,(self.buffersize.width, self.buffersize.height), self.zoomlevel)
        self.region = self.downloader.get_region_around_point(self.mapcenter, (self.buffersize.width, self.buffersize.height), self.zoomlevel)

        for x in range(self.region[0],self.region[1]):
            for y in range(self.region[2],self.region[3]):
                self.cachedtiles[x,y] = True
        self.downloader.query_region(self.region[0],self.region[1],self.region[2],self.region[3], self.zoomlevel, self.layer,
                                     gui_callback(self.tile_received),
                                     mapServ=self.mapservice,
                                     styleID=self.conf.cloudMade_styleID
                                     )

    def search(self,widget,event):
        """ 
        Callback used for searching for a location and displaying it on the map.

        @author: Brendan Johan Lee
        @contact: brendajl@simula.no
        @version: 1.0

        @param widget: the object invoking this callback
        @type widget: gtk.Object
        @param event: the event that invoked this callback 
        @type event: gtk.gdk.Event
        """
        
        if gtk.gdk.keyval_name(event.keyval)=="Return":
            self.menu.set_property("visible",False)
            location = self.map.search_location(self.searchbox.get_text())
            coord = self.map.get_locations()[location]
            self.mapcenter = mapUtils.coord_to_tile(coord)
            self.zoomlevel = coord[2]
            self.init_layers(self.drawing_area)
            self.rendermap()
        elif gtk.gdk.keyval_name(event.keyval)=="Escape":
            self.menu.set_property("visible",False)
            self.toolbox.set_property("visible",False)
            self.toolbox.set_property("sensitive",False)
        else:
            print gtk.gdk.keyval_name(event.keyval)

    def tile_received(self, tile_coord, layer, mapServ):
        """ 
        Callback called when the mapdownloader receives a new tile

        @author: Brendan Johan Lee
        @contact: brendajl@simula.no
        @version: 1.0

        @param tile_coord: the coordinates of the received tile
        @type tile_coord: tupple
        @param layer: the layer to render the tile on
        @type layer: int
        @param mapServ: the mapserver containing the tile
        @type mapServ: str
        """
        
        if tile_coord[2]==self.zoomlevel and layer==self.layer:
            if tile_coord[0] >= self.region[0] and tile_coord[0] <= self.region[1] and tile_coord[1] >= self.region[2] and tile_coord[1] <= self.region[3]:
                img = self.map.load_pixbuf(tile_coord, layer, False, mapServ) # False = don't force update
                px = tile_coord[0]-self.region[0]
                py = tile_coord[1]-self.region[2]
                add_tile(self.overlaystore.overlays, self.mapcontext, px*TILES_WIDTH,py*TILES_HEIGHT, img, tile_coord,self.region,self.mapcenter)
                gc = self.drawing_area.window.new_gc()
                rect = self.drawing_area.get_allocation()
                xloc = (px-self.xoffset)*TILES_WIDTH
                yloc = (py-self.yoffset)*TILES_HEIGHT
                if (xloc>=0 and xloc<=rect.width+self.mapcenter[1][0]) and (yloc>=0 and yloc<=rect.height+self.mapcenter[1][1]): 
                    self.drawing_area.window.draw_drawable(gc, self.pixmap, px*TILES_WIDTH,py*TILES_HEIGHT, 
                                                           xloc-self.mapcenter[1][0], yloc-self.mapcenter[1][1], TILES_WIDTH, TILES_HEIGHT)

    def init_layers(self, widget):
        """ 
        Initialize the map layers.

        @author: Brendan Johan Lee
        @contact: brendajl@simula.no
        @version: 1.0

        @param widget: drawingarea to draw the map on
        @type widget: gtk.DrawingArea
        """

        rect = self.drawing_area.get_allocation()
        self.width = rect.width
        self.height = rect.height
        self.region = None
        self.xoffset = 1
        self.yoffset = 2
        self.cachedtiles = {}
        self.draging_start = (0, 0)
        self.buffersize = gtk.gdk.Rectangle(
            width=(int(round((float(rect.width)/TILES_WIDTH),0)+3)*TILES_WIDTH),
            height=(int(round((float(rect.height)/TILES_HEIGHT),0)+3)*TILES_HEIGHT))
        self.pixmap = gtk.gdk.Pixmap(widget.window, self.buffersize.width, self.buffersize.height)
        self.mapcontext = self.pixmap.cairo_create()

    def do_expose(self,widget,event):
        """ 
        Expose event handler.  Repaint a portion of the screen.

        @author: Brendan Johan Lee
        @contact: brendajl@simula.no
        @version: 1.0

        @param widget: object that invoked this callback
        @type widget: gtk.Object
        @param event: event that invoked this callback
        @type event: gtk.gdk.Event
        """

        if not self.pixmap:
            self.init_layers(widget)
        x, y, width, height = event.area
        gc = widget.window.new_gc()
        widget.window.draw_drawable(gc, self.pixmap, x+self.mapcenter[1][0]+(self.xoffset*TILES_WIDTH), y+self.mapcenter[1][1]+(self.yoffset*TILES_HEIGHT), x, y, width, height)
        
        rect = self.drawing_area.get_allocation()


        #Nasty hack to render the map correctly the first time and also if windowsize has been changed
        #Since we get a bogus size for drawing_area in the begining
        if self.firstrun or not rect.width==self.width or not rect.height==self.height: 
            self.firstrun = False 
            self.init_layers(self.drawing_area)
            self.rendermap()


    def help_about(self,widget):
        """ 
        Callback that displays the help dialog.

        @author: Brendan Johan Lee
        @contact: brendajl@simula.no
        @version: 1.0

        @param widget: object that invoked this callback
        @type widget: gtk.Object
        """

        about = gtk.glade.XML("libs/glocalizer.glade", "aboutdialog")  
        dialog = about.get_widget("aboutdialog")
        dialog.run()
        dialog.destroy()

    def set_status_text(self,text):
        """ 
        Display a message on the main status bar

        @author: Brendan Johan Lee
        @contact: brendajl@simula.no
        @version: 1.0

        @param text: text to be displayed on the status bar
        @type text: str
        """

        self.statusbar.push(self.statusbar_context,text)


def main():
    """ 
    Application main method

    @author: Brendan Johan Lee
    @contact: brendajl@simula.no
    @version: 1.0
    """

    gtk.main()
    return 0

if __name__ == "__main__":
    PyCairo()
    main()

