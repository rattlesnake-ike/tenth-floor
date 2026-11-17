# Tenth Floor

**Play it in your browser: https://rattlesnake-ike.github.io/tenth-floor/** (nothing to install; click once to
start). Arrows or WASD to move, SPACE to jump, hold UP to search, F for the flashlight. It updates on its own
whenever a floor is merged.

The class game. You're in the building after hours. Start at the security desk, ride the elevators,
search every floor for a digit of the door code, stay out of security's way, and get into the 10th
floor, MFA Computer Arts, before the clock runs out. The building is SVA on West 21st Street; name
your floor after a real place in it.

**Everyone builds one floor.** The engine (player, elevators, clock, searching, the lobby) is shared and
already works. Your floor is one file, `floors/<your_name>.py`, with 2 to 5 rooms, and it shows up in the
building on its own. Ready-made furniture, hazards, moving platforms and decor are in the **kit**: see
**KIT.md** for a picture of every part.

## How the building works

Every floor runs between two elevators. You come off the **West** elevator into your floor's first
room, walk through its rooms, and get on the **East** elevator from the last one.

- The West elevator stops at the lobby through floor 9.
- The East elevator stops at floor 2 through the top, including 10.

So nobody gets to 10 without crossing floors. Floor 10's door takes a code; every floor hides one digit.

## Set up once

Mac:
```
git clone https://github.com/<you>/tenth-floor.git
cd tenth-floor
python3 -m venv .venv
.venv/bin/python -m pip install pygame-ce
.venv/bin/python main.py
```

Windows (PowerShell):
```
git clone https://github.com/<you>/tenth-floor.git
cd tenth-floor
python -m venv .venv
.venv\Scripts\python -m pip install pygame-ce
.venv\Scripts\python main.py
```

Plain `pygame` works too. The check runs your floor on both.

## Make your floor

How we work together (claiming pieces, one piece per pull request, reviewing a classmate's floor, syncing)
is in **CONTRIBUTING.md**. Every piece of the game has an owner: **OWNERS.md**. The rules are in
**RULES.md**, and the decisions behind them in **DECISIONS.md**.

0. Claim your floor (and anything else you want to own): open a **Claim a piece** issue.
1. Fork this repo on GitHub (the Fork button), then clone **your fork** as above.
2. Copy an example to `floors/<your_name>.py` (lowercase, no spaces: `floors/sam_k.py`):
   `floors/example_floor.py` (two rooms, the basics) or `floors/example_kit_floor.py` (three rooms, built
   from the kit). Set `NAME` (your floor's name on the elevator panel) and `AUTHOR` at the top.
3. Start your agent in the `tenth-floor` folder and tell it what the floor is. For example:

   > Read AGENTS.md, engine/room.py and KIT.md. Turn floors/sam_k.py into the 3D printing floor, three
   > rooms: the print lab with Printer3D parts and a moving platform, the filament storeroom with lockers
   > and a crusher, and a break room. Hide the code digit in one of the printers. Only change my file.
   > Run check.py --floor sam_k after each change and play it with main.py --floor sam_k.

4. Practice it: `python main.py --floor <your_name>`. You start on your floor with no clock, and
   you can retry forever.
5. Check it: `python check.py --floor <your_name>`. Fix everything it says.
6. Add one line to `CREDITS.md` under "Floors": `- <Floor name>: <Your Name>`.
7. Commit, push to your fork, and open a pull request to this repo. GitHub runs the check on it.
8. Ask a classmate to play it and review it (CONTRIBUTING.md, step 4). After anything is merged, click
   **Sync fork** on GitHub and `git pull`.

## What your floor needs

- 2 to 5 rooms, listed west to east in `ROOMS`, each with at least three pieces of furniture
- **Exactly one** piece of furniture on the whole floor with `holds_piece=True`: it hides your digit
- A way up to it: ledges a jump can reach (a jump rises about 100 px) or a lift
- Hazards: `PatrolBot`, `Zapper`, `Crusher`, `Drone`, `FloorLaser` from the kit, or one you make yourself
- Clear floor at both edges of every room: those are the doorways

The full contract is the docstring at the top of `engine/room.py`.

## Controls

Arrows or WASD to move, SPACE to jump. Run and jump to flip over a bot. Hold UP in front of furniture
to search it. On a yellow lift, UP and DOWN drive it. In an elevator, UP and DOWN ride, and you step
out toward the floor (RIGHT from the West elevator, LEFT from the East one).

## One piece per pull request

A floor pull request changes only your floor (and your CREDITS line). Everything else (the engine, the
kit, the screens, the check) belongs to its owner in OWNERS.md. If your floor needs something the engine
doesn't do, write it inside your floor file (see `SweepBeam` in `floors/example_floor.py`), ask that
piece's owner with an **Engine request** issue, or change it in its own pull request. The check refuses a
pull request that touches two pieces.
