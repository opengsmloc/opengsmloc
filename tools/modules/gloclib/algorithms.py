""" 
 Contains general algorithms to be used within all of the gloc
 project.

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

def orientation(p,q,r):
    """ 
    Return positive if p-q-r are clockwise, neg if ccw, zero if colinear.

    @author: Brendan Johan Lee
    @contact: brendajl@simula.no

    @version: 1.0

    @param p: p 
    @type p: point
    @param q: q
    @type q: point
    @param r: r
    @type r: point

    @return: neg if ccw, pos if cw, 0 if colinear
    @rtype: int
    @todo: Should be moved to an algorithm module
    """

    return (q[1]-p[1])*(r[0]-p[0]) - (q[0]-p[0])*(r[1]-p[1])

def hulls(Points):
    """ 
    Graham scan to find upper and lower convex hulls of a set of 2d points.

    @author: Brendan Johan Lee
    @contact: brendajl@simula.no

    @version: 1.0

    @param Points: Points to find convex hull of
    @type Points: Points

    @return: Upper and lower convex hulls
    @rtype: tupple of lists
    @todo: Should be moved to an algorithm module
    """

    U = []
    L = []
    Points.sort()
    for p in Points:
        while len(U) > 1 and orientation(U[-2],U[-1],p) <= 0: U.pop()
        while len(L) > 1 and orientation(L[-2],L[-1],p) >= 0: L.pop()
        U.append(p)
        L.append(p)

    L.reverse()
    U += L

    return U
    
