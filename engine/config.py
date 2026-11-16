"""Numbers the whole game shares. Room authors read these; only the engine owner changes them."""

W, H = 960, 540          # every room is exactly one screen
FPS = 60
FLOOR_Y = 500            # top of the ground floor in every room
WALL_X = 0               # rooms run edge to edge

# Player feel. The check script uses the same numbers to decide what a player can reach.
RUN_SPEED = 230.0        # pixels per second
JUMP_SPEED = 560.0       # launch speed straight up
GRAVITY = 1500.0         # pixels per second squared
MAX_FALL = 900.0
JUMP_HEIGHT = JUMP_SPEED ** 2 / (2 * GRAVITY)        # about 104 px
JUMP_REACH = RUN_SPEED * (2 * JUMP_SPEED / GRAVITY)   # about 171 px across flat ground

SEARCH_SECONDS = 1.2     # hold UP this long in front of furniture
CLOCK_SECONDS = 10 * 60  # the whole run
DEATH_PENALTY = 20       # seconds off the clock each time a bot gets you

# Palette. Rooms may use their own colours; these keep the shared parts readable.
INK = (20, 22, 28)
PAPER = (236, 232, 222)
SHAFT = (44, 48, 60)
WALL = (70, 74, 88)
PLATFORM = (200, 196, 182)
PLATFORM_EDGE = (120, 116, 104)
PIECE = (255, 196, 40)
DANGER = (230, 70, 60)
HUD = (250, 250, 250)
JUMP_SPEED = 900.0
