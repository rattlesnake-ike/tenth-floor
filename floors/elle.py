"""Floor 7: the Computer Lab.

Three rooms, west to east: the hallway off the West elevator, the computer lab, and the server closet
by the East elevator. The digit is in the filing cabinet on the high shelf in the computer lab:
climb the desk ledge, ride the moving platform, and jump up to the shelf.
Practise it: py main.py --floor elle    Check it: py check.py --floor elle
"""
import math
import random

import pygame

from engine import config as C
from engine.kit import (CeilingLight, Crusher, Drone, FilingCabinet, FloorLaser, Locker, MovingPlatform,
                        PatrolBot, Plant, Poster, ServerRack, Sign, VendingMachine, Window)
from engine.room import Furniture, Platform, Room

NAME = "Floor 7: Computer Lab"     # the name on the elevator panel
AUTHOR = "Elle"                    # your name


class ComputerDesk(Furniture):
    """A lab desk with a monitor: code scrolls up the screen and the cursor blinks.
    Once searched, the screen goes dark (someone logged out)."""

    W, H = 110, 80
    CODE = [(120, 220, 140), (110, 190, 250), (240, 140, 200), (230, 220, 150), (180, 180, 200)]

    def __init__(self, x, y, name="computer", holds_piece=False):
        super().__init__(x, y, self.W, self.H, name, holds_piece)
        rng = random.Random(x * 7 + y)               # each desk scrolls its own code
        self.lines = [(rng.randint(0, 3) * 4, rng.randint(8, 34), rng.choice(self.CODE)) for _ in range(12)]
        self.speed = rng.uniform(10, 18)             # pixels a second the code scrolls
        self.phase = rng.uniform(0, 6)

    def draw(self, surf):
        r = self.rect
        wood = (150, 110, 70) if not self.searched else (110, 96, 84)
        legs = (120, 88, 56) if not self.searched else (92, 82, 72)
        top = pygame.Rect(r.left, r.bottom - 34, r.w, 8)
        pygame.draw.rect(surf, wood, top)
        pygame.draw.rect(surf, legs, (r.left + 6, top.bottom, 8, r.bottom - top.bottom))
        pygame.draw.rect(surf, legs, (r.right - 14, top.bottom, 8, r.bottom - top.bottom))
        pygame.draw.rect(surf, C.INK, top, 2)
        # keyboard and mouse
        pygame.draw.rect(surf, (60, 62, 72), (r.left + 18, top.top - 4, 46, 4))
        pygame.draw.ellipse(surf, (60, 62, 72), (r.left + 72, top.top - 5, 9, 5))
        # monitor on a stand
        mon = pygame.Rect(r.centerx - 30, r.top, 60, 40)
        pygame.draw.line(surf, (30, 32, 40), (r.centerx, mon.bottom), (r.centerx, top.top - 4), 4)
        pygame.draw.rect(surf, (30, 32, 40), mon, border_radius=3)
        screen = mon.inflate(-6, -6)
        if self.searched:
            pygame.draw.rect(surf, (14, 16, 22), screen)
            return
        t = pygame.time.get_ticks() / 1000.0 + self.phase
        pygame.draw.rect(surf, (16, 22, 34), screen)
        surf.set_clip(screen)
        step = 5
        scroll = int(t * self.speed) % (step * len(self.lines))
        for i, (indent, width, col) in enumerate(self.lines):
            y = screen.top + 3 + i * step - scroll
            if y < screen.top - step:
                y += step * len(self.lines)
            pygame.draw.line(surf, col, (screen.left + 3 + indent, y), (screen.left + 3 + indent + width, y), 2)
        if int(t * 2) % 2 == 0:                       # blinking cursor
            pygame.draw.rect(surf, (230, 230, 230), (screen.left + 4, screen.bottom - 6, 4, 3))
        surf.set_clip(None)
        pygame.draw.rect(surf, (90, 160, 220), screen, 1)    # screen glow edge


class TiredStudent:
    """A student pulling an all-nighter at a lab computer. Come too close while he's awake and he
    jumps up and shoves you away ("GO AWAY! I'M RENDERING!"). It doesn't cost you time, it just pushes.
    Every few seconds he nods off at the keyboard: that's your chance to sneak past or search.

    x: where his chair is (left edge). y: the surface he sits on. He faces left, toward his desk.
    """

    W = 30
    AWAKE, ASLEEP = 4.5, 3.0          # seconds awake, then seconds dozing, over and over
    REACH = 95                        # how close you can get before he notices
    SHOVE_SPEED, SHOVE_TIME = 560.0, 0.3

    def __init__(self, x, y, offset=0.0):
        self.x, self.surface = int(x), int(y)
        self.t = offset
        self.dir = -1                 # which way he faces (the check reads .dir: he moves)
        self.shove_t = 0.0            # >0 while shoving
        self.shout_t = 0.0            # >0 while the speech bubble shows
        self.push_dir = 1
        self.rect = pygame.Rect(-200, -200, 1, 1)   # never touches you: he pushes instead
        font = pygame.font.Font(None, 20)
        self.shout = font.render("GO AWAY! I'M RENDERING!", True, C.INK)
        self.zzz = pygame.font.Font(None, 26).render("Zzz", True, (200, 220, 255))

    @property
    def asleep(self):
        return self.shove_t <= 0 and self.shout_t <= 0 and self.t % (self.AWAKE + self.ASLEEP) >= self.AWAKE

    def update(self, dt, room, player):
        self.t += dt
        self.shout_t = max(0.0, self.shout_t - dt)
        if player is None:
            return
        me_x = self.x + self.W // 2
        pr = player.rect
        level = abs(pr.bottom - self.surface) < 6
        if self.shove_t <= 0 and not self.asleep and level and abs(pr.centerx - me_x) < self.REACH:
            self.push_dir = 1 if pr.centerx >= me_x else -1
            self.dir = self.push_dir
            self.shove_t, self.shout_t = self.SHOVE_TIME, 1.4
            player.vy = -300.0                          # a little hop as he shoves
            player.on = None
        if self.shove_t > 0:
            self.shove_t -= dt
            player.x += self.push_dir * self.SHOVE_SPEED * dt
            player.x = max(4.0, min(C.W - player.W - 4.0, player.x))   # never out through a door
        elif self.shout_t <= 0:
            self.dir = -1                               # back to his screen

    def draw(self, surf):
        x, y = self.x, self.surface
        t = pygame.time.get_ticks() / 1000.0
        angry = self.shout_t > 0
        asleep = self.asleep
        # chair
        pygame.draw.rect(surf, (50, 52, 60), (x, y - 24, 30, 5))
        pygame.draw.line(surf, (50, 52, 60), (x + 15, y - 19), (x + 15, y - 4), 3)
        pygame.draw.line(surf, (50, 52, 60), (x + 4, y - 2), (x + 26, y - 2), 3)
        pygame.draw.rect(surf, (50, 52, 60), (x + 26, y - 50, 5, 30))
        # legs (seated, knees toward the desk)
        pygame.draw.line(surf, (40, 50, 80), (x + 14, y - 24), (x + 2, y - 24), 6)
        pygame.draw.line(surf, (40, 50, 80), (x + 2, y - 24), (x + 2, y - 4), 5)
        # body: a purple hoodie
        lean = 3 if asleep else 0
        body = pygame.Rect(x + 8 - lean, y - 50, 16, 27)
        pygame.draw.rect(surf, (110, 80, 160), body, border_radius=4)
        pygame.draw.rect(surf, C.INK, body, 1, border_radius=4)
        # head: droops when asleep
        hx, hy = x + 15 - lean * 2, y - 58 + (6 if asleep else 0)
        pygame.draw.circle(surf, (232, 196, 165), (hx, hy), 8)
        pygame.draw.arc(surf, (40, 30, 30), (hx - 9, hy - 10, 18, 14), 0, 3.14, 5)       # messy hair
        face = -1 if self.dir < 0 else 1
        ex = hx + 4 * face
        if asleep:
            pygame.draw.line(surf, C.INK, (ex - 2, hy), (ex + 2, hy), 1)                     # eyes shut
        else:
            pygame.draw.circle(surf, C.INK, (ex, hy - 1), 1)
            pygame.draw.line(surf, (130, 90, 140), (ex - 2, hy + 2), (ex + 2, hy + 2), 1)    # dark circles
            if angry:
                pygame.draw.line(surf, C.DANGER, (ex - 3, hy - 5), (ex + 3, hy - 3), 2)
        # arm: typing when awake (the hand bobs), flung out when shoving, limp when asleep
        if angry:
            pygame.draw.line(surf, (110, 80, 160), (hx, y - 44), (hx + 18 * self.push_dir, y - 46), 4)
        elif asleep:
            pygame.draw.line(surf, (110, 80, 160), (hx - 2, y - 42), (x - 10, y - 36), 4)
        else:
            bob = 2 if int(t * 10) % 2 else 0
            pygame.draw.line(surf, (110, 80, 160), (hx - 2, y - 44), (x - 12, y - 37 - bob), 4)
        # coffee mug on the desk edge, steaming
        pygame.draw.rect(surf, (230, 230, 225), (x - 26, y - 44, 9, 10))
        if not asleep and int(t * 3) % 2:
            pygame.draw.line(surf, (200, 200, 210), (x - 22, y - 48), (x - 20, y - 54), 1)
        if asleep:
            surf.blit(self.zzz, (hx + 4, hy - 26 - int(4 * math.sin(t * 3))))
        if angry:
            bw, bh = self.shout.get_width() + 12, self.shout.get_height() + 8
            bx = max(4, min(C.W - bw - 4, hx - bw // 2))
            bubble = pygame.Rect(bx, hy - 50, bw, bh)
            pygame.draw.rect(surf, (250, 250, 245), bubble, border_radius=6)
            pygame.draw.rect(surf, C.INK, bubble, 2, border_radius=6)
            surf.blit(self.shout, (bubble.x + 6, bubble.y + 4))


class SodaCan:
    """The vending machine in the hallway is broken: it spits out a soda can that rolls along the floor.
    Jump over it. A can rolls from x_start toward left_end, then waits for the next launch."""

    W = H = 12

    def __init__(self, x_start, left_end, speed=150.0, period=3.2, offset=0.0):
        self.x_start, self.left_end, self.speed, self.period = x_start, left_end, speed, period
        self.t = offset
        self.dir = -1                                  # it moves (the check reads .dir)
        self.rect = pygame.Rect(-100, -100, self.W, self.H)
        self.active = False

    def update(self, dt, room, player):
        self.t += dt
        x = self.x_start - (self.t % self.period) * self.speed
        self.active = x > self.left_end
        if self.active:
            self.rect.topleft = (int(x), C.FLOOR_Y - self.H)
        else:
            self.rect.topleft = (-100, -100)

    def draw(self, surf):
        if not self.active:
            return
        r = self.rect
        pygame.draw.rect(surf, (210, 50, 50), r, border_radius=3)
        spin = int(self.t * 20) % 3                      # the stripe spins as it rolls
        pygame.draw.line(surf, (240, 240, 240), (r.left + 3 + spin * 3, r.top + 1), (r.left + 3 + spin * 3, r.bottom - 2), 2)
        pygame.draw.rect(surf, C.INK, r, 1, border_radius=3)


class WetFloor:
    """A freshly mopped puddle: on it you keep sliding the way you face. Doesn't hurt, but the bot does."""

    SLIDE = 170.0

    def __init__(self, x_left, x_right):
        self.x_left, self.x_right = int(x_left), int(x_right)
        self.rect = pygame.Rect(-200, -200, 1, 1)       # harmless: it only makes you slide
        w = self.x_right - self.x_left
        self.puddle = pygame.Surface((w, 14), pygame.SRCALPHA)
        pygame.draw.ellipse(self.puddle, (120, 190, 255, 110), (0, 0, w, 14))
        self.font_sign = pygame.font.Font(None, 16).render("WET", True, C.INK)

    def update(self, dt, room, player):
        if player is None or player.on is not room.ground:
            return
        if self.x_left < player.rect.centerx < self.x_right:
            player.x += player.facing * self.SLIDE * dt
            player.x = max(4.0, min(C.W - player.W - 4.0, player.x))

    def draw(self, surf):
        surf.blit(self.puddle, (self.x_left, C.FLOOR_Y - 6))
        sx, y = self.x_left - 18, C.FLOOR_Y                # the yellow caution sign
        pygame.draw.polygon(surf, (250, 210, 50), [(sx, y), (sx + 9, y - 34), (sx + 18, y)])
        pygame.draw.polygon(surf, C.INK, [(sx, y), (sx + 9, y - 34), (sx + 18, y)], 2)
        surf.blit(self.font_sign, (sx + 9 - self.font_sign.get_width() // 2, y - 16))


class SteamVent:
    """An overheating server vents steam. It puffs as a warning, then blasts a column of steam that
    LAUNCHES you straight up (it doesn't hurt). Ride it up to the high cable trays.

    x: the vent's centre. surface: the floor or ledge it sits in. height: how tall the column is.
    launch: how hard it throws you (about 870 reaches 250 px up).
    """

    WARN, BLAST, REST = 0.6, 1.2, 1.4

    def __init__(self, x, surface=C.FLOOR_Y, height=200, launch=870.0, offset=0.0):
        self.x, self.surface, self.height, self.launch = int(x), int(surface), int(height), float(launch)
        self.t = offset
        self.dir = 0                                   # never hurts; the check reads .dir
        self.rect = pygame.Rect(-200, -200, 1, 1)
        self.phase = "rest"
        self.puff = pygame.Surface((40, 40), pygame.SRCALPHA)
        pygame.draw.circle(self.puff, (225, 235, 245, 130), (20, 20), 18)

    def update(self, dt, room, player):
        self.t = (self.t + dt) % (self.WARN + self.BLAST + self.REST)
        if self.t < self.WARN:
            self.phase = "warn"
        elif self.t < self.WARN + self.BLAST:
            self.phase = "blast"
        else:
            self.phase = "rest"
        if self.phase != "blast" or player is None:
            return
        pr = player.rect
        in_column = abs(pr.centerx - self.x) < 20 and self.surface - self.height - 20 < pr.bottom <= self.surface + 2
        if in_column and player.vy > -self.launch * 0.5:   # one big push each time you step in
            player.vy = -self.launch
            player.on = None

    def draw(self, surf):
        grate = pygame.Rect(self.x - 18, self.surface - 6, 36, 6)
        hot = self.phase != "rest"
        pygame.draw.rect(surf, (230, 120, 60) if hot else (80, 84, 96), grate)
        for gx in range(grate.left + 4, grate.right, 7):
            pygame.draw.line(surf, C.INK, (gx, grate.top), (gx, grate.bottom), 1)
        pygame.draw.polygon(surf, (250, 210, 50), [(self.x - 6, self.surface - 10), (self.x + 6, self.surface - 10),
                                                   (self.x, self.surface - 18)])   # an up arrow on the vent
        if self.phase == "warn":
            k = self.t / self.WARN
            surf.blit(self.puff, (self.x - 20, self.surface - 30 - int(20 * k)))
        elif self.phase == "blast":
            wob = pygame.time.get_ticks() // 60
            for i, y in enumerate(range(self.surface - 30, self.surface - self.height - 20, -24)):
                dx = ((wob + i) % 3 - 1) * 4
                surf.blit(self.puff, (self.x - 20 + dx, y))

class CodeRainRoom(Room):
    """A room whose wall is hacker-style code rain. Every room on this floor uses it:
    subclass it and call self.build_code_rain() at the end of build()."""

    # --- hacker-style code rain on the wall behind everything ---
    RAIN_CHARS = "0101010123456789ABCDEF{}<>/=;#$*+"
    RAIN_ROW = 16          # pixels between characters in a column
    RAIN_COL = 18          # pixels between columns

    def build_code_rain(self):
        """Fonts and glyphs are made once here, never in draw (they are slow to build)."""
        font = pygame.font.Font(None, 20)
        shades = [(16, 50, 26), (24, 85, 40), (36, 130, 60), (60, 190, 95), (200, 255, 210)]  # tail -> head
        self.glyphs = [[font.render(ch, True, col) for ch in self.RAIN_CHARS] for col in shades]
        self.rng = random.Random(self.title)
        self.rain = [self.new_drop(x, start=True) for x in range(4, C.W, self.RAIN_COL)]

    def new_drop(self, x, start=False):
        r = self.rng
        length = r.randint(6, 18)
        return {"x": x,
                "y": r.uniform(0, C.FLOOR_Y) if start else -r.uniform(0, 300),
                "speed": r.uniform(60, 160),
                "length": length,
                "chars": [r.randrange(len(self.RAIN_CHARS)) for _ in range(length)]}

    def update(self, dt, player):
        for i, d in enumerate(self.rain):
            d["y"] += d["speed"] * dt
            if d["y"] - d["length"] * self.RAIN_ROW > C.FLOOR_Y:
                self.rain[i] = self.new_drop(d["x"])
            elif self.rng.random() < dt * 4:             # characters flicker and change
                d["chars"][self.rng.randrange(d["length"])] = self.rng.randrange(len(self.RAIN_CHARS))

    def draw_background(self, surf):
        surf.fill((6, 12, 10))
        for d in self.rain:
            head = int(d["y"])
            n = d["length"]
            for k in range(n):
                y = head - k * self.RAIN_ROW
                if y < 0 or y > C.FLOOR_Y - 12:
                    continue
                level = 4 if k == 0 else 3 - min(3, k * 4 // n)
                surf.blit(self.glyphs[level][d["chars"][k]], (d["x"], y))


class Hallway(CodeRainRoom):
    """Off the West elevator: a broken vending machine spitting soda cans, a wet floor, and a patrol bot."""

    title = "Floor 7: Hallway"

    def build(self):
        self.decor += [Sign(330, 46, "FLOOR 7  COMPUTER LAB"), CeilingLight(300), CeilingLight(700),
                       Poster(130, 90, "SVA"), Poster(220, 90, "CRIT", (70, 130, 180)), Window(560, 70, seed=7)]
        self.platforms.append(Platform(250, 400, 160))          # a bench to hop onto, away from the bot
        self.furniture += [Plant(110, C.FLOOR_Y), VendingMachine(440, C.FLOOR_Y),
                           Locker(650, C.FLOOR_Y), Locker(700, C.FLOOR_Y), Locker(750, C.FLOOR_Y)]
        self.hazards.append(PatrolBot(500, C.FLOOR_Y, left=200, right=820, speed=75))
        # the broken vending machine spits soda cans that roll toward the West elevator: jump them
        self.hazards += [SodaCan(430, 120, offset=0.0), SodaCan(430, 120, offset=1.6)]
        self.hazards.append(WetFloor(560, 645))                 # just mopped: you slide on it
        self.build_code_rain()


class ComputerLab(CodeRainRoom):
    """The digit is in the filing cabinet on the high shelf: desk ledge -> moving platform -> shelf."""

    title = "Floor 7: Computer Lab"

    def build(self):
        self.decor += [Sign(360, 46, "COMPUTER LAB"), CeilingLight(250), CeilingLight(700),
                       Poster(110, 90, "RENDER", (150, 90, 160)), Window(380, 70, seed=2)]
        self.platforms.append(Platform(200, 410, 200))                              # the desk ledge
        self.platforms.append(MovingPlatform(430, 560, 320, width=110, speed=70))  # rides you across
        self.platforms.append(Platform(720, 230, 170))                              # the high shelf
        self.furniture += [ComputerDesk(100, C.FLOOR_Y, "front computer"), ComputerDesk(240, 410, "monitor row"),
                           ComputerDesk(520, C.FLOOR_Y, "teacher's computer"),
                           FilingCabinet(800, 230, "filing cabinet", holds_piece=True)]
        self.hazards.append(Drone(740, y_top=340, y_bottom=C.FLOOR_Y, speed=80))
        self.hazards.append(TiredStudent(634, C.FLOOR_Y))      # pulling an all-nighter at the teacher's computer
        self.build_code_rain()


class ServerCloset(CodeRainRoom):
    """By the East elevator. On the floor: racks, a floor laser and a crusher. Or go over the top:
    steam vents launch you up to the cable trays, and you drop down past the crusher to the elevator."""

    title = "Floor 7: Server Closet"

    def build(self):
        self.decor += [Sign(370, 46, "SERVER CLOSET"), CeilingLight(480),
                       Poster(120, 90, "NO FOOD", (200, 70, 60)), Poster(860, 300, "HOT!", (230, 120, 60), w=60, h=70)]
        # the high route: vent -> left tray -> middle tray ... rack shelf -> vent -> top tray -> drop to the elevator
        self.platforms.append(Platform(200, 280, 170))        # left cable tray (vent A throws you up here)
        self.platforms.append(Platform(420, 250, 100))        # middle cable tray, a jump across
        self.platforms.append(Platform(500, 405, 200))        # the rack shelf
        self.platforms.append(Platform(600, 160, 200))        # top cable tray (vent B throws you up here)
        self.furniture += [ServerRack(120, C.FLOOR_Y), ServerRack(180, C.FLOOR_Y), ServerRack(310, C.FLOOR_Y),
                           ServerRack(560, 405), FilingCabinet(250, 280, "spare parts"),
                           ServerRack(720, 160, "backup rack")]
        self.hazards.append(SteamVent(270, C.FLOOR_Y, height=230))                   # vent A, on the floor
        self.hazards.append(SteamVent(650, 405, height=255, launch=900, offset=1.3))  # vent B, on the rack shelf
        self.hazards.append(SteamVent(475, C.FLOOR_Y, height=150, launch=700, offset=0.7))  # a small hop up to the rack shelf
        self.hazards.append(FloorLaser(370, 430, on_time=1.2, off_time=1.6))
        self.hazards.append(Crusher(740, y_top=250, y_bottom=C.FLOOR_Y, w=60, h=50))
        self.build_code_rain()

ROOMS = [Hallway, ComputerLab, ServerCloset]
