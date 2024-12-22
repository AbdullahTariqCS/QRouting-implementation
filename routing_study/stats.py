import matplotlib.pyplot as plt
class PacketLoss: 
    def __init__(self, delay, timeFactor): 
        self.packetsGenerated = {}
        self.packetRecieved = {}
        self.packetsLost = {}
        self.packetsDelay = {}
        self.delay = delay
        self.time = 0
        self.timeFactor = timeFactor

    def generatePacket(self, time): 
        time = (time // self.delay) * self.delay
        self.packetsGenerated[time] = 1 if time not in self.packetsGenerated else  self.packetsGenerated[time] + 1

    def receivePacket(self, time): 
        time = (time // self.delay) * self.delay
        self.packetRecieved[time] = 1 if time not in self.packetRecieved else self.packetRecieved[time] + 1

    def lostPacket(self, time): 
        time = (time // self.delay) * self.delay
        self.packetsLost[time] = 1 if time not in self.packetsLost else self.packetsLost[time] + 1

    def avgDelay(self, time, delay): 
        print("delay: ", delay)
        time = (time // self.delay) * self.delay
        self.packetsDelay[time] = delay if time not in self.packetsDelay else (delay + self.packetsDelay[time]) / 2

    def updateTime(self, time): 
        self.time = max(time, self.time)

    def plot(self): 
        times = range(0, self.time, self.delay) 
        # received = [self.packetRecieved[t] if t in self.packetRecieved else 0 for t in times]
        # generated = [self.packetsGenerated[t] if t in self.packetsGenerated else 0 for t in times]
        lost = [self.packetsLost[t] if t in self.packetsLost else 0 for t in times]
        delay = [self.packetsDelay[t] if t in self.packetsDelay else 0 for t in times]
        times = [t * self.timeFactor for t in times]
        averagePacketLost = 0
        averagePacketLostList = []

        for t in range(len(times)): 
            averagePacketLost = (averagePacketLost + lost[t]) / 2
            averagePacketLostList.append(averagePacketLost)

            

        # plt.plot(times, lost, label='Packets Lost')
        # plt.ylabel('Packets')
        # plt.xlabel('Time')
        # plt.title('Packets lost over time')
        # plt.plot(times, delay, label='Packets Delay (s)')
        fig, (ax1, ax2) = plt.subplots(1, 2)

        ax1.plot(times, lost, label='Packets Lost')
        # ax1.plot(times, averagePacketLostList, label='Average Packets Lost')
        ax1.set_xlabel('Time')
        ax1.set_ylabel('Packets')
        ax1.set_title('Packet Lost Over Time')
        ax1.legend()

        ax2.plot(times, delay, label='Packets Delay (s)')
        ax2.set_xlabel('Time')
        ax2.set_ylabel('Delay (s)')
        ax2.set_title('Packet Delay Over Time')
        ax2.legend()

        plt.tight_layout()
        plt.show()
