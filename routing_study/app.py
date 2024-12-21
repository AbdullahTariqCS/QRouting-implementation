from packet import Packet, DataPacket, SixGPacket, SixGRes
from time import perf_counter
import simpy


class App: 
    def __init__(self, env: simpy.Environment, timeFactor, port): 
        self.env = env
        self.timeFactor = timeFactor
        self.port = port

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
    def __init__(self, env, timeFactor, port, quality, fps, destIp): 
        super().__init__(env, port=port, timeFactor=timeFactor)
        self.quality = quality
        self.fps = fps
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
            time = max(1, int(self.fps * self.timeFactor))
            yield self.env.timeout(time)

    def addProcess(self, env):
        env.process(self.start())


class udpVideoClient(App): 
    def __init__(self, env, timeFactor, port, packetTimeout, routerIps: dict): 
        super().__init__(env, port, timeFactor)
        self.packetTimeout = packetTimeout
        self.clients = {} #clients: last packet recieved
        self.routerIps = routerIps #ip: {}

    def onRecieve(self, packet: DataPacket):
        delay = perf_counter() -  packet.timeSent
        print("Delay:", delay)
        self.clients[packet.srcIp] = 0

    def start()
        #sends 6greq packets to relevant routers, indicating broken connections
    
    def __copy__(self): 
        return udpVideoClient(self.env, self.port)
        

class SixGServer(App): 
    def __init__(self, env, timeFactor, port, routerNextHop, routerIps, routerResTimeout, fps):
        super().__init__(env, timeFactor, port)
        self.routerNextHop = routerNextHop
        self.routerResTimeout = routerResTimeout 
        self.timeOfLastRes = {i:0 for i in routerIps} 
        self.fps = fps

    def send(self) -> SixGPacket: 
        packet = SixGPacket()
        return packet

        
    def onLinkBreak(ip, rewards:dict): 
        pass

    def start(self): 
        while True: 
            packet = self.send()
            self.sendToLinkLayer(packet)
            yield self.env.timeout(min(1, int(self.fps * self.timeFactor)))
    
    def onRecieve(self, packet: SixGRes):
        pass

class SixGRelay(App): 
    def __init__(self, env, timeFactor, port, gsNextHop, routerNextHop):
        super().__init__(env, timeFactor, port)
        self.gsNextHop = gsNextHop
        self.routerNextHop = routerNextHop
    
    def onRecieve(self, packet: SixGPacket | SixGRes):
        if isinstance(packet, SixGPacket): packet.nextHop = self.routerNextHop
        else: packet.nextHop = self.gsNextHop
        self.sendToLinkLayer(packet)


class SixGClient(App): 
    def __init__(self, env, timeFactor, port, gsNextHop, routerNextHop, alpha, beta):
        super().__init__(env, timeFactor, port)
        self.costs = {}
        self.gsNextHop = gsNextHop
        self.routerNextHop = routerNextHop

        #increases the rewards closest to it, and 
        self.alpha = alpha
        self.beta = beta


    def onRecieve(self, packet: SixGPacket | SixGRes):
        if isinstance(packet, SixGPacket): 
            #get the position for host using rewards, alpha, and beta


            #forward to the next router
            packet.nextHop = self.routerNextHop
            self.sendToLinkLayer(packet)

        else: 
            #forward to the ground station
            packet.nextHop = self.gsNextHop
            self.sendToLinkLayer(packet)
    







