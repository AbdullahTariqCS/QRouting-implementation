import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation
import numpy as np

# Initialize figure
fig, ax = plt.subplots()
ax.set_xlim(0, 10)
ax.set_ylim(0, 10)
ax.set_aspect('equal')

# List to store lines
lines = []

# Append new line function
def append_line(x1, y1, x2, y2, text_label):
    line, = ax.plot([x1, x2], [y1, y2], color='blue', alpha=1.0)
    # Create the arrow with annotation
    # arrow = ax.annotate("", xy=(x2, y2), xytext=(x1, y1), 
    #             arrowprops=dict(arrowstyle="->", color="blue", lw=2, alpha=1.0))

    # Add text at the midpoint of the line
    mid_x = (x1 + x2) / 2
    mid_y = (y1 + y2 + 1) / 2
    angle = np.arctan2(y2 - y1, x2 - x1) * 180 / np.pi
    text = ax.text(mid_x, mid_y, text_label, color="blue", fontsize=10, ha="center", va="center", alpha=1.0, rotation=angle)

    lines.append((line, text, 1.0))  # Store the lin,e and its initial alpha value

# Update function for animation
def update(frame):
    global lines

    # Gradually fade lines
    for i, (line, text, alpha) in enumerate(lines):
        alpha -= 0.2     # Decrease alpha to fade
        if alpha <= 0:
            line.remove()  # Remove fully faded lines
            lines[i] = None
        else:
            line.set_alpha(alpha)  # Update transparency
            # arrow.set_alpha(alpha)  # Update transparency
            text.set_alpha(alpha)  # Update transparency
            lines[i] = (line,  text, alpha)

    # Remove None entries from the list
    lines = [entry for entry in lines if entry is not None]

    # Append a new line every 20 frames
    if frame % 20 == 0:
        append_line(0, 0, 10, 10, "test")

# Create animation
ani = FuncAnimation(fig, update, frames=200, interval=50)

# Show plot
plt.show()
