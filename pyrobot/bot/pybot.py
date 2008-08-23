import logging
import os
import servers
import connection
import event

from pyrobot.bot.script import Script
from ConfigParser import *

log = logging.getLogger(__name__)

scripts={}
bots={}

cel = servers.eternity()

def my_import(name):
    mod = __import__(name)
    components = name.split('.')
    for comp in components[1:]:
        mod = getattr(mod, comp)
    return mod

def load_bots(config_filename):
    """Load the bots defined in the config file
    """

    
    # Find all the bots in the scripts folder
    script_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)),'scripts')
    for script_file in os.listdir(script_dir):
        if not script_file.endswith('.py'):
            continue
        script_name = os.path.splitext(script_file)[0]
        module_name = 'pyrobot.bot.scripts.'+script_name
        module = my_import(module_name)
        
        #Find the scripts in this module
        for name in module.__dict__.keys():
            object = module.__dict__[name]
            if isinstance(object,type(Script)) and object != Script:
                log.info('Loading script: %s', name)
                scripts[name] = object

    #initialize the bots
    config = ConfigParser()
    config.read(config_filename)
    runbots=config.get('pyrobot','run').split(',')
    for botname in runbots:
        usescripts = config.get(botname,'scripts').split(',')
        script_instances=[]
        for name in usescripts:
            scriptmodule = scripts[name]
            script_instances.append( scriptmodule(config.items(botname)))
        username= config.get(botname,'username')
        password= config.get(botname,'password')
        slot=int(config.get(botname,'slot'))
        bots[botname] = connection.Connection(cel, username, password, slot, script_instances)
        #bots[botname].connect()
    event.EventProcessor().start()
        
def getBots():
    return bots

