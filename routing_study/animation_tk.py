import tkinter as tk
from PIL import Image, ImageTk
from typing import List, Tuple
from host import Host
import math
from collections import deque
import sys
import numpy as np


class Animation:
    def __init__(self, dim: Tuple[int, int], scale, stopEvent, hosts: List[Host], timeFactor):
        self.lines = deque(maxlen=15)  # Limit the number of active lines to prevent memory issues
        self.oldLines = deque(maxlen=15)  # Limit the number of active lines to prevent memory issues
        self.hosts = hosts
        self.width, self.height = dim[0]* scale, dim[1]*scale
        self.timeFactor = timeFactor
        self.scale = scale

        # Create the Tkinter window and canvas
        self.root = tk.Tk()
        self.root.title("Host Animation")
        self.canvas = tk.Canvas(self.root, width=self.width, height=self.height, bg="white")
        self.canvas.pack()

        self.background_image = Image.open('res/path.jpg')  # Load the image
        self.background_image = self.background_image.resize((int(self.width), int(self.height)), Image.Resampling.LANCZOS)  # Resize to fit canvas
        self.bg_photo = ImageTk.PhotoImage(self.background_image)  # Convert to PhotoImage
        self.canvas.create_image(0, 0, image=self.bg_photo, anchor="nw")  # Draw on canvas

        # Pre-render host circles and labels
        self.stopEvent = stopEvent
        self.host_circles = []
        self.host_labels = []
        self.host_range = {}
        self.render_hosts()


        self.updating = False
        def on_closing():
            stopEvent.succeed()
            self.root.destroy()
            sys.exit()
        self.root.protocol("WM_DELETE_WINDOW", on_closing)

    def start(self): 
        try: 
            # Start the animation loop
            # self.root.after(int(1000 / self.fps), self.update, 0)
            self.root.after(int(1000 * self.timeFactor), self.update, 0)
            self.root.mainloop()
        except KeyboardInterrupt as k: 
            self.stopEvent.succeed()
            raise KeyboardInterrupt

    def render_hosts(self):
        """Pre-render the hosts and their labels."""
        for host in self.hosts:
            x, y, size = host.pos
            x, y = x*self.scale, y*self.scale
            # Draw the host as a red circle
            circle = self.canvas.create_oval(
                x - 5, y - 5, x + 5, y + 5, fill="red", outline="black"
            )
            self.host_circles.append(circle)

            # Draw the host ID as a label
            label = self.canvas.create_text(
                x + size + 5, y - 10, text=f"Host {host.id}", fill="black", anchor="w"
            )
            self.host_labels.append(label)

            # Draw the range of the host if required
            r = host.radio.range*self.scale
            if host.radio.displayRange:
                radio_range = self.canvas.create_oval(
                    x - r, y - r, x + r, y + r,
                    outline="blue", dash=(5,), fill="", width=1
                )
                self.host_range[host.id] = radio_range

    def appendLines(self, A: Host, B: Host, text_label, color): 
        x1, y1 = A.pos[:-1]
        x2, y2 = B.pos[:-1]

        x1, y1, x2, y2 = x1*self.scale, y1*self.scale, x2*self.scale, y2*self.scale
        if not self.updating: 
            if len(self.lines) >= self.lines.maxlen: self.lines.popleft()
            self.lines.append([x1, y1, x2, y2, text_label,color])

    def drawLines(self, x1, y1, x2, y2, text_label, color):
        """Draw a line between two hosts."""
        # Add the line
        line_id = self.canvas.create_line(x1,y1, x2, y2, fill=color, width=2)

        size = pow((x1 - x2)**2 + (y1-y2)**2, 0.5)
        # Add the label in the middle of the line
        mid_x, mid_y = (x1 + x2) / 2, (y1 + y2) / 2
        angle = math.degrees(math.atan2(y2 - y1, x2 - x1))
        label_id = self.canvas.create_text(
            mid_x, mid_y, text=text_label, fill="blue", font=("Arial", int(np.interp(size, [0, 300], [3, 10]))),
            anchor="center"
        )

        # Add the line and label to the deque
        self.oldLines.append((line_id, label_id, 255))
        if len(self.oldLines) >= self.oldLines.maxlen: 
            (line_id, label_id, alpha) = self.oldLines.popleft()
            self.canvas.delete(line_id)
            self.canvas.delete(label_id)

    def updatePositions(self): 
        for i , host in enumerate(self.hosts): 
            x, y, size= host.pos[0]*self.scale, host.pos[1]*self.scale, host.pos[2]*self.scale

            self.canvas.coords(
                self.host_circles[i],
                x - 5, y - 5, x + 5, y + 5
            )

            # Update the host's label position
            self.canvas.coords(
                self.host_labels[i],
                x + 5, y - 10
            )

            if host.radio.displayRange: 
                r = host.radio.range * self.scale
                self.canvas.coords(
                    self.host_range[i],
                    x - r, y - r, x + r, y + r
                )

    @staticmethod
    def color_from_alpha(alpha: int) -> str:
        """Generate a color string based on the alpha value."""
        blue_intensity = max(0, int(255 * (alpha / 255)))  # Scale blue intensity
        return f"#{blue_intensity:02x}{blue_intensity:02x}ff"  # Blue fading to white

    def update(self, num_update):
        """Update the animation."""
        self.updating = True 
        while len(self.lines): 
            args = self.lines.popleft()
            self.drawLines(*args)
        
        self.updating = False
            
        for i in range(self.oldLines.maxlen):  
            if not len(self.oldLines): break
            (line_id, label_id, alpha) = self.oldLines.popleft()
            alpha -= 30
            if alpha <= 0:
                self.canvas.delete(line_id)
                self.canvas.delete(label_id)
            else:
                # color = self.color_from_alpha(alpha)
                # self.canvas.itemconfig(line_id, fill=color)
                # self.canvas.itemconfig(label_id, fill=color)
                self.oldLines.append((line_id, label_id, alpha))  # Update with new alpha

        self.updatePositions()
        num_update += 1
        
        # Schedule the next frame
        self.root.after(int(1000 * self.timeFactor), self.update, num_update)
        # self.root.after(int(1000 / self.fps), self.update, num_update)
