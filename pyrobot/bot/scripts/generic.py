
import time

from pyrobot.bot.script import Script
from pyrobot.bot import packet,util
import logging

log = logging.getLogger(__name__)

class simplescript(Script):
    def __init__(self,config):
        self.config = config
    def register(self, client):
        self.client = client
    def handlers(self):
        return []
    def start(self):
        pass
    def stop(self):
        pass
    
class changemap(simplescript):
    def handlers(self):
        return [(packet.CHANGEMAP, self.changeMap)]
    def changeMap(self, name, x, y):
        self.client.addEvent(lambda: self.client.sendMapAck(), 1)


class accepttrade(simplescript):
    def handlers(self):
        return [(packet.TRADEREQUEST, self.traderequest),
                (packet.TRADELOCK, self.tradelock),
                (packet.TRADESTART, self.tradestart)]
        
    def traderequest(self, name, charId):
        self.client.sendTradeAck(3)
        
    def tradestart(self, type, charId):
        #add the item
        self.client.addTradeItem(0, 0)
        self.client.sendTradeOk()
        
    def tradelock(self):
        self.client.sendTradeCommit()
             
    def start(self):
        pass
        
class acceptparty(simplescript):
    def handlers(self):
        return [(packet.PARTYINVITE, self.partyInvite)]
        
    def partyInvite(self, accountId, partyName):
        self.client.sendPartyReply(accountId, 1)
        
    def tradestart(self, type, charId):
        #add the item
        self.client.addTradeItem(0, 0)
        self.client.sendTradeOk()
        
    def tradelock(self):
        self.client.sendTradeCommit()
             
    def start(self):
        pass

class autofollow(Script):
    def __init__(self, config):
        self.target = util.getConfig(config, 'leader')
        log.info('Autofollow leader: %s', self.target)
        self.targetLocated=False
        self.targets={}
        self.targetPos = (0, 0)
        self.targetID=''
        self.RANDOMIZE=False
        
    def register(self, server):
        self.server = server
        
    def start(self):
        pass
    def stop(self):
    	pass
             
    def handlers(self):
        return [(packet.CHARINFO, self.charInfo),
		(packet.CHARMOVE, self.charMove),
        (packet.CHARNAME, self.charName),
        (packet.MOVE, self.charMove),
		(packet.PRIVMESSAGE, self.privMsg)]

    def privMsg(self, name, msg):	
        name = name.split('\x00')[0]
        msg = msg.split('\x00')[0]
        
        t = self.targetID
        if not name == self.target:
            return

        if msg.startswith('(Hi)'):
            msg = msg[msg.index('(Hi)') + 5:-1]
        parts = msg.split()
        if len(parts) == 0:
            return

    	if len(parts) > 1:
    		targetName = msg[msg.index(' ')+1:]
    		if targetName in self.targets:
    			t = self.targets[targetName]	
			
        if parts[0] == "follow":
            self.RANDOMIZE=not self.RANDOMIZE
    	
    def charName(self, i, name):
        name= name.split('\x00')[0]
        if name not in self.targets:
            self.targets[name] = i
        if not self.targetLocated and name == self.target:
            self.targetLocated=True
            self.targetID=i
        
    def charInfo(self, i, name, party, gname, gid):
        name= name.split('\x00')[0]
        self.charName(i, name)
        
    def charMove(self, i, x0, y0, x1, y1):
        self.server.sendGetInfo(i)
        
        if not self.targetLocated:
            return 
    
        if i != self.targetID:
            return
        dx = x1 - x0
        dy = y1 - y0
        tx = x1
        ty = y1
        if dx < 0:
            tx +=1
        elif dx > 0:
            tx -=1

        if dy < 0:
            ty +=1
        elif dy > 0:
            ty -=1

        if self.RANDOMIZE:
            if random.uniform(0, 1) < 0.5:
                tx += 1
            else:
                tx -= 1
            if random.uniform(0, 1) < 0.5:
                ty += 1
            else:
                ty -= 1
        self.targetPos = (tx, ty)
        self.lastMove = time.time()
        self.server.addEvent(lambda: self.server.sendMove(tx, ty), 0.4)


class updatestatus(Script):
    def __init__(self, config):
        self.target = util.getConfig(config, 'leader')
    def register(self, server):
        self.server = server
        self.RANDOMIZE=True
        
    def start(self):
        self.server.addEvent(self.checkLoop, 2)

    def stop(self):
        pass
             
    def handlers(self):
        return []

    def checkLoop(self):
        self.server.addEvent(self.checkLoop, 5)
        if self.server.weight != -1 and self.server.maxweight != -1:
            if float(self.server.weight)/self.server.maxweight >=  0.5:
                self.server.sendMessage(self.target, "I'm overweight!")
        if self.server.sp != -1 and self.server.maxsp != -1:
            if float(self.server.sp)/self.server.maxsp <=  0.1:
                self.server.sendMessage(self.target, "I'm running low on SP!")
                
class tocart(simplescript):
    def register(self, server):
        self.server = server
    
    def start(self):
        self.server.addEvent(self.moveToStorage, 2)

    def moveToStorage(self):
        items=[]
        for item in self.server.inventory:
            items.append((item.index, item.amount))
            
        for (i, q) in items:
            self.server.moveToCart(i, q)
            
    def stop(self):
        pass
         
class tostorage(Script):
 
    def register(self, server):
        self.server = server
    
    def start(self):
        self.server.addEvent(self.moveToStorage, 5)

    def moveToStorage(self):
        items=[]
        for item in self.server.inventory:
            items.append((item.index, item.amount))
            
        for (i, q) in items:
            self.server.moveToStorage(i, q)
            
    def stop(self):
        pass
                 
    def handlers(self):
        return []

class fromcart(Script):
 
    def register(self, server):
        self.server = server
    
    def start(self):
        self.server.addEvent(self.getFromCart, 2)

    def getFromCart(self):
        items=[]
        self.server.getFromCart(2, 1)
            
    def stop(self):
        pass
             
    def handlers(self):
        return []

class precast(Script):    
    def __init__(self, x, y):
            self.x = x
            self.y = y
            self.amped=False

    def handlers(self):
        return [(packet.SKILLCAST, self.skillCast)]
    
    def register(self, client):
        self.client = client
        
    def start(self):
        self.client.addEvent(self.cast, 2)

    def stop(self):
        pass
    
    def skillCast(self, srcid, dstid, dstx, dsty, skill, pl, casttime):
        if srcid != self.client.accountID:
            return
        if skill == 0x16e:
            self.amped = True
        if skill == 0x59:
            self.amped = False
        
    def cast(self):
        self.client.addEvent(self.cast, 0.25)
        if self.amped == False:
            self.client.sendTargetSkill(self.client.accountID, 0x16e, 1)
        else:
            self.client.sendAreaSkill(0x59, 10, self.x, self.y)
        
class doat(Script):
    def __init__(self, scripts, map, x, y):
        self.scripts = scripts
        self.map = map
        self.x = x
        self.y = y
        self.moving = False
        
     
    def register(self, client):
        self.client = client
        self.p = pathfinder.Pathfinder(self.client.mapname)
    
    def handlers(self):
        return [(packet.WALKOK, self.walkOk),
                (packet.CHANGEMAP, self.changeMap)] 
    
    def start(self):
        self.client.addEvent(self.checkPos, 3)

    def stop(self):
        pass
    
    def changeMap(self, map, x, y):
        self.p = pathfinder.Pathfinder(self.client.mapname)
        
    def checkPos(self):
        if self.map != self.client.mapname:
            self.client.addEvent(self.checkPos, 3)
            return
        
        if self.client.x == self.x and self.client.y == self.y:
            self.startScripts()
        else:
            self.moveToSpot()
            
    def moveToSpot(self):
        path = self.p.findPath(self.client.x, self.client.y, self.x, self.y)
        
        if len(path) == 0:
            self.client.addEvent(self.moveToSpot, 3)
            return
        self.path = path
        self.moving = True
        self.pathindex = 5
        self.moveNext()
        
    def moveNext(self):
        if not (self.client.x == self.x and self.client.y == self.y):
            self.client.addEvent(self.moveNext, 1.0)
        if self.pathindex >= len(self.path):
            (x, y) = self.path[-1]
        else:
            (x, y) = self.path[self.pathindex]
        self.pathindex += 6
        self.client.sendMove(x, y)
        
    def walkOk(self, x0, y0, x1, y1):
        if self.moving != True:
            return
        if x1 == self.x and y1 == self.y:
            self.startScripts()
        else:
            self.pathindex+=1
            
    def startScripts(self):
        for s in self.scripts:
            self.client.startScript(s)
            
    def stopScripts(self):
        pass