"""The application's Globals object"""
from pylons import config
import time
from pyrobot.model.item import PricedItem,VendLog,PriceCheck

class Globals(object):
    """Globals acts as a container for objects available throughout the
    life of the application
    """

    
    def __init__(self):
        """One instance of Globals is created during application
        initialization and is available during requests via the 'g'
        variable
        """
        
        
    def getItems(self):
        return PricedItem.getAll()

    def getPriceChecks(self):
        return PriceCheck.getAll()
    
    def updateItems(self,newItems):
        PricedItem.updateAll(newItems)

    def addItem(self,itemId, lowPrice, highPrice, title):
        PricedItem.addItem(itemId, lowPrice, highPrice, True, title )
        
    def getVendLog(self):
        return VendLog.getAll()
