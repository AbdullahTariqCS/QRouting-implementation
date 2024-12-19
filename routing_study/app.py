from packet import Packet, DataPacket
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
            plen=plen
        )

    def start(self): 
        while True: 
            packet = self.send()
            self.sendToLinkLayer(packet)
            time = int(self.fps / self.timeFactor)
            yield self.env.timeout(1)

    def addProcess(self, env):
        env.process(self.start())


class udpVideoClient(App): 
    def __init__(self, env, timeFactor, port): 
        super().__init__(env, port, timeFactor)

    def onRecieve(self, packet: DataPacket):
        delay = packet.timeSent - perf_counter()
        print("Delay:", delay)
    
    def __copy__(self): 
        return udpVideoClient(self.env, self.port)
        
