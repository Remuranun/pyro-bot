from pyrobot.bot.script import Script
from pyrobot.bot.db import get_db
from pyrobot.bot import packet,util
from pyrobot.model.item import PricedItem
import logging
import random
import time


vends={}

keeplist=[]
uplist=[2322]
refineRate = [1,1,1,1,0.6,0.24,0.096,0.0192,0.00384,0.000384]

log = logging.getLogger(__name__)

class recordPrices(Script):
    def __init__(self,config):      
        self.config = config 
 
    def register(self, server):
        self.server = server
        self.vending={}
        self.vendnames={}
        self.vendRunning = False
        
    def start(self):
        self.server.addEvent(self.waitForItems, 0)
    
    def stop(self):
        if self.vendRunning:
            self.shutDown()
             
    def handlers(self):
        return [(packet.VENDOPENED, self.newVendor), 
                (packet.VENDITEMS,  self.vendOpened), 
                (packet.VENDREPORT, self.vendReport),
                (packet.VENDCONFIRM, self.vendConfirm)]
        
    def newVendor(self, vendID, vendName):
        wait = 20+ random.expovariate(1./20)
        log.info('New vendor: %s waiting %d',vendName, wait)
        self.server.addEvent(lambda : self.server.openVend(vendID), wait)
        self.vendnames[vendID] = vendName

    def sellable(self, lst):
        t=0
        for item in lst:
            if item.itemno in keeplist:
                continue
            item = pricedb.getItem(item.itemno)
            if item.active and item.highPrice <= 0:
                continue
            t+=1
        return t    	

    def moveAllToCart(self):
        num=0
        for item in self.server.inventory[:]:
            num+=1
            self.server.moveToCart(item.index, item.amount)
        log.info('Moved %d items to cart',num)
    def sendStartShop(self):
        log.info("Starting the shop")
        if self.vendRunning == True:
		    return
        toSell = []
        itemvalues = {}

        for cartitem in self.server.cart[:]:
            item = pricedb.getItem(cartitem.itemno)
            if item.itemId in keeplist:
                log.info('Keeping: %s', item.name)
                continue
            if not item.active:
                log.info('Inactive: %d,%s', item.itemId, item.name)
                continue
            log.info('Selling: %s - $%d', item.name , item.highPrice)
            if item.highPrice > 0:
                amount = min (cartitem.amount, int( random.normalvariate(100, 10)))
                expectedRevenue = amount * item.highPrice
                toSell.append([expectedRevenue, item, cartitem, amount])
                if  item.itemId not in itemvalues:
                    itemvalues[item.itemId]= 0
                itemvalues[item.itemId]+=expectedRevenue

        if len(toSell) == 0:
            self.server.addEvent(self.waitForItems, 200);
            return
        
        toSell.sort()
        if len(toSell) > 12:
            toSell = toSell[-12:] 
            
        for [_,item,cartitem,amount] in toSell:
            self.vending[cartitem.index] = [item,cartitem.amount]
            
        toSell.reverse()
        
        shopname=''
        uniquenames=set([])
        for [_,item,cartitem,_] in toSell:
            name = item.title or item.name
            if name.endswith('Card'):
                name=name[:name.rindex(' ')]
            if name not in uniquenames:
                uniquenames.add(name)
                shopname += name + '|'
            
        shopname=shopname[:-1]
        
        if len(shopname) > 70:
            shopname = shopname[:70]
            lastindex = shopname.rindex('|')
            shopname = shopname[:lastindex]

        log.info('Shopname: %s',shopname)
        
        #for the packet, we only need the index, amount, and price
        
        basic=[]
        for [_,item,cartitem,amount] in toSell:
            basic.append((cartitem.index, amount, item.highPrice))
        self.server.addEvent(lambda: self.server.openShop(shopname, basic), 5)
        self.vendRunning = True
               
    def startShop(self):
        self.server.addEvent(self.moveAllToCart, 0)
        self.server.addEvent(self.sendStartShop, 5)
        

    def waitForItems(self):
        numitems = self.sellable(self.server.cart) + self.sellable(self.server.inventory)
        log.info("Sellable items: %d", numitems)
        if numitems >= 2:
            self.server.addEvent(self.startShop, 0)
        else:
            self.server.addEvent(self.waitForItems, 30)
                    
    def vendReport(self, index, quantity):
        vi = self.vending[index]
        vi[1] -= quantity
        
        [item, remaining] = self.vending[index]
        log.info('Sold %s-%d',item.name, quantity)

        self.logSold(item, quantity)
        
        if self.vending[index] == 0:
            del self.vending[index]
            
        numitems = len(self.server.cart) + len(self.server.inventory)
        if len(self.vending.keys()) == 0:
            log.info('Shop Empty, Closing')
            self.shutDown()
            self.server.addEvent(self.waitForItems, 30)
            
        elif len(self.vending.keys()) <= 2 and numitems >= 4:
            log.info('Running Low, Restarting')
            self.server.logger.info('running low, restarting shop');
            self.server.addEvent(lambda: self.shutDown, 10)
            self.server.addEvent(self.startShop, 20)

    def shutDown(self):
        self.server.closeShop()
        self.vendRunning = False
        
    def vendConfirm(self, index, quantity, fail):
        print (index, quantity, fail)

    def buyItem(self, vendID, toBuy):
        if self.vendRunning == True:
            	log.info('Buying Item, Shutting Down')
                self.shutDown()
                self.server.addEvent(self.waitForItems, 300)
        self.server.buyVendor(vendID, toBuy)
        
    def vendOpened(self, vendID, vendItems):
        t=time.gmtime()
        cart = []
        display=[]
        for v in vendItems:
            key = str(v.itemno)
            item = pricedb.getItem(v.itemno)
            display.append([v.itemno, v.amount, v.value])
            if not item.active:
                continue

            if v.value <= item.lowPrice and (v.card1, v.card2, v.card3, v.card4)==(0, 0, 0, 0):
                profit = item.highPrice*v.amount - v.value*v.amount
                if (profit > 100000):
                    cart.append((profit, v))
                elif (v.itemno in keeplist):
		    cart.append((profit, v))
            elif v.refine > 0 and v.itemno in uplist:
	    	goodPrice = item.lowPrice / refineRate[v.refine - 1]
	    	if v.refine < 8 and (v.card1, v.card2, v.card3, v.card4)==(0, 0, 0, 0):
			if v.value <= goodPrice:
				profit = v.value - goodPrice
				cart.append((profit, v))
            elif v.value > item.lowPrice:
                log.info('Bad deal: %s '%str(v))
            
        
        vends[vendID]=(time.time(), repr(self.vendnames[vendID]), display)
        cart.sort()
        cart.reverse()
        #self.server.logger.info('shopping cart: '+str(cart))
        remainingZenny = self.server.zeny
        toBuy=[]
        for (profit, v) in cart:
            quantity = min(v.amount, int(remainingZenny/ v.value))
            if (quantity == 0):
                log.info("Good deal, Can't afford:" + str(v));
            else:
                totalCost = quantity*v.value
                log.info('Good item: ' + str(v))
                self.logBought(v.itemno, quantity, totalCost)
                toBuy.append((v.index, quantity))
                remainingZenny-=totalCost
        if len(toBuy) > 0:
            wait=0.5
            self.server.addEvent(lambda: self.buyItem(vendID, toBuy), wait)
            
    def logBought(self, id, quantity, totalPrice):
        vendlog = get_db('vendlog')
    	if 'log' not in vendlog:
		vendlog['log'] = repr([])
        l = eval(vendlog['log'])
        entry = [0, time.time(), id, quantity, totalPrice]
        l.append(entry)
        vendlog['log'] = repr(l)
	vendlog.sync()
        vendlog.close()
    
    def logSold(self, item, quantity):
        vendlog = get_db('vendlog')
        if 'log' not in vendlog:
            vendlog['log'] = repr([])
        l = eval(vendlog['log'])
        entry = [1, time.time(), item.itemId, quantity, quantity*item.highPrice]
        l.append(entry)
        vendlog['log'] = repr(l)
        vendlog.sync()
        vendlog.close()
    
    def logMissed(self, id, quantity, totalPrice):
        pass
