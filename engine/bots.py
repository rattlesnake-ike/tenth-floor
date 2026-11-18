"""Hazards you can use as they are, or subclass for your own.

Any hazard is an object with .rect, .update(dt, room, player) and .draw(surf). Touching its rect
costs the player a life (DEATH_PENALTY seconds off the clock) and sends them back to the door.

The security team, each one beaten a different way:
    PatrolBot       rolls back and forth on a surface            flip over it, or stay behind it
    HopBot          hops along a surface                         run under it while it's in the air
    SkyBot          flies a wavy path in the air                 duck under or time the gap
    PopUpBot        rises out of a floor hatch on a timer        cross while the hatch is shut
    SentryBot       stands still and fires pucks straight ahead  jump the puck, or come from behind
    Zapper          a beam that switches on and off              cross while it's off
    SecurityCamera  sweeps a spotlight along a surface           run at the spot and jump it
Robots never turn to face you (Decision 5): their eye shows which way they face, and behind them you're safe.
"""
import math

import pygame

from . import config as C


class PatrolBot:
    """A security bot that rolls back and forth along a surface.

    x is where it starts; y is the surface it rolls on (C.FLOOR_Y for the ground, or a platform's y).
    It patrols between left and right. With sees=True it speeds up when the player is on its level
    and in front of it.
    """

    W, H = 34, 40

    def __init__(self, x, y, left, right, speed=90.0, sees=True):
        self.x = float(x)
        self.y_surface = int(y)
        self.left, self.right = int(left), int(right)
        self.speed = float(speed)
        self.sees = sees
        self.dir = 1
        self.alert = False
        self.t = 0.0
        self.rect = pygame.Rect(int(self.x), self.y_surface - self.H, self.W, self.H)

    def update(self, dt, room, player):
        self.t += dt
        level = abs(player.rect.bottom - self.y_surface) < 6
        ahead = (player.rect.centerx - self.rect.centerx) * self.dir > 0
        self.alert = self.sees and level and ahead and abs(player.rect.centerx - self.rect.centerx) < 320
        v = self.speed * (2.2 if self.alert else 1.0)
        self.x += self.dir * v * dt
        if self.x < self.left:
            self.x, self.dir = float(self.left), 1
        elif self.x + self.W > self.right:
            self.x, self.dir = float(self.right - self.W), -1
        self.rect.x = int(self.x)

    def draw(self, surf):
        r = self.rect
        pygame.draw.rect(surf, (60, 64, 72), r, border_radius=8)
        pygame.draw.rect(surf, C.INK, r, 2, border_radius=8)
        eye_x = r.centerx + self.dir * 8
        eye = C.DANGER if self.alert else (120, 220, 255)
        pygame.draw.circle(surf, eye, (eye_x, r.top + 13), 6)
        if self.alert:
            s = pygame.Surface((90, 30), pygame.SRCALPHA)
            tip = 0 if self.dir > 0 else 90
            pygame.draw.polygon(s, (230, 70, 60, 70), [(tip, 13), (90 - tip, 2), (90 - tip, 28)])
            surf.blit(s, (eye_x if self.dir > 0 else eye_x - 90, r.top))
        wob = int(2 * math.sin(self.t * 14))
        pygame.draw.circle(surf, C.INK, (r.left + 8, r.bottom), 5 + (wob > 0))
        pygame.draw.circle(surf, C.INK, (r.right - 8, r.bottom), 5 + (wob <= 0))


class Zapper:
    """A floor-to-ceiling beam that switches on and off. x is its centre; it spans y_top..y_bottom.

    on_time and off_time are seconds; offset shifts it in the cycle so two zappers can alternate.
    For the last WARN seconds before it switches on, a faint flicker shows it's about to fire; it can't
    catch you until it's really on.
    """

    WARN = 0.5

    def __init__(self, x, y_top=0, y_bottom=C.FLOOR_Y, on_time=1.5, off_time=1.5, offset=0.0):
        self.on_time, self.off_time, self.t = on_time, off_time, offset
        self.on = self.warning = False
        self.box = pygame.Rect(int(x) - 4, int(y_top), 8, int(y_bottom - y_top))
        self.rect = pygame.Rect(0, 0, 0, 0)

    def update(self, dt, room, player):
        self.t = (self.t + dt) % (self.on_time + self.off_time)
        self.on = self.t < self.on_time
        self.warning = not self.on and (self.on_time + self.off_time) - self.t <= min(self.WARN, self.off_time)
        self.rect = self.box if self.on else pygame.Rect(0, 0, 0, 0)

    def draw(self, surf):
        pygame.draw.rect(surf, (90, 90, 100), (self.box.x - 4, self.box.top - 8, 16, 8))
        pygame.draw.rect(surf, (90, 90, 100), (self.box.x - 4, self.box.bottom, 16, 8))
        if self.on:
            pygame.draw.rect(surf, C.DANGER, self.box)
            pygame.draw.rect(surf, (255, 200, 190), self.box.inflate(-4, 0))
        elif self.warning and int(self.t * 20) % 2:
            pygame.draw.line(surf, (170, 80, 80), self.box.midtop, self.box.midbottom, 1)


class SecurityCamera:
    """A ceiling camera that sweeps a spotlight back and forth along a surface. Step into the lit spot and
    you're caught; jump over it, or wait while it pauses at the end of its sweep.

    x is where the camera hangs (from the ceiling at y=46). The spot sweeps between left and right along the
    surface at y (C.FLOOR_Y for the ground, or a platform's y), at speed px/s, and waits `pause` seconds at
    each end. spot is how wide the lit spot is. offset (px) starts the spot further along its sweep.
    """

    MOUNT_Y = 46

    def __init__(self, x, y=C.FLOOR_Y, left=None, right=None, speed=110.0, pause=0.6, spot=70, offset=0.0):
        self.x, self.y_surface = int(x), int(y)
        self.left = int(left if left is not None else x - 200)
        self.right = int(right if right is not None else x + 200)
        self.speed, self.pause, self.spot = float(speed), float(pause), int(spot)
        self.cx = float(min(self.right, self.left + offset))
        self.dir = 1                # which way the spot is moving (a moving hazard: not a doorway blocker)
        self.wait = 0.0
        self.rect = pygame.Rect(0, 0, 0, 0)
        self.glow = pygame.Surface((self.spot, 18), pygame.SRCALPHA)     # made once, not every frame
        pygame.draw.ellipse(self.glow, (255, 240, 170, 110), self.glow.get_rect())
        self._place()

    def _place(self):
        # The part that catches you: the lit patch, from the surface up to ankle height.
        self.rect = pygame.Rect(int(self.cx - self.spot / 2) + 6, self.y_surface - 14, self.spot - 12, 14)

    def update(self, dt, room, player):
        if self.wait > 0:
            self.wait -= dt
        else:
            self.cx += self.dir * self.speed * dt
            if self.cx >= self.right:
                self.cx, self.dir, self.wait = float(self.right), -1, self.pause
            elif self.cx <= self.left:
                self.cx, self.dir, self.wait = float(self.left), 1, self.pause
        self._place()

    def draw(self, surf):
        cam = (self.x, self.MOUNT_Y + 10)
        half = self.spot // 2
        beam = (255, 236, 160)
        pygame.draw.line(surf, beam, cam, (int(self.cx) - half, self.y_surface), 1)
        pygame.draw.line(surf, beam, cam, (int(self.cx) + half, self.y_surface), 1)
        surf.blit(self.glow, (int(self.cx) - half, self.y_surface - 9))
        pygame.draw.rect(surf, (90, 90, 100), (self.x - 3, self.MOUNT_Y - 6, 6, 8))
        body = pygame.Rect(0, 0, 26, 14)
        body.center = cam
        pygame.draw.rect(surf, (200, 202, 210), body, border_radius=4)
        pygame.draw.rect(surf, C.INK, body, 2, border_radius=4)
        lens_x = body.centerx + (6 if self.cx > self.x else -6)
        pygame.draw.circle(surf, C.DANGER, (lens_x, body.centery + 2), 3)



def _robot_eye(surf, center, alert):
    """Every robot's eye: blue while it hasn't seen you, red when it has."""
    pygame.draw.circle(surf, C.DANGER if alert else (120, 220, 255), center, 5)


class HopBot:
    """A spring-legged bot that hops along a surface between left and right, resting between hops.

    x is where it starts; y is the surface it hops on. hop is how high it jumps (px); speed is how fast it
    moves while in the air; rest is the seconds it waits on the ground between hops. Run under it while it's
    up, or flip over it while it rests. offset (seconds) delays its first hop so two can take turns.
    """

    W, H = 32, 34

    def __init__(self, x, y, left, right, hop=90, speed=90.0, rest=0.5, offset=0.0):
        self.x, self.y_surface = float(x), int(y)
        self.left, self.right = int(left), int(right)
        self.hop_v = math.sqrt(2 * C.GRAVITY * hop)
        self.speed, self.rest = float(speed), float(rest)
        self.lift = 0.0            # how far above the surface it is
        self.vy = 0.0
        self.wait = self.rest + offset
        self.dir = 1
        self.rect = pygame.Rect(int(self.x), self.y_surface - self.H, self.W, self.H)

    def update(self, dt, room, player):
        if self.lift <= 0 and self.wait > 0:
            self.wait -= dt
            if self.wait <= 0:
                self.vy = self.hop_v
        else:
            self.vy -= C.GRAVITY * dt
            self.lift += self.vy * dt
            self.x += self.dir * self.speed * dt
            if self.lift <= 0:
                self.lift, self.vy, self.wait = 0.0, 0.0, self.rest
        if self.x < self.left:
            self.x, self.dir = float(self.left), 1
        elif self.x + self.W > self.right:
            self.x, self.dir = float(self.right - self.W), -1
        self.rect = pygame.Rect(int(self.x), int(self.y_surface - self.H - self.lift), self.W, self.H)

    def draw(self, surf):
        r = self.rect
        squash = 4 if self.lift <= 0 and self.wait < 0.15 else 0       # crouch just before a hop
        body = pygame.Rect(r.left, r.top + squash, r.width, r.height - 8 - squash)
        legs = 8 + (6 if self.lift > 0 else 0)
        for lx in (r.left + 8, r.right - 8):
            pygame.draw.line(surf, C.INK, (lx, body.bottom), (lx - self.dir * 3, body.bottom + legs // 2), 2)
            pygame.draw.line(surf, C.INK, (lx - self.dir * 3, body.bottom + legs // 2), (lx, body.bottom + legs), 2)
        pygame.draw.rect(surf, (96, 150, 120), body, border_radius=9)
        pygame.draw.rect(surf, C.INK, body, 2, border_radius=9)
        _robot_eye(surf, (body.centerx + self.dir * 6, body.top + 9), False)


class SkyBot:
    """A flying bot that cruises back and forth between left and right at height y, bobbing in a wave.

    wave is how far it bobs up and down (px); period is the seconds per bob. offset (seconds) shifts its bob
    so two fly out of step. Flown at y <= C.FLOOR_Y - 60 - wave, you can walk under it; flown lower, run at it
    and jump it.
    """

    W, H = 36, 22

    def __init__(self, x, y, left, right, speed=90.0, wave=30, period=2.0, offset=0.0):
        self.x, self.y = float(x), int(y)
        self.left, self.right = int(left), int(right)
        self.speed, self.wave, self.period = float(speed), float(wave), max(0.2, float(period))
        self.t = float(offset)
        self.dir = 1
        self.rect = pygame.Rect(int(self.x), self.y - self.H // 2, self.W, self.H)

    def update(self, dt, room, player):
        self.t += dt
        self.x += self.dir * self.speed * dt
        if self.x < self.left:
            self.x, self.dir = float(self.left), 1
        elif self.x + self.W > self.right:
            self.x, self.dir = float(self.right - self.W), -1
        bob = self.wave * math.sin(self.t * 2 * math.pi / self.period)
        self.rect = pygame.Rect(int(self.x), int(self.y + bob - self.H / 2), self.W, self.H)

    def draw(self, surf):
        r = self.rect
        flap = int(5 * math.sin(self.t * 30))
        for wx in (r.left + 4, r.right - 4):
            pygame.draw.line(surf, (190, 196, 210), (wx, r.top + 4), (wx - self.dir * 8, r.top - 4 + flap), 3)
        pygame.draw.ellipse(surf, (88, 84, 120), r)
        pygame.draw.ellipse(surf, C.INK, r, 2)
        _robot_eye(surf, (r.centerx + self.dir * 9, r.centery), False)


class PopUpBot:
    """A bot that hides in a floor hatch and pops up on a timer. The hatch blinks before it rises.

    x is the hatch's left edge, y the surface it's set into. It stays up for up_time seconds and down for
    down_time, warning for the last `warn` of those. offset (seconds) shifts it in its cycle. It stands
    still, so keep it out of the doorways (the check will tell you).
    """

    W, H = 34, 44
    RISE = 0.18                 # seconds to come up or go down

    def __init__(self, x, y=C.FLOOR_Y, up_time=1.2, down_time=2.0, warn=0.5, offset=0.0):
        self.x, self.y_surface = int(x), int(y)
        self.up_time, self.down_time = float(up_time), float(down_time)
        self.warn = min(float(warn), self.down_time)
        self.t = float(offset)
        self.height = 0
        self.warning = False
        self.rect = pygame.Rect(0, 0, 0, 0)

    def update(self, dt, room, player):
        cycle = self.down_time + self.up_time
        self.t = (self.t + dt) % cycle
        up_t = self.t - self.down_time                    # < 0 while down
        self.warning = up_t < 0 and -up_t <= self.warn
        if up_t < 0:
            frac = 0.0
        else:
            frac = min(1.0, up_t / self.RISE, (self.up_time - up_t) / self.RISE)
        self.height = int(self.H * max(0.0, frac))
        if self.height > 6:
            self.rect = pygame.Rect(self.x, self.y_surface - self.height, self.W, self.height)
        else:
            self.rect = pygame.Rect(0, 0, 0, 0)

    def draw(self, surf):
        hatch = pygame.Rect(self.x - 4, self.y_surface - 4, self.W + 8, 4)
        blink = self.warning and int(self.t * 12) % 2
        pygame.draw.rect(surf, C.DANGER if blink else (60, 62, 72), hatch)
        if self.height <= 0:
            return
        body = pygame.Rect(self.x, self.y_surface - self.height, self.W, self.height)
        pygame.draw.rect(surf, (110, 74, 70), body, border_top_left_radius=12, border_top_right_radius=12)
        pygame.draw.rect(surf, C.INK, body, 2, border_top_left_radius=12, border_top_right_radius=12)
        if self.height > 16:
            _robot_eye(surf, (body.centerx, body.top + 12), True)


class _Puck:
    """A SentryBot's shot. Only one is out at a time, so it is its own hazard object."""

    W, H = 14, 8

    def __init__(self, facing):
        self.dir = facing           # it moves, so the doorway check leaves it alone
        self.live = False
        self.x = self.y = 0.0
        self.end = 0.0
        self.speed = 0.0
        self.rect = pygame.Rect(0, 0, 0, 0)

    def fire(self, x, y, speed, end):
        self.x, self.y, self.speed, self.end, self.live = float(x), float(y), float(speed), float(end), True

    def update(self, dt, room, player):
        if not self.live:
            self.rect = pygame.Rect(0, 0, 0, 0)
            return
        self.x += self.dir * self.speed * dt
        if (self.dir > 0 and self.x > self.end) or (self.dir < 0 and self.x + self.W < self.end):
            self.live = False
            self.rect = pygame.Rect(0, 0, 0, 0)
            return
        self.rect = pygame.Rect(int(self.x), int(self.y - self.H / 2), self.W, self.H)

    def draw(self, surf):
        if self.live:
            pygame.draw.ellipse(surf, (255, 180, 80), self.rect)
            pygame.draw.ellipse(surf, C.INK, self.rect, 1)


class SentryBot:
    """A bot bolted to a surface that fires a puck straight ahead, at shin height.

    x, y place it on a surface; facing is 1 (right) or -1 (left) and never changes. With sees=True (the
    default) it only fires when you're on its level and in front of it within range, with a red eye and a
    short charge first; with sees=False it fires every reload seconds anyway. Jump the puck, or come at it
    from behind. It stands still, so keep it out of the doorways (the check will tell you).
    """

    W, H = 30, 36
    CHARGE = 0.45

    def __init__(self, x, y, facing=1, range=520, reload=1.6, shot_speed=260.0, sees=True, offset=0.0):
        self.facing = 1 if facing >= 0 else -1
        self.box = pygame.Rect(int(x), int(y) - self.H, self.W, self.H)
        self.y_surface = int(y)
        self.range, self.reload, self.shot_speed, self.sees = int(range), float(reload), float(shot_speed), sees
        self.cool = float(offset)
        self.charge = 0.0
        self.alert = False
        self.puck = _Puck(self.facing)
        self.joined = False
        self.rect = self.box

    def update(self, dt, room, player):
        if not self.joined:                      # the puck goes in the room's hazards, once
            self.joined = True
            if room is not None and self.puck not in room.hazards:
                room.hazards.append(self.puck)
        self.cool = max(0.0, self.cool - dt)
        if self.sees:
            level = abs(player.rect.bottom - self.y_surface) < 6
            ahead = (player.rect.centerx - self.box.centerx) * self.facing > 0
            near = abs(player.rect.centerx - self.box.centerx) < self.range
            self.alert = level and ahead and near
        else:
            self.alert = True
        if self.alert and self.cool <= 0 and not self.puck.live:
            self.charge += dt
            if self.charge >= self.CHARGE:
                muzzle = self.box.right if self.facing > 0 else self.box.left - _Puck.W
                end = self.box.centerx + self.facing * self.range
                self.puck.fire(muzzle, self.y_surface - 14, self.shot_speed, end)
                self.cool, self.charge = self.reload, 0.0
        else:
            self.charge = 0.0

    def draw(self, surf):
        r = self.box
        pygame.draw.rect(surf, (60, 62, 72), (r.left - 4, r.bottom - 6, r.width + 8, 6))
        pygame.draw.rect(surf, (168, 140, 80), (r.left, r.top, r.width, r.height - 6), border_radius=6)
        pygame.draw.rect(surf, C.INK, (r.left, r.top, r.width, r.height - 6), 2, border_radius=6)
        barrel_x = r.right if self.facing > 0 else r.left - 12
        pygame.draw.rect(surf, (50, 52, 60), (barrel_x, self.y_surface - 19, 12, 10), border_radius=2)
        pygame.draw.rect(surf, C.INK, (barrel_x, self.y_surface - 19, 12, 10), 1, border_radius=2)
        _robot_eye(surf, (r.centerx + self.facing * 6, r.top + 10), self.alert and self.sees)
        if self.charge > 0:
            glow = int(4 + 6 * self.charge / self.CHARGE)
            pygame.draw.circle(surf, (255, 180, 80), (barrel_x + (12 if self.facing > 0 else 0), self.y_surface - 14), glow, 2)
