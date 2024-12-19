import simpy
from typing import Dict, List
import simpy.resources
from app import App
from heapq import heappush
from packet import Packet, DataPacket, RREQ, RRES
import json
import numpy as np
from copy import copy

class Host: 
    def __init__(self, env: simpy.Environment, id, timeFactor, radio, ipAddress, apps: Dict[int, App],\
                 pos:List[float], routingProtocol, routingTable: Dict[str, list], consoleRes : simpy.Resource, speed, 
                waypointFile, gsIp, rreqTimeout
        ): 
        self.id = id
        self.env = env
        self.timeFactor = timeFactor
        self.radio = radio
        self.ipAddress = ipAddress
        self.apps = apps #{port : App}
        self.pos = pos
        self.routingProtocol = routingProtocol
        self.routingTable = routingTable
        self.packetQueue = []
        self.heapLock = False 
        self.consoleRes = consoleRes
        self.speed = speed
        self.waypointFile = waypointFile
        self.gsIp = gsIp
        self.rreqTimeout = rreqTimeout
        self.rreqSentTime = 0
        for app in self.apps.values(): 
            app.addLinkLayer(lambda packet: self.onSelfRecieve(packet))

    def getNextHop(self): 
        ip = ''
        if len(self.routingTable): 
            ip = min(self.routingTable, key=self.routingTable.get)
            if self.routingTable[ip] == 10 ** 1000: 
                ip = ''
        return ip

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



    def onPacketLoss(self, packet: Packet): 
        self.routingTable[self.getNextHop()] = 10 ** 1000
        if self.env.now - self.rreqSentTime >= self.rreqTimeout: 
            self.sendRREQ()
            heappush(self.packetQueue, [packet.priority, packet])



    def onPacketRecieve(self, packet: Packet): 
        string = ''
        if isinstance(packet, RREQ): 
            self.onRREQRecieve(packet)
        
        if isinstance(packet, RRES): 
            self.onRRESRecieve(packet)
        
        if isinstance(packet, DataPacket): 
            if packet.destIp == self.ipAddress: 
                self.apps[packet.destPort].onRecieve(packet)

            elif packet.nextHop == self.ipAddress: 
                packet.nextHop = self.getNextHop()
                if packet.nextHop == '': 
                    # string += f'Dropping Packet {packet.name}'
                    self.onPacketLoss(packet)
                else: 
                    heappush(self.packetQueue, [packet.priority, packet])
                    print(f'Host-{self.id}: Recieved {packet.name} from {packet.srcIp}, forwarding to {packet.nextHop}')
            else: 
                string += f'Dropping Packet {packet.name}'
        


                
    def onSelfRecieve(self, packet: DataPacket): 
        packet.addRouting(self.ipAddress, self.getNextHop())
        if packet.nextHop == '': 
            print(f'Host-{self.id}: Dropping {packet.name}')
        else: 
            heappush(self.packetQueue, [packet.priority, packet])
            
    
    def addProcesses(self): 
        for app in self.apps.values(): 
            app.addProcess(self.env)
        if self.waypointFile != '': 
            self.env.process(self.executeMission(self.waypointFile))


    def executeMission(self, path): 
        with open(path) as f: 
            data = json.load(f)
            waypoints = data['waypoints']

        for w in waypoints: 
            while self.move(w): 
                yield self.env.timeout(1)
         

    def move(self, newPos): 
        distance = pow((self.pos[0] - newPos[0])**2 + 
                    (self.pos[1] - newPos[1])**2 + 
                    (self.pos[2] - newPos[2])**2, 0.5)

        if distance == 0: return False
        x = (newPos[0] - self.pos[0]) / distance
        y = (newPos[1] - self.pos[1]) / distance
        z = (newPos[2] - self.pos[2]) / distance

        step_distance = min(self.speed * self.timeFactor, distance)
        
        self.pos[0] += x * step_distance
        self.pos[1] += y * step_distance
        self.pos[2] += z * step_distance

        distance -= step_distance
        
        return distance > 1e-6
        
