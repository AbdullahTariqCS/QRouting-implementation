import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation
from matplotlib.offsetbox import AnnotationBbox, OffsetImage
import matplotlib.image as mpimg
from host import Host
from typing import List, Tuple
from itertools import count
import numpy as np 

class Animation: 
    def __init__(self, dim: Tuple[int, int], hosts: List[Host], fps = 30): 
        self.lines = {}
        self.hosts = hosts
        self.fig, self.ax = plt.subplots()

        self.ax.set_xlim(0, dim[0])
        self.ax.set_ylim(0, dim[1])
        self.ax.set_aspect('equal')

        self.scat = self.ax.scatter([], [], color = [])
        self.update_scatter_data()

        for host in self.hosts:
            x, y, size = host.pos
            # self.ax.scatter(x, y, s=max(size * np.interp(size, [0, 500], [2, 0]), 1), label=f"{host.id}")  # `s` scales the marker size
            # self.ax.scatter(x, y, label=f"{host.pos[2]}")  # `s` scales the marker size
            if host.radio.displayRange: 
                circle = plt.Circle((x, y), host.radio.range, color='blue', fill=False, linestyle='--', alpha=0.5)
                self.ax.add_patch(circle)
        
        self.ax.legend()
        

        ani = FuncAnimation(self.fig, lambda f: self.update(f), frames=count(), interval=50, save_count=10)
        plt.show()

    def update_scatter_data(self):
        """Initialize the scatter data for hosts."""
        positions = [(host.pos[0], host.pos[1]) for host in self.hosts]
        sizes = [max(host.pos[2] / 2, 1) for host in self.hosts]
        colors = ['red', 'blue', 'red', 'blue','red', 'blue','red', 'blue','red', 'blue']
        # labels = [f"Host {host.id}" for host in self.hosts]

        self.scat.set_offsets(positions)
        self.scat.set_color(colors)
        # self.scat.set_sizes(sizes)
        # self.scat.set_label(labels)
        
    def drawLines(self, A: Host, B: Host, text_label):
        x1, y1 = A.pos
        x2, y2 = B.pos
        line, = self.ax.plot([x1, x2], [y1, y2], color='blue', alpha=1.0)
        mid_x = (x1 + x2) / 2
        mid_y = (y1 + y2) / 2
        angle = np.arctan2(y2 - y1, x2 - x1) * 180 / np.pi
        text = self.ax.text(mid_x, mid_y, text_label, color="blue", fontsize=10, ha="center", va="center", alpha=1.0, rotation=angle)
        self.lines.append((line, text, 1.0))  

    def update(self, frame):

        # Gradually fade lines
        for i, (line, text, alpha) in self.lines.items():
            alpha -= 0.2     # Decrease alpha to fade
            if alpha <= 0:
                line.remove()  # Remove fully faded lines
                self.lines[i] = None
            else:
                line.set_alpha(alpha)  # Update transparency
                text.set_alpha(alpha)  # Update transparency
                self.lines[i] = (line, text, alpha)

        self.update_scatter_data() 
        # for i, host in enumerate(self.hosts):
        #     x, y, size = host.pos
        #     # self.icons[i].xy = (x, y)
        #     self.ax.scatter(x, y, s=max(size/2, 1), label=f"Host {host.id}")  # `s` scales the marker size

        
        #{also update the position of the hosts}
