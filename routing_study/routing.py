from packet import Packet, RREQ, RRES, Priority, QRREQ, QRRES
import numpy as np
from time import perf_counter

class Routing: 
    def __init__(self, env, table, hostId, ipAddress, timeFactor): 
        self.table = table.copy()
        self.ipAddress = ipAddress
        self.hostId = hostId
        self.env = env
        self.timeFactor = timeFactor
    
    def passHeapPushFunc(self, onHeapPush): 
        self.onHeapPush = onHeapPush
    
    def start(): 
        pass

    def sendRREQ(self): 
        pass
        
    def onRREQRecieve(self, packet: RREQ): 
        self.sendRRES(packet)

    def sendRRES(self, packet: RREQ): 
        pass
    
    def onRRESRecieve(self, packet: RRES): 
        pass

class Static(Routing): 
    def __init__(self, routingTable): 
       table = {
           '10.0.0.1': '10.0.0.2', 
           '10.0.0.2': '10.0.0.3', 
           '10.0.0.3': '10.0.0.4', 
           '10.0.0.4': '10.0.0.5', 
           '10.0.0.5': '10.0.0.6', 
           '10.0.0.6': '10.0.0.7', 
           '10.0.0.7': '10.0.0.8', 
           '10.0.0.8': '10.0.0.9', 
           '10.0.0.9': '10.0.0.10',  
           '10.0.0.10': '10.0.0.11' 
        }
       super().__init__(table)
    
    def setNextHop(self, ipAddress, packet):
        packet.nextHop = self.table[packet.nextHop]

class DynamicSplit(Routing): 
    def __init__(self): 
        self.nextHopIdx = 0
    


class QRouting(Routing): 
    def __init__(self, env, id, table, ipAddress, rreqTimeout, gsIp, learningRate, timeFactor): 
        super().__init__(env, table, id, ipAddress, timeFactor)
        self.initialTable = table.copy()
        self.rreqTimout = rreqTimeout
        self.gsIp = gsIp
        self.learningRate = learningRate
        self.tableId = 0

    def start(self):
        def proc(): 
            while True: 
                self.sendRREQ()
                time = int(self.rreqTimout / self.timeFactor)
                yield self.env.timeout(time)
        self.env.process(proc())            

    def sendRREQ(self): 
        packet = QRREQ(f'QRREQ({self.hostId})', self.ipAddress, perf_counter(), self.tableId)
        self.onHeapPush(packet.copy())

    def onRREQRecieve(self, packet: QRREQ): 
        # print(f'Host-{self.hostId}: Recived {packet.name}, replying')
        self.sendRRES(packet)

    def sendRRES(self, packet: QRREQ): 
        if self.ipAddress == self.gsIp: 
            cost = 0
        else: 
            tmp = self.table[packet.srcIp]
            self.table[packet.srcIp] = 10 ** 1000
            cost = min(self.table.values())
            self.table[packet.srcIp] = tmp

        packet = QRRES(
            name=f'QRRES({self.hostId})', 
            srcIp=self.ipAddress, 
            timeCreated=packet.timeCreated, 
            tableId=packet.tableId + 1,
            nextHop=packet.srcIp, 
            cost=cost
        )

        self.onHeapPush(packet)
    
    def onRRESRecieve(self, packet: QRRES): 
        #initializing cost
        if self.tableId != packet.tableId: 
            self.table = self.initialTable.copy()
            self.tableId = packet.tableId

        if packet.cost == 10 ** 1000: return
        if self.table[packet.srcIp] == 10 ** 1000: 
            # print(f'Host-{self.id}: updated path through {packet.srcIp}')
            # print('host id:', self.hostId, 'table id: ', self.tableId)
            # for key,val in self.table.items(): 
            #     print(f"\t{key}: {'' if val == 10 ** 1000 else val}" )
            self.table[packet.srcIp] = perf_counter() - packet.timeCreated

        #learning new costs 
        elif self.table[packet.srcIp] != 10 ** 1000: 
            # print(f'Host-{self.id}: updated path through {packet.srcIp}')
            # print('table id: ', self.tableId)
            # for key,val in self.table.items(): 
            #     print(f"\t{key}: {val}" )

            self.table[packet.srcIp] += self.learningRate * (perf_counter() - packet.timeCreated + packet.cost - self.table[packet.srcIp])

        