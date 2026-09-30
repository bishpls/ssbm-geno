"""Melee fighter move scripts ("subactions"), assembled from Python.

Layouts come from the decompilation (src/melee/lb/types.h command unions, ftaction.c handlers and ftAction_803C0870's
sizes), which compiles to the original binary; HSDRaw's community table differs in places (the hitbox's first word, the
smash charge's size). Opcodes below 0x0A run in the interpreter (lbcommand.c); the rest dispatch through
ftAction_803C06E8[opcode - 0x0A].

Timing: `at(n)` waits until the animation reaches frame n, and whatever follows happens on frame n in the usual 1-based
frame data (a hitbox after `at(5)` is active from frame 5); `wait(k)` waits k more frames. Hitboxes address engine parts
(the per-kind parts table), not joints, so a script never depends on the skeleton's joint order.

    from fcmd import *
    s = Script(); s.at(3); s.hitbox(0, 'RArmJ', dmg=3, size=2.0, off=(2.4, 0, 0), angle=80, kbg=100, wdsk=20); s.wait(2)
    s.clear(); s.at(18); s.iasa(); data = s.bytes()
"""
import struct

PARTS = ['TopN', 'TransN', 'XRotN', 'YRotN', 'HipN', 'WaistN', 'LLegJA', 'LLegJ', 'LKneeJ', 'LFootJA', 'LFootJ',
         'RLegJA', 'RLegJ', 'RKneeJ', 'RFootJA', 'RFootJ', 'WaistB', 'BustN', 'LShoulderN', 'LShoulderJA', 'LShoulderJ',
         'LArmJ', 'LHandN', 'L1stNa', 'L1stNb', 'L2ndNa', 'L2ndNb', 'L3rdNa', 'L3rdNb', 'L4thNa', 'L4thNb', 'LHandNb',
         'LThumbNa', 'LThumbNb', 'NeckN', 'HeadN', 'RShoulderN', 'RShoulderJA', 'RShoulderJ', 'RArmJ', 'RHandN',
         'R1stNa', 'R1stNb', 'R2ndNa', 'R2ndNb', 'R3rdNa', 'R3rdNb', 'R4thNa', 'R4thNb', 'RHandNb', 'RThumbNa',
         'RThumbNb', 'ThrowN', 'TransN2']

# hit sounds (severity 0-2 small to large, kind): kinds seen in Melee's own scripts
PUNCH, KICK, FIRE = 1, 2, 8
# common swing sounds (the fighter common bank): small, medium, large
SWING_S, SWING_M, SWING_L = 0xA6, 0xA5, 0xA4


def bits(fields):
    """Pack (value, width) pairs MSB-first into 32-bit words (MWCC's big-endian bitfield order)."""
    out, acc, n = [], 0, 0
    for v, w in fields:
        acc = (acc << w) | (int(v) & ((1 << w) - 1))
        n += w
        if n == 32:
            out.append(acc); acc, n = 0, 0
        assert n < 32 or n == 0
    assert n == 0, 'fields must fill whole words'
    return b''.join(struct.pack('>I', x) for x in out)


def fx(v):
    """A position or size in the 1/256 fixed point the commands use."""
    return int(round(v * 256)) & 0xFFFF


class Script:
    def __init__(self):
        self.data = bytearray()
        self.frame = 0            # the frame the next command runs on, for checks

    def raw(self, b):
        self.data += b
        return self

    # ---- interpreter commands
    def at(self, frame):
        assert frame >= self.frame, f'at({frame}) after frame {self.frame}'
        self.frame = frame
        return self.raw(bits([(0x02, 6), (frame, 26)]))

    def wait(self, k):
        self.frame += k
        return self.raw(bits([(0x01, 6), (k, 26)]))

    def end(self):
        return self.raw(bits([(0x00, 6), (0, 26)]))

    # ---- fighter commands
    def hitbox(self, id, part, dmg, size, off=(0, 0, 0), angle=361, kbg=100, wdsk=0, bkb=0, element=0, shield=0,
               sfx=(0, PUNCH), group=0, grounded=1, aerial=1, clank=1, rebound=1, item_hit=1, ignore_scale=0, common=1,
               only_grabbed=0):
        """Open hitbox `id` (0-3) on an engine part. off is in the part's joint frame (+X runs down a limb).
        only_grabbed: hits only the fighter being held (every pummel in the cast but Samus's sets it)."""
        bone = PARTS.index(part) if isinstance(part, str) else part
        w0 = bits([(0x0B, 6), (id, 3), (group, 3), (only_grabbed, 1), (bone, 8), (common, 1), (dmg, 10)])
        w1 = bits([(fx(size), 16), (fx(off[0]), 16)])
        w2 = bits([(fx(off[1]), 16), (fx(off[2]), 16)])
        w3 = bits([(angle, 9), (kbg, 9), (wdsk, 9), (item_hit, 1), (0, 1), (ignore_scale, 1), (clank, 1), (rebound, 1)])
        w4 = bits([(bkb, 9), (element, 5), (shield, 8), (sfx[0], 3), (sfx[1], 5), (grounded, 1), (aerial, 1)])
        return self.raw(w0 + w1 + w2 + w3 + w4)

    def remove(self, id):
        return self.raw(bits([(0x0F, 6), (id, 26)]))

    def clear(self):
        return self.raw(bits([(0x10, 6), (0, 26)]))

    def sound(self, sfx, vol=0x7F, pan=0x40, behavior=1):
        """behavior 1 is how Melee's scripts play a swing; 0 plays it plainly."""
        return self.raw(bits([(0x11, 6), (behavior, 8), (0, 18)]) + struct.pack('>I', sfx) + bits([(0, 16), (vol, 8), (pan, 8)]))

    def var(self, idx, value):
        """cmd_vars[idx] = value. Aerials read var 0 as 'landing now costs the aerial's landing lag'."""
        return self.raw(bits([(0x13, 6), (idx, 2), (value, 24)]))

    def lag_on(self):
        return self.var(0, 1)

    def lag_off(self):
        return self.var(0, 0)

    def release(self, idx=0):
        """Throws: let go of the victim (idx 0), with the throw hitbox set by throw()."""
        return self.raw(bits([(0x14, 6), (idx, 26)]))

    def iasa(self):
        """From here the move can be interrupted by any action."""
        return self.raw(bits([(0x17, 6), (0, 26)]))

    def interruptible(self):
        """For a character's own states (specials): cmd_vars[0] = 1, which their IASA code reads."""
        return self.var(0, 1)

    def flag(self):
        """Raise throw_flags_b0: special-move code polls it to fire a projectile or change phase on this frame."""
        return self.raw(bits([(0x18, 6), (0, 26)]))

    def hurt(self, joint, state):
        """One bone's hurtboxes: 0 normal, 1 invincible, 2 intangible (0x1C; the engine resets it on the next action)."""
        import rig
        ji = [j[0] for j in rig.JOINTS].index(joint) if isinstance(joint, str) else joint
        return self.raw(bits([(0x1C, 6), (ji, 8), (state, 18)]))

    def body(self, state):
        """0 normal, 1 invincible, 2 intangible."""
        return self.raw(bits([(0x1A, 6), (state, 26)]))

    def jab_window(self, open_=True):
        """Jab combo: 0 opens the window to the next jab (Mario's scripts write 1 early, then 0)."""
        return self.raw(bits([(0x1D, 6), (0 if open_ else 1, 26)]))

    def jab_rapid(self, on=True):
        return self.raw(bits([(0x1E, 6), (1 if on else 0, 26)]))

    def throw(self, idx, dmg, angle, kbg, wdsk, bkb, element=0, sfx=(0, 0)):
        """The throw's hit on its victim (idx 0) or on bystanders the victim hits (idx 1)."""
        return self.raw(bits([(0x22, 6), (idx, 3), (dmg, 23)]) +
                        bits([(angle, 9), (kbg, 9), (wdsk, 9), (0, 5)]) +
                        bits([(bkb, 9), (element, 4), (sfx[0], 3), (sfx[1], 4), (0, 12)]))

    def smash_charge(self, frames=60, rate=350, colour=0x77):
        """Hold here while A is held (up to `frames`), damage x rate/256 at full charge (Melee's 1.367)."""
        return self.raw(bits([(0x38, 6), (frames, 10), (rate, 16)]) + bits([(colour, 8), (0, 24)]))

    # ---- the model: visibility groups and part poses (decomp lb/types.h; ftaction.c ftAction_80071D40, 800727C8)
    def model(self, group, option):
        """0x1F model mod: show option `option` of visibility group `group` (-1 hides the group)."""
        return self.raw(bits([(0x1F, 6), (group, 7), (option, 19)]))

    def model_revert(self):
        """0x20: every group back to its default (what an action change does)."""
        return self.raw(bits([(0x20, 6), (0, 26)]))

    def part_pose(self, part, pose, blend=0):
        """0x29: model part `part` to pose `pose`, blending over `blend` frames (0 snaps)."""
        return self.raw(bits([(0x29, 6), (part, 7), (pose, 7), (blend, 12)]))

    def form(self, side, name):
        """Geno: show weapon form `name` (rig.FORMS) on hand `side` ('L' or 'R'): two model-mod commands."""
        import rig
        for g, o in rig.form_commands(side, name):
            self.model(g, o)
        return self

    def hand(self, side, pose, blend=0):
        """Geno: hand `side` to pose `pose` (rig.HAND_POSE: fist, open, point, grip)."""
        import rig
        return self.part_pose(rig.PART[side], rig.HAND_POSE[pose], blend)

    def cap(self, pose, blend=0):
        """Geno: the cap to pose `pose` (rig.CAP_POSE: rest, back, low)."""
        import rig
        return self.part_pose(rig.PART['cap'], rig.CAP_POSE[pose], blend)

    def bytes(self):
        if not self.data.endswith(b'\0\0\0\0'):
            self.end()
        return bytes(self.data)


def disasm(data):
    """A readable listing, for checks."""
    sizes = [5, 5, 1, 1, 1, 1, 1, 3, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 3, 1, 1, 1, 7, 4, 1, 1, 1, 1, 1, 1, 1,
             1, 1, 1, 1, 1, 1, 1, 3, 3, 2, 1, 4]
    o, out = 0, []
    while o < len(data):
        op = data[o] >> 2
        n = (2 if op in (5, 7) else 1) if op < 10 else sizes[op - 10]
        w = data[o:o + 4 * n]
        out.append(f'{o:4d} {op:02X} {w.hex()}')
        if op == 0: break
        o += 4 * n
    return '\n'.join(out)


class ItemScript(Script):
    """An item state's script (the item command set, it_803F22A8): hitboxes are 6 words, offsets in the item's frame
    (a laser flies along its local +Z, so a trail sits at negative z)."""

    def hitbox(self, id, dmg, size, off=(0, 0, 0), angle=361, kbg=100, wdsk=0, bkb=0, element=0, shield=0, group=0,
               bone=0, tail=0x047, flags=0x00FDD000, rehit=0):
        """tail: the low 9 bits of word 4 (sfx severity/kind and two flags); flags: word 5's low 24 bits (what it can
        hit), Falco's laser's by default; rehit: word 5's top byte, frames before a victim can be hit again (0: once;
        Falco's laser uses 16)."""
        flags = (rehit & 0xFF) << 24 | (flags & 0xFFFFFF)
        w0 = bits([(0x0B, 6), (id, 3), (group, 3), (bone, 7), (dmg, 13)])
        w1 = bits([(fx(size), 16), (fx(off[0]), 16)])
        w2 = bits([(fx(off[1]), 16), (fx(off[2]), 16)])
        w3 = bits([(angle, 9), (kbg, 9), (wdsk, 9), (0, 5)])
        w4 = bits([(bkb, 9), (element, 5), (0, 1), (shield & 0xFF, 8), (tail, 9)])
        return self.raw(w0 + w1 + w2 + w3 + w4 + flags.to_bytes(4, 'big'))


def _item_clear(self):
    """Items clear all hitboxes with 0x0F (it_802796C4); 0x0E removes one, 0x0C sets one's damage."""
    return self.raw(bits([(0x0F, 6), (0, 26)]))


ItemScript.clear = _item_clear
