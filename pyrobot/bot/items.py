import db
import bsddb


itemsdb = db.get_db('items')

class item:
    def __init__(self, index, itemno, type, identify, amount, equippoint, equip, attribute, refine, card1, card2, card3, card4):
        self.index = index
        self.itemno = itemno
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
        
    def __str__(self):
        ret=''
        if self.amount > 1:
            ret+='%d '%self.amount
        else:
            ret+='a '
            
        
        if self.refine > 0:
            ret+='+%d '%self.refine
            
        if self.attribute > 0:
            ret+=' enchanted  '%self.attribute
            
        key =str(self.itemno)
        if key in itemsdb:
            entry=eval(itemsdb[key])
            ret+=entry[1]
        else:
            print 'noid'
            
            ret+=' - $%d  '%self.value
        
        return ret

class venditem:
    def __init__(self, value, amount, index, type, itemno, identify, attribute, refine, card1, card2, card3, card4):
        self.value = value
        self.amount = amount
        self.index = index
        self.type = type
        self.itemno = itemno
        self.identify = identify
        self.attribute = attribute
        self.refine =refine
        self.card1 = card1
        self.card2 = card2
        self.card3 = card3
        self.card4 = card4
        
    def tuple(self):
        return (self.value,self.amount,self.index ,self.type,self.itemno,self.identify,self.attribute, self.refine ,self.card1,self.card2 ,self.card3,self.card4)
    def __str__(self):
        ret='$%d - '%self.value
        if self.amount > 1:
            ret+='%d '%self.amount
        else:
            ret+='a '
            
        
        if self.refine > 0:
            ret+='+%d '%self.refine
            
        #if self.attribute > 0:
        #    ret+=' enchanted  '%self.attribute
            
        key =str(self.itemno)
        if key in itemsdb:
            entry=eval(itemsdb[key])
            ret+=entry[1]
        else:
            print 'item does not exist'
            
            ret+=' - $%d  '%self.value
        
        return ret