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
    def __init__(self, name, srcPort, destPort, destIp, timeSent, plen, ttl, checksum=None): 
        super().__init__(name=name, plen=plen, broadcast = False, priority=Priority.LOW)

        #upd header
        self.srcPort = srcPort
        self.destPort = destPort
        self.checksum = checksum
        self.destIp = destIp
        self.timeSent = timeSent
        self.ttl = ttl
    
    def addRouting(self, srcIp, nextHopIp): 
        super().addRouting(srcIp, nextHopIp)

class RREQ(Packet): 
    def __init__(self, name, plen, broadcast, priority, nextHop=''):
        super().__init__(name, plen, broadcast, priority, nextHop)

class RRES(Packet): 
    def __init__(self, name, plen, broadcast, priority, nextHop=''):
        super().__init__(name, plen, broadcast, priority, nextHop)

class QRREQ(RREQ): 
    def __init__(self, name, srcIp, timeCreated, tableId):
        super().__init__(name, 20, True, priority=Priority.MEDIUM, nextHop='')
        self.timeCreated = timeCreated
        self.srcIp = srcIp
        self.tableId = tableId

    def copy(self): 
        return QRREQ(self.name, self.srcIp, self.tableId, self.timeCreated)

class QRRES(RRES): 
    def __init__(self, name, srcIp, timeCreated, tableId, nextHop, cost, path: set):
        super().__init__(name, 20, False, priority=Priority.HIGH, nextHop=nextHop)
        self.srcIp = srcIp
        self.timeCreated = timeCreated
        self.cost = cost
        self.tableId = tableId 
        self.path = path

    def copy(self): 
        return QRREQ(self.name, self.timeCreated, self.tableId, self.nextHop, self.cost)


class SixGReq(Packet): 
    """
    Sent by the gc to routers, indicating the reward of each position
    Each router modifies the cost according the their position and forwards it to the next one
    """
    def __init__(self, name, nextHop, speedUp):
        super().__init__(name, 50, False, Priority.HIGH, nextHop)
        self.speedUp = speedUp

    def copy(self): 
        return SixGReq(self.name, self.nextHop, self.speedUp)

    def addRouting(self, srcIp, nextHopIp):
        self.srcIp = srcIp

class SixGRes(Packet): 
    """
    Sent by routers to gc, indicating their positions. 
    It also allows the gc to monitor 
    """
    def __init__(self, name, nextHop, srcIp, pos):
        super().__init__(name, 20, False, Priority.HIGH, nextHop)
        self.pos = pos
        self.srcIp = srcIp

    def copy(self): 
        return SixGRes(self.name, self.nextHop, self.srcIp, self.pos.copy())

    def addRouting(self, srcIp, nextHopIp):
        self.srcIp = srcIp
    





