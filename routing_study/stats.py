import matplotlib.pyplot as plt
class PacketLoss: 
    def __init__(self, delay): 
        self.packetsGenerated = {}
        self.packetRecieved = {}
        self.delay = delay

    def generatePacket(self, time): 
        self.packetsGenerated[(time // self.delay)] = 1 if time not in self.packetsGenerated else  self.packetsGenerated[time] + 1

    def receivePacket(self, time): 
        self.packetRecieved[(time // self.delay)] = 1 if time not in self.packetRecieved else self.packetRecieved[time] + 1

    def plot(self): 
        times = sorted(self.packetsGenerated.keys())
        generated = [self.packetsGenerated[t] for t in times]
        received = [self.packetRecieved.get(t, 0) for t in times]

        plt.plot(times, generated, label='Packets Generated')
        plt.plot(times, received, label='Packets Received')
        plt.fill_between(times, generated, received, color='gray', alpha=0.5, label='Packet Loss')

        plt.xlabel('Time')
        plt.ylabel('Packets')
        plt.title('Packet Generation and Reception Over Time')
        plt.legend()
        plt.show()
