"""Example floor: a render farm, then a crit room.

Copy this file to floors/<your_name>.py and make it yours. This floor is two rooms side by side: you come
off the WEST elevator into the LEFT room, walk through into the RIGHT room, and get on the EAST elevator.
A floor can have up to 5 rooms: see floors/example_kit_floor.py, which also uses the kit (KIT.md).
Exactly ONE piece of furniture on the floor hides your floor's digit of the door code (here, rack D).
"""
import math

import pygame

from engine import config as C
from engine.bots import PatrolBot, Zapper
from engine.room import Furniture, Lift, Platform, Room

NAME = "Test Floor"
AUTHOR = "Test"


# --- LEFT room: the West elevator is through its left edge ---

class ServerRack(Furniture):
    """Furniture with its own look: blinking lights. Keep self.rect as the part you search."""

    def draw(self, surf):
        r = self.rect
        pygame.draw.rect(surf, (36, 38, 46) if not self.searched else (60, 60, 64), r, border_radius=2)
        pygame.draw.rect(surf, C.INK, r, 2, border_radius=2)
        t = pygame.time.get_ticks() / 1000.0
        for i, y in enumerate(range(r.top + 8, r.bottom - 6, 10)):
            on = math.sin(t * 3 + i * 1.7 + r.x) > 0
            pygame.draw.line(surf, (70, 72, 84), (r.left + 6, y), (r.right - 16, y), 2)
            pygame.draw.circle(surf, (90, 230, 120) if on else (40, 80, 50), (r.right - 9, y), 2)


class RenderFarm(Room):
    title = "Render Farm"

    def build(self):
        # Two ledges and a lift up to the high shelf.
        self.platforms.append(Platform(120, 390, 230))
        self.platforms.append(Platform(560, 280, 300))
        self.lifts.append(Lift(470, y_top=280, y_bottom=C.FLOOR_Y, width=70))

        self.furniture.append(ServerRack(160, 390, 50, 70, "rack A"))
        self.furniture.append(ServerRack(260, 390, 50, 70, "rack B"))
        self.furniture.append(ServerRack(620, 280, 50, 90, "rack C"))
        self.furniture.append(ServerRack(760, 280, 50, 90, "rack D", holds_piece=True))
        self.furniture.append(Furniture(820, C.FLOOR_Y, 90, 40, "cable crate"))

        self.hazards.append(PatrolBot(300, C.FLOOR_Y, left=240, right=840, speed=80))
        self.hazards.append(PatrolBot(700, 280, left=600, right=860, speed=60, sees=False))
        # Make fonts and text once, here, never in a draw function: they are slow to build.
        self.sign = pygame.font.Font(None, 28).render("RENDER FARM - DO NOT POWER OFF", True, (120, 200, 255))

    def draw_background(self, surf):
        surf.fill((28, 32, 44))
        for x in range(30, C.W, 90):              # cold-aisle floor vents
            pygame.draw.rect(surf, (36, 42, 58), (x, 60, 60, 300), border_radius=4)
        surf.blit(self.sign, (C.W // 2 - self.sign.get_width() // 2, 40))


# --- RIGHT room: the East elevator is through its right edge ---

class SweepBeam:
    """A hazard of your own: anything with .rect, .update(dt, room, player) and .draw(surf)."""

    def __init__(self, y, left, right, speed):
        self.y, self.left, self.right, self.speed = y, left, right, speed
        self.x = float(left)
        self.dir = 1
        self.rect = pygame.Rect(left, y, 24, 24)
        self.glow = pygame.Surface((80, 80), pygame.SRCALPHA)     # made once, not every frame
        pygame.draw.circle(self.glow, (255, 240, 180, 60), (40, 40), 38)

    def update(self, dt, room, player):
        self.x += self.dir * self.speed * dt
        if self.x < self.left or self.x > self.right:
            self.dir *= -1
            self.x = max(self.left, min(self.right, self.x))
        self.rect.x = int(self.x)

    def draw(self, surf):
        surf.blit(self.glow, (self.rect.centerx - 40, self.rect.centery - 40))
        pygame.draw.circle(surf, (255, 240, 180), self.rect.center, 12)


class CritRoom(Room):
    title = "Crit Room"

    def build(self):
        self.platforms.append(Platform(80, 410, 200))
        self.platforms.append(Platform(330, 330, 180))
        self.platforms.append(Platform(570, 250, 200))
        self.furniture.append(Furniture(110, 410, 70, 36, "flat file"))
        self.furniture.append(Furniture(380, 330, 60, 50, "easel"))
        self.furniture.append(Furniture(640, 250, 80, 40, "projector cart"))
        self.furniture.append(Furniture(520, C.FLOOR_Y, 120, 30, "pin-up bench"))
        self.hazards.append(Zapper(300, y_top=340, y_bottom=C.FLOOR_Y, on_time=1.2, off_time=1.8))
        self.hazards.append(Zapper(820, y_top=340, y_bottom=C.FLOOR_Y, on_time=1.2, off_time=1.8, offset=1.5))
        self.hazards.append(SweepBeam(200, left=560, right=900, speed=140))

    def draw_background(self, surf):
        surf.fill((58, 54, 52))
        for i, x in enumerate(range(60, C.W, 150)):   # pinned-up work on the wall
            col = [(200, 120, 90), (90, 150, 190), (220, 200, 120), (140, 180, 120)][i % 4]
            pygame.draw.rect(surf, col, (x, 70, 90, 120))
            pygame.draw.rect(surf, (30, 30, 30), (x, 70, 90, 120), 2)


LEFT = RenderFarm      # off the West elevator
RIGHT = CritRoom       # on to the East elevator
