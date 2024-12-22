from packet import Packet, DataPacket, SixGReq, SixGRes
from time import perf_counter
import simpy
from statistics import mean

class App: 
    def __init__(self, env: simpy.Environment, timeFactor, port, delay): 
        self.env = env
        self.timeFactor = timeFactor
        self.port = port
        self.fps = delay
        # self.simpyDelay = max(1, int(1 / (timeFactor * delay))) 
        self.simpyDelay = delay

    def start(self): 
        pass

    def send(self): 
        return None

    def onRecieve(self, packet:DataPacket): 
        pass

    def addLinkLayer(self, func): 
        self.sendToLinkLayer = func
    
    def addProcess(self, env: simpy.Environment): 
        pass

class udpVideoServer(App): 
    def __init__(self, env, timeFactor, port, quality, delay, destIp, stats): 
        super().__init__(env, port=port, timeFactor=timeFactor, delay=delay)
        self.quality = quality
        self.destIp = destIp
        self.numframes = -1
        self.getPos = None
        self.getNewPos = None
        self.stats = stats

    def send(self) -> DataPacket: 
        """
        sending a single frame
        """
        plen = 3 * self.quality[0] * self.quality[1]
        self.numframes += 1
        # print("Sending data from client", self.getPos(), self.getNewPos())
        self.stats.generatePacket(self.env.now)
        return DataPacket(
            name=f"UdpPacket-{self.numframes}", 
            srcPort=self.port, 
            destPort=100, 
            destIp=self.destIp, 
            timeSent=perf_counter(), 
            plen=plen, 
            ttl = 10, 
            data= {'pos': self.getPos(), 'now': self.env.now, 'north': self.getNewPos()[1] > self.getPos()[1]}
        )
    

    def start(self): 
        while True: 
            packet = self.send()
            self.sendToLinkLayer(packet)
            yield self.env.timeout(self.simpyDelay)

    def addProcess(self, env):
        env.process(self.start())


class udpGroundStation(App): 
    """
    recieves video footage from swarm
    request new routes from routers if a link is not recieved
    """
    def __init__(self, env, timeFactor, port,delay, packetTimeout, routerForIp: dict, swarmLeaders: set, stats): 
        super().__init__(env=env, port=port, timeFactor=timeFactor, delay=delay)
        self.packetTimeout = packetTimeout

        self.lastRecieved = {} #clientIps: last packet recieved
        self.lastSentConnReq = {} #clientIps: last 6g request sent
        self.timeSent = {}
        self.Ypos = {}
        self.North = {}
        self.routerForIp = routerForIp #ip : router => maps swarm ip to a router
        self.stats = stats

    def onRecieve(self, packet: DataPacket):
        delay = perf_counter() -  packet.timeSent
        print("Delay:", delay)
        self.stats.receivePacket(packet.data['now'])
         

    def __copy__(self): 
        return udpGroundStation(self.env, self.port)
        

class SixGRelay(App): 
    """
    for the peripheral hosts to establish connection between ground station and routers
    """
    def __init__(self, env, timeFactor, port, delay, gsNextHop, routerNextHop):
        super().__init__(env=env, timeFactor=timeFactor, port=port, delay=delay)
        self.gsNextHop = gsNextHop
        self.routerNextHop = routerNextHop
    
    def onRecieve(self, packet: SixGReq | SixGRes):
        if isinstance(packet, SixGReq): packet.nextHop = self.routerNextHop
        else: packet.nextHop = self.gsNextHop
        self.sendToLinkLayer(packet)


class SixGRouter(App): 
    def __init__(self, env, timeFactor, port, fps, posBounds, swarmSpeed, maxSpeed, getSpeed, setSpeed, goTo, atWaypoint):
        super().__init__(env=env, timeFactor=timeFactor, port=port, delay=fps)

        self.swarmSpeed = swarmSpeed
        self.maxSpeed = maxSpeed
        self.getSpeed = getSpeed
        self.setSpeed = setSpeed
        self.atWaypoint = atWaypoint

        self.goTo = goTo 
        self.posBounds = posBounds.copy()
        self.posCounter = 0
        self.goingToWaypoint = False

    def start(self): 
        while True: 
            if self.atWaypoint(): 
                self.setSpeed(0)
                self.goingToWaypoint = False 
            yield self.env.timeout(self.simpyDelay)
     

    def onRecieve(self, packet: SixGReq):
        #predict position and go to that position + set the appropriate direction
        # time = distance / speed
        # if not (self.posBounds[0][1] <= packet.yPos <= self.posBounds[1][1]): return

        time = (self.env.now - packet.timeSent) * self.timeFactor 
        predictedYPos = packet.yPos + (self.swarmSpeed * time)


        range_y = self.posBounds[1][1] - self.posBounds[0][1]
        if predictedYPos < self.posBounds[0][1]:
            excess = self.posBounds[0][1] - predictedYPos
            bounces = excess // range_y
            predictedYPos = self.posBounds[0][1] + (excess % range_y)
            # Reverse direction if odd number of bounces
            # if bounces % 2 == 1:
            #     packet.isNorth = not packet.isNorth

        elif predictedYPos > self.posBounds[1][1]:
            excess = predictedYPos - self.posBounds[1][1]
            bounces = excess // range_y
            predictedYPos = self.posBounds[1][1] - (excess % range_y)
            # Reverse direction if odd number of bounces
            # if bounces % 2 == 1:
            #     packet.isNorth = not packet.isNorth

        print(packet.name, packet.yPos, predictedYPos, self.env.now - packet.timeSent, packet.isNorth)
        # breakpoint()
        
        self.setSpeed(self.maxSpeed)
        self.goingToWaypoint = True
        self.goTo([self.posBounds[0][0], predictedYPos, self.posBounds[0][1]])
