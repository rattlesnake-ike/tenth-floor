"""Sound: the game's sound effects, made from waves in code (no sound files). Its owner is in OWNERS.md.

    from engine import sound
    sound.play("ding")
    sound.ambient(True)        # the building's hum, looping quietly

Effects: jump, tick, found, nothing, caught, ding, locked, win, lose, zap, alarm, lunge, click.
Each effect is made in a few slightly different takes, and play() picks one, so repeats don't sound copied.
They're made in the background when the game starts; until a sound is ready, play() skips it. If the computer
has no sound (or the check runs with none), every call quietly does nothing.
"""
import math
import random
import threading
from array import array

import pygame

RATE = 22050
TAKES = 3
_sounds = {}             # name -> [Sound, ...]
_ready = None            # None = not started, False = no sound on this machine, True = mixer up
_hum = None
_want_hum = False


# --- making waves --------------------------------------------------------------------------------------------
def _n(secs):
    return int(RATE * secs)


def _env(i, n, attack=0.005, decay=None):
    """A fast attack, then an exponential fade over the whole length (or `decay` seconds)."""
    t = i / RATE
    a = min(1.0, t / attack) if attack > 0 else 1.0
    d = decay if decay else max(0.02, n / RATE)
    return a * math.exp(-4.0 * t / d)


def _bell(freq, secs, vol=0.25, decay=None):
    """A struck bell: a few inharmonic partials, the high ones dying first."""
    n, out = _n(secs), []
    parts = ((1.0, 1.0, 1.0), (2.76, 0.45, 0.55), (5.4, 0.25, 0.3), (8.93, 0.12, 0.2))
    for i in range(n):
        t = i / RATE
        v = 0.0
        for mult, amp, life in parts:
            v += amp * math.sin(2 * math.pi * freq * mult * t) * math.exp(-t / (secs * life))
        out.append(v * vol * min(1.0, t / 0.002))
    return out


def _tone(f0, f1, secs, vol=0.3, kind="tri", decay=None, vibrato=0.0):
    """A tone gliding from f0 to f1 Hz. kind: sine, tri, square, saw."""
    n, out, ph = _n(secs), [], 0.0
    for i in range(n):
        f = f0 + (f1 - f0) * i / n
        if vibrato:
            f *= 1 + vibrato * math.sin(2 * math.pi * 5.5 * i / RATE)
        ph = (ph + f / RATE) % 1.0
        if kind == "sine":
            v = math.sin(2 * math.pi * ph)
        elif kind == "square":
            v = 0.7 if ph < 0.5 else -0.7
        elif kind == "saw":
            v = 2 * ph - 1
        else:
            v = 4 * abs(ph - 0.5) - 1
        out.append(v * vol * _env(i, n, decay=decay))
    return out


def _noise(secs, vol=0.3, lo=0.0, hi=1.0, sweep=None, decay=None, crackle=0.0):
    """Filtered noise. lo/hi are one-pole filter amounts (0..1); sweep=(start, end) moves the lowpass."""
    n, out, lp, lp2 = _n(secs), [], 0.0, 0.0
    for i in range(n):
        x = random.uniform(-1, 1)
        if crackle and random.random() > crackle:
            x *= 0.08                                       # mostly quiet, with sharp pops: electricity
        a = hi if not sweep else sweep[0] + (sweep[1] - sweep[0]) * i / n
        lp += a * (x - lp)
        lp2 += lo * (lp - lp2)
        out.append((lp - lp2) * vol * _env(i, n, decay=decay))
    return out


def _mix(*layers):
    n = max(len(l) for l in layers)
    return [sum(l[i] for l in layers if i < len(l)) for i in range(n)]


def _seq(*parts, gap=0.0):
    out = []
    for p in parts:
        out += p + [0.0] * _n(gap)
    return out


def _recipes(k):
    """(name, how to make it) for every effect at pitch factor k, made one at a time."""
    return [(name, (lambda name=name: _effects(k, only=name)[name])) for name in NAMES]


NAMES = ("jump", "tick", "found", "nothing", "caught", "ding", "locked", "win", "lose", "zap", "alarm", "lunge", "click")


def _effects(k, only=None):
    """Every effect, at pitch factor k (the takes differ by a few percent). `only` makes just that one."""
    if only:
        return {only: _EFFECTS[only](k)}
    return {name: _EFFECTS[name](k) for name in NAMES}


_EFFECTS = {   # name -> how to make it at pitch factor k
        "jump": lambda k: _mix(_tone(240 * k, 560 * k, 0.16, 0.22, "tri", decay=0.12), _noise(0.06, 0.06, hi=0.5)),
        "tick": lambda k: _noise(0.025, 0.2, lo=0.3, hi=0.9, decay=0.01),
        "found": lambda k: _seq(_bell(1319 * k, 0.16, 0.18), _bell(1661 * k, 0.16, 0.18), _bell(1976 * k, 0.16, 0.18),
                      _bell(2637 * k, 0.9, 0.2)),
        "nothing": lambda k: _seq(_mix(_tone(170 * k, 90 * k, 0.12, 0.35, "sine", decay=0.08), _noise(0.02, 0.2, hi=0.6)),
                        _mix(_tone(130 * k, 70 * k, 0.16, 0.35, "sine", decay=0.1), _noise(0.02, 0.15, hi=0.5))),
        "caught": lambda k: _mix(_seq(*[_tone(880 * k, 620 * k, 0.16, 0.16, "square") for _ in range(3)]),
                       _noise(0.5, 0.18, hi=0.35, decay=0.5)),
        "ding": lambda k: _seq(_bell(784 * k, 0.55, 0.22), _bell(659 * k, 1.2, 0.22)),
        "locked": lambda k: _seq(_tone(196 * k, 190 * k, 0.16, 0.22, "square", vibrato=0.04), _tone(147 * k, 140 * k, 0.32, 0.22, "square", vibrato=0.04),
                       gap=0.05),
        "win": lambda k: _mix(_seq(_bell(1047 * k, 0.18, 0.16), _bell(1319 * k, 0.18, 0.16), _bell(1568 * k, 0.18, 0.16),
                         _bell(2093 * k, 1.4, 0.2)), _tone(262 * k, 262 * k, 2.0, 0.08, "tri", decay=2.0)),
        "lose": lambda k: _seq(_tone(392 * k, 380 * k, 0.4, 0.2, "sine", vibrato=0.02), _tone(330 * k, 320 * k, 0.4, 0.2, "sine", vibrato=0.02),
                     _tone(262 * k, 230 * k, 1.1, 0.2, "sine", vibrato=0.03)),
        "zap": lambda k: _mix(_noise(0.3, 0.5, lo=0.2, hi=0.9, crackle=0.7, decay=0.3), _tone(120 * k, 118 * k, 0.3, 0.15, "saw", decay=0.3)),
        "alarm": lambda k: _tone(1100 * k, 700 * k, 0.22, 0.14, "sine", decay=0.25, vibrato=0.12),
        "lunge": lambda k: _noise(0.3, 0.45, sweep=(0.02, 0.6), decay=0.35),
        "click": lambda k: _seq(_noise(0.012, 0.25, lo=0.4, hi=0.95, decay=0.006), _noise(0.012, 0.18, lo=0.4, hi=0.95, decay=0.006), gap=0.03),
}


def _hum_wave():
    """Two seconds of building at night: mains hum and a buzzing fluorescent tube. Whole cycles, so it loops clean."""
    n, out, lp = _n(2.0), [], 0.0
    for i in range(n):
        t = i / RATE
        lp += 0.02 * (random.uniform(-1, 1) - lp)
        buzz = (2 * ((120 * t) % 1.0) - 1) * (0.5 + 0.5 * math.sin(2 * math.pi * 0.5 * t))
        out.append(0.05 * math.sin(2 * math.pi * 60 * t) + 0.025 * math.sin(2 * math.pi * 120 * t) + 0.012 * buzz + 0.04 * lp)
    return out


def _to_sound(samples):
    freq, _size, channels = pygame.mixer.get_init()
    if freq != RATE:
        step = RATE / freq
        samples = [samples[int(i * step)] for i in range(int(len(samples) / step))]
    pcm = array("h", (int(max(-1.0, min(1.0, s)) * 32767) for s in samples for _ in range(channels)))
    return pygame.mixer.Sound(buffer=pcm.tobytes())


def _jobs():
    """The sounds to make, one job at a time: the hum, then every effect, take by take."""
    global _hum
    random.seed(11)
    _hum = _to_sound(_hum_wave())
    if _want_hum:
        _hum.play(loops=-1)
    yield
    for take in range(TAKES):
        k = 1.0 + (take - 1) * 0.035
        for name, make in _recipes(k):
            _sounds.setdefault(name, []).append(_to_sound(make()))
            yield


_queue = None            # where there are no threads (a web browser): the jobs, run by pump()


def _make_all():
    try:
        for _ in _jobs():
            pass
    except Exception:
        pass


def pump():
    """Call once a frame. Where sounds can't be made in the background (a web browser), this makes the next
    one. Elsewhere it does nothing."""
    global _queue
    if _queue is not None:
        try:
            next(_queue)
        except Exception:
            _queue = None


def _init():
    global _ready
    if _ready is not None:
        return _ready
    try:
        if not pygame.mixer.get_init():
            pygame.mixer.init(RATE, -16, 1, 512)
    except Exception:                                          # no audio device: play nothing, never crash
        _ready = False
        return _ready
    _ready = True
    try:
        threading.Thread(target=_make_all, daemon=True).start()
    except Exception:                                          # no threads (a web browser): pump() makes them
        global _queue
        _queue = _jobs()
    return _ready


def play(name):
    """Play one effect by name (one of its takes, at random). Unknown names, effects still being made, and
    machines without sound do nothing."""
    if _init() and _sounds.get(name):
        random.choice(_sounds[name]).play()


def ambient(on=True):
    """The building's hum: on loops it quietly under everything, off stops it."""
    global _want_hum
    _want_hum = on
    if not _init() or _hum is None:
        return
    _hum.stop()
    if on:
        _hum.set_volume(0.6)
        _hum.play(loops=-1)
