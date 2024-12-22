from host import Host
from radio import Radio, RadioMedium
from routing import Static, DynamicSplit, QRouting
from app import App, udpGroundStation, udpVideoServer, SixGRouter, SixGRelay
from animation_tk import Animation
from stats import PacketLoss
from typing import List
from random import randint
import simpy
import simpy.rt
import threading
import json

class Network: 
    def __init__(self, env: simpy.Environment, animation, timeFactor, num_hosts, stats): 
        # self.routing = Static()
        self.hosts: List[Host] = []
        self.env = env
        self.consoleRes = simpy.Resource(env, capacity=1)
        starting_pos = [100, 100, 0] 

        for i in range(num_hosts): 
            routing_table = {f'10.0.0.{j}':  [10 ** 1000, set()] for j in range(1,num_hosts+1)} #nextHop : cost, path

            if i < 10: 
                app = udpVideoServer(env, timeFactor=timeFactor, port=100, quality=[640, 320], delay=2, destIp='10.0.0.11', stats = stats) 
                with open(f'waypoints-2/waypoint-{i}.json', 'r') as f: 
                    starting_pos = json.load(f)['waypoints'][0]
                speed = 20
                radio = Radio(150, displayRange=True, eth=[])
                waypointFile = f'waypoints-2/waypoint-{i}.json'
                name = f'host-{i}'

            else: 
                if i == 10: 
                    routerForIp = {f'10.0.0.{j}': f'10.0.0.{12 if j <= 5 else 11}' for j in range(1, 11)}
                    app = udpGroundStation(
                        env, timeFactor, port=100, delay=1, 
                        packetTimeout=10, 
                        routerForIp=routerForIp,
                        swarmLeaders={'10.0.0.3', '10.0.0.8'}, 
                        stats=stats
                        ) 
                else: app = App(env, 1, 1, 1)
                name = 'GCS'
                starting_pos = [500, 60, 0]
                speed = 0
                radio = Radio(150, eth=[])
                waypointFile = ''
        
            host = Host(
                env, 
                id=i, 
                name=name,
                timeFactor=timeFactor, 
                radio=radio, 
                ipAddress=f'10.0.0.{i+1}', 
                apps={100: app},
                pos = starting_pos.copy(), 
                routingProtocol= QRouting(
                    env=env,
                    id = i, 
                    table=routing_table, 
                    ipAddress=f'10.0.0.{i+1}', 
                    rreqTimeout=1, 
                    tableResetTimeout = 10,
                    gsIp = '10.0.0.11', 
                    learningRate=0.5, 
                    timeFactor = timeFactor
                ),
                routingTable=routing_table.copy(), 
                consoleRes=self.consoleRes, 
                speed = speed, 
                waypointFile=waypointFile, 
                gsIp='10.0.0.11', 
                rreqTimeout=20
            )

            self.hosts.append(host) 
        
        self.radiomedium = RadioMedium(env, timeFactor= timeFactor, animation = animation, bps = 10e6, host=self.hosts)

        for host in self.hosts[:10]: 
            host.apps[100].getPos = host.getPos
            host.apps[100].getNewPos = host.getNewPos


        self.hosts[10].radio.eth.append(11)

        self.hosts[11].apps = {}
        self.hosts[11].pos = [180, 60, 0]
        self.hosts[11].name = 'Switch'
        self.hosts[11].radio.eth.append(10)
        self.hosts[11].radio.eth.append(12)
        self.hosts[11].radio.eth.append(13)
        self.hosts[11].radio.eth.append(14)
        self.hosts[11].radio.eth.append(15)


        self.hosts[12].apps = {}
        self.hosts[12].pos = [180, 300, 0]
        self.hosts[12].name = 'Router-1'
        self.hosts[12].radio.eth.append(11)


        self.hosts[13].apps = {}
        self.hosts[13].pos = [180, 500, 0]
        self.hosts[13].name = 'Router-2'
        self.hosts[13].radio.eth.append(11)

        self.hosts[14].apps = {}
        self.hosts[14].pos = [180, 700, 0]
        self.hosts[14].name = 'Router-3'
        self.hosts[14].radio.eth.append(11)


        self.hosts[15].apps = {}
        self.hosts[15].pos = [180, 900, 0]
        self.hosts[15].name = 'Router-4'
        self.hosts[15].radio.eth.append(11)

        #add movement and application process 
        self.app_proc = []
        for host in self.hosts: 
            host.addProcesses()

        #add radio process
        self.env.process(self.radiomedium.start())
    
    
    def passAddLineFunction(self, func): 
        self.radiomedium.passLineFunction(func)


        


if __name__ == '__main__': 
    # env = simpy.Environment()
    timeFactor = 0.1 #1 is equvialent to 1000ms
    env = simpy.rt.RealtimeEnvironment(factor=timeFactor, strict=False)
    stats = PacketLoss(1)
    network = Network(env, animation=True, timeFactor=timeFactor, stats=stats, num_hosts=16) #10 swarm, 1 gcs, 4 routers, 1 switch
    stopEvent = simpy.Event(env)

    animation = Animation(dim=[1000, 1000], scale=0.6, stopEvent=stopEvent, hosts=network.hosts, timeFactor=timeFactor, stats=stats)
    network.passAddLineFunction(lambda A, B, text, color: animation.appendLines(A, B, text, color))
    threading.Thread(target=env.run,kwargs={'until': stopEvent}, daemon=True).start()
    animation.start()
    # env.run()
    
        
    
