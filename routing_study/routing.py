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
    def __init__(self, env, id, table, ipAddress, rreqTimeout, tableResetTimeout, gsIp, learningRate, timeFactor): 
        super().__init__(env, table, id, ipAddress, timeFactor)
        self.initialTable = table.copy()
        self.rreqTimout = rreqTimeout
        self.gsIp = gsIp
        self.learningRate = learningRate
        self.tableId = 0
        self.tableResetTimeout = 0
        self.lastTableUpdatedTime = 0
        self.requestedTableId = 0
        self.lastSent = {t:0 for t in table}
        self.tableResetTimeout = tableResetTimeout

    def start(self):
        def proc(): 
            while True: 
                self.sendRREQ()
                time = int(self.rreqTimout / self.timeFactor)
                yield self.env.timeout(1)
        self.env.process(proc())            

    def sendRREQ(self): 
        self.requestedTableId = self.tableId + 1
        packet = QRREQ(f'QRREQ({self.hostId})', self.ipAddress, perf_counter(), self.requestedTableId)
        self.onHeapPush(packet.copy())

        # for ip, t in self.lastSent.items(): 
        #     self.lastSent[ip] += 1
        #     if t >= self.tableResetTimeout: 
        #         self.table[ip] = [10 ** 1000, set()]

    def onRREQRecieve(self, packet: QRREQ): 
        # print(f'Host-{self.hostId}: Recived {packet.name}, replying')
        self.sendRRES(packet)

    def sendRRES(self, packet: QRREQ): 
        if self.ipAddress == self.gsIp: 
            cost, path = 0, set()
        else: 
            cost, path = self.table[min(self.table, key=lambda x: self.table[x][0])]

        # path.add(self.ipAddress)

        packet = QRRES(
            name=f'QRRES({self.hostId})', 
            srcIp=self.ipAddress, 
            timeCreated=packet.timeCreated, 
            tableId=packet.tableId, #send response for the new table
            nextHop=packet.srcIp, 
            cost=cost,
            path=path
        )
        self.onHeapPush(packet)


    def onRRESRecieve(self, packet: QRRES): 
        if self.tableId != packet.tableId: 
            self.table = self.initialTable.copy()
            self.tableId = packet.tableId
        
        if packet.cost == 10 ** 1000 or self.ipAddress in packet.path or packet.srcIp == self.ipAddress: 
            self.table[packet.srcIp] = [10 ** 1000, set()]

        elif self.table[packet.srcIp][0] == 10 ** 1000: 
            self.table[packet.srcIp] = [perf_counter() - packet.timeCreated + packet.cost, packet.path.copy()]

        #learning new costs 
        elif self.table[packet.srcIp][0] != 10 ** 1000: 
            self.table[packet.srcIp][0] += self.learningRate * (perf_counter() - packet.timeCreated + packet.cost - self.table[packet.srcIp][0])
            self.table[packet.srcIp][1] = packet.path.copy()
        