"""Mo's Cafe: Nora Wentz's floor (claim #3), from a starter.

Two rooms, west to east: the counter (with a shelf holding the digit) and the seating area,
which is a dead end - the East elevator doesn't come down to the basement, so walk back
through the library to leave.

Eat the snack on the counter (hold UP in front of it) to gain a one-hit shield: the first
hazard that touches you after that does nothing, the second one catches you.
"""
import math

import pygame

from engine import config as C
from engine.kit import (CeilingLight, Couch, Desk, FloorLaser, PatrolBot, Plant, Poster, Sign,
                        VendingMachine, Window)
from engine.room import Platform, Room

NAME = "Mo's Cafe"
AUTHOR = "Nora Wentz"

SHIELD_AVAILABLE = False


class Food:
    """A snack you eat by holding UP in front of it (one hit shield afterwards)."""

    def __init__(self, x, y):
        import pygame
        self.rect = pygame.Rect(int(x), int(y - 24), 40, 24)
        self.name = "cafe snack"
        self.holds_piece = False
        self.searched = False
        self.progress = 0.0

    def draw(self, surf):
        r = self.rect
        if self.searched:
            # empty plate
            pygame.draw.ellipse(surf, (220, 210, 190), (r.x, r.bottom - 6, r.w, 12))
            pygame.draw.ellipse(surf, C.INK, (r.x, r.bottom - 6, r.w, 12), 2)
            return
        pygame.draw.rect(surf, (200, 120, 60), r, border_radius=4)
        pygame.draw.rect(surf, (240, 200, 120), r.inflate(-6, -6), border_radius=3)
        pygame.draw.rect(surf, C.INK, r, 2, border_radius=4)


class Counter(Room):
    """The counter and the espresso shelf. The digit is in the vending machine up on the shelf."""

    title = "Mo's Cafe: the counter"

    def build(self):
        self.decor += [Sign(400, 46, "MO'S CAFE"), CeilingLight(260), CeilingLight(700),
                       Poster(120, 90, "COFFEE", (150, 100, 60)), Poster(820, 90, "OPEN", (80, 140, 90)),
                       Window(40, 70, seed=1)]
        self.platforms.append(Platform(260, 420, 160))        # the counter top
        self.platforms.append(Platform(500, 330, 220))        # the shelf behind it
        food = Food(290, 420)
        self.furniture += [Desk(130, C.FLOOR_Y), Plant(450, C.FLOOR_Y),
                           VendingMachine(600, 330, holds_piece=True),
                           Desk(780, C.FLOOR_Y), food]
        self.hazards.append(PatrolBot(520, C.FLOOR_Y, left=440, right=820, speed=80))
        self._food = food

    def update(self, dt, player):
        global SHIELD_AVAILABLE
        if self._food.searched and not SHIELD_AVAILABLE:
            SHIELD_AVAILABLE = True

    def tick(self, dt, player):
        super().tick(dt, player)
        global SHIELD_AVAILABLE
        if SHIELD_AVAILABLE and player.safe <= 0:
            for h in self.hazards:
                if player.rect.colliderect(h.rect):
                    SHIELD_AVAILABLE = False
                    h.rect = pygame.Rect(0, 0, 0, 0)
                    break

    def draw_foreground(self, surf):
        if SHIELD_AVAILABLE:
            font = pygame.font.Font(None, 22)
            img = font.render("SHIELD READY", True, (120, 230, 140))
            surf.blit(img, (C.W - img.get_width() - 12, 12))


class Seating(Room):
    """Tables, couches and a dead end: the East elevator doesn't come down to the basement."""

    title = "Mo's Cafe: seating"

    def build(self):
        self.decor += [Window(150, 70, seed=3), Window(620, 70, seed=4), CeilingLight(480),
                       Sign(380, 46, "SEATING")]
        self.platforms.append(Platform(250, 390, 150))
        self.furniture += [Couch(140, C.FLOOR_Y), Desk(380, C.FLOOR_Y), Desk(560, C.FLOOR_Y),
                           Couch(740, C.FLOOR_Y), Plant(280, 390), Plant(880, C.FLOOR_Y)]
        self.hazards.append(FloorLaser(320, 560, on_time=1.1, off_time=1.7))

    def tick(self, dt, player):
        super().tick(dt, player)
        global SHIELD_AVAILABLE
        if SHIELD_AVAILABLE and player.safe <= 0:
            for h in self.hazards:
                if player.rect.colliderect(h.rect):
                    SHIELD_AVAILABLE = False
                    h.rect = pygame.Rect(0, 0, 0, 0)
                    break

    def draw_foreground(self, surf):
        if SHIELD_AVAILABLE:
            font = pygame.font.Font(None, 22)
            img = font.render("SHIELD READY", True, (120, 230, 140))
            surf.blit(img, (C.W - img.get_width() - 12, 12))


ROOMS = [Counter, Seating]
