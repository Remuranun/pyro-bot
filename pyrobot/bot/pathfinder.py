import readgat
import heapq

class PriorityDict(dict):
    def __init__(self):
        self.heap=[]
        self.priorities={}

    
    def __setitem__(self, i, y):
        if i not in self.priorities:
            key = [y, i]
            heapq.heappush(self.heap,key)
            self.priorities[i] = key
        else:
            key = self.priorities[i]
            key[0] = y
            heapq.heapify(self.heap)
        dict.__setitem__(self,i, y)
        
    def first(self):
        if len(self.heap) == 0:
            raise IndexError
        item=self.heap[0]
        return (item[1], item[0])
        
    def removeFirst(self):
        if len(self.heap) == 0:
            raise IndexError
        (p, k) = heapq.heappop(self.heap)
        dict.__delitem__(self, k)
        return k
    

class Pathfinder:
    def __init__(self, mapname):
        self.mapname = mapname
        self.costs={}
        self.width, self.height,self.cells = readgat.loadGat(mapname)
        #self.calcCosts()
        #self.printCosts()
        #self.printMap()
        #print "dim",self.width, self.height

                    
    def calcCosts(self):
        print 'calculating costs!'
        unwalkable=set([])
        queue=[]
        queued=set([])
        visited=set([])

        for x in range(0, self.width):
            for y in range(0, self.height):
                cell = self.cells[x][y]
                if not(cell.type == 0 or cell.type == 3):
                    queue.append(cell)
                    queued.add(cell)
                    unwalkable.add(cell)

        while len(queue) > 0:
            node = queue[0]
            del queue[0]
            queued.remove(node)
            visited.add(node)

            for s in node.neighbors:
                if s in visited or s in queued:
                    continue
                queue.append(s)
                queued.add(s)
                if node in unwalkable:
                    self.costs[s] = 5
                else:
                    self.costs[s] = max(self.costs[node]-1, 1)  
        print 'done calculating!'              
    
        
    def inrange(self, x, y):
        if y < 0 or y >= self.height:
            return False
        if x < 0 or x >= self.width:
            return False
        
        return True
    def isclear(self, x, y):
        if not self.inrange(x, y):
            return False
        
        return self.cells[x][y].type == 0
    
    def successors(self, (x, y)):
            if not self.inrange(x, y):
                return []
        
            succ = [(x-1, y),(x+1, y),(x, y+1),(x, y - 1)]
            return filter(lambda (x, y): self.inrange(x, y) and self.isclear(x,y), succ)

    def printMap(self, showlist):
        print 'printing map!'
        f = file('map.txt','w+')
        for y in range(0, self.height):
            row=''
            for x in range(0, self.width):
                ry =  self.height - y - 1
                cell = self.cells[x][ry]
                if cell in showlist:
                    row+='*'
                elif cell.type == 0:
                    row+= ' '
                else:
                    row+= '#'
            f.write(row+'\n')   
            
    def printCosts(self):
        f = file('map.txt','w+')
        for y in range(0, self.height):
            row=''
            for x in range(0, self.width):
                ry =  self.height - y - 1
                cell = self.cells[x][ry]
                if cell.type == 3 or cell.type == 0:
                    row+=str(cell.cost)
                else:
                    row+= '#'
            f.write(row+'\n')  

    def walkable(self, x0, y0, x1, y1):    
        pass
    
    def manhattan(self, c1, c2):
        
        width = c1.x - c2.x
        height = c1.y - c2.y
        if width < 0:
            width*=-1
        if height < 0:
            height*=-1
        return width + height
    
    #returns a sequence of points 
    #start at the start point, while the path is clear, keep going, 
    def findPath(self, x0, y0, x1, y1):
        print self.mapname,'finding path between ',(x0,y0), ' and ',(x1,y1)
        queue=PriorityDict()
        visited={}
        parent={}
        
        cell = self.cells[x0][y0]
        final=self.cells[x1][y1]
        
        queue[cell] = self.manhattan(cell, final)
        parent[cell] = None
        
        while True:
            #if len(queue.keys()) == 0:
            #    return []
            (node, cost) = queue.first()
            if node not in parent:
                print node
            if node == final:
                break
            
            queue.removeFirst()
            visited[node] = True

            g = cost - self.manhattan(node, final)
            for s in node.neighbors:
                if s in visited:
                    continue
                
                dist = g + s.cost
                h = self.manhattan(s, final)
                if s in queue:
                    if dist + h < queue[s]:
                        queue[s] =  dist+h
                        parent[s] = node
                else:
                    parent[s] = node
                    queue[s] = dist + h
                    

        tmp = final
        path = [final]
        while True:
            if parent[tmp] == None:
                break
            path.append(parent[tmp])
            tmp = parent[tmp]
            
        #self.printMap(path)
        path.reverse()
        return map(lambda c: (c.x, c.y), path)
    
    