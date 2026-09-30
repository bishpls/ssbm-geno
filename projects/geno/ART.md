# GENO: art direction (production model and animation)

The production model replaces the blocky rig on the same skeleton (the gameplay contract: hurtboxes, the shield fit, ledge
grabs and grab holds all hang off his bones). Style targets and research boards are local only, in
`~/games/melee/work/art/` (they include game renders and derived art: never commit them).

## Decided (Michael, 2026-09-27)

- **The throws (2026-09-29):**
  - The up throw's shots are spinning gold stars with sparkle trails (SMRPG's Star Gun).
  - The forward throw's rocket launches as a rocket, not a cannon (Michael, 2026-09-29: "remove the explosion effect
    from fthrow"): a small white four-point star at the wrist, then an unbroken trail of soft grey exhaust puffs behind
    the fist, out and back, as Double Punch's. No flash, smoke or sparks.
- **Geno Flash (2026-09-29):**
  - SMRPG's sequence: the yellow glow, a fireball from the cannon, the sun, then a red flash.
  - **One sun for the whole move** (Michael's review, 2026-09-29, from the 2023 remake's sun as his reference): an orange
    disc, light yellow at its heart to deep orange at the rim, with a thin bright rim; round it a ragged corona of yellow
    flame tongues, orange at their tips, churning and slowly turning (SMRPG's spinning triangles were a 16-bit corona);
    a small surprised face, two small dark oval eyes and a round "o" mouth (no smile). The fireball is the same sun,
    small; it grows into the sun. No star.
  - Sized to the hitbox: the disc's edge just inside it, only the corona past it (about 1.2x its radius).
  - **Smaller** (Michael, 2026-09-29: "excellent! It's just still too big"): the sun appears at PK Flash's burst size
    (radius 14.3) and grows to 28, not 38 (about 34 drawn at full, not 46). Its first 8 frames, the burst and the kill
    hit, are drawn white-hot; the late sun, a weaker hit, is the plain orange sun.
  - The red flash as it ends is the sun's own silhouette flashing red as it goes, not a four-point flash.
  - Over it, the finishing flash (Michael, 2026-09-29): a pink-hot five-point star spinning out of the sun, a round ring
    and small gold stars spinning away. The old ending's flash and ring, with a star for its diamond.
  - The full-body cannon (a blue-and-gold cannon on a wheeled carriage, SPR0030): built 2026-09-29 (geno-cannon), below
    ("Geno Flash's cannon"). Its interface is in DESIGN §12.
  - Approved (Michael, 2026-09-29): "Cannon size looks good. Timing and sounds are good. Wheels are good. Mallow cannon
    is good." The size, the swap timing under the glows, the wheeled carriage and the costume rule stay as built.
- **The Geno Blast (2026-09-29):**
  - SMRPG's flat columns of colour dropping from the sky, a new colour each column, landing in white clouds.
  - The cast's blue sparkles at his hand.
  - Our own tell: a floor oval and a thin rising beam that widens toward the strike.
- **The Geno Whirl (2026-09-29):**
  - A white-yellow bladed disc of light, tilted into SMRPG's oval, with SMRPG's trail of fading yellow ovals.
  - A yellow-white explosion with orange sparks on the hit, and a blue flash on the timed crit.

- **The gun normals' bursts (2026-09-29, Michael's brief: the gun moves must read in play; geno-fxnormals,
  `fx/efge_normals.py`):**
  - Each gun blast draws on its own hitbox spheres on their active frames, as far out as they reach (DESIGN changelog
    has the numbers), with one language per weapon form.
  - **Hand Gun** (forward tilts, forward air): a four-point flash at the barrel (SMRPG's flash that turns 45 degrees);
    on each sphere a hot glow and soft yellow-white puffs of SMRPG's finger-shot mist (SPR0527) that turn grey, drift
    up and fade in ~10 frames; at the tip the mist forms the small gold star, which shrinks to an orange one and blinks
    out.
  - **The jab's finger taps:** the same puff, smaller and quicker, with the Finger Shot puff's grey mist and a small
    star, so the two finger weapons read as one family.
  - **Star Gun** (up smash, up air): small gold stars with white twinkles sprayed over each sphere, flung up and spinning
    out over a brief gold glow (~16 frames), and a blue-white flash at each star gun's muzzle.
  - **Down tilt** (the low Finger Shot): the Finger Shot's own muzzle puff and the taps' burst along the floor;
    **pummel:** a tap's pop on the held opponent.
  - **Hand Cannon** (back air, down smash, the slow ledge attack): a heavy four-point flash, a hot shock ring
    and a curl of smoke at the muzzle; on each sphere a hot orange-white glow and yellow-orange fire puffs that blacken
    to smoke, rise and linger ~24 frames. Down air was a Hand Cannon column until 2026-09-29; it is now a rocket fist
    (below), trailing Double Punch's exhaust.
  - **The quick ledge attack and the get-ups** fire the Hand Gun's burst (the get-ups' low blast, then its bloom a frame
    later, the star at the far tip), and the slow ledge attack the Hand Cannon's. Their hands show the weapon forms
    while they fire: the Hand Gun a few frames round each shot, the Hand Cannons on both arms from the draw-back to
    after the recoil.
  - **Double Punch's rocket fists** leave an unbroken trail of soft grey exhaust puffs along their flight.
  - **Their sounds end with the moves** (2026-09-29): the Hand Gun a four-shot burst of SMRPG's rattle, the Hand Cannon
    and Star Gun faded out after the boom and the cascade's first two groups (DESIGN changelog).
  - **And land on the shots:** each key transient is within 0.3 frames of the first active frame. The Hand Cannon's
    cock is heard 6 frames ahead (as the arm folds) and its boom on the shot, SMRPG's cock-then-boom rhythm.
  - All of it is round in the stage plane, so it reads the same facing either way.
- **The Finger Shot (2026-09-29, after Michael's "what happened to the finger bullets?"):**
  - A volley of four golden slugs with orange tracers and a warm halo, in SMRPG's pellet colours (SPR0527).
  - A grey mist puff at the fingertips that condenses into a small yellow star.
  - The bullets are at least as thick as their hitbox, so they read at match distance.
- **The Geno Beam (Michael, 2026-09-29):**
  - Blue at every charge level, as in SMRPG. Thickness, and the head's size, are the level cue.
  - It's drawn big: about twice as thick and ~1.45x as long as its hitbox at match distance, like the cast's big
    charged shots. The glow pads the hitbox, which stays as it is.
  - The charge draws energy into the barrel as waves of small stars (projects/geno/fx/efge.py, 22011+).
- **SMRPG's own graphics (Michael, 2026-09-28):** the ROM's sprites and battle effects (the Geno Beam, Whirl, Blast,
  Flash, the timed-hit stars) may serve as direct reference assets and a starting point (traced, their shapes and palettes
  reused, even textures started from them), adapted to Melee's style: higher resolution, Melee's glow, blending, particle
  behaviour and scale in 3D, never a raw 16-bit sprite dropped in. ROM-derived material stays local, like all game data.
- **Look:** Melee's own. Its polygon count, texturing, lighting and model orientation, while recognizably Super Mario RPG's
  Geno. Built in Blender by script, not image-to-3D. Image generation makes style targets only.
- **Orientation (Michael: Samus-style):** the arm-cannon precedent. Samus's neutral is nearly side-on (hips 21°, shoulders
  9°, head 1° toward the camera facing right) with the cannon arm held forward toward the opponent; Geno's gun arm (his
  right) leads the same way, so facing right shows a little of his front. Runs are side-on (the cast: under 5°). The engine
  turns the model to face the other way and never mirrors it, so facing left shows his left side: both halves of the model
  and cape get full detail. Measured in the motion study (`art/motion/MOTION_STUDY.md`), which also sets the animation
  bar: no blending between actions (every move starts or ends exactly on the idle's first frame), the jumpsquat is the
  Landing animation's opening frames, and idle variants play only on menus.
- **Motion:** professional, polished, natural and fluid. A puppet is not an excuse for rough animation, and this is not
  Game & Watch's style.
- **Design source:** the 1996 render's proportions (a big round wooden head, a short jointed doll body, big boots). Design
  details (read from the 2023 art Michael shared; nothing is extracted from the remake):
  - a floppy blue stocking cap that flops back like Link's, with the yellow ribbon emblem;
  - two orange paper curls on the cap's front left;
  - a carved wooden face with seam lines;
  - a jagged blue cape with a yellow collar and lining, fastened by a gold rope through two brass grommets;
  - visible ball joints and wood grain;
  - black eyes (the remake's choice, over the 1996 render's red);
  - the cap at pass B's mid length (longer would be off-model).
- **Style target:** pass B's direction (`art/target/turnaround_b.png`, with black eyes: `turnaround_final.png`). Where the
  target and the remake art disagree, the remake art wins (the target's jaw is a closed square; it shouldn't be).
- **Stance (Michael: side-by-side legs read spindly):** every fighter in the cast except DK staggers its feet in Wait, by
  18-42% of height along the facing axis (median ~31%; Samus 38%, Mario 34%, Fox 29%; `art/motion/fk/*/Wait1.json`). Geno
  takes Samus's: left foot forward (+1.8), right back (-2.0), 2.6 apart, toes out 15°, knees soft, but turned further
  toward the camera than hers (Michael chose B of three in game: hips 25°, shoulders 25°, head 10°; her 20°/9°/1° read as
  full profile on him) (`anims.py` STANCE; the blockout plants the feet by IK). Runs stay side-on; in the air
  the left knee leads.
- **Special effects (Michael, 2026-09-28):** his specials get effects that look like their Super Mario RPG origins: custom
  models on his projectiles and his own particle effect file (`EfGeData.dat`). SMRPG's ROM sprite graphics may be
  direct reference assets to build from, but the result is adapted to Melee's style (resolution, glow, blending,
  particle motion, 3D scale), not raw 16-bit sprites. ROM-derived material stays local.
- **Costumes (Michael, 2026-09-28 and 29):** one costume uses **Mallow's colour scheme** (09-28). The set (09-29): "the 5
  from SMRPG are excellent" (Geno in his party's colours: Geno, Mario for the red team, Bowser for green, Mallow, Peach)
  and a black-and-red **Dark** outfit, a fan favourite, as number 6: black felt, collar and boots, the red on the curls,
  ribbon, lining, clasp, collar piping and soles. A costume recolours the felt, ribbon, curls, clasp and boots only
  (`model/costumes.py`, in OKLab, keeping the texture's shading); the wood, the face and the weapon forms stay. Targets
  are texture colours, judged in game (the lights lift them ~1.2x): Mallow's cap was warmed after the first in-game
  look, where the off-yellow read as white; Dark's boots went black after its first look, where brown boots made it
  read as Geno in a black cape rather than an outfit.
- **Menu art (2026-09-28):** rendered from the production model in game, not painted: the portrait is the Geno Beam's
  charge from 45 degrees in front (heavy-lidded and determined, his look in SMRPG's art, the steel barrel forward),
  difference-matted on black and white renders (`director/portrait_lab.py`, `menus/portrait.py`). Left ungraded: a
  gamma lift toward the cast's brighter menu art washed out the wood.
- **Mouth (Michael):** a puppet jaw, like a nutcracker's. A short stepped groove on top is the mouth; the jaw's two side seams
  drop from its ends and run off the underside of the head. There is **no bottom line**. The long cheek seam under each eye
  also runs to the underside.
- **Cape front (compared with the remake art):** a capelet, not a back cape.
  - Blue panels drape over the shoulders and come forward over the chest's sides, blue face out. They dome, then flare like
    a bell, and hide most of each upper arm from the front.
  - The panels' inner edges start at the throat and angle out, so the chest shows as a narrow opening widening to the belly.
  - The fastening is a short twisted gold rope through two brass grommets set just under the collar, sagging in a small U.
    It is not a chain across the chest.
  - The hem ends at mid-belly in front and lower at the sides, with 3-4 big irregular points per panel.
  - The yellow lining shows only as slivers at the edges.
  - The collar is two tall, stiff yellow flaps rising to mouth height, folding out to points, with blue piping.
  - The torso under it is a smooth wooden barrel (a subtle chest plate, one waist seam), not carved abs.
- **Nose (Michael):** a carved wedge that reads from the front as well as in profile: faceted planes with hard edges catching the
  light differently, a soft shadow under it, no dark triangle painted on the face.
- **Boots (Michael; the target's side view):** a heavy, rounded, Mario-like loaf. A tall, blunt toe box nearly as high as the
  instep, with the sole rockering up a little at the front (not a pointed tip); a thick light tan sole all round; a wide rolled
  cuff flaring out at the ankle; the leg entering the back third, with a short rounded heel.
- **Wood grain:** subtle at game scale. Strong vertical stripes read as striped fabric in game.
- **Cape and scarf:** Melee dynamics chains (ftData+0x2C), no hurtboxes. The precedent: Marth's, Roy's and Ganondorf's
  capes are three 4-bone chains each with none (Fox's tail has one small hurtbox mid-tail).
  - In (`rig/rig.py` DYNAMICS, written by datkit): four chains, the back, the two side panels and the cap's point, tuned
    as felt, not a cloak. The capelet holds its modelled bell at rest, trails about 20 degrees in a run, lifts in a
    fall, swings once on a stop or a turn and settles. The cap's point is the floppy one. Three spheres keep the back off
    the chest, waist and pelvis. In the guard the cap follows the animation, which folds it inside the shield.
  - The chains return to the joints' rest pose, so a model change that moves a chain's joints moves the shape it holds.
    Retune off line with `rig/dynsim.py` on a recorded run, then check in `director/cape_lab.py`.
  - The arms passed through the front panels' surface when they rose (forward tilt, up tilt, up smash, the smash
    wind-up), as Marth's pass through his cape. Arm spheres wouldn't fix it: they steer only a chain's joints, which run
    down the panels' outer edges behind the arms, and the shoulder joint is kept nearly rigid. The fix is in the
    skinning (done 2026-09-29, geno-cannon polish): the panels ride the arm by their distance from it in the design
    pose (`geno_geo.CAPE_ARM`: the dome's rows 0.4 and 0.8 on the upper arm, the skirt 0.2 on the forearm), fitted by
    `model/cape_fit.py` against `model/cape_clip.py`, which measures the panel area inside the arms on every action's
    frames. With an arm raised, the cut area fell from 1.27 to 0.36 square units a frame; static skinning costs some
    arms-down poses (the shield, the item swings, the walk: DESIGN changelog). `GENO_CAPE_GATE2=1` builds the old rule.
- **Sounds:** non-vocal movement sounds for a wooden puppet, synthesized (knocks, clacks, creaks, cape flaps), separate
  from the SNES attack bank. He's silent otherwise. Built (`sound/synth.py`, bank 55 round 4: 550028-550052) and wired
  (`sound/wiring.py`): voice-table slots and first-frame cues are in; the walk and run footsteps wait for the production
  walk and run, since they follow its footfalls.

## Budget (the cast spec, `art/spec/SPEC.md`: 13 fighters measured from the disc)

- **High model** ~4,900 triangles, never over ~5,050 (the cast clusters at 4,600-5,050): head and cap ~1,400, torso and
  collar ~900, a two-layer cape ~400, arms ~550, hands ~750 (jointed fingers), legs and boots ~850. About 40-45 meshes of
  one material each; each mesh skinned to at most 10 bones (the hardware limit), 75-92% of vertices on one bone and the
  rest on two (a wooden doll is mostly rigid parts, which suits this).
- **Low model** ~350 triangles, reusing the high textures plus a small face texture with painted eyes. The game draws it
  only in the off-screen magnifier bubble and in reflections.
  - Built (2026-09-29 polish, geno-cannon): 397 triangles without the cannon (Mario 332, Link 391). The face texture
    (`lowface`, `paint.paint_lowface`) is 64x64 CI8 (4.5 KiB with its palette; Link's low model has two CI8 textures) and
    holds the face only, resampled from the high model's finished face with its eye drawn bold for the bubble's ~7 px a
    unit; the back of the head uses the high `headback` texture and the nose the high nose mesh. CMP smeared the old
    whole-head texture's 9-texel eye (DESIGN changelog has the numbers).
- **Textures** ~30, ~170 KiB in all, CMP (the GameCube's 4-bit compressed format), mostly 128x128 and 64x64, no mipmaps;
  about 37 texels per unit on the face and 30 on the body. Materials as the cast: diffuse and ambient (179,179,179),
  white specular at shininess 50 on about a third of them, texture colour replacing the base; no vertex colours, no
  transparency.
- **Face:** two eye-patch meshes with a 6-frame swapped eye texture (black eyes: open, half-lidded, closed, looking
  aside...); the mouth is static, expressions come from head joints posed by the fighter data.
- **Dynamics chains:** the cape as 3 chains of 4 bones (Marth, Roy), the cap's point as 1 chain of 4 (Link's cap).
- **Skeleton:** his current joints (the gameplay contract) plus the new chains.

## Weapon forms: his hands transform (the model shows it)

From the SNES battles (1996; `art/target/weapons/weapons_snes.png`) and the references Michael sent. Each form is a
model part the move scripts switch to, the way Melee swaps hand poses.

| Form | Look | Used by (sounds already mapped) |
|---|---|---|
| Hand | wooden doll hand: open, fist, point | everything else |
| Finger Shot | every finger and the thumb turn into short hollow wooden tubes, splayed forward | neutral B tap |
| Hand Gun | a slim metal barrel from the hand | forward tilt, forward air |
| Star Gun | a slim barrel firing a stream of small stars | up smash, up air |
| Hand Cannon | the forearm and hand fold open into a wooden barrel with a brass muzzle ring (Michael: wood and brass) | back air, down smash |
| Geno Beam | the hand gives way to a steel barrel with a brass collar and a starry bore, from the forearm | neutral B (charge) |
| Rocket fist | the fist launches on its own and returns (Double Punch launches both) | forward smash, the grab, down air (from 2026-09-29, Michael: straight down and back) |
| Geno Flash | his whole body transforms into SMRPG's blue-and-gold cannon on its wheeled carriage | down B (third star): the body group's option 1 ("Geno Flash's cannon" below) |


### Weapon forms: the interface (Gate 2, projects/geno/model/geno_forms.py; the constants live in rig/rig.py)

The engine shows one **option** per **visibility group** (script command 0x1F "model mod"; decomp `ftAction_80071D40` ->
`ftParts_80074B0C`). Group 0 is the body. Each hand has two groups: an **arm group** (its base meshes at four levels:
forearm + palm + fingers, forearm + palm, forearm, none) and a **form group** (the form's own mesh; option 0 is empty).
A form therefore takes two commands, which `Script.form(side, name)` issues (`rig.form_commands`):

| Form | Form group option | Arm group option (kept) | Joints | Script |
|---|---|---|---|---|
| hand | 0 | 0 (forearm, palm, fingers) | | `s.form('R', 'hand')` |
| fshot: Finger Shot | 1 | 1 (forearm, palm) | HandN | `s.form('R', 'fshot')` |
| gun: Hand Gun | 2 | 0 | HandN | `s.form('R', 'gun')` (with the fist) |
| stargun: Star Gun | 3 | 0 | HandN | `s.form('R', 'stargun')` (the stars are effects) |
| cannon: Hand Cannon | 4 | 3 (none: it replaces the forearm and hand) | ArmJ | `s.form('R', 'cannon')` |
| beam: Geno Beam | 5 | 2 (forearm) | HandN | `s.form('R', 'beam')` |
| rocket: Rocket fist | 6 | 0 | HandN, ArmJ | `s.form('R', 'rocket')`; the launch is HandN's translation in the animation; the fist grows on its hit frames (HandN's scale, `poses_ground.FS_GROW`/`GRAB_GROW`; DESIGN changelog 2026-09-29) |

Groups: the right (gun) hand is arm group 1 and form group 2; the left is 3 and 4. Raw commands: `Script.model(group,
option)` (`7C` + group:7 + option:19; option -1 hides a group), `Script.model_revert()` (0x20, every group to its default).

**Hand and cap poses** (script command 0x29, `Script.part_pose(part, pose, blend)`; decomp `ftAnim_ApplyPartAnim`): part
0 is the left hand, 1 the right hand, 2 the cap. `Script.hand(side, pose, blend)` with poses `fist` 0, `open` 1, `point`
2 and `grip` 3 (fist and open in Mario's order); `Script.cap(pose, blend)` with `rest` 0, `back` 1 (the crown tipped
back) and `low` 2 (pulled down over the eyes). `blend` is the blend length in frames (0 snaps). The poses are rig.py's
HAND_POSES and CAP_POSES; the cap part owns the crown (CapN) only, since its point is a physics chain.

**Persistence:**
- Both reset on every action change. The groups go back to their defaults (every group's option 0: `ftGe_Init_OnDeath`)
  unless the new action is entered with `Ft_MF_SkipModel`; the poses always reset.
- So every action that shows a form or a pose sets it itself, on its first frame, and sets it back when it's done.
- Geno's specials switch between ground and air with `ftGe_MF_Keep`, which skips the new action's commands. A form set
  in a special's ground half is lost when it switches to the air half, and must be set again from C, or the flags
  changed.

**Metal and the magnifier:** the metal model is every group's option 0 (the plain hand), and the low model has no
variants.

**The lab:** `GENO_FORM_LAB=1` turns the taunt into a lab that cycles every form and pose on both hands
(director/form_lab.py).

**Budget:** a form adds 104-180 triangles on its hand (the cannon and beam remove more than they add). The default model
is 5,034. One gun hand makes 5,138 and one star gun 5,178, like Link's and Marth's in-hand alternates; the cast's
largest default models are 5,171 and 5,298.

## Geno Flash's cannon (2026-09-29, geno-cannon)

SMRPG's SPR0030, adapted to Melee and to his materials (`model/geno_cannon.py`; boards from `model/cannon_look.py` and
`director/flash_cannon_lab.py`):
- **The look:** a stout barrel in his capelet's blue, lacquered over eight wooden staves, bound by two brass hoops, with
  the capelet's points where the blue meets the ribbed brass cascabel, a big wooden back (SMRPG's red-brown), a chase
  studded with ten steel studs (SMRPG's grey ones) and a flared brass muzzle round a dark bore; trunnions of brass. Two
  turned-wood wheels in six planks with thick brass tyres, rivets and iron hubs in brass rings (SMRPG's gold half-discs
  with the dark hole); dark wooden cheeks with iron bolts, a bed and a short trail, brass-bound. Scale `rig.CANNON_K`
  1.25: 12.5 long, the muzzle's top ~9 up (SMRPG's is about his height long; ours is about Fox's height).
- **The swap:** visibility group 0 (the body) gets an option 1, the cannon, so one command hides every body mesh, as
  Samus's group 0 option 2 is her Morph Ball; the hand groups go to their empty options (`rig.cannon_commands`). The low
  model and the metal model have the same option 1 (datkit builds a metal model per body option), so the magnifier shows
  the low cannon and a metal Geno becomes a metal cannon.
- **The joints:** `CannonN`, `CannonBarrelN` and `CannonWheelN`, TopN's last children (DESIGN §12 says why they're new).
  Every vertex is rigid on one of them. The barrel joint is unrotated at rest (its pitch is a plain X rotation, clear of
  the Euler gimbal), so the bore runs along its +Z.
- **Budget:** 1,344 triangles high (barrel 720, carriage and wheels 624), 168 low (84 and 84), shown only while the body
  is hidden (the default model is 5,034; the file's high LOD goes 7,350 to 8,694, the low 368 to 536). Two DObjs high, two
  low, one metal. Textures: `fcbarrel` 256x128 and `fccarriage` 128x128, CMP, 24 KiB (the model's 243 to 267 KiB), specular
  (96, 90, 80) and (72, 62, 48) as the brass forms'. Every mesh and texture of the default model and the forms is
  byte-identical to Gate 2's (checked mesh by mesh).
- **Costumes:** the barrel's blue follows the capelet (costumes.py `fcbarrel`, left out of the families' reference so no
  judged costume moves); the brass, the knob and the carriage stay.
- **His hurtboxes follow it** (Michael, 2026-09-29): the hidden body curls into the cannon while it shows
  (`poses_air.curl_pose`), covering 90% of its side silhouette with 11% spill (DESIGN §12 has the numbers and the
  guardrail). The neck keeps the Flash's own place and turn through the curl, so the capelet comes out of the fold as it
  did before.
- **Painted, not image-generated:** `paint.py` `paint_fcbarrel` and `paint_fccarriage` (the wood, brass and felt palettes the
  body uses); its ambient occlusion is baked with the body hidden, and the body's with the cannon hidden.

## Order of work

1. Research: the cast spec (polygon and texture budgets, formats, faces, skeleton and dynamics conventions) and the
   orientation and motion study. In progress.
2. Style target: pass B approved with black eyes (2026-09-27).
3. The model in Blender on the current skeleton, plus the cape and scarf chains and the weapon-form parts.
4. datkit: a skinned-mesh importer (materials, textures, envelopes) replacing the blocks.
5. Production animation for the normals: timing and hit-frame poses locked, remeasured against `research/`.
6. Specials' visuals (the Beam, Whirl, Blast and Flash art; the Geno Flash transformation) once their tuning settles.
