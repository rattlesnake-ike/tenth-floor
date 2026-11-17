"""The ground floor, built with the engine: the security desk where you start, and the Flatiron Gallery's
hallway out to the West elevator. Students don't edit this; it shows the controls before anyone's floor."""
import pygame

from . import config as C
from .bots import PatrolBot, Zapper
from .room import Furniture, Platform, Room

NAME = "Lobby / Flatiron Gallery"
AUTHOR = "the class"


class Plinth(Furniture):
    """A plinth with a sculpture on it. Searching it finds nothing; it's the gallery. kind picks the piece."""

    def __init__(self, x, y, kind, label):
        super().__init__(x, y, 70, 46, label)
        self.kind = kind

    def draw(self, surf):
        r = self.rect
        pygame.draw.rect(surf, (226, 223, 215), r)
        pygame.draw.rect(surf, C.INK, r, 2)
        cx, top = r.centerx, r.top
        if self.kind == "primitives":           # 3D class: a cube, a sphere and a cone, stacked
            pygame.draw.rect(surf, (200, 80, 70), (cx - 22, top - 30, 44, 30))
            pygame.draw.circle(surf, (70, 120, 190), (cx, top - 46), 16)
            pygame.draw.polygon(surf, (235, 190, 60), [(cx - 12, top - 62), (cx + 12, top - 62), (cx, top - 92)])
            for shape in ((cx - 22, top - 30, 44, 30),):
                pygame.draw.rect(surf, C.INK, shape, 2)
        elif self.kind == "vase":               # ceramics: a striped pot
            body = pygame.Rect(cx - 20, top - 56, 40, 56)
            pygame.draw.ellipse(surf, (60, 110, 120), body)
            for i, col in enumerate(((230, 220, 200), (190, 90, 60), (230, 220, 200))):
                pygame.draw.line(surf, col, (body.left + 6, body.top + 18 + i * 9), (body.right - 6, body.top + 18 + i * 9), 3)
            pygame.draw.rect(surf, (60, 110, 120), (cx - 9, top - 64, 18, 10))
            pygame.draw.ellipse(surf, C.INK, body, 2)
        else:                                   # neon: a hand-bent sign that hums
            on = (pygame.time.get_ticks() // 700) % 5 != 0
            glow = (255, 90, 170) if on else (110, 60, 90)
            box = pygame.Rect(cx - 30, top - 44, 60, 40)
            pygame.draw.rect(surf, (30, 30, 36), box, border_radius=6)
            pygame.draw.lines(surf, glow, False, [(box.left + 10, box.bottom - 10), (box.left + 22, box.top + 10),
                                                  (box.centerx, box.bottom - 12), (box.right - 22, box.top + 10),
                                                  (box.right - 10, box.bottom - 10)], 3)


def _comic(font):
    """Cartooning: a six-panel page with a character and a speech balloon."""
    page = pygame.Surface((120, 150))
    page.fill((250, 248, 240))
    for i in range(6):
        px, py = 6 + (i % 2) * 56, 6 + (i // 2) * 47
        pygame.draw.rect(page, (20, 20, 20), (px, py, 52, 43), 2)
        head = (px + 16 + i * 3, py + 26)
        pygame.draw.circle(page, (20, 20, 20), head, 6, 2)
        pygame.draw.line(page, (20, 20, 20), (head[0], head[1] + 6), (head[0], py + 40), 2)
        if i in (1, 4):
            pygame.draw.ellipse(page, (20, 20, 20), (px + 26, py + 4, 22, 14), 2)
    page.blit(font.render("!", True, (200, 40, 40)), (95, 102))
    return page


def _photo():
    """Photography: a black-and-white print of the street, a wedge-shaped building in the middle."""
    img = pygame.Surface((150, 110))
    img.fill((200, 200, 196))
    for i, (x, w, h) in enumerate(((0, 30, 60), (28, 22, 80), (100, 26, 70), (124, 26, 50))):
        pygame.draw.rect(img, (70 + i * 12,) * 3, (x, 110 - h, w, h))
    pygame.draw.polygon(img, (40, 40, 42), [(52, 110), (98, 110), (90, 18), (60, 18)])      # the wedge
    for y in range(26, 106, 9):
        pygame.draw.line(img, (150, 150, 146), (62, y), (88, y), 1)
    pygame.draw.rect(img, (250, 250, 250), img.get_rect(), 6)                                # the print's border
    return img


def _poster(big, small):
    """Design: a type poster."""
    img = pygame.Surface((110, 150))
    img.fill((235, 60, 50))
    for i, word in enumerate(("LOOK", "MAKE", "SHOW")):
        img.blit(big.render(word, True, (250, 245, 235) if i != 1 else (20, 20, 24)), (10, 12 + i * 36))
    img.blit(small.render("open late", True, (20, 20, 24)), (10, 126))
    return img


class GalleryHall(Room):
    """Left of the lobby: the gallery hallway, hung with work from SVA's departments. The West elevator is
    through its left wall."""

    title = "Flatiron Gallery"

    def build(self):
        self.furniture.append(Plinth(150, C.FLOOR_Y, "primitives", "sculpture: three primitives"))
        self.furniture.append(Plinth(440, C.FLOOR_Y, "vase", "ceramics: striped pot"))
        self.platforms.append(Platform(600, 400, 170))                  # the mezzanine bench
        self.furniture.append(Plinth(650, 400, "neon", "neon: hand-bent sign"))
        self.furniture.append(Furniture(820, C.FLOOR_Y, 70, 30, "visitor bench"))
        # A slow guard bot that doesn't chase: jump over it (run and jump to flip).
        self.hazards.append(PatrolBot(300, C.FLOOR_Y, left=260, right=560, speed=55, sees=False))
        f = pygame.font.Font(None, 30)
        self.sign = f.render("SVA FLATIRON GALLERY", True, (40, 40, 44))
        self.hint = pygame.font.Font(None, 22).render(
            "WEST ELEVATOR  <--   run + SPACE to flip over a bot", True, (70, 70, 76))
        cap = pygame.font.Font(None, 18)
        self.works = [(_comic(pygame.font.Font(None, 40)), 70, "Cartooning"),
                      (_photo(), 250, "Photography"),
                      (_poster(pygame.font.Font(None, 40), pygame.font.Font(None, 16)), 470, "Design"),
                      (None, 660, "Animation")]
        self.captions = [cap.render(t, True, (90, 90, 96)) for _, _, t in self.works]

    def draw_background(self, surf):
        surf.fill((236, 233, 226))                                       # white-cube walls
        for x in range(90, C.W, 210):                                    # track lights
            pygame.draw.line(surf, (190, 186, 178), (x, 36), (x + 40, 60), 3)
        for (img, x, _), capimg in zip(self.works, self.captions):
            if img is None:                                              # animation: a walk cycle on a screen
                screen = pygame.Rect(x, 110, 170, 110)
                pygame.draw.rect(surf, (24, 26, 32), screen)
                frame = (pygame.time.get_ticks() // 120) % 8
                fx = screen.left + 20 + frame * 16
                head = (fx, screen.top + 40)
                swing = (-9, -5, 0, 5, 9, 5, 0, -5)[frame] or 3
                ink = (240, 236, 220)
                pygame.draw.circle(surf, ink, head, 7, 2)
                pygame.draw.line(surf, ink, (fx, head[1] + 7), (fx, head[1] + 32), 2)
                pygame.draw.line(surf, ink, (fx, head[1] + 32), (fx - swing, head[1] + 52), 2)
                pygame.draw.line(surf, ink, (fx, head[1] + 32), (fx + swing, head[1] + 52), 2)
                pygame.draw.line(surf, ink, (fx, head[1] + 14), (fx + swing, head[1] + 28), 2)
                pygame.draw.rect(surf, (30, 30, 30), screen, 4)
                bottom = screen.bottom
            else:
                surf.blit(img, (x, 110))
                pygame.draw.rect(surf, (30, 30, 30), (x, 110, img.get_width(), img.get_height()), 3)
                bottom = 110 + img.get_height()
            surf.blit(capimg, (x, bottom + 6))
        surf.blit(self.sign, (C.W // 2 - self.sign.get_width() // 2, 46))
        surf.blit(self.hint, (20, 300))


class SecurityDesk(Room):
    """Right of the lobby: where the game starts, at its left side. The East elevator is through its right
    edge, past security: a metal detector that switches on and off, and a guard that speeds up when it sees
    you. Time the gate, then jump the guard, or go over him from the monitor ledge."""

    title = "Security Desk"

    def build(self):
        self.furniture.append(Furniture(560, C.FLOOR_Y, 160, 60, "security desk"))
        self.furniture.append(Furniture(320, C.FLOOR_Y, 40, 70, "turnstile"))
        self.furniture.append(Furniture(130, C.FLOOR_Y, 60, 90, "coat rack"))
        self.platforms.append(Platform(760, 400, 150))
        self.furniture.append(Furniture(790, 400, 60, 40, "monitor bank"))
        self.hazards.append(Zapper(430, y_top=300, on_time=1.0, off_time=1.3))                  # the metal detector
        self.hazards.append(PatrolBot(700, C.FLOOR_Y, left=490, right=870, speed=70, sees=True))  # the guard
        f = pygame.font.Font(None, 30)
        self.sign = f.render("SVA  -  133/141 WEST 21ST STREET", True, (220, 220, 228))
        small = pygame.font.Font(None, 24)
        self.lines = [small.render(t, True, (200, 204, 214)) for t in (
            "After hours. MFA Computer Arts is on floor 10, and its door takes a code.",
            "Every floor hides one digit. Hold UP at furniture to search it.",
            "West elevator: the basement up to 9. East elevator, to the right: here to the top.",
            "Walk across a floor to switch elevators.   <-- West      East (past security) -->")]

    def draw_background(self, surf):
        surf.fill((44, 48, 60))
        pygame.draw.rect(surf, (58, 62, 78), (0, 300, C.W, 200))         # marble wainscot
        pygame.draw.rect(surf, (80, 84, 96), (412, 292, 36, 8))         # the detector's frame
        surf.blit(self.sign, (C.W // 2 - self.sign.get_width() // 2, 46))
        for i, img in enumerate(self.lines):
            surf.blit(img, (40, 110 + i * 30))


LEFT = GalleryHall
RIGHT = SecurityDesk
