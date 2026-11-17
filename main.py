"""Tenth Floor - the class game.

    python main.py                  # play the whole building
    python main.py --floor NAME     # practice your floor (floors/NAME.py): no clock, endless retries

The loop is async so the same file also runs in a web browser (built with pygbag): each frame it hands the
browser a turn with `await asyncio.sleep(0)`. On a computer that costs nothing.
"""
import argparse
import asyncio
import sys

import pygame

from engine import config as C, sound
from engine.game import Game, keys_from_keyboard


async def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--floor", help="practice one floor, by file name without .py")
    args, _ = ap.parse_known_args()

    pygame.init()
    screen = pygame.display.set_mode((C.W, C.H), pygame.SCALED)
    pygame.display.set_caption("Tenth Floor")
    game = Game(practice_floor=args.floor)
    clock = pygame.time.Clock()
    while True:
        start = False
        for e in pygame.event.get():
            if e.type == pygame.QUIT or (e.type == pygame.KEYDOWN and e.key == pygame.K_ESCAPE):
                pygame.quit()
                return 0
            if e.type == pygame.KEYDOWN and e.key == pygame.K_f:
                game.toggle_light()
            if e.type == pygame.KEYDOWN and e.key in (pygame.K_SPACE, pygame.K_RETURN):
                start = True
        dt = min(clock.tick(C.FPS) / 1000.0, 1 / 30)
        game.step(dt, keys_from_keyboard(), pressed_start=start)
        game.draw(screen)
        pygame.display.flip()
        sound.pump()                     # in a browser, sounds are made a little at a time, between frames
        await asyncio.sleep(0)


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
