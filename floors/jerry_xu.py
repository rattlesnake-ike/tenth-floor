"""Floor 12: the Installation Lab and the XR Lab, as five platformer levels.

Run-and-jump platforming (coins, item crates you hit from below, bots you stomp, springs) and portal
puzzles (a portal device, white panels that take portals, momentum through portals, cubes, buttons,
doors, light bridges, a fizzler). Everything lives in this file; the engine is untouched.

Controls, on top of the engine's (arrows / WASD to move, SPACE to jump, UP to search):
    Mouse        aim the portal device
    Left click   blue portal      (or E)
    Right click  orange portal    (or Q)
    DOWN or S    grab / drop a cube, press a switch   (F is the game's flashlight)

Levels, west to east:   1 Orientation (the tutorial)  ->  2 Installation Lab  ->  3 Fabrication Bay
                        ->  4 XR Tracking Floor  ->  5 XR Holo Stage (the code digit)

Every level has a step-by-step guide (top left) and an arrow over what to do next. With the portal
device, a dotted line shows where a portal would land: a ring on a white panel, a red X anywhere else.
The look: white industrial lab walls, with fast diagonal stripes and speed streaks when you fly.
Coming in from the east (floor 12 is reached by the East elevator), doors and bridges you arrive
behind are already open, so each level can be crossed from either side. The digit's own puzzle
(cube on the button turns off the laser grid) has to be solved from whichever side you come in.
"""
import math
import random
import threading
from array import array

import pygame

from engine import config as C
from engine.kit import CeilingLight, Easel, FilingCabinet, Locker, Plant, Plinth, Poster, Printer3D, ServerRack, Window
from engine.player import Player
from engine.room import Furniture, Lift, Platform, Room

NAME = "Installation Lab + XR Lab"
AUTHOR = "Jerry Xu"

PW, PH = Player.W, Player.H

# What you carry from level to level (kept across rooms; the engine rebuilds a room every time you enter it).
RUN = {"coins": 0, "taken": set(), "device": False, "boots": False, "helmet": False, "star": 0.0,
       "helmet_at": 20, "card": False}

BLUE = (70, 160, 255)
ORANGE = (255, 150, 40)
PANEL = (226, 230, 236)
CONCRETE = (58, 60, 70)
GOO = (120, 200, 60)
HARD_LIGHT = (130, 210, 255)
GUIDE = (255, 214, 90)
INK2 = (14, 16, 22)

_FONTS = {}


def _font(size):
    if size not in _FONTS:
        pygame.font.init()
        _FONTS[size] = pygame.font.Font(None, size)
    return _FONTS[size]


# --- sound: the floor's own effects, made from waves in code (no files), like engine/sound.py ---------------
# They only play once the game has the mixer running (the engine starts it); in the check there's no sound,
# and every call quietly does nothing.

_RATE = 22050
_SFX = {}
_SFX_STATE = {"started": False}


def _wave(secs, fn, vol):
    n = int(_RATE * secs)
    return [vol * fn(i / _RATE, i / max(1, n - 1)) for i in range(n)]


def _glide(f0, f1, secs, vol=0.2, shape="sine", wobble=0.0):
    ph = [0.0]

    def fn(t, u):
        f = f0 + (f1 - f0) * u
        if wobble:
            f *= 1 + wobble * math.sin(2 * math.pi * 9 * t)
        ph[0] = (ph[0] + f / _RATE) % 1.0
        x = ph[0]
        v = math.sin(2 * math.pi * x) if shape == "sine" else (1.0 if x < 0.5 else -1.0) if shape == "square" \
            else 4 * abs(x - 0.5) - 1
        return v * min(1.0, t / 0.004) * (1 - u) ** 1.5
    return _wave(secs, fn, vol)


def _hiss(secs, vol=0.15, falling=True):
    rng = random.Random(7)
    last = [0.0]

    def fn(t, u):
        last[0] = 0.6 * last[0] + 0.4 * rng.uniform(-1, 1)          # a soft, filtered noise
        return last[0] * ((1 - u) if falling else math.sin(math.pi * u))
    return _wave(secs, fn, vol)


def _mixw(*waves):
    n = max(len(w) for w in waves)
    return [sum(w[i] for w in waves if i < len(w)) for i in range(n)]


def _then(*waves):
    out = []
    for w in waves:
        out += w
    return out


def _sfx_waves():
    return {
        "blue": _mixw(_glide(420, 980, 0.22, 0.16), _hiss(0.22, 0.05, falling=False)),
        "orange": _mixw(_glide(330, 760, 0.22, 0.16), _hiss(0.22, 0.05, falling=False)),
        "fizzle": _mixw(_glide(180, 120, 0.18, 0.12, "square"), _hiss(0.18, 0.08)),
        "warp": _mixw(_glide(200, 1400, 0.28, 0.12, "tri"), _hiss(0.32, 0.12, falling=False)),
        "coin": _then(_glide(988, 988, 0.06, 0.10, "square"), _glide(1319, 1319, 0.16, 0.10, "square")),
        "bump": _mixw(_glide(160, 90, 0.12, 0.25), _hiss(0.08, 0.10)),
        "power": _then(*[_glide(f, f, 0.07, 0.11, "tri") for f in (523, 659, 784, 1047)], _glide(1319, 1319, 0.25, 0.11, "tri")),
        "stomp": _mixw(_glide(300, 70, 0.16, 0.25), _hiss(0.1, 0.12)),
        "spring": _glide(220, 880, 0.3, 0.16, "sine", wobble=0.08),
        "button": _then(_hiss(0.02, 0.15), _glide(600, 900, 0.12, 0.12, "tri")),
        "door": _mixw(_glide(110, 150, 0.4, 0.10, "tri"), _hiss(0.4, 0.06, falling=False)),
        "bridge": _mixw(_glide(660, 990, 0.35, 0.08), _glide(990, 1320, 0.35, 0.05)),
        "grab": _then(_hiss(0.015, 0.12), _glide(500, 700, 0.06, 0.10, "tri")),
        "drop": _then(_hiss(0.015, 0.12), _glide(500, 330, 0.08, 0.10, "tri")),
        "step": _then(_glide(784, 784, 0.08, 0.07, "tri"), _glide(1175, 1175, 0.22, 0.07, "tri")),
        "device": _then(*[_glide(f, f * 1.5, 0.09, 0.10, "tri") for f in (392, 523, 659)], _glide(1047, 1568, 0.3, 0.1)),
    }


def _make_sfx():
    try:
        freq, _size, channels = pygame.mixer.get_init()
        for name, w in _sfx_waves().items():
            if freq != _RATE:
                step = _RATE / freq
                w = [w[int(i * step)] for i in range(int(len(w) / step))]
            pcm = array("h", (int(max(-1.0, min(1.0, v)) * 32767) for v in w for _ in range(channels)))
            _SFX[name] = pygame.mixer.Sound(buffer=pcm.tobytes())
    except Exception:          # no sound on this machine: stay quiet
        pass


def sfx(name):
    """Play one of the floor's effects. Does nothing until the game's mixer is up and the sounds are made."""
    try:
        if not pygame.mixer.get_init():
            return
    except Exception:
        return
    if not _SFX_STATE["started"]:
        _SFX_STATE["started"] = True
        threading.Thread(target=_make_sfx, daemon=True).start()
        return
    snd = _SFX.get(name)
    if snd is not None:
        snd.play()


# --- input the engine doesn't hand to rooms: the mouse and a few extra keys ---------------------------

_FAKE = None    # tests set this to {"pressed": {...}, "aim": (x, y)} to drive the floor without a keyboard


class _Input:
    KEYS = {"blue": ("K_e",), "orange": ("K_q",), "use": ("K_DOWN", "K_s")}

    def __init__(self):
        self.was = set()

    def poll(self):
        """Returns (actions pressed this frame, mouse position or None)."""
        if _FAKE is not None:
            return set(_FAKE.get("pressed", ())), _FAKE.get("aim")
        held, aim = set(), None
        try:
            k = pygame.key.get_pressed()
            for name, codes in self.KEYS.items():
                if any(k[getattr(pygame, c)] for c in codes):
                    held.add(name)
            b = pygame.mouse.get_pressed()
            if b[0]:
                held.add("blue")
            if b[2]:
                held.add("orange")
            if pygame.display.get_surface() is not None and pygame.mouse.get_focused():
                aim = pygame.mouse.get_pos()
        except pygame.error:
            pass
        pressed = held - self.was
        self.was = held
        return pressed, aim


INPUT = _Input()


def _overlap_x(a, b):
    return min(a.right, b.right) - max(a.left, b.left)


def _ray_hit(ox, oy, dx, dy, r):
    """Where a ray from (ox, oy) along (dx, dy) first enters rect r: (t, face) or None.
    face is the side it hits, named by the way that side faces: 'left', 'right', 'up', 'down'."""
    tmin, tmax, face = -1e9, 1e9, None
    for o, d, lo, hi, axis in ((ox, dx, r.left, r.right, "x"), (oy, dy, r.top, r.bottom, "y")):
        if abs(d) < 1e-9:
            if o < lo or o > hi:
                return None
            continue
        t1, t2 = (lo - o) / d, (hi - o) / d
        if t1 > t2:
            t1, t2 = t2, t1
        if t1 > tmin:
            tmin = t1
            face = ("left" if d > 0 else "right") if axis == "x" else ("up" if d > 0 else "down")
        tmax = min(tmax, t2)
        if tmin > tmax:
            return None
    if tmin < 0 or face is None:
        return None
    return tmin, face


# --- the level pieces ----------------------------------------------------------------------------------

class Wall:
    """A solid block: you can't walk or jump through it, and you can stand on its top.
    panels: faces that take portals, as (face, start, end) with face 'left' / 'right' / 'up' / 'down'."""

    def __init__(self, x, y, w, h, panels=()):
        self.rect = pygame.Rect(x, y, w, h)
        self.panels = [Panel(self, *p) for p in panels]

    @property
    def solid(self):
        return True

    def draw(self, surf):
        r = self.rect
        pygame.draw.rect(surf, CONCRETE, r)
        pygame.draw.rect(surf, (74, 77, 90), (r.left, r.top, r.width, 4))           # lit top edge
        pygame.draw.rect(surf, (48, 50, 58), (r.right - 5, r.top, 5, r.height))     # shaded side
        for y in range(r.top + 24, r.bottom, 24):
            pygame.draw.line(surf, (50, 52, 60), (r.left + 2, y), (r.right - 6, y), 1)
        pygame.draw.rect(surf, INK2, r, 2)


class Door(Wall):
    """A wall that slides up out of the way while its signal is on."""

    def __init__(self, x, y, w, h, link):
        super().__init__(x, y, w, h)
        self.link = link
        self.open = 0.0      # 0 shut .. 1 fully open
        self.want = False

    @property
    def solid(self):
        return self.open < 0.8

    def step(self, dt, on):
        self.want = on
        self.open = max(0.0, min(1.0, self.open + (dt * 2.5 if on else -dt * 2.5)))

    def draw(self, surf):
        r = self.rect
        pygame.draw.rect(surf, (36, 38, 46), r.inflate(6, 0), 3)                   # the frame
        h = int(r.height * (1 - self.open))
        if h > 0:
            body = pygame.Rect(r.left, r.top, r.width, h)
            pygame.draw.rect(surf, (104, 108, 124), body)
            for y in range(body.bottom - 14, body.top, -28):
                pygame.draw.line(surf, (88, 92, 106), (body.left + 3, y), (body.right - 3, y), 2)
            pygame.draw.rect(surf, (230, 190, 60), (body.left, body.bottom - 10, body.width, 10))
            for x in range(body.left - 6, body.right, 8):                             # hazard stripes at the foot
                pygame.draw.line(surf, INK2, (x, body.bottom), (x + 8, body.bottom - 10), 2)
            pygame.draw.rect(surf, INK2, body, 2)
            lamp = (90, 220, 120) if self.want else C.DANGER
            pygame.draw.circle(surf, lamp, (r.centerx, body.bottom - 22), 5)


class GlassWall(Door):
    """A pane of glass: you can't walk through it, but portal shots go straight through.
    It's open from the start if you come in from the east."""

    glass = True

    def __init__(self, x, y, w, h):
        super().__init__(x, y, w, h, link="glass")
        self.pane = pygame.Surface((w, h), pygame.SRCALPHA)                 # made once, not every frame
        self.pane.fill((150, 210, 255, 60))
        for k in range(0, h, 90):
            pygame.draw.line(self.pane, (255, 255, 255, 130), (2, k + 30), (w - 3, k + 10), 2)

    def draw(self, surf):
        r = self.rect
        h = int(r.height * (1 - self.open))
        pygame.draw.rect(surf, (60, 64, 76), (r.left - 4, r.top - 6, r.width + 8, 6))
        pygame.draw.rect(surf, (60, 64, 76), (r.left - 4, r.bottom, r.width + 8, 4))
        if h > 0:
            surf.blit(self.pane, r.topleft, (0, r.height - h, r.width, h))
            pygame.draw.rect(surf, (90, 150, 200), (r.left, r.top, r.width, h), 2)


class Panel:
    """A white strip on one face of a wall (or on the floor) that takes portals."""

    def __init__(self, wall, face, start, end):
        self.wall, self.face = wall, face
        r = wall.rect
        if face == "left":
            self.rect = pygame.Rect(r.left - 4, start, 4, end - start)
        elif face == "right":
            self.rect = pygame.Rect(r.right, start, 4, end - start)
        elif face == "up":
            self.rect = pygame.Rect(start, r.top - 4, end - start, 4)
        else:
            self.rect = pygame.Rect(start, r.bottom, end - start, 4)
        self.vertical = face in ("left", "right")

    highlight = False        # the guide sets this on the panel it wants you to shoot

    def draw(self, surf, t=0.0):
        r = self.rect
        glow = 0.5 + 0.5 * math.sin(t * 5)
        edge = (int(60 + 120 * glow), int(190 + 60 * glow), 255) if self.highlight else (60, 190, 255)
        pygame.draw.rect(surf, INK2, r.inflate(10, 10), border_radius=3)        # a dark frame, so white
        pygame.draw.rect(surf, edge, r.inflate(6, 6), border_radius=2)          # panels stand out on white walls
        pygame.draw.rect(surf, (250, 252, 255), r)
        if self.highlight:
            pygame.draw.rect(surf, edge, r.inflate(16 + int(6 * glow), 16 + int(6 * glow)), 2, border_radius=4)


class FloorPanel(Panel):
    """A portal panel set into the ground."""

    def __init__(self, x0, x1):
        self.wall, self.face, self.vertical = None, "up", False
        self.rect = pygame.Rect(x0, C.FLOOR_Y - 4, x1 - x0, 4)


class Portal:
    HALF_WALL, HALF_FLOOR = 32, 30

    def __init__(self, color, panel, along):
        self.color, self.panel, self.normal = color, panel, panel.face
        half = self.HALF_WALL if panel.vertical else self.HALF_FLOOR
        r = panel.rect
        lo, hi = (r.top, r.bottom) if panel.vertical else (r.left, r.right)
        self.c = max(lo + half, min(hi - half, along))
        self.lo, self.hi = self.c - half, self.c + half
        self.face_at = {"left": r.left, "right": r.right, "up": r.top, "down": r.bottom}[self.normal]
        self.t = 0.0
        if panel.vertical:
            self.box = pygame.Rect(0, 0, 20, int(self.hi - self.lo))
            self.box.center = (self.face_at, int(self.c))
        else:
            self.box = pygame.Rect(0, 0, int(self.hi - self.lo), 16)
            self.box.center = (int(self.c), self.face_at)
        self.halo = pygame.Surface(self.box.inflate(28, 28).size, pygame.SRCALPHA)   # made once
        for k, a in ((0, 40), (8, 60), (14, 90)):
            pygame.draw.ellipse(self.halo, (*color, a), self.halo.get_rect().inflate(-k, -k))

    def entering(self, p, room):
        """Is the player going in? Returns their speed if so, else None."""
        r = p.rect
        moving = p.vx + room.fling
        n, f = self.normal, self.face_at
        if n == "up":
            if self.lo <= r.centerx <= self.hi and f - 3 <= r.bottom <= f + 24 and (p.on is not None or p.vy >= 0):
                return max(room.last_vy, p.vy, 0.0)
        elif n == "down":
            if self.lo <= r.centerx <= self.hi and f - 24 <= r.top <= f + 3 and p.vy < 0:
                return -p.vy
        elif n == "right":
            if self.lo <= r.centery <= self.hi and f - 24 <= r.left <= f + 3 and moving < 0:
                return -moving
        elif n == "left":
            if self.lo <= r.centery <= self.hi and f - 3 <= r.right <= f + 24 and moving > 0:
                return moving
        return None

    def draw(self, surf):
        self.t += 1 / 60
        box = self.box
        surf.blit(self.halo, box.inflate(28, 28).topleft)
        pygame.draw.ellipse(surf, (16, 18, 26), box)
        if min(box.size) > 12:
            pygame.draw.ellipse(surf, tuple(c // 3 for c in self.color), box.inflate(-6, -6), 2)
        pygame.draw.ellipse(surf, self.color, box, 3)
        a = self.t * 4                                                     # two sparks circling the rim
        for k in (0, math.pi):
            sx = box.centerx + math.cos(a + k) * box.width / 2
            sy = box.centery + math.sin(a + k) * box.height / 2
            pygame.draw.circle(surf, (255, 255, 255), (int(sx), int(sy)), 2)


class Coin:
    R = 8

    def __init__(self, key, x, y):
        self.key, self.x, self.y = key, x, y
        self.rect = pygame.Rect(x - self.R, y - self.R, 2 * self.R, 2 * self.R)

    def draw(self, surf, t):
        w = max(2, int(self.R * 2 * abs(math.cos(t * 3 + self.x * 0.05))))
        box = pygame.Rect(0, 0, w, self.R * 2)
        box.center = (self.x, self.y)
        pygame.draw.ellipse(surf, C.PIECE, box)
        pygame.draw.ellipse(surf, (160, 110, 20), box, 2)


class Crate(Platform):
    """A floating supply crate: stand on it, or jump into it from below to knock out what's inside."""

    S = 40
    ICON = {"coin": C.PIECE, "boots": (90, 200, 255), "helmet": (240, 200, 60), "star": (255, 120, 220)}

    def __init__(self, key, x, top, contents):
        super().__init__(x, top, self.S)
        self.rect = pygame.Rect(int(x), int(top), self.S, self.S)
        self.key, self.contents = key, contents
        self.used = key in RUN["taken"]
        self.bounce = 0.0

    def draw(self, surf):
        r = self.rect.move(0, -int(6 * math.sin(self.bounce * math.pi)) if self.bounce > 0 else 0)
        if self.used:
            pygame.draw.rect(surf, (128, 132, 142), r, border_radius=4)
            pygame.draw.rect(surf, (104, 108, 118), r.inflate(-12, -12), 2, border_radius=3)
        else:
            pygame.draw.rect(surf, (214, 154, 62), r, border_radius=4)
            pygame.draw.rect(surf, (238, 186, 92), (r.left + 2, r.top + 2, r.width - 4, 8), border_radius=3)
            pygame.draw.rect(surf, (170, 116, 44), (r.left + 2, r.bottom - 8, r.width - 4, 6), border_radius=3)
            pygame.draw.rect(surf, (250, 222, 150), r.inflate(-14, -14), 2, border_radius=3)
            pygame.draw.circle(surf, self.ICON[self.contents], r.center, 6)
            pygame.draw.circle(surf, INK2, r.center, 6, 1)
        pygame.draw.rect(surf, INK2, r, 2, border_radius=4)


class Spring(Platform):
    """A bounce pad. Land on it and it throws you high."""

    V = 950.0

    def __init__(self, x, width=56):
        super().__init__(x, C.FLOOR_Y - 10, width)
        self.squash = 0.0

    def draw(self, surf):
        r = self.rect
        h = 10 - int(6 * self.squash)
        base = pygame.Rect(r.left + 6, C.FLOOR_Y - 4, r.width - 12, 4)
        pygame.draw.rect(surf, (70, 70, 80), base)
        top = pygame.Rect(r.left, C.FLOOR_Y - 4 - h, r.width, 6)
        for i in range(3):
            y = top.bottom + i * 2
            pygame.draw.line(surf, (200, 200, 210), (r.left + 10, y), (r.right - 10, y), 1)
        pygame.draw.rect(surf, (230, 80, 80), top, border_radius=3)


class Ledge(Platform):
    """A steel catwalk: an ordinary one-way ledge with a nicer look."""

    def draw(self, surf):
        r = self.rect
        for x in (r.left + 14, r.right - 14):
            pygame.draw.line(surf, (70, 74, 86), (x, r.bottom), (x - 10, r.bottom + 14), 3)
        pygame.draw.rect(surf, (96, 102, 116), r, border_radius=2)
        pygame.draw.rect(surf, (168, 174, 188), (r.left, r.top, r.width, 3))
        pygame.draw.rect(surf, GUIDE, (r.left, r.bottom - 3, r.width, 3))
        for x in range(r.left + 10, r.right - 6, 26):
            pygame.draw.circle(surf, (70, 74, 86), (x, r.top + 7), 2)
        pygame.draw.rect(surf, INK2, r, 1, border_radius=2)


class LightBridge(Platform):
    """A bridge of hard light: it's only there while its signal is on."""

    def draw(self, surf):
        r = self.rect
        pygame.draw.rect(surf, HARD_LIGHT, (r.left, r.top, r.width, 6))
        pygame.draw.line(surf, (230, 250, 255), (r.left, r.top + 1), (r.right, r.top + 1), 2)


class Cube:
    S = 26

    def __init__(self, home):
        self.home = home
        self.respawn()

    def respawn(self):
        self.x, self.y = float(self.home[0]), float(self.home[1] - self.S - 120)
        self.vy, self.carried = 0.0, False

    @property
    def rect(self):
        return pygame.Rect(int(self.x), int(self.y), self.S, self.S)

    def fall(self, dt, room):
        prev = self.y + self.S
        self.vy = min(C.MAX_FALL, self.vy + C.GRAVITY * dt)
        self.y += self.vy * dt
        bottom, best = self.y + self.S, None
        for s in room.surfaces():
            r = s.rect
            if self.x + self.S > r.left and self.x < r.right and prev <= r.top + 1 and bottom >= r.top:
                best = r.top if best is None else min(best, r.top)
        if best is not None:
            self.y, self.vy = float(best - self.S), 0.0
        if self.y > C.H:
            self.respawn()

    def draw(self, surf):
        r = self.rect
        pygame.draw.rect(surf, (170, 176, 190), r, border_radius=4)
        pygame.draw.rect(surf, C.INK, r, 2, border_radius=4)
        pygame.draw.circle(surf, (255, 140, 190), r.center, 6)
        pygame.draw.circle(surf, C.INK, r.center, 6, 1)


class Dispenser:
    """The tube a cube drops out of."""

    def __init__(self, x):
        self.x = x

    def draw(self, surf):
        r = pygame.Rect(self.x - 6, 36, Cube.S + 12, 40)
        pygame.draw.rect(surf, (90, 94, 108), r, border_radius=4)
        pygame.draw.rect(surf, C.INK, r, 2, border_radius=4)
        pygame.draw.rect(surf, (30, 30, 36), (r.left + 6, r.bottom - 6, r.width - 12, 6))


class Button:
    """A floor button. Weighed down by a cube (or you standing on it). latch=True stays on once pressed."""

    def __init__(self, x, y, link, latch=False):
        self.y, self.link, self.latch = y, link, latch
        self.rect = pygame.Rect(x, y - 8, 64, 8)
        self.down = self.latched = False

    def step(self, room, p):
        weight = any(not c.carried and abs(c.rect.bottom - self.y) <= 2 and _overlap_x(c.rect, self.rect) >= 8
                     for c in room.cubes)
        if p.on is not None and abs(p.rect.bottom - self.y) <= 2 and _overlap_x(p.rect, self.rect) >= 6:
            weight = True
        if self.latch and weight:
            self.latched = True
        self.down = weight or self.latched

    def draw(self, surf):
        r = self.rect
        pygame.draw.rect(surf, (60, 60, 70), (r.left - 4, self.y - 4, r.width + 8, 4))
        cap = pygame.Rect(r.left + 6, self.y - (4 if self.down else 10), r.width - 12, 6)
        pygame.draw.rect(surf, (90, 220, 120) if self.down else C.DANGER, cap, border_radius=3)
        pygame.draw.rect(surf, C.INK, cap, 1, border_radius=3)


class Switch:
    """A pedestal switch: press DOWN next to it and its signal stays on for `seconds`, ticking down."""

    def __init__(self, x, link, seconds):
        self.x, self.link, self.seconds = x, link, seconds
        self.rect = pygame.Rect(x, C.FLOOR_Y - 56, 20, 56)
        self.left = 0.0

    def draw(self, surf):
        r = self.rect
        pygame.draw.rect(surf, (80, 84, 96), (r.left + 6, r.top + 12, 8, r.height - 12))
        pygame.draw.rect(surf, (60, 62, 72), (r.left - 6, C.FLOOR_Y - 6, r.width + 12, 6))
        on = self.left > 0
        pygame.draw.circle(surf, (90, 220, 120) if on else (240, 80, 80), (r.centerx, r.top + 8), 9)
        pygame.draw.circle(surf, C.INK, (r.centerx, r.top + 8), 9, 2)
        if on:
            frac = self.left / self.seconds
            ring = pygame.Rect(r.centerx - 16, r.top - 8, 32, 32)
            pygame.draw.arc(surf, (230, 250, 255), ring, math.pi / 2, math.pi / 2 + 2 * math.pi * frac, 3)


class DevicePedestal:
    """Where the portal device sits until you walk into it."""

    def __init__(self, x):
        self.rect = pygame.Rect(x, C.FLOOR_Y - 60, 40, 60)

    def draw(self, surf, t):
        r = self.rect
        pygame.draw.rect(surf, (200, 204, 214), (r.left + 4, r.top + 30, r.width - 8, 30), border_radius=4)
        pygame.draw.rect(surf, C.INK, (r.left + 4, r.top + 30, r.width - 8, 30), 2, border_radius=4)
        y = r.top + 12 + int(4 * math.sin(t * 3))
        pygame.draw.rect(surf, (240, 240, 245), (r.left + 6, y, 28, 12), border_radius=5)
        pygame.draw.circle(surf, BLUE, (r.left + 12, y + 6), 4)
        pygame.draw.circle(surf, ORANGE, (r.left + 28, y + 6), 4)


class Fizzler:
    """A shimmering field. Walk through it and your portals close; a cube you're carrying dissolves."""

    def __init__(self, x):
        self.rect = pygame.Rect(x, 40, 10, C.FLOOR_Y - 40)

    def draw(self, surf, t):
        r = self.rect
        pygame.draw.rect(surf, (60, 64, 80), (r.left - 3, r.top, 3, r.height))
        pygame.draw.rect(surf, (60, 64, 80), (r.right, r.top, 3, r.height))
        for i in range(0, r.height, 18):
            y = r.top + (i + int(t * 60)) % r.height
            pygame.draw.line(surf, (140, 200, 255), (r.left, y), (r.right, y + 6), 1)


# --- hazards (each has .rect, .update(dt, room, player), .draw(surf); an empty rect can't hurt) -----

NO_RECT = pygame.Rect(0, 0, 0, 0)


def _shield(p):
    """Something is about to hit the player. A helmet takes the hit instead. True if they're safe."""
    if p.safe > 0:
        return True
    if RUN["helmet"]:
        RUN["helmet"] = False
        p.safe = 1.5
        return True
    return False


class StompBot:
    """A little security bot that rolls back and forth. Touch its side and you're caught; land on it and
    it's done for."""

    W, H = 34, 30

    def __init__(self, x, y, left, right, speed=70.0):
        self.x, self.y_surface, self.left, self.right, self.speed = float(x), y, left, right, speed
        self.dir = 1
        self.box = pygame.Rect(int(x), y - self.H, self.W, self.H)
        self.rect = self.box.copy()
        self.was_above = False
        self.dead = 0.0      # > 0 while it's squashed
        self.t = 0.0

    def update(self, dt, room, player):
        self.t += dt
        if self.dead:
            self.dead += dt
            self.rect = NO_RECT
            return
        self.x += self.dir * self.speed * dt
        if self.x < self.left:
            self.x, self.dir = float(self.left), 1
        elif self.x + self.W > self.right:
            self.x, self.dir = float(self.right - self.W), -1
        self.box.x = int(self.x)
        r = player.rect
        touching = r.colliderect(self.box)
        if touching and (RUN["star"] > 0 or (self.was_above and player.vy > 0)):
            self.dead = 0.01
            self.rect = NO_RECT
            if RUN["star"] <= 0:
                player.vy = -430.0          # bounce off it
                player.on = None
                room.launched = True
            room.add_coins(1, "Bot stomped")
            room.effect("stomp", self.box.centerx, self.box.top, (150, 156, 170), 14)
            return
        above = r.bottom <= self.box.top + 6 and _overlap_x(r, self.box) > -20
        self.was_above = above
        self.rect = NO_RECT if above else self.box
        if touching and not above:
            _shield(player)

    def draw(self, surf):
        if self.dead:
            if self.dead < 0.6:
                flat = pygame.Rect(self.box.left, self.box.bottom - 8, self.W, 8)
                pygame.draw.rect(surf, (60, 64, 72), flat, border_radius=3)
            return
        r = self.box
        pygame.draw.rect(surf, (70, 74, 86), r, border_radius=10)
        pygame.draw.rect(surf, C.INK, r, 2, border_radius=10)
        pygame.draw.circle(surf, (120, 220, 255), (r.centerx + self.dir * 7, r.top + 11), 5)
        pygame.draw.line(surf, C.INK, (r.centerx, r.top), (r.centerx - self.dir * 6, r.top - 9), 2)
        pygame.draw.circle(surf, C.DANGER, (r.centerx - self.dir * 6, r.top - 10), 3)
        wob = int(2 * math.sin(self.t * 14))
        pygame.draw.circle(surf, C.INK, (r.left + 7, r.bottom), 4 + (wob > 0))
        pygame.draw.circle(surf, C.INK, (r.right - 7, r.bottom), 4 + (wob <= 0))


class Turret:
    """A sentry on the floor. It sees along its eye line; when it sees you it charges, then fires.
    It can't see over a light bridge. Land on it to knock it over."""

    W, H = 30, 44
    RANGE = 640

    def __init__(self, x, y, facing=-1):
        self.dir = facing           # (a .dir also tells the check this hazard isn't parked in a doorway)
        self.box = pygame.Rect(x, y - self.H, self.W, self.H)
        self.eye = self.box.top + 14
        self.state, self.t = "idle", 0.0
        self.rect = NO_RECT
        self.beam = None
        self.was_above = False
        self.down = 0.0             # > 0 once knocked over
        self.mode = None            # "fire" while the beam is out: the engine plays its zap and lights it up
        self.alert = False          # charging at you: the engine sounds its alarm

    def _sight_end(self, room):
        """Where its eye line starts and stops: at its range, or at the first wall or cube in the way."""
        x0 = self.box.left if self.dir < 0 else self.box.right
        end = x0 + self.dir * self.RANGE
        probe = pygame.Rect(min(x0, end), self.eye - 2, self.RANGE, 4)
        for b in [w.rect for w in room.walls if w.solid] + [c.rect for c in room.cubes]:
            if probe.colliderect(b):
                end = max(end, b.right) if self.dir < 0 else min(end, b.left)
        return x0, end, pygame.Rect(min(x0, end), self.eye - 2, abs(end - x0), 4)

    def update(self, dt, room, player):
        r = player.rect
        if self.down:
            self.down += dt
            self.rect = NO_RECT
            return
        touching = r.colliderect(self.box)
        if touching and (RUN["star"] > 0 or (self.was_above and player.vy > 0)):
            self.down = 0.01
            self.rect = NO_RECT
            if RUN["star"] <= 0:
                player.vy, player.on = -400.0, None
                room.launched = True
            room.add_coins(2, "Turret knocked over")
            room.effect("stomp", self.box.centerx, self.box.top, (230, 232, 238), 18)
            self.mode, self.alert = None, False
            return
        self.was_above = r.bottom <= self.box.top + 6
        x0, end, line = self._sight_end(room)
        sees = line.colliderect(r)
        self.t += dt
        self.mode = "fire" if self.state == "fire" else None
        self.alert = self.state in ("charge", "fire")
        if self.state == "idle":
            self.rect = NO_RECT
            if sees:
                self.state, self.t = "charge", 0.0
        elif self.state == "charge":
            if self.t > 0.6:
                self.state, self.t = "fire", 0.0
        elif self.state == "fire":
            self.beam = pygame.Rect(min(x0, end), self.eye - 3, abs(end - x0), 6)
            self.rect = self.beam
            if self.beam.colliderect(r):
                _shield(player)
            if self.t > 0.25:
                self.state, self.t, self.rect = "cool", 0.0, NO_RECT
        elif self.state == "cool":
            self.rect = NO_RECT
            if self.t > 0.6:
                self.state = "idle"
        self.sight = (x0, end)

    def draw(self, surf):
        r = self.box
        if self.down:
            pygame.draw.ellipse(surf, (220, 222, 228), (r.left - 8, r.bottom - 16, r.width + 16, 16))
            pygame.draw.ellipse(surf, C.INK, (r.left - 8, r.bottom - 16, r.width + 16, 16), 2)
            return
        pygame.draw.line(surf, C.INK, (r.left + 4, r.bottom), (r.left - 4, r.bottom + 0), 3)
        pygame.draw.ellipse(surf, (230, 232, 238), r)
        pygame.draw.ellipse(surf, C.INK, r, 2)
        eye_x = r.centerx + self.dir * 6
        pygame.draw.circle(surf, C.DANGER, (eye_x, self.eye), 4)
        if self.state in ("charge", "fire") and hasattr(self, "sight"):
            x0, end = self.sight
            width = 1 if self.state == "charge" else 5
            color = (255, 90, 90) if self.state == "charge" else (255, 60, 60)
            pygame.draw.line(surf, color, (x0, self.eye), (end, self.eye), width)


class Goo:
    """A pool of something you really shouldn't step in."""

    def __init__(self, x, w):
        self.rect = pygame.Rect(x, C.FLOOR_Y - 12, w, 12)
        self.t = 0.0

    def update(self, dt, room, player):
        self.t += dt

    def draw(self, surf):
        r = self.rect
        pygame.draw.rect(surf, (40, 80, 30), (r.left, r.top, r.width, C.H - r.top))
        pygame.draw.rect(surf, GOO, r)
        for i in range(r.left + 10, r.right - 6, 26):
            y = r.top + 3 + int(2 * math.sin(self.t * 4 + i))
            pygame.draw.circle(surf, (170, 240, 110), (i, y), 3)


class LaserGrid:
    """A wall of laser that switches off while its signal is on."""

    def __init__(self, x, y_top, y_bottom, link):
        self.box = pygame.Rect(x, y_top, 8, y_bottom - y_top)
        self.link = link
        self.rect = self.box
        self.t = 0.0

    def update(self, dt, room, player):
        self.t += dt
        self.rect = NO_RECT if room.sig.get(self.link) else self.box

    def draw(self, surf):
        b = self.box
        pygame.draw.rect(surf, (60, 62, 72), (b.left - 4, b.top - 8, 16, 8))
        pygame.draw.rect(surf, (60, 62, 72), (b.left - 4, b.bottom, 16, 8))
        if self.rect is NO_RECT:
            return
        for k in range(3):
            x = b.left + 1 + k * 3
            a = 160 + int(90 * math.sin(self.t * 20 + k))
            pygame.draw.line(surf, (255, a // 3, a // 3), (x, b.top), (x, b.bottom), 1)


# --- furniture with its own look ---------------------------------------------------------------------

class Projector(Furniture):
    """A projector on a cart, throwing a cone of light up the wall."""

    def __init__(self, x, y, name="projector cart", holds_piece=False):
        super().__init__(x, y, 60, 56, name, holds_piece)
        self.cone = pygame.Surface((200, 220), pygame.SRCALPHA)     # made once, not every frame
        pygame.draw.polygon(self.cone, (160, 220, 255, 40), [(100, 220), (0, 0), (200, 0)])

    def draw(self, surf):
        r = self.rect
        if not self.searched:
            surf.blit(self.cone, (r.centerx - 100, r.top - 220))
        pygame.draw.rect(surf, (70, 74, 90), (r.left + 6, r.top + 22, r.width - 12, r.height - 22))
        pygame.draw.rect(surf, (40, 42, 52) if not self.searched else (90, 90, 96), (r.left, r.top, r.width, 22),
                         border_radius=4)
        pygame.draw.circle(surf, (190, 230, 255), (r.centerx, r.top + 11), 7)
        pygame.draw.rect(surf, C.INK, r, 2, border_radius=4)


class VRStation(Furniture):
    """A desk with a headset on a stand; the headset's lights pulse."""

    def __init__(self, x, y, name="VR station", holds_piece=False):
        super().__init__(x, y, 100, 64, name, holds_piece)

    def draw(self, surf):
        r = self.rect
        top = (120, 100, 140) if not self.searched else (100, 96, 104)
        pygame.draw.rect(surf, top, (r.left, r.top + 30, r.width, 10))
        pygame.draw.rect(surf, (60, 56, 70), (r.left + 8, r.top + 40, 8, r.height - 40))
        pygame.draw.rect(surf, (60, 56, 70), (r.right - 16, r.top + 40, 8, r.height - 40))
        pygame.draw.line(surf, C.INK, (r.centerx, r.top + 30), (r.centerx, r.top + 14), 3)
        glow = 150 + int(100 * (0.5 + 0.5 * math.sin(pygame.time.get_ticks() / 300.0)))
        pygame.draw.rect(surf, (30, 30, 36), (r.centerx - 22, r.top, 44, 16), border_radius=6)
        pygame.draw.circle(surf, (glow, 80, 220), (r.centerx - 10, r.top + 8), 4)
        pygame.draw.circle(surf, (glow, 80, 220), (r.centerx + 10, r.top + 8), 4)


class _WorldLayer:
    """Decor hook: draws the room's level pieces on top of its background, under platforms and the player."""

    def __init__(self, room):
        self.room = room

    def draw(self, surf):
        self.room.draw_world(surf)


_BACKGROUNDS = {}       # one painted wall per level class, made the first time it's drawn
_CARD = None            # the portal device's controls card, made once


DEVICE_STEP = "Walk into the portal device to pick it up"


def _never():
    return False


def _paint_background(level):
    """The white industrial lab wall for one level: panels, seams, rivets, vents, a hazard band, a big level
    number and a fast diagonal stripe in the level's accent colour. Painted once, then just blitted."""
    bg = pygame.Surface((C.W, C.H))
    top, bottom = (232, 235, 240), (204, 209, 217)
    for y in range(C.FLOOR_Y):
        f = y / C.FLOOR_Y
        bg.fill(tuple(int(top[i] + (bottom[i] - top[i]) * f) for i in range(3)), (0, y, C.W, 1))
    accent = level.accent
    # speed stripes: two long diagonals across the wall, behind everything
    stripes = pygame.Surface((C.W, C.FLOOR_Y), pygame.SRCALPHA)
    for x0, w, a in ((level.stripe_x, 70, 60), (level.stripe_x + 110, 22, 80), (level.stripe_x + 150, 8, 90)):
        pygame.draw.polygon(stripes, (*accent, a), [(x0, C.FLOOR_Y), (x0 + w, C.FLOOR_Y),
                                                    (x0 + w + 380, 0), (x0 + 380, 0)])
    bg.blit(stripes, (0, 0))
    # wall panels with seams and rivets
    for x in range(0, C.W, 160):
        pygame.draw.line(bg, (176, 182, 192), (x, 36), (x, C.FLOOR_Y), 2)
        pygame.draw.line(bg, (246, 248, 250), (x + 2, 36), (x + 2, C.FLOOR_Y), 1)
    for y in (156, 296):
        pygame.draw.line(bg, (176, 182, 192), (0, y), (C.W, y), 2)
        pygame.draw.line(bg, (246, 248, 250), (0, y + 2), (C.W, y + 2), 1)
    for x in range(10, C.W, 160):
        for y in (46, 166, 306, 420):
            for dx in (0, 140):
                pygame.draw.circle(bg, (160, 166, 178), (x + dx, y), 2)
    # the big painted level number
    num = _font(190).render(f"{level.number:02d}", True, (214, 218, 226))
    bg.blit(num, (C.W - num.get_width() - 30, 40))
    # vents
    for vx, vy in level.vents:
        pygame.draw.rect(bg, (120, 126, 138), (vx, vy, 64, 40), border_radius=4)
        for k in range(6):
            pygame.draw.line(bg, (80, 84, 96), (vx + 6, vy + 7 + k * 5), (vx + 58, vy + 7 + k * 5), 2)
    # ceiling rail and the lower wall: dark wainscot, an accent band, and a hazard stripe at the floor
    pygame.draw.rect(bg, (60, 64, 76), (0, 0, C.W, 36))
    pygame.draw.rect(bg, (178, 184, 194), (0, 440, C.W, C.FLOOR_Y - 440))
    pygame.draw.rect(bg, accent, (0, 440, C.W, 5))
    pygame.draw.rect(bg, (230, 190, 60), (0, C.FLOOR_Y - 9, C.W, 9))
    for x in range(-10, C.W, 18):
        pygame.draw.polygon(bg, (34, 36, 44), [(x, C.FLOOR_Y), (x + 8, C.FLOOR_Y), (x + 17, C.FLOOR_Y - 9),
                                               (x + 9, C.FLOOR_Y - 9)])
    return bg


def _plaque(text, size=20, accent=GUIDE):
    """A dark sign plate with a coloured edge, for on-wall instructions."""
    img = _font(size).render(text, True, (240, 242, 246))
    plate = pygame.Surface((img.get_width() + 22, img.get_height() + 10), pygame.SRCALPHA)
    pygame.draw.rect(plate, (24, 28, 38, 225), plate.get_rect(), border_radius=5)
    pygame.draw.rect(plate, accent, (0, 0, 5, plate.get_height()), border_top_left_radius=5,
                     border_bottom_left_radius=5)
    plate.blit(img, (14, 5))
    return plate


def _controls_card():
    """The card that appears the first time you pick up the portal device."""
    global _CARD
    if _CARD is not None:
        return _CARD
    lines = [("Mouse", "aim (the dotted line shows where it lands)", (230, 232, 238)),
             ("LEFT click  or  E", "BLUE portal", BLUE),
             ("RIGHT click  or  Q", "ORANGE portal", ORANGE),
             ("WHITE panels", "the only surfaces portals stick to", (150, 230, 255)),
             ("Walk or fall in", "you come out of the other one, just as fast", (230, 232, 238)),
             ("DOWN  or  S", "grab or drop a cube, press a switch", (230, 232, 238))]
    w, h = 560, 58 + 34 * len(lines) + 20
    card = pygame.Surface((w, h), pygame.SRCALPHA)
    pygame.draw.rect(card, (20, 24, 34, 240), card.get_rect(), border_radius=10)
    pygame.draw.rect(card, (150, 230, 255), card.get_rect(), 2, border_radius=10)
    pygame.draw.rect(card, BLUE, (18, 20, 18, 18), border_radius=9)
    pygame.draw.rect(card, ORANGE, (40, 20, 18, 18), border_radius=9)
    card.blit(_font(34).render("PORTAL DEVICE", True, (255, 255, 255)), (68, 16))
    for i, (key, what, color) in enumerate(lines):
        y = 62 + i * 34
        card.blit(_font(24).render(key, True, color), (22, y))
        card.blit(_font(24).render(what, True, (200, 204, 214)), (210, y))
    card.blit(_font(20).render("(this closes on its own; it'll be in the guide too)", True, (140, 146, 160)),
              (22, h - 26))
    _CARD = card
    return card


# --- the level room --------------------------------------------------------------------------------

class Level(Room):
    """A room with platformer and portal pieces. Subclasses fill in layout() and guide()."""

    number = 0
    name = "LEVEL"
    dark = 0.15                   # the lab keeps its lights on after hours (the engine's default is 0.6)
    accent = (255, 150, 40)
    stripe_x = 120
    vents = ((60, 330),)
    needs_device = False
    spare_device = (110, 840)     # where a spare device appears if you arrive without one: (from west, from east)

    def build(self):
        self.walls, self.doors, self.coins, self.crates = [], [], [], []
        self.cubes, self.buttons, self.switches, self.bridges = [], [], [], []
        self.springs, self.fizzlers, self.panels, self.dispensers = [], [], [], []
        self.portals = {"blue": None, "orange": None}
        self.pedestal = None
        self.hints = []
        self.sig = {}
        self.fling = 0.0
        self.last_vy = self.last_top = self.last_cx = 0.0
        self.launched = False
        self.last_on = False
        self.portal_cool = 0.0
        self.first = True
        self.from_east = False
        self.msg, self.msg_t = "", 0.0
        self.shot = None             # (start, end, color, seconds) of the last portal shot, for drawing
        self.aim = None
        self.preview = None          # (start, end, panel or None) where a portal would land right now
        self.player = None
        self.t = 0.0
        self.trail = []              # recent player positions while moving fast, for the speed streaks
        self.burst = None            # (x, y, color, seconds left) when you come out of a portal
        self.card_t = 0.0
        self.steps, self.step_i, self.step_img, self.step_flash = [], -1, None, 0.0
        self.parts = []              # particles: [x, y, vx, vy, life, max_life, color, size]
        self.flash = None            # (color, seconds left): a quick full-screen tint for big moments
        self.was_down = {}
        self.was_open = {}
        self.was_bridge = False
        self.was_flying = False
        self.layout()
        for w in self.walls:
            self.panels += w.panels
            if 40 <= w.rect.top < C.FLOOR_Y and not isinstance(w, Door):
                self.platforms.append(_WallTop(w))
        self.decor.insert(0, _WorldLayer(self))

    def layout(self):
        raise NotImplementedError

    def guide(self):
        """The steps for this level, in order: (text, done(), target() -> (x, y) or None)."""
        return []

    # helpers for layout()
    def coin_row(self, x0, y, n, gap=30):
        for i in range(n):
            key = f"{type(self).__name__}:coin:{x0 + i * gap},{y}"
            if key not in RUN["taken"]:
                self.coins.append(Coin(key, x0 + i * gap, y))

    def coin_arc(self, x0, x1, y_base, height, n):
        for i in range(n):
            f = i / (n - 1)
            x = int(x0 + (x1 - x0) * f)
            y = int(y_base - height * 4 * f * (1 - f))
            key = f"{type(self).__name__}:coin:{x},{y}"
            if key not in RUN["taken"]:
                self.coins.append(Coin(key, x, y))

    def crate(self, x, top, contents):
        c = Crate(f"{type(self).__name__}:crate:{x},{top}", x, top, contents)
        self.crates.append(c)
        self.platforms.append(c)
        return c

    def hint(self, x, y, text):
        self.hints.append((_plaque(text, accent=self.accent), (x, y)))

    def say(self, text, seconds=1.6):
        self.msg, self.msg_t = text, seconds

    def effect(self, sound, x, y, color, n=10, speed=160, flash=None):
        """A sound and a burst of particles at (x, y); flash tints the whole screen for a moment."""
        if sound:
            sfx(sound)
        for _ in range(n):
            a = random.uniform(0, 2 * math.pi)
            v = random.uniform(0.3, 1.0) * speed
            life = random.uniform(0.3, 0.6)
            self.parts.append([x, y, math.cos(a) * v, math.sin(a) * v - speed * 0.4, life, life, color,
                               random.choice((2, 3, 3, 4))])
        del self.parts[:-220]
        if flash:
            self.flash = (flash, 0.18)

    def add_coins(self, n, why=None):
        RUN["coins"] += n
        if RUN["coins"] >= RUN["helmet_at"]:
            RUN["helmet_at"] += 20
            if not RUN["helmet"]:
                RUN["helmet"] = True
                self.say("20 coins: a helmet! It takes one hit for you", 2.2)
                return
        if why:
            self.say(f"{why}  +{n}", 1.0)
        p = self.player
        if p is not None:
            self.effect("coin", p.rect.centerx, p.rect.top, C.PIECE, 6, 120)

    # guide helpers
    def portal_on(self, panel):
        return any(pt and pt.panel is panel for pt in self.portals.values())

    def portal_at(self, panel):
        pt = next((pt for pt in self.portals.values() if pt and pt.panel is panel), None)
        return pt.box.center if pt else panel.rect.center

    @staticmethod
    def center_top(rect):
        return rect.centerx, rect.top

    # --- every frame --------------------------------------------------------------------------------
    def update(self, dt, p):
        if p is None:
            return
        self.player, self.t = p, self.t + dt
        self.msg_t = max(0.0, self.msg_t - dt)
        if self.first:
            self.first = False
            self.from_east = p.x > C.W / 2
            if self.needs_device and not RUN["device"]:
                self.pedestal = DevicePedestal(self.spare_device[1 if self.from_east else 0])
            self.steps = [st for st in self.guide() if not (RUN["device"] and st[0] == DEVICE_STEP)]
            if self.from_east and not getattr(self, "guide_both_ways", False):
                self.steps = [("You came in from the east: the way west is open", _never, lambda: None)]
        pressed, aim = INPUT.poll()
        self.aim = aim

        # power-ups
        if RUN["star"] > 0:
            RUN["star"] = max(0.0, RUN["star"] - dt)
            p.safe = max(p.safe, 0.05)
        jumped = (not self.launched and self.last_on and p.on is None and p.vy < -400)
        if jumped and RUN["boots"]:
            p.vy = -C.JUMP_SPEED * 1.3 + C.GRAVITY * dt
        self.launched = False
        for s in self.springs:
            s.squash = max(0.0, s.squash - dt * 4)
            if p.on is s:
                p.vy = -Spring.V * (1.12 if RUN["boots"] else 1.0)
                p.on, p.y = None, p.y - 1
                s.squash = 1.0
                self.launched = True
                self.effect("spring", p.rect.centerx, p.rect.bottom, (230, 80, 80), 8, 120)

        # momentum from a portal keeps carrying you until you land
        if p.on is not None:
            self.fling = 0.0
        elif self.fling:
            p.x += self.fling * dt

        self.signals(dt)
        self.portal_step(dt, p, pressed, aim)
        self.collide(p)
        self.cube_step(dt, p, pressed)
        self.pickups(p)
        for c in self.crates:
            c.bounce = max(0.0, c.bounce - dt * 4)
        for f in self.fizzlers:
            if f.rect.colliderect(p.rect):
                if self.portals["blue"] or self.portals["orange"]:
                    self.say("The field closed your portals", 1.2)
                    for pt in self.portals.values():
                        if pt:
                            self.effect("fizzle", pt.box.centerx, pt.box.centery, pt.color, 12)
                self.portals = {"blue": None, "orange": None}
                for c in self.cubes:
                    if c.carried:
                        c.respawn()
                        self.say("The cube dissolved; a new one drops in", 1.6)

        # speed streaks, the exit burst, the card, and the guide
        fast = abs(self.fling) > 250 or abs(p.vy) > 620
        if fast:
            self.trail.append((p.rect.centerx, p.rect.centery))
            del self.trail[:-7]
        elif self.trail:
            self.trail.pop(0)
        if self.burst:
            x, y, color, left = self.burst
            self.burst = (x, y, color, left - dt) if left > dt else None
        if self.card_t > 0:
            self.card_t = max(0.0, self.card_t - dt)
            if self.portals["blue"] and self.portals["orange"]:
                self.card_t = min(self.card_t, 0.4)
        self.preview = self.trace(p, aim) if RUN["device"] else None
        self.guide_step(dt)
        self.fx_step(dt, p)

        self.last_vy, self.last_top, self.last_cx = p.vy, p.rect.top, p.rect.centerx
        self.last_on = p.on is not None

    def fx_step(self, dt, p):
        """Particles, the screen flash, light from portals in the dark, and sounds for doors and buttons."""
        for q in self.parts:
            q[0] += q[2] * dt
            q[1] += q[3] * dt
            q[3] += 600 * dt
            q[4] -= dt
        self.parts = [q for q in self.parts if q[4] > 0]
        if self.flash:
            color, left = self.flash
            self.flash = (color, left - dt) if left > dt else None
        flying = abs(self.fling) > 250
        if self.was_flying and not flying and p.on is not None:       # landing after a portal flight: dust
            self.effect(None, p.rect.centerx, p.rect.bottom, (200, 204, 214), 12, 140)
        self.was_flying = flying
        for b in self.buttons:
            if b.down and not self.was_down.get(id(b)):
                self.effect("button", b.rect.centerx, b.rect.top, (90, 220, 120), 8, 90)
            self.was_down[id(b)] = b.down
        for d in self.doors:
            if d.want != self.was_open.get(id(d), d.want) and not getattr(d, "glass", False):
                sfx("door")
            self.was_open[id(d)] = d.want
        bridge = any(br in self.platforms for br in self.bridges)
        if bridge and not self.was_bridge and not self.from_east:
            sfx("bridge")
        self.was_bridge = bridge
        lights = []
        for pt in self.portals.values():
            if pt:
                lights.append((pt.box.centerx, pt.box.centery, 70))
        if self.pedestal:
            lights.append((self.pedestal.rect.centerx, self.pedestal.rect.top + 18, 60))
        for br in self.bridges:
            if br in self.platforms:
                lights += [(x, br.rect.top, 50) for x in range(br.rect.left + 30, br.rect.right, 90)]
        self.lights = lights

    def guide_step(self, dt):
        self.step_flash = max(0.0, self.step_flash - dt)
        i = max(self.step_i, 0)
        while i < len(self.steps) - 1 and self.steps[i][1]():
            i += 1
        if i != self.step_i:
            if self.step_i >= 0:
                self.step_flash = 0.6
                sfx("step")
            self.step_i = i
            self.step_img = self.render_step()
        target = self.steps[self.step_i][2]() if self.steps else None
        for pnl in self.panels:
            pnl.highlight = target is not None and pnl.rect.collidepoint(target)

    def render_step(self):
        if not self.steps:
            return None
        text = self.steps[self.step_i][0]
        head = _font(20).render(f"LEVEL {self.number}  {self.name}", True, self.accent)
        count = _font(20).render(f"STEP {self.step_i + 1}/{len(self.steps)}", True, (170, 176, 190))
        body = _font(26).render(text, True, (255, 255, 255))
        w = max(head.get_width() + count.get_width() + 40, body.get_width() + 28)
        box = pygame.Surface((w, 62), pygame.SRCALPHA)
        pygame.draw.rect(box, (18, 22, 32, 230), box.get_rect(), border_radius=8)
        pygame.draw.rect(box, self.accent, (0, 0, 6, 62), border_top_left_radius=8, border_bottom_left_radius=8)
        box.blit(head, (16, 8))
        box.blit(count, (w - count.get_width() - 12, 8))
        box.blit(body, (16, 32))
        return box

    def signals(self, dt):
        p = self.player
        for b in self.buttons:
            b.step(self, p)
        sig = {}
        for b in self.buttons:
            sig[b.link] = sig.get(b.link, False) or b.down
        for s in self.switches:
            s.left = max(0.0, s.left - dt)
            sig[s.link] = sig.get(s.link, False) or s.left > 0
        self.sig = sig
        for d in self.doors:
            d.step(dt, sig.get(d.link, False) or self.from_east)
        for br in self.bridges:
            on = sig.get(br.link, False) or self.from_east
            if on and br not in self.platforms:
                self.platforms.append(br)
            elif not on and br in self.platforms:
                self.platforms.remove(br)

    def solids(self):
        return [w.rect for w in self.walls if w.solid] + [c.rect for c in self.crates]

    def collide(self, p):
        """Walls and crates are solid from every side (the engine only knows one-way ledges)."""
        for s in self.solids():
            r = p.rect
            if not r.colliderect(s):
                continue
            if p.vy < 0 and self.last_top >= s.bottom - 2:         # head into it from below
                p.y, p.vy = float(s.bottom), 0.0
                for c in self.crates:
                    if c.rect == s:
                        self.bump(c)
                continue
            if r.bottom <= s.top + 6:                              # standing on it
                continue
            p.x = float(s.left - PW) if self.last_cx < s.centerx else float(s.right)
            self.fling = 0.0

    def bump(self, c):
        c.bounce = 1.0
        if c.used:
            sfx("bump")
            return
        c.used = True
        big = c.contents != "coin"
        self.effect("power" if big else "bump", c.rect.centerx, c.rect.top, Crate.ICON[c.contents], 16 if big else 8,
                    flash=Crate.ICON[c.contents] if big else None)
        RUN["taken"].add(c.key)
        if c.contents == "coin":
            self.add_coins(1, "Coin")
        elif c.contents == "boots":
            RUN["boots"] = True
            self.say("Jump boots! You jump higher now", 2.2)
        elif c.contents == "helmet":
            RUN["helmet"] = True
            self.say("Helmet! It takes one hit for you", 2.2)
        elif c.contents == "star":
            RUN["star"] = 8.0
            self.say("Invincible for 8 seconds! Run into things", 2.2)

    def pickups(self, p):
        r = p.rect
        for coin in list(self.coins):
            if r.colliderect(coin.rect):
                self.coins.remove(coin)
                RUN["taken"].add(coin.key)
                self.add_coins(1)
        if self.pedestal and r.colliderect(self.pedestal.rect):
            self.effect("device", self.pedestal.rect.centerx, self.pedestal.rect.top + 18, BLUE, 12, flash=(150, 210, 255))
            self.effect(None, self.pedestal.rect.centerx, self.pedestal.rect.top + 18, ORANGE, 12)
            self.pedestal = None
            RUN["device"] = True
            if not RUN["card"]:
                RUN["card"] = True
                self.card_t = 6.0
            else:
                self.say("Portal device: left click blue, right click orange", 2.5)

    # --- portals ---------------------------------------------------------------------------------------
    def portal_step(self, dt, p, pressed, aim):
        if self.shot:
            self.shot = (*self.shot[:3], self.shot[3] - dt) if self.shot[3] > dt else None
        if RUN["device"]:
            for color in ("blue", "orange"):
                if color in pressed:
                    self.fire(p, color, aim)
        self.portal_cool = max(0.0, self.portal_cool - dt)
        a, b = self.portals["blue"], self.portals["orange"]
        if not (a and b) or self.portal_cool > 0:
            return
        for src, dst in ((a, b), (b, a)):
            speed = src.entering(p, self)
            if speed is not None:
                self.emerge(p, dst, speed)
                self.portal_cool = 0.3
                return

    def trace(self, p, aim):
        """Where a portal shot from the player toward `aim` lands: (start, end, panel or None).
        Glass doesn't stop a shot; walls, crates and the floor do."""
        ox, oy = p.rect.centerx, p.rect.centery - 6
        if aim is None:
            aim = (ox + p.facing * 600, oy)
        dx, dy = aim[0] - ox, aim[1] - oy
        d = math.hypot(dx, dy)
        if d < 1:
            return None
        dx, dy = dx / d, dy / d
        best = None
        blockers = [w.rect for w in self.walls if w.solid and not getattr(w, "glass", False)]
        blockers += [c.rect for c in self.crates] + [pygame.Rect(0, C.FLOOR_Y, C.W, C.H - C.FLOOR_Y)]
        for panel in self.panels:
            hit = _ray_hit(ox, oy, dx, dy, panel.rect)
            if hit and hit[1] == panel.face and (best is None or hit[0] < best[0]):
                best = (hit[0], panel)
        for r in blockers:
            hit = _ray_hit(ox, oy, dx, dy, r)
            if hit and (best is None or hit[0] < best[0] - 0.5):
                best = (hit[0], None)
        t = best[0] if best else 1400
        return (ox, oy), (ox + dx * t, oy + dy * t), (best[1] if best else None)

    def fire(self, p, color, aim):
        tr = self.trace(p, aim)
        if tr is None:
            return
        start, end, panel = tr
        rgb = BLUE if color == "blue" else ORANGE
        self.shot = (start, end, rgb, 0.12)
        if panel is None:
            self.say("Portals only open on white panels", 1.0)
            self.effect("fizzle", end[0], end[1], (230, 70, 60), 8, 100)
            return
        along = end[1] if panel.vertical else end[0]
        new = Portal(rgb, panel, along)
        other = self.portals["orange" if color == "blue" else "blue"]
        if other and other.panel is panel and abs(other.c - new.c) < (new.hi - new.lo):
            self.say("Too close to the other portal", 1.0)
            sfx("fizzle")
            return
        self.portals[color] = new
        self.effect(color, new.box.centerx, new.box.centery, rgb, 14, 140)

    def emerge(self, p, dst, speed):
        n = dst.normal
        if n == "up":
            p.x, p.y = dst.c - PW / 2, dst.face_at - PH - 1
            p.vy, self.fling = -max(speed, 420.0), p.facing * 140.0     # a nudge, so you land clear of it
        elif n == "down":
            p.x, p.y = dst.c - PW / 2, dst.face_at + 1
            p.vy, self.fling = max(speed, 60.0), 0.0
        elif n == "right":
            p.x, p.y = dst.face_at + 1, dst.c - PH / 2
            p.vy, self.fling, p.facing = -120.0, max(speed, 330.0), 1
        else:
            p.x, p.y = dst.face_at - PW - 1, dst.c - PH / 2
            p.vy, self.fling, p.facing = -120.0, -max(speed, 330.0), -1
        p.on = None
        self.launched = True
        self.last_top = p.rect.top
        self.last_cx = p.rect.centerx
        self.burst = (dst.box.centerx, dst.box.centery, dst.color, 0.35)
        self.effect("warp", dst.box.centerx, dst.box.centery, dst.color, 16, 200)

    # --- cubes -------------------------------------------------------------------------------------------
    def cube_step(self, dt, p, pressed):
        held = next((c for c in self.cubes if c.carried), None)
        if "use" in pressed:
            on_lift = p.on is not None and hasattr(p.on, "drive")
            if held:
                held.carried = False
                x = p.rect.centerx + p.facing * 20 - Cube.S / 2
                x = max(0, min(C.W - Cube.S, x))
                probe = pygame.Rect(int(x), int(p.rect.bottom - Cube.S), Cube.S, Cube.S)
                if probe.collidelist(self.solids()) >= 0:
                    x = p.rect.centerx - Cube.S / 2
                held.x, held.y, held.vy = float(x), float(p.rect.bottom - Cube.S), 0.0
                held = None
                sfx("drop")
            elif not on_lift:
                near = p.rect.inflate(30, 20)
                cube = next((c for c in self.cubes if near.colliderect(c.rect)), None)
                switch = next((s for s in self.switches if near.colliderect(s.rect)), None)
                if cube:
                    cube.carried = True
                    sfx("grab")
                elif switch:
                    switch.left = switch.seconds
                    sfx("button")
                    self.say(f"Bridge on: {switch.seconds} seconds!", 1.2)
        for c in self.cubes:
            if c.carried:
                c.x = p.rect.centerx + p.facing * 14 - Cube.S / 2
                c.y = p.rect.top + 8
                c.vy = 0.0
            else:
                c.fall(dt, self)
                for h in self.hazards:
                    if isinstance(h, Goo) and h.rect.colliderect(c.rect):
                        self.effect("fizzle", c.rect.centerx, c.rect.top, GOO, 10)
                        c.respawn()

    # --- drawing -----------------------------------------------------------------------------------------
    def draw_background(self, surf):
        key = type(self)
        if key not in _BACKGROUNDS:
            _BACKGROUNDS[key] = _paint_background(self)
        surf.blit(_BACKGROUNDS[key], (0, 0))

    def draw_world(self, surf):
        t = self.t
        for img, pos in self.hints:
            surf.blit(img, pos)
        for d in self.dispensers:
            d.draw(surf)
        for w in self.walls:
            w.draw(surf)
        for pnl in self.panels:
            pnl.draw(surf, t)
        for f in self.fizzlers:
            f.draw(surf, t)
        for b in self.buttons:
            b.draw(surf)
        for s in self.switches:
            s.draw(surf)
        if self.pedestal:
            self.pedestal.draw(surf, t)
        for coin in self.coins:
            coin.draw(surf, t)
        for c in self.cubes:
            if not c.carried:
                c.draw(surf)
        for pt in self.portals.values():
            if pt:
                pt.draw(surf)

    def draw_foreground(self, surf):
        p = self.player
        if p is not None:
            self.draw_speed(surf, p)
            r = p.rect
            for c in self.cubes:
                if c.carried:
                    c.draw(surf)
            if RUN["star"] > 0:
                hue = int(self.t * 12) % 3
                color = ((255, 120, 220), (255, 230, 90), (120, 230, 255))[hue]
                pygame.draw.rect(surf, color, r.inflate(8, 8), 2, border_radius=8)
            if RUN["helmet"]:
                pygame.draw.ellipse(surf, (240, 200, 60), (r.centerx - 10, r.top - 4, 20, 12))
                pygame.draw.ellipse(surf, INK2, (r.centerx - 10, r.top - 4, 20, 12), 1)
            if RUN["boots"]:
                pygame.draw.rect(surf, (90, 200, 255), (r.left, r.bottom - 5, r.width, 5), border_radius=2)
            self.draw_aim(surf)
        if self.shot:
            a, b, rgb, _ = self.shot
            pygame.draw.line(surf, rgb, a, b, 3)
        for x, y, _vx, _vy, life, full, color, size in self.parts:
            pygame.draw.circle(surf, color, (int(x), int(y)), max(1, int(size * life / full + 0.5)))
        if self.flash:
            color, left = self.flash
            tint = getattr(self, "_tint", None)
            if tint is None:
                tint = self._tint = pygame.Surface((C.W, C.H), pygame.SRCALPHA)     # made once per room
            tint.fill((*color, int(110 * left / 0.18)))
            surf.blit(tint, (0, 0))
        self.draw_arrow(surf)
        self.draw_hud(surf)

    def draw_speed(self, surf, p):
        """Speed streaks and after-images while you're moving fast; a ring where you came out of a portal."""
        if self.burst:
            x, y, color, left = self.burst
            rad = int(14 + (0.35 - left) * 160)
            pygame.draw.circle(surf, color, (x, y), rad, 3)
            pygame.draw.circle(surf, (255, 255, 255), (x, y), max(2, rad - 10), 1)
        if len(self.trail) < 2:
            return
        n = len(self.trail)
        for i, (x, y) in enumerate(self.trail[:-1]):
            k = (i + 1) / n
            ghost = pygame.Rect(0, 0, PW, PH)
            ghost.center = (x, y)
            pygame.draw.rect(surf, self.accent, ghost, 1 + int(k * 2), border_radius=6)
        hx, hy = self.trail[-1]
        tx, ty = self.trail[0]
        for dy in (-14, -4, 6, 16):
            pygame.draw.line(surf, (255, 255, 255), (tx, ty + dy), (hx, hy + dy), 2)
            pygame.draw.line(surf, self.accent, (tx, ty + dy + 2), (hx, hy + dy + 2), 1)

    def draw_aim(self, surf):
        """With the device: a dotted line to where a portal would land, and a ring (yes) or a red X (no)."""
        if not RUN["device"] or self.aim is None or self.preview is None:
            return
        (ox, oy), (ex, ey), panel = self.preview
        ok = panel is not None
        color = (60, 200, 255) if ok else (230, 70, 60)
        length = math.hypot(ex - ox, ey - oy)
        if length > 1:
            ux, uy = (ex - ox) / length, (ey - oy) / length
            d = 18.0
            while d < length - 10:
                a = (int(ox + ux * d), int(oy + uy * d))
                b = (int(ox + ux * min(d + 8, length)), int(oy + uy * min(d + 8, length)))
                pygame.draw.line(surf, INK2, a, b, 4)
                pygame.draw.line(surf, color, a, b, 2)
                d += 16
        end = (int(ex), int(ey))
        if ok:
            pygame.draw.circle(surf, INK2, end, 11, 4)
            pygame.draw.arc(surf, BLUE, pygame.Rect(end[0] - 10, end[1] - 10, 20, 20), math.pi / 2, 3 * math.pi / 2, 3)
            pygame.draw.arc(surf, ORANGE, pygame.Rect(end[0] - 10, end[1] - 10, 20, 20), -math.pi / 2, math.pi / 2, 3)
        else:
            for sx in (-1, 1):
                pygame.draw.line(surf, INK2, (end[0] - 7, end[1] - 7 * sx), (end[0] + 7, end[1] + 7 * sx), 5)
                pygame.draw.line(surf, color, (end[0] - 7, end[1] - 7 * sx), (end[0] + 7, end[1] + 7 * sx), 3)
        pygame.draw.circle(surf, INK2, self.aim, 6, 1)
        pygame.draw.circle(surf, (255, 255, 255), self.aim, 2)

    def draw_arrow(self, surf):
        """A bouncing arrow over the thing the guide wants you to do next."""
        if not self.steps or self.step_i < 0:
            return
        target = self.steps[self.step_i][2]()
        if target is None:
            return
        x, y = int(target[0]), int(target[1]) - 14 - int(6 * abs(math.sin(self.t * 5)))
        y = max(44, y)
        pts = [(x - 12, y - 18), (x + 12, y - 18), (x, y)]
        pygame.draw.polygon(surf, GUIDE, pts)
        pygame.draw.polygon(surf, INK2, pts, 2)

    def pill(self, surf, x, y, text, color):
        img = _font(22).render(text, True, color)
        box = img.get_rect(topright=(x, y)).inflate(16, 8)
        pygame.draw.rect(surf, (18, 22, 32), box, border_radius=11)
        pygame.draw.rect(surf, color, box, 1, border_radius=11)
        surf.blit(img, img.get_rect(center=box.center))
        return box.left - 8

    def draw_hud(self, surf):
        x, y = C.W - 10, 42
        if RUN["star"] > 0:
            x = self.pill(surf, x, y, f"STAR {RUN['star']:.0f}", (255, 140, 220))
        if RUN["helmet"]:
            x = self.pill(surf, x, y, "HELMET", (240, 200, 60))
        if RUN["boots"]:
            x = self.pill(surf, x, y, "BOOTS", (90, 200, 255))
        if RUN["device"]:
            box = pygame.Rect(0, 0, 58, 25)
            box.topright = (x, y - 4)
            pygame.draw.rect(surf, (18, 22, 32), box, border_radius=11)
            for k, (name, rgb) in enumerate((("blue", BLUE), ("orange", ORANGE))):
                c = (box.left + 17 + k * 24, box.centery)
                pygame.draw.circle(surf, rgb, c, 7, 0 if self.portals[name] else 2)
            x = box.left - 8
        self.pill(surf, x, y, f"COINS {RUN['coins']}", C.PIECE)
        if self.step_img is not None:
            surf.blit(self.step_img, (8, 40))
            if self.step_flash > 0:
                pygame.draw.rect(surf, (90, 230, 130), pygame.Rect((8, 40), self.step_img.get_size()), 3,
                                 border_radius=8)
        if self.msg_t > 0:
            img = _font(26).render(self.msg, True, (255, 255, 255))
            box = img.get_rect(center=(C.W // 2, 128))
            pygame.draw.rect(surf, (18, 22, 32), box.inflate(18, 10), border_radius=6)
            pygame.draw.rect(surf, self.accent, box.inflate(18, 10), 2, border_radius=6)
            surf.blit(img, box)
        if self.card_t > 0:
            card = _controls_card()
            surf.blit(card, card.get_rect(center=(C.W // 2, 250)))


class _WallTop(Platform):
    """The standable top of a wall block (the wall draws itself)."""

    def __init__(self, wall):
        super().__init__(wall.rect.left, wall.rect.top, wall.rect.width)

    def draw(self, surf):
        pass


# --- the five levels, west to east -----------------------------------------------------------------

class Orientation(Level):
    """Level 1, the tutorial: run, jump, crates from below, stomping, then the portal device and a first portal
    through a glass wall. Every step is spelled out in the guide."""

    title = "Level 1 - Orientation (tutorial)"
    number, name, accent, stripe_x = 1, "ORIENTATION", (255, 150, 40), 40
    vents = ((40, 330), (560, 190))

    def layout(self):
        self.decor += [CeilingLight(250), CeilingLight(760), Poster(830, 300, "LAB", (255, 150, 40))]
        self.hint(110, 250, "Crates: hit them from below")
        self.hint(456, 160, "Shoot through glass, walk in")
        self.crate_a = self.crate(150, 380, "coin")
        self.crate_b = self.crate(190, 380, "boots")
        self.coin_row(162, 346, 2, gap=40)
        self.bot = StompBot(320, C.FLOOR_Y, left=260, right=420, speed=40)
        self.hazards.append(self.bot)
        if not RUN["device"]:
            self.pedestal = DevicePedestal(452)
        self.panel_a = FloorPanel(500, 630)
        self.panel_b = FloorPanel(730, 870)
        self.panels += [self.panel_a, self.panel_b]
        self.glass = GlassWall(676, 40, 16, C.FLOOR_Y - 40)
        self.walls.append(self.glass)
        self.doors.append(self.glass)
        self.coin_arc(740, 860, 470, 70, 5)
        self.furniture += [Plant(90, C.FLOOR_Y), FilingCabinet(212, C.FLOOR_Y), Locker(634, C.FLOOR_Y)]

    def guide(self):
        p = lambda: self.player
        return [
            ("Run with LEFT / RIGHT (or A / D)", lambda: p().x > 110, lambda: None),
            ("Jump with SPACE: hit a crate from below", lambda: self.crate_a.used or self.crate_b.used or p().x > 250,
             lambda: (170, 372)),
            ("Stomp the bot: land right on top of it", lambda: bool(self.bot.dead) or p().x > 440,
             lambda: self.center_top(self.bot.box)),
            (DEVICE_STEP, lambda: RUN["device"],
             lambda: self.center_top(self.pedestal.rect) if self.pedestal else None),
            ("LEFT-click the glowing white floor panel", lambda: self.portal_on(self.panel_a),
             lambda: self.panel_a.rect.center),
            ("RIGHT-click the panel past the glass", lambda: self.portal_on(self.panel_b),
             lambda: self.panel_b.rect.center),
            ("Walk into your portal: out the other one!", lambda: p().x > 700, lambda: self.portal_at(self.panel_a)),
            ("That's portals. Head right to Level 2", _never, lambda: (930, 470)),
        ]


class InstallationLab(Level):
    """Level 2: a floor panel and a wall panel get you up to the switch ledge that opens the door."""

    title = "Level 2 - Installation Lab"
    number, name, accent, stripe_x = 2, "INSTALLATION LAB", (220, 70, 170), 260
    vents = ((80, 190),)
    needs_device = True
    spare_device = (190, 760)

    def layout(self):
        self.decor += [CeilingLight(230), CeilingLight(560)]
        if not RUN["device"]:
            self.pedestal = DevicePedestal(190)
        self.hint(300, 250, "Up high? Floor portal in, wall portal out")
        self.wall = Wall(840, 40, 40, 160, panels=[("left", 90, 196)])
        self.walls.append(self.wall)
        self.floor_panel = FloorPanel(360, 540)
        self.panels.append(self.floor_panel)
        self.platforms.append(Ledge(620, 200, 220))
        self.button = Button(680, 200, "exit", latch=True)
        self.buttons.append(self.button)
        self.door = Door(846, 200, 28, 300, "exit")
        self.walls.append(self.door)
        self.doors.append(self.door)
        self.coin_row(770, 176, 2)
        self.coin_row(390, 440, 5, gap=36)
        self.furniture += [Plinth(100, C.FLOOR_Y, colors=((200, 90, 160), (240, 240, 240))),
                           Projector(260, C.FLOOR_Y), Easel(560, C.FLOOR_Y)]

    def guide(self):
        p = lambda: self.player
        wall_panel = self.wall.panels[0]
        on_ledge = lambda: p().on is not None and p().rect.bottom <= 201 and p().x > 600
        return [
            (DEVICE_STEP, lambda: RUN["device"],
             lambda: self.center_top(self.pedestal.rect) if self.pedestal else None),
            ("Put a portal on the white floor panel", lambda: self.portal_on(self.floor_panel) or on_ledge(),
             lambda: self.floor_panel.rect.center),
            ("Put the other on the white wall panel, up high", lambda: self.portal_on(wall_panel) or on_ledge(),
             lambda: wall_panel.rect.center),
            ("Walk into the floor portal", on_ledge, lambda: self.portal_at(self.floor_panel)),
            ("Step on the red button", lambda: self.button.down, lambda: self.center_top(self.button.rect)),
            ("The door is open: drop down and go right", _never, lambda: (self.door.rect.centerx, 440)),
        ]


class FabricationBay(Level):
    """Level 3: carry a cube up the lift, drop into a floor portal, fly out of the wall over the goo,
    and set the cube on the button by the door."""

    title = "Level 3 - Fabrication Bay"
    number, name, accent, stripe_x = 3, "FABRICATION BAY", (40, 190, 170), 330
    vents = ((300, 190), (560, 330))
    needs_device = True
    spare_device = (100, 780)

    def layout(self):
        self.decor += [CeilingLight(520)]
        self.dispensers.append(Dispenser(100))
        self.cube = Cube((100, C.FLOOR_Y))
        self.cubes.append(self.cube)
        self.hint(560, 300, "Fall in fast, fly out fast")
        self.lift = Lift(150, y_top=150, y_bottom=C.FLOOR_Y, width=64)
        self.lifts.append(self.lift)
        self.wall = Wall(100, 170, 30, 130, panels=[("right", 176, 296)])
        self.walls.append(self.wall)
        self.floor_panel = FloorPanel(214, 400)
        self.panels.append(self.floor_panel)
        self.hazards.append(Goo(420, 260))
        br = LightBridge(420, 470, 260)
        br.link = "east_bridge"
        self.bridges.append(br)
        self.coin_arc(160, 700, 300, 60, 8)
        self.button = Button(720, C.FLOOR_Y, "exit")
        self.buttons.append(self.button)
        self.door = Door(846, 40, 28, C.FLOOR_Y - 40, "exit")
        self.walls.append(self.door)
        self.doors.append(self.door)
        self.platforms.append(Ledge(690, 400, 140))
        self.furniture += [FilingCabinet(670, C.FLOOR_Y), Printer3D(720, 400), Locker(800, C.FLOOR_Y)]

    def guide(self):
        p = lambda: self.player
        wall_panel = self.wall.panels[0]
        across = lambda: p().x > 680
        return [
            ("Stand by the cube, press DOWN to pick it up", lambda: self.cube.carried or across(),
             lambda: self.center_top(self.cube.rect)),
            ("Stand on the yellow lift, hold UP to ride it", lambda: self.lift.rect.top <= 160 or across(),
             lambda: self.center_top(self.lift.rect)),
            ("Put a portal on the floor panel below", lambda: self.portal_on(self.floor_panel) or across(),
             lambda: self.floor_panel.rect.center),
            ("Put the other on the wall panel to your left", lambda: self.portal_on(wall_panel) or across(),
             lambda: wall_panel.rect.center),
            ("Step off the lift: drop into the floor portal", across, lambda: self.portal_at(self.floor_panel)),
            ("Press DOWN to set the cube on the button", lambda: self.button.down,
             lambda: self.center_top(self.button.rect)),
            ("The door is open: go right", _never, lambda: (self.door.rect.centerx, 440)),
        ]


class XRTracking(Level):
    """Level 4: a timed bridge over the goo, a turret that can't see over the bridge, and a star crate."""

    title = "Level 4 - XR Tracking Floor"
    number, name, accent, stripe_x = 4, "XR TRACKING FLOOR", (140, 100, 255), 200
    vents = ((440, 190),)

    def layout(self):
        self.decor += [CeilingLight(300), CeilingLight(700)]
        self.hint(330, 330, "Turrets can't see you on the bridge")
        self.crate_a = self.crate(120, 380, "star")
        self.crate_b = self.crate(160, 380, "helmet")
        self.switch = Switch(240, "bridge", 5)
        self.switches.append(self.switch)
        self.hazards.append(Goo(300, 320))
        br = LightBridge(300, 440, 320)
        br.link = "bridge"
        self.bridges.append(br)
        self.coin_row(330, 410, 9, gap=32)
        self.turret = Turret(810, C.FLOOR_Y, facing=-1)
        self.hazards.append(self.turret)
        self.platforms.append(Ledge(640, 360, 130))
        self.coin_row(655, 336, 4, gap=32)
        self.furniture += [VRStation(100, C.FLOOR_Y), ServerRack(700, 360), ServerRack(680, C.FLOOR_Y)]

    def guide(self):
        p = lambda: self.player
        return [
            ("Jump into the crates: a star and a helmet", lambda: (self.crate_a.used and self.crate_b.used)
             or p().x > 230, lambda: (160, 372)),
            ("Press DOWN at the switch: a bridge for 5 s", lambda: self.switch.left > 0 or p().x > 620,
             lambda: self.center_top(self.switch.rect)),
            ("Hurry across the light bridge", lambda: p().x > 620, lambda: (460, 430)),
            ("Get on the ledge, then drop onto the turret", lambda: bool(self.turret.down) or p().x > 860,
             lambda: self.center_top(self.turret.box)),
            ("Onward: go right", _never, lambda: (930, 470)),
        ]


class XRHoloStage(Level):
    """Level 5: the cube is up on a ledge only a portal reaches. Put it on the button to drop the laser grid
    in front of the headset vault, which holds the floor's code digit."""

    title = "Level 5 - XR Holo Stage"
    dark = 0.42
    number, name, accent, stripe_x = 5, "XR HOLO STAGE", (40, 200, 255), 380
    vents = ((300, 330),)
    needs_device = True
    spare_device = (440, 820)
    guide_both_ways = True        # the digit's puzzle is the same whichever side you come in

    def layout(self):
        self.decor += [Window(420, 70, seed=5), CeilingLight(640)]
        self.wall = Wall(60, 110, 36, 110, panels=[("right", 116, 216)])
        self.walls.append(self.wall)
        self.platforms.append(Ledge(96, 220, 170))
        self.dispensers.append(Dispenser(190))
        self.cube = Cube((190, 220))
        self.cubes.append(self.cube)
        self.floor_panel = FloorPanel(110, 260)
        self.panels.append(self.floor_panel)
        self.hint(590, 196, "The field closes portals")
        self.button = Button(470, C.FLOOR_Y, "grid")
        self.buttons.append(self.button)
        self.fizzlers.append(Fizzler(590))
        self.platforms.append(Ledge(640, 410, 120))
        self.platforms.append(Ledge(760, 320, 120))
        self.hazards.append(LaserGrid(754, 230, 410, "grid"))
        self.hazards.append(StompBot(620, C.FLOOR_Y, left=610, right=860, speed=75))
        self.coin_row(660, 386, 3)
        self.vault = Locker(810, 320, name="headset vault", holds_piece=True)
        self.furniture += [VRStation(300, C.FLOOR_Y), ServerRack(680, 410), self.vault]

    def guide(self):
        p = lambda: self.player
        wall_panel = self.wall.panels[0]
        up_top = lambda: (p().on is not None and p().rect.bottom <= 221 and p().x < 280) or self.cube.carried \
            or self.button.down
        return [
            (DEVICE_STEP, lambda: RUN["device"],
             lambda: self.center_top(self.pedestal.rect) if self.pedestal else None),
            ("Put a portal on the floor panel under the ledge", lambda: self.portal_on(self.floor_panel) or up_top(),
             lambda: self.floor_panel.rect.center),
            ("Put the other on the wall panel above the ledge", lambda: self.portal_on(wall_panel) or up_top(),
             lambda: wall_panel.rect.center),
            ("Walk into the floor portal: up to the cube", up_top, lambda: self.portal_at(self.floor_panel)),
            ("DOWN grabs the cube; then walk off the ledge", lambda: self.cube.carried or self.button.down,
             lambda: self.center_top(self.cube.rect)),
            ("DOWN sets the cube on the button: lasers off", lambda: self.button.down,
             lambda: self.center_top(self.button.rect)),
            ("Climb to the headset vault. Hold UP to search it", lambda: self.vault.searched,
             lambda: self.center_top(self.vault.rect)),
            ("Code digit found! The East elevator is right", _never, lambda: (930, 470)),
        ]


ROOMS = [Orientation, InstallationLab, FabricationBay, XRTracking, XRHoloStage]
