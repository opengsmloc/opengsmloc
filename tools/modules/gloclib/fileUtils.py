""" 
 File utils used by the server configuration infrastructure.

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
import re
from time import time

def check_dir(strPath, strSubPath=None):
    """ 
    Checks if a path exists, and if not create it.

    @author: Unknown

    @version: 1.0

    @param strPath: path to be checked
    @type strPath: str
    @param strSubPath: will be appended to strPath before checking 
    @type strSubPath: str

    @return: checked path
    @rtype: str
    """

    if (strSubPath is not None):
        strPath = os.path.join(strPath, strSubPath)
    if not os.path.isdir(strPath):
        try:
            os.mkdir(strPath)
        except Exception:
            print 'Error! Can not create directory:'
            print '  ' + strPath
    return strPath

def del_file(filename):
    """ 
    Deletes a file ignoring errors

    @author: Unknown

    @version: 1.0

    @param filename: file to be deleted 
    @type filename: str
    """

    try:
        os.remove(filename)
    except:
        pass

def delete_old(filename, intSeconds=86400):
    """ 
    Remove file if is older than given time 

    @author: Unknown

    @version: 1.0

    @param filename: file to be removed
    @type filename: str
    @param intSeconds: remove file only if older than intSeconds. Defaults to 24h
    @type intSeconds: int
    """

    if os.path.isfile(filename):
        if (int(time() - os.path.getmtime(filename)) > intSeconds):
            try:
                os.remove(filename)
                return True
            except:
                pass
