"""Art History Center, 4th floor: the reading room, the slide and archive room, the conservation studio,
the lecture room, then the immersive Van Gogh projection room.

West elevator -> Reading Room -> Slide and Archive Room -> Conservation Studio -> Lecture Room
-> Immersive Van Gogh -> East elevator.
The digit is in the archive box up on the top shelf of the Slide and Archive Room: ride the lift up to it,
and watch the crusher (the archive's book press).
"""
import math
import random

import pygame

from engine import config as C
from engine.kit import (Bookshelf, CeilingLight, Crusher, Desk, Drone, FilingCabinet, FloorLaser,
                        MovingPlatform, PatrolBot, Plant, Poster, Sign, Window)
from engine.room import Furniture, Lift, Platform, Room

NAME = "Art History Center"     # the name on the elevator panel
AUTHOR = "Elise Dumaine"        # your name


# --- my own parts ---

class Painting:
    """Decor: a framed painting on the wall. style picks which one."""

    def __init__(self, x, y, w, h, style="mondrian"):
        self.pos = (x, y)
        self.image = pygame.Surface((w, h))          # painted once, not every frame
        draw_artwork(self.image, style)
        pygame.draw.rect(self.image, (176, 140, 60), self.image.get_rect(), 6)   # gold frame
        pygame.draw.rect(self.image, C.INK, self.image.get_rect(), 2)

    def draw(self, surf):
        surf.blit(self.image, self.pos)


def draw_artwork(img, style):
    w, h = img.get_size()
    if style == "mondrian":
        img.fill((240, 236, 224))
        pygame.draw.rect(img, (200, 40, 40), (0, 0, w * 0.55, h * 0.6))
        pygame.draw.rect(img, (30, 60, 150), (0, h * 0.75, w * 0.3, h))
        pygame.draw.rect(img, (240, 200, 40), (w * 0.8, h * 0.75, w, h))
        for x in (w * 0.3, w * 0.55, w * 0.8):
            pygame.draw.line(img, C.INK, (x, 0), (x, h), 5)
        for y in (h * 0.6, h * 0.75):
            pygame.draw.line(img, C.INK, (0, y), (w, y), 5)
    elif style == "night":                         # a starry night
        img.fill((30, 50, 110))
        for i in range(6):
            pygame.draw.arc(img, (90, 130, 200), (i * w // 5 - 20, h // 5, w // 3, h // 3), 0, 3.1, 3)
        pygame.draw.circle(img, (250, 220, 90), (int(w * 0.8), int(h * 0.22)), max(6, w // 10))
        for sx, sy in ((0.2, 0.15), (0.45, 0.1), (0.6, 0.3), (0.3, 0.4)):
            pygame.draw.circle(img, (250, 240, 150), (int(w * sx), int(h * sy)), 4)
        pygame.draw.polygon(img, (20, 40, 30), [(w * 0.15, h), (w * 0.22, h * 0.3), (w * 0.3, h)])
        pygame.draw.rect(img, (40, 60, 70), (0, h * 0.8, w, h))
    elif style == "mona lisa":                      # Leonardo: hazy landscape, dark dress, folded hands
        img.fill((110, 120, 80))
        pygame.draw.rect(img, (140, 150, 110), (0, 0, w, h * 0.35))
        pygame.draw.polygon(img, (90, 100, 70), [(0, h * 0.45), (w * 0.3, h * 0.3), (w, h * 0.4), (w, h), (0, h)])
        pygame.draw.ellipse(img, (40, 34, 24), (w * 0.12, h * 0.55, w * 0.76, h * 0.7))      # dress
        pygame.draw.ellipse(img, (40, 30, 20), (w * 0.27, h * 0.1, w * 0.46, h * 0.55))      # hair
        pygame.draw.ellipse(img, (210, 170, 110), (w * 0.35, h * 0.14, w * 0.3, h * 0.4))    # face
        pygame.draw.polygon(img, (210, 170, 110), [(w * 0.38, h * 0.56), (w * 0.62, h * 0.56), (w * 0.5, h * 0.66)])
        pygame.draw.arc(img, (120, 70, 50), (w * 0.43, h * 0.38, w * 0.14, h * 0.05), 3.4, 6.0, 2)  # the smile
        for ex in (0.44, 0.56):
            pygame.draw.circle(img, (60, 40, 30), (int(w * ex), int(h * 0.3)), 2)
        pygame.draw.ellipse(img, (210, 170, 110), (w * 0.35, h * 0.8, w * 0.32, h * 0.1))     # hands
    elif style == "pearl":                          # Vermeer: blue and yellow turban, the pearl
        img.fill((22, 20, 22))
        pygame.draw.ellipse(img, (100, 80, 60), (w * 0.2, h * 0.7, w * 0.7, h * 0.5))         # jacket
        pygame.draw.ellipse(img, (230, 200, 160), (w * 0.3, h * 0.25, w * 0.42, h * 0.5))     # face
        pygame.draw.ellipse(img, (40, 80, 170), (w * 0.22, h * 0.1, w * 0.48, h * 0.3))       # turban
        pygame.draw.polygon(img, (220, 190, 90), [(w * 0.55, h * 0.18), (w * 0.8, h * 0.25), (w * 0.72, h * 0.6),
                                                  (w * 0.62, h * 0.3)])
        pygame.draw.circle(img, (60, 40, 30), (int(w * 0.45), int(h * 0.45)), 3)
        pygame.draw.circle(img, (60, 40, 30), (int(w * 0.6), int(h * 0.44)), 2)
        pygame.draw.circle(img, (180, 60, 60), (int(w * 0.5), int(h * 0.64)), 3)               # lips
        pygame.draw.circle(img, (245, 245, 240), (int(w * 0.36), int(h * 0.66)), 4)            # the pearl
    elif style == "scream":                         # Munch: orange sky, blue fjord, the screaming figure
        img.fill((220, 110, 50))
        for i, y in enumerate(range(0, int(h * 0.5), 10)):
            pygame.draw.arc(img, ((240, 160, 60), (200, 70, 40))[i % 2], (-20, y, w + 40, 24), 0, 3.1, 4)
        pygame.draw.ellipse(img, (40, 70, 120), (-w * 0.2, h * 0.4, w * 0.9, h * 0.3))         # fjord
        pygame.draw.polygon(img, (130, 90, 60), [(0, h), (w * 0.2, h), (w, h * 0.45), (w, h * 0.55)])   # bridge
        pygame.draw.line(img, (90, 60, 40), (0, h * 0.85), (w, h * 0.38), 3)                  # rail
        pygame.draw.ellipse(img, (50, 50, 60), (w * 0.32, h * 0.62, w * 0.3, h * 0.45))       # body
        pygame.draw.ellipse(img, (220, 200, 150), (w * 0.36, h * 0.42, w * 0.22, h * 0.26))   # head
        pygame.draw.ellipse(img, (40, 30, 30), (w * 0.44, h * 0.56, w * 0.06, h * 0.08))      # mouth
        for ex in (0.42, 0.52):
            pygame.draw.circle(img, (40, 30, 30), (int(w * ex), int(h * 0.5)), 2)
        for hx in (0.33, 0.58):
            pygame.draw.ellipse(img, (220, 200, 150), (w * hx, h * 0.48, w * 0.06, h * 0.16))  # hands on cheeks


class ProjectorScreen:
    """Decor: the pull-down screen in the lecture room. The professor keeps clicking to the wrong slide."""

    SLIDES = ["mondrian", "shades", "mondrian", "cat", "mondrian", "blank"]

    def __init__(self, x, y, w, h):
        self.pos = (x, y)
        self.t = 0.0
        self.near = False
        self.images = []
        font = pygame.font.Font(None, 20)
        for kind in self.SLIDES:                    # every slide drawn once
            img = pygame.Surface((w, h + 14))
            img.fill((70, 74, 88))
            pygame.draw.rect(img, (60, 60, 66), (0, 0, w, 10))                     # the roller
            pygame.draw.rect(img, (238, 238, 232), (4, 10, w - 8, h))
            slide = pygame.Surface((int(w * 0.6), int(h * 0.75)))
            if kind == "blank":
                slide.fill((238, 238, 232))
                for i, line in enumerate(("This slide intentionally", "left blank.")):
                    text = font.render(line, True, C.INK)
                    slide.blit(text, (slide.get_width() // 2 - text.get_width() // 2, 44 + i * 20))
            elif kind == "cat":                     # the professor's cat, in a beret
                draw_cat(slide)
            else:
                draw_artwork(slide, "mona lisa" if kind == "shades" else kind)
                if kind == "shades":                # the Mona Lisa, but cool
                    sw, sh = slide.get_size()
                    for ex in (0.44, 0.56):
                        pygame.draw.rect(slide, (10, 10, 10), (sw * ex - 9, sh * 0.27, 18, 9), border_radius=3)
                    pygame.draw.line(slide, (10, 10, 10), (sw * 0.44, sh * 0.3), (sw * 0.56, sh * 0.3), 2)
            img.blit(slide, (w // 2 - slide.get_width() // 2, 10 + h // 2 - slide.get_height() // 2))
            img.set_colorkey((70, 74, 88))
            self.images.append(img)

    def update(self, dt, player):
        self.t += dt

    def draw(self, surf):
        surf.blit(self.images[int(self.t / 3.5) % len(self.images)], self.pos)

    def draw_bubble(self, surf):
        pass


def draw_cat(img):
    """A ginger cat in a black beret: the professor's cat, Pablo Catsso."""
    w, h = img.get_size()
    img.fill((200, 220, 230))
    cx, cy = w // 2, int(h * 0.58)
    pygame.draw.polygon(img, (230, 140, 60), [(cx - 34, cy - 14), (cx - 26, cy - 46), (cx - 8, cy - 26)])   # ears
    pygame.draw.polygon(img, (230, 140, 60), [(cx + 34, cy - 14), (cx + 26, cy - 46), (cx + 8, cy - 26)])
    pygame.draw.ellipse(img, (230, 140, 60), (cx - 38, cy - 30, 76, 60))                                    # head
    pygame.draw.ellipse(img, (20, 20, 24), (cx - 30, cy - 52, 56, 22))                                      # beret
    pygame.draw.line(img, (20, 20, 24), (cx, cy - 52), (cx + 2, cy - 58), 3)
    for ex in (-14, 14):
        pygame.draw.ellipse(img, (120, 200, 90), (cx + ex - 6, cy - 10, 12, 12))
        pygame.draw.line(img, C.INK, (cx + ex, cy - 9), (cx + ex, cy + 1), 2)
    pygame.draw.polygon(img, (240, 130, 140), [(cx - 4, cy + 6), (cx + 4, cy + 6), (cx, cy + 11)])          # nose
    for dy in (8, 13):                                                                                       # whiskers
        pygame.draw.line(img, C.INK, (cx - 10, cy + dy), (cx - 34, cy + dy - 4), 1)
        pygame.draw.line(img, C.INK, (cx + 10, cy + dy), (cx + 34, cy + dy - 4), 1)


class LightTable(Furniture):
    """A glowing table covered in 35 mm slides."""

    def __init__(self, x, y, name="light table", holds_piece=False, w=120, h=40):
        super().__init__(x, y, w, h, name, holds_piece)

    def draw(self, surf):
        r = self.rect
        pygame.draw.rect(surf, (90, 84, 76), (r.left + 8, r.top + 10, 6, r.height - 10))
        pygame.draw.rect(surf, (90, 84, 76), (r.right - 14, r.top + 10, 6, r.height - 10))
        top = pygame.Rect(r.left, r.top, r.width, 12)
        pygame.draw.rect(surf, (250, 246, 220) if not self.searched else (170, 168, 156), top)
        pygame.draw.rect(surf, C.INK, top, 2)
        for i, x in enumerate(range(r.left + 8, r.right - 14, 18)):
            color = ((200, 80, 60), (60, 110, 180), (220, 190, 60), (90, 150, 90))[i % 4]
            pygame.draw.rect(surf, color, (x, r.top + 3, 12, 7))


class ArchiveBox(Furniture):
    """A stack of labeled archive boxes."""

    def __init__(self, x, y, name="archive boxes", holds_piece=False, w=70, h=60):
        super().__init__(x, y, w, h, name, holds_piece)

    def draw(self, surf):
        r = self.rect
        body = (196, 170, 120) if not self.searched else (140, 130, 112)
        half = r.height // 2
        for i, box in enumerate((pygame.Rect(r.left, r.top + half, r.width, half),
                                 pygame.Rect(r.left + 6, r.top, r.width - 12, half))):
            pygame.draw.rect(surf, body, box)
            pygame.draw.rect(surf, C.INK, box, 2)
            pygame.draw.rect(surf, (240, 236, 224), (box.centerx - 12, box.top + 8, 24, 10))


class Lectern(Furniture):
    """The professor's lectern."""

    def __init__(self, x, y, name="lectern", holds_piece=False, w=50, h=90):
        super().__init__(x, y, w, h, name, holds_piece)

    def draw(self, surf):
        r = self.rect
        wood = (120, 80, 50) if not self.searched else (100, 90, 80)
        pygame.draw.rect(surf, wood, (r.left + 8, r.top + 16, r.width - 16, r.height - 16))
        pygame.draw.polygon(surf, wood, [(r.left, r.top + 18), (r.right, r.top + 18), (r.right - 4, r.top),
                                         (r.left + 4, r.top)])
        pygame.draw.rect(surf, C.INK, (r.left + 8, r.top + 16, r.width - 16, r.height - 16), 2)
        pygame.draw.polygon(surf, C.INK, [(r.left, r.top + 18), (r.right, r.top + 18), (r.right - 4, r.top),
                                          (r.left + 4, r.top)], 2)


class Seats(Furniture):
    """A row of folding lecture seats."""

    def __init__(self, x, y, name="seats", holds_piece=False, w=100, h=34):
        super().__init__(x, y, w, h, name, holds_piece)

    def draw(self, surf):
        r = self.rect
        red = (150, 50, 50) if not self.searched else (110, 90, 90)
        for x in range(r.left, r.right - 20, 34):
            pygame.draw.rect(surf, red, (x, r.top, 28, r.height - 14), border_radius=4)
            pygame.draw.rect(surf, red, (x, r.bottom - 16, 30, 8), border_radius=2)
            pygame.draw.line(surf, C.INK, (x + 14, r.bottom - 8), (x + 14, r.bottom), 3)
            pygame.draw.rect(surf, C.INK, (x, r.top, 28, r.height - 14), 2, border_radius=4)


def make_bubble(font, line):
    """A speech bubble with a little tail, drawn once."""
    text = font.render(line, True, C.INK)
    w, h = text.get_width() + 16, text.get_height() + 12
    img = pygame.Surface((w, h + 8), pygame.SRCALPHA)
    pygame.draw.rect(img, (250, 248, 240), (0, 0, w, h), border_radius=8)
    pygame.draw.rect(img, C.INK, (0, 0, w, h), 2, border_radius=8)
    pygame.draw.polygon(img, (250, 248, 240), [(w // 2 - 6, h - 2), (w // 2 + 6, h - 2), (w // 2, h + 7)])
    pygame.draw.lines(img, C.INK, False, [(w // 2 - 6, h - 1), (w // 2, h + 7), (w // 2 + 6, h - 1)], 2)
    img.blit(text, (8, 6))
    return img


class Person:
    """Decor: someone working late. Only to look at; says something when you come close.

    x is the left edge, y the surface they stand or sit on. pose: "stand", "talk", "read", "type", "sleep".
    seated=True draws them sitting (with a chair unless chair=False, e.g. behind a row of Seats).
    always=True: they talk whether you're close or not (the professor).
    """

    def __init__(self, x, y, pose="stand", shirt=(80, 120, 200), hair=(40, 30, 20), skin=(230, 190, 150),
                 lines=(), seated=False, chair=True, facing=1, always=False):
        self.x, self.y = x, y
        self.pose, self.shirt, self.hair, self.skin = pose, shirt, hair, skin
        self.seated, self.chair, self.facing, self.always = seated, chair, facing, always
        self.t = (x * 0.37) % 3          # so two people don't move in step
        self.near = always
        font = pygame.font.Font(None, 20)
        self.bubbles = [make_bubble(font, line) for line in lines]

    @property
    def head_y(self):
        return self.y - (40 if self.seated else 52)

    def update(self, dt, player):
        self.t += dt
        if self.always:
            self.near = True
        elif player is None:
            self.near = False
        else:
            r = player.rect
            self.near = abs(r.centerx - (self.x + 12)) < 140 and abs(r.bottom - self.y) < 130

    def draw(self, surf):
        x, y, f, t = self.x, self.y, self.facing, self.t
        cx = x + 12
        hand_x = cx + 12 * f
        if self.seated:
            if self.chair:
                pygame.draw.rect(surf, (90, 70, 55), (cx - 14 * f - 3, y - 44, 6, 44))         # chair back
                pygame.draw.rect(surf, (90, 70, 55), (min(cx - 14 * f, cx + 8 * f) - 2, y - 20, 26, 5))
                pygame.draw.line(surf, (90, 70, 55), (cx + 6 * f, y - 16), (cx + 6 * f, y), 3)
            pygame.draw.rect(surf, (50, 54, 70), (min(cx, cx + 14 * f), y - 22, 16, 7))       # thigh
            pygame.draw.rect(surf, (50, 54, 70), (cx + 12 * f - 3, y - 22, 7, 22))              # shin
            torso = pygame.Rect(cx - 8, y - 42, 16, 22)
        else:
            step = 2 if self.pose == "talk" else 0
            pygame.draw.rect(surf, (50, 54, 70), (cx - 7, y - 22, 6, 22))
            pygame.draw.rect(surf, (50, 54, 70), (cx + 1, y - 22 + step, 6, 22 - step))
            torso = pygame.Rect(cx - 9, y - 46, 18, 26)
        if self.pose == "sleep":                    # slumped over
            torso = torso.move(4 * f, 3)
        pygame.draw.rect(surf, self.shirt, torso, border_radius=4)
        hy = self.head_y + (6 if self.pose == "sleep" else 0)
        hx = cx + (5 * f if self.pose == "sleep" else 0)
        pygame.draw.circle(surf, self.skin, (hx, hy), 8)
        pygame.draw.ellipse(surf, self.hair, (hx - 9, hy - 10, 18, 10))
        if self.pose != "sleep":
            pygame.draw.circle(surf, C.INK, (hx + 3 * f, hy - 1), 1)
        arm_y = torso.top + 8
        if self.pose == "read":                      # a book, and a page that turns now and then
            book = pygame.Rect(hand_x - 8, arm_y - 2, 16, 12)
            pygame.draw.rect(surf, (170, 50, 50), book)
            if int(t * 0.5) % 3 == 0:
                pygame.draw.line(surf, (240, 236, 224), book.midtop, book.midbottom, 2)
            pygame.draw.line(surf, self.shirt, (cx, arm_y), book.center, 4)
        elif self.pose == "type":                    # hands tapping away
            bob = 2 if math.sin(t * 14) > 0 else 0
            pygame.draw.line(surf, self.shirt, (cx, arm_y), (hand_x + 4 * f, arm_y + 8 + bob), 4)
            pygame.draw.circle(surf, self.skin, (hand_x + 4 * f, arm_y + 8 + bob), 3)
        elif self.pose == "talk":                    # waving a hand while explaining
            up = int(10 * math.sin(t * 3))
            pygame.draw.line(surf, self.shirt, (cx, arm_y), (hand_x + 2 * f, arm_y - 8 - up), 4)
            pygame.draw.circle(surf, self.skin, (hand_x + 2 * f, arm_y - 8 - up), 3)
        elif self.pose == "sleep":
            if int(t * 1.5) % 2 == 0:
                pygame.draw.line(surf, (220, 220, 240), (hx + 10, hy - 14), (hx + 16, hy - 14), 2)
                pygame.draw.line(surf, (220, 220, 240), (hx + 16, hy - 14), (hx + 10, hy - 20), 2)
                pygame.draw.line(surf, (220, 220, 240), (hx + 10, hy - 20), (hx + 16, hy - 20), 2)
        else:
            pygame.draw.line(surf, self.shirt, (cx + 6 * f, arm_y), (cx + 8 * f, arm_y + 18), 4)

    def draw_bubble(self, surf):
        if not self.near or not self.bubbles:
            return
        b = self.bubbles[int(self.t / 2.8) % len(self.bubbles)]
        bx = max(4, min(C.W - b.get_width() - 4, self.x + 12 - b.get_width() // 2))
        surf.blit(b, (bx, self.head_y - 14 - b.get_height()))


class Sculpture(Furniture):
    """A famous sculpture on a plinth: "bust", "venus", "thinker", or "amphora" (no plinth)."""

    SIZES = {"bust": (60, 100), "venus": (50, 130), "thinker": (64, 104), "amphora": (44, 64)}
    NAMES = {"bust": "Greek bust", "venus": "Venus de Milo", "thinker": "The Thinker", "amphora": "Greek amphora"}

    def __init__(self, x, y, kind, holds_piece=False):
        w, h = self.SIZES[kind]
        super().__init__(x, y, w, h, self.NAMES[kind], holds_piece)
        self.kind = kind

    def draw(self, surf):
        r = self.rect
        dim = 0.75 if self.searched else 1.0
        marble = tuple(int(c * dim) for c in (232, 228, 216))
        shade = tuple(int(c * dim) for c in (190, 186, 176))
        bronze = tuple(int(c * dim) for c in (78, 98, 76))
        if self.kind == "amphora":
            self.draw_amphora(surf, r, dim)
            return
        base = pygame.Rect(r.left, r.bottom - 26, r.w, 26)
        pygame.draw.rect(surf, (210, 206, 196), base)
        pygame.draw.rect(surf, C.INK, base, 2)
        a = pygame.Rect(r.left + 4, r.top, r.w - 8, r.h - 26)          # where the statue stands
        cx = a.centerx
        if self.kind == "bust":
            pygame.draw.ellipse(surf, marble, (a.left, a.bottom - 30, a.w, 40))
            pygame.draw.rect(surf, (210, 206, 196), (a.left, a.bottom, a.w, 12))
            pygame.draw.rect(surf, marble, (cx - 7, a.bottom - 40, 14, 14))
            pygame.draw.ellipse(surf, marble, (cx - 14, a.top + 4, 28, 36))
            for k in range(5):                                        # curly hair
                pygame.draw.circle(surf, shade, (cx - 12 + k * 6, a.top + 7), 5)
            pygame.draw.line(surf, shade, (cx + 4, a.top + 18), (cx + 6, a.top + 26), 2)   # nose
            pygame.draw.ellipse(surf, C.INK, (cx - 14, a.top + 4, 28, 36), 1)
        elif self.kind == "venus":
            pygame.draw.polygon(surf, marble, [(cx - 8, a.top + 22), (cx + 8, a.top + 22), (cx + 12, a.top + 50),
                                               (cx + 9, a.top + 58), (cx - 9, a.top + 58), (cx - 11, a.top + 50)])
            pygame.draw.circle(surf, shade, (cx - 9, a.top + 26), 4)     # broken-off arms
            pygame.draw.circle(surf, shade, (cx + 9, a.top + 26), 4)
            pygame.draw.polygon(surf, shade, [(cx - 10, a.top + 56), (cx + 12, a.top + 52), (cx + 16, a.bottom),
                                              (cx - 16, a.bottom)])        # the drapery
            for k in range(4):
                pygame.draw.line(surf, marble, (cx - 8 + k * 6, a.top + 60), (cx - 12 + k * 8, a.bottom - 2), 2)
            pygame.draw.rect(surf, marble, (cx - 3, a.top + 14, 6, 9))
            pygame.draw.circle(surf, marble, (cx, a.top + 9), 8)
            pygame.draw.ellipse(surf, shade, (cx - 8, a.top, 16, 8))
        else:                                                         # the thinker, on his rock
            pygame.draw.rect(surf, tuple(int(c * dim) for c in (90, 90, 86)), (a.left + 6, a.bottom - 26, a.w - 12, 26))
            pygame.draw.polygon(surf, bronze, [(cx - 14, a.bottom - 26), (cx + 2, a.bottom - 26), (cx + 8, a.top + 26),
                                               (cx - 6, a.top + 22)])      # back bent forward
            pygame.draw.rect(surf, bronze, (cx - 2, a.bottom - 34, 22, 9))  # thigh
            pygame.draw.rect(surf, bronze, (cx + 14, a.bottom - 34, 8, 34))  # shin
            pygame.draw.line(surf, bronze, (cx + 18, a.bottom - 34), (cx + 14, a.top + 34), 6)   # arm up to the chin
            pygame.draw.circle(surf, bronze, (cx + 12, a.top + 22), 9)
            pygame.draw.line(surf, (40, 50, 40), (cx + 2, a.top + 30), (cx + 8, a.bottom - 30), 1)

    @staticmethod
    def draw_amphora(surf, r, dim):
        clay = tuple(int(c * dim) for c in (206, 120, 60))
        cx = r.centerx
        pygame.draw.arc(surf, C.INK, (r.left, r.top + 6, 16, 22), 1.6, 4.7, 3)     # handles
        pygame.draw.arc(surf, C.INK, (r.right - 16, r.top + 6, 16, 22), -1.6, 1.6, 3)
        pygame.draw.rect(surf, clay, (cx - 8, r.top, 16, 14))
        pygame.draw.ellipse(surf, clay, (r.left + 4, r.top + 10, r.w - 8, r.h - 18))
        pygame.draw.rect(surf, clay, (cx - 9, r.bottom - 10, 18, 10))
        band = pygame.Rect(r.left + 6, r.top + 26, r.w - 12, 18)
        pygame.draw.rect(surf, (30, 24, 20), band)
        for k in range(2):                                            # black-figure warriors
            fx = band.left + 8 + k * 16
            pygame.draw.circle(surf, clay, (fx, band.top + 4), 3)
            pygame.draw.line(surf, clay, (fx, band.top + 6), (fx, band.bottom - 2), 3)
            pygame.draw.line(surf, clay, (fx - 4, band.top + 9), (fx + 5, band.top + 7), 2)
        pygame.draw.ellipse(surf, C.INK, (r.left + 4, r.top + 10, r.w - 8, r.h - 18), 2)


class Timeline:
    """Decor: a banner of art history, oldest on the left."""

    EVENTS = [("450 BC", "Greece"), ("1503", "Leonardo"), ("1889", "Van Gogh"), ("1921", "Mondrian")]

    def __init__(self, x, y, w):
        self.pos = (x, y)
        self.image = pygame.Surface((w, 56), pygame.SRCALPHA)
        pygame.draw.rect(self.image, (236, 226, 196), (0, 0, w, 56), border_radius=4)
        pygame.draw.rect(self.image, (120, 90, 50), (0, 0, w, 56), 2, border_radius=4)
        pygame.draw.line(self.image, (120, 90, 50), (10, 28), (w - 10, 28), 3)
        small = pygame.font.Font(None, 18)
        step = (w - 20) / (len(self.EVENTS) - 1)
        for i, (year, what) in enumerate(self.EVENTS):
            x = int(10 + i * step)
            pygame.draw.circle(self.image, (170, 60, 50), (x, 28), 5)
            for text, ty in ((year, 6), (what, 36)):
                img = small.render(text, True, (60, 44, 30))
                self.image.blit(img, (max(2, min(w - img.get_width() - 2, x - img.get_width() // 2)), ty))

    def draw(self, surf):
        surf.blit(self.image, self.pos)


# --- the conservation studio: damaged masterpieces ---

def draw_more_art(img, style):
    """More famous paintings, for the conservation studio. Falls back to draw_artwork."""
    w, h = img.get_size()
    if style == "wave":                             # Hokusai, The Great Wave
        img.fill((236, 222, 190))
        pygame.draw.polygon(img, (230, 230, 225), [(w * 0.55, h), (w * 0.62, h * 0.55), (w * 0.7, h)])   # Fuji
        pygame.draw.polygon(img, (40, 70, 130), [(0, h), (0, h * 0.5), (w * 0.15, h * 0.2), (w * 0.4, h * 0.1),
                                                 (w * 0.5, h * 0.3), (w * 0.35, h * 0.3), (w * 0.3, h * 0.6),
                                                 (w * 0.5, h * 0.8), (w, h * 0.75), (w, h)])
        for k in range(6):                          # the claws of foam
            pygame.draw.circle(img, (245, 245, 240), (int(w * (0.14 + k * 0.05)), int(h * (0.22 - k * 0.015))), 4)
        pygame.draw.arc(img, (245, 245, 240), (w * 0.1, h * 0.15, w * 0.35, h * 0.5), 0.3, 2.8, 3)
    elif style == "clocks":                         # Dali, The Persistence of Memory
        img.fill((200, 160, 90))
        pygame.draw.rect(img, (110, 150, 190), (0, 0, w, h * 0.45))
        pygame.draw.rect(img, (120, 90, 50), (w * 0.05, h * 0.55, w * 0.35, h * 0.12))      # the table
        pygame.draw.line(img, (90, 70, 40), (w * 0.7, h), (w * 0.7, h * 0.35), 3)          # the dead tree
        pygame.draw.line(img, (90, 70, 40), (w * 0.7, h * 0.4), (w * 0.85, h * 0.35), 3)
        for cx, cy, sx in ((0.25, 0.55, 0.22), (0.82, 0.42, 0.16), (0.55, 0.78, 0.26)):    # melting clocks
            pygame.draw.ellipse(img, (220, 210, 170), (w * (cx - sx / 2), h * cy - 6, w * sx, 14))
            pygame.draw.ellipse(img, (220, 210, 170), (w * (cx + sx / 2) - 8, h * cy, 10, 18))
            pygame.draw.line(img, C.INK, (w * cx, h * cy), (w * cx + 5, h * cy + 3), 1)
    elif style == "sunflowers":                     # Van Gogh, Sunflowers
        img.fill((230, 200, 80))
        pygame.draw.rect(img, (200, 170, 60), (0, h * 0.7, w, h))
        pygame.draw.rect(img, (210, 140, 60), (w * 0.3, h * 0.55, w * 0.4, h * 0.35))       # the vase
        for fx, fy in ((0.3, 0.25), (0.55, 0.18), (0.72, 0.35), (0.42, 0.42), (0.2, 0.45)):
            for a in range(0, 360, 45):
                dx, dy = math.cos(math.radians(a)) * 8, math.sin(math.radians(a)) * 8
                pygame.draw.circle(img, (250, 180, 30), (int(w * fx + dx), int(h * fy + dy)), 4)
            pygame.draw.circle(img, (120, 70, 30), (int(w * fx), int(h * fy)), 5)
    elif style == "kiss":                           # Klimt, The Kiss
        img.fill((180, 150, 60))
        pygame.draw.ellipse(img, (220, 180, 50), (w * 0.2, h * 0.1, w * 0.6, h * 0.9))
        for k in range(14):
            x, y = w * (0.28 + (k % 4) * 0.12), h * (0.35 + (k // 4) * 0.14)
            pygame.draw.rect(img, (40, 40, 40), (x, y, 6, 8))
        pygame.draw.circle(img, (240, 210, 180), (int(w * 0.45), int(h * 0.22)), 7)
        pygame.draw.circle(img, (240, 210, 180), (int(w * 0.57), int(h * 0.27)), 6)
        pygame.draw.circle(img, (60, 40, 30), (int(w * 0.45), int(h * 0.17)), 7)
    elif style == "adam":                           # Michelangelo, The Creation of Adam: the two hands
        img.fill((196, 200, 190))
        pygame.draw.ellipse(img, (170, 60, 50), (w * 0.68, h * 0.05, w * 0.4, h * 0.5))      # God's red cloak
        skin = (214, 156, 112)
        pygame.draw.line(img, skin, (0, h * 0.7), (w * 0.4, h * 0.56), 10)                 # Adam's arm
        pygame.draw.line(img, skin, (w * 0.4, h * 0.56), (w * 0.46, h * 0.52), 4)          # his lazy finger
        pygame.draw.line(img, skin, (w, h * 0.38), (w * 0.58, h * 0.5), 10)                # God's arm
        pygame.draw.line(img, skin, (w * 0.58, h * 0.5), (w * 0.51, h * 0.52), 4)          # almost touching
        pygame.draw.circle(img, skin, (int(w * 0.4), int(h * 0.57)), 6)
        pygame.draw.circle(img, skin, (int(w * 0.58), int(h * 0.5)), 6)
    else:
        draw_artwork(img, style)


class BrokenPainting:
    """Decor: a famous painting waiting for repair.
    damage: "tear", "crooked", "flaking", "half", "cracked", "hole", "frame"."""

    def __init__(self, x, y, w, h, style, damage, seed=1):
        rng = random.Random(seed)
        img = pygame.Surface((w, h))
        draw_more_art(img, style)
        canvas = (226, 214, 186)
        if damage == "half":                        # half cleaned: the old yellow varnish is still on the right
            dirt = pygame.Surface((w // 2, h), pygame.SRCALPHA)
            dirt.fill((120, 90, 20, 150))
            img.blit(dirt, (w // 2, 0))
            pygame.draw.line(img, (250, 250, 250), (w // 2, 0), (w // 2, h), 1)
        elif damage == "flaking":                   # paint flaking off, bare canvas showing
            for _ in range(14):
                px, py = rng.randrange(w), rng.randrange(h)
                pygame.draw.polygon(img, canvas, [(px, py), (px + rng.randint(4, 12), py + rng.randint(-3, 5)),
                                                  (px + rng.randint(0, 8), py + rng.randint(5, 12))])
        elif damage == "cracked":                   # craquelure all over
            for _ in range(30):
                px, py = rng.randrange(w), rng.randrange(h)
                pygame.draw.line(img, (50, 40, 30), (px, py), (px + rng.randint(-10, 10), py + rng.randint(-10, 10)), 1)
        elif damage == "tear":                      # a long slash through the canvas
            pts = [(w * 0.15, h * 0.1)]
            for k in range(1, 6):
                pts.append((w * (0.15 + k * 0.14) + rng.randint(-4, 4), h * (0.1 + k * 0.16)))
            pygame.draw.lines(img, (30, 24, 20), False, pts, 6)
            pygame.draw.lines(img, canvas, False, [(px + 3, py) for px, py in pts], 2)
        elif damage == "hole":
            for a in range(0, 360, 40):
                ex = w * 0.6 + math.cos(math.radians(a)) * 14
                ey = h * 0.45 + math.sin(math.radians(a)) * 14
                pygame.draw.line(img, canvas, (w * 0.6, h * 0.45), (ex, ey), 2)
            pygame.draw.circle(img, (30, 24, 20), (int(w * 0.6), int(h * 0.45)), 8)
        pygame.draw.rect(img, (176, 140, 60), img.get_rect(), 6)                   # gold frame
        if damage == "frame":                       # a corner of the frame snapped off
            pygame.draw.rect(img, (70, 74, 88), (w - 30, h - 6, 30, 6))
            pygame.draw.rect(img, (70, 74, 88), (w - 6, h - 30, 6, 30))
        pygame.draw.rect(img, C.INK, img.get_rect(), 2)
        self.loose = damage == "frame"
        self.nail = (x + w // 2, y - 6)
        if damage == "crooked":                     # hanging by one nail
            clear = pygame.Surface((w, h), pygame.SRCALPHA)
            clear.blit(img, (0, 0))
            img = pygame.transform.rotate(clear, -9)
        self.image, self.pos, self.size = img, (x, y), (w, h)

    def draw(self, surf):
        surf.blit(self.image, self.pos)
        if self.loose:                              # the broken piece of frame, dangling
            x, y = self.pos[0] + self.size[0], self.pos[1] + self.size[1]
            pygame.draw.line(surf, (176, 140, 60), (x - 4, y - 2), (x + 6, y + 22), 6)
        pygame.draw.circle(surf, (40, 40, 40), self.nail, 2)


class XRayBox:
    """Decor: a lightbox with an X-ray of a painting: you can see the first sketch under the paint."""

    def __init__(self, x, y, w=110, h=80):
        self.pos = (x, y)
        img = pygame.Surface((w, h))
        img.fill((200, 220, 235))
        pygame.draw.rect(img, (30, 34, 40), (8, 8, w - 16, h - 16))
        pygame.draw.ellipse(img, (150, 160, 170), (w * 0.35, h * 0.2, w * 0.3, h * 0.4))      # the hidden face
        pygame.draw.ellipse(img, (110, 120, 130), (w * 0.25, h * 0.55, w * 0.5, h * 0.4))
        pygame.draw.line(img, (180, 190, 200), (w * 0.2, h * 0.3), (w * 0.8, h * 0.7), 1)    # a painted-over line
        pygame.draw.rect(img, C.INK, img.get_rect(), 2)
        self.image = img
        self.label = pygame.font.Font(None, 18).render("X-RAY", True, (200, 220, 235))

    def draw(self, surf):
        surf.blit(self.image, self.pos)
        surf.blit(self.label, (self.pos[0] + 4, self.pos[1] + self.image.get_height() + 3))


class ToolRack:
    """Decor: brushes, scalpels and a magnifier on a pegboard."""

    def __init__(self, x, y, w=130, h=60):
        self.rect = pygame.Rect(x, y, w, h)

    def draw(self, surf):
        r = self.rect
        pygame.draw.rect(surf, (150, 120, 80), r)
        pygame.draw.rect(surf, C.INK, r, 2)
        for i, x in enumerate(range(r.left + 10, r.right - 30, 12)):
            tip = ((200, 60, 60), (60, 90, 170), (230, 190, 60), (240, 240, 240))[i % 4]
            pygame.draw.line(surf, (110, 80, 50), (x, r.top + 10), (x, r.bottom - 14), 3)
            pygame.draw.rect(surf, tip, (x - 2, r.bottom - 16, 5, 7))
        pygame.draw.circle(surf, (200, 220, 230), (r.right - 16, r.top + 22), 9)          # magnifier
        pygame.draw.circle(surf, C.INK, (r.right - 16, r.top + 22), 9, 2)
        pygame.draw.line(surf, C.INK, (r.right - 16, r.top + 31), (r.right - 16, r.bottom - 6), 3)


class RestorationEasel(Furniture):
    """An easel holding a famous painting half way through being cleaned."""

    def __init__(self, x, y, style, name="restoration easel", holds_piece=False, w=90, h=130):
        super().__init__(x, y, w, h, name, holds_piece)
        self.art = pygame.Surface((w - 10, 70))
        draw_more_art(self.art, style)
        dirt = pygame.Surface(((w - 10) // 2, 70), pygame.SRCALPHA)
        dirt.fill((120, 90, 20, 150))
        self.art.blit(dirt, ((w - 10) // 2, 0))
        pygame.draw.rect(self.art, (176, 140, 60), self.art.get_rect(), 4)

    def draw(self, surf):
        r = self.rect
        wood = (140, 100, 60) if not self.searched else (110, 100, 90)
        pygame.draw.line(surf, wood, (r.left + 10, r.bottom), (r.centerx, r.top), 4)
        pygame.draw.line(surf, wood, (r.right - 10, r.bottom), (r.centerx, r.top), 4)
        pygame.draw.line(surf, wood, (r.centerx, r.top + 30), (r.centerx + 6, r.bottom), 3)
        pygame.draw.rect(surf, wood, (r.left + 2, r.top + 84, r.w - 4, 6))
        surf.blit(self.art, (r.left + 5, r.top + 12))


class WorkTable(Furniture):
    """The conservator's table: solvent jars, cotton swabs, a lamp."""

    def __init__(self, x, y, name="work table", holds_piece=False, w=120, h=56):
        super().__init__(x, y, w, h, name, holds_piece)

    def draw(self, surf):
        r = self.rect
        wood = (170, 160, 140) if not self.searched else (130, 126, 118)
        top = pygame.Rect(r.left, r.top + 22, r.w, 8)
        pygame.draw.rect(surf, wood, top)
        pygame.draw.rect(surf, C.INK, top, 2)
        for x in (r.left + 6, r.right - 12):
            pygame.draw.rect(surf, (90, 90, 96), (x, top.bottom, 6, r.bottom - top.bottom))
        for i, x in enumerate((r.left + 8, r.left + 24, r.left + 40)):          # jars of solvent
            col = ((180, 210, 230), (230, 200, 120), (200, 140, 170))[i]
            pygame.draw.rect(surf, col, (x, top.top - 14, 12, 14))
            pygame.draw.rect(surf, C.INK, (x, top.top - 14, 12, 14), 1)
        for k in range(4):                                                         # cotton swabs
            pygame.draw.line(surf, (240, 240, 240), (r.left + 60 + k * 6, top.top - 2), (r.left + 64 + k * 6, top.top - 12), 2)
        pygame.draw.line(surf, (60, 60, 66), (r.right - 20, top.top), (r.right - 30, r.top + 4), 3)   # the lamp
        pygame.draw.polygon(surf, (60, 60, 66), [(r.right - 42, r.top + 8), (r.right - 24, r.top), (r.right - 26, r.top + 14)])


class BrokenSculpture(Furniture):
    """A famous sculpture that had a bad day: "david" (lost his head), "nike" (a wing fell off),
    "nefertiti" (cracked, one eye missing like the real one), "discobolus" (dropped an arm)."""

    SIZES = {"david": (60, 150), "nike": (70, 120), "nefertiti": (50, 90), "discobolus": (70, 110)}
    NAMES = {"david": "Michelangelo's David", "nike": "Winged Victory", "nefertiti": "Bust of Nefertiti",
             "discobolus": "Discobolus"}

    def __init__(self, x, y, kind, holds_piece=False):
        w, h = self.SIZES[kind]
        super().__init__(x, y, w, h, self.NAMES[kind], holds_piece)
        self.kind = kind

    def draw(self, surf):
        r = self.rect
        dim = 0.75 if self.searched else 1.0
        m = tuple(int(c * dim) for c in (232, 228, 216))
        sh = tuple(int(c * dim) for c in (186, 182, 172))
        crack = (70, 66, 60)
        base = pygame.Rect(r.left, r.bottom - 22, r.w, 22)
        pygame.draw.rect(surf, (210, 206, 196), base)
        pygame.draw.rect(surf, C.INK, base, 2)
        cx, top, bot = r.centerx, r.top, base.top
        if self.kind == "david":
            pygame.draw.rect(surf, m, (cx - 9, bot - 52, 7, 52))                      # legs
            pygame.draw.polygon(surf, m, [(cx + 1, bot - 52), (cx + 8, bot - 52), (cx + 12, bot), (cx + 4, bot)])
            pygame.draw.polygon(surf, m, [(cx - 12, bot - 52), (cx + 12, bot - 52), (cx + 11, top + 22), (cx - 11, top + 22)])
            pygame.draw.line(surf, m, (cx - 12, top + 26), (cx - 16, bot - 60), 5)    # arms
            pygame.draw.line(surf, m, (cx + 12, top + 26), (cx + 8, top + 8), 5)
            pygame.draw.rect(surf, sh, (cx - 4, top + 14, 8, 8))                    # broken neck
            pygame.draw.line(surf, crack, (cx - 4, top + 14), (cx + 4, top + 16), 2)
            pygame.draw.circle(surf, m, (r.right - 10, base.top - 9), 9)             # his head, fallen on the plinth
            pygame.draw.ellipse(surf, sh, (r.right - 19, base.top - 19, 18, 8))
            pygame.draw.line(surf, crack, (cx - 6, top + 50), (cx + 3, top + 70), 1)
        elif self.kind == "nike":
            pygame.draw.polygon(surf, m, [(cx - 10, top + 30), (cx + 8, top + 30), (cx + 16, bot), (cx - 18, bot)])
            for k in range(4):
                pygame.draw.line(surf, sh, (cx - 8 + k * 6, top + 40), (cx - 14 + k * 9, bot - 2), 2)
            pygame.draw.polygon(surf, m, [(cx + 6, top + 32), (cx + 30, top), (cx + 34, top + 10), (cx + 12, top + 46)])
            for k in range(3):                                                         # the feathers
                pygame.draw.line(surf, sh, (cx + 12 + k * 6, top + 34 - k * 10), (cx + 30, top + 6 + k * 6), 1)
            pygame.draw.rect(surf, sh, (cx - 6, top + 24, 12, 7))                    # no head (the real one has none)
            pygame.draw.polygon(surf, m, [(r.left + 2, base.top), (r.left + 20, base.top - 12), (r.left + 26, base.top - 4)])
            pygame.draw.line(surf, crack, (cx + 8, top + 30), (cx + 14, top + 40), 2)  # where the other wing broke
        elif self.kind == "nefertiti":
            pygame.draw.ellipse(surf, (190, 150, 100), (r.left + 4, bot - 26, r.w - 8, 30))     # shoulders
            pygame.draw.rect(surf, (60, 110, 120), (r.left + 6, bot - 22, r.w - 12, 8))        # painted collar
            pygame.draw.rect(surf, (220, 170, 120), (cx - 5, bot - 38, 10, 16))                 # neck
            pygame.draw.ellipse(surf, (210, 160, 110), (cx - 10, top + 26, 20, 28))           # face
            pygame.draw.polygon(surf, (40, 70, 130), [(cx - 10, top + 30), (cx - 14, top + 4), (cx + 16, top),
                                                      (cx + 12, top + 30)])                   # the blue crown
            pygame.draw.line(surf, (220, 180, 70), (cx - 12, top + 22), (cx + 13, top + 20), 3)
            pygame.draw.circle(surf, C.INK, (cx + 4, top + 38), 2)                          # one eye: the other was never there
            pygame.draw.line(surf, crack, (cx - 10, top + 6), (cx - 2, top + 26), 2)
            pygame.draw.line(surf, crack, (cx - 2, top + 26), (cx - 6, top + 40), 1)
        else:                                                                           # discobolus
            pygame.draw.line(surf, m, (cx - 4, bot), (cx - 10, top + 60), 6)           # legs
            pygame.draw.line(surf, m, (cx + 6, bot), (cx + 2, top + 64), 6)
            pygame.draw.polygon(surf, m, [(cx - 12, top + 62), (cx + 6, top + 64), (cx + 12, top + 28), (cx - 4, top + 24)])
            pygame.draw.circle(surf, m, (cx + 10, top + 18), 8)
            pygame.draw.line(surf, m, (cx + 8, top + 34), (cx + 22, top + 52), 5)      # the arm that's left
            pygame.draw.line(surf, crack, (cx - 4, top + 30), (cx - 8, top + 34), 3)   # the broken shoulder
            pygame.draw.line(surf, m, (r.left + 4, base.top - 4), (r.left + 26, base.top - 8), 5)   # the arm, fallen
            pygame.draw.ellipse(surf, sh, (r.right - 22, base.top - 7, 20, 7))         # the discus


class UVLamp:
    """A hazard of my own: the conservators' UV lamp on a ceiling rail. It sweeps the room looking for
    retouched paint; when it's on, its purple beam reaches the floor. Stay out of the light."""

    def __init__(self, left, right, speed=110, on_time=2.4, off_time=1.4, offset=0.0):
        self.left, self.right, self.speed = left, right, speed
        self.on_time, self.off_time = on_time, off_time
        self.x = float(left)
        self.dir = 1
        self.t = offset
        self.on = False
        self.rect = pygame.Rect(0, 0, 0, 0)
        self.glow = pygame.Surface((60, C.FLOOR_Y - 80), pygame.SRCALPHA)       # made once
        for i in range(30):
            pygame.draw.line(self.glow, (170, 90, 255, 110 - i * 3), (30 - i, 0), (30 - i, C.FLOOR_Y - 80))
            pygame.draw.line(self.glow, (170, 90, 255, 110 - i * 3), (30 + i, 0), (30 + i, C.FLOOR_Y - 80))

    def update(self, dt, room, player):
        self.x += self.dir * self.speed * dt
        if self.x < self.left or self.x > self.right:
            self.dir *= -1
            self.x = max(self.left, min(self.right, self.x))
        self.t = (self.t + dt) % (self.on_time + self.off_time)
        self.on = self.t < self.on_time
        self.rect = pygame.Rect(int(self.x) - 10, 80, 20, C.FLOOR_Y - 80) if self.on else pygame.Rect(0, 0, 0, 0)

    def draw(self, surf):
        x = int(self.x)
        pygame.draw.line(surf, (90, 90, 100), (self.left - 20, 70), (self.right + 20, 70), 4)   # the rail
        if self.on:
            surf.blit(self.glow, (x - 30, 80))
            pygame.draw.rect(surf, (200, 140, 255), (x - 3, 80, 6, C.FLOOR_Y - 80))
        pygame.draw.rect(surf, (60, 60, 70), (x - 14, 70, 28, 12), border_radius=3)
        pygame.draw.rect(surf, (200, 140, 255) if self.on else (80, 60, 100), (x - 9, 80, 18, 4))


# --- paintings that come alive ---

class MonaLisa(Painting):
    """The Mona Lisa, whose eyes follow you around the room. Closer, and she smiles a little more."""

    def __init__(self, x, y, w, h):
        super().__init__(x, y, w, h, "mona lisa")
        self.x, self.y, self.w, self.h = x, y, w, h
        self.look = (0.0, 0.0)
        self.near = False
        self.t = 0.0
        self.bubbles = [make_bubble(pygame.font.Font(None, 20), line)
                        for line in ("...I see you.", "Leonardo never finished me, you know.")]
        self.head_y = y + 20

    def update(self, dt, player):
        self.t += dt
        if player is None:
            return
        r = player.rect
        dx = max(-1.0, min(1.0, (r.centerx - (self.x + self.w / 2)) / 300))
        dy = max(-1.0, min(1.0, (r.centery - (self.y + self.h * 0.3)) / 300))
        self.look = (dx, dy)
        self.near = abs(r.centerx - (self.x + self.w / 2)) < 110

    def draw(self, surf):
        super().draw(surf)
        wink = self.t % 6.0 < 0.35                  # now and then, a wink
        for ex in (0.44, 0.56):                     # repaint the eyes, looking at you
            cx, cy = int(self.x + self.w * ex), int(self.y + self.h * 0.3)
            if wink and ex == 0.44:
                pygame.draw.arc(surf, (60, 40, 30), (cx - 4, cy - 2, 8, 6), 0.2, 2.9, 2)
                continue
            pygame.draw.ellipse(surf, (236, 226, 200), (cx - 4, cy - 2, 8, 5))
            pygame.draw.circle(surf, (50, 34, 24), (cx + round(self.look[0] * 2), cy + round(self.look[1])), 2)
        if self.near:                               # the famous smile, a bit wider
            mx, my = int(self.x + self.w * 0.5), int(self.y + self.h * 0.4)
            pygame.draw.arc(surf, (120, 60, 40), (mx - 9, my - 3, 18, 8), 3.4, 6.0, 2)

    def draw_bubble(self, surf):
        if self.near:
            b = self.bubbles[int(self.t / 2.8) % len(self.bubbles)]
            surf.blit(b, (self.x + self.w // 2 - b.get_width() // 2, self.y - b.get_height() - 4))


class LivingScream(Painting):
    """The Scream, which screams when you walk up to it."""

    def __init__(self, x, y, w, h):
        super().__init__(x, y, w, h, "scream")
        self.x, self.y, self.w, self.h = x, y, w, h
        self.near = False
        self.t = 0.0
        self.bubble = make_bubble(pygame.font.Font(None, 26), "AAAAAAAH!!")

    def update(self, dt, player):
        self.t += dt
        self.near = player is not None and abs(player.rect.centerx - (self.x + self.w / 2)) < 90

    def draw(self, surf):
        if not self.near:
            super().draw(surf)
            return
        shake = int(3 * math.sin(self.t * 40))
        surf.blit(self.image, (self.x + shake, self.y))
        mx, my = int(self.x + shake + self.w * 0.47), int(self.y + self.h * 0.6)
        open_ = 6 + int(3 * abs(math.sin(self.t * 12)))
        pygame.draw.ellipse(surf, (30, 20, 20), (mx - 4, my - open_ // 2, 9, open_ + 4))

    def draw_bubble(self, surf):
        if self.near:
            surf.blit(self.bubble, (self.x + self.w // 2 - self.bubble.get_width() // 2, self.y - self.bubble.get_height() - 4))


# --- the immersive Van Gogh room ---

class VanGogh(Person):
    """Vincent himself: straw hat, red beard, blue coat, and a bandage over one ear."""

    def draw(self, surf):
        super().draw(surf)
        hx, hy = self.x + 12, self.head_y
        pygame.draw.ellipse(surf, (200, 100, 40), (hx - 7, hy + 1, 14, 10))            # the red beard
        pygame.draw.ellipse(surf, (230, 200, 90), (hx - 14, hy - 10, 28, 7))           # straw hat brim
        pygame.draw.rect(surf, (230, 200, 90), (hx - 7, hy - 16, 14, 8), border_radius=3)
        pygame.draw.rect(surf, (245, 245, 245), (hx - 9, hy - 4, 5, 8))                 # the bandaged ear


class VanGoghChair(Furniture):
    """The yellow chair from "Van Gogh's Chair" (1888), with his pipe on the seat."""

    def __init__(self, x, y, name="Van Gogh's chair", holds_piece=False, w=50, h=70):
        super().__init__(x, y, w, h, name, holds_piece)

    def draw(self, surf):
        r = self.rect
        wood = (220, 170, 60) if not self.searched else (150, 130, 90)
        for x in (r.left + 4, r.right - 9):
            pygame.draw.rect(surf, wood, (x, r.top, 5, r.h))
        for y in range(r.top + 6, r.top + 34, 9):
            pygame.draw.line(surf, wood, (r.left + 4, y), (r.right - 4, y), 3)
        pygame.draw.rect(surf, (200, 160, 70), (r.left, r.top + 38, r.w, 8))          # rush seat
        pygame.draw.line(surf, (60, 40, 30), (r.left + 14, r.top + 36), (r.left + 30, r.top + 34), 3)   # the pipe
        pygame.draw.rect(surf, C.INK, r, 1)


class ArlesBed(Furniture):
    """The red-blanket bed from "The Bedroom" in Arles (1888)."""

    def __init__(self, x, y, name="the bed from The Bedroom", holds_piece=False, w=120, h=56):
        super().__init__(x, y, w, h, name, holds_piece)

    def draw(self, surf):
        r = self.rect
        wood = (200, 140, 60) if not self.searched else (140, 120, 100)
        pygame.draw.rect(surf, wood, (r.left, r.top, 10, r.h))                          # headboard
        pygame.draw.rect(surf, wood, (r.right - 8, r.top + 18, 8, r.h - 18))            # footboard
        pygame.draw.rect(surf, (200, 50, 40), (r.left + 10, r.top + 22, r.w - 18, 18))  # the red blanket
        pygame.draw.rect(surf, (236, 236, 200), (r.left + 12, r.top + 16, 26, 10), border_radius=3)   # pillow
        pygame.draw.rect(surf, wood, (r.left + 10, r.top + 40, r.w - 18, 6))
        pygame.draw.rect(surf, C.INK, r, 1)


class PortraitEasel(Furniture):
    """An easel with one of Van Gogh's self-portraits on it."""

    def __init__(self, x, y, name="self-portrait easel", holds_piece=False, w=70, h=110):
        super().__init__(x, y, w, h, name, holds_piece)

    def draw(self, surf):
        r = self.rect
        wood = (140, 100, 60) if not self.searched else (110, 100, 90)
        pygame.draw.line(surf, wood, (r.left + 8, r.bottom), (r.centerx, r.top), 4)
        pygame.draw.line(surf, wood, (r.right - 8, r.bottom), (r.centerx, r.top), 4)
        art = pygame.Rect(r.left + 6, r.top + 10, r.w - 12, 60)
        pygame.draw.rect(surf, (70, 120, 150), art)                                    # swirly blue background
        for k in range(3):
            pygame.draw.arc(surf, (110, 160, 190), art.inflate(-8 - k * 12, -8 - k * 10), 0, 4.5, 2)
        pygame.draw.ellipse(surf, (220, 170, 120), (art.centerx - 9, art.top + 12, 18, 24))   # face
        pygame.draw.ellipse(surf, (200, 100, 40), (art.centerx - 8, art.top + 26, 16, 12))    # beard
        pygame.draw.rect(surf, (50, 80, 160), (art.left + 8, art.bottom - 14, art.w - 16, 14))
        pygame.draw.rect(surf, (176, 140, 60), art, 3)
        pygame.draw.rect(surf, wood, (r.left + 2, art.bottom, r.w - 4, 5))


class ShootingStar:
    """A hazard of my own: a star that falls out of the painted sky, now and then, at a slant."""

    def __init__(self, xs, period=2.6, offset=0.0, speed=(-170, 320)):
        self.xs, self.period, self.speed = xs, period, speed
        self.t = offset
        self.n = 0
        self.rect = pygame.Rect(0, 0, 0, 0)
        self.pos = None

    def update(self, dt, room, player):
        self.t += dt
        if self.t >= self.period:
            self.t -= self.period
            self.n += 1
        fall = self.t - 1.0                         # it twinkles for a second, then drops
        x0 = self.xs[self.n % len(self.xs)]
        if fall < 0:
            self.pos, self.rect = (x0, 40), pygame.Rect(0, 0, 0, 0)
            return
        x, y = x0 + self.speed[0] * fall, 40 + self.speed[1] * fall
        if y > C.FLOOR_Y:
            self.pos, self.rect = None, pygame.Rect(0, 0, 0, 0)
            return
        self.pos = (x, y)
        self.rect = pygame.Rect(int(x) - 8, int(y) - 8, 16, 16)

    def draw(self, surf):
        if self.pos is None:
            return
        x, y = int(self.pos[0]), int(self.pos[1])
        if self.rect.w == 0:                        # about to fall: blinking warning
            if int(self.t * 8) % 2 == 0:
                pygame.draw.circle(surf, (255, 240, 150), (x, y), 6, 2)
            return
        tail = (x - self.speed[0] // 6, y - self.speed[1] // 6)
        pygame.draw.line(surf, (255, 220, 120), (x, y), tail, 4)
        pygame.draw.line(surf, (255, 250, 220), (x, y), ((x + tail[0]) // 2, (y + tail[1]) // 2), 2)
        for a in range(0, 360, 72):
            pygame.draw.line(surf, (255, 240, 150), (x, y),
                             (x + math.cos(math.radians(a + self.t * 400)) * 10, y + math.sin(math.radians(a + self.t * 400)) * 10), 3)
        pygame.draw.circle(surf, (255, 255, 230), (x, y), 5)


# --- animals and people who walk around ---
# They work like Person: put them in self.people AND self.decor. Only to look at: they never hurt you.

class Dog:
    """A little dog who trots around the room, stops to sniff, wags its tail, and barks hello when you're close.

    x is where it starts, y the surface it walks on, left..right how far it roams. color, ear: its coat.
    """

    def __init__(self, x, y, left, right, color=(200, 150, 90), ear=(140, 90, 50), name="Woof!", speed=60):
        self.x, self.y, self.left, self.right, self.speed = float(x), y, left, right, speed
        self.color, self.ear = color, ear
        self.dir = 1
        self.t = (x * 0.13) % 2
        self.pause = 0.0
        self.near = False
        font = pygame.font.Font(None, 20)
        self.bubbles = [make_bubble(font, line) for line in (name, "*wags tail*", "Woof woof!")]

    @property
    def head_y(self):
        return self.y - 20

    def update(self, dt, player):
        self.t += dt
        self.near = player is not None and abs(player.rect.centerx - self.x) < 90 and abs(player.rect.bottom - self.y) < 60
        if self.near:                               # it stops and looks at you
            if player.rect.centerx != int(self.x):
                self.dir = 1 if player.rect.centerx > self.x else -1
            return
        if self.pause > 0:                          # sniffing something
            self.pause -= dt
            return
        self.x += self.dir * self.speed * dt
        if self.x < self.left or self.x > self.right:
            self.dir *= -1
            self.x = max(self.left, min(self.right, self.x))
        if int(self.t * 10) % 37 == 0:              # now and then, stop and sniff
            self.pause = 1.2

    def draw(self, surf):
        x, y, d = int(self.x), self.y, self.dir
        walking = self.pause <= 0 and not self.near
        step = int(3 * math.sin(self.t * 14)) if walking else 0
        sniff = 3 if self.pause > 0 else 0
        for lx, s in ((-9, step), (-4, -step), (5, step), (10, -step)):           # four legs
            pygame.draw.line(surf, self.ear, (x + lx * d, y - 8), (x + lx * d + s, y), 3)
        pygame.draw.ellipse(surf, self.color, (x - 14, y - 18, 28, 12))           # body
        wag = int(5 * math.sin(self.t * (20 if self.near else 8)))
        pygame.draw.line(surf, self.color, (x - 13 * d, y - 15), (x - 19 * d, y - 22 + wag), 3)   # tail
        hx, hy = x + 14 * d, y - 20 + sniff
        pygame.draw.circle(surf, self.color, (hx, hy), 7)                           # head
        pygame.draw.ellipse(surf, self.color, (hx + (2 if d > 0 else -10), hy - 1, 8, 6))          # snout
        pygame.draw.circle(surf, C.INK, (hx + 9 * d, hy + 1), 2)                    # nose
        pygame.draw.circle(surf, C.INK, (hx + 2 * d, hy - 2), 1)                    # eye
        pygame.draw.ellipse(surf, self.ear, (hx - 5 * d - 3, hy - 5, 6, 10))       # floppy ear
        if self.near:
            pygame.draw.line(surf, (220, 80, 90), (hx + 6 * d, hy + 4), (hx + 7 * d, hy + 8), 2)   # tongue out

    def draw_bubble(self, surf):
        if not self.near:
            return
        b = self.bubbles[int(self.t / 1.6) % len(self.bubbles)]
        bx = max(4, min(C.W - b.get_width() - 4, int(self.x) - b.get_width() // 2))
        surf.blit(b, (bx, self.head_y - 14 - b.get_height()))


class Walker(Person):
    """A Person who strolls back and forth between left and right, and stops to chat when you're close."""

    def __init__(self, x, y, left, right, speed=40, **kw):
        super().__init__(x, y, pose="stand", **kw)
        self.left, self.right, self.speed = left, right, speed
        self.fx = float(x)

    def update(self, dt, player):
        super().update(dt, player)
        if self.near:
            if player is not None:
                self.facing = 1 if player.rect.centerx > self.x + 12 else -1
            self.pose = "talk"
            return
        self.pose = "stand"
        self.fx += self.facing * self.speed * dt
        if self.fx < self.left or self.fx > self.right:
            self.facing *= -1
            self.fx = max(self.left, min(self.right, self.fx))
        self.x = int(self.fx)

    def draw(self, surf):
        if self.pose == "stand":                    # a little walking bob
            self.pose = "talk" if int(self.t * 4) % 2 else "stand"
            super().draw(surf)
            self.pose = "stand"
        else:
            super().draw(surf)


class GiantVanGogh:
    """A giant, flickering projection of Van Gogh's face across the night sky. His glowing eyes follow you
    around the room; come close and they turn red and he speaks. Only to look at (and be scared of)."""

    W, H = 280, 330

    def __init__(self, x, y):
        self.x, self.y = x, y
        self.t = 0.0
        self.look = (0.0, 0.0)
        self.near = False
        rng = random.Random(1889)
        face = pygame.Surface((self.W, self.H), pygame.SRCALPHA)       # painted once, in brush strokes

        def strokes(rect, colors, n, length=10, width=3):
            for _ in range(n):
                sx = rng.randint(rect[0], rect[0] + rect[2])
                sy = rng.randint(rect[1], rect[1] + rect[3])
                a = rng.uniform(0, math.pi)
                pygame.draw.line(face, rng.choice(colors), (sx, sy),
                                 (sx + math.cos(a) * length, sy + math.sin(a) * length), width)

        pygame.draw.ellipse(face, (40, 60, 130), (0, 250, self.W, 160))                  # his blue coat
        strokes((10, 262, 260, 60), [(60, 90, 170), (30, 50, 110), (80, 120, 190)], 70, 14, 4)
        pygame.draw.ellipse(face, (210, 150, 100), (60, 50, 160, 210))                   # face
        strokes((80, 70, 120, 150), [(190, 130, 90), (120, 150, 100), (230, 170, 120)], 90, 8, 3)
        pygame.draw.ellipse(face, (200, 100, 40), (70, 170, 140, 110))                   # the red beard
        strokes((80, 180, 120, 90), [(230, 120, 50), (170, 70, 30), (240, 150, 70)], 80, 9, 3)
        pygame.draw.ellipse(face, (210, 150, 100), (112, 180, 56, 30))                  # around the mouth
        pygame.draw.ellipse(face, (200, 170, 70), (10, 20, 260, 46))                     # straw hat brim
        pygame.draw.rect(face, (200, 170, 70), (70, 0, 140, 44), border_radius=14)
        strokes((20, 4, 240, 54), [(230, 200, 90), (170, 140, 50)], 60, 12, 3)
        pygame.draw.rect(face, (245, 245, 240), (48, 120, 22, 56), border_radius=6)     # the bandaged ear
        for sx in (92, 148):                                                             # deep eye sockets
            pygame.draw.ellipse(face, (40, 26, 40), (sx, 108, 44, 30))
        pygame.draw.line(face, (140, 60, 30), (88, 96), (134, 112), 7)                  # angry brows
        pygame.draw.line(face, (140, 60, 30), (196, 96), (150, 112), 7)
        pygame.draw.line(face, (150, 90, 60), (140, 130), (132, 168), 4)                # nose
        pygame.draw.line(face, (150, 90, 60), (132, 168), (146, 170), 4)
        self.face = face
        big = pygame.font.Font(None, 28)
        self.bubbles = [make_bubble(big, line) for line in
                        ("Who goes there...?", "You can't escape my sky...", "Give... me... back... my... EAR!")]

    @property
    def head_y(self):
        return self.y

    def update(self, dt, player):
        self.t += dt
        if player is None:
            self.near = False
            return
        r = player.rect
        ex, ey = self.x + self.W / 2, self.y + 122
        dx, dy = r.centerx - ex, r.centery - ey
        dist = max(1.0, math.hypot(dx, dy))
        self.look = (dx / dist, dy / dist)
        self.near = abs(dx) < 200

    def draw(self, surf):
        t = self.t
        alpha = 150 + int(50 * math.sin(t * 1.3))
        if int(t * 6) % 23 == 0:                    # the projector glitches now and then
            alpha = 60
        self.face.set_alpha(alpha)
        surf.blit(self.face, (self.x, self.y))
        blink = (t % 4.0) < 0.15
        for sx in (92, 148):
            cx, cy = self.x + sx + 22, self.y + 123
            if blink:
                pygame.draw.line(surf, (60, 40, 50), (cx - 18, cy), (cx + 18, cy), 4)
                continue
            pygame.draw.ellipse(surf, (250, 236, 160), (cx - 16, cy - 10, 32, 20))      # glowing eyes
            px, py = cx + int(self.look[0] * 9), cy + int(self.look[1] * 5)
            pygame.draw.circle(surf, (200, 30, 30) if self.near else (30, 20, 20), (px, py), 7)
            pygame.draw.circle(surf, (255, 255, 255), (px - 2, py - 2), 2)
        mx, my = self.x + 140, self.y + 195
        if self.near:                               # he speaks
            open_ = 10 + int(8 * abs(math.sin(t * 6)))
            pygame.draw.ellipse(surf, (40, 10, 20), (mx - 22, my - open_ // 2, 44, open_))
        else:
            pygame.draw.arc(surf, (120, 50, 30), (mx - 20, my - 4, 40, 14), 0.3, 2.8, 3)   # a frown

    def draw_bubble(self, surf):
        if not self.near:
            return
        b = self.bubbles[int(self.t / 2.4) % len(self.bubbles)]
        surf.blit(b, (self.x + self.W // 2 - b.get_width() // 2, self.y + self.H - 40))


class Voice:
    """Something that isn't a person but talks anyway (a sculpture). Put it in self.people only, not in decor:
    it draws nothing, it just shows a speech bubble at (x, y) when you come close."""

    def __init__(self, x, y, lines, reach=70):
        self.x, self.y, self.reach = x, y, reach
        self.t = 0.0
        self.near = False
        font = pygame.font.Font(None, 20)
        self.bubbles = [make_bubble(font, line) for line in lines]

    def update(self, dt, player):
        self.t += dt
        self.near = (player is not None and abs(player.rect.centerx - self.x) < self.reach
                     and -40 < player.rect.bottom - self.y < 160)

    def draw(self, surf):
        pass

    def draw_bubble(self, surf):
        if not self.near:
            return
        b = self.bubbles[int(self.t / 2.8) % len(self.bubbles)]
        bx = max(4, min(C.W - b.get_width() - 4, self.x - b.get_width() // 2))
        surf.blit(b, (bx, self.y - 8 - b.get_height()))


class PeopleRoom(Room):
    """A room with people in it: they move and talk; their speech bubbles go over everything."""

    people = ()

    def update(self, dt, player):
        for p in self.people:
            p.update(dt, player)

    def draw_foreground(self, surf):
        for p in self.people:
            p.draw_bubble(surf)


# --- the rooms, west to east ---

class ReadingRoom(PeopleRoom):
    title = "Reading Room"

    def build(self):
        self.decor += [Sign(370, 46, "READING ROOM", (230, 200, 140)), CeilingLight(250), CeilingLight(700),
                       Window(640, 80, seed=4),
                       Painting(240, 110, 110, 80, "night"), Painting(470, 110, 80, 100, "pearl")]
        self.platforms.append(Platform(380, 400, 200))
        self.furniture += [Bookshelf(130, C.FLOOR_Y), Bookshelf(420, 400), Desk(640, C.FLOOR_Y, "study desk"),
                           Plant(800, C.FLOOR_Y), Sculpture(260, C.FLOOR_Y, "bust")]
        self.hazards.append(PatrolBot(300, C.FLOOR_Y, left=200, right=780, speed=70))
        self.people = [
            MonaLisa(120, 90, 90, 130),
            Dog(330, C.FLOOR_Y, left=230, right=760, name="Woof! (it's Leonardo's dog)"),
            Person(512, 400, "read", shirt=(150, 70, 90), hair=(120, 70, 30), seated=True, facing=-1,
                   lines=["Shh... this is a library.", "Vermeer used real ultramarine. So pricey!"]),
            Person(608, C.FLOOR_Y, "type", shirt=(60, 130, 110), hair=(20, 20, 20), skin=(190, 140, 100), seated=True,
                   lines=["My art history paper is due at 9 AM...", "Leonardo took 16 years on the Mona Lisa?!"]),
        ]
        self.decor += self.people
        self.people.append(Voice(290, 400, ["2,000 years old and I still don't have a body.", "Nice nose. Mine fell off twice."]))

    def draw_background(self, surf):
        surf.fill((92, 72, 60))                                   # warm wood paneling
        pygame.draw.rect(surf, (74, 56, 46), (0, 360, C.W, C.FLOOR_Y - 360))
        for x in range(0, C.W, 120):
            pygame.draw.line(surf, (70, 54, 44), (x, 360), (x, C.FLOOR_Y), 2)


class SlideArchive(PeopleRoom):
    """The digit is in the archive boxes on the top shelf: take the lift up, then dodge the book press."""

    title = "Slide and Archive Room"

    def build(self):
        self.decor += [Sign(330, 46, "SLIDE AND ARCHIVE ROOM", (200, 220, 240)), CeilingLight(470),
                       Poster(150, 90, "35mm", (70, 110, 160)), Poster(240, 90, "ARCHIVE", (150, 110, 70), w=96),
                       Timeline(360, 100, 300)]
        self.platforms.append(Platform(150, 400, 180))
        self.platforms.append(Platform(360, 300, 180))
        self.platforms.append(Platform(630, 200, 240))
        self.lifts.append(Lift(560, y_top=200, y_bottom=C.FLOOR_Y, width=64))
        self.furniture += [FilingCabinet(180, 400, "slide drawers"), LightTable(380, 300),
                           ArchiveBox(650, 200, holds_piece=True), FilingCabinet(800, 200, "old catalogs"),
                           Desk(660, C.FLOOR_Y, "scanner desk"), Sculpture(100, C.FLOOR_Y, "thinker"),
                           Sculpture(256, 400, "amphora")]
        self.people = [
            Person(784, C.FLOOR_Y, "stand", shirt=(110, 100, 80), hair=(200, 200, 200), facing=-1,
                   lines=["Careful, these slides are from 1965!", "The rare boxes are on the top shelf.",
                          "That press up there? Wait for it to rise."]),
            Dog(700, C.FLOOR_Y, left=600, right=840, color=(60, 60, 60), ear=(30, 30, 30),
                name="Woof! (the archivist's dog)", speed=40),
        ]
        self.decor += self.people
        self.people += [Voice(132, 396, ["I've been thinking for 140 years...", "...and I still forgot why I came in here."]),
                        Voice(278, 336, ["Handle with care.", "Get it? I have two handles."], reach=40)]
        self.hazards.append(FloorLaser(200, 520, on_time=1.2, off_time=1.6))
        self.hazards.append(Crusher(735, y_top=80, y_bottom=200, w=50, h=40))

    def draw_background(self, surf):
        surf.fill((50, 56, 70))                                   # dim, cool storage room
        for y in range(80, C.FLOOR_Y, 70):
            pygame.draw.line(surf, (60, 66, 82), (0, y), (C.W, y), 2)


class ConservationStudio(PeopleRoom):
    """Where damaged masterpieces get fixed. Stay out of the UV lamp's purple light."""

    title = "Conservation Studio"

    def build(self):
        self.decor += [Sign(330, 46, "CONSERVATION STUDIO", (230, 230, 240)),
                       BrokenPainting(95, 100, 100, 76, "clocks", "tear", seed=1),
                       BrokenPainting(215, 96, 70, 92, "sunflowers", "flaking", seed=2),
                       BrokenPainting(305, 100, 76, 96, "kiss", "cracked", seed=3),
                       BrokenPainting(400, 104, 70, 92, "scream", "hole"),
                       BrokenPainting(490, 100, 120, 76, "adam", "crooked"),
                       BrokenPainting(630, 96, 110, 76, "wave", "frame"),
                       BrokenPainting(770, 100, 80, 100, "mona lisa", "half"),
                       BrokenPainting(845, 236, 66, 80, "pearl", "tear", seed=4),
                       BrokenPainting(620, 230, 100, 70, "night", "cracked", seed=5),
                       XRayBox(190, 222, 100, 70), ToolRack(320, 236, 130, 60)]
        self.platforms.append(Platform(560, 400, 240))
        self.furniture += [RestorationEasel(110, C.FLOOR_Y, "mona lisa"), WorkTable(260, C.FLOOR_Y),
                           BrokenSculpture(400, C.FLOOR_Y, "discobolus"), BrokenSculpture(490, C.FLOOR_Y, "david"),
                           BrokenSculpture(570, 400, "nike"), BrokenSculpture(660, 400, "nefertiti")]
        self.hazards.append(UVLamp(150, 800, speed=110))
        self.people = [
            Person(205, C.FLOOR_Y, "type", shirt=(240, 240, 236), hair=(150, 60, 40), facing=-1,
                   lines=["Don't touch! The varnish is still wet.", "500 years of dirt on this one...",
                          "Someone dropped David. Again."]),
            Person(720, C.FLOOR_Y, "type", shirt=(240, 240, 236), hair=(30, 30, 30), skin=(200, 150, 110), facing=-1,
                   lines=["I'm just the intern!", "Is it bad if I glued his arm on backwards?"]),
            Walker(300, C.FLOOR_Y, left=280, right=760, shirt=(170, 60, 60), hair=(230, 200, 120),
                   lines=["Is this a real Van Gogh?", "I'm the museum's night guide!"]),
        ]
        self.decor += self.people
        self.people += [Voice(435, 390, ["Has anyone seen my arm?", "It was right here. With my discus."], reach=40),
                        Voice(520, 350, ["Can someone pass me my head?", "I lost it over a Goliath joke."], reach=40),
                        Voice(605, 280, ["No head, one wing. Still winning.", "They call me VICTORY, you know."], reach=40),
                        Voice(685, 310, ["Stop staring at my missing eye.", "3,300 years and not one wrinkle."], reach=40)]

    def draw_background(self, surf):
        surf.fill((84, 86, 92))                                   # clean, bright workshop walls
        pygame.draw.rect(surf, (72, 74, 80), (0, 330, C.W, C.FLOOR_Y - 330))


class LectureRoom(PeopleRoom):
    title = "Lecture Room"

    def build(self):
        self.decor += [Sign(380, 46, "LECTURE ROOM", (240, 220, 180)),
                       Poster(430, 100, "ART HIST", (130, 60, 70), w=96), CeilingLight(620), CeilingLight(820)]
        self.platforms.append(Platform(560, 440, 140))      # the tiered seats
        self.platforms.append(Platform(690, 380, 140))
        self.furniture += [Plant(100, C.FLOOR_Y), Lectern(300, C.FLOOR_Y), Seats(575, 440), Seats(710, 380),
                           Sculpture(480, C.FLOOR_Y, "venus")]
        self.screen = ProjectorScreen(120, 90, 260, 170)
        self.people = [
            LivingScream(545, 110, 80, 110),
            Person(250, C.FLOOR_Y, "talk", shirt=(70, 70, 80), hair=(90, 90, 90), always=True,
                   lines=["...and Mondrian painted this in 1921.", "Wait, that's my cat. Wrong slide.",
                          "Notice the primary colors.", "Who put sunglasses on the Mona Lisa?!", "Quiz on Thursday!"]),
            Person(575, 430, "stand", shirt=(200, 140, 60), hair=(60, 40, 20), seated=True, chair=False, facing=-1,
                   lines=["Is this on the exam?"]),
            Person(643, 430, "sleep", shirt=(90, 110, 170), hair=(160, 110, 50), seated=True, chair=False, facing=-1,
                   lines=["Zzz... five more minutes..."]),
            Person(744, 370, "type", shirt=(120, 60, 120), hair=(20, 20, 20), skin=(170, 120, 90), seated=True,
                   chair=False, facing=-1, lines=["I love this slide!"]),
        ]
        self.decor += self.people
        self.decor.insert(1, self.screen)
        self.people += [self.screen, Voice(505, 330, ["Has anyone seen my arms?", "I'd wave hello, but..."], reach=50)]
        self.hazards.append(Drone(450, y_top=300, y_bottom=C.FLOOR_Y, speed=80))
        self.hazards.append(PatrolBot(700, C.FLOOR_Y, left=540, right=850, speed=60))

    def draw_background(self, surf):
        surf.fill((64, 60, 74))
        pygame.draw.rect(surf, (54, 50, 62), (0, 300, C.W, C.FLOOR_Y - 300))


class ImmersiveVanGogh(PeopleRoom):
    """A projection room where The Starry Night fills the walls and moves, and a giant Van Gogh watches you.
    Watch for falling stars."""

    title = "Immersive Van Gogh"
    dark = 0.15                                     # the projection lights the room

    STARS = [(110, 90), (230, 60), (380, 70), (640, 64), (930, 150)]

    def build(self):
        self.decor.append(Sign(330, 20, "IMMERSIVE VAN GOGH", (250, 230, 140)))
        self.platforms += [Platform(150, 400, 170), MovingPlatform(350, 560, 320, width=110, speed=60),
                           Platform(690, 240, 180)]
        self.furniture += [VanGoghChair(200, 400), ArlesBed(450, C.FLOOR_Y), PortraitEasel(760, 240)]
        self.hazards += [ShootingStar([460, 720, 580, 820], period=2.6),
                         ShootingStar([420, 660, 540], period=3.1, offset=1.3)]
        self.people = [
            VanGogh(800, C.FLOOR_Y, "talk", shirt=(50, 80, 160), hair=(200, 100, 40), facing=-1,
                    lines=["Bonsoir! Welcome to my night sky.", "I painted it from my window, in 1889.",
                           "I sold only one painting in my whole life...", "Mind the falling stars!"]),
            Person(300, C.FLOOR_Y, "type", shirt=(230, 120, 160), hair=(240, 220, 120),
                   lines=["This is SO going on my story.", "Wait... is that the real Van Gogh?"]),
            Dog(400, C.FLOOR_Y, left=200, right=780, color=(230, 200, 120), ear=(180, 140, 70),
                name="Woof! (Vincent's dog)"),
        ]
        self.decor += self.people
        self.giant = GiantVanGogh(340, 40)        # drawn in the sky, behind the village; watches you
        self.people.append(self.giant)
        self.lights = [(840, 80, 110)] + [(x, y, 60) for x, y in self.STARS]
        self.front = pygame.Surface((C.W, C.FLOOR_Y), pygame.SRCALPHA)      # the village and cypress, made once
        pygame.draw.polygon(self.front, (30, 50, 90), [(0, 400), (200, 360), (420, 390), (640, 350), (960, 380),
                                                       (960, 500), (0, 500)])
        for i, x in enumerate(range(150, 900, 46)):
            h = 22 + (i * 7) % 16
            pygame.draw.rect(self.front, (40, 50, 70), (x, 470 - h, 34, h + 30))
            pygame.draw.rect(self.front, (250, 210, 90), (x + 12, 478 - h, 7, 7))
        pygame.draw.polygon(self.front, (40, 50, 70), [(560, 470), (574, 340), (588, 470)])   # the church spire
        pygame.draw.polygon(self.front, (14, 30, 20), [(36, 500), (46, 330), (62, 200), (74, 110), (88, 220),
                                                       (100, 340), (112, 500)])            # the cypress, like a flame
        for k in range(6):
            pygame.draw.arc(self.front, (30, 60, 40), (50, 140 + k * 55, 50, 70), 1.0, 4.0, 3)

    def draw_background(self, surf):
        t = self.time
        surf.fill((22, 40, 100))
        swirls = [(300, 170, 80, 1), (540, 140, 100, -1), (420, 260, 60, 1), (720, 230, 60, -1), (170, 260, 50, -1)]
        colors = [(70, 110, 190), (110, 150, 220), (170, 200, 240)]
        for cx, cy, r, turn in swirls:              # the sky turning, the way he painted it
            for k in range(3):
                start = turn * t * 0.8 + k * 2.1
                rr = r - k * 14
                pygame.draw.arc(surf, colors[k], (cx - rr, cy - rr * 0.6, 2 * rr, 1.2 * rr), start, start + 2.6, 5)
        for x0 in range(-200, C.W, 260):            # the long wind across the middle
            x = x0 + (t * 30) % 260
            pygame.draw.arc(surf, (130, 170, 230), (x, 190, 260, 60), 0.2, 2.9, 4)
        for i, (x, y) in enumerate(self.STARS):
            r = 9 + int(3 * math.sin(t * 2 + i))
            pygame.draw.circle(surf, (200, 200, 120), (x, y), r + 10, 3)
            pygame.draw.circle(surf, (230, 220, 120), (x, y), r + 4, 2)
            pygame.draw.circle(surf, (255, 245, 170), (x, y), r)
        pygame.draw.circle(surf, (230, 200, 80), (840, 80), 40, 4)        # the moon
        pygame.draw.circle(surf, (255, 220, 90), (840, 80), 26)
        pygame.draw.circle(surf, (22, 40, 100), (852, 72), 20)
        self.giant.draw(surf)
        surf.blit(self.front, (0, 0))


ROOMS = [ReadingRoom, SlideArchive, ConservationStudio, LectureRoom, ImmersiveVanGogh]
