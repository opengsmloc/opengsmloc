""" 
 Configuration object for the glocalizer (gloc map GUI project)

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

import os
import ConfigParser
import fileUtils
from mapConst import *
from mapUtils import str_to_tuple

class MapConf():
    """ 
    glocalizer configuration object

    @author: Brendan Johan Lee
    @contact: brendajl@simula.no
    @version: 1.0
    """

    def get_configpath(self):
        """ 
        Return the full path to the configuration file.

        @author: Brendan Johan Lee
        @contact: brendajl@simula.no
        @version: 1.0

        @return: full path to .conf file
        @rtype: str
        """

        configpath = os.path.expanduser(DEFAULT_PATH)
        fileUtils.check_dir(configpath)
        configpath = os.path.join(configpath, 'glocalizer.conf')
        return configpath

    def __init__(self):
        """ 
        Initialize the MapConf class

        @author: Brendan Johan Lee
        @contact: brendajl@simula.no
        @version: 1.0
        """

        configpath = self.get_configpath()
        self.read(configpath)
        if not os.path.exists(configpath):
            self.write(configpath)

    def write(self, configpath):
        """ 
        Write the current configuration to file.

        @author: Brendan Johan Lee
        @contact: brendajl@simula.no
        @version: 1.0

        @param configpath: full path to the file to write the configuration to
        @type configpath: str
        """

        config = ConfigParser.RawConfigParser()
        config.add_section(SECTION_INIT)
        config.add_section(SECTION_DATABASE)
        if self.init_path:
            config.set(SECTION_INIT, 'path', self.init_path)
        config.set(SECTION_INIT, 'width', self.init_width)
        config.set(SECTION_INIT, 'height', self.init_height)
        config.set(SECTION_INIT, 'zoom', self.init_zoom)
        config.set(SECTION_INIT, 'center', self.init_center)
        config.set(SECTION_INIT, 'map_service', self.map_service)
        config.set(SECTION_INIT, 'cloudmade_styleid', self.cloudMade_styleID)
        config.set(SECTION_DATABASE, 'host', self.db_host)
        config.set(SECTION_DATABASE, 'port', self.db_port)
        config.set(SECTION_DATABASE, 'name', self.db_name)
        config.set(SECTION_DATABASE, 'username', self.db_username)
        config.set(SECTION_DATABASE, 'password', self.db_password)

        configfile = open(configpath, 'wb')
        config.write(configfile)

    def read(self, configpath):
        """ 
        Read the configuration from a given file

        @author: Brendan Johan Lee
        @contact: brendajl@simula.no
        @version: 1.0

        @param configpath: full path to file to read from
        @type configpath: str
        """

        def read_config(section, keyOption, defaultValue, castFunction):
            """ 
            Read a configuration option

            @author: Brendan Johan Lee
            @contact: brendajl@simula.no
            @version: 1.0

            @param section: section to read from
            @type section: str
            @param keyOption: key to read
            @type keyOption: str
            @param defaultValue: value to use as default if option not existing 
            @type defaultValue: castable
            @param castFunction: type to cast the object to before returning
            @type castFunction: castable

            @return: value of configuration option
            @rtype: castable
            """

            try:
                strValue = config.get(section, keyOption)
                return castFunction(strValue)
            except Exception:
                return defaultValue

        config = ConfigParser.RawConfigParser()
        config.read(configpath)

        self.init_width = read_config(SECTION_INIT,'width', 550, int)
        self.init_height = read_config(SECTION_INIT,'height', 450, int)
        self.init_zoom = read_config(SECTION_INIT,'zoom', MAP_MAX_ZOOM_LEVEL-10, int)
        self.init_center = read_config(SECTION_INIT,'center', ((1,0),(9,200)), str_to_tuple)
        self.init_path = os.path.join(os.path.expanduser(USER_PATH), TILES_PATH)

        strPath = read_config(SECTION_INIT,'path', self.init_path, str)
        if not strPath.strip().lower() in ['none', '']:
            strPath = fileUtils.check_dir(strPath)
            if os.path.isdir(strPath):
                self.init_path = strPath

        self.map_service = read_config(SECTION_INIT,'map_service', MAP_SERVERS[GOOGLE], str)
        self.cloudMade_styleID = read_config(SECTION_INIT,'cloudmade_styleid', 1, int)

        self.db_host = read_config(SECTION_DATABASE,'host','localhost',str)
        self.db_port = read_config(SECTION_DATABASE,'port',5432,int)
        self.db_name = read_config(SECTION_DATABASE,'name','gloc',str)
        self.db_username = read_config(SECTION_DATABASE,'username','gloc',str)
        self.db_password = read_config(SECTION_DATABASE,'password','99ab97a',str)

    def save(self):
        """ 
        Save configuration to default configuration file

        @author: Brendan Johan Lee
        @contact: brendajl@simula.no
        @version: 1.0
        """

        configpath = self.get_configpath()
        self.write(configpath)

