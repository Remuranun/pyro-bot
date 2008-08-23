import socket
import struct
import time
import threading
import util
import items
import event
import md5
import logging

log = logging.getLogger(__name__)

class eternityPacketManager:
    
    connections={}
    eventHandlers={}
    packetHandlers={}
    socketData={}

    
    def __init__(self):
        self.packetHandlers['\x33\x01'] = self.getVendItems2
        self.packetHandlers['\x31\x01'] = self.getVendTitle
        self.packetHandlers['\xb1\x00'] = self.getProperty2
        self.packetHandlers['\xb0\x00'] = self.getProperty
        self.packetHandlers['\x25\x01'] = self.cartDelItem
        self.packetHandlers['\xaf\x00'] = self.delItem
        self.packetHandlers['\x24\x01'] = self.newCartItem
        self.packetHandlers['\xa0\x00'] = self.newInventoryItem
        #self.packetHandlers['\x22\x01'] = self.newCartEquip
        self.packetHandlers['\xee\x01'] = self.getItemList
        self.packetHandlers['\xa4\x00'] = self.getEquipList
        self.packetHandlers['\xef\x01'] = self.getCartItemList
        self.packetHandlers['\x22\x01'] = self.getCartEquipList
        self.packetHandlers['\x37\x01'] = self.getVendReport
        self.packetHandlers['\x35\x01'] = self.getVendConfirm
        self.packetHandlers['\x8d\x00'] = self.getGlobalMessage
        self.packetHandlers['\x8e\x00'] = self.getMessage
        self.packetHandlers['\x97\x00'] = self.getPrivMessage
        self.packetHandlers['\x7f\x01'] = self.getGuildMessage
        self.packetHandlers['\x95\x01'] = self.getCharInfo
        self.packetHandlers['\x95\x00'] = self.getCharName
        self.packetHandlers['\x2a\x02'] = self.getCharArea
        self.packetHandlers['\x2c\x02'] = self.getCharMove
        self.packetHandlers['\x3e\x01'] = self.getSkillCast
        self.packetHandlers['\x06\x01'] = self.partyHP
        self.packetHandlers['\x91\x00'] = self.changeMap
        self.packetHandlers['\x0f\x01'] = self.skillInfoBlock
        self.packetHandlers['\xe9\x01'] = self.partyMemberInfo
        self.packetHandlers['\xfb\x00'] = self.partyInfo
        self.packetHandlers['\x96\x01'] = self.statusLoad
        self.packetHandlers['\x29\x02'] = self.changeOption
        self.packetHandlers['\x09\x01'] = self.partyMessage
        self.packetHandlers['\x17\x01'] = self.poseEffect
        self.packetHandlers['\x1a\x01'] = self.noDamage
        self.packetHandlers['\x9e\x00'] = self.itemDrop
        self.packetHandlers['\xc8\x01'] = self.useItemAck
        self.packetHandlers['\x73\x00'] = self.authOk
        self.packetHandlers['\x87\x00'] = self.walkOk
        self.packetHandlers['\x86\x00'] = self.move
        self.packetHandlers['\xf4\x01'] = self.traderequest
        self.packetHandlers['\xf5\x01'] = self.tradestart
        self.packetHandlers['\xea\x00'] = self.tradeok
        self.packetHandlers['\xec\x00'] = self.tradelock
        self.packetHandlers['\xfe\x00'] = self.partyinvite
        
    def connect(self, connection):
        accountsocket=socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        accountsocket.connect(connection.server.accountServer());
        md5obj = md5.new()
        md5obj.update(connection.password)
        md5sum=md5obj.digest()
        prefix='\xdd\x01\x8c\xa9\x00\x00'        
        packet=prefix + struct.pack("24s16sb", connection.username, md5sum, 0x10)
        
        accountsocket.send(packet);
        accountsocket.setblocking(1)
        
        def loginParser(socket):
            data = socket.recv(1024)
            (header,) = struct.unpack('H', data[0:2])
            if header == 0x6a:
                log.info("Rejected from server")
                return
            elif header == 0x69:
                (length,) = struct.unpack('H', data[2:4])
                numServers = (length-47)/32
                connection.accountID =data[8:12];
                connection.sessionID1=data[4:8];
                connection.sessionID2=data[12:16];
                log.info("AccountId: %s SessionId1: %s SessionId2 %s", connection.accountID, connection.sessionID1, connection.sessionID2)
                connection.sex = data[46]
                socket.close()
                event.removeSocket(socket)
                event.addEvent(lambda: self.charLogin(connection), 0)
        
        #add the login socket to the event manager
        event.addSocket(accountsocket, loginParser)
        

    def charLogin(self, conn):
        log.info("Logging in %s", conn.username)
        charsocket=socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        charsocket.connect(conn.server.charServer());
        
        packet=struct.pack("bx4s4s4sxxc", 0x65, conn.accountID, conn.sessionID1, conn.sessionID2, conn.sex);
        print len(packet), util.toHex(packet)
        
        charsocket.send(packet);
        charsocket.setblocking(1)
        
        def charParser(socket):
            data = socket.recv(1024)
            print len(data)
            if len(data) < 4:
                log.error("Char login bad error")
                return
            if data.startswith(conn.accountID):
                data = data[4:]
                if len(data) == 0:
                    return
            
            (header,) = struct.unpack('H', data[0:2])
            if header == 0x6c:
                log.error("Char login denied")
                return
            elif header == 0x81:
                log.error("Already logged in")
                return
            elif header == 0x71:
                mapname = data[6:22].split('\x00\x00')[0]
                conn.mapname = mapname
                socket.close()
                event.removeSocket(socket)
                event.addEvent(lambda: self.mapConnect(conn), 0)
            elif header == 0x6b:
                (length,) = struct.unpack('H', data[2:4])
                if (length - 24) % 108 == 0:
                    charlen = 108
                elif (length - 24) % 106 == 0:
                    charlen = 106
                    
                numChars = (length - 24) / charlen
                
                log.info("Number of characters: %d",numChars)
                
                for i in range(0, numChars):
                    offset = 24 + i * charlen
                    res = struct.unpack('IIIIIIIIIIHHHHHHHHHHHHHHHHH24sBBBBBBH', data[offset:offset+106])
                    if conn.slot == res[34]:
                        conn.charID = res[0]
                        log.info('CharId: %s', util.toHex(struct.pack('I', conn.charID)))
                        conn.baseExp = res[1]
                        conn.zeny = res[2]
                        conn.jobExp = res[3]
                        conn.jobLevel = res[4]
                        conn.hp = res[11]
                        conn.maxhp = res[12]
                        conn.sp = res[13]
                        conn.maxsp = res[14]
                        conn.charname = res[27].split('\x00')[0]
                        socket.send('\x87\x01' + conn.accountID);
                        socket.send(struct.pack('bxb', 0x66, conn.slot));

        event.addSocket(charsocket, charParser)

    def mapConnect(self, conn):
        mapsocket=socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        mapsocket.connect(conn.server.mapServer());

        packet='\x9b\x00\x37\x00' + struct.pack('4s', conn.accountID) + '\x00' + struct.pack('I', conn.charID) + '\x65\x32\x39\x00' + struct.pack('4s', conn.sessionID1) + struct.pack('4s', util.getTickCount(3)) + conn.sex
        

        mapsocket.send(packet)

        mapsocket.setblocking(1)
        def initialHandler(socket):
            header = socket.recv(2)
            if header == '\x83\x02':
                #Eat the account ID
                data = socket.recv(4)
                event.setSocketHandler(socket, self.receiveData)
                conn.mapSocket = socket
                conn.addEvent(lambda: self.syncLoop(conn), 0)
                self.connections[socket] = conn
                self.sendMapAck(socket)
                self.eventHandlers[socket] = {}
                conn.startScripts()
            else:
                header = struct.unpack('H', data[0:2])
                socket.close()
                event.removeSocket(socket)
                return
        
        event.addSocket(mapsocket, initialHandler)
        

    def registerHandler(self, mapSocket, packet, handler):
        if packet not in self.eventHandlers[mapSocket]:
            self.eventHandlers[mapSocket][packet]=[]
        self.eventHandlers[mapSocket][packet].append(handler)
        
    def syncLoop(self, conn):
        self.sendSync(conn)
        conn.addEvent(lambda: self.syncLoop(conn), 12.0)
        
    def sendSync(self, conn):
        packet='\x89\x00\x33\x00'+util.getTickCount(4)
        conn.mapSocket.send(packet);                

        
    def receiveData(self, socket):
        if socket not in self.socketData:
            self.socketData[socket]=''
        data = socket.recv(1024)
        self.socketData[socket]+=data
        self.parsePackets(socket)
    
    def parsePackets(self, socket):
        gamedata = self.socketData[socket]
        if len(gamedata) < 2:
            return
        
        
        conn = self.connections[socket] 
        header=gamedata[0:2];
        num=struct.unpack('H', header)[0];
        length=packetLengths[num];
        dataLength=len(gamedata);

        if length==-1:
            if dataLength < 4:
                return
        
            length=struct.unpack('H', gamedata[2:4])[0];
    
        if length > dataLength:
            #we don't have enough data for this packet
            return
        scriptHandlers=self.eventHandlers[socket]
        packetdata = gamedata[0:length]

        if (header in self.packetHandlers):
            handlers=[]
            if header in scriptHandlers:
                handlers=scriptHandlers[header]
            self.packetHandlers[header](gamedata[0:length], conn, handlers)

        self.socketData[socket] = gamedata[length:]
    
        self.parsePackets(socket)
        
    def getItemList(self, gamedata, connection, handler):
        len=struct.unpack('H', gamedata[2:4])[0];
        numitems=(len-4)/18
        
        for n in range(numitems):
            data=gamedata[4+18*n: 22+18*n];            
            (index, itemno, type, identify, amount, equip, card0, card1, card2, card3)=struct.unpack('HHBBHHHHHH', data);
            new=items.item(index, itemno, type, identify, amount, 0, equip, 0, 0, card0, card1, card2, card3);
            connection.inventory.append(new)


    def getEquipList(self, gamedata, connection, handler):
        len=struct.unpack('H', gamedata[2:4])[0];
        numitems=(len-4)/20

        for n in range(numitems):
            data=gamedata[4+20*n: 24+20*n];    
            (index, itemno, type, identify, equippoint, equip, attribute, refine, card0, card1, card2, card3)=struct.unpack('HHBBHHBBHHHH', data);
              
            new=items.item(index, itemno, type, identify, 1, equippoint, equip, attribute, refine, card0, card1, card2, card3);
            connection.inventory.append(new)
            
    def getCartItemList(self, gamedata, connection, handler):
        len=struct.unpack('H', gamedata[2:4])[0];
        numitems=(len-4)/18
 
        for n in range(numitems):
            data=gamedata[4+18*n: 22+18*n];            
            (index, itemno, type, identify, amount, equip, card0, card1, card2, card3)=struct.unpack('HHBBHHHHHH', data);
            new=items.item(index, itemno, type, identify, amount, 0, equip, 0, 0, card0, card1, card2, card3);
            connection.cart.append(new)


    def getCartEquipList(self, gamedata, connection, handler):
        len=struct.unpack('H', gamedata[2:4])[0];
        numitems=(len-4)/20
 
        for n in range(numitems):
            data=gamedata[4+20*n: 24+20*n];  
            (index, itemno, type, identify, equip, cartequip, attribute, refine, card0, card1, card2, card3)=struct.unpack('HHBBHHBBHHHH', data)
                     
            new=items.item(index, itemno, type, identify, 1, cartequip, equip, attribute, refine, card0, card1, card2, card3);
            connection.cart.append(new)
            
    def newInventoryItem(self, gamedata, connection, handler):
        (index, amount, itemno, identify, attribute, refine) = struct.unpack('HHHBBB', gamedata[2:11])
        
        (card0, card1, card2, card3, equippoint, type, fail)=struct.unpack('HHHHHBB', gamedata[11:])
        new=items.item(index, itemno, type, identify, amount, equippoint, 0, attribute, refine, card0, card1, card2, card3);
        
        connection.inventory.append(new)


    def newCartItem(self, gamedata, connection, handler):
        (index,) = struct.unpack('H', gamedata[2:4]) 
        (amount, itemno, identify, attribute, refine) = struct.unpack('IHBBB', gamedata[4:13]) 
        (card0, card1, card2, card3) = struct.unpack('HHHH', gamedata[13:]) 
        new=items.item(index, itemno, type, identify, amount, 0, 0, attribute, refine, card0, card1, card2, card3);
        
        connection.cart.append(new)
        
    def cartDelItem(self, gamedata, connection, handler):
                
        
        newCart=[]
        (packet, index, amount) =struct.unpack('HHI', gamedata)
        for item in connection.cart:
            if item.index != index:
                newCart.append(item)
            else:
                if amount < item.amount:
                    item.amount -= amount
                    newCart.append(item)
        connection.cart = newCart
        #new=items.item(index, itemno, type, identify, amount, equippoint, 0, attribute, refine, card0, card1, card2, card3);
        
        
    def delItem(self, gamedata, connection, handler):
                
        
        (index, amount) =struct.unpack('HH', gamedata[2:])
        connection.inventory= filter (lambda item: item.index != index, connection.inventory)
        #new=items.item(index, itemno, type, identify, amount, equippoint, 0, attribute, refine, card0, card1, card2, card3);
        
    def getVendItems2(self, gamedata, connection, handler):
        (len, vendID)=struct.unpack('H4s', gamedata[2:8]);
        numitems = (len-8)/22;
        venditems=[]
        for i in range(numitems):
            start=8+i*22
            (price, quantity, index, type) =  struct.unpack('ihhb', gamedata[start:start+9])
            (cart, identify, attribute, refine) = struct.unpack('Hbbb', gamedata[start+9:start+14])
            (card1, card2, card3, card4) =  struct.unpack('hhhh', gamedata[start+14:start+22])
            ni=items.venditem(price, quantity, index, type, cart, identify, attribute, refine, card1, card2, card3, card4)
            venditems.append(ni)
        for h in handler:
            h(vendID, venditems)      

    def getVendTitle(self, gamedata, connection, handler):
        vendId=gamedata[2:6]
        #I honestly don't give a crap about the name....
        vendName=gamedata[6:]
        vendName=vendName[0:vendName.index('\x00')];
        for h in handler:
            h(vendId, vendName)        
        
    def getProperty2(self, gamedata, connection, handler):
        (header, property, value)=struct.unpack('HHI', gamedata[0:8]);
        if property==20:
            log.info('zeny went from %d->%d (%d)',connection.zeny, value, (value - connection.zeny))
            connection.zeny = value
            
        for h in handler:
            h(property, value)
    def getProperty(self, gamedata, connection, handler):
        (header, property, value)=struct.unpack('HHI', gamedata[0:8]);
        if property == 24:
            connection.weight = value
        elif property == 25:
            connection.maxweight = value
        elif property == 7:
            connection.sp = value
        elif property == 8:
            connection.maxsp = value
        elif property == 5:
            connection.hp = value
        elif property == 6:
            connection.maxhp = value
            
        for h in handler:
            h(property, value)

    def getVendReport(self, gamedata, connection, handler):
        (index, quantity)=struct.unpack('HH', gamedata[2:6])
        for h in handler:
            h(index, quantity)
        
    def getVendConfirm(self, gamedata, connection, handler):
        (index, quantity, fail)=struct.unpack('HHB', gamedata[2:7])
        for h in handler:
            h(index, quantity, fail)
         
    def getGlobalMessage(self, gamedata, connection, handler):
        len=struct.unpack('H', gamedata[2:4])[0];
        #log.info('Global message: %s',gamedata[8:len])


    def getMessage(self, gamedata, connection, handler):
        len=struct.unpack('H', gamedata[2:4])[0]
        #ignore the null character at the end
        message = gamedata[4:len-1]
        #log.info('Message: %s',message)
        for h in handler:
            h(message)
            
    def getPrivMessage(self, gamedata, connection, handler):
        (l, f)=struct.unpack('H24s', gamedata[2:28]);
        msg = gamedata[28:]
        #log.info('(From %s): %s',f, msg)
        for h in handler:
            h(f, msg)

    def getGuildMessage(self, gamedata, connection, handler):
        len=struct.unpack('H', gamedata[2:4])[0];
        #log.info('Guild message: %s',gamedata[4:len])

    def partyMessage(self, gamedata, connection, handler):
        (len, accountID) = struct.unpack('H4s', gamedata[2:8]);
        message = gamedata[8:len]

        for h in handler:
            h(accountID, message)

    def poseEffect(self, gamedata, connection, handler):
        (sid, id, val, x, y) = struct.unpack('H4sHHH', gamedata[2:14])
        for h in handler:
            h(sid, id, val, x, y)
    def noDamage(self, gamedata, connection, handler):
        (sid, heal, dstid, srcid, fail) = struct.unpack('HH4s4sB', gamedata[2:15])
        for h in handler:
            h(sid, heal, dstid, srcid, fail)
    def itemDrop(self, gamedata, connection, handler):
        (id, nameid, identify) = struct.unpack('IHB', gamedata[2:9])
        (x, y, sx, xy, amount) = struct.unpack('HHBBH', gamedata[9:])
        for h in handler:
            h(id, nameid, identify, x, y, sx, xy, amount)

    def useItemAck(self, gamedata, connection, handler):
        (index, itemid, id, amount, ok) = struct.unpack('HH4sHB', gamedata[2:])
        for h in handler:
            h(index, itemid, id, amount, ok)

    def authOk(self, gamedata, connection, handler):
        (b0, b1, b2) = struct.unpack('BBB', gamedata[6:9])
        x, y= util.getPos(b0, b1, b2)
        connection.x = x
        connection.y = y
        for h in handler:
            h(x, y)

    def walkOk(self, gamedata, connection, handler):    
        (b0, b1, b2, b3, b4, b5) = struct.unpack('BBBBBB', gamedata[6:12])
        (x0, y0, x1, y1) = util.getPos2(b0, b1, b2, b3, b4, b5)
        (connection.x, connection.y) = x0, y0
        for h in handler:
            h(x0, y0, x1, y1)
            
    def move(self, gamedata, connection, handler):    
        (charId,b0, b1, b2, b3, b4, b5) = struct.unpack('4sBBBBBB', gamedata[2:12])
        (x0, y0, x1, y1) = util.getPos2(b0, b1, b2, b3, b4, b5)
        (connection.x, connection.y) = x0, y0
        for h in handler:
            h(charId,x0, y0, x1, y1)

    def getCharInfo(self, gamedata, connection, handler):
        (i, name, party, gname, gid)=struct.unpack('4s24s24s24s24s', gamedata[2:])
        for h in handler:
            h(i, name.strip(), party.strip(), gname.strip(), gid.strip())

    def getCharName(self, gamedata, connection, handler):
        (i, name)=struct.unpack('4s24s', gamedata[2:])
        for h in handler:
            h(i, name.strip())

    def getCharMove(self, gamedata, connection, handler):
        (i,) = struct.unpack('4s', gamedata[2:6])	
        (b0, b1, b2, b3, b4, b5) = struct.unpack('BBBBBB', gamedata[54:60])	
        x0 = (b0 << 2) + (b1 >> 6) 
        y0 = ((b1 & 0x3f) << 4) + (b2 >> 4)
        x1 = ((b2 & 0xf) << 6) + (b3 >> 2)
        y1 = ((b3 & 0x03) << 8) + b4
        for h in handler:
            h(i, x0, y0, x1, y1)

    def getCharArea(self, gamedata, connection, handler):
        (i,) = struct.unpack('4s', gamedata[2:6])    
        (b0, b1, b2) = struct.unpack('BBB', gamedata[50:53])
        x = (b0 << 2) + (b1 >> 6)
        y = ((b1&0x3f)<<4) + (b2 >> 4)
        for h in handler:
            h(i, x, y)
        

    def getSkillCast(self, gamedata, connection, handler):
        (srcid, dstid, dstx, dsty, skill) = struct.unpack('4s4sHHH', gamedata[2:16])	
        (pl, casttime) = struct.unpack('II', gamedata[16:])	
        for h in handler:
            h(srcid, dstid, dstx, dsty, skill, pl, casttime)

    def changeMap(self, gamedata, connection, handler):
        (name, x, y) = struct.unpack('16sHH', gamedata[2:])
        name = name.split('\x00')[0]
        connection.mapname = name
        connection.x = x
        connection.y = y
        for h in handler:
            h(name, x, y)

    def skillInfoBlock(self, gamedata, connection, handler):
        (l,) = struct.unpack('H', gamedata[2:4])
        numskills = (l - 4)/37
        skillList=[]

        for n in range(0, numskills):
            base = 4 + n * 37
            info = struct.unpack('HHHHHH24sB', gamedata[base:base+37])
            skillName = info[6].split('\x00')[0]
            skillList.append((info[0], info[1], info[2], info[3], info[4], info[5], skillName))
        for h in handler:
            h(skillList)
    	

    def partyMemberInfo(self, gamedata, connection, handler):
        info = struct.unpack('4s4sHHB24s24s16sBB', gamedata[2:])
        return

    def partyInfo(self, gamedata, connection, handler):
        (l,) = struct.unpack('H', gamedata[2:4])
        numMembers = (l - 28)/46
        memberList=[]
        
        partyMembers = connection.partyMembers
        for n in range(0, numMembers):
            base = 28 + n * 46
            info = struct.unpack('4s24s16sBB', gamedata[base:base+46])
            member = (info[0], info[1].split('\x00')[0], info[2], info[3], info[4])
            partyMembers.append(member)
            memberList.append(member)
    
        for h in handler:
            h(memberList)
            
    def statusLoad(self, gamedata, connection, handler):
        (type, id, flag) = struct.unpack('H4sB', gamedata[2:])
        for h in handler:
            h(type, id, flag)

    def changeOption(self, gamedata, connection, handler):
        (id, opt1, opt2, option, pk) = struct.unpack('4sHHIB', gamedata[2:])
        for h in handler:
            h(id, opt1, opt2, option)
            
    def partyHP(self, gamedata, connection, handler):
        (srcid, hp, maxhp) = struct.unpack('4sHH', gamedata[2:])	
        for h in handler:
            h(srcid, hp, maxhp)
            
    def traderequest(self, gamedata, connection, handler):
        (name, charId) = struct.unpack('24sI', gamedata[2:30]) 
        for h in handler:
            h(name, charId)   
    def tradestart(self, gamedata, connection, handler):
        (type,) = struct.unpack('B', gamedata[2:3]) 
        (charId,) = struct.unpack('I', gamedata[3:7]) 
        for h in handler:
            h(type, charId)   
    
    def tradeok(self, gamedata, connection, handler):
        pass
    
    def tradelock(self, gamedata, connection, handler):
        for h in handler:
            h()   
            
    def partyinvite(self, gamedata, connection, handler):
        (accountId, name) = struct.unpack('4s24s',gamedata[2:])
        for h in handler:
            h(accountId, name)   
    

    def sendGetInfo(self, gamesocket, id):
    	packet='\x8c\x00\x34\x63\x64\x30\x00'+id
        gamesocket.send(packet)

    def sendMapAck(self, gamesocket):
        packet='\x1d\x02\x00\x00\x00\x00';
        gamesocket.send(packet)
        packet='\x7d\x00'
        gamesocket.send(packet)

    def sendMoveToKafra(self, gamesocket, index, quantity):
        packet='\x94\x00' + util.pad(3) + util.packWord(index) + util.pad(12) +util.packWord(quantity)+ util.pad(2)
        gamesocket.send(packet)


    def sendMove(self, gamesocket, x, y):
        b0 = 0xFF & (x >> 2);
        b1 = 0xFF & ((x << 6) | (y >> 4)&0x3f)
        b2 = 0xFF & (y << 4)  
        packet = '\xA7\x00\x30\x63\x00'+struct.pack('BBB', b0, b1, b2)
        gamesocket.send(packet)

    def sendAreaSkill(self, gamesocket, skillNum, level, x, y):
        #packet=struct.pack('2s9xH5xH2x4s', '\x72\x00', level, skillNum, targetID)
        packet='\x13\x01'+util.pad(3)+util.packWord(level) + util.pad(8) + util.packWord(skillNum) + util.pad(12) + util.packWord(x) + util.pad(7) + util.packWord(y)
        
        gamesocket.send(packet)
    def sendEquipItem(self, gamesocket, index, target):
        packet=struct.pack('2sHH', '\xa9\x00', index, target)
        #packet='\x72\x00\x35\x39\x35\x63\x65\x30\x31\x35\x00\x0A\x00\x31\x61\x30\x33\x00\x1C\x00\x39\x00'+id
        gamesocket.send(packet)
        
    def sendToId(self, gamesocket, id, skill, level):
        packet='\x72\x00\x33\x62\x33\x00'+struct.pack('H',level)+'\x63\x00'+struct.pack('H',skill)+'\x33\x31\x32\x30\x63\x33\x61\x33\x00'+id
        gamesocket.send(packet)

    def sendOpenVendor(self, gamesocket, vendor):
        packet=struct.pack('BB4s', 0x30, 0x01, vendor);
        gamesocket.send(packet);
        
    def sendMessage(self, gamesocket, target, message):
        length = 28 + len(message) + 1
        packet = struct.pack('HH24s', 0x96, length, target) + message + '\x00'
        gamesocket.send(packet)
        
      
    def sendGlobalMessage(self, gamesocket, charname, message):
        packet=struct.pack('BxH', 0xf3, len(charname)+len(message)+8);
        packet=packet+charname+' : '+message+'\x00';
        gamesocket.send(packet);
  
    def sendBuyVendor(self, gamesocket, vendor, items):
        header=struct.pack('BBH', 0x34, 0x01, 8+len(items)*4);
        packet=struct.pack('4s4s', header, vendor);
        for (index, quantity) in items:
            packet = packet+struct.pack('HH', quantity , index);
        gamesocket.send(packet);
        
    def sendMoveToCart(self, gamesocket, index, quantity):
        packet=struct.pack('BBHI', 0x26, 0x01, index, quantity);
        gamesocket.send(packet);
        
    def sendMoveToStorage(self, gamesocket, index, quantity):
        packet=struct.pack('BB5x',0x94, 0x00,)+struct.pack('H', index)+'\x00' + struct.pack('I',quantity);
        gamesocket.send(packet);
    
    def sendGetFromCart(self, gamesocket, index, quantity):
        packet=struct.pack('BBHI', 0x27, 0x01, index, quantity);
        gamesocket.send(packet);
    
    def sendOpenShop(self, gamesocket, title, items):
        conn = self.connections[gamesocket]
        length=0x55+8*len(items)
        packet=struct.pack('BBH80sB', 0xb2, 0x01, length, title, 0x01);
        for (index, quantity, price) in items:
            packet=packet+struct.pack('HHI', index, quantity, price);

        conn.addEvent(lambda: self.sendToId(gamesocket,conn.accountID, 0x29,10), 1.0);
        conn.addEvent(lambda: gamesocket.send(packet), 5.0);
        
    def sendCloseShop(self, gamesocket):
        packet='\x2e\x01'
        gamesocket.send(packet);
        
    def sendTradeAck(self, gamesocket, level):
        packet='\xe6\x00'+struct.pack('b',level)
        gamesocket.send(packet)
    def sendAddTradeItem(self, gamesocket, index, amount):
        packet='\xe8\x00'+struct.pack('H',index) + struct.pack('I',amount)
        gamesocket.send(packet)
        
    def sendTradeCancel(self,gamesocket):
        packet='\xed\x00'
        gamesocket.send(packet)
        
    def sendTradeOk(self,gamesocket):
        packet='\xeb\x00'
        gamesocket.send(packet)
        
    def sendTradeCommit(self,gamesocket):
        packet='\xef\x00'
        gamesocket.send(packet)
    
    def sendPartyReply(self, gamesocket,accountID, reply):
        packet='\xc7\x02' + accountID + struct.pack('B',reply)
        gamesocket.send(packet)
        
    def sendQuitGame(self, gamesocket):
        packet='\x8a\x01\x00\x00'
        gamesocket.send(packet)

packetLengths = [
 10, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
  0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
  0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
  0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
  0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
 55, 17, 3, 37, 46, -1, 23, -1, 3, 108, 3, 2, 3, 28, 19, 11, 3, -1, 9, 5,
 55, 53, 58, 60, 42, 2, 6, 6, 7, 3, 2, 2, 2, 5, 16, 12, 10, 7, 29, 2,
 -1, -1, -1, 0, 7, 22, 28, 2, 6, 30, -1, -1, 3, -1, -1, 5, 9, 17, 17, 6,
 23, 6, 6, -1, -1, -1, -1, 8, 7, 6, 7, 4, 7, 0, -1, 6, 8, 8, 3, 3,
 -1, 6, 6, -1, 7, 6, 2, 5, 6, 44, 5, 3, 7, 2, 6, 8, 6, 7, -1, -1,
 -1, -1, 3, 3, 6, 3, 2, 27, 3, 4, 4, 2, -1, -1, 3, -1, 6, 14, 3, -1,
 28, 29, -1, -1, 30, 30, 26, 2, 6, 26, 3, 3, 8, 19, 5, 2, 3, 2, 2, 2,
  3, 2, 6, 8, 21, 8, 8, 2, 2, 26, 3, -1, 6, 27, 30, 10, 2, 6, 6, 30,
 79, 31, 10, 10, -1, -1, 4, 6, 6, 2, 11, -1, 10, 39, 4, 10, 31, 35, 10, 18,
  2, 13, 15, 20, 68, 2, 3, 16, 6, 14, -1, -1, 21, 8, 8, 8, 8, 8, 2, 2,
  3, 4, 2, -1, 6, 86, 6, -1, -1, 7, -1, 6, 3, 16, 4, 4, 4, 6, 24, 26,
 22, 14, 6, 10, 23, 19, 6, 39, 8, 9, 6, 27, -1, 2, 6, 6, 110, 6, -1, -1,
 -1, -1, -1, 6, -1, 54, 66, 54, 90, 42, 6, 42, -1, -1, -1, -1, -1, 30, -1, 3,
 14, 3, 30, 10, 43, 14, 186, 182, 14, 30, 10, 3, -1, 6, 106, -1, 4, 5, 4, -1,
  6, 7, -1, -1, 6, 3, 106, 10, 10, 34, 0, 6, 8, 4, 4, 4, 29, -1, 10, 6,
 90, 86, 24, 6, 30, 102, 9, 4, 8, 4, 14, 10, -1, 6, 2, 6, 3, 3, 35, 5,
 11, 26, -1, 4, 4, 6, 10, 12, 6, -1, 4, 4, 11, 7, -1, 67, 12, 18, 114, 6,
  3, 6, 26, 26, 26, 26, 2, 3, 2, 14, 10, -1, 22, 22, 4, 2, 13, 97, 3, 9,
  9, 30, 6, 28, 8, 14, 10, 35, 6, -1, 4, 11, 54, 53, 60, 2, -1, 47, 33, 6,
 30, 8, 34, 14, 2, 6, 26, 2, 28, 81, 6, 10, 26, 2, -1, -1, -1, -1, 20, 10,
 32, 9, 34, 14, 2, 6, 48, 56, -1, 4, 5, 10, 26, -1, 26, 10, 18, 26, 11, 34,
 14, 36, 10, 0, 0, -1, 32, 10, 22, 0, 26, 26, 42, 6, 6, 2, 2, 282, 282, 10,
 10, -1, -1, 66, 10, -1, -1, 8, 10, 2, 282, 18, 18, 15, 58, 57, 65, 5, 71, 5,
 12, 26, 9, 11, -1, -1, 10, 2, 282, 11, 4, 36, -1, -1, 4, 2, -1, -1, -1, -1,
 -1, 3, 4, 8, -1, 3, 70, 4, 8, 12, 4, 10, 3, 32, -1, 3, 3, 5, 5, 8,
  2, 3, -1, -1, 4, -1, 4, 0, 6, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
  0, 0, 0, 0, 0, 0, 0, 0, 8, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
  0, 0, 0, 6, 0, 0, 0, 0, 0, 8, 18, 0, 0, 0, 0, 0, 0, 4, 0, 0,
  0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
  0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 191, 0, 0,
  0, 0, 0, 0, 0, 0, 0, 0, 0, 30, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
  0, 0, 0, 0, 0, 0, 6, -1, 10, 10, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
  0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]

  
