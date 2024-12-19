from packet import Packet, RREQ, RREQ
import numpy as np

class Routing: 
    def __init__(self, table): 
        self.table = table.copy()

    def setNextHop(self, packet: Packet): 
        pass

    def updateRoutingTable(): 
        pass
    
    def onPacketLoss(self, routingTable, packet) -> str: #returns the updated nexthop 
        pass

class Static(Routing): 
    def __init__(self): 
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
    
        def sendRREQ(self): 
        #starting reverse bfs
        packet = RREQ(name=f'Host-{self.id} RREQ', origIp=self.ipAddress, srcIp=self.ipAddress, origPos=self.pos) 
        print(f'Host-{self.id}: Route broken, Generating RREQ')
        self.rreqSentTime = self.env.now
        heappush(self.packetQueue, [packet.priority, packet])

    def sendRRES(self, packet: RREQ, cost = 0): 
        #starting bfs
        resPacket = RRES(name=f'Host-{self.id} RRES', srcIp=self.ipAddress, origIp=packet.origIp, path=packet.path.copy(), cost=cost) 
        print(f'Host-{self.id}: Found Route for RREQ({packet.name})')
        heappush(self.packetQueue, [resPacket.priority, resPacket])

    def onRREQRecieve(self, packet: RREQ): 
        if self.ipAddress in packet.path: return 
        packet = packet.copy()
        currentNextHop = self.getNextHop()
        if self.ipAddress == self.gsIp: 
            self.sendRRES(packet)
        elif currentNextHop != '' and currentNextHop not in packet.path:  
            self.sendRRES(packet, self.routingTable[currentNextHop])            

        #forward the request
        else: 
            print(f'Host-{self.id}: Recieved RREQ({packet.name}) orig({packet.origIp}) srcIp({packet.srcIp}), broadcasting request')
            self.routingTable[packet.srcIp] = 10 ** 1000 #indicating that the path from this nexthop is broken
            self.rreqSentTime = self.env.now #preventing multiple requests
            packet.path.append(self.ipAddress)
            packet.srcIp = self.ipAddress
            heappush(self.packetQueue, [packet.priority, packet])
    

    def onRRESRecieve(self, packet: RRES): 
        #updates the routing table
        if self.ipAddress in packet.path: 
            return
        
        print(f'Host-{self.id}: Recieved RRES from {packet.srcIp}. ', end='')
        packet = packet.copy()

        self.routingTable[packet.srcIp] = packet.cost #updating the routing table


        if packet.nextHopCounter >= 0: 
            print('Resending new route')
            packet.srcIp = self.ipAddress
            packet.cost += 1
            packet.nextHop = packet.path[-packet.nextHopCounter]
            packet.nextHopCounter -= 1
            heappush(self.packetQueue, [packet.priority, packet])


        