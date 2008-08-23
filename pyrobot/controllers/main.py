import logging
import re

from pyrobot.lib.base import *
from pyrobot.model.item import PricedItem

log = logging.getLogger(__name__)

def item_compare(a,b):
    return a.itemId - b.itemId
    
class MainController(BaseController):

    def getItem(index):
        return items[index]
    def index(self):
        return render('/index.mako')
    
    def prices(self):
        items = g.getItems()
        pricechecks = g.getPriceChecks()
        itemlist = []
        for key in items:
            itemlist.append(items[key])
            
        itemlist.sort(item_compare)
        c.itemlist = itemlist
        c.pricechecks = pricechecks
        return render('/prices.mako')
    
    def update(self):
        newprices = {}
        dsp = re.compile('([0-9]+)_([a-z]+)')
        for key in request.POST:
            groups = dsp.findall(key)
            if len(dsp.findall(key)) == 0:
                continue
            
            group = groups[0]
            (itemId,type,value) = int(group[0]),group[1],request.POST[key]
            if itemId not in newprices:
                newitem=PriceItem()
                newitem.itemId = itemId
                newitem.active = False
                newitem.title=''
                newprices[itemId]=newitem
            item = newprices[itemId]
            
            if (type == 'low'):
                item.lowPrice = int(value)
            elif (type == 'high'):
                item.highPrice = int(value)
            elif (type == 'active'):
                item.active = (value == 'on')
            elif (type == 'title'):
                item.title = value.encode('ascii')
        g.updateItems(newprices)
        redirect_to("/prices")
        
    def add(self):
        newprices = {}
        dsp = re.compile('([0-9]+)_([a-z]+)')
        itemId = int(request.POST["itemId"])
        lowPrice = int(request.POST["lowPrice"])
        highPrice = int(request.POST["highPrice"])
        title = request.POST["title"].encode('ascii')
        g.addItem(itemId, lowPrice, highPrice,title)
        redirect_to("/prices")
        
    def log(self):
        c.vendlog = g.getVendLog()
        return render('/vendlog.mako')

    def control(self):
        botname = request.POST['botname']
        if 'start' in request.POST:
            h.getBots()[botname].connect()
        elif 'stop' in request.POST:
             h.getBots()[botname].disconnect()
        redirect_to("/")
        
    def pricechecks(self):
        items = g.getItems()
        c.pricechecks = g.getPriceChecks()
        return render('/pricechecks.mako')
