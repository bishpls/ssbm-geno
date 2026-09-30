"""Where Geno's movement sounds (bank 55, 550028-550052) play: his voice-table slots and his action scripts.

Command layouts are the decomp's (src/melee/lb/types.h, ftaction.c):
- 0x11 SoundEffect, 3 words: opcode:6 behavior:8 pad:18 | sfx id | pad:16 vol:8 pan:8. Behavior 0 = ft_PlaySFX,
  untracked (what Geno's move scripts use); 1 = the tracked slot the Beam charge uses; 2 and 6 = the voice tracks.
- 0x26 PseudoRandomSoundEffect, 7 words: opcode:6 vol:8 pan:8 behavior:4 range:6 | six sfx ids. It plays
  ids[HSD_Randi(range)]; retail pads unused slots with 540000 (Fox: 99FD0083 0001ADEA 0001ADEA 0001ADCF 00083D60 x3).
The command's vol (0-127) is doubled and clamped to 255, then multiplied with the sem script's vol (lbaudio_ax.c
fn_80023750, synth.c): 0x7F is full, 0x6E is -1.3 dB, 0x64 is -2.1 dB.

    .venv/bin/python projects/geno/sound/wiring.py      # prints the tables and every command's hex
"""
import struct

ID = dict(
    STEP_WALK_L=(550028, 550029, 550030), STEP_WALK_R=(550031, 550032, 550033),
    STEP_RUN_L=(550034, 550035, 550036), STEP_RUN_R=(550037, 550038, 550039),
    LAND=(550040, 550041), LAND_HEAVY=550042, JUMP=550043, JUMP_AIR=550044, CAPE1=550045, CAPE2=550046,
    LEDGE=550047, TECH=(550048, 550049), TEETER=550050, STARKO=550051, RATTLE=550052,
    CHANT=550053,                          # the crowd's "Ge-no! Ge-no!" (cheer/bank.py appends it to geno.ssm)
    TIMED_HIT=550054, TIMED_BOOST=550055)  # SMRPG's timed-press sounds (timed.py): ROM 172 and ROM 078 cut short
SILENT, NONE = 540001, 540000              # 540001 stops the voice track (what the build uses now); 540000 plays nothing


def sfx(sid, vol=0x7F, pan=0x40, behavior=0):
    """0x11: one sound."""
    return struct.pack('>III', (0x11 << 26) | (behavior << 18), sid, (vol << 8) | pan)


def random_sfx(ids, vol=0x7F, pan=0x40, behavior=0):
    """0x26: one of up to six sounds, uniformly (HSD_Randi(len(ids)))."""
    ids = list(ids) if isinstance(ids, (tuple, list)) else [ids]
    assert 1 <= len(ids) <= 6
    w0 = (0x26 << 26) | (vol << 18) | (pan << 10) | (behavior << 6) | len(ids)
    return struct.pack('>7I', w0, *(ids + [NONE] * (6 - len(ids))))


def cue(ids, vol=0x7F):
    return random_sfx(ids, vol) if isinstance(ids, tuple) else sfx(ids, vol)


def decode_random(b):
    w0 = struct.unpack('>I', b[:4])[0]
    return dict(op=w0 >> 26, vol=(w0 >> 18) & 0xFF, pan=(w0 >> 10) & 0xFF, behavior=(w0 >> 6) & 0xF, range=w0 & 0x3F,
                ids=list(struct.unpack('>6I', b[4:28])))


# ---- ftData+0x4C (SBM_PlayerSFXTable) for PlGe.dat. How the engine plays each slot (decomp call sites):
VOICE_TABLE = [
    # (HSDRaw field, offset, value, played by)
    ('SFX_YouFreakinDied', 0x04, SILENT, 'blast-zone KO, ft_0D31.c playDeadSfx -> ft_800881D8 (voice track). Keep silent: the KO blast covers it'),
    ('SFX_MetalBox', 0x08, NONE, 'also on the blast-zone KO; unchanged'),
    ('SFX_StarKO', 0x0C, ID['STARKO'], 'DeadUpStar / DeadUpStarIce entry (ft_0D31.c) via ft_800881D8; stamina KO (ft_0C8C.c) via ft_PlaySFX'),
    ('SFX_Jump', 0x10, ID['JUMP'], 'ground jump take-off, ftCo_Jump.c via ft_800881D8 (JumpF/B scripts still play 74 at frame 1)'),
    ('SFX_DoubleJump', 0x14, ID['JUMP_AIR'], 'JumpAerialF/B entry, ftCo_JumpAerial.c via ft_80088328 (track 0x2A)'),
    ('SFX_Dodge', 0x18, ID['TEETER'], 'teeter: OttottoWait entry, ftCo_Ottotto.c via ft_80088328 (the only reader of +0x18)'),
    ('LightHitSFX', 0x1C, [ID['RATTLE']], 'array: medium knockback (ftCo_Damage.c, kb >= x208) -> ft_800889F4 picks one'),
    ('HeavyHitSFX', 0x20, [ID['RATTLE'], ID['RATTLE']], 'array (2 entries now): strong knockback (kb >= x20C) and the screen-KO splat (ft_0D31.c)'),
    ('SFX_Tech', 0x24, ID['TECH'][0], 'Passive, PassiveStandF/B, PassiveWall, PassiveCeil entry via ft_800881D8'),
    ('SFX_LedgeGrab', 0x28, ID['LEDGE'], 'CliffCatch, ftcliffcommon.c via ft_800881D8'),
    ('SFX_HeavyLift', 0x2C, ID['TEETER'], 'heavy item pickup, ftpickupitem.c via ft_800881D8 (a strained creak)'),
    ('SFX_GrabCatch', 0x30, 81, 'unchanged (the common grab)'),
    ('SFX_Cheer', 0x34, ID['CHANT'], 'the crowd chant: crowdsfx.c un_80321EBC reads it (ftLib_8008746C) when a human Geno at '
     '100%+ lands a big hit in a string, and plays it back to back through lbAudioAx_800240B4. 540000 would mean no chant; '
     "540001 (the old value) isn't that sentinel, so the crowd gasped, 'chanted' nothing and cheered"),
]

# ---- script cues. Frames are the scripts' timer frames (at(n) / AsynchronousTimer n, as Mario's templates count);
# frame 0 means the top of the script (the action's first frame, before any timer).
# Footfalls come from the locomotion (rig/locomotion.py: foot paths and IK). The walks and the run loop, so their steps
# live in their own looping scripts (locomotion.scripts(): a FootstepEffect, the rumble and these wooden steps on each heel
# strike; anims.FOOTFALL_CUES keeps them out of the cues below); these rows only record where the heels land. Frame 0
# of each walk is the left heel strike (a step on 0 fires as the loop wraps, not on entry from Wait).
CUES = [
    # (action, anim frames, [(frame, ids, cmd vol, note)])
    ('WalkSlow', 56, [(28, ID['STEP_WALK_R'], 0x64, 'locomotion.scripts(): right heel strike'),
                      (0, ID['STEP_WALK_L'], 0x64, 'left heel strike, as the loop wraps')]),
    ('WalkMiddle', 32, [(16, ID['STEP_WALK_R'], 0x6E, 'locomotion.scripts()'), (0, ID['STEP_WALK_L'], 0x6E, '')]),
    ('WalkFast', 26, [(13, ID['STEP_WALK_R'], 0x6E, 'locomotion.scripts()'), (0, ID['STEP_WALK_L'], 0x6E, '')]),
    ('Run', 18, [(7, ID['STEP_RUN_L'], 0x7F, 'locomotion.scripts(), with a dust puff as each toe leaves (2, 11)'),
                 (16, ID['STEP_RUN_R'], 0x7F, '')]),
    ('Dash', 18, [(0, ID['CAPE2'], 0x7F, 'with the template sound 0; dash-dancing retriggers it (see note)'),
                  (9, ID['STEP_RUN_R'], 0x7F, 'the right heel lands out of the lunge'),
                  (13, ID['STEP_RUN_L'], 0x7F, 'the left boot plants to brake (a released dash only)')]),
    ('TurnRun', 18, [(0, ID['CAPE1'], 0x7F, 'the cape swings round'),
                     (3, ID['STEP_RUN_L'], 0x7F, 'the left boot plants for the skid'),
                     (15, ID['STEP_RUN_R'], 0x7F, 'the right heel lands the other way (after the hold at 9)')]),
    ('Turn', 12, [(0, ID['CAPE1'], 0x64, 'standing turn')]),
    ('RunBrake', 18, [(2, ID['CAPE1'], 0x64, 'optional: the cape swings forward over the skid (sound 5 at frame 1 stays)'),
                      (3, ID['STEP_RUN_L'], 0x7F, 'the left boot plants to brake'),
                      (15, ID['STEP_WALK_L'], 0x64, 'it steps back into the stance (after the hold at 11)')]),
    ('Landing', 29, [(0, ID['LAND'], 0x7F, 'with the template LandingEffect (0x37) at frame 1')]),
    ('LandingFallSpecial', 29, [(0, ID['LAND_HEAVY'], 0x7F, 'landing out of a helpless fall: the heavy clatter')]),
    ('LandingAirN/F/B/Hi/Lw', 30, [(0, ID['LAND'], 0x7F, 'aerial landing lag, with their LandingEffect at frame 1')]),
    ('EscapeF / EscapeB', 32, [(4, ID['TECH'], 0x6E, 'roll: the body goes over (the template roll sound 1 at frame 1 stays)')]),
    ('EscapeN', 23, [(2, ID['CAPE2'], 0x6E, 'spot dodge (template sound 2 at frame 1 stays)')]),
    ('EscapeAir', 49, [(4, ID['CAPE1'], 0x6E, 'air dodge (where the template had Mario\'s voice, now silent)')]),
    ('DownBoundU / DownBoundD', 26, [(0, ID['LAND_HEAVY'], 0x7F, 'knocked down / missed tech: the impact (template sound 13 at 22 stays)')]),
    ('DownStandU / DownStandD', 30, [(3, ID['TECH'], 0x6E, 'get-up')]),
    ('DownForwardU/D, DownBackU/D', 36, [(3, ID['TECH'], 0x6E, 'get-up rolls')]),
    ('CliffClimbQuick', 35, [(30, ID['STEP_RUN_R'], 0x6E, 'with the template step (443) at 30')]),
    ('CliffClimbSlow', 60, [(37, ID['STEP_WALK_L'], 0x6E, 'with the template steps (443) at 37 and 59'),
                            (59, ID['STEP_WALK_R'], 0x6E, '')]),
    # the item actions (rig/states_items.py): a wooden clack as the hand closes on a light item, the arm's swish as a
    # throw lets go (the templates' release frames), the heave of a heavy throw, and his steps under a crate
    ('LightGet', 8, [(2, ID['LEDGE'], 0x40, 'the hand closes on it (the template attaches it on frame 2)')]),
    ('LightThrowF', 25, [(7, ID['CAPE1'], 0x50, 'the release (template 0x14 at 7)')]),
    ('LightThrowB', 25, [(4, ID['JUMP'], 0x48, 'the hop round'), (7, ID['CAPE1'], 0x50, 'the release')]),
    ('LightThrowHi', 24, [(9, ID['CAPE1'], 0x50, 'the release')]),
    ('LightThrowLw', 25, [(7, ID['CAPE1'], 0x50, 'the release')]),
    ('LightThrowDash', 40, [(4, ID['CAPE1'], 0x50, 'the release')]),
    ('LightThrowAirF', 25, [(7, ID['CAPE1'], 0x50, 'the release')]),
    ('LightThrowAirB', 25, [(7, ID['CAPE1'], 0x50, 'the release')]),
    ('LightThrowAirHi', 25, [(6, ID['CAPE1'], 0x50, 'the release')]),
    ('LightThrowAirLw', 25, [(7, ID['CAPE1'], 0x50, 'the release')]),
    ('HeavyWalk1', 40, [(19, ID['STEP_WALK_R'], 0x58, 'his steps under the crate'), (39, ID['STEP_WALK_L'], 0x58, '')]),
    ('HeavyWalk2', 40, [(19, ID['STEP_WALK_L'], 0x58, ''), (39, ID['STEP_WALK_R'], 0x58, '')]),
    ('HeavyThrowF', 40, [(18, ID['CAPE2'], 0x60, 'the heave (template release at 18)')]),
    ('HeavyThrowB', 40, [(4, ID['JUMP'], 0x50, 'the hop round with it'), (10, ID['LAND'], 0x50, ''), (18, ID['CAPE2'], 0x60, 'the heave')]),
    ('HeavyThrowHi', 30, [(14, ID['CAPE2'], 0x60, 'the heave (template release at 14)')]),
    ('HeavyThrowLw', 30, [(11, ID['LAND_HEAVY'], 0x58, 'the slam (template release at 11)')]),
]


def check():
    fox = bytes.fromhex('99FD00830001ADEA0001ADEA0001ADCF00083D6000083D6000083D60')
    d = decode_random(fox)
    assert (d['op'], d['vol'], d['pan'], d['behavior'], d['range']) == (0x26, 0x7F, 0x40, 2, 3) and d['ids'][:3] == [110058, 110058, 110031]
    assert random_sfx(d['ids'][:3], 0x7F, 0x40, 2)[:16] == fox[:16]
    assert sfx(443) == bytes.fromhex('44000000000001BB00007F40')     # Mario's CliffClimbQuick step, byte for byte


if __name__ == '__main__':
    check()
    print('voice table (ftData+0x4C):')
    for f, off, v, how in VOICE_TABLE:
        print(f'  +{off:02X} {f:20s} {str(v):22s} {how}')
    print('script cues (0x26 for variant sets, 0x11 for single sounds; behavior 0):')
    for act, n, cues in CUES:
        for fr, ids, vol, note in cues:
            print(f'  {act:28s} n={n:2d} {("top" if fr == 0 else f"at({fr})"):>6s} vol {vol:#04x}  {cue(ids, vol).hex().upper()}  {note}')
