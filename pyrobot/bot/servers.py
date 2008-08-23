import packetmanager

class server:
    def accountServer(self):
        abstract

    def charServer(self):
        abstract    

    def mapServer(self):
        abstract    
        
    def packetManager(self):
        abstract        
	
class eternity(server):
    ip = '208.43.73.90'
    pm = packetmanager.eternityPacketManager()
    def accountServer(self):
        return ((self.ip,6025))
    
    def charServer(self):
        return ((self.ip,6185))

    def mapServer(self):
        return  ((self.ip,5193))
        
    def packetManager(self):
        return self.pm