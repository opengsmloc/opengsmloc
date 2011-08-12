## @package src.mapServices
# All the interaction with the map services

import os
import gtk
import sys
from gloclib import fileUtils
import tilesRepoFS
from gloclib import openanything

from map.mapServers import googleMaps
import map.mapServers.openStreetMaps as openStreetMaps
import map.mapServers.cloudMade as cloudMade
import map.mapServers.yahoo as yahoo
import map.mapServers.informationFreeway as informationFreeway
import map.mapServers.openCycleMap as openCycleMap
import map.mapServers.googleMapMaker as googleMapMaker
import map.mapServers.virtualEarth as virtualEarth

from mapConst import *
from threading import Timer
from gobject import TYPE_STRING

## All the interaction with the map services.
#  Other map services can be added see def get_url_from_coord
class MapServ:

    # coord = (lat, lng, zoom_level)
    exThread = None

    def read_locations(self):
        #       self.locations = fileUtils.read_file('location', self.locationpath)
        return None

    def write_locations(self):
        #fileUtils.write_file('location', self.locationpath, self.locations)
        return None

    def __init__(self, configpath=None):
        configpath = os.path.expanduser(configpath or DEFAULT_PATH)
        self.mt_counter=0
        self.configpath = fileUtils.check_dir(configpath)
        self.locationpath = os.path.join(self.configpath, 'locations')
        self.locations = {}

        #implementation of the method is set in maps.py:__init__()
        self.tile_repository = tilesRepoFS.TilesRepositoryFS(self)

        if (os.path.exists(self.locationpath)):
            self.read_locations()
        else:
            self.write_locations()

    def finish(self):
        self.tile_repository.finish()
        if self.exThread:
            self.exThread.cancel()

    def get_locations(self):
        return self.locations

    def search_location(self, location):
        print location
        location, coord = googleMaps.search_location(location)
        print location
        if (location[:6] != "error="):
            self.locations[location] = coord
            self.write_locations()
        return location

    ## Get the URL for the given coordinates
    # In this function we point to the proper map service
    def get_url_from_coord(self, coord, layer, mapServ, styleID):
        self.mt_counter += 1
        self.mt_counter = self.mt_counter % NR_MTS

        if mapServ == MAP_SERVERS[OSM] and (layer == LAYER_MAP):
            return openStreetMaps.get_url(self.mt_counter, coord)

        elif mapServ == MAP_SERVERS[CLOUDMADE] and (layer == LAYER_MAP):
            return cloudMade.get_url(self.mt_counter, coord, styleID)

        elif mapServ == MAP_SERVERS[YAHOO] and (layer != LAYER_TERRAIN):
            return yahoo.get_url(self.mt_counter, coord, layer)

        elif mapServ == MAP_SERVERS[INFO_FREEWAY] and (layer == LAYER_MAP):
            return informationFreeway.get_url(self.mt_counter, coord)

        elif mapServ == MAP_SERVERS[OPENCYCLEMAP] and (layer == LAYER_MAP):
            return openCycleMap.get_url(self.mt_counter, coord)

        elif mapServ == MAP_SERVERS[GOOGLE_MAKER] and (layer == LAYER_MAP):
            return googleMapMaker.get_url(self.mt_counter, coord)

        elif mapServ == MAP_SERVERS[VIRTUAL_EARTH] and (layer != LAYER_TERRAIN):
            return virtualEarth.get_url(self.mt_counter, coord, layer)

        else:
            return googleMaps.get_url(self.mt_counter, coord, layer)

    def get_tile_from_coord(self, coord, layer, mapServ, styleID):
        href = self.get_url_from_coord(coord, layer, mapServ, styleID)
        if href:
            try:
                print 'downloading:', href
                oa = openanything.fetch(href)
                if oa['status']==200:
                    return oa['data']
                else:
                    raise RuntimeError, ("HTTP Reponse is: " + str(oa['status']),)
            except:
                raise

    def get_file(self, coord, layer, online, force_update,
                                mapServ='Google', styleID =1):
        return self.tile_repository.get_file(
                    coord, layer, online, force_update, mapServ, styleID
                )

    ## Call the do_export in the tile_repository
    # Export tiles to one big map
    def do_export(self, tcoord, layer, online, mapServ, styleID, size):
        def exportThread():
            self.tile_repository.do_export(
                tcoord, layer, online, mapServ, styleID, size
            )
            print "Export completed!"
        self.exThread = Timer(0, exportThread)
        self.exThread.start()


    def load_pixbuf(self, coord, layer, force_update, mapServ):
        return self.tile_repository.load_pixbuf(coord, layer, force_update, mapServ)


    def completion_model(self, strAppend=''):
        store = gtk.ListStore(TYPE_STRING)
        for str in sorted(self.locations.keys()):
            iter = store.append()
            store.set(iter, 0, str + strAppend)
        return store
