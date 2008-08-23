import bsddb
import os

def get_db(name):
    if (name.endswith('.db')):
        name= name[:-3]
    db_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)),'db')
    db_file = os.path.join(db_dir,name+'.db')
    return bsddb.hashopen(db_file)
