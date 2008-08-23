import struct
import util
import bsddb
import zlib
mapcache = bsddb.hashopen('mapcache.db')
costcache = bsddb.hashopen('costcache.db')
#data storage class
class Cell:
    type=0
    x=0
    y=0
    def __str__(self):
       return '%d,%d)'%(self.x, self.y) 


def loadGat(filename):
    if filename not in mapcache:
        return
    print 'reading file'
    mapdata = zlib.decompress(mapcache[filename])
    costdata = zlib.decompress(costcache[filename])
    cells=[]
    (width, height) = struct.unpack('HH', mapdata[0:4])

    #print width, height
    #build the map
    for x in range(0, width):
        col=[]
        for y in range(0, height):
            col.append(Cell())
        cells.append(col)
        
    offset = 4
    for y in range(0, height):
        for x in range(0, width):
            cell = cells[x][y]
            cell.type = ord(mapdata[offset])
            cell.cost = ord(costdata[offset])
            cell.x = x
            cell.y = y
            cell.neighbors=[]
            offset+=1
            
    
    for y in range(0, height):
        for x in range(0, width):
            cell = cells[x][y]
            if not(cell.type == 3 or cell.type == 0):
                continue
            nl=[]
            dx = [-1,0,1]
            dy = [-1,0,1]
            for a in dx:
                for b in dy:
                    if a == b == 0:
                        continue
                    tx = x+a
                    ty = y + b
                    if x> 0 and x < width - 1 and y >0 and y< height-1:
                        cell.neighbors.append(cells[tx][ty])
            
    print 'done reading file'
    return width, height, cells