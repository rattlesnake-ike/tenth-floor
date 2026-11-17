"""Floor 8: Upside Down. Cartoon physics: low gravity, a lever that throws you onto the ceiling, falling anvils.

  1. Zero-G Lab         shimmering columns where gravity almost lets go: jump in one and you float. Furniture
                        hangs from the ceiling. An anvil drops when you walk under it; watch its shadow.
  2. Upside-Down Room   the floor is lasers and a ShockBot. Search the GRAVITY lever and you fall UP onto the
                        ceiling and walk across it upside down. At the far end, gravity comes back.
  3. Anvil Alley        anvils dropping in turn. The digit is in the locker at the end.

Everything here is in this file: the room bends the player's gravity in update(), before the player moves.
"""
import math

import pygame

from engine import config as C
from engine.kit import Couch, Desk, FilingCabinet, FloorLaser, Locker, Plant, ShockBot, Sign
from engine.room import Furniture, Platform, Room

NAME = "Upside Down"
AUTHOR = "Isaac Holze"

INK = (16, 16, 20)
CEILING = 44                      # where your head is when you stand on the ceiling


def pop(surf, font, text, pos, color):
    """Cartoon lettering: a thick black outline around bright letters."""
    img = font.render(text, True, color)
    out = font.render(text, True, INK)
    r = img.get_rect(center=pos)
    for dx, dy in ((-2, 0), (2, 0), (0, -2), (0, 2), (-2, -2), (2, 2), (-2, 2), (2, -2)):
        surf.blit(out, r.move(dx, dy))
    surf.blit(img, r)


class Anvil:
    """A cartoon anvil. Walk under it and its shadow grows on the floor; a moment later it drops. It only hurts
    while it's falling. Then it sits there, THUD, and floats back up."""

    W, H = 52, 34

    def __init__(self, x, warn=0.5, offset=0.0):
        self.x, self.warn = int(x), warn
        self.mode, self.timer = "up", offset
        self.y = -self.H - 10.0
        self.rect = pygame.Rect(0, 0, 0, 0)
        self.font = pygame.font.Font(None, 30)

    def update(self, dt, room, player):
        self.timer -= dt
        under = abs(player.rect.centerx - (self.x + self.W // 2)) < 46
        if self.mode == "up" and under and self.timer <= 0:
            self.mode, self.timer = "warn", self.warn
        elif self.mode == "warn" and self.timer <= 0:
            self.mode = "fall"
        elif self.mode == "fall":
            self.y += 950 * dt
            if self.y + self.H >= C.FLOOR_Y:
                self.y, self.mode, self.timer = float(C.FLOOR_Y - self.H), "thud", 0.7
        elif self.mode == "thud" and self.timer <= 0:
            self.mode = "rise"
        elif self.mode == "rise":
            self.y -= 300 * dt
            if self.y < -self.H - 10:
                self.mode, self.timer = "up", 0.6
        box = pygame.Rect(self.x, int(self.y), self.W, self.H)
        self.rect = box if self.mode == "fall" else pygame.Rect(0, 0, 0, 0)

    def draw(self, surf):
        if self.mode == "warn":                                     # the shadow, growing
            k = 1 - max(0.0, self.timer) / self.warn
            w = int(20 + 40 * k)
            pygame.draw.ellipse(surf, (20, 20, 30), (self.x + self.W // 2 - w // 2, C.FLOOR_Y - 6, w, 10))
        if self.mode == "up":
            return
        x, y = self.x, int(self.y)
        body = [(x, y + 10), (x + self.W, y + 10), (x + self.W - 10, y + 20), (x + self.W - 14, y + self.H),
                (x + 14, y + self.H), (x + 10, y + 20)]
        pygame.draw.polygon(surf, (70, 72, 82), body)
        pygame.draw.polygon(surf, (70, 72, 82), [(x - 10, y), (x + self.W, y), (x + self.W, y + 10), (x, y + 10)])
        pygame.draw.polygon(surf, INK, body, 3)
        pygame.draw.lines(surf, INK, True, [(x - 10, y), (x + self.W, y), (x + self.W, y + 10), (x, y + 10)], 3)
        pygame.draw.line(surf, (150, 150, 160), (x + 4, y + 3), (x + 30, y + 3), 2)
        if self.mode == "fall":
            for i in range(3):                                       # speed lines
                pygame.draw.line(surf, INK, (x + 8 + i * 16, y - 26), (x + 8 + i * 16, y - 8), 2)
        if self.mode == "thud":
            pop(surf, self.font, "THUD!", (x + self.W // 2, y - 20), (255, 210, 60))


class Lever(Furniture):
    """The GRAVITY lever. Search it and the room's gravity turns upside down. It's ready again straight after."""

    def __init__(self, x, y):
        super().__init__(x, y, 50, 70, "GRAVITY lever")
        self.font = pygame.font.Font(None, 20)
        self.down = False

    def draw(self, surf):
        r = self.rect
        pygame.draw.rect(surf, (230, 60, 60), (r.left, r.bottom - 24, r.width, 24), border_radius=4)
        pygame.draw.rect(surf, INK, (r.left, r.bottom - 24, r.width, 24), 3, border_radius=4)
        end = (r.right - 4, r.bottom - 22) if self.down else (r.left + 6, r.top + 6)
        pygame.draw.line(surf, INK, (r.centerx, r.bottom - 22), end, 5)
        pygame.draw.circle(surf, (255, 220, 60), end, 8)
        pygame.draw.circle(surf, INK, end, 8, 2)
        pop(surf, self.font, "GRAVITY", (r.centerx, r.bottom - 12), (255, 255, 255))


class CartoonRoom(Room):
    """A bright cartoon room (no after-hours dark here) with furniture glued to the ceiling."""

    dark = 0.0
    wall = (120, 200, 230)
    hanging = ()                     # x positions of upside-down furniture on the ceiling

    def draw_background(self, surf):
        surf.fill(self.wall)
        for x in range(0, C.W, 60):                                   # cartoon wallpaper stripes
            pygame.draw.line(surf, tuple(min(255, c + 14) for c in self.wall), (x, 0), (x, C.FLOOR_Y), 18)
        pygame.draw.rect(surf, (240, 220, 120), (0, 0, C.W, 30))     # the "floor" up on the ceiling
        pygame.draw.line(surf, INK, (0, 30), (C.W, 30), 3)
        for i, x in enumerate(self.hanging):                         # a desk and a chair, upside down
            if i % 2 == 0:
                pygame.draw.rect(surf, (170, 110, 60), (x, 30, 90, 12))
                pygame.draw.rect(surf, INK, (x, 30, 90, 12), 2)
                for lx in (x + 8, x + 76):
                    pygame.draw.line(surf, (120, 76, 40), (lx, 42), (lx, 80), 6)
            else:
                pygame.draw.rect(surf, (60, 120, 200), (x, 30, 40, 30), border_radius=4)
                pygame.draw.rect(surf, INK, (x, 30, 40, 30), 2, border_radius=4)
                pygame.draw.line(surf, INK, (x + 20, 60), (x + 20, 90), 4)
        p = getattr(self, "_player", None)
        if p is not None and getattr(self, "flipped", False):        # the player hangs upside down
            p.flipping, p.spin = True, 180.0


class ZeroGLab(CartoonRoom):
    """Columns where gravity almost lets go. Jump in one and you float."""

    title = "Zero-G Lab"
    wall = (120, 200, 230)
    hanging = (120, 300, 600, 760)
    zones = ((240, 360), (520, 640))

    def build(self):
        self.decor.append(Sign(360, 60, "ZERO-G LAB  -  MIND YOUR HEAD", INK, 26))
        self.platforms += [Platform(380, 250, 120), Platform(700, 300, 140)]
        self.furniture += [Couch(110, C.FLOOR_Y), Desk(420, C.FLOOR_Y), Plant(410, 250), FilingCabinet(740, 300)]
        self.hazards.append(Anvil(430, warn=0.5))
        self.big = pygame.font.Font(None, 40)
        self.t = 0.0

    def update(self, dt, player):
        self.t += dt
        self._player = player
        for a, b in self.zones:
            if a < player.rect.centerx < b:
                player.vy -= 0.66 * C.GRAVITY * dt                   # a third of gravity: you float
                player.vy = max(player.vy, -C.JUMP_SPEED * 1.15)

    def draw_foreground(self, surf):
        for a, b in self.zones:                                      # the shimmer
            s = pygame.Surface((b - a, C.FLOOR_Y), pygame.SRCALPHA)
            for y in range(0, C.FLOOR_Y, 24):
                off = int(8 * math.sin(self.t * 4 + y * 0.05))
                pygame.draw.circle(s, (255, 255, 255, 60), ((b - a) // 2 + off, (y - int(self.t * 60)) % C.FLOOR_Y), 5)
            pygame.draw.rect(s, (200, 240, 255, 40), s.get_rect())
            surf.blit(s, (a, 0))
            pop(surf, self.big, "0G", ((a + b) // 2, C.FLOOR_Y - 30), (255, 255, 255))


class UpsideDownRoom(CartoonRoom):
    """The floor is lasers and a ShockBot. Search the GRAVITY lever: you fall up onto the ceiling."""

    title = "Upside-Down Room"
    wall = (240, 150, 190)
    hanging = (300, 470, 640)
    flip_back_x = 840

    def build(self):
        self.decor.append(Sign(330, 170, "PULL LEVER  -  FALL UP", INK, 26))
        self.lever = Lever(100, C.FLOOR_Y)
        self.furniture += [self.lever, Locker(200, C.FLOOR_Y, "upside-down locker"), Plant(880, C.FLOOR_Y)]
        self.hazards += [FloorLaser(230, 520, on_time=1.6, off_time=0.5),
                         FloorLaser(540, 820, on_time=1.6, off_time=0.5, offset=0.8),
                         ShockBot(600, C.FLOOR_Y, left=240, right=830, speed=80)]
        self.flipped = False
        self.big = pygame.font.Font(None, 40)
        self.small = pygame.font.Font(None, 26)

    def update(self, dt, player):
        self._player = player
        if self.lever.searched:                                       # pulled: gravity turns over
            self.lever.searched, self.lever.down = False, True
            self.flipped = True
        if self.flipped and player.rect.centerx > self.flip_back_x:   # GRAVITY RESUMES
            self.flipped, self.lever.down = False, False
            player.flipping, player.spin = True, 0.0
        if self.flipped:
            player.vy -= 2 * C.GRAVITY * dt                            # falls up just as fast as you'd fall down
            if player.y < CEILING:
                player.y, player.vy = float(CEILING), 0.0

    def draw_foreground(self, surf):
        x = self.flip_back_x
        pygame.draw.line(surf, INK, (x, 30), (x, C.FLOOR_Y), 2)
        pop(surf, self.small, "GRAVITY", (x + 58, 70), (255, 255, 255))
        pop(surf, self.small, "RESUMES", (x + 58, 94), (255, 255, 255))
        if self.flipped:
            pop(surf, self.big, "BOING!", (160, 120), (255, 210, 60))


class AnvilAlley(CartoonRoom):
    """Anvils dropping in turn. The digit is in the locker at the end."""

    title = "Anvil Alley"
    wall = (250, 210, 110)
    hanging = (150, 420, 700)

    def build(self):
        self.decor.append(Sign(370, 60, "ANVIL ALLEY  -  LOOK UP", INK, 26))
        self.platforms.append(Platform(700, 410, 170))
        self.furniture += [Desk(120, C.FLOOR_Y), FilingCabinet(560, C.FLOOR_Y),
                           Locker(780, 410, "the last locker", holds_piece=True), Plant(880, C.FLOOR_Y)]
        self.hazards += [Anvil(260, warn=0.45), Anvil(400, warn=0.4, offset=0.3), Anvil(540, warn=0.35, offset=0.6),
                         Anvil(760, warn=0.45)]

    def update(self, dt, player):
        self._player = player


ROOMS = [ZeroGLab, UpsideDownRoom, AnvilAlley]
