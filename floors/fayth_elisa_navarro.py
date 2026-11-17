"""The Library: circulation desk, the stacks, the reading room.

West elevator -> Circulation Desk -> The Stacks -> Reading Room -> East elevator.
The floor's digit is in the Special Collections cabinet, up on the high ledge in the Reading Room.

The look follows SVA's real library in the basement: charcoal walls, glass partitions in grey frames with
the stacks and the iMac lab behind them, long LED strip lights, white tables on dark steel legs, light grey
chairs, steel shelving full of bright spines, and a dark plank floor.
"""
import math
import random

import pygame

from engine import config as C
from engine.bots import Zapper
from engine.kit import Crusher, Drone, Plant, Poster, Sign
from engine.room import Furniture, Lift, Platform, Room

NAME = "The Library"
AUTHOR = "Fayth Elisa Navarro & Fiori Sims"

# Colours taken from a photo of SVA's library.
CHARCOAL = (74, 74, 78)          # the walls
CHARCOAL_DARK = (54, 54, 58)
FRAME = (96, 98, 102)            # glass partition frames
BACK_ROOM = (204, 207, 207)      # the bright rooms behind the glass
CEILING = (226, 226, 222)
LED = (252, 252, 246)
WHITE_TOP = (234, 231, 226)      # table and counter tops
STEEL_DARK = (40, 38, 38)        # table legs
STEEL = (120, 122, 128)          # shelving, cabinets
CHAIR = (188, 184, 179)
SVA_PURPLE = (124, 72, 176)
FILM_GREEN = (66, 168, 128)
TEXT = (238, 238, 236)
BOOKS = [(196, 58, 52), (232, 182, 62), (52, 104, 176), (236, 234, 228), (58, 150, 110),
         (220, 112, 58), (150, 82, 160), (36, 36, 40), (170, 40, 70)]

GLASS_TOP, GLASS_BOTTOM = 96, 396   # the glass band on the walls


def tone(f, col):
    """Greyer once searched, like the kit parts."""
    return tuple(int(c * 0.7) for c in col) if f.searched else col


def mix(a, b, k):
    return tuple(int(x + (y - x) * k) for x, y in zip(a, b))


# --- walls, built once per room (see background()) ---

def books(surf, x0, x1, y, h, rng, dim=1.0):
    """A shelf's worth of spines from x0 to x1, standing on y."""
    x = x0
    while x < x1 - 4:
        w = rng.randint(4, 8)
        bh = rng.randint(int(h * 0.7), h)
        col = mix(BOOKS[rng.randrange(len(BOOKS))], CHARCOAL, 1 - dim)
        if rng.random() < 0.08:                                   # a gap on the shelf
            x += w + 4
            continue
        pygame.draw.rect(surf, col, (x, y - bh, w, bh))
        x += w + 1


def shelving(surf, x0, x1, top, bottom, rng, dim=1.0, unit=96):
    """Steel shelving units with books on every shelf."""
    post = mix(STEEL, CHARCOAL_DARK, 0.35 + 0.4 * (1 - dim))
    shelf = mix((150, 150, 154), CHARCOAL, 1 - dim)
    for ux in range(x0, x1, unit):
        right = min(ux + unit - 6, x1)
        for y in range(top + 46, bottom, 46):
            books(surf, ux + 6, right - 4, y - 2, 36, rng, dim)
            pygame.draw.rect(surf, shelf, (ux, y - 2, right - ux, 4))
        pygame.draw.rect(surf, post, (ux, top, 5, bottom - top))
        pygame.draw.rect(surf, post, (right - 5, top, 5, bottom - top))


def imac(surf, x, y, w=46):
    """An iMac standing on y: silver stand, black bezel, the blue-purple wallpaper."""
    h = int(w * 0.62)
    pygame.draw.rect(surf, (210, 212, 214), (x + w // 2 - 4, y - 10, 8, 10))
    pygame.draw.rect(surf, (210, 212, 214), (x + w // 2 - 10, y - 2, 20, 2))
    pygame.draw.rect(surf, (28, 28, 30), (x, y - 10 - h, w, h), border_radius=2)
    for k in range(h - 6):
        pygame.draw.line(surf, mix((60, 70, 150), (220, 110, 90), k / (h - 6)),
                         (x + 3, y - 7 - h + k), (x + w - 4, y - 7 - h + k))
    pygame.draw.rect(surf, (210, 212, 214), (x, y - 10 - h + h - 5, w, 5))


def back_room(surf, x0, x1, inside, rng):
    """What you see through the glass: the stacks, the iMac lab, or the office's white cabinets."""
    pygame.draw.rect(surf, BACK_ROOM, (x0, GLASS_TOP, x1 - x0, GLASS_BOTTOM - GLASS_TOP))
    pygame.draw.rect(surf, (236, 236, 232), (x0, GLASS_TOP, x1 - x0, 18))                 # their ceiling
    for lx in range(x0 + 30, x1 - 60, 180):
        pygame.draw.rect(surf, LED, (lx, GLASS_TOP + 18, 110, 3))
    if inside == "stacks":
        shelving(surf, x0 + 10, x1 - 10, GLASS_TOP + 30, GLASS_BOTTOM - 20, rng)
    elif inside == "imacs":
        shelving(surf, x0 + 10, x1 - 10, GLASS_TOP + 30, GLASS_TOP + 130, rng, unit=110)
        pygame.draw.rect(surf, (238, 236, 232), (x0, 318, x1 - x0, 8))                     # long white desk
        pygame.draw.rect(surf, (150, 150, 152), (x0, 326, x1 - x0, 3))
        for mx in range(x0 + 24, x1 - 60, 92):
            imac(surf, mx, 318)
    elif inside == "office":
        for cx in range(x0 + 12, x1 - 70, 74):                                          # white upper cabinets
            pygame.draw.rect(surf, (226, 226, 230), (cx, GLASS_TOP + 32, 70, 92))
            pygame.draw.line(surf, (180, 180, 186), (cx + 35, GLASS_TOP + 32), (cx + 35, GLASS_TOP + 124), 1)
        pygame.draw.rect(surf, (176, 176, 180), (x0, GLASS_TOP + 190, x1 - x0, GLASS_BOTTOM - GLASS_TOP - 190))
        imac(surf, x0 + 60, GLASS_TOP + 190, 54)
        pygame.draw.rect(surf, (226, 226, 228), (x1 - 120, GLASS_TOP + 168, 70, 22), border_radius=3)  # printer
        pygame.draw.rect(surf, (90, 90, 96), (x1 - 112, GLASS_TOP + 174, 54, 4))


def glass(surf, x0, x1, inside, rng, film=None):
    """A glass partition from x0 to x1: the room behind, frames, reflections."""
    back_room(surf, x0, x1, inside, rng)
    sheen = pygame.Surface((x1 - x0, GLASS_BOTTOM - GLASS_TOP), pygame.SRCALPHA)
    for k in range(0, x1 - x0, 230):                                                    # reflections
        pygame.draw.polygon(sheen, (255, 255, 255, 34), [(k + 40, 0), (k + 90, 0), (k - 60, 300), (k - 110, 300)])
    if film:                                                                             # SVA's coloured film
        fx, fw = film
        pygame.draw.rect(sheen, (*SVA_PURPLE, 150), (fx - x0, 126, fw, 16))
        pygame.draw.rect(sheen, (*FILM_GREEN, 120), (fx - x0, 52, fw, 74))
    surf.blit(sheen, (x0, GLASS_TOP))
    for mx in list(range(x0, x1, 150)) + [x1 - 8]:                                      # mullions
        pygame.draw.rect(surf, FRAME, (mx, GLASS_TOP, 8, GLASS_BOTTOM - GLASS_TOP))
    pygame.draw.rect(surf, FRAME, (x0, GLASS_TOP - 8, x1 - x0, 8))
    pygame.draw.rect(surf, FRAME, (x0, 352, x1 - x0, 6))                                 # the rail across
    pygame.draw.rect(surf, FRAME, (x0, GLASS_BOTTOM, x1 - x0, 8))


def background(spans, seed):
    """The whole wall for one room, drawn once. spans: [(x0, x1, inside, film)] of glass."""
    rng = random.Random(seed)
    surf = pygame.Surface((C.W, C.H))
    surf.fill(CHARCOAL)
    pygame.draw.rect(surf, CEILING, (0, 0, C.W, 24))                                     # ceiling and soffit
    pygame.draw.rect(surf, CHARCOAL_DARK, (0, 24, C.W, 6))
    for x0, x1, inside, film in spans:
        glass(surf, x0, x1, inside, rng, film)
    pygame.draw.rect(surf, CHARCOAL_DARK, (0, C.FLOOR_Y - 10, C.W, 10))                   # baseboard
    return surf


def plank_floor(seed):
    """Dark grey-brown planks for the floor strip, drawn over the engine's plain one."""
    rng = random.Random(seed)
    surf = pygame.Surface((C.W, C.H - C.FLOOR_Y))
    surf.fill((78, 68, 60))
    for row, y in enumerate(range(0, C.H - C.FLOOR_Y, 14)):
        x = -rng.randint(0, 120)
        while x < C.W:
            w = rng.randint(110, 200)
            pygame.draw.rect(surf, mix((86, 76, 66), (66, 58, 52), rng.random()), (x, y, w, 13))
            pygame.draw.line(surf, (50, 44, 40), (x, y), (x, y + 12), 1)
            x += w
        pygame.draw.line(surf, (54, 48, 43), (0, y + 13), (C.W, y + 13), 1)
    pygame.draw.line(surf, (112, 104, 96), (0, 0), (C.W, 0), 2)                           # the edge you walk on
    return surf


class LinearLight:
    """A long LED pendant: two thin cords and a bright bar, with a soft wash below. Decor."""

    def __init__(self, x, length=200, drop=10):
        self.rect = pygame.Rect(int(x) - length // 2, 30 + drop, length, 5)
        self.glow = pygame.Surface((length + 120, 200), pygame.SRCALPHA)
        pygame.draw.polygon(self.glow, (255, 255, 250, 14),
                            [(60, 0), (60 + length, 0), (length + 120, 200), (0, 200)])

    def draw(self, surf):
        r = self.rect
        for cx in (r.left + 16, r.right - 16):
            pygame.draw.line(surf, (40, 40, 44), (cx, 30), (cx, r.top), 1)
        surf.blit(self.glow, (r.left - 60, r.bottom))
        pygame.draw.rect(surf, (60, 60, 64), r.inflate(0, 2))
        pygame.draw.rect(surf, LED, (r.left + 2, r.bottom - 2, r.width - 4, 3))


# --- furniture with the library's look (the searchable area is self.rect) ---

class CirculationDesk(Furniture):
    """The service counter: charcoal front, white top, an iMac."""

    def __init__(self, x, y, holds_piece=False):
        super().__init__(x, y, 170, 66, "circulation desk", holds_piece)
        self._label = pygame.font.Font(None, 16).render("CIRCULATION", True, (200, 200, 204))

    def draw(self, surf):
        r = self.rect
        pygame.draw.rect(surf, tone(self, (62, 62, 66)), r)
        pygame.draw.rect(surf, tone(self, WHITE_TOP), (r.left - 6, r.top, r.width + 12, 9))
        pygame.draw.rect(surf, tone(self, SVA_PURPLE), (r.left, r.top + 22, r.width, 3))
        surf.blit(self._label, (r.centerx - self._label.get_width() // 2, r.top + 34))
        imac(surf, r.left + 18, r.top, 44)
        pygame.draw.rect(surf, (60, 60, 64), (r.right - 52, r.top - 6, 30, 6), border_radius=2)  # scanner
        pygame.draw.rect(surf, (220, 60, 50), (r.right - 40, r.top - 5, 6, 2))
        pygame.draw.rect(surf, C.INK, r, 2)


class ReturnBin(Furniture):
    def __init__(self, x, y, holds_piece=False):
        super().__init__(x, y, 60, 74, "book return", holds_piece)
        self._label = pygame.font.Font(None, 16).render("RETURNS", True, (40, 40, 44))

    def draw(self, surf):
        r = self.rect
        pygame.draw.rect(surf, tone(self, (160, 162, 168)), r, border_radius=4)
        pygame.draw.rect(surf, tone(self, (186, 188, 194)), (r.left + 4, r.top + 4, r.width - 8, 6), border_radius=2)
        pygame.draw.rect(surf, (24, 24, 28), (r.left + 10, r.top + 16, r.width - 20, 7), border_radius=2)
        surf.blit(self._label, (r.centerx - self._label.get_width() // 2, r.top + 36))
        pygame.draw.rect(surf, C.INK, r, 2, border_radius=4)


class CardCatalog(Furniture):
    """White laminate drawers with steel pulls."""

    def __init__(self, x, y, holds_piece=False):
        super().__init__(x, y, 84, 92, "card catalog", holds_piece)

    def draw(self, surf):
        r = self.rect
        pygame.draw.rect(surf, tone(self, (222, 222, 224)), r)
        for i in range(4):
            for j in range(5):
                d = pygame.Rect(r.left + 6 + i * 19, r.top + 6 + j * 17, 16, 13)
                pygame.draw.rect(surf, tone(self, (204, 204, 208)), d)
                pygame.draw.rect(surf, tone(self, (176, 176, 182)), d, 1)
                pygame.draw.rect(surf, tone(self, STEEL), (d.centerx - 4, d.bottom - 5, 8, 2))
        pygame.draw.rect(surf, tone(self, STEEL_DARK), (r.left, r.bottom - 4, r.width, 4))
        pygame.draw.rect(surf, C.INK, r, 2)


class BookCart(Furniture):
    def __init__(self, x, y, holds_piece=False):
        super().__init__(x, y, 80, 60, "book cart", holds_piece)

    def draw(self, surf):
        r = self.rect
        frame = tone(self, (150, 152, 158))
        for y in (r.top + 20, r.bottom - 14):
            pygame.draw.rect(surf, frame, (r.left, y, r.width, 5))
        for k, x in enumerate(range(r.left + 4, r.right - 8, 9)):
            h = 14 + (k * 5) % 7
            pygame.draw.rect(surf, tone(self, BOOKS[(k * 4) % len(BOOKS)]), (x, r.top + 20 - h, 7, h))
        for x in (r.left + 2, r.right - 6):
            pygame.draw.line(surf, frame, (x + 2, r.top + 6), (x + 2, r.bottom - 6), 3)
            pygame.draw.circle(surf, (30, 30, 34), (x + 2, r.bottom - 4), 5)
        pygame.draw.line(surf, frame, (r.right - 4, r.top + 6), (r.right + 10, r.top - 4), 3)    # handle


class ReadingTable(Furniture):
    """A long white table on dark steel legs, grey chairs behind it, a laptop and a magazine."""

    def __init__(self, x, y, holds_piece=False):
        super().__init__(x, y, 170, 44, "reading table", holds_piece)

    def draw(self, surf):
        r = self.rect
        for cx in (r.left + 24, r.centerx - 14, r.right - 52):                              # chair backs
            pygame.draw.rect(surf, tone(self, CHAIR), (cx, r.top - 22, 28, 26), border_radius=6)
            pygame.draw.rect(surf, tone(self, (160, 156, 152)), (cx, r.top - 22, 28, 26), 1, border_radius=6)
        pygame.draw.rect(surf, tone(self, WHITE_TOP), (r.left, r.top, r.width, 8))
        pygame.draw.rect(surf, tone(self, (200, 196, 190)), (r.left, r.top + 8, r.width, 2))
        for x in (r.left + 6, r.right - 12):
            pygame.draw.rect(surf, tone(self, STEEL_DARK), (x, r.top + 10, 6, r.height - 10))
        pygame.draw.rect(surf, tone(self, STEEL_DARK), (r.left + 6, r.top + 10, r.width - 12, 3))
        lx = r.left + 34                                                                      # open laptop
        pygame.draw.polygon(surf, (40, 40, 44), [(lx, r.top), (lx + 6, r.top - 20), (lx + 34, r.top - 20), (lx + 30, r.top)])
        pygame.draw.polygon(surf, (110, 140, 190), [(lx + 3, r.top - 2), (lx + 8, r.top - 18), (lx + 32, r.top - 18), (lx + 28, r.top - 2)])
        pygame.draw.rect(surf, (200, 202, 206), (lx - 4, r.top - 2, 40, 2))
        pygame.draw.rect(surf, (226, 92, 70), (r.right - 74, r.top - 3, 26, 3))                # magazine
        pygame.draw.rect(surf, C.INK, (r.left, r.top, r.width, 10), 1)


class ArchiveCabinet(Furniture):
    """Special Collections: a locked steel flat-file cabinet with a white label plate."""

    def __init__(self, x, y, holds_piece=False):
        super().__init__(x, y, 70, 96, "special collections", holds_piece)

    def draw(self, surf):
        r = self.rect
        pygame.draw.rect(surf, tone(self, (104, 108, 114)), r, border_radius=2)
        for j in range(5):
            d = pygame.Rect(r.left + 6, r.top + 8 + j * 17, r.width - 12, 13)
            pygame.draw.rect(surf, tone(self, (138, 142, 148)), d, border_radius=1)
            pygame.draw.line(surf, (40, 42, 46), (d.centerx - 10, d.centery), (d.centerx + 10, d.centery), 2)
        pygame.draw.rect(surf, tone(self, (240, 240, 236)), (r.centerx - 16, r.top - 12, 32, 8))
        pygame.draw.rect(surf, tone(self, SVA_PURPLE), (r.centerx - 16, r.top - 12, 4, 8))
        pygame.draw.rect(surf, C.INK, r, 2, border_radius=2)


class SteelShelf(Furniture):
    """The stacks' shelving: steel uprights, bright spines. Same size as the kit Bookshelf (70 x 110)."""

    def __init__(self, x, y, holds_piece=False):
        super().__init__(x, y, 70, 110, "bookshelf", holds_piece)
        self.seed = int(x) * 7 + int(y)

    def draw(self, surf):
        r = self.rect
        rng = random.Random(self.seed)                       # same spines every frame
        pygame.draw.rect(surf, tone(self, (176, 178, 180)), r)
        for y in range(r.top + 30, r.bottom, 26):
            x = r.left + 6
            while x < r.right - 8:
                w = rng.randint(5, 8)
                pygame.draw.rect(surf, tone(self, BOOKS[rng.randrange(len(BOOKS))]), (x, y - rng.randint(17, 22), w, 22))
                x += w + 1
            pygame.draw.rect(surf, tone(self, (128, 130, 136)), (r.left, y, r.width, 4))
        for x in (r.left, r.right - 5):
            pygame.draw.rect(surf, tone(self, STEEL), (x, r.top, 5, r.height))
        pygame.draw.rect(surf, tone(self, STEEL), (r.left, r.top, r.width, 5))
        pygame.draw.rect(surf, C.INK, r, 2)


# --- the rooms ---

class LibraryRoom(Room):
    """Shared by the three rooms: the wall is drawn once, the plank floor goes over the engine's."""

    spans = []
    seed = 0

    def make_walls(self):
        self.wall = background(self.spans, self.seed)
        self.floor = plank_floor(self.seed)

    def draw_background(self, surf):
        surf.blit(self.wall, (0, 0))

    def draw_foreground(self, surf):
        surf.blit(self.floor, (0, C.FLOOR_Y + 1), (0, 1, C.W, C.H - C.FLOOR_Y - 1))
        for lift in self.lifts:                                   # keep a lift at the bottom visible
            lift.draw(surf)


class CirculationDesk_(LibraryRoom):
    title = "Circulation Desk"
    spans = [(0, 600, "stacks", (100, 170)), (660, 950, "office", None)]
    seed = 1

    def build(self):
        self.make_walls()
        self.decor += [Sign(330, 46, "LIBRARY", TEXT), LinearLight(140, 200), LinearLight(800, 220),
                       Poster(150, 150, "QUIET", SVA_PURPLE)]
        self.furniture += [CirculationDesk(330, C.FLOOR_Y), ReturnBin(560, C.FLOOR_Y),
                           CardCatalog(660, C.FLOOR_Y), Plant(800, C.FLOOR_Y)]
        # the anti-theft gate by the door zaps on and off
        self.hazards.append(Zapper(230, y_top=380, y_bottom=C.FLOOR_Y, on_time=1.2, off_time=1.6))
        self.gate = pygame.Rect(214, 380, 32, 120)

    def draw_foreground(self, surf):
        super().draw_foreground(surf)
        for x in (self.gate.left, self.gate.right - 6):          # the two pillars of the security gate
            pygame.draw.rect(surf, (170, 172, 180), (x, self.gate.top, 6, self.gate.height), border_radius=2)


class TheStacks(LibraryRoom):
    """Ride the rolling ladder up to the top shelves."""

    title = "The Stacks"
    seed = 2

    def build(self):
        self.make_walls()
        shelving(self.wall, 20, C.W - 20, 70, C.FLOOR_Y - 10, random.Random(9), dim=0.3, unit=120)
        self.decor += [Sign(360, 46, "STACKS  A - M", TEXT), LinearLight(160, 220), LinearLight(780, 220)]
        self.platforms.append(Platform(110, 400, 230))
        self.platforms.append(Platform(450, 290, 260))
        self.lifts.append(Lift(370, y_top=290, y_bottom=C.FLOOR_Y, width=60))   # the rolling library ladder
        self.furniture += [SteelShelf(130, 400), SteelShelf(240, 400),
                           SteelShelf(480, 290), SteelShelf(610, 290), BookCart(740, C.FLOOR_Y)]
        self.hazards.append(Drone(800, y_top=300, y_bottom=C.FLOOR_Y, speed=80))

    def draw_foreground(self, surf):
        super().draw_foreground(surf)
        lift = self.lifts[0]
        rx = lift.rect.centerx
        steel = (150, 152, 158)
        for dx in (-22, 22):                                       # the ladder's rails ride with it
            pygame.draw.line(surf, steel, (rx + dx, lift.rect.top), (rx + dx, lift.rect.top - 70), 3)
        for k in range(1, 5):
            y = lift.rect.top - k * 16
            pygame.draw.line(surf, steel, (rx - 22, y), (rx + 22, y), 2)


class ReadingRoom(LibraryRoom):
    """The digit is in Special Collections, up on the high ledge past the book drop."""

    title = "Reading Room"
    spans = [(0, 540, "imacs", None)]
    seed = 3

    def build(self):
        self.make_walls()
        self.decor += [Sign(330, 46, "READING ROOM", TEXT), LinearLight(150, 220), LinearLight(800, 200)]
        self.platforms.append(Platform(560, 410, 200))
        self.platforms.append(Platform(720, 320, 150))
        self.furniture += [ReadingTable(110, C.FLOOR_Y), ReadingTable(340, C.FLOOR_Y), Plant(680, 410),
                           ArchiveCabinet(785, 320, holds_piece=True)]
        self.hazards.append(Crusher(610, y_top=240, y_bottom=410, w=50, h=40))    # the overnight book drop
        sign = pygame.font.Font(None, 22).render("SPECIAL COLLECTIONS", True, TEXT)
        self.wall.blit(sign, (730, 200))
        pygame.draw.rect(self.wall, SVA_PURPLE, (730, 220, sign.get_width(), 3))
        self.dust = pygame.Surface((C.W, 140), pygame.SRCALPHA)

    def draw_background(self, surf):
        super().draw_background(surf)
        t = self.time
        a = 20 + int(12 * (1 + math.sin(t * 2)))                  # a little dust in the LED light
        dust = self.dust
        dust.fill((0, 0, 0, 0))
        for k in range(18):
            x = (k * 53 + int(t * 12 * (1 + k % 3))) % C.W
            pygame.draw.circle(dust, (255, 255, 255, a), (x, (k * 37) % 140), 1)
        surf.blit(dust, (0, 330))


ROOMS = [CirculationDesk_, TheStacks, ReadingRoom]
