from packet import Packet, DataPacket, SixGReq, SixGRes
from time import perf_counter
import simpy


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
    def __init__(self, env, timeFactor, port, quality, delay, destIp): 
        super().__init__(env, port=port, timeFactor=timeFactor, delay=delay)
        self.quality = quality
        self.destIp = destIp
        self.numframes = -1

    def send(self) -> DataPacket: 
        """
        sending a single frame
        """
        plen = 3 * self.quality[0] * self.quality[1]
        self.numframes += 1
        return DataPacket(
            name=f"UdpPacket-{self.numframes}", 
            srcPort=self.port, 
            destPort=100, 
            destIp=self.destIp, 
            timeSent=perf_counter(), 
            plen=plen, 
            ttl = 10
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
    The fps of this app should be less than the fps of udpVideoclient so that it can detect the client before sending anymore connection requests
    """
    def __init__(self, env, timeFactor, port,delay, packetTimeout, routerForIp: dict): 
        super().__init__(env=env, port=port, timeFactor=timeFactor, delay=delay)
        self.packetTimeout = packetTimeout

        self.lastRecieved = {} #clientIps: last packet recieved
        self.lastSentConnReq = {} #clientIps: last 6g request sent
        self.routerForIp = routerForIp #ip : router => maps swarm ip to a router

    def onRecieve(self, packet: DataPacket):
        delay = perf_counter() -  packet.timeSent
        print("Delay:", delay)
        self.lastRecieved[packet.srcIp] = 0
        packet = SixGReq(name=f"6Greq({packet.srcIp})", nextHop=self.routerForIp[packet.srcIp], speedUp=False)                    
        self.sendToLinkLayer(packet)

    def start(self): 
        #sends 6greq packets to relevant routers, indicating broken connections
        while True: 
            for c in self.lastRecieved: 
                self.lastRecieved[c] += 1
                if self.lastRecieved[c] >= self.packetTimeout: 
                    packet = SixGReq(name=f"6Greq({c})", nextHop=self.routerForIp[c], speedUp=True)                    
                    self.sendToLinkLayer(packet)
            yield self.env.timeout(self.simpyDelay)
            

    def addProcess(self, env):
        env.process(self.start())

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
    def __init__(self, env, timeFactor, port,fps, posBounds, swarmSpeed, maxSpeed, getSpeed, setSpeed, goTo):
        super().__init__(env=env, timeFactor=timeFactor, port=port, delay=fps)

        self.swarmSpeed = swarmSpeed
        self.speedBound = maxSpeed
        self.getSpeed = getSpeed
        self.setSpeed = setSpeed

        self.goTo = goTo 
        self.posBounds = posBounds.copy()
        self.posCounter = 0


    def onRecieve(self, packet: SixGReq):
        # if packet.speedUp: breakpoint()
        # if self.getSpeed() <= 1e-6: 
        #     self.setSpeed(10) 

        if packet.speedUp : self.setSpeed(self.speedBound)
        else: self.setSpeed(self.swarmSpeed)
        # newSpeed = max(min(self.speedDelta * self.getSpeed() + (1 if packet.speedUp else -1) * self.getSpeed(), self.speedBound), 0)

        if self.goTo(self.posBounds[self.posCounter]): 
            self.posCounter = (self.posCounter + 1) % 2
            self.goTo(self.posBounds[self.posCounter])