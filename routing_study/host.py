import simpy
from typing import Dict, List
import simpy.resources
from app import App
from heapq import heappush
from packet import Packet, DataPacket, RREQ, RRES
import json
import numpy as np
from routing import Routing
from copy import copy

class Host: 
    def __init__(self, env: simpy.Environment, id, timeFactor, radio, ipAddress, apps: Dict[int, App],\
                 pos:List[float], routingProtocol:Routing, routingTable: Dict[str, list], consoleRes : simpy.Resource, speed, 
                waypointFile, gsIp, rreqTimeout, flightMode = 'Auto'
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
        self.flightMode = flightMode
        self.newPos = [0, 0, 0]
        for app in self.apps.values(): 
            app.addLinkLayer(lambda packet: self.onSelfRecieve(packet))

        routingProtocol.passHeapPushFunc(lambda packet: heappush(self.packetQueue, [packet.priority, packet]))

    def getNextHop(self): 
        ip = min(self.routingProtocol.table, key=lambda x: self.routingProtocol.table[x][0])
        if self.routingProtocol.table[ip] == 10 ** 1000 or self.ipAddress == ip: 
            return ''
        return ip

    def getSpeed(self): return self.speed
    def setSpeed(self, speed): self.speed = speed

    def onPacketLoss(self, packet: Packet): 
        pass
    #     self.routingTable[self.getNextHop()] = 10 ** 1000
    #     if self.env.now - self.rreqSentTime >= self.rreqTimeout: 
    #         self.sendRREQ()
    #         heappush(self.packetQueue, [packet.priority, packet])


    def onPacketRecieve(self, packet: Packet): 
        string = ''
        if isinstance(packet, RREQ): 
            self.routingProtocol.onRREQRecieve(packet)
        
        if isinstance(packet, RRES): 
            self.routingProtocol.onRRESRecieve(packet)
     
        if isinstance(packet, DataPacket): 

            if packet.destIp == self.ipAddress: 
                self.apps[packet.destPort].onRecieve(packet)
            elif packet.nextHop == self.ipAddress: 
                packet.nextHop = self.getNextHop()
                if packet.nextHop == '': 
                    self.onPacketLoss(packet)
                else: 
                    heappush(self.packetQueue, [packet.priority, packet])
                    print(f'Host-{self.id}: Recieved {packet.name} from {packet.srcIp}, forwarding to {packet.nextHop}')
            else: 
                string += f'Dropping Packet {packet.name} {packet.nextHop}'
        

                
    def onSelfRecieve(self, packet: DataPacket): 
        packet.addRouting(self.ipAddress, self.getNextHop())
        if packet.nextHop == '': 
            print(f'Host-{self.id}: Dropping {packet.name}')
        else: 
            heappush(self.packetQueue, [packet.priority, packet])
            
    
    def addProcesses(self): 
        for app in self.apps.values(): 
            app.addProcess(self.env)
        self.routingProtocol.start()
        if self.waypointFile != '': 
            self.env.process(self.executeMission(self.waypointFile))
        



    def getDistance(self, newPos) :
        return pow((self.pos[0] - newPos[0])**2 + 
                    (self.pos[1] - newPos[1])**2 + 
                    (self.pos[2] - newPos[2])**2, 0.5)

    def goTo(self, targetPos): 
        distance = self.getDistance(targetPos)
        if distance <= 1e-6: return True #incidation we have reached the targetposition
        else: 
            self.newPos = targetPos
            return False  


    def executeMission(self, path): 
        waypoints = []
        if self.waypointFile != '': 
            with open(path) as f: 
                data = json.load(f)
                waypoints = data['waypoints']

        wCount = -1
        while True: 
            if self.flightMode == 'Auto' and wCount < len(waypoints): 
                wCount += 1
                if not self.move(waypoints[wCount]): break
            elif self.flightMode == 'Guided': 
                if not self.move(self.newPos): break
            else: 
                break

            yield self.env.timeout(1)
         

    def move(self, newPos): 
        distance = self.getDistance()
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
        
