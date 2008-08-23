from pyrobot.bot.script import Script

class bard(Script):
    def __init__(self, config):
        if 'leader' in config:
            self.target = config['leader']
        
    def register(self, server):
        self.server = server
        
        self.targetLocated=False
        self.targets={}
        self.targetPos = (0, 0)
        self.targetID=''
        
        self.instrument = 1901
        self.weapon = 1714
        
        self.useEncore = False
        self.bragiUp = False
        
        self.RANDOMIZE=True
        
        self.CONCENTRATE=False
        
        self.mode = "flashbragi"
        
        
        self.instrumentSlot = -1
        self.weaponSlot = -1
            
    def start(self):
        self.server.addEvent(self.waitForInstrument, 2)        
        
    def equipInstrument(self):
        for i in self.inventory:
            if i.itemid == self.instrument:
                self.server.sendEquip(i.itemid, )
                
                
    def waitForInstrument(self):
        for item in self.server.inventory:
            if item.itemno == self.instrument:
                self.instrumentSlot = item.index
            elif item.itemno == self.weapon:
                self.weaponSlot = item.index
                
        if self.instrumentSlot == -1 or self.weaponSlot == -1:
            print "Don't have the necessary weapons!"
            return
        
        curtime = time.time()
        
        self.nextConcentrate = curtime
        
        if self.mode == "flashbragi" or self.mode == "longbragi":
            self.nextBragi = curtime
            
        for p in self.server.partyMembers:
            if p[1] == self.target:
                self.targetID = p[0]
                self.targetLocated = True
        self.bardLoop()
        
        
    def stop(self):
    	pass
             
    def handlers(self):
        return [(packet.CHARINFO, self.charInfo),
                (packet.PRIVMESSAGE, self.privMsg),
                (packet.SKILLCAST, self.skillCast),
                (packet.STATUSLOAD, self.statusLoad),
                (packet.PARTYMESSAGE, self.partyMessage),
                (packet.NODAMAGE, self.noDamage)]

    def sendSong(self, song, level):
        if self.useEncore == True:
            print 'sending encore!'
            self.server.sendTargetSkill(self.server.accountID,0x131 , 1)
        else:
            print 'sending bragi!'
            self.server.sendTargetSkill(self.server.accountID,song , level)
            
        
    def privMsg(self, name, msg):	
        name = name.split('\x00')[0]
        msg = msg.split('\x00')[0]
        
        if not name == self.target:
            return

        if msg.startswith('(Hi)'):
            msg = msg[msg.index('(Hi)') + 5:]
            
        parts = msg.split(" ")

        if len(parts) == 0:
            return

        parts = msg.split(" ")
        
        t = self.targetID

    	if len(parts) > 1:
    		targetName = msg[msg.index(' ')+1:]
    		if targetName in self.targets:
    			t = self.targets[targetName]	
			
        if parts[0] == "stop":
            self.mode = "stop"

    	if parts[0] in ["flashbragi","longbragi","apple","joke"]:
            self.mode = parts[0]
            
        if parts[0] == "flashbragi" or parts[0] == "longbragi":
            self.nextBragi = time.time()
    		
    def partyMessage(self, id,msg):    
        msg = msg.split('\x00')[0]
        if msg.find('UltimaBR') > 0 and msg.find('joke') > 0:
            self.joke = not self.joke
        print 'we got a party message!'
        print msg
        
    def noDamage(self, sid, heal, dstid, srcid, fail):
        if sid == 0x139:
            self.joked = True
        if sid == 0x141:
            if self.useEncore == False:
                self.useEncore = True
            if self.mode == "flashbragi":
                self.server.sendEquipItem(self.weaponSlot, 0x22)
                self.nextBragi = time.time() + 15
            else:
                self.nextBragi = time.time() + 180
                    
    def charInfo(self, i, name, party, gname, gid):
        name= name.split('\x00')[0]
        if name not in self.targets:
            self.targets[name] = i
        if not self.targetLocated and name == self.target:
            self.nextCast = time.time() + 2
            self.targetLocated=True
            self.targetID=i

    def skillCast(self, srcid, dstid, dstx, dsty, skill, pl, casttime):
        if srcid == self.targetID:
            delay = float(casttime)/1000
            self.nextCast = time.time() + delay

    def statusLoad(self):
        self.server.sendMapAck()


    def switchToBow(self):
        self.server.mapSocket.send('\xa9\x00\x04\x00\x22\x00')
        
    def switchToInstrument(self):
        self.server.mapSocket.send('\xa9\x00\x05\x00\x02\x00')
    
    def statusLoad(self, type, id, flag):
        if not id == self.server.accountID:
            return
    
        print 'got a status load!!!!' , type
        if type == 175 and flag == 1:
            self.server.sendEquipItem(self.weaponSlot, 0x22)
            self.nextBragi = time.time() + 10
        elif type == 3 and flag == 1:
            self.nextConcentrate = time.time() + 240
    

    def skillLoop(self):
        pass

    def bardLoop(self):
        self.server.addEvent(self.bardLoop, 0.25)
        
        if self.mode == "stop" or not self.targetLocated:
            return
    
        curtime = time.time()

        if curtime >= self.nextConcentrate:
            if self.mode == "longbragi":
                print "longbragu mode!!!"
                self.server.sendEquipItem(self.weaponSlot, 0x22)
                self.nextBragi = curtime
            self.server.sendTargetSkill(self.server.accountID,0x2d , 10)
            return

        if (self.mode == "flashbragi" or self.mode == "longbragi") and curtime >= self.nextBragi:
            self.server.sendEquipItem(self.instrumentSlot, 0x2)
            self.sendSong(0x141,10)
            return
        
