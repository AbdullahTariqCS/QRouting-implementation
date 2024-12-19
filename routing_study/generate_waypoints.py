import cv2
import numpy as np
from copy import deepcopy
import json

def generate_waypoint(startWp, startGrid, wpSpeed, height, length, width, numGrids): 
    waypoints = [deepcopy(startWp), deepcopy(startGrid)]

    offset = [[0, length], [width, 0], [0, -length], [width, 0]]
    
    for i in range(numGrids): 
        for j in range(4): 
            if i == numGrids - 1 and j == 3: 
                wp = deepcopy(startWp)
            else: 
                wp = [(startGrid[k] + offset[j][k]) for k in range(2)] + [height] 

            waypoints.append(deepcopy(wp))
            startGrid = wp
    return waypoints

        
def config1(): 
    length = 800
    width = 10
    numGrids = 3 #total area covered = 500m
    speed = 2
    height = 100
    image = np.zeros((1000, 1000, 3)) + 255
    for host in range(10): 
        startWp = [450 + 10*host, 30, 0] 
        startGrid = [200 + 60*host, 100, height]

        waypoints = generate_waypoint(startWp, startGrid, speed, height, length, width, numGrids)

        with open(f'waypoints/waypoint-{host}.json', 'w') as f: 
            json.dump({'waypoints': waypoints}, f, indent=2)
        
        for i in range(len(waypoints) - 1): 
            p1 = waypoints[i]
            p2 = waypoints[i+1]

            cv2.line(image, (int(p1[0]), int(p1[1])), (int(p2[0]), int(p2[1])), (255 * (1-host%2), 0, 255*(host%2)), 1)


    cv2.imshow('test', image)
    cv2.waitKey()
    cv2.imwrite('res/path.jpg', image)

def config2(): 
    length = 400
    width = 10
    numGrids = 6 
    speed = 2
    height = 100
    image = np.zeros((1000, 1000, 3)) + 255
    evenc, oddc = 0, 0
    for host in range(5): 
        startWp = [450 + 20*host, 30, 0]
        # startGrid = [
        #     [200 + 120*evenc, 100, height], 
        #     [200 + 120*oddc, 510, height]
        # ]

        startGrid = [200 + 120*host, 100, height]
        waypoints = generate_waypoint(startWp, startGrid, speed, height, length, width, numGrids)

        with open(f'waypoints-2/waypoint-{host}.json', 'w') as f: 
            json.dump({'waypoints': waypoints}, f, indent=2)
        
        for i in range(len(waypoints) - 1): 
            p1 = waypoints[i]
            p2 = waypoints[i+1]

            if i == 0 or i + 1 == len(waypoints) - 1: continue
            cv2.line(image, (int(p1[0]), int(p1[1])), (int(p2[0]), int(p2[1])), (255 * (1-host%2), 0, 255*(host%2)), 1)
        
        evenc += host%2
        oddc += 1-host%2

    for host in range(5, 10): 
        startWp = [460 + 20*(host-5), 30, 0] 
        startGrid = [200 + 120*(host-5), 510, height]

        waypoints = generate_waypoint(startWp, startGrid, speed, height, length, width, numGrids)

        with open(f'waypoints-2/waypoint-{host}.json', 'w') as f: 
            json.dump({'waypoints': waypoints}, f, indent=2)
        
        for i in range(len(waypoints) - 1): 
            p1 = waypoints[i]
            p2 = waypoints[i+1]

            if i == 0 or i + 1 == len(waypoints) - 1: continue
            cv2.line(image, (int(p1[0]), int(p1[1])), (int(p2[0]), int(p2[1])), (255 * (1-host%2), 0, 255*(host%2)), 1)


    cv2.imshow('test', image)
    cv2.waitKey()
    cv2.imwrite('res/path.jpg', image)

# config1()
config2()


