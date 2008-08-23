import socket
import struct
import time
import event
import sys
import random
import db
import script

def getTickCount(n):
    a=int(time.time()*1000);
    return struct.pack("Q", a)[0:n];

class Connection:
    mapSockets={}
    packetHandlers={}
    connections={}

    def __init__(self, server, username, password, slot, scripts):
        self.server = server
        self.pm = self.server.packetManager()
        self.username = username
        self.password = password
        self.slot = slot
        self.scripts = scripts
        self.inventory=[]
        self.cart=[]
        self.scriptInstances=[]
        self.scriptTokens={}
        self.partyMembers=[]
        
        self.zeny = -1
        self.hp = -1
        self.maxhp = -1
        self.sp = -1
        self.maxsp=-1
        self.weight = -1
        self.maxweight=-1
        Connection.connections[username]=self
        
    def addEvent(self, e, delay):
        eventToken = random.randint(0, sys.maxint)
        
	#this wrapper is necessary to perform 'cleanup' when an event ends
        def eventWrapper():
            e()
	    del self.scriptTokens[eventToken]
        
        token = event.addEvent(eventWrapper, delay)
        self.scriptTokens[eventToken] = token
	return eventToken
        
    def removeEvent(self, token):
    	eventToken = self.scriptTokens[token]
        event.removeEvent(eventToken)
        del self.scriptTokens[token]

    def connect(self):
        self.pm.connect(self)

    def disconnect(self):
        self.stopScripts()
        self.pm.sendQuitGame(self.mapSocket)
        event.removeSocket(self.mapSocket)
        self.mapSocket.close()
        self.inventory=[]
        self.cart=[]
        
    def startScript(self, script):
        script.register(self)
            
        for (packet, handler) in script.handlers():
            self.pm.registerHandler(self.mapSocket, packet, handler)   
            self.scriptInstances.append(script)
            script.start()
        
    def startScripts(self):
        for s in self.scripts:
            s.register(self)
            for (packet, handler) in s.handlers():
                self.pm.registerHandler(self.mapSocket, packet, handler)
            self.scriptInstances.append(s)
            s.start()
                
    def stopScripts(self):
        for k in self.scriptTokens.keys():
            token =self.scriptTokens[k]
            event.removeEvent(token)
            del self.scriptTokens[k]
        
        for s in self.scriptInstances:
            s.stop()
            
    def sendMessage(self, target, message):
    	self.pm.sendMessage(self.mapSocket, target, message);
        
    def sendGlobalMessage(self, username, message):
        self.pm.sendGlobalMessage(self.mapSocket, username, message);
    def openVend(self, vendID):
        self.pm.sendOpenVendor(self.mapSocket, vendID)
    def buyVendor(self, vendor, items):
        self.pm.sendBuyVendor(self.mapSocket, vendor, items)
    def moveToCart(self, index, quantity):
        self.pm.sendMoveToCart(self.mapSocket, index, quantity)    
    def moveToStorage(self, index, quantity):
        self.pm.sendMoveToStorage(self.mapSocket, index, quantity)    
    def getFromCart(self, index, quantity):
        self.pm.sendGetFromCart(self.mapSocket, index, quantity)       
    def openShop(self, title, items):
        self.pm.sendOpenShop(self.mapSocket,  title, items)
    def closeShop(self):
        self.pm.sendCloseShop(self.mapSocket)
    def sendToId(self, id, skill,level):
        self.pm.sendToId(self.mapSocket, id, skill,level);
    def sendAreaSkill(self,skillNum, level, x, y):
        self.pm.sendAreaSkill(self.mapSocket,skillNum, level, x, y)
    def sendEquipItem(self,index, target):
        self.pm.sendEquipItem(self.mapSocket,index, target)
    def sendMove(self, x, y):
    	self.pm.sendMove(self.mapSocket, x, y)
    def sendMapAck(self):
        self.pm.sendMapAck(self.mapSocket)
    def sendMoveToKafra(self, index, quantity):
        self.pm.sendMoveToKafra(self.mapSocket, index, quantity)

    def sendGetInfo(self, id):
    	self.pm.sendGetInfo(self.mapSocket,id)
        
    def sendTradeAck(self, level):
        self.pm.sendTradeAck(self.mapSocket,level)
    def sendTradeOk(self):
        self.pm.sendTradeOk(self.mapSocket)
        
    def sendTradeCommit(self):
        self.pm.sendTradeCommit(self.mapSocket)
    def sendTradeCancel(self):
        self.pm.sendTradeCancel(self.mapSocket)
    def addTradeItem(self, index, amount):
        self.pm.sendAddTradeItem(self.mapSocket, index, amount)
    def sendPartyReply(self, accountId, reply):
        self.pm.sendPartyReply(self.mapSocket, accountId, reply)
