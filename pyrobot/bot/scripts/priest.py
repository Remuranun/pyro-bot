import time
import logging

from pyrobot.bot import packet,util
from pyrobot.bot.script import Script

log = logging.getLogger(__name__)

class priest(Script):
    def __init__(self, config):
        self.config = config
        for (key,value) in config:
            if key == 'leader':
                self.target = value
                log.info('Leader: %s', self.target)
                
        #simulate dual-client (i.e a lot longer delays between casts)
        self.SIMULATEDC=False
        
    def register(self, server):
        self.server = server
        
        #list of targets that we see
        self.targets={}
        self.targetNames={}
        self.positions={}
        
        #Information about the target
        self.targetPos = (0, 0)
        self.targetID=''
        self.targetLocated=False

        #lower bound on the time it takes to cast again
        self.nextCast = time.time()
        self.lastMove = time.time()
        
        #information about character skills
        self.skills={}
        

        #contains information about party members, keyed by account ID
        self.partyMembers={}

        #a list of Buff classes we're using
        self.buffs=[]

        #method of status update methods, keyed by status update ID
        self.statusUpdates={}


    class PartyMember:
    	#just a data storage class
    	pass

    class Buff:
        def register(self, priest):
            self.priest = priest
            self.myID = priest.server.accountID
            self.target = priest.target
            self.server = priest.server
            self.skills = priest.skills
            self.partyMembers = priest.partyMembers

        def getStatusNumber(self):
            abstract

        def needsBuff(self):
            abstract
    
        def sendBuff(self):
            abstract

        def updateStatus(self, id, oldflag, newflag):
            abstract

    class GenericBuff(Buff):
        def __init__(self, priest, skillId, level, duration, statusNumber, mode, targets, name, anal):
            self.priest = priest

            self.duration = duration
            self.statusNumber = statusNumber
            self.mode = mode
            self.skillId = skillId
            self.level = level
            self.attempts={}
            self.nextCast ={}
            self.name = name
            self.anal= anal
            self.targets = targets
            self.targetIDS = []
            self.mode = mode
            self.findTargets()
            
        def findTargets(self):
            if self.mode == 1:
                for id in self.priest.partyMembers:
                    p=self.priest.partyMembers[id]
                    if p.name in self.targets:
                        self.targetIDS.append(id)
                        
        def getStatusNumber(self):
            return self.statusNumber

        def updateStatus(self, id, oldflag, newflag):
            curtime = time.time()
            self.attempts[id]=0
            if newflag == 0:
                if self.anal == True:
                    self.nextCast[id] = curtime
                    return
                

            if oldflag == 0 or id not in self.nextCast:
                self.nextCast[id] = curtime + self.duration
                return

            nextWait = self.nextCast[id]
            
            if curtime > nextWait:
                self.nextCast[id] = time.time() + self.duration
            
            
            #curWait = self.nextCast[id]
            #if cur
            #if id in self.next
            #they just got blessed, wait 4 minutes
            #curtime = time.time()
            #nextTime = 


        def needsBuff(self):
            self.findTargets()
            curtime = time.time()
            population = []
            if self.mode == 0:
                population = self.partyMembers.keys()
            else:
                population = self.targetIDS
			
            for id in population:
                p = self.partyMembers[id]
                if not (p.offline==0 and p.map == self.partyMembers[self.myID].map):
                    continue
                if p.id in self.nextCast and self.nextCast[p.id] > curtime:
                    continue

                if p.id not in self.attempts:
				    self.attempts[p.id]=0

                self.attempts[p.id]+=1
                if self.attempts[p.id] >= 10:
                    self.attempts[p.id] = 0
                elif self.attempts[p.id]>=5:
				    continue
                return p.id
            return False

        def sendBuff(self, id):
            self.server.sendToId(id, self.skillId, self.level)

    class Res(Buff):
        def __init__(self):
            self.needsRes={}

        def getStatusNumber(self):
            return 'res'

        def updateStatus(self, id, oldflag, newflag):
            #did we res him?
            if id in self.needsRes and oldflag != 0:
                del self.needsRes[id]	


            #he's not dead
            if oldflag != 0:
                return

            #if you die, you can't res
            if id == self.myID:
                return

            self.needsRes[id] = True

        def needsBuff(self):
            curtime = time.time()

            if len(self.needsRes.keys()) == 0:
                return False

            return self.needsRes.keys()[0]

        def sendBuff(self, id):
            self.server.addEvent(lambda: self.server.sendToId(id, 0x36, 4), 0.5)

    class Teleport(Buff):
        def __init__(self):
            self.tele = False
        def getStatusNumber(self):
            return 'tele'

        def updateStatus(self, id, opt1, opt2):
            if opt1 == 1:
	         self.tele = True
            elif opt1 == 0:
	         self.tele = False

        def needsBuff(self):
	    if self.tele == True:
	        return self.myID
	    return False

        def sendBuff(self, id):
            self.server.sendToId(self.server.accountID, 26, 1)

    class Recovery(Buff):
        def __init__(self):
            self.needsRecovery={}
            self.attempts={}
        def getStatusNumber(self):
            return 'recovery'

        def updateStatus(self, id, opt1, opt2):
            self.attempts[id] = 0
            if id in self.needsRecovery and opt1 == 0:
                del self.needsRecovery[id]    

            if opt1 == 0:
                return
        
            if id == self.myID:
                return
        
            if id not in self.attempts:
                self.attempts[id]=0

            if opt1 == 1 or opt1 == 2 or opt1 == 6:
                self.needsRecovery[id] = True

        def needsBuff(self):
            curtime = time.time()

            if len(self.needsRecovery.keys()) == 0:
                    return False
                
            id = self.needsRecovery.keys()[0]
            self.attempts[id]+=1
            if self.attempts[id] > 5:
                return False
            if self.attempts[id] > 10:
                self.attempts[id] = 0
                

            return self.needsRecovery.keys()[0]

        def sendBuff(self, id):
            self.server.addEvent(lambda: self.server.sendToId(id,72,1), 1)  


    class Lex(Buff):
        def __init__(self):
            self.needsLex={}
        def getStatusNumber(self):
            return 'lex'
        def updateStatus(self, id, opt1, opt2):
            if opt1 == 0:
                self.needsLex[id] = time.time()+(float(opt2)/1000)
            else:
                if id in self.needsLex:
                    del self.needsLex[id]
            

        def needsBuff(self):
            if len(self.needsLex.keys()) == 0:
                return False
            curtime = time.time()
            
            first = self.needsLex.keys()[0]
            delay = self.needsLex[first]
            if curtime >= delay:
                del self.needsLex[first]
                return False
            return first

        def sendBuff(self, id):
            self.server.sendToId(id, 78, 1)
            
    class Pneuma(Buff):
        def __init__(self):
            self.nextPneuma = time.time()
        #    self.pneumaID = None
        #    for id in priest.partyMembers:
        #        p = priest.partyMembers[id]
        #        if p.name == target:
        #            self.pneumaID = id
        #            
        #    self.nextPneuma = time.time()
            
        def getStatusNumber(self):
            return 'pneuma'

        def updateStatus(self, id, opt1, opt2):
            if opt1 == 0 and opt2 == 1:
                self.nextPneuma = time.time() + 10
            if opt1 == 1 and opt2 == 0:
                self.nextPneuma = time.time()

        def needsBuff(self):
            curtime = time.time()
            if curtime > self.nextPneuma:
                return True
            else:
                return False

        def sendBuff(self, id):
            target = self.priest.partyMembers[self.priest.targetID]
            self.server.sendPneuma(target.x, target.y) 

    class Heal(Buff):
        def __init__(self, level):
            self.healKeys={}
            self.hpHeal = []
            self.attempts={}
            self.level = level

        def getStatusNumber(self):
            return 'heal'

        def updateStatus(self, id, oldflag, newflag):
            if id in self.healKeys:
                healkey  = self.healKeys[id]
                healkey[0] = float(oldflag)/float(newflag)
            else:
                healkey = [float(oldflag)/float(newflag), id]
                self.healKeys[id]=healkey
                self.hpHeal.append(healkey)

            self.hpHeal.sort()
            self.attempts[id]=0

        def needsBuff(self):
            curtime = time.time()

            for [p, k] in self.hpHeal:
                if p > 0.75:
                    return False
                m = self.partyMembers[k]
                if m.offline == 0 and m.map == self.partyMembers[self.myID].map:
                    self.attempts[k]+=1
                    return k
            return False


        def sendBuff(self, id):
            self.server.sendToId(id, 0x1c, self.level) 

    def start(self):
        for p in self.server.partyMembers:
            self.addPartyMember(p)
        self.myHP = (self.server.hp, self.server.maxhp)
        self.token = self.server.addEvent(self.initBuffs, 1)

    def initBuffs(self):
    	bless = self.GenericBuff(self, 0x22, 10, 4*60, 10, 0, None, "bless", True)
    	agi = self.GenericBuff(self, 0x1d, 10, 4*60, 12, 0, None, "agi", True)
    	kyrie = self.GenericBuff(self, 73,10, 60, 19, 1, ['MyBigAss'], "kyrie", True)
    	imp = self.GenericBuff(self, 66, 5, 60, 15,  1, ["Pylon"], "imp", True)
        suff = self.GenericBuff(self, 0x43, 3, 10, 16, 1, ['Pylon'], "suff", True)
    	mag = self.GenericBuff(self, 0x4a, 5, 60, 20,1, ['Pylon'], "mag", True)
    	#buffClasses = [self.Res(), self.Recovery(), self.Heal(), self.Lex(), mag, suff, bless, agi]
        buffClasses = [self.Res(), self.Recovery(), self.Teleport(), self.Heal(10),suff,self.Lex(), bless, agi,mag]
        #buffClasses = [self.Res(), self.Heal(1), bless, agi, imp]

	for  instance in buffClasses:
		statusNumber = instance.getStatusNumber()
		if statusNumber != None:
			self.statusUpdates[statusNumber]=instance.updateStatus
		instance.register(self)
		self.buffs.append(instance)

        self.server.addEvent(self.priestLoop, 0)
    
    def stop(self):
    	pass
             
    def handlers(self):
        return [(packet.CHARINFO, self.charInfo),
                (packet.CHARNAME, self.charName),
                (packet.CHARMOVE, self.charMove),
                (packet.MOVE, self.charMove),
                (packet.CHARAREA, self.charArea),
                (packet.PRIVMESSAGE, self.privMsg),
                (packet.SKILLCAST, self.skillCast),
                (packet.PARTYHP, self.partyHP),
                (packet.GETPROPERTY, self.getProperty),
                (packet.CHANGEMAP, self.changeMap),
                (packet.SKILLINFO, self.skillInfo),
                (packet.PARTYMEMBER, self.partyMember),
                (packet.PARTYINFO, self.partyInfo),
                (packet.STATUSLOAD, self.statusLoad),
                (packet.CHANGEOPTION, self.changeOption),
                (packet.POSEEFFECT, self.poseEffect),
                (packet.NODAMAGE, self.noDamage),
                (packet.USEITEMACK, self.useItemAck)]

    def heal(self, id):
        self.server.addEvent(lambda: self.server.sendToId(id, 0x22, 10) , 0)
        self.server.addEvent(lambda: self.server.sendToId(id, 0x1d, 10), 1.5)
        self.server.addEvent(lambda: self.server.sendToId(id, 0x1c, 10) , 3)
        self.server.addEvent(lambda: self.server.sendToId(id, 0x1c, 10) , 5)

    def privMsg(self, name, msg):
    	
        name = name.split('\x00')[0]
        msg = msg.split('\x00')[0]

        t = None
        if not name == self.target:
            return

        if msg.startswith('(Hi)'):
            msg = msg[msg.index('(Hi)') + 5:-1]
            
        parts = msg.split(" ")

        if len(parts) == 0:
            return

        if len(parts) > 1:
            targetName = msg[msg.index(' ')+1:]
            for n in self.targetNames:
                if n.lower().startswith(targetName.lower()):
                    t = self.targetNames[n]
			
        if parts[0] == "tele":
            self.statusUpdates['tele'](self.server.accountID, 1, 0)
    
        if t == None:
            return
        if parts[0] == "heal":
            self.heal(t)

        if parts[0] == "buff":
            self.buff(t)

        if parts[0] == "target":
            if t in self.partyMembers:
                self.targetID = t
                self.targetName = self.partyMembers[t].name
        if parts[0] == "follow":
            self.RANDOMIZE=not self.RANDOMIZE
    def skillInfo(self, skillList):
    	#we might want to use this sometime
        self.skills = skillList
    	pass

    def partyMember(self):
    	#this probably gets sent if a party member joins or leaves
    	pass

    def addPartyMember(self, l):
            m = self.PartyMember()
            (m.id, m.name, m.map, m.leader, m.offline) = l
            m.status={}
            self.partyMembers[m.id] = m
            if m.id in self.positions:
                m.x = self.positions[m.id][0]
                m.y = self.positions[m.id][1]
            if m.name == self.target:
                self.targetID = m.id
                self.targetLocated = True
                
    def partyInfo(self, partyList):
        for l in partyList:
            self.addPartyMember(l)

    def statusLoad(self, type, id, flag):
        #we dont care about the status of non-party members
        if id not in self.partyMembers:
            return
        
        #return if we aren't paying attention to these statuses
        if type not in self.statusUpdates:
            return

        if type in self.partyMembers[id].status:
            oldflag = self.partyMembers[id].status[type]
        else:
            oldflag = None

        self.partyMembers[id].status[type]=flag

        self.statusUpdates[type](id, oldflag, flag)
		
    def changeOption(self, id, opt1, opt2, option):
        if id in self.partyMembers:
            p = self.partyMembers[id]
            if 'recovery' in self.statusUpdates:
                self.statusUpdates['recovery'](id, opt1, opt2)
            if 10 in self.statusUpdates and opt2 == 2:
	        self.statusUpdates[10](id, 1, 0)

    def poseEffect(self, sid, id, val, x, y):
        if id in self.partyMembers:
            p = self.partyMembers[id]
            if sid == 0x19 and 'pneuma' in self.statusUpdates:
                self.statusUpdates['pneuma'](id, 0, 1)
                
    def noDamage(self, sid, heal, dstid, srcid, fail):
        if srcid == self.server.accountID:
            if sid == 78 and 'lex' in self.statusUpdates:
                self.statusUpdates['lex'](dstid, 1, 0)
                    
    def useItemAck(self , index, itemid, id, amount, ok):
        if id == self.targetID and itemid == 601:
            if 'tele' in self.statusUpdates:
                self.statusUpdates['tele'](self.server.accountID, 1, 0)
            
            
    def charName(self, i, name):
        name= name.split('\x00')[0]
        if i not in self.targets:
            self.targetNames[name] = i
            self.targets[i] = True
        
        
    def charInfo(self, i, name, party, gname, gid):
        self.charName(i, name)

    def skillCast(self, srcid, dstid, dstx, dsty, skill, pl, casttime):
    	#if we cast something, we have to wait at least the cast time + delay
        if srcid == self.server.accountID:
            nextCast = float(casttime)/1000 + 0.5
            self.server.removeEvent(self.token)
            self.token = self.server.addEvent(self.priestLoop, nextCast)
        elif srcid in self.partyMembers:
            if skill == 0x54 or skill == 379 or skill == 267 or skill == 266 or skill == 15 or skill == 19:
                if 'lex' in self.statusUpdates:
                    self.statusUpdates['lex'](dstid, 0, casttime)
    	
    def partyHP(self, srcid, hp, maxhp):
        if 'heal' in self.statusUpdates:
            self.statusUpdates['heal'](srcid, hp, maxhp)
        if 'res' in self.statusUpdates:
            self.statusUpdates['res'](srcid, hp, maxhp)

    def changeMap(self, map, x, y):
        if 'tele' in self.statusUpdates:
            self.statusUpdates['tele'](self.server.accountID, 0, 0)
        

    def getProperty(self, property, value):
        if 'heal' not in self.statusUpdates:
            return

        hp = self.server.hp 
        maxhp = self.server.maxhp
        if self.server.accountID not in self.partyMembers:
            return
        self.partyMembers[self.server.accountID].maxhp = maxhp
        self.partyMembers[self.server.accountID].hp = hp
        self.statusUpdates['heal'](self.server.accountID, hp, maxhp)
		
    #simple auto-follow
    def charArea(self, i, x, y):
        self.positions[i] = (x, y)
        if i not in self.partyMembers:
            self.server.sendGetInfo(i)
            return
        if i in self.targets:
            self.partyMembers[i].x = x
            self.partyMembers[i].y = y
        
    #simple auto-follow
    def charMove(self, i, x0, y0, x1, y1):
        self.positions[i] = (x1, y1)
        if i not in self.partyMembers:
            self.server.sendGetInfo(i)
            return
        if i in self.partyMembers:
            self.partyMembers[i].x = x1
            self.partyMembers[i].y = y1
        if 'pneuma' in self.statusUpdates:
            self.statusUpdates['pneuma'](i, 1, 0)

            
    def priestLoop(self):
        #by default, we spam every quarter second
        self.token = self.server.addEvent(self.priestLoop, 0.25)

        curtime = time.time()
        if self.SIMULATEDC == True:
            if not (curtime - self.lastMove >= 1.5):
                return
        
        for b in self.buffs:
            id = b.needsBuff()
            #iterate the count at the end of buffs
            if not id == False:
                b.sendBuff(id)
                #we only send one buff per quanta
                return
