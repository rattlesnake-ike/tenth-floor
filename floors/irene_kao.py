"""5th Floor Comics: a bullpen, an ink room, and a gallery.

Three rooms side by side. You come off the WEST elevator into the Bullpen, walk east through the Ink Room
into the Gallery, and get on the EAST elevator. The digit of the door code is on the "original page" plinth
at the top of the Ink Room's ledges.

The villains are the kit's patrol bots and crushers in comic-book costumes. When one catches you, you freeze,
POW! and BAM! pop up around you, and then the engine sends you back.
"""
import math

import pygame

from engine import config as C
from engine.kit import Bookshelf, CeilingLight, Couch, Crusher, Easel, FilingCabinet, PatrolBot, Plinth
from engine.room import Furniture, Platform, Room

NAME = "5th Floor Comics"              # the name on the elevator panel
AUTHOR = "Irene Kao"                   # your name

INK = (14, 14, 18)                     # the black of inked comic linework
PAPER = (250, 240, 220)                # speech-balloon paper and drawing paper
WHITE = (255, 255, 255)
YELLOW = (255, 214, 40)
ORANGE = (255, 110, 50)
RED = (226, 48, 48)
CYAN = (80, 200, 255)
MINT = (150, 240, 200)
GOLD = (255, 200, 80)
WOOD = (150, 98, 56)
WOOD_LIGHT = (184, 130, 80)
WOOD_DARK = (96, 60, 34)
METAL = (70, 72, 84)

# Each room has its own palette: a wall colour, its halftone dots, and the colour of its title box.
BULLPEN = {"wall": (24, 46, 110), "dots": (44, 84, 170), "title": YELLOW}
INK_ROOM = {"wall": (14, 66, 70), "dots": (30, 110, 104), "title": MINT}
GALLERY = {"wall": (92, 24, 72), "dots": (140, 50, 110), "title": GOLD}


def comic_wall(palette):
    """A halftone comic wall with a shaded vignette, a baseboard and an ink frame. Built once in build(),
    then blitted every frame."""
    surf = pygame.Surface((C.W, C.H))
    surf.fill(palette["wall"])
    step = 14
    for row, y in enumerate(range(0, C.FLOOR_Y, step)):
        offset = step // 2 if row % 2 else 0
        for x in range(-step, C.W + step, step):
            pygame.draw.circle(surf, palette["dots"], (x + offset, y), 2)
    shade = pygame.Surface((C.W, C.H), pygame.SRCALPHA)
    for i in range(0, 60, 3):                                 # darker towards the edges of the room
        pygame.draw.rect(shade, (0, 0, 0, 60 - i), (i, i, C.W - 2 * i, C.H - 2 * i), 3)
    surf.blit(shade, (0, 0))
    base = tuple(int(c * 0.55) for c in palette["wall"])      # the baseboard along the floor
    pygame.draw.rect(surf, base, (0, C.FLOOR_Y - 16, C.W, 16))
    pygame.draw.line(surf, INK, (0, C.FLOOR_Y - 16), (C.W, C.FLOOR_Y - 16), 3)
    pygame.draw.rect(surf, INK, surf.get_rect(), 8)
    return surf


# --- comic-book shapes ------------------------------------------------------------------------------
# Shapes are in fractions of a rectangle: (0, 0) is its top-left, (1, 1) its bottom-right.

def _pts(r, pairs):
    return [(round(r.left + fx * r.w), round(r.top + fy * r.h)) for fx, fy in pairs]


def shape(surf, colour, r, pairs, edge=2):
    """A filled polygon with an ink outline (edge=0 for no outline)."""
    pts = _pts(r, pairs)
    pygame.draw.polygon(surf, colour, pts)
    if edge:
        pygame.draw.polygon(surf, INK, pts, edge)


def disc(surf, colour, r, fx, fy, fr, edge=2):
    """A filled circle; fr is its radius as a fraction of the rectangle's width (edge=0 for no outline)."""
    centre = (round(r.left + fx * r.w), round(r.top + fy * r.h))
    radius = max(1, round(fr * r.w))
    pygame.draw.circle(surf, colour, centre, radius)
    if edge:
        pygame.draw.circle(surf, INK, centre, radius, edge)


def stroke(surf, colour, r, a, b, width=2):
    pygame.draw.line(surf, colour, _pts(r, [a])[0], _pts(r, [b])[0], width)


# --- comic-book decor -------------------------------------------------------------------------------

def hero_art(surf, r, sky):
    """A caped hero against a burst of rays."""
    for i in range(12):
        a = math.pi * 2 * i / 12
        stroke(surf, (255, 236, 160), r, (0.5, 0.42), (0.5 + math.cos(a), 0.42 + math.sin(a)), 2)
    shape(surf, RED, r, [(0.30, 0.44), (0.70, 0.44), (0.98, 1.0), (0.02, 1.0)])          # cape
    shape(surf, INK, r, [(0.33, 0.42), (0.67, 0.42), (0.58, 0.82), (0.42, 0.82)], edge=0)  # suit
    shape(surf, YELLOW, r, [(0.50, 0.50), (0.58, 0.58), (0.50, 0.68), (0.42, 0.58)], edge=1)  # emblem
    disc(surf, INK, r, 0.50, 0.28, 0.15, edge=0)                                          # head
    stroke(surf, WHITE, r, (0.40, 0.27), (0.60, 0.27), 3)                                  # mask slit


def skyline_art(surf, r, sky):
    """A night city: a moon over lit windows."""
    disc(surf, (250, 240, 210), r, 0.74, 0.22, 0.12, edge=0)
    for x0, x1, height in ((0.02, 0.24, 0.52), (0.24, 0.44, 0.72), (0.44, 0.62, 0.42),
                           (0.62, 0.82, 0.84), (0.82, 0.98, 0.58)):
        top = 1 - height
        shape(surf, (16, 16, 32), r, [(x0, top), (x1, top), (x1, 1.0), (x0, 1.0)])
        wy = top + 0.06
        while wy < 0.92:
            wx = x0 + 0.05
            while wx < x1 - 0.10:
                if (round(wx * 100) + round(wy * 100)) % 3:
                    shape(surf, YELLOW, r, [(wx, wy), (wx + 0.06, wy), (wx + 0.06, wy + 0.05), (wx, wy + 0.05)], edge=0)
                wx += 0.12
            wy += 0.10


def inkwell_art(surf, r, sky):
    """An ink bottle, a splat and a pen nib."""
    shape(surf, (150, 100, 60), r, [(0.38, 0.20), (0.62, 0.20), (0.62, 0.29), (0.38, 0.29)])        # cork
    shape(surf, (90, 110, 120), r, [(0.42, 0.29), (0.58, 0.29), (0.58, 0.44), (0.42, 0.44)])        # neck
    shape(surf, (120, 50, 190), r, [(0.28, 0.44), (0.72, 0.44), (0.80, 0.66), (0.80, 0.90),
                                    (0.20, 0.90), (0.20, 0.66)])                                    # ink
    shape(surf, (215, 195, 255), r, [(0.30, 0.52), (0.36, 0.52), (0.33, 0.80), (0.27, 0.80)], edge=0)  # glint
    disc(surf, INK, r, 0.16, 0.93, 0.08, edge=0)
    disc(surf, INK, r, 0.50, 0.97, 0.12, edge=0)
    disc(surf, INK, r, 0.84, 0.92, 0.07, edge=0)
    shape(surf, (190, 190, 200), r, [(0.78, 0.10), (0.97, 0.02), (0.92, 0.22)], edge=1)               # nib


class Panel:
    """A comic-book panel: an ink-framed picture with halftone shading and an optional caption box.
    x, y is its top-left corner. Decor: only looked at."""

    def __init__(self, x, y, w, h, art, sky, caption=None, caption_fill=YELLOW, frame=None):
        pad = 7 if frame else 0                  # a gilt frame goes around the picture when frame is given
        self.image = pygame.Surface((w + 2 * pad, h + 2 * pad))
        if frame:
            self.image.fill(frame)
        pic = self.image.subsurface(pygame.Rect(pad, pad, w, h))
        r = pic.get_rect()
        pic.fill(sky)
        dots = tuple(max(0, c - 22) for c in sky)
        for row, yy in enumerate(range(0, h, 8)):
            for xx in range(4 if row % 2 else 0, w, 8):
                pygame.draw.circle(pic, dots, (xx, yy), 1)
        art(pic, r, sky)
        if caption:
            font = pygame.font.Font(None, 24)
            font.set_bold(True)
            label = font.render(caption, True, INK)
            box = pygame.Rect(0, 0, label.get_width() + 12, label.get_height() + 6)
            box.midtop = (r.centerx, 6)
            pygame.draw.rect(pic, caption_fill, box)
            pygame.draw.rect(pic, INK, box, 2)
            pic.blit(label, label.get_rect(center=box.center))
        pygame.draw.rect(pic, INK, r, 4)
        if frame:
            pygame.draw.rect(self.image, INK, self.image.get_rect(), 2)
        self.pos = (int(x) - pad, int(y) - pad)

    def draw(self, surf):
        surf.blit(self.image, self.pos)


class Caption:
    """A caption box, like the title boxes in a comic: room names and TO BE CONTINUED... x, y is its top-left."""

    def __init__(self, x, y, text, fill, size=26):
        font = pygame.font.Font(None, size)
        font.set_bold(True)
        label = font.render(text, True, INK)
        w, h = label.get_width() + 24, label.get_height() + 12
        self.image = pygame.Surface((w + 5, h + 5), pygame.SRCALPHA)
        pygame.draw.rect(self.image, INK, (5, 5, w, h))            # drop shadow
        pygame.draw.rect(self.image, fill, (0, 0, w, h))
        pygame.draw.rect(self.image, INK, (0, 0, w, h), 3)
        self.image.blit(label, label.get_rect(center=(w // 2, h // 2)))
        self.pos = (int(x), int(y))

    def draw(self, surf):
        surf.blit(self.image, self.pos)


class Corkboard:
    """A cork noticeboard with pages pinned to it. x, y is its top-left corner. Decor: only looked at.
    pages: (fx, fy, fw, fh, pin colour), as fractions of the board."""

    def __init__(self, x, y, w, h, pages):
        self.image = pygame.Surface((w, h))
        self.image.fill((176, 128, 74))
        for xx in range(3, w, 7):
            for yy in range(3, h, 7):
                if (xx * 3 + yy * 5) % 4 == 0:
                    pygame.draw.circle(self.image, (140, 96, 52), (xx, yy), 1)
        for fx, fy, fw, fh, pin in pages:
            page = pygame.Rect(int(fx * w), int(fy * h), int(fw * w), int(fh * h))
            pygame.draw.rect(self.image, PAPER, page)
            pygame.draw.rect(self.image, INK, page, 1)
            pygame.draw.line(self.image, INK, (page.left + 3, page.top + 4), (page.right - 4, page.top + 4), 1)
            pygame.draw.circle(self.image, pin, (page.centerx, page.top + 2), 3)
            pygame.draw.circle(self.image, INK, (page.centerx, page.top + 2), 3, 1)
        pygame.draw.rect(self.image, INK, self.image.get_rect(), 4)
        self.pos = (int(x), int(y))

    def draw(self, surf):
        surf.blit(self.image, self.pos)


class Clock:
    """A wall clock, set to ten past ten. x, y is its centre. Decor: only looked at."""

    def __init__(self, x, y, r):
        self.centre, self.r = (int(x), int(y)), r

    def draw(self, surf):
        cx, cy = self.centre
        r = self.r
        pygame.draw.circle(surf, PAPER, self.centre, r)
        pygame.draw.circle(surf, INK, self.centre, r, 3)
        for k in range(12):
            a = math.radians(k * 30) - math.pi / 2
            outer = (cx + math.cos(a) * (r - 2), cy + math.sin(a) * (r - 2))
            inner = (cx + math.cos(a) * (r - 6), cy + math.sin(a) * (r - 6))
            pygame.draw.line(surf, INK, outer, inner, 2)
        for degrees, length, width in ((300, 0.5, 3), (60, 0.8, 2)):     # hour hand and minute hand
            a = math.radians(degrees) - math.pi / 2
            tip = (cx + math.cos(a) * r * length, cy + math.sin(a) * r * length)
            pygame.draw.line(surf, INK, self.centre, tip, width)
        pygame.draw.circle(surf, RED, self.centre, 2)


class Splat:
    """A splash of ink on the wall. x, y is its centre. Decor: only looked at."""

    def __init__(self, x, y, size, colour):
        span = size * 6
        self.image = pygame.Surface((span, span), pygame.SRCALPHA)
        c = (span // 2, span // 2)
        pygame.draw.circle(self.image, colour, c, size)
        for dx, dy, k in ((-1.3, -0.4, 0.45), (1.1, -1.0, 0.35), (1.4, 0.6, 0.5), (-0.6, 1.3, 0.4), (0.3, -1.6, 0.3)):
            pygame.draw.circle(self.image, colour, (int(c[0] + dx * size), int(c[1] + dy * size)), max(2, int(size * k)))
        for dx, k in ((-0.5, 0.8), (0.6, 1.0), (1.2, 0.5)):          # drips
            top = (int(c[0] + dx * size), int(c[1] + size * 0.6))
            bottom = (int(c[0] + dx * size), int(c[1] + size * (1.6 + k)))
            pygame.draw.line(self.image, colour, top, bottom, max(2, size // 4))
        self.pos = (int(x) - span // 2, int(y) - span // 2)

    def draw(self, surf):
        surf.blit(self.image, self.pos)


class Burst:
    """A comic sound-effect burst (POW!, BAM!). x, y is its centre. Decor: only looked at."""

    def __init__(self, x, y, text, fill):
        self.image = pygame.Surface((120, 120), pygame.SRCALPHA)
        points = []
        for i in range(24):
            r = 58 if i % 2 == 0 else 40
            a = math.pi * 2 * i / 24
            points.append((60 + r * math.cos(a), 60 + r * math.sin(a)))
        pygame.draw.polygon(self.image, fill, points)
        pygame.draw.polygon(self.image, INK, points, 4)
        font = pygame.font.Font(None, 24)
        font.set_bold(True)
        label = font.render(text, True, INK)
        self.image.blit(label, label.get_rect(center=(60, 60)))
        self.pos = (int(x) - 60, int(y) - 60)

    def draw(self, surf):
        surf.blit(self.image, self.pos)


def place(burst, cx, cy):
    """Move a Burst so its centre is at (cx, cy)."""
    burst.pos = (int(cx) - 60, int(cy) - 60)


class Bubble:
    """A speech balloon with a tail. x, y is its top-left corner. Decor: only looked at."""

    def __init__(self, x, y, text):
        label = pygame.font.Font(None, 28).render(text, True, INK)
        w, h = label.get_width() + 24, label.get_height() + 16
        self.image = pygame.Surface((w, h + 16), pygame.SRCALPHA)
        body = pygame.Rect(0, 0, w, h)
        pygame.draw.rect(self.image, PAPER, body, border_radius=12)
        pygame.draw.rect(self.image, INK, body, 3, border_radius=12)
        tail = [(w // 3, h - 2), (w // 3 + 14, h - 2), (w // 3 - 6, h + 14)]
        pygame.draw.polygon(self.image, PAPER, tail)
        pygame.draw.lines(self.image, INK, False, [tail[0], tail[2], tail[1]], 3)
        self.image.blit(label, label.get_rect(center=body.center))
        self.pos = (int(x), int(y))

    def draw(self, surf):
        surf.blit(self.image, self.pos)


# --- furniture: the artist's table ------------------------------------------------------------------

def _mirror(pairs, flip):
    return [(1 - fx if flip else fx, fy) for fx, fy in pairs]


class ArtistDesk(Furniture):
    """An artist's table, drawn at twice the characters' scale (a person is about 44 px tall in this game).
    60 px wide and its top sits about 42 px off the floor. Two views:

      'side'           in profile, with a tilted board and a lamp
      'front'          facing you, with a comic page standing on it

    flip=True turns it around. Searchable like any desk: its rect is the part you search.
    """

    W, H = 60, 64

    def __init__(self, x, y, name, view="side", flip=False, holds_piece=False):
        super().__init__(x, y, self.W, self.H, name, holds_piece=holds_piece)
        self.view, self.flip = view, flip

    def draw(self, surf):
        r = self.rect
        wood = WOOD_DARK if self.searched else WOOD
        light = WOOD_DARK if self.searched else WOOD_LIGHT
        f = self.flip

        def poly(colour, pairs, edge=1):
            shape(surf, colour, r, _mirror(pairs, f), edge)

        def line(colour, a, b, width=2):
            p, q = _mirror([a, b], f)
            stroke(surf, colour, r, p, q, width)

        if self.view == "front":
            poly(PAPER, [(0.18, 0.02), (0.82, 0.02), (0.82, 0.56), (0.18, 0.56)])        # comic page on the easel
            line(INK, (0.50, 0.02), (0.50, 0.56), 1)
            line(INK, (0.18, 0.28), (0.82, 0.28), 1)
            poly(light, [(0.00, 0.58), (1.00, 0.58), (1.00, 0.66), (0.00, 0.66)])         # table top
            line(WOOD_DARK, (0.06, 0.66), (0.06, 1.00), 2)
            line(WOOD_DARK, (0.94, 0.66), (0.94, 1.00), 2)
            poly((200, 60, 60), [(0.08, 0.44), (0.22, 0.44), (0.22, 0.58), (0.08, 0.58)])  # pencil cup
            line(YELLOW, (0.12, 0.44), (0.10, 0.30), 2)
            line(CYAN, (0.18, 0.44), (0.20, 0.32), 2)
        else:                                                                             # 'side'
            poly(wood, [(0.00, 0.52), (0.92, 0.36), (0.92, 0.46), (0.00, 0.62)])         # tilted board
            poly(PAPER, [(0.08, 0.52), (0.82, 0.38), (0.82, 0.45), (0.08, 0.60)])        # page on the board
            line(WOOD_DARK, (0.18, 0.62), (0.10, 1.00), 2)
            line(WOOD_DARK, (0.80, 0.46), (0.90, 1.00), 2)
            line(METAL, (0.92, 0.36), (0.92, 0.04), 2)                                    # lamp pole
            poly(YELLOW, [(0.84, 0.00), (1.00, 0.10), (0.80, 0.10)])                       # lamp shade
            poly((200, 60, 60), [(0.10, 0.88), (0.30, 0.88), (0.30, 1.00), (0.10, 1.00)])  # pencil cup


# --- the villains -----------------------------------------------------------------------------------
# Costumes are drawn with the same fractional shapes as the panels: (0, 0) is the hit-box's top-left.

def pencil_thug(surf, inner):
    """The Pencil Thug: a scalloped red cape, a dark coat with a red tie, a domino mask and a pencil."""
    r = inner.rect
    shape(surf, (190, 40, 40), r, [(0.05, 0.28), (0.50, 0.22), (0.95, 0.28), (1.18, 0.98), (1.04, 0.90),
                                   (0.86, 1.02), (0.68, 0.92), (0.50, 1.02), (0.32, 0.92), (0.14, 1.02),
                                   (-0.04, 0.90), (-0.18, 0.98)])
    shape(surf, (46, 42, 62), r, [(0.16, 0.44), (0.84, 0.44), (0.98, 0.98), (0.02, 0.98)])
    shape(surf, WHITE, r, [(0.40, 0.44), (0.60, 0.44), (0.50, 0.68)], edge=1)              # shirt V
    shape(surf, (220, 40, 40), r, [(0.46, 0.50), (0.54, 0.50), (0.57, 0.60), (0.50, 0.68), (0.43, 0.60)], edge=1)
    for fy in (0.80, 0.90):
        disc(surf, WHITE, r, 0.5, fy, 0.025, edge=1)                                        # buttons
    disc(surf, (196, 222, 170), r, 0.50, 0.27, 0.23)                                        # head
    shape(surf, (20, 20, 26), r, [(0.30, 0.16), (0.36, 0.04), (0.50, 0.00), (0.62, 0.04), (0.70, 0.14),
                                  (0.58, 0.10), (0.44, 0.10)], edge=1)                      # quiff
    shape(surf, INK, r, [(0.26, 0.22), (0.74, 0.22), (0.66, 0.34), (0.50, 0.30), (0.34, 0.34)], edge=0)  # mask
    disc(surf, WHITE, r, 0.40, 0.26, 0.05, edge=1)
    disc(surf, WHITE, r, 0.60, 0.26, 0.05, edge=1)
    disc(surf, INK, r, 0.41, 0.27, 0.02, edge=0)
    disc(surf, INK, r, 0.61, 0.27, 0.02, edge=0)
    stroke(surf, INK, r, (0.28, 0.17), (0.44, 0.22), 2)                                     # angry brows
    stroke(surf, INK, r, (0.72, 0.17), (0.56, 0.22), 2)
    shape(surf, WHITE, r, [(0.40, 0.39), (0.60, 0.39), (0.58, 0.43), (0.42, 0.43)], edge=1)  # sneer
    shape(surf, YELLOW, r, [(0.90, 0.60), (0.96, 0.56), (1.30, 0.22), (1.24, 0.16)], edge=1)  # pencil
    shape(surf, (70, 70, 80), r, [(1.24, 0.16), (1.30, 0.22), (1.40, 0.10)], edge=1)
    disc(surf, (255, 200, 170), r, 0.93, 0.60, 0.05, edge=1)                                # hand


def inkblot(surf, inner):
    """Inkblot: a purple blob of ink with dripping edges, a monocle and fangs."""
    r = inner.rect
    ink = (96, 40, 150)
    for x0, x1, length in ((0.12, 0.25, 1.02), (0.44, 0.56, 1.10), (0.76, 0.88, 0.98)):
        shape(surf, ink, r, [(x0, 0.70), (x1, 0.70), (x1, length), ((x0 + x1) / 2, length + 0.06), (x0, length)],
              edge=1)
    disc(surf, ink, r, 0.50, 0.40, 0.36, edge=0)                                            # head of ink
    disc(surf, ink, r, 0.50, 0.74, 0.30, edge=0)                                            # body of ink
    pygame.draw.arc(surf, (180, 130, 255), pygame.Rect(r.left + 5, r.top + 4, 14, 14),
                    math.pi * 0.7, math.pi * 1.2, 2)                                        # shine
    disc(surf, WHITE, r, 0.36, 0.34, 0.13)
    disc(surf, WHITE, r, 0.64, 0.34, 0.13)
    disc(surf, YELLOW, r, 0.36, 0.35, 0.07, edge=0)
    disc(surf, YELLOW, r, 0.64, 0.35, 0.07, edge=0)
    stroke(surf, INK, r, (0.36, 0.30), (0.36, 0.40), 1)
    stroke(surf, INK, r, (0.64, 0.30), (0.64, 0.40), 1)
    pygame.draw.circle(surf, GOLD, (round(r.left + 0.64 * r.w), round(r.top + 0.34 * r.h)), 6, 2)   # monocle
    stroke(surf, GOLD, r, (0.70, 0.42), (0.86, 0.66), 1)                                             # chain
    shape(surf, INK, r, [(0.30, 0.54), (0.70, 0.54), (0.60, 0.68), (0.40, 0.68)], edge=1)            # grin
    shape(surf, WHITE, r, [(0.34, 0.54), (0.44, 0.54), (0.39, 0.66)], edge=1)                        # fangs
    shape(surf, WHITE, r, [(0.56, 0.54), (0.66, 0.54), (0.61, 0.66)], edge=1)
    disc(surf, ink, r, 0.90, 0.16, 0.03, edge=0)                                                     # splatters
    disc(surf, ink, r, 0.08, 0.30, 0.02, edge=0)


def framer(cape):
    """The Framer: a top-hatted gentleman in a striped jacket, a handlebar moustache and a monocle."""

    def paint(surf, inner):
        r = inner.rect
        shape(surf, cape, r, [(0.18, 0.34), (0.82, 0.34), (1.16, 1.0), (-0.16, 1.0)])          # cape
        shape(surf, (20, 20, 26), r, [(0.22, 0.44), (0.78, 0.44), (0.86, 0.98), (0.14, 0.98)])   # jacket
        for fx in (0.30, 0.42, 0.58, 0.70):
            stroke(surf, WHITE, r, (fx, 0.50), (fx + (fx - 0.5) * 0.10, 0.96), 1)                 # pinstripes
        shape(surf, WHITE, r, [(0.40, 0.44), (0.60, 0.44), (0.50, 0.64)], edge=1)                  # shirt
        shape(surf, (220, 40, 40), r, [(0.44, 0.48), (0.50, 0.50), (0.44, 0.54)], edge=1)          # bow tie
        shape(surf, (220, 40, 40), r, [(0.56, 0.48), (0.50, 0.50), (0.56, 0.54)], edge=1)
        disc(surf, (236, 200, 160), r, 0.50, 0.26, 0.21)                                            # head
        shape(surf, (20, 20, 26), r, [(0.30, 0.16), (0.70, 0.16), (0.66, -0.06), (0.34, -0.06)], edge=1)  # hat
        shape(surf, (20, 20, 26), r, [(0.14, 0.16), (0.86, 0.16), (0.80, 0.22), (0.20, 0.22)], edge=1)    # brim
        shape(surf, YELLOW, r, [(0.34, 0.08), (0.66, 0.08), (0.66, 0.13), (0.34, 0.13)], edge=0)        # band
        shape(surf, (20, 20, 26), r, [(0.36, 0.34), (0.50, 0.31), (0.64, 0.34), (0.72, 0.29), (0.62, 0.40),
                                      (0.50, 0.37), (0.38, 0.40), (0.28, 0.29)], edge=1)            # moustache
        stroke(surf, INK, r, (0.36, 0.25), (0.46, 0.25), 2)                                         # narrow eyes
        stroke(surf, INK, r, (0.54, 0.25), (0.64, 0.25), 2)
        stroke(surf, INK, r, (0.34, 0.20), (0.46, 0.22), 1)                                         # stern brows
        stroke(surf, INK, r, (0.66, 0.20), (0.54, 0.22), 1)
        pygame.draw.circle(surf, GOLD, (round(r.left + 0.62 * r.w), round(r.top + 0.25 * r.h)), 4, 1)  # monocle
        stroke(surf, GOLD, r, (0.66, 0.30), (0.84, 0.58), 1)                                        # chain

    return paint


def anvil(surf, inner):
    """The Anvil: a riveted steel block on a piston, with a fanged, scowling face and hazard stripes."""
    r = inner.rect
    piston = pygame.Rect(r.centerx - 5, inner.y_top - 40, 10, max(0, r.top - inner.y_top + 40))
    pygame.draw.rect(surf, (90, 92, 100), piston)
    pygame.draw.rect(surf, INK, piston, 1)
    for y in range(inner.y_top - 34, r.top - 2, 9):
        pygame.draw.circle(surf, (170, 170, 180), (r.centerx, y), 2)                              # bolts
    pygame.draw.rect(surf, (128, 130, 142), r, border_radius=4)
    pygame.draw.rect(surf, (96, 70, 70), (r.left, r.bottom - 9, r.w, 9))                          # rust band
    for x in range(r.left, r.right, 12):
        pygame.draw.line(surf, YELLOW, (x, r.bottom - 1), (x + 7, r.bottom - 9), 3)               # hazard stripes
    pygame.draw.line(surf, (200, 200, 210), (r.left + 3, r.top + 3), (r.right - 4, r.top + 3), 2)  # shine
    pygame.draw.rect(surf, INK, r, 2, border_radius=4)
    stroke(surf, INK, r, (0.68, 0.10), (0.78, 0.30), 1)                                           # crack
    stroke(surf, INK, r, (0.78, 0.30), (0.74, 0.40), 1)
    for fx, fy in ((0.12, 0.20), (0.88, 0.20), (0.12, 0.62), (0.88, 0.62)):
        disc(surf, (176, 176, 186), r, fx, fy, 0.035, edge=1)                                     # rivets
    shape(surf, INK, r, [(0.14, 0.18), (0.44, 0.30), (0.44, 0.36), (0.14, 0.26)], edge=0)          # brows
    shape(surf, INK, r, [(0.86, 0.18), (0.56, 0.30), (0.56, 0.36), (0.86, 0.26)], edge=0)
    disc(surf, WHITE, r, 0.28, 0.44, 0.07)                                                        # eyes
    disc(surf, WHITE, r, 0.72, 0.44, 0.07)
    disc(surf, INK, r, 0.30, 0.46, 0.03, edge=0)
    disc(surf, INK, r, 0.70, 0.46, 0.03, edge=0)
    shape(surf, (70, 14, 14), r, [(0.22, 0.60), (0.78, 0.60), (0.72, 0.78), (0.28, 0.78)], edge=1)  # mouth
    for fx in (0.30, 0.46, 0.60):
        shape(surf, WHITE, r, [(fx, 0.60), (fx + 0.09, 0.60), (fx + 0.045, 0.74)], edge=1)        # fangs


def draw_fx_for(room, surf):
    """The sound effects go over the player. Each room calls this from draw_foreground."""
    for h in room.hazards:
        if isinstance(h, Villain):
            h.draw_fx(surf)


class Villain:
    """A kit hazard (a PatrolBot or a Crusher) in a comic-book costume.

    Its movement and hit-box come from the kit part inside. When it catches you, the fight plays out like a
    1960s TV episode: you freeze, POW! and BAM! pop up over you, and only then does the engine send you back.
    """

    HIT_TIME = 1.2                      # seconds of sound effects before you're sent back

    def __init__(self, inner, paint):
        self.inner = inner
        self.rect = inner.rect
        self.paint = paint              # paint(surf, inner) draws the costume
        self.pow = Burst(0, 0, "POW!", YELLOW)
        self.bam = Burst(0, 0, "BAM!", ORANGE)
        self.hit_left = 0.0
        self.pin = (0.0, 0.0)
        self.player = None

    def update(self, dt, room, player):
        self.player = player
        if self.hit_left > 0:
            self.hit_left -= dt
            self.rect = pygame.Rect(0, 0, 0, 0)      # no collision while the sound effects play
            self.freeze(player)
            if self.hit_left <= 0:
                self.rect = player.rect              # touching now: the engine sends you back
            return
        self.inner.update(dt, room, player)
        # The engine checks for a touch inside Player.update(), which runs before the player's move is
        # finished. If the hit-box were live here, a walk into a villain would send you back with no POW!.
        # So the box stays off, and draw() checks for the touch once the player has moved.
        self.rect = pygame.Rect(0, 0, 0, 0)

    def start_hit(self, player):
        cx, cy = player.rect.center
        place(self.pow, cx - 60, cy - 70)
        place(self.bam, cx + 60, cy - 40)
        self.pin = (player.x, player.y)
        self.hit_left = self.HIT_TIME

    def freeze(self, player):
        player.x, player.y = self.pin                # you're frozen in place
        player.vx = player.vy = 0.0
        player.searching = None

    def draw(self, surf):
        player = self.player
        if player is not None:
            if self.hit_left > 0:
                # The player moves after update() and before they're drawn, so hold them in place here.
                self.freeze(player)
            elif player.safe <= 0 and self.inner.rect.colliderect(player.rect):
                self.start_hit(player)                   # touching, after the player's move: POW! and BAM!
        self.paint(surf, self.inner)

    def draw_fx(self, surf):
        if self.hit_left <= 0:
            return
        elapsed = self.HIT_TIME - self.hit_left
        if elapsed >= 0.0:
            self.pow.draw(surf)
        if elapsed >= 0.25:
            self.bam.draw(surf)


# --- Room 1: the West elevator is through its left edge ---

class Bullpen(Room):
    title = "Bullpen"

    def build(self):
        self.comic_bg = comic_wall(BULLPEN)
        self.decor += [
            Caption(300, 22, "THE BULLPEN!", BULLPEN["title"]),
            Panel(110, 66, 92, 124, hero_art, RED, "POW!", YELLOW),
            Panel(214, 66, 92, 124, skyline_art, (30, 90, 200), "NIGHT", CYAN),
            Bubble(300, 210, "DEADLINE!"),
            Bubble(470, 250, "HA HA!"),
            Burst(500, 160, "ZAP!", YELLOW),
            Panel(640, 56, 150, 124, skyline_art, (20, 60, 150), "CITY", YELLOW),
            Corkboard(40, 226, 124, 110, [(0.08, 0.14, 0.38, 0.34, RED), (0.54, 0.10, 0.36, 0.30, CYAN),
                                          (0.18, 0.56, 0.48, 0.30, YELLOW), (0.66, 0.52, 0.28, 0.38, MINT)]),
            Clock(868, 262, 20),
            CeilingLight(480),
        ]
        self.platforms.append(Platform(400, 410, 200))
        self.furniture += [
            ArtistDesk(90, C.FLOOR_Y, "drafting table", view="front"),
            ArtistDesk(160, C.FLOOR_Y, "inking desk", view="side"),
            ArtistDesk(230, C.FLOOR_Y, "lettering desk", view="side", flip=True),
            ArtistDesk(700, C.FLOOR_Y, "ink wash table", view="front"),
            Bookshelf(806, C.FLOOR_Y, "back issues"),
            ArtistDesk(420, 410, "layout desk", view="side"),
            ArtistDesk(500, 410, "sketch desk", view="front", flip=True),
        ]
        self.hazards.append(Villain(PatrolBot(360, C.FLOOR_Y, left=330, right=640, speed=80), pencil_thug))

    def draw_background(self, surf):
        surf.blit(self.comic_bg, (0, 0))

    def draw_foreground(self, surf):
        draw_fx_for(self, surf)


# --- Room 2: the digit is on the top ledge ---

class InkRoom(Room):
    title = "Ink Room"

    def build(self):
        self.comic_bg = comic_wall(INK_ROOM)
        self.decor += [
            Caption(360, 46, "INK ROOM!", INK_ROOM["title"]),
            Panel(110, 62, 92, 124, inkwell_art, (60, 30, 90), "INK!", MINT),
            Panel(590, 60, 96, 124, hero_art, (230, 90, 40), None),
            Bubble(220, 190, "SHH..."),
            Bubble(200, 330, "MWAHAHA!"),
            Burst(820, 170, "INK!", ORANGE),
            Splat(250, 268, 16, (120, 40, 170)),
            Splat(708, 34, 11, (120, 40, 170)),
            Splat(470, 96, 9, (40, 130, 120)),
            CeilingLight(320),
        ]
        # Each ledge is one jump (about 90 px) above the last, so you can climb them in order.
        self.platforms += [
            Platform(90, 410, 200),
            Platform(380, 330, 200),
            Platform(640, 250, 230),
        ]
        self.furniture += [
            Easel(110, 410, "sketch easel"),
            FilingCabinet(430, 330, "ink drawer"),
            Plinth(700, 250, "original page", holds_piece=True),
            ArtistDesk(500, 330, "ink table", view="side"),
            ArtistDesk(320, C.FLOOR_Y, "light table", view="side"),
            ArtistDesk(392, C.FLOOR_Y, "drafting table", view="front", flip=True),
            ArtistDesk(464, C.FLOOR_Y, "page desk", view="front"),
            Couch(600, C.FLOOR_Y, "reading couch"),
            ArtistDesk(760, C.FLOOR_Y, "inking table", view="side", flip=True),
        ]
        self.hazards.append(Villain(PatrolBot(180, C.FLOOR_Y, left=90, right=262, speed=80), inkblot))

    def draw_background(self, surf):
        surf.blit(self.comic_bg, (0, 0))

    def draw_foreground(self, surf):
        draw_fx_for(self, surf)


# --- Room 3: the East elevator is through its right edge ---

class Gallery(Room):
    title = "Gallery"

    def build(self):
        self.comic_bg = comic_wall(GALLERY)
        self.decor += [
            Caption(250, 46, "THE GALLERY!", GALLERY["title"]),
            Caption(60, 230, "TO BE CONTINUED...", GOLD, size=22),
            Panel(120, 66, 92, 124, hero_art, (200, 60, 50), "END", GOLD, frame=GOLD),
            Panel(600, 56, 150, 124, skyline_art, (60, 20, 110), "NIGHT", GOLD, frame=GOLD),
            Burst(868, 338, "WHAM!", GOLD),
            Caption(700, 232, "DO NOT TOUCH", GOLD, size=20),
            CeilingLight(480),
        ]
        self.platforms.append(Platform(300, 410, 180))
        self.furniture += [
            Plinth(120, C.FLOOR_Y, "panel one"),
            ArtistDesk(204, C.FLOOR_Y, "ink table", view="front"),
            ArtistDesk(268, C.FLOOR_Y, "drafting table", view="side", flip=True),
            Plinth(330, 410, "panel two"),
            ArtistDesk(412, 410, "lettering desk", view="side"),
            ArtistDesk(580, C.FLOOR_Y, "drafting table", view="front"),
            ArtistDesk(650, C.FLOOR_Y, "ink table", view="side", flip=True),
            Bookshelf(716, C.FLOOR_Y, "bound volumes"),
        ]
        self.hazards += [
            Villain(PatrolBot(360, C.FLOOR_Y, left=330, right=520, speed=70), framer((40, 110, 200))),
            Villain(Crusher(790, y_top=180, w=50, h=40), anvil),
        ]

    def draw_background(self, surf):
        surf.blit(self.comic_bg, (0, 0))

    def draw_foreground(self, surf):
        draw_fx_for(self, surf)


ROOMS = [Bullpen, InkRoom, Gallery]     # west to east
