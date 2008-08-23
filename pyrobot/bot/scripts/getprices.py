import time
import re
import logging
from pyrobot.bot.script import Script
from pyrobot.bot import packet,util
from pyrobot.db import get_db
from pyrobot.model.item import PriceCheck

log = logging.getLogger(__name__)

re1=re.compile('Amount: ([0-9]+) \| Price: ([0-9]+) \| Map: ([a-zA-Z]+)')
re2=re.compile('Found (\d)+ being vended. Range of prices: (\d+) ~ (\d+).')
re3=re.compile('Item not found.')
re4=re.compile('@pc failed.')

class getprices(Script):
    def __init__(self,config):
        self.config = config

    def register(self, client):
        self.client = client
    def handlers(self):
        return [(packet.MESSAGE, self.getMessage)]
    def getMessage(self, message):
        if not (re1.match(message) or re2.match(message) or re3.match(message) or re4.match(message)):
            return
        key = int(self.allKeys[self.currentIndex])
        if key not in self.items:
            self.items[key] = PriceCheck()
        pc = self.items[key]
        pc.content += [message]
        if (re2.match(message) or re3.match(message) or re4.match(message)):
            self.currentIndex+=1
            self.client.addEvent(lambda: self.nextPriceCheck(), 0.1)
        
    def nextPriceCheck(self):
        if (self.currentIndex >= len(self.allKeys)):
            PriceCheck.updateAll(self.items)
            return
            
        key = int(self.allKeys[self.currentIndex])
        log.info('Sending price check for %d',key)
        self.client.sendGlobalMessage(self.client.charname, '@pc %d'%key)
    def start(self):
        self.allKeys=get_db("items").keys()
        print self.allKeys
        self.currentIndex = len(self.allKeys) - 10
        self.items={}
        self.client.addEvent(lambda: self.nextPriceCheck(), 0.25)
    def stop(self):
        pass