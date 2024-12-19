from host import Host
from radio import Radio, RadioMedium
from routing import Static, DynamicSplit, QRouting
from app import udpVideoClient, udpVideoServer
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
            routing_table = {f'10.0.0.{j}':  10 ** 1000 for j in range(1,12)}

            if i != num_hosts-1: 
                app = udpVideoServer(env, timeFactor=timeFactor, port=100, quality=[640, 320], fps=10, destIp='10.0.0.11') 
                with open(f'waypoints-2/waypoint-{i}.json', 'r') as f: 
                    starting_pos = json.load(f)['waypoints'][0]
                speed = 10
                radio = Radio(150, displayRange=True)
                waypointFile = f'waypoints-2/waypoint-{i}.json'
            else: 
                app = udpVideoClient(env, timeFactor, 100) 
                starting_pos = [500, 15, 0]
                speed = 0
                radio = Radio(400)
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
                    
            del routing_table
            self.hosts.append(host)
        
        self.radiomedium = RadioMedium(env, timeFactor= timeFactor, animation = animation, bps = 10e6, host=self.hosts)


        #add movement and application process 
        self.app_proc = []
        for host in self.hosts: 
            host.addProcesses()


        #add radio process
        self.env.process(self.radiomedium.start())
    
    
    def passAddLineFunction(self, func): 
        self.radiomedium.passLineFunction(func)


class NetworkWithDynamicRouting(Network): 
    def __init__(self, *args, **kwargs): 
        super().__init__(*args, **kwargs)

        routing_table = {
            '10.0.0.1': {f'10.0.0.{i}': 10 ** 1000 if i != 2 else 0 for i in range(1, 12)}, 
            '10.0.0.2': {f'10.0.0.{i}': 10 ** 1000 if i != 3 else 0 for i in range(1, 12)}, 
            '10.0.0.3': {f'10.0.0.{i}': 10 ** 1000 if i != 11 else 0 for i in range(1, 12)}, 
            '10.0.0.4': {f'10.0.0.{i}': 10 ** 1000 if i != 3 else 0 for i in range(1, 12)}, 
            '10.0.0.5': {f'10.0.0.{i}': 10 ** 1000 if i != 4 else 0 for i in range(1, 12)}, 
            '10.0.0.6': {f'10.0.0.{i}': 10 ** 1000 if i != 7 else 0 for i in range(1, 12)}, 
            '10.0.0.7': {f'10.0.0.{i}': 10 ** 1000 if i != 8 else 0 for i in range(1, 12)}, 
            '10.0.0.8': {f'10.0.0.{i}': 10 ** 1000 if i != 3 else 0 for i in range(1, 12)}, 
            '10.0.0.9': {f'10.0.0.{i}': 10 ** 1000 if i != 8 else 0 for i in range(1, 12)}, 
            '10.0.0.10': {f'10.0.0.{i}': 10 ** 1000 if i != 9 else 0 for i in range(1, 12)}, 
            '10.0.0.11': {f'10.0.0.{i}': 10 ** 1000 for i in range(1, 12)}, 
        }
        for host in self.hosts: 
            host.routingTable = routing_table[host.ipAddress].copy()
            host.routingProtocol = DynamicSplit()
            host.radio.displayRange = False

        self.hosts[1].radio.range = 400
        self.hosts[1].radio.displayRange = True
        self.hosts[2].radio.displayRange = True


        


if __name__ == '__main__': 
    # env = simpy.Environment()
    timeFactor = 0.1 #1 is equvialent to 1000ms
    env = simpy.rt.RealtimeEnvironment(factor=timeFactor, strict=False)
    network = Network(env, animation=True, timeFactor=timeFactor, num_hosts=11)
    stopEvent = simpy.Event(env)

    animation = Animation(dim=[1000, 1000], scale=0.6, stopEvent=stopEvent, hosts=network.hosts, timeFactor=timeFactor)
    network.passAddLineFunction(lambda A, B, text, color: animation.appendLines(A, B, text, color))
    threading.Thread(target=env.run,kwargs={'until': stopEvent}, daemon=True).start()
    animation.start()
    # env.run()
    
        
    
