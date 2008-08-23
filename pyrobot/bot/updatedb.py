import bsddb
import urllib2

idb = bsddb.hashopen('items.db')

dburl = 'http://svn.eathena.ws/svn/ea/trunk/db/item_db.txt'
dbtext = urllib2.urlopen(dburl).read()
dblines = dbtext.split('\n')
dblines = filter(lambda a: not a.startswith('//'), dblines)
    
for k in idb:
    del idb[k]
    
for line in dblines:
    marks = line.split(',')
    if len(marks) > 20:
        itemid = marks[0]
        info = marks[:19]
        idb[itemid] = repr(info)    

idb.sync()
idb.close()
