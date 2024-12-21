from packet import Packet, DataPacket
from typing import List
from heapq import heappop
from host import Host
import simpy

class Radio: 
    def __init__(self, range,  eth: list = [], displayRange = False): 
        self.range = range
        self.displayRange = displayRange
        self.eth = eth
        
class RadioMedium: 
    def __init__(self, env: simpy.Environment, timeFactor, animation, bps, host: List[Host]): 
        self.hosts = {h.ipAddress: h for h in host}
        self.bps = int(bps * timeFactor)
        self.env = env
        self.animation = animation
    
    def passLineFunction(self, func): 
        self.drawLine = func

    @staticmethod
    def inDistance(A: Host, B: Host): 
        distance = pow((A.pos[0] - B.pos[0])**2 + (A.pos[1] - B.pos[1])**2 + (A.pos[2] - B.pos[2])**2, 0.5)
        return A.radio.range >= distance or B.id in A.radio.eth
    
    @staticmethod
    def getDistance(A, B): 
        return pow((A.pos[0] - B.pos[0])**2 + (A.pos[1] - B.pos[1])**2 + (A.pos[2] - B.pos[2])**2, 0.5)
        

    def start(self): 
        while True: 
            # for A in self.host: 
            #     for B in self.host: 
            #         if A == B or not self.inDistance(A, B) or len(A.packetQueue) == 0: continue
            #         packet : Packet = A.packetQueue[0][1]
            #         print(packet.nextHop, B.ipAddress)
            #         if packet.nextHop != B.ipAddress: continue

            #         plen = packet.plen
            #         while plen < self.bps: 
            #             heappop(A.packetQueue)
            #             if self.animation: self.drawLine(A, B, packet.name)
            #             B.onPacketRecieve(packet)
            #             if not len(A.packetQueue): break
            #             packet = A.packetQueue[0][1]
            #             plen += packet.plen
            broadcasts = []
            for A in self.hosts.values(): 
                if not len(A.packetQueue): continue

                packet : Packet = A.packetQueue[0][1]
                plen = packet.plen 
                while plen < self.bps and len(A.packetQueue): 
                    heappop(A.packetQueue)

                    if packet.broadcast: 
                        broadcasts.append(packet)           
                    elif packet.nextHop in self.hosts: 
                        B = self.hosts[packet.nextHop]
                        if not self.inDistance(A, B): 
                            A.onPacketLoss(packet)
                        else: 
                            # if (A.id == 0 and B.id == 11) or (A.id == 11 and B.id == 0): print('Distance between 0 and 11', self.getDistance(A,B))
                            if self.animation and isinstance(packet, DataPacket):
                                self.drawLine(A, B, packet.name if self.getDistance(A, B) > 50 else '', 'blue')
                                if B.id == 12: print('host-12', self.getDistance(A, B))
                            B.onPacketRecieve(packet)

                    if not len(A.packetQueue): break
                    packet : Packet = A.packetQueue[0][1]
                    plen += packet.plen

            for packet in broadcasts: 
                A = self.hosts[packet.srcIp]
                for B in self.hosts.values(): 
                    # if A.id == 10 and B.id == 12: breakpoint()
                    if self.inDistance(A, B) and A.ipAddress != B.ipAddress: 
                        # print(f'Broadcasting {packet.name}: {A.id} --- {B.id}')
                        # if self.animation : self.drawLine(A, B, packet.name, 'red')
                        B.onPacketRecieve(packet.copy())

            yield self.env.timeout(1) 