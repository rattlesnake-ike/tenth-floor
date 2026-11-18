"""SVA Animation, 6th floor: three life-drawing studios after hours.

West elevator -> Figure Drawing Studio -> Life Drawing Studio -> Charcoal Studio -> East elevator.

Search the easels, the cabinets and the models for the floor's digit. The models are posing nude (their private
areas are pixelated), and a model you search stares back: their eyes grow while you look them over and stay
wide afterwards. Instead of security robots, art teachers walk the studios. If you're on their level and in
front of them, they chase you (and tell you what they think of you). Get up on a model stand or a ledge to get
away. The digit is in the supply cabinet up on the Charcoal Studio's mezzanine: ride the lift up and wait for
the teacher up there to walk away before you search it.

Practise it alone with: python main.py --floor brent_shultz
"""
import math
import random

import pygame

from engine import config as C
from engine.kit import CeilingLight, Poster, ShockBot, Sign, Window
from engine.kit._base import KitFurniture, shade
from engine.room import Furniture, Lift, Platform, Room

NAME = "SVA Animation"
AUTHOR = "Brent Shultz"

INK = C.INK
WOOD = (150, 108, 70)
WOOD_DARK = (112, 78, 50)
SKIN = [(236, 196, 164), (198, 146, 104), (141, 94, 62), (222, 172, 132), (110, 72, 48)]
HAIR = [(40, 30, 24), (120, 72, 36), (210, 180, 120), (30, 30, 34), (150, 150, 150)]

_FONTS = {}


def font(size):
    """One pygame Font per size, made the first time a room is built (never while drawing)."""
    if size not in _FONTS:
        if not pygame.font.get_init():
            pygame.font.init()
        _FONTS[size] = pygame.font.Font(None, size)
    return _FONTS[size]


def mosaic(w, h, skin, seed):
    """The censor block: a little grid of skin tones, like a pixelated video."""
    rng = random.Random(seed)
    img = pygame.Surface((w, h))
    cell = 4
    for y in range(0, h, cell):
        for x in range(0, w, cell):
            img.fill(shade(skin, rng.choice([0.45, 0.6, 0.78, 0.95, 1.15, 1.3])), (x, y, cell, cell))
    pygame.draw.rect(img, shade(skin, 0.4), img.get_rect(), 1)
    return img


# --- the studio itself --------------------------------------------------------------------------------------

def studio_wall(seed, wall=(88, 80, 76)):
    """A night-time art studio wall: paint spatters, pinned-up figure drawings, a baseboard. Built once per room."""
    rng = random.Random(seed)
    img = pygame.Surface((C.W, C.FLOOR_Y))
    img.fill(wall)
    for x in range(0, C.W, 160):                                  # wall panels
        pygame.draw.line(img, shade(wall, 0.88), (x, 0), (x, C.FLOOR_Y), 2)
    for _ in range(70):                                           # years of paint on the walls
        col = rng.choice([(200, 70, 60), (60, 110, 170), (230, 190, 70), (240, 236, 226), (70, 140, 90)])
        x, y = rng.randrange(C.W), rng.randrange(150, C.FLOOR_Y)
        pygame.draw.circle(img, shade(col, 0.75), (x, y), rng.randint(1, 4))
    for _ in range(9):                                            # figure drawings pinned up high
        x, y = rng.randrange(20, C.W - 60), rng.randrange(190, 260)
        sheet = pygame.Rect(x, y, 34, 46)
        pygame.draw.rect(img, (226, 220, 204), sheet)
        cx = sheet.centerx + rng.randint(-3, 3)
        pygame.draw.circle(img, (60, 56, 52), (cx, y + 9), 4, 1)
        pygame.draw.line(img, (60, 56, 52), (cx, y + 13), (cx + rng.randint(-3, 3), y + 30), 2)
        pygame.draw.line(img, (60, 56, 52), (cx, y + 30), (cx - 6, y + 42), 1)
        pygame.draw.line(img, (60, 56, 52), (cx, y + 30), (cx + 6, y + 42), 1)
        pygame.draw.line(img, (60, 56, 52), (cx - 8, y + 18), (cx + 8, y + 20), 1)
        pygame.draw.circle(img, (200, 60, 50), (sheet.centerx, y + 2), 2)   # the push pin
    pygame.draw.rect(img, shade(wall, 0.6), (0, C.FLOOR_Y - 14, C.W, 14))   # baseboard
    return img


def spotlight(x, top_w=40, bottom_w=220):
    """The warm light on a model stand, drawn behind everything."""
    img = pygame.Surface((bottom_w, C.FLOOR_Y), pygame.SRCALPHA)
    a = (bottom_w - top_w) // 2
    pygame.draw.polygon(img, (255, 236, 180, 38), [(a, 0), (a + top_w, 0), (bottom_w, C.FLOOR_Y), (0, C.FLOOR_Y)])
    return img, x - bottom_w // 2


class ModelStand(Platform):
    """The model's wooden stand with a cloth over it. Stand on top like any ledge."""

    def __init__(self, x, y, width, cloth=(150, 50, 60)):
        super().__init__(x, y, width)
        self.cloth = cloth

    def draw(self, surf):
        r = self.rect
        box = pygame.Rect(r.left, r.top, r.width, C.FLOOR_Y - r.top)
        pygame.draw.rect(surf, WOOD, box)
        pygame.draw.rect(surf, WOOD_DARK, box, 3)
        drape = [(r.left + 6, r.top), (r.right - 10, r.top), (r.right - 26, r.top + 18), (r.left + 30, r.top + 26)]
        pygame.draw.polygon(surf, self.cloth, drape)
        pygame.draw.line(surf, shade(self.cloth, 1.3), (r.left + 6, r.top), (r.right - 10, r.top), 3)


class Mezzanine(Platform):
    """A wooden storage loft with a railing."""

    def draw(self, surf):
        r = self.rect
        pygame.draw.rect(surf, WOOD, r)
        pygame.draw.line(surf, WOOD_DARK, r.bottomleft, r.bottomright, 3)
        for x in range(r.left + 10, r.right, 40):                       # posts holding it up
            pygame.draw.line(surf, WOOD_DARK, (x, r.bottom), (x, C.FLOOR_Y), 4)


# --- furniture: easels, cabinets, models ---------------------------------------------------------------------

class StudioEasel(KitFurniture):
    """An easel with a half-finished figure drawing on it."""

    W, H, NAME = 60, 104, "easel"

    def __init__(self, x, y, name=None, holds_piece=False, seed=0, paper=(236, 230, 214)):
        super().__init__(x, y, name, holds_piece)
        self.seed, self.paper = seed, paper
        self.sketch = self.make_sketch()

    def make_sketch(self):
        rng = random.Random(self.seed)
        img = pygame.Surface((self.rect.w - 12, 50))
        img.fill(self.paper)
        cx = img.get_width() // 2 + rng.randint(-4, 4)
        lean = rng.randint(-4, 4)
        charcoal = (54, 50, 48)
        pygame.draw.circle(img, charcoal, (cx, 9), 5, 1)
        pygame.draw.line(img, charcoal, (cx, 14), (cx + lean, 30), 2)
        pygame.draw.line(img, charcoal, (cx - 9, 18), (cx + 9, 20), 1)
        pygame.draw.line(img, charcoal, (cx - 9, 18), (cx - 12 + lean, 30), 1)
        pygame.draw.line(img, charcoal, (cx + 9, 20), (cx + 11, 31), 1)
        pygame.draw.line(img, charcoal, (cx + lean, 30), (cx - 7, 46), 1)
        pygame.draw.line(img, charcoal, (cx + lean, 30), (cx + 8, 46), 1)
        for _ in range(5):                                                # loose gesture lines
            x0, y0 = rng.randrange(img.get_width()), rng.randrange(50)
            pygame.draw.line(img, (150, 144, 136), (x0, y0), (x0 + rng.randint(-10, 10), y0 + rng.randint(-8, 8)), 1)
        return img

    def draw(self, surf):
        r = self.rect
        leg = self.tone(WOOD)
        pygame.draw.line(surf, leg, (r.left + 6, r.bottom), (r.centerx, r.top), 4)
        pygame.draw.line(surf, leg, (r.right - 6, r.bottom), (r.centerx, r.top), 4)
        pygame.draw.line(surf, self.tone(WOOD_DARK), (r.centerx, r.top + 30), (r.centerx + 4, r.bottom), 3)
        pygame.draw.line(surf, self.tone(WOOD_DARK), (r.left + 4, r.top + 66), (r.right - 4, r.top + 66), 4)  # ledge
        canvas = pygame.Rect(r.left + 6, r.top + 14, r.w - 12, 50)
        surf.blit(self.sketch, canvas.topleft)
        if self.searched:
            dim = pygame.Surface(canvas.size, pygame.SRCALPHA)
            dim.fill((0, 0, 0, 70))
            surf.blit(dim, canvas.topleft)
        pygame.draw.rect(surf, INK, canvas, 2)


class SupplyCabinet(KitFurniture):
    """A tall paint-spattered supply cabinet with two doors."""

    W, H, NAME = 64, 96, "supply cabinet"

    def __init__(self, x, y, name=None, holds_piece=False, seed=0, w=None, h=None):
        super().__init__(x, y, name, holds_piece, w, h)
        rng = random.Random(seed)
        self.spots = [(rng.randrange(4, self.rect.w - 4), rng.randrange(4, self.rect.h - 4), rng.randint(1, 3),
                       rng.choice([(200, 70, 60), (60, 110, 170), (230, 190, 70), (240, 236, 226)]))
                      for _ in range(10)]

    def draw(self, surf):
        r = self.rect
        pygame.draw.rect(surf, self.tone((96, 104, 112)), r)
        half = r.w // 2
        for k in range(2):
            door = pygame.Rect(r.left + 4 + k * half, r.top + 4, half - 6, r.h - 8)
            pygame.draw.rect(surf, INK, door, 1)
            pygame.draw.rect(surf, (200, 200, 200), (door.right - 6 if k == 0 else door.left + 3, door.centery - 6, 3, 12))
        for x, y, rad, col in self.spots:
            pygame.draw.circle(surf, self.tone(col), (r.left + x, r.top + y), rad)
        if self.searched:                                                 # left ajar once you've looked
            pygame.draw.line(surf, INK, (r.left + half - 2, r.top + 4), (r.left + half + 6, r.top + 10), 2)
        pygame.draw.rect(surf, INK, r, 2)


class NudeModel(Furniture):
    """A life-drawing model, nude and posing, with the private areas pixelated.

    pose: "standing", "contrapposto", "seated" (on a stool) or "reclining" (on a stand).
    Search one and they look right back at you: the eyes grow while you search and stay wide afterwards.
    """

    SIZES = {"standing": (46, 112), "contrapposto": (46, 112), "seated": (60, 88), "reclining": (150, 46)}

    def __init__(self, x, y, pose="standing", skin=0, hair=0, chest=False, seed=0, holds_piece=False):
        w, h = self.SIZES[pose]
        super().__init__(x, y, w, h, "model", holds_piece)
        self.pose = pose
        self.skin, self.hair = SKIN[skin % len(SKIN)], HAIR[hair % len(HAIR)]
        self.chest = chest
        self.line = shade(self.skin, 0.6)
        self.groin_px = mosaic(20, 16, self.skin, seed)
        self.chest_px = mosaic(28, 12, self.skin, seed + 1) if chest else None
        self.tag = font(20).render("!", True, C.PIECE)

    # how wide the eyes are: 0 = calm, 1 = staring
    def stare(self):
        return 1.0 if self.searched else self.progress

    def draw_head(self, surf, cx, cy, face=1):
        pygame.draw.circle(surf, self.skin, (cx, cy), 9)
        pygame.draw.circle(surf, self.line, (cx, cy), 9, 1)
        pygame.draw.arc(surf, self.hair, (cx - 10, cy - 11, 20, 16), 0.2, math.pi - 0.2, 5)
        s = self.stare()
        rad = 1.4 + 4.6 * s
        for ex in (cx - 4 * face, cx + 3 * face):
            if s > 0.05:
                pygame.draw.circle(surf, (250, 250, 250), (int(ex), cy - 1), int(round(rad)))
                pygame.draw.circle(surf, INK, (int(ex), cy - 1), int(round(rad)), 1)
                pygame.draw.circle(surf, INK, (int(ex + face), cy - 1), max(1, int(rad * 0.45)))
            else:
                pygame.draw.circle(surf, INK, (int(ex), cy - 1), 1)
        if s > 0.6:                                                       # surprised mouth
            pygame.draw.circle(surf, (120, 40, 40), (cx + face, cy + 5), 2)
        else:
            pygame.draw.line(surf, self.line, (cx - 2, cy + 5), (cx + 3, cy + 5), 1)

    def limb(self, surf, a, b, width):
        pygame.draw.line(surf, self.skin, a, b, width)
        pygame.draw.circle(surf, self.skin, b, width // 2)

    def draw(self, surf):
        getattr(self, "draw_" + self.pose)(surf, self.rect.centerx, self.rect.bottom)
        if self.searched:
            surf.blit(self.tag, (self.rect.right - 4, self.rect.top - 6))

    def draw_standing(self, surf, cx, by, sway=0):
        hip = by - 50
        self.limb(surf, (cx - 5, hip), (cx - 7 - sway, by - 2), 8)                       # legs
        self.limb(surf, (cx + 5, hip), (cx + 7, by - 2), 8)
        torso = [(cx - 13, by - 92), (cx + 13, by - 92), (cx + 9, hip - 6), (cx + 12, hip + 4),
                 (cx - 12, hip + 4), (cx - 9, hip - 6)]
        pygame.draw.polygon(surf, self.skin, torso)
        pygame.draw.polygon(surf, self.line, torso, 1)
        if self.pose == "contrapposto":                                                   # hand on the hip
            self.limb(surf, (cx - 12, by - 88), (cx - 20, by - 68), 6)
            self.limb(surf, (cx - 20, by - 68), (cx - 11, hip - 2), 6)
            self.limb(surf, (cx + 12, by - 88), (cx + 20, by - 104), 6)                   # and behind the head
            self.limb(surf, (cx + 20, by - 104), (cx + 6, by - 108), 6)
        else:
            self.limb(surf, (cx - 12, by - 88), (cx - 17, by - 56), 6)
            self.limb(surf, (cx + 12, by - 88), (cx + 17, by - 56), 6)
        pygame.draw.rect(surf, self.skin, (cx - 3, by - 98, 6, 8))                        # neck
        self.draw_head(surf, cx, by - 103)
        if self.chest_px:
            surf.blit(self.chest_px, (cx - 14, by - 87))
        surf.blit(self.groin_px, (cx - 10, hip - 6))

    def draw_contrapposto(self, surf, cx, by):
        self.draw_standing(surf, cx, by, sway=5)

    def draw_seated(self, surf, cx, by):
        x0 = self.rect.left
        pygame.draw.rect(surf, WOOD, (x0 + 4, by - 40, 34, 7))                            # the stool
        for lx in (x0 + 8, x0 + 32):
            pygame.draw.line(surf, WOOD_DARK, (lx, by - 34), (lx, by), 4)
        hip_x, hip_y = x0 + 20, by - 46
        self.limb(surf, (hip_x, hip_y), (hip_x + 26, hip_y + 2), 9)                      # thighs, then shins
        self.limb(surf, (hip_x + 26, hip_y + 2), (hip_x + 30, by - 2), 8)
        torso = [(hip_x - 12, hip_y - 40), (hip_x + 12, hip_y - 40), (hip_x + 10, hip_y + 4), (hip_x - 10, hip_y + 4)]
        pygame.draw.polygon(surf, self.skin, torso)
        pygame.draw.polygon(surf, self.line, torso, 1)
        self.limb(surf, (hip_x + 10, hip_y - 36), (hip_x + 24, hip_y - 4), 6)             # hands on the knee
        self.limb(surf, (hip_x - 10, hip_y - 36), (hip_x - 14, hip_y - 6), 6)
        pygame.draw.rect(surf, self.skin, (hip_x - 3, hip_y - 46, 6, 8))
        self.draw_head(surf, hip_x + 1, hip_y - 52)
        if self.chest_px:
            surf.blit(self.chest_px, (hip_x - 14, hip_y - 35))
        surf.blit(self.groin_px, (hip_x - 3, hip_y - 9))

    def draw_reclining(self, surf, cx, by):
        x0 = self.rect.left
        y = by - 14
        self.limb(surf, (x0 + 22, y - 4), (x0 + 14, by - 2), 6)                           # propped on an elbow
        torso = [(x0 + 22, y - 12), (x0 + 82, y - 6), (x0 + 84, y + 8), (x0 + 22, y + 8)]
        pygame.draw.polygon(surf, self.skin, torso)
        pygame.draw.polygon(surf, self.line, torso, 1)
        self.limb(surf, (x0 + 80, y), (x0 + 116, y - 8), 9)                              # one knee up
        self.limb(surf, (x0 + 116, y - 8), (x0 + 142, y + 6), 8)
        self.limb(surf, (x0 + 80, y + 4), (x0 + 140, y + 10), 8)
        self.limb(surf, (x0 + 40, y - 8), (x0 + 70, y + 2), 6)                            # arm along the side
        self.draw_head(surf, x0 + 18, y - 22)
        if self.chest_px:
            surf.blit(self.chest_px, (x0 + 30, y - 12))
        surf.blit(self.groin_px, (x0 + 74, y - 8))


# --- the art teachers ----------------------------------------------------------------------------------------

LINES = ["Where's your sketchbook?!", "That's a 20-minute pose!", "Gesture, not contour!", "See me after crit!",
         "No phones in the studio!", "Check your proportions!", "Who let you in here?"]


class ArtTeacher:
    """An art teacher on patrol, instead of a security robot.

    Walks back and forth between left and right on the surface at y. If you're on the same level, in front of
    them and close, they turn red, shout, and chase you (a bit slower than you can run). They never leave
    their stretch of floor, so a ledge, a model stand or the far side of the room gets you away.
    """

    W, H = 28, 62

    def __init__(self, x, y, left, right, speed=60.0, chase=150.0, sight=340, seed=0):
        self.x = float(x)
        self.y_surface = int(y)
        self.left, self.right = int(left), int(right)
        self.speed, self.chase_speed, self.sight = float(speed), float(chase), int(sight)
        self.dir = 1
        self.alert = False
        self.memory = 0.0           # keeps chasing a moment after losing you
        self.t = seed * 0.37
        rng = random.Random(seed)
        self.skin = rng.choice(SKIN)
        self.hair = rng.choice([(150, 150, 150), (220, 220, 214), (60, 44, 34), (120, 72, 36)])
        self.top = rng.choice([(110, 60, 70), (60, 80, 110), (70, 96, 70), (150, 120, 70)])     # the cardigan
        self.beard = rng.random() < 0.5
        self.bubbles = [font(16).render(text, True, INK) for text in LINES]
        self.bubble = self.bubbles[seed % len(self.bubbles)]
        self.rect = pygame.Rect(int(self.x), self.y_surface - self.H, self.W, self.H)

    def update(self, dt, room, player):
        self.t += dt
        pc = player.rect.centerx
        level = abs(player.rect.bottom - self.y_surface) < 6
        near = abs(pc - self.rect.centerx) < self.sight and self.left - 40 <= pc <= self.right + 40
        ahead = (pc - self.rect.centerx) * self.dir > 0
        sees = level and near and ahead and getattr(player, "safe", 0) <= 0
        if sees and not self.alert:
            self.bubble = random.choice(self.bubbles)
        if sees:
            self.memory = 0.8
        else:
            self.memory = max(0.0, self.memory - dt)
        self.alert = sees or (self.memory > 0 and level and near)
        if self.alert:
            self.dir = 1 if pc > self.rect.centerx else -1
        v = self.chase_speed if self.alert else self.speed
        self.x += self.dir * v * dt
        if self.x < self.left:
            self.x = float(self.left)
            if not self.alert:
                self.dir = 1
        elif self.x + self.W > self.right:
            self.x = float(self.right - self.W)
            if not self.alert:
                self.dir = -1
        self.rect.x = int(self.x)

    def draw(self, surf):
        r = self.rect
        cx, d = r.centerx, self.dir
        step = math.sin(self.t * (14 if self.alert else 7)) * 6
        trousers = (54, 52, 60)
        pygame.draw.line(surf, trousers, (cx - 3, r.bottom - 24), (cx - 3 + step, r.bottom - 1), 7)    # legs
        pygame.draw.line(surf, trousers, (cx + 3, r.bottom - 24), (cx + 3 - step, r.bottom - 1), 7)
        body = pygame.Rect(r.left + 3, r.top + 18, r.w - 6, 24)
        pygame.draw.rect(surf, self.top, body, border_radius=5)
        pygame.draw.rect(surf, INK, body, 1, border_radius=5)
        pygame.draw.line(surf, shade(self.top, 0.7), (cx, body.top + 2), (cx, body.bottom - 2), 1)     # cardigan
        # the arm with the long brush: pointed at you when chasing, down at the side when not
        hand = (cx + d * 22, r.top + 18) if self.alert else (cx + d * 8, body.bottom + 2)
        pygame.draw.line(surf, self.top, (cx + d * 6, body.top + 4), hand, 5)
        tip = (hand[0] + d * 16, hand[1] - (10 if self.alert else -10))
        pygame.draw.line(surf, WOOD, hand, tip, 2)
        pygame.draw.circle(surf, (200, 70, 60), tip, 2)
        face = (232, 120, 110) if self.alert else self.skin
        head = (cx, r.top + 10)
        pygame.draw.circle(surf, face, head, 9)
        pygame.draw.circle(surf, INK, head, 9, 1)
        pygame.draw.arc(surf, self.hair, (head[0] - 10, head[1] - 11, 20, 14), 0.3, math.pi - 0.3, 4)
        if self.beard:
            pygame.draw.arc(surf, self.hair, (head[0] - 8, head[1] - 2, 16, 12), math.pi + 0.3, 2 * math.pi - 0.3, 4)
        ex = head[0] + d * 3
        pygame.draw.circle(surf, INK, (ex, head[1] - 1), 4, 1)                                     # glasses
        pygame.draw.circle(surf, INK, (ex - d * 7, head[1] - 1), 3, 1)
        if self.alert:
            pygame.draw.line(surf, INK, (ex - 4, head[1] - 7), (ex + 3, head[1] - 5 + d), 2)       # angry brow
            b = self.bubble
            box = pygame.Rect(0, 0, b.get_width() + 10, b.get_height() + 6)
            box.midbottom = (max(box.w // 2 + 4, min(C.W - box.w // 2 - 4, cx)), r.top - 8)
            pygame.draw.rect(surf, (250, 248, 240), box, border_radius=6)
            pygame.draw.rect(surf, INK, box, 1, border_radius=6)
            surf.blit(b, (box.left + 5, box.top + 3))


# --- the three studios ---------------------------------------------------------------------------------------

class StudioRoom(Room):
    """What all three studios share: the wall, the model's spotlight, the night windows."""

    wall_seed = 0
    light_x = 480

    def build(self):
        self.wall = studio_wall(self.wall_seed)
        self.light, self.light_left = spotlight(self.light_x)
        self.layout()

    def layout(self):
        raise NotImplementedError

    def draw_background(self, surf):
        surf.blit(self.wall, (0, 0))
        surf.blit(self.light, (self.light_left, 0))


class FigureDrawing(StudioRoom):
    """A standing model on a stand in the middle, easels around, one teacher on the floor."""

    title = "Figure Drawing Studio"
    wall_seed, light_x = 1, 470

    def layout(self):
        self.decor += [Window(90, 64, seed=6), Window(720, 64, seed=7), CeilingLight(470, cord=40),
                       Sign(330, 30, "6  ANIMATION  -  FIGURE DRAWING", size=26),
                       Poster(270, 96, "POSE", (60, 110, 170)), Poster(610, 96, "CRIT", (200, 90, 70))]
        self.platforms.append(ModelStand(400, 440, 150, cloth=(150, 50, 60)))
        self.furniture += [StudioEasel(150, C.FLOOR_Y, seed=1), StudioEasel(290, C.FLOOR_Y, seed=2),
                           NudeModel(452, 440, "contrapposto", skin=0, hair=1, chest=True, seed=11),
                           StudioEasel(600, C.FLOOR_Y, seed=3), SupplyCabinet(770, C.FLOOR_Y, seed=4)]
        self.hazards.append(ArtTeacher(640, C.FLOOR_Y, left=130, right=840, speed=60, chase=150, seed=1))


class LifeDrawing(StudioRoom):
    """A reclining model on a long stand, a seated model, and a ledge with the flat files."""

    title = "Life Drawing Studio"
    wall_seed, light_x = 2, 470

    def layout(self):
        self.decor += [Window(110, 64, seed=8), CeilingLight(470, cord=40), CeilingLight(160, cord=30),
                       Sign(350, 30, "LIFE DRAWING  -  NO PHOTOS", size=26),
                       Poster(560, 96, "SVA", (70, 140, 90)), Poster(820, 70, "2 MIN", (230, 160, 60))]
        self.platforms.append(ModelStand(360, 430, 230, cloth=(60, 90, 150)))
        self.platforms.append(Platform(650, 340, 210))
        self.furniture += [NudeModel(160, C.FLOOR_Y, "seated", skin=2, hair=0, chest=False, seed=21),
                           StudioEasel(250, C.FLOOR_Y, seed=5),
                           NudeModel(400, 430, "reclining", skin=3, hair=2, chest=True, seed=22),
                           StudioEasel(690, 340, seed=6), SupplyCabinet(780, 340, "flat files", seed=7, h=80),
                           StudioEasel(700, C.FLOOR_Y, seed=8)]
        self.hazards.append(ArtTeacher(560, C.FLOOR_Y, left=120, right=850, speed=70, chase=155, seed=2))
        self.hazards.append(ShockBot(600, C.FLOOR_Y, left=450, right=860))     # jump its bolt, or get up on the stand


class CharcoalStudio(StudioRoom):
    """The last studio before the East elevator. The digit is in the supply cabinet on the mezzanine."""

    title = "Charcoal Studio"
    wall_seed, light_x = 3, 250

    def layout(self):
        self.decor += [Window(380, 64, seed=9), CeilingLight(250, cord=40), CeilingLight(740, cord=30),
                       Sign(120, 30, "CHARCOAL STUDIO", size=26), Poster(470, 200, "INK", (40, 40, 48))]
        self.platforms.append(ModelStand(170, 450, 150, cloth=(90, 130, 80)))
        self.platforms.append(Mezzanine(600, 300, 270))
        self.lifts.append(Lift(526, 300, C.FLOOR_Y, width=64))
        self.furniture += [NudeModel(222, 450, "standing", skin=4, hair=3, chest=False, seed=31),
                           StudioEasel(360, C.FLOOR_Y, seed=9), StudioEasel(440, C.FLOOR_Y, seed=10),
                           SupplyCabinet(640, 300, seed=12, holds_piece=True),
                           StudioEasel(790, 300, seed=13),
                           SupplyCabinet(720, C.FLOOR_Y, seed=14)]
        self.hazards.append(ArtTeacher(300, C.FLOOR_Y, left=120, right=850, speed=65, chase=150, seed=3))
        self.hazards.append(ArtTeacher(800, 300, left=630, right=868, speed=55, chase=120, sight=220, seed=4))


ROOMS = [FigureDrawing, LifeDrawing, CharcoalStudio]
