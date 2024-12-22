from host import Host
from radio import Radio, RadioMedium
from routing import Static, DynamicSplit, QRouting
from app import App, udpGroundStation, udpVideoServer, SixGRouter, SixGRelay
from animation_tk import Animation
from typing import List
from random import randint
import simpy
import simpy.rt
import threading
import json

class Network: 
    def __init__(self, env: simpy.Environment, animation, timeFactor, num_hosts): 
        # self.routing = Static()
        self.hosts: List[Host] = []
        self.env = env
        self.consoleRes = simpy.Resource(env, capacity=1)
        starting_pos = [100, 100, 0] 

        for i in range(num_hosts): 
            routing_table = {f'10.0.0.{j}':  [10 ** 1000, set()] for j in range(1,num_hosts+1)} #nextHop : cost, path

            if i < num_hosts-4: 
                app = udpVideoServer(env, timeFactor=timeFactor, port=100, quality=[640, 320], delay=2, destIp='10.0.0.14') 
                with open(f'waypoints-2/waypoint-{i}.json', 'r') as f: 
                    starting_pos = json.load(f)['waypoints'][0]
                speed = 20
                radio = Radio(150, displayRange=True, eth=[])
                waypointFile = f'waypoints-2/waypoint-{i}.json'

            else: 
                if i == num_hosts - 1: 
                    routerForIp = {f'10.0.0.{j}': f'10.0.0.{12 if j <= 5 else 11}' for j in range(1, 11)}
                    app = udpGroundStation(
                        env, timeFactor, port=100, delay=1, 
                        packetTimeout=10, 
                        routerForIp=routerForIp,
                        swarmLeaders={'10.0.0.3', '10.0.0.8'} 
                        ) 
                else: app = App(env, 1, 1, 1)
                starting_pos = [500, 15, 0]
                speed = 0
                radio = Radio(150, eth=[])
                waypointFile = ''
        
            host = Host(
                env, 
                id=i, 
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
                    gsIp = '10.0.0.14', 
                    learningRate=0.5, 
                    timeFactor = timeFactor
                ),
                routingTable=routing_table.copy(), 
                consoleRes=self.consoleRes, 
                speed = speed, 
                waypointFile=waypointFile, 
                gsIp='10.0.0.14', 
                rreqTimeout=20
            )

            self.hosts.append(host) 
        
        self.radiomedium = RadioMedium(env, timeFactor= timeFactor, animation = animation, bps = 10e6, host=self.hosts)

        for host in self.hosts[:10]: 
            host.apps[100].getPos = host.getPos
            host.apps[100].getNewPos = host.getNewPos

        self.hosts[10].apps = {0: SixGRelay(env, timeFactor, 100, 1, gsNextHop='10.0.0.14', routerNextHop='10.0.0.13')}
        self.hosts[10].pos = [500, 920, 0]
        self.hosts[10].radio.eth.append(12)
        self.hosts[10].radio.eth.append(13)
        self.hosts[10].speed = 0
        self.hosts[10].apps[0].addLinkLayer(lambda packet: self.hosts[10].onSelfRecieve(packet))

        self.hosts[11].apps = {
            0: SixGRouter(
                env, timeFactor, 100, 1, 
                posBounds=[[500, 100, 110], [500, 500, 110]], 
                swarmSpeed=20, 
                maxSpeed=50, 

                #endpoints to control the drone
                goTo=self.hosts[11].goTo, 
                getSpeed=self.hosts[11].getSpeed, 
                setSpeed=self.hosts[11].setSpeed, 
                atWaypoint=self.hosts[11].atWaypoint 
            )}
        
        self.hosts[11].pos = [500, 366, 0]
        self.hosts[11].radio.eth.append(13)
        # self.hosts[11].flightMode = 'Guided'
        self.hosts[11].apps[0].addLinkLayer(lambda packet : self.hosts[11].onSelfRecieve(packet))
        
        self.hosts[12].apps = {
            0: SixGRouter(
                env, timeFactor, 100, 1,
                posBounds=[[500, 900, 110], [500, 510, 110]], 
                swarmSpeed=20, 
                maxSpeed=50, 
                goTo=self.hosts[12].goTo, 
                getSpeed=self.hosts[12].getSpeed, 
                setSpeed=self.hosts[12].setSpeed,
                atWaypoint=self.hosts[12].atWaypoint 
            )}

        self.hosts[12].pos = [510, 632, 0]
        self.hosts[12].radio.eth.append(10)
        # self.hosts[12].flightMode = 'Guided'
        self.hosts[12].apps[0].addLinkLayer(lambda packet: self.hosts[12].onSelfRecieve(packet))

        self.hosts[13].radio.eth.append(10)
        self.hosts[13].radio.eth.append(11)
        self.hosts[13].speed = 0 

        
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
    network = Network(env, animation=True, timeFactor=timeFactor, num_hosts=14) #10 swarm, 1 gcs, 2 routers, 1 routerGsRelay
    stopEvent = simpy.Event(env)

    animation = Animation(dim=[1000, 1000], scale=0.6, stopEvent=stopEvent, hosts=network.hosts, timeFactor=timeFactor)
    network.passAddLineFunction(lambda A, B, text, color: animation.appendLines(A, B, text, color))
    threading.Thread(target=env.run,kwargs={'until': stopEvent}, daemon=True).start()
    animation.start()
    # env.run()
    
        
    
