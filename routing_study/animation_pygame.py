import pygame
import math
from typing import List, Tuple
from host import Host
from radio import Radio
import threading


class Animation:
    def __init__(self, dim: Tuple[int, int], hosts: List[Host], fps=30):
        pygame.init()
        self.width, self.height = dim
        self.hosts = hosts
        self.fps = fps

        self.screen = pygame.display.set_mode((self.width, self.height))
        pygame.display.set_caption("Host Animation")

        self.clock = pygame.time.Clock()

        self.lines = []

        threading.Thread(target=self.run, daemon=True).start()

    def draw_hosts(self):
        """Draw all the hosts."""
        for host in self.hosts:
            x, y, size = host.pos
            # Draw the host as a circle
            pygame.draw.circle(self.screen, (255, 0, 0), (x, y), 10)
            
            # Draw the host's range if displayRange is enabled
            if host.radio.displayRange:
                pygame.draw.circle(
                    self.screen, 
                    (0, 0, 255), 
                    (x, y), 
                    host.radio.range, 
                    1  # Outline only
                )
            
            # Draw the host ID as a label
            font = pygame.font.Font(None, 20)
            text = font.render(f"Host {host.id}", True, (0, 0, 0))
            self.screen.blit(text, (x + size + 5, y - 10))

    def drawLines(self, A, B): 
        self.lines.append([*A.pos[:-1], *B.pos[:-1], 1.0])

    def draw_lines(self):
        """Draw fading lines between hosts."""
        for line in self.lines[:]:
            x1, y1, x2, y2, alpha = line
            alpha -= 5  # Reduce alpha to create fading effect
            if alpha <= 0:
                self.lines.remove(line)
                continue

            color = (0, 0, 255, alpha)  # Blue with transparency
            pygame.draw.line(self.screen, color[:3], (x1, y1), (x2, y2), 2)

    def add_line(self, host_a: Host, host_b: Host):
        """Add a line between two hosts."""
        x1, y1 = host_a.pos[:2]
        x2, y2 = host_b.pos[:2]
        self.lines.append((x1, y1, x2, y2, 255))  # Start with full opacity


    def run(self):
        """Main animation loop."""
        running = True
        while running:
            self.screen.fill((255, 255, 255))  # Clear the screen with a white background

            # Event handling
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False

            # Draw hosts and lines
            self.draw_hosts()
            self.draw_lines()

            # Refresh the display
            pygame.display.flip()

            # Cap the frame rate
            self.clock.tick(self.fps)

        pygame.quit()

