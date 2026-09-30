# Locomotion: how the cast walks and runs, and Geno's numbers

Measured 2026-09-28 from the disc's own animations (`datkit fk`, sampled per frame) with
`tools/machinima/melee/motion/gait.py`, across ten distinct animators: Mario, Marth, Fox, Link, Sheik, Falcon, Ness,
Peach, Samus and Ganondorf. Lengths are in units of leg length L (hip socket to knee to ankle in the bind pose, times
ModelScale), and angles are in degrees. Geno's legs are L = 5.05 (thigh 2.6, shin 2.45), close to Mario's 5.2. Geno's
own numbers come from the same tool run on his built `PlGeAJ.dat` (`--fk DIR --codes Ge --skel DIR/skel`). In-game
checks come from `director/walk_lab.py` and `director/labs/footslide.py`, `walk_board.py`.

## Engine facts that shape the animation

| Fact | Evidence | Consequence |
|---|---|---|
| Walks play at \|v\| / 0.18, 0.44 or 0.70, and the run at \|v\| / 1.45 (Geno keeps Mario's attributes). The stick picks the walk (0.4 and 0.8 of the walk speed, PlCo) | ftwalkcommon.c, ftCo_Run.c | A stance boot slides back at exactly that speed per frame, so it stays planted at any speed. In play WalkSlow runs at 1.6-2.2x, WalkMiddle at 0.9-1.8x, WalkFast at 1.14-1.43x and Run at 1.1x |
| A walk speed change keeps the phase: new frame = int(new length x old frame / old length) | ftWalkCommon_800DFEC8 | All three walks share phase: frame 0 is the left heel strike and n/2 the right. The int() truncation costs up to a frame of stride at each change |
| **Wait1, the three walks and Run blend 6 frames into themselves**; every other action cuts | ftData+0x10 byte 0 (HSDRaw's "Flags") is the default blend that Fighter_ChangeMotionState uses when a caller passes 0. It is 6 on those five in Mario, Fox and Samus alike | A blend holds the old pose still while the body moves, so a planted boot drifts: 3.3 units over the run's first four frames out of the dash. Geno's Run blends 0 frames (`locomotion.BLEND`, fighter-build's `blend`), because its entries (Dash 11, TurnRun 17) already equal its frame 0. The walks keep 6, which smooths speed changes |
| Dash_Enter plays a frame on entry | ftAnim_8006EBA4 in Dash_Enter; the FEET log's frame | Dash frame 1 is the first on screen and frame 0 never shows. Held, the run takes over after frame 10 (Run frame 0 = Dash frame 11); released, frame 17 is Wait1 |
| Dash speed per frame: 0, 1.45, 1.55, then 1.6 held; released, 0.08 slower each frame | POS log | The drive foot's stance is keyed to it. Dash-dance dashes start from the other way (0.32 back, then 1.13, 1.23...), so the drive foot slips about 0.9 there |
| RunBrake: 0.08 slower each frame from 1.6. The flag at 11 (template) freezes the pose until he stops (x42C = 0), then 11-17 play standing | ftCo_RunBrake.c | Frames 0-11 are the skid and 11 the held skid. 12-17 stand up and step back into Wait1 frame 0 (frame 17) |
| TurnRun: 0.1 slower each frame, frozen on the flag frame until the slide stops, then the facing flips and he speeds up the other way; Run follows | ftCo_TurnRun.c | The template's flag was at 18 of an 18-frame animation, so the turnaround ended first and he stood, then turned. Geno's own script puts it at 9 (Fox's frame). The half turn is on YRotN (Mario's and Fox's convention) |
| Script frames run on animation time; SetTimerAnimation waits for the loop to wrap | lbcommand.c | Loop scripts use SetLoop/ExecuteLoop (no pointers) with the footsteps on the heel strikes |
| GraphicEffect's second word is the effect id (16 bits); its first word holds the bone | ftAction_80071028 | datkit's RemapScript rewrites bits 42-47, the low bits of the id, not the bone. Every remapped template GFX is a different effect (the dash's 1023 became 983). Geno's locomotion scripts are authored with the right ids |

## The cast (median, with the interquartile range)

| | frames | stride / L | duty | knee at strike | knee stance max | knee swing max | ankle lift / L | pelvis bob / L | hip yaw ± | shoulder yaw ± | arm swing ± | elbow bend | lean |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| WalkSlow | 57 (50-70) | 1.62 (1.44-2.06) | 0.55 | 66 | 71 | 82 | 0.19 | 0.10 | 10 | 5 | 11 | 81 | 12 |
| WalkMiddle | 40 (35-45) | 2.36 (1.63-3.43) | 0.43 | 45 | 66 | 90 | 0.29 | 0.11 | 9 | 8 | 14 (7-32) | 71 | 13 |
| WalkFast | 30 (26-30) | 3.12 (2.56-4.02) | 0.30 | 46 | 73 | 113 | 0.38 | 0.15 | 16 | 12 | 19 (11-38) | 73 | 23 |
| Run | 20 (20-20) | 4.42 (3.59-6.18) | 0.28 | 77 | 98 | 137 | 0.65 | 0.19 | 23 | 13 | 13 (10-80) | 63 | 53 (43-71) |

- **Walks are brisk and airborne.** At the attribute speed the fast walk has each foot down only 30% of the cycle,
  with a flight between steps. Only the slow walk has double support. The pelvis is lowest shortly after each strike and
  bobs twice a cycle, about 0.1-0.15 L.
- **The feet roll.** The toe is up 1-12 degrees at the strike and the heel up 22-27 degrees at toe-off in the middle and
  fast walks. The stance boot slides back at 0.93-1.0 of the body speed (median slip under 0.5 units a stance).
- **Hips and shoulders counter-rotate** (correlation about -0.5 in the medians, -0.9 in Mario's and Fox's walks). The
  arms counter-swing the legs by half a cycle with the elbows well bent (60-80 degrees). The head bobs with the hips
  (ratio about 1.0-1.15) and holds its line.
- **Runs lean hard and bound.** The torso is 43-71 degrees off vertical. The feet are down a quarter of the cycle, lift
  0.65 L, and the swing knee folds to about 137 degrees.
- **Dash** (22-31 frames): frame 0 is Wait, a 1-2 frame load, then a leap held as a lunge. Mid-dash the lean is 67
  degrees (45-90) at frames 5-8 and the legs split 1.4 L. It ends back on Wait. **TurnRun** (20-30): a skid that turns
  half round and leans back 68 degrees. **RunBrake** (18-28): it starts on the run's lean (56 degrees), sits back to
  about -5 by frame 6 and stands up into Wait.

## Geno

Each cycle is one stride authored for the attribute speed (`projects/geno/rig/locomotion.py`, GAITS). T is how far the
body passes over a planted boot, which sets the duty. The strike is centred on the pelvis.

| | frames | stride / L | T (duty) | knee strike / stance max / swing max | ankle lift / L | bob / L | hip yaw mean ± | chest ± | arm ± / elbow | lean (chest, pelvis) |
|---|---|---|---|---|---|---|---|---|---|---|
| WalkSlow | 56 | 2.00 | 5.6 (0.56) | 33 / 54 / 90 | 0.23 | 0.13 | -14 ± 8 | ± 6 | 16 / 44 | 11, 3 |
| WalkMiddle | 32 | 2.79 | 5.8 (0.41) | 37 / 48 / 108 | 0.31 | 0.11 | -9 ± 11 | ± 9 | 28 / 50 | 15, 4 |
| WalkFast | 26 | 3.60 | 6.0 (0.33) | 39 / 65 / 131 | 0.39 | 0.11 | -4 ± 13 | ± 11 | 36 / 56 | 18, 5 |
| Run | 18 | 5.17 | 6.4 (0.25) | 53 / 72 / 151 | 0.56 | 0.15 | 0 ± 20 | ± 13 | 48 / 84 | 42, 16 |

(Knee and lift figures are gait.py's measurements of the built animations; the rest are the authored values.)

- **Frame counts.** Geno's legs match Mario's, so each stride per leg length sits inside the cast's range at a
  slightly quicker cadence than Mario's (stride / L: 2.0, 2.8, 3.6, 5.2 against the medians 1.6, 2.4, 3.1, 4.4). At
  top speed that is 18-39 game frames per walk stride and 16 per run stride (Mario 19-33 and 19).
- **Stance.** The boot lands on its heel with the toe up 14-20 degrees (10 in the run), rolls flat, and peels onto its
  ball; the heel is up 26-40 degrees at toe-off. Heel and ball are fixed points on the floor (the loaf's heel 0.8 behind
  the ankle, its ball 1.3 ahead, sole 0.95 below). The pelvis height is held under 95% of leg reach and smoothed, so the
  knees never straighten past about 33 degrees and never pop.
- **Swing.** A Hermite path from toe-off (leaving with the roll's own velocity) to the next strike, landing from above
  with 60-75% of the ground speed matched (a short plant, not a skim), plus a lift. The sole is kept 0.12 off the floor
  mid-swing.
- **Orientation.** The idle opens 25 degrees toward the camera. The walks fade from -14 (slow) through -9 and -4 to the
  run's 0, and the chest and head follow (head -7, -4, -2, 0), while the hips swing ±8-20 and the chest counters.
- **Arms.** They counter the legs with a 1-2 frame lag, and the elbow bends more on the forward swing, trailing the
  upper arm by another 1.5-2.5 frames.
- **One-shots** (key poses on monotone splines, boots pinned to the floor at the engine's speeds):
  - **Dash.** Frame 1 loads (pelvis down 0.4, the rear heel up); 2-4 drive off the left ball as the right knee comes
    through; 5-8 are the lunge, with the chest 44-46 degrees forward and the pelvis 16; the right heel lands at 9 where
    the run's stance has it; 9-11 are Run 16, 17, 0. Released, the left boot swings through and brakes, and 17 is Wait1.
  - **TurnRun.** The left boot plants and he pivots a quarter turn toward the camera into a low sideways skid (the hold
    at 9). Then he comes round over the right boot and runs; 17 is Run frame 0 turned half round.
  - **RunBrake.** The left boot plants heel-first ahead and both skid while he sits back (held at 11). He stands, the
    front boot steps back to +1.8, and 17 is Wait1 frame 0.
- **Footfalls.** Walks: the left heel on 0, the right on 28, 16 or 13. Run: the left on 7, the right on 16, with dust
  as each toe leaves (2, 11). Dash: the right heel on 9, and the braking left on 13. TurnRun: the left plant on 3, the
  right on 15. RunBrake: the plant on 3 and the step back on 15.

## Foot slide, measured in the game

`walk_lab` logs both foot bones every frame (the FEET cue), and `footslide.py` tracks the boot's heel and ball points
while each is on the floor, splitting the stances by phase. These numbers are the drift of a planted point over one
stance, in world units: median / worst.

| | settled | entry (the first 8 frames after an action change) |
|---|---|---|
| WalkSlow | 0.002 / 0.005 | 0.56 / 1.05 |
| WalkMiddle | 0.011 / 0.091 | 0.43 / 0.61 |
| WalkFast | 0.015 / 0.024 | 0.21 / 0.38 |
| Run | 0.030 / 0.089 | 0.15 / 0.52 |

| one-shot | phase: median / worst |
|---|---|
| Dash | drive 0.51 / 0.52; strike, held into the run 0.0004; strike, released 1.1-1.9; stop, released 0.6-3.1 |
| TurnRun | skid (slides by design, with dust): 6.3; the push the other way 0.09 |
| RunBrake | skid (by design): 8.0; standing up 0.19 / 0.25 |

- **Settled walks and the run hold the floor** (under 0.1 per stance at every speed; the engine plays them at the
  stick's own rate). The dash hands its planted right boot to the run exactly.
- **What still slides is the engine's.**
  - Every entry into a walk blends 6 frames from the pose before. The frozen old pose rides along with the body, so the
    boot drifts; every character does this.
  - Walk speed changes truncate the frame.
  - A walk's first steps lag its acceleration by a frame.
  - A released dash slows at 0.08 a frame from whenever the stick let go, while the animation can only assume one speed.
  - The dash dance starts each dash against the last one's momentum, so the drive boot slips about 0.5 in both a
    standing dash and a dance.

## The states around it (states_air.py)

These are key poses on monotone splines, solved every frame: arms move as directions, and legs are either planted by IK
or posed by joint angle in the air. The states are registered into moves.MOVES. Every seam is exact (to the bit, checked
on the solved poses):
- **Turn** starts on Wait1 and ends on Wait1 turned half round.
- **The jumps and Pass** end on Fall frame 0. **The double jumps** end on FallAerial frame 0. moves.air_base() is Fall
  frame 0, so every aerial starts and ends there too.
- **Landing, LandingFallSpecial and SquatRv** end on Wait1.
- **Squat** ends on the crouch that SquatWait loops, and anims.crouch_pose() returns the same crouch, so the crouching
  attacks meet it.
- **The loops** close.

| | engine facts | Geno |
|---|---|---|
| Turn (12) | A dash dance shows only frame 1 of it between dashes (Turn_Enter_Smash). The standing turn is authored in the old facing and rotates 180 degrees (MOTION_STUDY) | The head leads, 55 degrees round by frame 1 and 80 by 2, while the chest winds. A hop spins the legs half round toward the camera over 3-8. He lands in the stagger at 8 and settles by 12 |
| KneeBend (jumpsquat 5) | The engine plays whatever KneeBend points at and jumps on frame 5. The template pointed it at Landing's figatree, the cast's convention | His own animation. Already dipping on frame 0, deepest on 2-3 (hips down half a leg, 17% of his height, knees at about 60 degrees; the cast: 17-39% and 33-64 degrees), arms swung back, rear heel up |
| JumpF / JumpB (55 / 60) | They end in Fall; frame 0 is extended in the cast (knees 93-124 degrees) | Frame 0 has straight legs, pointed toes and arms flung up. Then a jaunty tuck (left knee up, right leg trailing), or rocked back with both knees up for JumpB, settling into the fall |
| JumpAerialF / B (60 / 90) | The cast's double jumps flip or kick | A kick off the air, then a tight forward or back somersault (a full turn on XRotN about his middle over frames 3-19), opening into the fall |
| Fall family | FallF and FallB are blended in by drift on Fall's own frame (ftCo_Fall_Anim_Inner) | A fluttering 20-frame loop: a puppet's balance, arms out with forearms up, knees soft. FallF and FallB lean and trail on the same cycle. FallAerial* raise the arms 8 degrees. FallSpecial*: the strings cut (limp arms trailing up, head lolled) |
| Landing (29) | The normal landing lag is 4. The cast bottoms out on frames 2-16 and sinks 13-40% | The impact bottoms out on frame 2 (hips down 2.45) and is still low when the lag ends. Wait1 by 29 |
| LandingFallSpecial (30) | Its own animation (the template pointed it at Landing's). The engine stretches it over the special's landing lag | A deeper sink and a slower rise |
| Squat / SquatWait / SquatRv (8 / 130 / 10) | His crouch height is a gameplay contract | The boots stay planted in the idle's stagger (rear heel up) and the body folds over the knees with the head up. **The crouched hurtbox top is 10.52** (Fox's crouch-to-stand ratio on his 15.0; the blockout's 9.52 came from its head rolled onto its side). Two slow breaths a loop |
| Pass (29) | He is falling from its first frame | The crouch pulls up into a tuck through the platform, then the legs let down into the fall |
| Ottotto / OttottoWait (13 / 185) | | The front boot hops back to the edge. Then he lurches twice a loop, windmilling four times with the rear leg swinging back as a counterweight, with a nervous tremble on top |

Planted boots in game (footslide.py, drift per stance, median / worst):
- Squat, SquatWait and SquatRv: 0.000 / 0.001.
- KneeBend: 0.001.
- LandingFallSpecial: 0.03 / 0.05.
- Ottotto: 0.001. OttottoWait: 0.005 / 0.015.
- The Turn's planted frames: 0.000.

The only larger drifts come from momentum: a landing out of a drifting jump slides by the landing's own ground velocity
(2.1), and a turn entered while still sliding drifts 0.45.
