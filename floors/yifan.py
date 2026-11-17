"""Floor 11: Interior Design - a design studio, then the materials library.

You come off the WEST elevator into the Design Studio, walk through into the Materials Library,
and get on the EAST elevator. Exactly ONE piece of furniture hides this floor's digit
(the sample drawer on the library's top shelf).
"""
import pygame

from engine import config as C
from engine.bots import PatrolBot, Zapper
from engine.room import Furniture, Lift, Platform, Room

NAME = "Interior Design"     # the name on the elevator panel
AUTHOR = "Yifan Wang"        # your name


# --- custom furniture looks (keep self.rect as the part you search) ---

class DraftingTable(Furniture):
    """A tilted drawing board on two legs."""

    def draw(self, surf):
        r = self.rect
        wood = (150, 118, 82) if not self.searched else (110, 100, 92)
        board = (236, 232, 220) if not self.searched else (170, 168, 162)
        # legs
        pygame.draw.line(surf, wood, (r.left + 6, r.top + 14), (r.left + 6, r.bottom), 4)
        pygame.draw.line(surf, wood, (r.right - 6, r.top + 6), (r.right - 6, r.bottom), 4)
        # tilted board
        pts = [(r.left, r.top + 18), (r.right, r.top), (r.right, r.top + 8), (r.left, r.top + 26)]
        pygame.draw.polygon(surf, board, pts)
        pygame.draw.polygon(surf, C.INK, pts, 2)


class SwatchShelf(Furniture):
    """A shelf full of fabric and material swatches."""

    COLORS = [(196, 120, 96), (122, 156, 128), (214, 190, 140), (96, 120, 160), (180, 150, 190)]

    def draw(self, surf):
        r = self.rect
        pygame.draw.rect(surf, (120, 92, 66) if not self.searched else (90, 86, 82), r, border_radius=2)
        pygame.draw.rect(surf, C.INK, r, 2, border_radius=2)
        rows = max(1, (r.height - 8) // 22)
        for row in range(rows):
            y = r.top + 6 + row * 22
            for i, x in enumerate(range(r.left + 5, r.right - 8, 9)):
                col = self.COLORS[(i + row) % len(self.COLORS)]
                if self.searched:
                    col = tuple(c // 2 + 40 for c in col)
                pygame.draw.rect(surf, col, (x, y, 7, 16))


class Sofa(Furniture):
    """A low sample sofa."""

    def draw(self, surf):
        r = self.rect
        col = (98, 132, 140) if not self.searched else (90, 96, 100)
        pygame.draw.rect(surf, col, (r.left, r.top + r.height // 3, r.width, r.height * 2 // 3), border_radius=6)
        pygame.draw.rect(surf, col, (r.left + 6, r.top, r.width - 12, r.height // 2), border_radius=6)
        pygame.draw.rect(surf, C.INK, r, 2, border_radius=6)


# --- LEFT room: the West elevator is through its left edge ---

class DesignStudio(Room):
    title = "Design Studio"

    def build(self):
        # Two ledges and a lift up to the high mezzanine.
        self.platforms.append(Platform(120, 390, 230))
        self.platforms.append(Platform(560, 280, 300))
        self.lifts.append(Lift(470, y_top=280, y_bottom=C.FLOOR_Y, width=70))

        self.furniture.append(DraftingTable(160, 390, 60, 50, "drafting table"))
        self.furniture.append(DraftingTable(260, 390, 60, 50, "drafting table 2"))
        self.furniture.append(Furniture(620, 280, 60, 70, "model stand"))
        self.furniture.append(Furniture(760, 280, 70, 50, "plan cabinet"))
        self.furniture.append(Sofa(800, C.FLOOR_Y, 110, 40, "sample sofa"))

        self.hazards.append(PatrolBot(300, C.FLOOR_Y, left=240, right=840, speed=80))
        self.hazards.append(PatrolBot(700, 280, left=600, right=860, speed=60, sees=False))
        # Fonts and text are made once, here, never in a draw function.
        self.sign = pygame.font.Font(None, 28).render("INTERIOR DESIGN - STUDIO 11", True, (90, 70, 50))

    def draw_background(self, surf):
        surf.fill((214, 206, 192))                     # warm plaster wall
        for x in range(40, C.W, 180):                  # tall studio windows
            pygame.draw.rect(surf, (150, 176, 196), (x, 70, 110, 240), border_radius=3)
            pygame.draw.rect(surf, (120, 110, 100), (x, 70, 110, 240), 3, border_radius=3)
            pygame.draw.line(surf, (120, 110, 100), (x + 55, 70), (x + 55, 310), 2)
        surf.blit(self.sign, (C.W // 2 - self.sign.get_width() // 2, 40))


# --- RIGHT room: the East elevator is through its right edge ---

class LaserMeasure:
    """A hazard of our own: a laser-measure dot sweeping across the room."""

    def __init__(self, y, left, right, speed):
        self.y, self.left, self.right, self.speed = y, left, right, speed
        self.x = float(left)
        self.dir = 1
        self.rect = pygame.Rect(left, y, 24, 24)
        self.glow = pygame.Surface((80, 80), pygame.SRCALPHA)     # made once, not every frame
        pygame.draw.circle(self.glow, (255, 60, 60, 60), (40, 40), 38)

    def update(self, dt, room, player):
        self.x += self.dir * self.speed * dt
        if self.x < self.left or self.x > self.right:
            self.dir *= -1
            self.x = max(self.left, min(self.right, self.x))
        self.rect.x = int(self.x)

    def draw(self, surf):
        surf.blit(self.glow, (self.rect.centerx - 40, self.rect.centery - 40))
        pygame.draw.circle(surf, (255, 70, 70), self.rect.center, 10)


class MaterialsLibrary(Room):
    title = "Materials Library"

    def build(self):
        self.platforms.append(Platform(80, 410, 200))
        self.platforms.append(Platform(330, 330, 180))
        self.platforms.append(Platform(570, 250, 200))
        self.furniture.append(SwatchShelf(110, 410, 80, 48, "fabric shelf"))
        self.furniture.append(SwatchShelf(370, 330, 80, 48, "tile shelf"))
        self.furniture.append(Furniture(640, 250, 80, 40, "sample drawer", holds_piece=True))
        self.furniture.append(Furniture(520, C.FLOOR_Y, 120, 30, "pin-up bench"))
        self.hazards.append(Zapper(300, y_top=340, y_bottom=C.FLOOR_Y, on_time=1.2, off_time=1.8))
        self.hazards.append(Zapper(820, y_top=340, y_bottom=C.FLOOR_Y, on_time=1.2, off_time=1.8, offset=1.5))
        self.hazards.append(LaserMeasure(200, left=560, right=900, speed=140))
        self.sign = pygame.font.Font(None, 28).render("MATERIALS LIBRARY - RETURN ALL SAMPLES", True, (240, 230, 210))

    def draw_background(self, surf):
        surf.fill((70, 62, 56))                        # dark walnut walls
        cols = [(196, 120, 96), (122, 156, 128), (214, 190, 140), (96, 120, 160), (180, 150, 190)]
        for row, y in enumerate(range(80, 320, 40)):   # wall of material sample tiles
            for i, x in enumerate(range(40, C.W - 40, 46)):
                pygame.draw.rect(surf, cols[(i * 2 + row) % len(cols)], (x, y, 36, 30))
                pygame.draw.rect(surf, (40, 34, 30), (x, y, 36, 30), 1)
        surf.blit(self.sign, (C.W // 2 - self.sign.get_width() // 2, 40))


LEFT = DesignStudio        # off the West elevator
RIGHT = MaterialsLibrary   # on to the East elevator