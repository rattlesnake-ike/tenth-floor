"""Floor 2: Lights Out. The scariest floor in the building.

Four rooms, west to east, almost pitch dark: you see what your flashlight shows you.
  1. Paint Storage    a lamp that keeps failing, a ShockBot on patrol, a drone dropping from the ceiling
  2. Mannequin Room   wooden figure-drawing mannequins that creep toward you whenever you look away
  3. Kiln Room        heat vents in the floor, the kiln press, a platform riding over the vents
  4. The Long Hall    a ShockBot, a Sentry and a guard together; the digit is in a locker up on the ledge.
                      The security terminal by the door freezes them all for 5 seconds. Use it well.
"""
import math
import random

import pygame

from engine import config as C
from engine.kit import (Bookshelf, CeilingLight, Crusher, Drone, Easel, FilingCabinet, FloorLaser, Locker,
                        MovingPlatform, PatrolBot, Plinth, Poster, SecurityTerminal, Sentry, ShockBot, Sign, Zapper)
from engine.room import Platform, Room

NAME = "Lights Out"
AUTHOR = "Isaac Holze"


class Mannequin:
    """A wooden figure-drawing mannequin. It only moves when you're facing away from it. Look at it, and it stops.
    It creeps along its own stretch of floor (left..right); touch it and you're caught."""

    W, H = 24, 54

    def __init__(self, x, left, right, speed=62.0):
        self.x, self.left, self.right, self.speed = float(x), int(left), int(right), float(speed)
        self.dir = -1
        self.moving = False
        self.rect = pygame.Rect(int(x), C.FLOOR_Y - self.H, self.W, self.H)
        self.lean = 0.0

    def update(self, dt, room, player):
        dx = player.rect.centerx - self.rect.centerx
        watched = dx * player.facing < 0                          # you face toward it
        near_level = abs(player.rect.bottom - C.FLOOR_Y) < 130
        self.moving = (not watched) and near_level and abs(dx) > 4
        if self.moving:
            self.dir = 1 if dx > 0 else -1
            self.x += self.dir * self.speed * dt
            self.x = max(float(self.left), min(float(self.right - self.W), self.x))
        self.lean += ((6 * self.dir if self.moving else 0) - self.lean) * min(1.0, dt * 8)
        self.rect.x = int(self.x)

    def draw(self, surf):
        r = self.rect
        wood, dark = (196, 160, 112), (120, 92, 60)
        cx = r.centerx + int(self.lean * 0.5)
        pygame.draw.line(surf, dark, (r.centerx, r.bottom), (r.centerx, r.bottom - 6), 3)          # the stand
        pygame.draw.line(surf, dark, (r.centerx - 8, r.bottom), (r.centerx + 8, r.bottom), 3)
        hip, neck = (cx, r.top + 30), (cx + int(self.lean * 0.4), r.top + 12)
        for side in (-1, 1):                                                                        # jointed legs
            knee = (hip[0] + side * 4, hip[1] + 10)
            pygame.draw.line(surf, wood, hip, knee, 4)
            pygame.draw.line(surf, wood, knee, (hip[0] + side * 3, r.bottom - 6), 4)
            pygame.draw.circle(surf, dark, knee, 2)
        pygame.draw.line(surf, wood, hip, neck, 6)                                                  # torso
        reach = 10 if self.moving else 4                                                            # arms reach when it moves
        for side in (-1, 1):
            elbow = (neck[0] + side * 6 + self.dir * reach // 2, neck[1] + 8)
            pygame.draw.line(surf, wood, (neck[0], neck[1] + 2), elbow, 3)
            pygame.draw.line(surf, wood, elbow, (elbow[0] + self.dir * reach, elbow[1] + 4), 3)
        pygame.draw.ellipse(surf, wood, (neck[0] - 6, neck[1] - 14, 12, 15))                         # the blank head


class _Flicker(Room):
    """A room whose lamps fail now and then: the dark comes and goes."""

    base_dark = 0.9

    def update(self, dt, player):
        self.t = getattr(self, "t", 0.0) + dt
        rnd = random.Random(int(self.t * 9))
        out = rnd.random() < 0.18
        self.dark = 0.985 if out else self.base_dark
        if not hasattr(self, "_lamps"):
            self._lamps = [d for d in self.decor if isinstance(d, CeilingLight)]
        rest = [d for d in self.decor if not isinstance(d, CeilingLight)]
        self.decor = rest if out else rest + self._lamps          # a failing lamp is really off

    def draw_background(self, surf):
        surf.fill((22, 22, 30))
        for x in range(0, C.W, 48):
            pygame.draw.line(surf, (28, 28, 38), (x, 0), (x, C.FLOOR_Y), 1)
        rnd = random.Random(3)
        for _ in range(40):                                                   # stains on the wall
            pygame.draw.circle(surf, (30, 26, 32), (rnd.randrange(C.W), rnd.randrange(60, C.FLOOR_Y)), rnd.randrange(4, 18))


class PaintStorage(_Flicker):
    """A lamp that keeps failing, a ShockBot on patrol, a drone dropping from the ceiling."""

    title = "Paint Storage"
    base_dark = 0.9

    def build(self):
        self.decor += [CeilingLight(470, reach=360), Sign(330, 46, "PAINT STORAGE  -  KEEP CLOSED", (150, 140, 140), 24),
                       Poster(120, 90, "TOXIC", (150, 60, 50))]
        self.platforms += [Platform(200, 420, 120), Platform(380, 340, 140)]
        self.furniture += [FilingCabinet(130, C.FLOOR_Y, "paint cabinet"), Bookshelf(410, 340, "solvent shelf"),
                           Easel(580, C.FLOOR_Y), Locker(760, C.FLOOR_Y, "drop cloth locker")]
        self.hazards += [ShockBot(560, C.FLOOR_Y, left=300, right=860, speed=70),
                         Drone(690, y_top=200, y_bottom=C.FLOOR_Y, speed=120)]


class MannequinRoom(_Flicker):
    """They move when you look away. Walk backwards, or run."""

    title = "Mannequin Room"
    base_dark = 0.94

    def build(self):
        self.decor += [Sign(300, 46, "FIGURE DRAWING  -  LIFE ROOM B", (150, 140, 140), 24)]
        self.lights = [(480, 120, 60)]
        self.furniture += [Plinth(140, C.FLOOR_Y, "model stand"), Easel(300, C.FLOOR_Y), Easel(560, C.FLOOR_Y),
                           Plinth(720, C.FLOOR_Y, "model stand")]
        self.hazards += [Mannequin(250, left=120, right=470), Mannequin(620, left=360, right=860),
                         Mannequin(800, left=520, right=860),
                         Zapper(470, y_top=290, on_time=0.9, off_time=1.2)]


class KilnRoom(Room):
    """Heat vents in the floor, the kiln press, a platform riding over the vents. Only the kiln gives light."""

    title = "Kiln Room"
    dark = 0.9

    def build(self):
        self.decor += [Sign(380, 46, "CERAMICS  -  KILN ROOM", (170, 140, 120), 24)]
        self.platforms += [MovingPlatform(160, 440, 410, width=110, speed=80), Platform(600, 330, 180)]
        self.furniture += [Plinth(120, C.FLOOR_Y, "drying pots"), FilingCabinet(640, 330, "glaze shelf"),
                           Plinth(720, 330, "bisque ware"), Locker(860, C.FLOOR_Y, "apron locker")]
        self.hazards += [FloorLaser(170, 560, on_time=1.0, off_time=1.3),
                         Crusher(680, y_top=150, y_bottom=330, w=60, h=40),
                         Zapper(800, y_top=300, on_time=1.0, off_time=1.0, offset=0.5)]

    def update(self, dt, player):
        self.t = getattr(self, "t", 0.0) + dt
        glow = 90 + int(14 * math.sin(self.t * 5) + 8 * math.sin(self.t * 13))
        self.lights = [(640, 450, glow)]

    def draw_background(self, surf):
        surf.fill((30, 20, 18))
        pygame.draw.rect(surf, (60, 40, 32), (560, 380, 160, 120), border_radius=8)                # the kiln
        pygame.draw.rect(surf, (230, 120, 40), (600, 420, 80, 50), border_radius=4)
        pygame.draw.rect(surf, (255, 190, 90), (612, 432, 56, 26), border_radius=3)


class LongHall(_Flicker):
    """Three kinds of security at once. The terminal by the door buys you five seconds."""

    title = "The Long Hall"
    base_dark = 0.9

    def build(self):
        self.decor += [CeilingLight(260, reach=360), CeilingLight(700, reach=360),
                       Sign(360, 46, "EXIT  -->  EAST ELEVATOR", (200, 80, 70), 24)]
        terminal = SecurityTerminal(110, C.FLOOR_Y)
        self.furniture += [terminal, FilingCabinet(320, C.FLOOR_Y, "lost and found"),
                           Locker(800, 320, "the last locker", holds_piece=True), Easel(470, C.FLOOR_Y)]
        self.hazards.append(terminal.control)
        self.platforms += [Platform(580, 410, 140), Platform(740, 320, 160)]
        self.hazards += [ShockBot(420, C.FLOOR_Y, left=220, right=560, speed=65),
                         Sentry(640, C.FLOOR_Y, left=560, right=870),
                         PatrolBot(760, 320, left=740, right=900, speed=55, sees=False)]


ROOMS = [PaintStorage, MannequinRoom, KilnRoom, LongHall]
