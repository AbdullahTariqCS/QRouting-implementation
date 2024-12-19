from enum import IntEnum
class Priority(IntEnum): 
    LOW = 2
    MEDIUM = 1
    HIGH = 0

class Packet: 
    def __init__(self, name, plen, broadcast, priority, nextHop = ''): 
        self.name = name
        self.plen = plen
        self.nextHop = nextHop
        self.broadcast = broadcast
        self.priority = int(priority)
    
    def addRouting(self, srcIp, nextHopIp): 
        self.nextHop = nextHopIp
        self.srcIp = srcIp
    
    def __lt__(self, other:'Packet'): 
        self.priority < other.priority

class DataPacket(Packet): 
    def __init__(self, name, srcPort, destPort, destIp, timeSent, plen, checksum=None): 
        super().__init__(name=name, plen=plen, broadcast = False, priority=Priority.LOW)

        #upd header
        self.srcPort = srcPort
        self.destPort = destPort
        self.checksum = checksum
        self.destIp = destIp
        self.timeSent = timeSent
    
    def addRouting(self, srcIp, nextHopIp): 
        super().addRouting(srcIp, nextHopIp)

class RREQ(Packet): 
    def __init__(self, name, srcIp, origIp, origPos): 
        super().__init__(name=name, plen=20, broadcast=True, priority=Priority.MEDIUM)
        self.origPos = origPos
        self.timesent = 0
        self.origIp = origIp 
        self.srcIp = srcIp
        self.path = [origIp]

    def copy(self): 
        packet = RREQ(
            name=self.name, 
            origPos = self.origPos,  
            origIp = self.origIp, 
            srcIp = self.srcIp 
        )
        packet.path = self.path.copy()
        packet.timesent = self.timesent
        return packet
        
class RRES(Packet): 
    def __init__(self, name, path:list, srcIp, origIp, cost): 
        super().__init__(name=name, plen=20, broadcast=False, priority=Priority.HIGH)
        self.cost = cost
        self.path = path 
        self.srcIp = srcIp
        self.origIp = origIp
        self.nextHopCounter = 1

        self.nextHop = path[-self.nextHopCounter]
        self.nextHopCounter -= 1

    def copy(self): 
        return RRES(
            name=self.name, 
            path = self.path.copy(), 
            srcIp = self.srcIp, 
            origIp = self.origIp, 
            cost = self.cost 
        )

