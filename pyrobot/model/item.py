from pyrobot.db import get_db

#Base class of item, just has an id and a name
class Item:
    def __init__(self):
        self.itemId = 0
        self.name = ''
    def __init__(self, itemId):
        itemdb=get_db('items')
        self.itemId = itemId
        self.name = itemdb[str(itemId)][2]
        itemdb.close()

class GameItem(Item):
    def __init__(self):
        super(Item, self).__init__()
        self.index = 0
        self.type = 0
        self.identify = 0
        self.amount = 0
        self.equippoint=0
        self.equip = 0
        self.attribute = 0
        self.card1 = 0
        self.card2 = 0
        self.card3 = 0
        self.card4 = 0
        
    def __init__(self, index, itemId, type, identify, amount, equippoint, equip, attribute, refine, card1, card2, card3, card4):
        super(Item, self).__init__(itemId)
        self.index = index
        self.itemId = itemId
        self.type = type
        self.identify = identify
        self.amount = amount
        self.equippoint = equippoint
        self.equip = equip
        self.attribute = attribute
        self.refine = refine
        self.card1 = card1
        self.card2 = card2
        self.card3 = card3
        self.card4 = card4
        
class PricedItem(Item):
    def __init__(self):
        super(Item, self).__init__()
        self.lowPrice = -1
        self.highPrice = -1
        self.active = False
        self.title = ''
    def __init__(self, itemId, lowPrice, highPrice, active, title):
        super(Item, self).__init__(itemId)
        self.lowPrice = lowPrice
        self.highPrice = highPrice
        self.active = active
        self.title = title
        
    def getAll(self):
        prices=get_db('prices')
        items={}
        for key in prices:
            (itemId,lowPrice, highPrice, active, title) = eval(prices[key])
            newitem = PricedItem(itemId, lowPrice, highPrice, active, title)
            items[key] = newitem
        prices.close()
        return items
    
    def updateAll(self):
        prices = get_db('prices')
        for key in newitems:
            newitem = newitems[key]
            prices[str(key)] = repr((newitem.itemId, newitem.lowPrice, newitem.highPrice, newitem.active, newitem.title))
        prices.sync()
        prices.close()
        
    def addItem(self, itemId, lowPrice, highPrice, active=True, title='' ):
        prices = get_db('prices')
        prices[str(itemId)] = repr((itemId, lowPrice, highPrice, active, title))
        prices.sync()
        prices.close()
        
    def deleteItem(self, itemId):
        prices = get_db('prices')
        if str(itemId) in prices:
            del prices[str(itemId)]
        prices.sync()
        prices.close()

class VendLog(Item):
    def __init__(self):
        super(Item, self).__init__()
        self.type = 0
        self.time = 0
        self.quantity = 0
        self.price = 0
    def __init__(self, itemId, type, time, quantity, price):
        super(Item, self).__init__(itemId)
        self.type = type
        self.time = time
        self.quantity = quantity
        self.price = price
    def getAll(self):    
        venddb = get_db('vendlog')
        logitems=eval(venddb['log'])
        vendlog=[]
        for item in logitems:
            (type, actionTime, itemId, quantity, price) = item
            entry = VendLog(itemId, type, actionTime, quantity, price)
            vendlog.append(entry)
        itemdb.close()
        venddb.close()
        return vendlog
    
class PriceCheck(Item):
    def __init__(self, itemId):
        self.content=[]
        super(Item, self).__init__()
    def __init__(self, itemId, content):
        super(Item, self).__init__(itemId)
        self.content = content
    def getAll(self):
        items={}
        pricecheck = get_db('pricecheck')
        for key in pricecheck:
            content = eval(pricecheck[key])
            pc = PriceCheck(int(key), content)
            items[key] = pc
        pricecheck.close()
        return items
    def updateAll(self,items):
        pricecheck = get_db('pricecheck')
        pricecheck.clear()
        for key in items:
            pc = items[key]
            pricecheck[str(key)] = repr(pc.content)
        pricecheck.sync()
        pricecheck.close()