from pyrobot.bot.script import Script

class greed(Script):
    def __init__(self, config):
        pass
        
    def register(self, server):
        self.server = server
        
        self.targetLocated=False
        self.targets={}
        self.targetPos = (0, 0)
        self.targetID=''
        self.RANDOMIZE=False
        self.greedEnabled=False
        
    def start(self):
        self.nextCast = time.time() + 4
        self.server.addEvent(self.Waitloop, 4)

    def stop(self):
    	pass
             
    def handlers(self):
        return [(packet.CHARINFO, self.charInfo),
		(packet.CHARMOVE, self.charMove),
		(packet.PRIVMESSAGE, self.privMsg),
		(packet.CHANGEMAP, self.changeMap)]

        
    def privMsg(self, name, msg):	

        name = name.split('\x00')[0]
        msg = msg.split('\x00')[0]
        t = self.targetID
        if not name == self.target:
            return
	if not msg.startswith('(Hi)'):
	    return

	msg = msg[msg.index('(Hi)')+5:]
        parts = msg.split(" ")   
        if len(parts) == 0:
            return

        if len(parts) > 1:
            targetName = msg[msg.index(' ')+1:]
            if targetName in self.targets:
                t = self.targets[targetName]	
			

        if parts[0] == "greed":
            self.greedEnabled = not self.greedEnabled
    	
        if parts[0] == "follow":
            self.RANDOMIZE=not self.RANDOMIZE
    		
        
    def charInfo(self, i, name, party, gname, gid):
        name= name.split('\x00')[0]
        if name not in self.targets:
            self.targets[name] = i
        if not self.targetLocated and name == self.target:
            self.nextCast = time.time() + 2
            self.targetLocated=True
            self.targetID=i

    def changeMap(self):
        self.server.sendMapAck()

    def statusLoad(self, type, id, flag):
        if not id == self.server.accountID:
            return
    
        print 'we got a status update!!!'
        if type == 175 and flag == 1:
            print 'we got bragid!!!, next cast in 10 seconds'
            self.switchToBow()
            self.nextBragi = time.time() + 10

    
    def updateStatus(self, property, value):
        pass
        
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

    def Waitloop(self):

        self.server.addEvent(self.Waitloop, 0.5)
        if not self.targetLocated:
            return
        curtime = time.time()
        if self.greedEnabled:
            if curtime > self.nextCast:
                self.server.sendGreed(self.server.accountID)
                self.nextCast = curtime + 4

            
        
        
