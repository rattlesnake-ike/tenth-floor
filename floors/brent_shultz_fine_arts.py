"""MFA Fine Arts, 9th floor: three studios, and each one has a job to finish before its door opens.

West elevator -> Painting Studio -> Sculpture Studio -> Fabrication Lab -> East elevator.

  Painting Studio   Dump every paint bucket: climb to each one and hold UP in front of it. The paint pours
                    onto the drop cloth below. When all four are dumped, the door opens.
  Sculpture Studio  Throw clay at the armature on the stand (F or E throws, the way you face). The clay sticks
                    and builds up a sculpture. Once there are at least 8 lumps on it, you decide when it's
                    finished: hold UP at the stand to sign it, and the door opens.
  Fabrication Lab   Start the human-size 3D printer (hold UP in front of it). It prints a copy of you, layer
                    by layer, and the door opens when the print is done. The floor's digit is in the printer.

The backgrounds are photos of real gallery spaces, with the game drawn over them in flat cutout style.
Coming in from the East elevator, every door is already open, so the floor can be crossed both ways.

Practise it alone with: python main.py --floor brent_shultz_fine_arts
"""
import math
import os
import random

import pygame

from engine import config as C
from engine.kit import CeilingLight, Crusher, Drone, Easel, FilingCabinet, PatrolBot, Plinth, Printer3D, ShockBot, Sign
from engine.player import Player
from engine.room import Furniture, Platform, Room

NAME = "MFA Fine Arts"
AUTHOR = "Brent Shultz"

INK = C.INK
ASSETS = os.path.join(os.path.dirname(os.path.abspath(__file__)), "brent_shultz_fine_arts_assets")
GATE_X = C.W - 70              # while a door is shut, you can't get past here

_CACHE = {}


def font(size):
    key = ("font", size)
    if key not in _CACHE:
        if not pygame.font.get_init():
            pygame.font.init()
        _CACHE[key] = pygame.font.Font(None, size)
    return _CACHE[key]


def label(text, size=22, color=(250, 248, 240)):
    """Rendered text, made once per string and kept."""
    key = ("label", text, size, color)
    if key not in _CACHE:
        _CACHE[key] = font(size).render(text, True, color)
    return _CACHE[key]


def backdrop(name):
    """The room's photo, stretched to fill the wall and dimmed for night, loaded once for the whole game."""
    key = ("bg", name)
    if key not in _CACHE:
        img = pygame.image.load(os.path.join(ASSETS, name))
        w, h = img.get_size()
        k = max(C.W / w, C.FLOOR_Y / h)
        img = pygame.transform.smoothscale(img, (int(w * k) + 1, int(h * k) + 1))
        out = pygame.Surface((C.W, C.FLOOR_Y))
        out.blit(img, ((C.W - img.get_width()) // 2, (C.FLOOR_Y - img.get_height()) // 2))
        night = pygame.Surface((C.W, C.FLOOR_Y), pygame.SRCALPHA)
        night.fill((10, 12, 30, 95))
        out.blit(night, (0, 0))
        _CACHE[key] = out
    return _CACHE[key]


def you_statue(scale=2.6):
    """The player character, drawn once off screen and blown up: what the 3D printer prints."""
    key = ("statue", scale)
    if key not in _CACHE:
        surf = pygame.Surface((80, 80), pygame.SRCALPHA)
        p = Player(29, 70)
        p.safe = 0.0
        p.on = True                     # standing, not mid-air
        p.draw(surf)
        box = surf.get_bounding_rect()
        fig = surf.subsurface(box).copy()
        fig = pygame.transform.scale(fig, (int(box.w * scale), int(box.h * scale)))
        lines = pygame.Surface(fig.get_size(), pygame.SRCALPHA)   # print layer lines, only on the figure itself
        lines.fill((255, 255, 255, 255))
        for y in range(0, fig.get_height(), 4):
            pygame.draw.line(lines, (205, 205, 205, 255), (0, y), (fig.get_width(), y), 1)
        fig.blit(lines, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)
        fig.fill((95, 85, 70), special_flags=pygame.BLEND_RGB_ADD)      # lighter, like printed filament
        _CACHE[key] = fig
    return _CACHE[key]


def cutout(surf, rect, color, radius=6):
    """Flat colour with a thick dark outline: the paper-cutout look over the photos."""
    pygame.draw.rect(surf, color, rect, border_radius=radius)
    pygame.draw.rect(surf, INK, rect, 3, border_radius=radius)


# --- the door each studio opens when its job is done ---------------------------------------------------------

class Studio(Room):
    """A room with a job. Subclasses say how far along it is (progress) and when it's done."""

    photo = "painting.jpg"

    def build(self):
        self.bg = backdrop(self.photo)
        self.first = True
        self.from_east = False
        self.layout()

    def layout(self):
        raise NotImplementedError

    def job_done(self):
        return False

    def task(self):
        """(short task text, progress text)"""
        return "", ""

    def door_open(self):
        return self.from_east or self.job_done()

    def update(self, dt, player):
        if player is None:
            return
        if self.first:                                   # came in from the east: the door behind you is open
            self.first = False
            self.from_east = player.rect.centerx > C.W // 2
            self.arrive()
        self.job(dt, player)
        if not self.door_open() and player.x + player.W > GATE_X:
            player.x = float(GATE_X - player.W)
            player.vx = 0.0

    def arrive(self):
        """First frame in the room, after the engine has copied back what was already searched."""

    def job(self, dt, player):
        pass

    def draw_background(self, surf):
        surf.blit(self.bg, (0, 0))

    def draw_foreground(self, surf):
        self.draw_job(surf)
        door = pygame.Rect(GATE_X + 6, C.FLOOR_Y - 120, 50, 120)
        if self.door_open():
            pygame.draw.rect(surf, (30, 30, 36), door)
            pygame.draw.polygon(surf, (150, 110, 70), [door.topright, (door.right + 10, door.top + 8),
                                                        (door.right + 10, door.bottom), door.bottomright])
            pygame.draw.rect(surf, INK, door, 3)
        else:
            cutout(surf, door, (150, 110, 70), 2)
            pygame.draw.circle(surf, (230, 200, 90), (door.left + 9, door.centery), 4)
            text, prog = self.task()
            tag = label(prog, 24, INK)
            plate = pygame.Rect(0, 0, max(tag.get_width() + 12, 44), 26)
            plate.midbottom = (door.centerx, door.top - 4)
            cutout(surf, plate, (250, 236, 120), 4)
            surf.blit(tag, (plate.centerx - tag.get_width() // 2, plate.top + 5))
            hint = label(text, 24)
            box = pygame.Rect(0, 0, hint.get_width() + 20, hint.get_height() + 10)
            box.midtop = (C.W // 2, 74)
            cutout(surf, box, (30, 30, 40), 8)
            surf.blit(hint, (box.left + 10, box.top + 5))

    def draw_job(self, surf):
        pass


# --- room 1: painting -----------------------------------------------------------------------------------------

class PaintBucket(Furniture):
    """A bucket of paint. 'Searching' it tips it over the edge: the paint pours down onto the drop cloth."""

    def __init__(self, x, y, color):
        super().__init__(x, y, 34, 36, "paint bucket")
        self.color = color
        self.pour = 0.0                     # seconds since it was dumped (for the pour)

    def draw(self, surf):
        r = self.rect
        if not self.searched:
            body = [(r.left + 3, r.top + 6), (r.right - 3, r.top + 6), (r.right - 6, r.bottom), (r.left + 6, r.bottom)]
            pygame.draw.polygon(surf, (220, 220, 226), body)
            pygame.draw.polygon(surf, INK, body, 3)
            pygame.draw.ellipse(surf, self.color, (r.left + 3, r.top + 2, r.w - 6, 9))
            pygame.draw.ellipse(surf, INK, (r.left + 3, r.top + 2, r.w - 6, 9), 2)
            pygame.draw.arc(surf, INK, (r.left + 5, r.top - 8, r.w - 10, 18), 0.2, math.pi - 0.2, 2)
            pygame.draw.rect(surf, self.color, (r.left + 9, r.top + 16, r.w - 18, 10))
        else:                               # on its side, empty, a drip down the front
            side = pygame.Rect(r.left, r.bottom - 22, 36, 22)
            pygame.draw.rect(surf, (200, 200, 206), side, border_radius=4)
            pygame.draw.rect(surf, INK, side, 3, border_radius=4)
            pygame.draw.ellipse(surf, self.color, (side.right - 8, side.top + 2, 10, 18))
            pygame.draw.line(surf, self.color, (side.right, side.bottom), (side.right + 3, side.bottom + 8), 4)


class PaintingStudio(Studio):
    """Four buckets on four ledges. Dump them all onto the drop cloth to open the door."""

    title = "Painting Studio"
    photo = "painting.jpg"

    def layout(self):
        self.decor += [Sign(330, 34, "9  MFA FINE ARTS  -  PAINTING", (255, 255, 255), size=26), CeilingLight(260, cord=30),
                       CeilingLight(700, cord=30)]
        self.platforms += [Platform(150, 400, 160), Platform(380, 310, 170), Platform(560, 220, 140),
                           Platform(690, 400, 160)]
        colors = [(220, 60, 60), (60, 120, 220), (240, 200, 50), (60, 170, 90)]
        self.buckets = [PaintBucket(200, 400, colors[0]), PaintBucket(445, 310, colors[1]),
                        PaintBucket(610, 220, colors[2]), PaintBucket(760, 400, colors[3])]
        self.furniture += self.buckets + [Easel(120, C.FLOOR_Y, name="easel")]
        rng = random.Random(9)
        self.splats = []                    # where each bucket's paint lands on the drop cloth
        for b in self.buckets:
            cx = b.rect.centerx + 30
            self.splats.append([(cx + rng.randint(-40, 40), C.FLOOR_Y + rng.randint(4, 22), rng.randint(5, 14))
                                for _ in range(12)])
        self.hazards.append(PatrolBot(420, C.FLOOR_Y, left=180, right=820, speed=75))
        self.hazards.append(Drone(530, y_top=110, y_bottom=290, speed=60))

    def job_done(self):
        return all(b.searched for b in self.buckets)

    def task(self):
        n = sum(b.searched for b in self.buckets)
        return "Dump every paint bucket (hold UP at each one)", f"{n}/{len(self.buckets)}"

    def arrive(self):
        for b in self.buckets:              # dumped on an earlier visit: just show the paint on the cloth
            if b.searched:
                b.pour = 99.0

    def job(self, dt, player):
        for b in self.buckets:
            if b.searched:
                b.pour += dt

    def draw_job(self, surf):
        cloth = pygame.Rect(90, C.FLOOR_Y + 2, C.W - 220, 30)          # the drop cloth on the floor
        pygame.draw.rect(surf, (226, 218, 196), cloth)
        pygame.draw.rect(surf, INK, cloth, 2)
        for b, splat in zip(self.buckets, self.splats):
            if not b.searched:
                continue
            stream = min(1.0, b.pour / 0.5)                              # the paint falls, then lands
            if b.pour < 1.6:
                x = b.rect.right + 4
                y0 = b.rect.bottom - 4
                pygame.draw.line(surf, b.color, (x, y0), (x + 6, y0 + (C.FLOOR_Y + 10 - y0) * stream), 7)
            if b.pour > 0.4:
                for sx, sy, rad in splat:
                    pygame.draw.circle(surf, b.color, (sx, sy), rad)
            if b.pour < 1.2:
                pop = label("SPLASH!", 30, b.color)
                surf.blit(pop, (b.rect.centerx - pop.get_width() // 2, b.rect.top - 34))


# --- room 2: sculpture ----------------------------------------------------------------------------------------

CLAY = []           # lumps stuck to the armature: (dx, dy, radius, colour), kept while the game runs
MIN_LUMPS = 8
CLAY_COLORS = [(176, 110, 76), (160, 98, 66), (190, 124, 88), (150, 92, 62)]


class SculptureStand(Furniture):
    """The stand with the wire armature. Clay sticks to it; hold UP here to sign the finished work."""

    def __init__(self, x, y):
        super().__init__(x, y, 120, 40, "sculpture stand")
        self.arm = pygame.Rect(self.rect.centerx - 30, self.rect.top - 150, 60, 150)   # where clay sticks

    def draw(self, surf):
        r = self.rect
        cutout(surf, r, (232, 230, 222), 3)
        a = self.arm
        cx, top = a.centerx, a.top
        wire = (90, 90, 96)                                            # the armature: a wire figure
        pygame.draw.line(surf, wire, (cx, r.top), (cx, top + 20), 4)
        pygame.draw.circle(surf, wire, (cx, top + 12), 11, 3)
        pygame.draw.line(surf, wire, (cx - 26, top + 40), (cx + 26, top + 34), 3)
        pygame.draw.line(surf, wire, (cx, top + 90), (cx - 16, r.top), 3)
        pygame.draw.line(surf, wire, (cx, top + 90), (cx + 18, r.top), 3)
        for dx, dy, rad, col in CLAY:
            p = (cx + dx, top + dy)
            pygame.draw.circle(surf, shade(col, 0.7), (p[0] + 1, p[1] + 2), rad)
            pygame.draw.circle(surf, col, p, rad)
        if self.searched and len(CLAY) >= MIN_LUMPS:
            card = label("\"Untitled (Clay)\" - signed", 20, INK)
            plate = pygame.Rect(0, 0, card.get_width() + 10, 20)
            plate.midtop = (r.centerx, r.top + 10)
            pygame.draw.rect(surf, (250, 240, 200), plate)
            surf.blit(card, (plate.left + 5, plate.top + 3))


def shade(col, k):
    return tuple(max(0, min(255, int(c * k))) for c in col)


class Lump:
    """A thrown lump of clay, flying in an arc."""

    G = 900.0

    def __init__(self, x, y, facing):
        self.x, self.y = float(x), float(y)
        self.vx, self.vy = 470.0 * facing, -280.0
        self.col = random.choice(CLAY_COLORS)
        self.splat = 0.0                # > 0 once it has hit the floor

    def update(self, dt):
        if self.splat:
            self.splat += dt
            return
        self.vy += self.G * dt
        self.x += self.vx * dt
        self.y += self.vy * dt
        if self.y >= C.FLOOR_Y - 3:
            self.y, self.splat = C.FLOOR_Y - 3, 0.001


class SculptureStudio(Studio):
    """Throw clay at the armature (F or E) until it's a sculpture, then sign it at the stand."""

    title = "Sculpture Studio"
    photo = "sculpture.jpg"

    def layout(self):
        self.decor += [Sign(60, 34, "SCULPTURE STUDIO", (255, 255, 255), size=28), CeilingLight(470, cord=30)]
        self.stand = SculptureStand(410, C.FLOOR_Y)
        self.platforms.append(Platform(620, 400, 200))
        self.furniture += [self.stand, Plinth(170, C.FLOOR_Y, name="plinth"),
                           Plinth(300, C.FLOOR_Y, name="plinth", colors=((200, 90, 70), (230, 230, 230))),
                           FilingCabinet(720, 400, name="tool cabinet")]
        self.lumps = []
        self.cool = 0.0
        self.throw_was = False
        self.hazards.append(ShockBot(700, C.FLOOR_Y, left=580, right=860))

    def job_done(self):
        return self.stand.searched and len(CLAY) >= MIN_LUMPS

    def task(self):
        if len(CLAY) < MIN_LUMPS:
            return "Throw clay at the armature: F or E", f"{len(CLAY)}/{MIN_LUMPS}"
        return "Done? Hold UP at the stand to sign it", "SIGN"

    def job(self, dt, player):
        self.cool = max(0.0, self.cool - dt)
        keys = pygame.key.get_pressed()
        throw = keys[pygame.K_f] or keys[pygame.K_e]
        if throw and not self.throw_was and self.cool == 0 and len(self.lumps) < 8:
            r = player.rect
            self.lumps.append(Lump(r.centerx + player.facing * 12, r.top + 14, player.facing))
            self.cool = 0.25
        self.throw_was = throw
        arm = self.stand.arm
        for lump in self.lumps:
            lump.update(dt)
            if not lump.splat and arm.collidepoint(int(lump.x), int(lump.y)) and len(CLAY) < 60:
                CLAY.append((int(lump.x) - arm.centerx, int(lump.y) - arm.top, random.randint(7, 11), lump.col))
                lump.splat = 99.0                 # stuck: gone from the air
        self.lumps = [l for l in self.lumps if l.splat < 0.8 and -40 < l.x < C.W + 40]

    def draw_job(self, surf):
        for lump in self.lumps:
            if lump.splat:
                pygame.draw.ellipse(surf, lump.col, (int(lump.x) - 10, C.FLOOR_Y - 5, 20, 6))
            else:
                pygame.draw.circle(surf, lump.col, (int(lump.x), int(lump.y)), 7)
                pygame.draw.circle(surf, INK, (int(lump.x), int(lump.y)), 7, 2)


# --- room 3: fabrication --------------------------------------------------------------------------------------

class BigPrinter(Furniture):
    """A human-size 3D printer. Start it (hold UP) and it prints you. The floor's digit is in here."""

    PRINT_TIME = 5.0

    def __init__(self, x, y):
        super().__init__(x, y, 130, 190, "human-size 3D printer", holds_piece=True)
        self.t = None                       # seconds into the print, None = not started

    def printed(self):
        if self.t is None:
            return 1.0 if self.searched else 0.0
        return min(1.0, self.t / self.PRINT_TIME)

    def draw(self, surf):
        r = self.rect
        frame = (200, 200, 210)
        bed = pygame.Rect(r.left + 10, r.bottom - 14, r.w - 20, 10)
        for x in (r.left + 4, r.right - 12):                              # the posts and gantry
            cutout(surf, pygame.Rect(x, r.top, 8, r.h), frame, 2)
        cutout(surf, pygame.Rect(r.left, r.top, r.w, 12), frame, 2)
        cutout(surf, bed, (90, 90, 100), 2)
        statue = you_statue()
        p = self.printed()
        shown = int(statue.get_height() * p)
        sx = r.centerx - statue.get_width() // 2
        sy = bed.top - statue.get_height()
        if shown > 0:                                                      # reveal it bottom up
            part = statue.subsurface((0, statue.get_height() - shown, statue.get_width(), shown))
            surf.blit(part, (sx, bed.top - shown))
        if 0 < p < 1:
            ny = bed.top - shown - 6
            nx = r.left + 16 + int((r.w - 40) * (0.5 + 0.5 * math.sin((self.t or 0) * 9)))
            pygame.draw.line(surf, frame, (nx + 6, r.top + 12), (nx + 6, ny), 3)
            cutout(surf, pygame.Rect(nx, ny - 4, 14, 10), (240, 120, 60), 2)
            pygame.draw.circle(surf, (255, 200, 120), (nx + 7, ny + 7), 3)
        if p == 0:
            tag = label("START", 22, INK)
            plate = pygame.Rect(0, 0, tag.get_width() + 12, 22)
            plate.center = (r.centerx, sy + statue.get_height() // 2)
            cutout(surf, plate, (120, 220, 130), 4)
            surf.blit(tag, (plate.left + 6, plate.top + 4))


class FabricationLab(Studio):
    """Start the human-size printer and wait for it to print you before the East door opens."""

    title = "Fabrication Lab"
    photo = "fabrication.jpg"

    def layout(self):
        self.decor += [Sign(60, 34, "FABRICATION LAB", (255, 255, 255), size=28), CeilingLight(470, cord=30)]
        self.printer = BigPrinter(400, C.FLOOR_Y)
        self.platforms.append(Platform(130, 390, 170))
        self.furniture += [self.printer, Printer3D(170, 390, name="desktop printer"),
                           FilingCabinet(640, C.FLOOR_Y, name="filament cabinet"),
                           Printer3D(740, C.FLOOR_Y, name="resin printer")]
        self.hazards.append(Crusher(300, y_top=200, y_bottom=C.FLOOR_Y, w=60, h=50))
        self.hazards.append(ShockBot(760, C.FLOOR_Y, left=600, right=860))

    def job_done(self):
        return self.printer.printed() >= 1.0

    def task(self):
        if not self.printer.searched:
            return "Start the 3D printer (hold UP in front of it)", "PRINT"
        return "Printing you...", f"{int(self.printer.printed() * 100)}%"

    def arrive(self):
        self.printed_before = self.printer.searched     # printed on an earlier visit: it's already standing there

    def job(self, dt, player):
        pr = self.printer
        if pr.searched and pr.t is None and not self.printed_before:
            pr.t = 0.0                                   # you just started it
        elif pr.t is not None:
            pr.t += dt


ROOMS = [PaintingStudio, SculptureStudio, FabricationLab]
