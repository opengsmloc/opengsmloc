#!/usr/bin/env python
"""
 Module that interfaces with the GLoc main database.

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

import psycopg2, psycopg2.extras

rxlevlimits = ["rxlev > 90","rxlev < 90 AND rxlev > 80","rxlev < 80"]

class GlocDB:
    """
    Class used to interface with the gloc database

    @author: Brendan Johan Lee
    @contact: brendajl@simula.no

    @version: 1.0
    """

    def __init__(self, conf):
        """
        Initialize GlocDB

        @author: Brendan Johan Lee
        @contact: brendajl@simula.no

        @version: 1.0

        @param conf: server configuration that contains database information
        @type conf: L{ServerConf}
        """
        self.conf = conf
        self.cur = self.__getdbcursor__()

    def getStrongestGSM(self,mcc,mnc,la,cellid):
        """
        Returns the strongest observation of a given cell

        @author: Brendan Johan Lee
        @contact: brendajl@simula.no

        @version: 1.0

        @param mcc: Mobile Country Code of cell
        @type mcc: str
        @param mnc: Mobile Network Code of cell
        @type mnc: str
        @param la: Location Area of cell
        @type la: str
        @param cellid: Cell ID of cell
        @type cellid: str

        @return: result of query
        @rtype: list

        @todo: Needs errorchecking
        """
        return self.sql("SELECT * FROM gatheredcells WHERE mcc=%s AND mnc=%s AND la=%s AND cellid=%s"%(mcc,mnc,la,cellid))

    def getCid(self,mcc,mnc,la,cellid):
        """
        Get a GSM-cells cid (internal database identification) based on
        its mcc, mnc, la and cellid.

        @author: Brendan Johan Lee
        @contact: brendajl@simula.no
        @version: 1.0

        @param mcc: Mobile Country Code
        @type mcc: int
        @param mnc: Mobile Network Code
        @type mnc: int
        @param la: Location Area
        @type la: int
        @param cellid: Cell Identification
        @type cellid: int

        @return: cid of given cell or False
        @rtype: int or bool

        @todo: Error checking
        """

        cellid = self.sql("SELECT cid FROM gatheredcells WHERE mcc=%s AND mnc=%s AND la=%s AND cellid=%s"%(mcc,mnc,la,cellid))
        if len(cellid)<1:
            return False
        return cellid[0][0]

    def getClosestGSMmatch(self,mcc,mnc,la,cellid,rxlev):
        """
        Selects the closest mathcing fingerprint in the database to the
        supplied cell and rxlev.

        @author: Brendan Johan Lee
        @contact: brendajl@simula.no
        @version: 1.0

        @param mcc: Mobile Country Code
        @type mcc: int
        @param mnc: Mobile Network Code
        @type mnc: int
        @param la: Location Area
        @type la: int
        @param cellid: Cell Identification
        @type cellid: int
        @param rxlev: Radio Receive Level
        @type rxlev: int

        @return: closest matching fingerprint from database
        @rtype: list

        @todo: Error checking
        """

        cid = self.getCid(mcc,mnc,la,cellid)
        if not cid:
            return False
        return self.sql("SELECT gatheredcellobservations.*,ABS(rxlev - %s) AS diff FROM gatheredcellobservations WHERE cid=%s ORDER BY diff ASC LIMIT 1"%(rxlev,cid))

    def getClosestWLANmatch(self,bssid,rxlev):
        """
        Selects the closest matching fingerprint in the database to the
        supplied ssid and rxlev.

        @author: Brendan Johan Lee
        @contact: brendajl@simula.no
        @version: 1.0

        @param bssid: ssid of WLAN
        @type bssid: str
        @param rxlev: receivelevel of WLAN
        @type rxlev: int

        @return: closest matching fingerprint from database
        @rtype: list

        @todo: error checking
        """
        return self.sql("SELECT gatheredwlanobservations.*,ABS(rxlev - %s) AS diff FROM gatheredwlanobservations WHERE bssid='%s' ORDER BY diff ASC LIMIT 1"%(rxlev,bssid))

    def getcellobservations(cid,type=None):
        """ 
        Returns a database cursor containing all observations of a given cell.
        If the optional 

        @author: Brendan Johan Lee
        @contact: brendajl@simula.no

        @version: 1.0

        @param cid: ID of cell to return observations of
        @type cid: int
        @param type: limit to a given signal level
            - 0 rxlev > 90
            - 1 rxlev < 90 > 80
            - 2 rxlev < 80
        @type type: int

        @return: all results as tupples
        @rtype: list of tupples
        """

        return self.sql("SELECT * FROM gatheredcellobservations WHERE cid=%i %s"%(int(cid),"AND %s"%rxlevlimits[int(type)] if type else ""))

    def getstats(self):
        """ 
        Return statistics of the content of the database. The return is a
        tupple containing number of location areas, cells, observations of cells, 
        neightbour cells, wlans, observations of wlans and equipment.

        @author: Brendan Johan Lee
        @contact: brendajl@simula.no
        @version: 1.0

        @return: database statistics
        @rtype: tupple
        """

        return (self.sql("SELECT COUNT(*) FROM la")[0][0],
                self.sql("SELECT COUNT(*) FROM cells")[0][0],
                self.sql("SELECT COUNT(*) FROM cellobservations")[0][0],
                self.sql("SELECT COUNT(*) FROM neighbouringcells")[0][0],
                self.sql("SELECT COUNT(*) FROM wlan")[0][0],
                self.sql("SELECT COUNT(*) FROM wlanobservations")[0][0],
                self.sql("SELECT COUNT(*) FROM equipment")[0][0])

    def getbeaconintervals(self):
        """ 
        Returns a list of unique wlan beacon intervals from the database.

        @author: Brendan Johan Lee
        @contact: brendajl@simula.no
        @version: 1.0

        @return: list of unique wlan beacon intervals
        @rtype: list
        """
        
        return self.sql("SELECT DISTINCT ON(beaconinterval) beaconinterval FROM wlan")

    def getcapabilities(self):
        """ 
        Returns a list of unique wlan capabilities from the database.

        @author: Brendan Johan Lee
        @contact: brendajl@simula.no
        @version: 1.0

        @return: list of unique bacon intervals
        @rtype: list
        """

        return self.sql("SELECT DISTINCT ON(capabilities) capabilities FROM wlan")

    def getwlanconnectionmodes(self):
        """ 
        Returns a list of unique wlan connection modes from the database.

        @author: Brendan Johan Lee
        @contact: brendajl@simula.no
        @version: 1.0

        @return: list of unique wlan connection modes
        @rtype: list
        """

        return self.sql("SELECT * FROM wlanconnectionmodes")

    def getwlansecuritymodes(self):
        """ 
        Returns a list of unique wlan security modes from the database.

        @author: Brendan Johan Lee
        @contact: brendajl@simula.no
        @version: 1.0

        @return: list of unique wlan security modes
        @rtype: list
        """

        return self.sql("SELECT * FROM wlansecuritymodes")

    def getimeis(self):
        """ 
        Returns a list of unique registered equipment from the database. Equipment
        list is based on IMEI numbers of devices, and each device has a descriptive
        string attached where such information is available.

        @author: Brendan Johan Lee
        @contact: brendajl@simula.no
        @version: 1.0

        @return: list of unique registered equipment
        @rtype: list
        """

        return self.sql("SELECT * FROM equipment")

    def getmccs(self):
        """ 
        Returns a list of unique Mobile Country Codes (mcc) registered in the database.

        @author: Brendan Johan Lee
        @contact: brendajl@simula.no
        @version: 1.0

        @return: list of unique Mobile Country Codes
        @rtype: list
        """

        return self.sql("SELECT * FROM mcc")

    def getmncs(self, mcc):
        """ 
        Return a list of unique Mobile Network Codes (mnc) registered in the database
        belonging to the supplied Mobile Country Code (mcc).  

        @author: Brendan Johan Lee
        @contact: brendajl@simula.no
        @version: 1.0

        @param mcc: Mobile Country Code of interest
        @type mcc: int

        @return: list of unique Mobile Network Codes
        @rtype: list
        """

        return self.sql("SELECT * FROM mnc WHERE mcc=%s"%mcc)

    def getcids(self, mcc,mnc,la):
        """ 
        Return a list of unique cells registered in the database belonging to the
        supplied Mobile Country Code (mcc),  Mobile Network Code (mnc) and
        Location Area (la).  

        @author: Brendan Johan Lee
        @contact: brendajl@simula.no
        @version: 1.0

        @param mcc: Mobile Country Code of interest
        @type mcc: int
        @param mnc: Mobile Network code of interest
        @type mnc: int
        @param la: Location Area of interest
        @type la: int

        @return: list of unique cells
        @rtype: list
        """

        return self.sql("SELECT * FROM cells WHERE mcc=%s AND mnc=%s AND la=%s"%(mcc,mnc,la))

    def getlas(self, mcc,mnc):
        """ 
        Returns a list of unique Location Areas (la) registered in the database based
        on the supplied Mobile Country Code (mcc) and Mobile Network Code (mnc).  

        @author: Brendan Johan Lee
        @contact: brendajl@simula.no
        @version: 1.0

        @param mcc: Mobile Country Code of interest
        @type mcc: int
        @param mnc: Mobile Network Code of interest
        @type mnc: int

        @return: list of unique Location Areas
        @rtype: list
        """

        return self.sql("SELECT * FROM la WHERE mcc=%s AND mnc=%s"%(mcc,mnc))

    def getcells(self, mcc=None,mnc=None,la=None):
        """ 
        Return all of the cells in the GLoc database. Can optionally be
        limited to cells within a Mobile Country Code, Mobile Network
        Code and Location Area

        @author: Brendan Johan Lee
        @contact: brendajl@simula.no

        @version: 1.0

        @param mcc: Optional limit on Mobile Country Code
        @type mcc: int
        @param mnc: Optional limit on Mobile Network Code (makes no sense if mcc is None)
        @type mnc: int
        @param la: Optional limit on Location Area (makes no sense if mnc is None)
        @type la: int

        @return: Textual representation of optional limitations and information on cells
        @rtype: tupple of string and list of tupples
        """

        sql = ""
        if mcc:
            sql += "%s mcc=%i "%("WHERE" if first else "AND",int(mcc))
        if mnc:
            sql += "%s mnc=%i "%("WHERE" if first else "AND",int(mnc))
        if la:
            sql += "%s la=%i "%("WHERE" if first else "AND",int(la))

        return self.sql("SELECT * FROM gatheredcells %s"%(sql))

    def getnorwegian(self):
        """ 
        Returns a list of all of the cells ripped from finnsenderen.no and
        registered in the database.

        @author: Brendan Johan Lee
        @contact: brendajl@simula.no
        @version: 1.0

        @return: List of cells
        @rtype: list
        """

        return self.sql("SELECT * FROM norwegiancells.sites;")
    
    def sql(self, sql):
        """
        Run a SQL-query against the database and return the result.

        @author: Brendan Johan Lee
        @contact: brendajl@simula.no

        @version: 1.0

        @param sql: SQL-query to be run
        @type sql: str

        @return: result of query
        @rtype: list
        """
        self.cur.execute(sql)
        return self.cur.fetchall()

    def __getdbcursor__(self):
        """
        Connect to the GLoc database and return the connection object.

        @author: Brendan Johan Lee
        @contact: brendajl@simula.no

        @version: 1.0

        @return: Connetion to database
        @rtype: psycopg2.extras.DictConnection
        """
        conn = psycopg2.extras.DictConnection("dbname='%s' user='%s' password='%s' host='%s' port='%s'"%(
                self.conf.db_name,self.conf.db_username,self.conf.db_password,self.conf.db_host,self.conf.db_port))
        return conn.cursor()
