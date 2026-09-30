"""Geno's articles: the projectile data his items load (the fighter data's article list, registered at OnLoad). Each
starts as a copy of a donor fighter's article (its model, common attributes and state scripts) and is overridden here:
`ext` sets special-attribute floats by byte offset, `scripts` replaces state scripts (hex, item command set). The item
code that drives each one lives in the decomp (src/melee/it/kinds/itgeno.c); the order here is the kinds' order.
"""
import os, sys

from fcmd import ItemScript

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'fx'))
import beam_model, blast_model, finger_model, flash_model, whirl_model  # noqa: E402

# geno-fx: the Beam's own model (projects/geno/fx/beam_model.py) replaces the donor laser's mesh; GENO_BEAM_MODEL=0 builds
# the donor's (the "before"). Its trail stretches to BEAM_STRETCH times its 12 units (the laser's ext +4; Falco's is 3)
BEAM_MODEL = os.environ.get('GENO_BEAM_MODEL', '1') != '0'
BEAM_STRETCH = 1.6
BEAM_R = (2.2, 2.9, 3.8) if BEAM_MODEL else (2.0, 2.6, 3.4)   # the nose radius at one, two, three stars (+12% with the model)


def beam_script(dmg, size, kbg, bkb, angle=361):
    """A Beam level: a bolt of spheres along its trail (the laser flies along its local +Z).
    The donor laser's model: three spheres on the root, as Falco's. The Beam's own model (geno-fx, Michael: a slightly
    thicker and longer hitbox is fine if the glow pads it, for the SNES beam's look): four spheres on the trail joint
    (bone 1), which the item code stretches as the beam leaves the barrel and scales by the level, so the spheres spread
    with the drawn beam and none sits behind the barrel at the spawn. `size` is the level's nose radius."""
    s = ItemScript()
    if BEAM_MODEL:
        lv = size / BEAM_R[-1]                      # the item code's thickness factor for this level (itgeno.c)
        for i in range(4):
            z = -i * 1.3 * BEAM_R[-1] / BEAM_STRETCH    # full level: 0, -4.9, -9.9, -14.8 once stretched (x lv lower)
            s.hitbox(i, dmg, size * (1.0 - 0.08 * i), (0, 0, z), angle=angle, kbg=kbg, bkb=bkb, bone=1)
    else:
        for i, z in enumerate((0.0, -size * 1.4, -size * 2.8)):
            s.hitbox(i, dmg, size * (1.0 - 0.15 * i), (0, 0, z), angle=angle, kbg=kbg, bkb=bkb)
    s.end()
    return s.bytes().hex()


# ---- Geno Whirl (DESIGN v1.2 §5): the outbound hit, the shield grind, the hover, the recall; each opens its hitbox in a
# new hit group, so each can hit a given opponent once per throw (§8 rule 3)
WHIRL_EXT = {0x00: 1.35,   # starting speed (units a frame); v1.3 x0.84 with his run (1.9 -> 1.6), so he still runs behind it
             0x04: 0.93,   # speed at the end of the travel
             0x08: 47.0,   # travel frames (~54 units, as before), then the hover
             0x0C: 45.0,   # hover frames
             0x10: 4.0,    # recall speed
             0x14: 43.0,   # grind frames (hits at 15, 28, 41), then the hover
             0x18: 5.0,    # catch radius: recalled into his hands
             0x1C: 0.349,  # the stick bends the throw up to 20 degrees (radians)
             0x20: 4.0,    # the hover's damage: the travel's hitbox stays live into the hover (its victims can't be
             0x24: 60.0}   # hit again) and drops to these numbers (damage, angle)
WHIRL_R = 3.6              # the disc's hit radius


def whirl_travel():
    s = ItemScript()
    s.hitbox(0, 7, WHIRL_R, angle=40, kbg=60, bkb=25, group=0)
    s.end()
    return s.bytes().hex()


def whirl_grind():
    """Three 3% hits on the shield, 13 frames apart: each leaves a 6-frame gap after hitlag and shieldstun (§8 rule 4)."""
    s = ItemScript()
    for g in (1, 2, 3):
        s.wait(11)
        s.hitbox(0, 3, WHIRL_R, angle=361, kbg=20, bkb=10, group=g)
        s.wait(2)
        s.clear()
    s.end()
    return s.bytes().hex()


def whirl_hover():
    # after the grind only (a fresh group); after the outbound hit or the end of the travel, the item code keeps the
    # travel's hitbox live and lowers it to the hover's numbers, so whoever the outbound hit caught can't be hit again
    s = ItemScript()
    s.hitbox(0, 4, WHIRL_R, angle=60, kbg=60, bkb=20, group=4)
    s.end()
    return s.bytes().hex()


def whirl_recall():
    s = ItemScript()
    s.hitbox(0, 6, WHIRL_R, angle=80, kbg=70, bkb=30, group=5)
    s.end()
    return s.bytes().hex()


# ---- Geno Blast (down B, DESIGN v1.2 §5): a mark on the floor, then ~32 frames later a column sweeps down through it. It
# meteors airborne targets (cancellable) and pops grounded ones up at ~83 degrees, 9% each; one hit group for the
# column, so a target is hit once. Aerial-only and grounded-only spheres are word 4's last two bits (hit grounded, hit
# aerial): Falco's laser's 0x047 hits both
BLAST_LIFT = 40.0          # the stand-in model's hanging length, from its data: Pikachu's thunder is one billboard quad,
                           # x -10..10, y -40..0 under its root (no joint animation). The item rides this high, so the tell
                           # stands on the floor and the bolt's lower end leads the strike; the hitboxes go this far down
BLAST_EXT = {0x00: 32.0,   # mark frames (the tell)
             0x04: 8.0,    # strike frames: the column sweeps down from `drop` to the floor
             0x08: 50.0,   # drop height
             0x0C: BLAST_LIFT}
BLAST_R = 6.0


def blast_mark():
    s = ItemScript(); s.end()
    return s.bytes().hex()


def blast_strike():
    s = ItemScript()
    for i, y in enumerate((BLAST_R - BLAST_LIFT, BLAST_R * 3 - BLAST_LIFT)):     # the lowest 24 of the bolt, as before
        s.hitbox(i, 9, BLAST_R, (0, y, 0), angle=270, kbg=80, bkb=20, tail=0x045)      # airborne: meteor
        s.hitbox(2 + i, 9, BLAST_R, (0, y, 0), angle=83, kbg=70, bkb=40, tail=0x046)   # grounded: popped up
    s.end()
    return s.bytes().hex()


# ---- Geno Flash (down B's third star, DESIGN §5). Michael, 2026-09-29: smaller, and a sweetspot then a sourspot in time.
# The sun appears as a burst the size of PK Flash's full-charge explosion (its radius 2150/256 x 1.7 = 14.3, measured
# 14.2), the move's kill hit, and grows over 40 frames to a 28 radius (was 38), lingering 30 as a weaker hit. One hitbox
# the whole time, so one hit per target: whoever the burst hit, the late sun can't hit again (itgeno.c itGe_Flash_Anim)
# Measured on Fox at centre stage (kill_lab, clean KO at no DI / optimal DI; DESIGN changelog 2026-09-29): the burst 75 / 75
# (Michael: 18% and a little less knockback than PK Flash's 65 / 65, its charge and control being better; tried at 18%:
# 100/55 70, 95/55 75, 100/50 75, 95/50 80), the late sun 150 / 190. The cast: a full PK Flash 65 / 65, Falcon Punch
# 50 / 70, Warlock Punch 35 / 50, a full Charge Shot 70 / 100; the old sun (18%, 100/55, radius 8 to 38) 70 / 70
FLASH_BURST = dict(dmg=18, angle=45, kbg=95, bkb=55)      # the burst, the kill hit
FLASH_LATE = dict(dmg=12, angle=45, kbg=85, bkb=45)        # the lingering sun
FLASH_EXT = {0x00: 40.0,   # grow frames
             0x04: 30.0,   # linger frames
             0x08: 14.3,   # starting radius: PK Flash's at full charge
             0x0C: 28.0,   # full radius
             0x10: 30.0,   # the sun's centre: this far ahead of him
             0x14: 14.0,   # and this high
             0x18: 8.0,    # the burst: its frames (the sun's first 8, radius 14.3 to 16.7)
             0x1C: float(FLASH_LATE['dmg']), 0x20: float(FLASH_LATE['angle']),
             0x24: float(FLASH_LATE['kbg']), 0x28: float(FLASH_LATE['bkb'])}


def flash_sun():
    s = ItemScript()
    # Melee's knockback: ((p/10 + p*d/20) * 200/(w+100) * 1.4 + 18) * kbg/100 + bkb, p the percent after the hit. Fox
    # (weight 75) dies from centre stage at 45 degrees at ~210 (kill_lab: the formula at the measured kill percents). The
    # burst: 1.52q + 99.5 at Fox q% (measured: 75%); the late sun (FLASH_LATE, set by the item code at the burst's end):
    # 0.95q + 72 (150%), weaker than the burst at every percent
    b = FLASH_BURST
    s.hitbox(0, b['dmg'], FLASH_EXT[0x08], angle=b['angle'], kbg=b['kbg'], bkb=b['bkb'], element=0)
    s.end()
    return s.bytes().hex()


# ---- the throws' projectiles (DESIGN §6f): real projectiles, as Fox's and Falco's throw lasers are (their laser article's
# state 1). The decomp's ftGe_Throw_Anim (ftgeno_throw.c) spawns them on the throw script's flags. No knockback (kbg and bkb
# 0, as Fox's): a hit adds its damage and hitlag without changing the opponent's launch or hold, so a throw's knockback is
# the throw's own. The up throw's stars fly after the release, so good DI slips some; the down throw's shots meet an
# opponent pinned to the floor.
THROW_STAR = dict(dmg=1, r=6.0)        # the up throw's Star Gun stars (the Beam article's state 3): Fox's throw lasers'
                                       # size (6.6), so full DI slips the later stars and not the first (lab: 2.6 missed all three)
THROW_SHOT = dict(dmg=2, r=2.6)        # the down throw's Finger Shots (the Finger Shot article's state 1): 1% each, since
                                       # a held opponent takes half (ftcoll.c: p_ftCommonData->x128), as Fox's are 2 for 1%


def throw_shot(dmg, r):
    """A throw projectile: two spheres along its trail, no knockback, Fox's throw-laser flags (rehit 16)."""
    s = ItemScript()
    for i, z in enumerate((0.0, -r)):
        s.hitbox(i, dmg, r, (0, 0, z), angle=361, kbg=0, bkb=0, flags=0x00FDC000, rehit=16)
    s.end()
    return s.bytes().hex()


ARTICLES = [
    # Finger Shot (neutral B tap): Falco's laser (3%, hitstun). Lifetime 19 frames at 4 units a frame: ~75 units
    dict(name='finger', frm='PlFc.dat', index=0, ext={0x00: 19.0},
         scripts=[None, throw_shot(**THROW_SHOT)],           # state 1: the down throw's shots
         # geno-fx: our own model, a volley of golden slugs (projects/geno/fx/finger_model.py; GENO_FINGER_MODEL=0: the donor's)
         **({'model': finger_model.spec(os.path.join(os.environ.get('MELEE_WORK', os.path.expanduser('~/games/melee/work')), 'fx', 'finger'))}
            if os.environ.get('GENO_FINGER_MODEL', '1') != '0' else {})),
    # Geno Beam (neutral B hold): a faster, longer bolt at one, two or three stars (states 0-2). Lifetime 26 at 6 units a
    # frame: ~155 units, near full screen. Levels against Samus's charge shot (3-25%, kbg 42-72, bkb 14-50); the full
    # Beam aims to kill Fox from centre stage at ~115-125% (to be measured)
    dict(name='beam', frm='PlFc.dat', index=0, ext={0x00: 26.0, **({0x04: BEAM_STRETCH} if BEAM_MODEL else {})},
         scripts=[beam_script(6, BEAM_R[0], 48, 18), beam_script(11, BEAM_R[1], 58, 28), beam_script(17, BEAM_R[2], 82, 48),   # full: ~233 KB on Fox at 120%
                  throw_shot(**THROW_STAR)],                     # state 3: the up throw's stars
         **({'model': beam_model.spec(os.path.join(os.environ.get('MELEE_WORK', os.path.expanduser('~/games/melee/work')), 'fx', 'beam'))}
            if BEAM_MODEL else {})),
    # Geno Whirl (side B): its own item code (itgeno.c). Samus's charge-shot ball stands in for the disc (donor state 4,
    # a mid-sized ball, for all four states). ext is itGe_WhirlAttr: speeds, frames and the recall/catch numbers
    dict(name='whirl', frm='PlSs.dat', index=1, state_from=[4, 4, 4, 4], ext_size=0x28, ext=WHIRL_EXT, hurt_r=WHIRL_R,
         scripts=[whirl_travel(), whirl_grind(), whirl_hover(), whirl_recall()],
         # geno-fx: our own disc (projects/geno/fx/whirl_model.py; GENO_WHIRL_MODEL=0: the donor's ball)
         **({'model': whirl_model.spec(os.path.join(os.environ.get('MELEE_WORK', os.path.expanduser('~/games/melee/work')), 'fx', 'whirl'))}
            if os.environ.get('GENO_WHIRL_MODEL', '1') != '0' else {})),
    # Geno Blast: Pikachu's thunder bolt stands in for the column; its own item code (itgeno.c)
    dict(name='blast', frm='PlPk.dat', index=0, state_from=[0, 0], ext_size=0x10, ext=BLAST_EXT,
         scripts=[blast_mark(), blast_strike()],
         # geno-fx: our own mark and columns (projects/geno/fx/blast_model.py; GENO_BLAST_MODEL=0: the donor's bolt)
         **({'model': blast_model.spec(os.path.join(os.environ.get('MELEE_WORK', os.path.expanduser('~/games/melee/work')), 'fx', 'blast'))}
            if os.environ.get('GENO_BLAST_MODEL', '1') != '0' else {})),
    # Geno Flash: Ness's PK Flash explosion stands in for the sun; its own item code (itgeno.c)
    dict(name='flash', frm='PlNs.dat', index=8, ext_size=0x2C, ext=FLASH_EXT, scripts=[flash_sun()],
         # geno-fx: SMRPG's star with a face rounding into the sun (projects/geno/fx/flash_model.py; GENO_FLASH_MODEL=0: the
         # donor's PK Flash)
         **({'model': flash_model.spec(os.path.join(os.environ.get('MELEE_WORK', os.path.expanduser('~/games/melee/work')), 'fx', 'flash'))}
            if os.environ.get('GENO_FLASH_MODEL', '1') != '0' else {})),
]
