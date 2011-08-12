""" 
 Contains static variables (constants) for the glocalizer (gloc map GUI) project

 @author: Brendan Johan Lee
 @contact: brendajl@simula.no
 @version: 1.0
"""
NAME = "GlocAlizer"
VERSION = "1.0"
VERSION_NAME = ""
WEB_ADDRESS = "http://opengsmloc.org"

GOOGLE = 0
OSM = 1
CLOUDMADE = 2
YAHOO = 3
INFO_FREEWAY = 4
OPENCYCLEMAP = 5
GOOGLE_MAKER = 6
VIRTUAL_EARTH = 7
MAP_SERVERS = ["Google", "OpenStreetMap", "CloudMade", "Yahoo",
               "InformationFreeway", "OpenCycleMap", "Google Map Maker",
               "Virtual Earth"]

MAP_MAX_ZOOM_LEVEL = 17
MAP_MIN_ZOOM_LEVEL = -2
TILES_WIDTH = 256
TILES_HEIGHT = 256
NR_MTS = 4

LAYER_MAP = 0
LAYER_SATELLITE = 1
LAYER_TERRAIN = 2
LAYER_NAMES = ["Map", "Satellite", "Terrain"]
LAYER_DIRS = ["tiles", "sat_tiles", "ter_tiles"]

SECTION_INIT  = 'init'
SECTION_DATABASE  = 'database'
R_EARTH = 6371.
USER_PATH = "~"
TILES_PATH = ".glocalizer"
DEFAULT_PATH = USER_PATH + "/" + TILES_PATH

TYPE_POINTS = 0
TYPE_POLYGON = 1
TYPE_FILLEDPOLYGON = 2
TYPE_PATH =  3
TYPES = ["Points", "Polygon", "Filled Polygon",  "Path"]


LAYER_BUFFER_TILES = 20

FOUNDATION_CELLS = 0
FOUNDATION_OBSERVATIONS = 1
FOUNDATION_WLANS = 2
FOUNDATION_WLAN_OBSERVATIONS = 3
FOUNDATION_FILE = 4
FOUNDATIONS = ["Cells", "Observations", "WLANs", "WLAN observations", "File"]

VIEWS = ["gatheredcells", "gatheredcellobservations", "gatheredwlans", "gatheredwlanobservations"]
