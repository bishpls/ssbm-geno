# Geno's own visual effects: how Melee draws them, and how we add ours

Written 2026-09-28 (branch `geno-fx`). Two routes are proven in game: Geno's own effect file, `EfGeData.dat` (the timed
release's rainbow stars), and the Geno Beam's own projectile model. Everything under `~/games/...` is game data or
ROM-derived and stays local.

## 1. Melee's effect system

**Effect files.** Each series has one (`EfMrData.dat`, `EfFxData.dat`, ...; `EfCoData.dat` holds the common effects).
The decomp lists them in `src/melee/ef/efasync.c` as `efAsync_DatEntries[51]`: slot i is `{file, root name, loaded data}`.
The root, `eff<Name>DataTable`, is three things (HSDRaw `SBM_EffectTable`):

| Offset | What | Format |
|---|---|---|
| +0 | particle bank | `u16 version (0x42), u16 slot, s32 first id, s32 count, s32 offset[count]`, then the generators. Offsets are from the bank's start, and `psInitDataBankLocate` adds the base in place |
| +4 | texture bank | `s32 count, s32 offset[count]`, then groups: `num, GXTexFmt, GXTlutFmt, width, height, u16 palnum, u16 palflag, image offsets[num] (+ palette offsets)`, then the image data (32-byte aligned) |
| +8 | model effects | `EF_EffectDesc[n]`, 0x14 each: `f32 lifetime, JOBJ*, AnimJoint*, MatAnimJoint*, ShapeAnimJoint*`: an animated joint tree, which can also carry particle joints (`JOBJ_PTCL`) that start generators |

**A generator** (`HSD_PSCmdList`, 0x3C bytes plus a command list) is an emitter: its shape (disc, line, tornado, rect,
cone, cylinder, sphere), texture group, emitter life, particle life, kind flags (gravity, friction, prim/env tint,
additive blend, billboarding, trails...), gravity, friction, velocity, radius, spread angle, rate (negative: that many a
frame), size and shape parameters. Each particle then runs the **command list**, a small bytecode interpreted every frame
(`sysdolphin/baselib/particle.c` `hsd_8039930C`; HSDRaw's `HSDRawViewer/Scripts/ptcl.yml` names every opcode): waits, the
texture frame (`0x40`), position and velocity (`0x80-0x9F`), size over time (`0xA0`), gravity and friction, child particles
and generators (`0xA4`, `0xA5`, `0xEF`, `0xF0`), random speed and rotation, prim and env colour over time (`0xC0`, `0xD0`),
loops and marks, and `0xFF` to end.

**How a particle is drawn** (`psdisp.c`, `psdisptev.c`): a textured quad (or point or line) facing the camera. With the
prim/env tint on, its colour is `lerp(env, prim, texture intensity)` and its alpha `lerp(env.a, prim.a, texture alpha)`. So
Melee's textures are mostly white intensity-and-alpha images (IA4, IA8, I8), coloured per particle. Env alpha must be 0 or
the texture's alpha is ignored: our first build drew opaque squares for exactly that reason. Blending is normal or additive.

**Ids.** An effect id is slot × 1000 + n. For a generator, n indexes the slot's particle bank, whose first id is its slot ×
1000. For a model effect, `id % 1000` indexes the table's models (`efLib_Create`). Many ids a move script uses aren't
direct: `efSync_Spawn` routes ids below 0x250 and the stage's bank (30xxx) straight to generators, and the rest (0x250-0x512)
through hand-written cases (`efAsync_Dispatch`, `efAlt_Spawn`, `efSync_Spawn`'s switch) that pick generators and models
from the per-series files. That's why the common "stars" 1010-1012 are dispatch cases (generators 331, 11 and 72 of
`EfCoData.dat`).

**Spawning.** From a move script, the graphic-effect command (datkit's `gfx`; `ftAction` then `ftCo_8009F834`) spawns at a
bone with an offset and a random range. From code, `efSync_Spawn(id, gobj, ...)` or the `efLib_Create*` and
`efLib_CreateGenerator*` family (at a position, attached to a joint, facing, scaled). Fighters queue theirs through
`efAsync_Spawn` during logic and flush them later.

**Loading.** Per fighter kind: `ftData_UnkBytePerCharacter[kind]` is the slot. The fighter preload queues it
(`efAsync_LoadAsync`, `lbDvd` type 3, into the preload heap with the fighter's files), and fighter creation loads it
synchronously (`efAsync_LoadSync`, which registers the particle and texture banks as bank `slot`). `EfCoData.dat` (slot 0)
and the menu's (31) load per scene. Kirby's copies have their own slots (32-48). The particle system has 65 banks: 30 is
the stage's, 64 the stage's second.

**Free slots.** Slots 22-29, 35, 40 and 42-45 are empty (30 is taken by the stage's particle bank). That leaves 14 new
series files of 1000 ids each.

## 2. What HSDRaw reads and writes

- It reads and writes all three parts: `SBM_EffectTable`, `HSD_ParticleGroup` (generators with raw command lists; its
  setter lays out the offsets), `HSD_TEXGraphicBank`/`HSD_TexGraphic` (`SetFromTOBJs` encodes frames), and the model
  effects as ordinary joint trees and animations.
- `HSDRaw.Tools.ParticleEncoding` encodes and decodes the command lists. Its decoder misprints partial colour masks (`C8`),
  but the bytes are right.
- Its viewer (`HSDRawViewer`, Windows) has a particle editor and renderer. We don't need them: datkit does the rest.

Our tools:
- **`datkit ef-dump FILE [--gen ids] [--tex DIR] [--models]`**: any effect file, generators with their command lists
  decoded, texture groups as PNG.
- **`datkit ef-build SPEC.json OUT.dat`**: builds one from a spec (`projects/geno/fx/efge.py` writes it).
- **`datkit art-dump PlXx.dat N [--verts]`**: an article's model, materials, blending and state animations.

## 3. Route 2: Geno's own effect file (proven)

- **Decomp** (`geno-fx`, all inside `#ifndef MUST_MATCH`; the matching build still matches):
  - `EfGeData.dat` / `effGenoDataTable` is slot 22 (`EF_GENO_BANK`), and Geno's `ftData_UnkBytePerCharacter` entry is 22.
  - The file is looked for once, and a disc without it plays him with no effects of his own (`efGe_Loaded()`), which is
    tested.
  - `efSync_Spawn` and the move scripts' graphic-effect command take 22000-22499 as his generators, and 22500+m as his
    model effect m.
  - The Beam's timed release spawns generator 22000 at the barrel (`ftGe_BeamTimedCue`; Kirby's copy at its hand).
  - Verified: the burst in game (Geno's and Kirby's copy's, `fx_lab`, `timed_lab`), the missing-file fallback, the
    matching check, and an empty remeasure diff. Wired but not yet exercised: the model-effect ids (22500+m) and the
    move-script path (no script spawns a 22xxx id yet).
- **Content** (`projects/geno/fx/efge.py`, our own art drawn in code):
  - 3 IA8 texture groups: a plump SMRPG five-point star, a four-point flash and a twinkle cross.
  - 11 generators. 22000 is a root particle that starts the rest where it stands: eight ring generators, one per rainbow
    colour in SMRPG's order (the defeated-enemy star burst, SPR0516), a flash that turns into an X (SMRPG's three-frame
    flash), and six white twinkles (the come-back star's, SPR0522, drawn with the timed-hit "ding").
  - The file is 20 KB.
- **Build and install:** `.venv/bin/python projects/geno/fx/efge.py --install` (to `$MELEE_DISC/files/`).
- **Check:** `director/fx_lab.py`. Each segment opens with a two-frame magenta sync slate; `fx/fxstrips.py` and
  `fx/fxreel.py` line every segment up on its own slate (`fx/fxsync.py`) and print each segment's drift, and the reel's
  audio is cut by logic frame, because Dolphin's dump can drop images on heavy frames. Checked: Fox's hit spark first
  shows on the image of the logged hit frame (596) in both the before and after runs.
- **The charge's draw-in** (2026-09-29, Michael's concept):
  - **Generators** 22011+3(L-1)+k: an inner arc, an outer arc and the tip's flare, for a wave landing at star L.
  - **Shape:** a disc with a fixed (negative) radius and a spread angle of 3π/2 emits on its arc with the velocity pointing
    at the centre. Every star of an arc therefore reaches the centre on the same frame (9).
  - **Spawning:** `ftGe_BeamDrawIn` (decomp) spawns the three on the hand joint with
    `efLib_CreateGenerator_Attach_AddAppSRT`, sets their centre to the barrel's tip in the joint's space, and mirrors the
    arc when he faces left.
  - **Why the stars follow the barrel:** an AppSRT generator carries its joint's position to its particles, and the
    engine keeps the generator alive while any of them live (`hsd_8039D3AC`). Only the position is carried, not the
    scale (`0x1000` unset), so a grown hand chain doesn't scale the stars.
  - **Budget:** 3 generators a wave, and at most ~14 live particles.
- **Measuring projectiles** (`director/scale_lab.py`, `fx/scalemeasure.py`):
  - One camera at match distance, run twice: drawn on black (coll 0), then as collision capsules only (coll 2).
  - Each projectile's glow, core and hitbox are measured in units, from the same frames of both runs.
  - Pixels are square (13.15 px/unit at res 2), calibrated by the Beam's known speed.
  - The capsules are drawn swept across one frame's travel, so a hitbox's instantaneous length is its drawn length
    less the speed.
- **Generators by name** (2026-09-29): nothing refers to a generator by its number.
  - `efge.py` builds the list: Geno's specials' generators first, then each extension module's (`EXTENSIONS`: the
    normals' and aerials' `efge_normals.py`). Extension ids follow the specials', so adding to either never moves
    anyone else's. A duplicate name fails the build.
  - **In C:** `efge.py --c src/melee/ft/kinds/ftGeno/ftgeno_efge.h` writes a generated header with `EFGE_<NAME> <id>`.
    Include it and spawn with `efSync_Spawn(EFGE_<NAME>, gobj, &pos)`.
  - **In move scripts:** `efge.gid('<NAME>')` gives the id at build time (for datkit's `gfx`).
  - **Extension modules** define `TEXTURES`, appended after `efge.py`'s, and `generators(tex, first_id)`. `tex` maps
    every texture group's name to its index; `first_id` is the id their first generator gets, for a root that spawns
    its children by id.
  - Rerun `--c` and the build after any change to either list. For a merge of two lanes' additions, just rerun.
- **The Finger Shot** (2026-09-29, `fx/finger_model.py`, `director/finger_lab.py`):
  - **The model:** four bullets, each a child joint of the root placed on one of the donor laser's four hitbox spheres
    (z −0.78, −3.64, −6.51, −9.38, radius 1.17).
  - **In flight:** the laser code's growth of the root (up to 3x along Z) strings them out with their hitboxes, and
    `itGe_Finger_Anim` undoes the growth on the bullets themselves so no head is squashed.
  - **The muzzle puff:** `FINGER_PUFF` (a mist and a star), spawned by `ftGe_FingerPuff` for Geno's shots, Kirby's
    copy's and the down throw's.
- **Article models with nested joints:** a joint with a translucent mesh anywhere below it needs `ROOT_XLU`, or the
  renderer skips that subtree in the translucent pass. `ArticleModel.cs` sets it up the chain. The Whirl's disc, two
  joints down, didn't draw until it did.
- **Camera-facing joints** (`"flags": ["VBILLBOARD"]` in an article model's spec) turn about Y to face the camera,
  which suits columns and beams. Hide one with `HSD_JObjSetFlags(j, JOBJ_HIDDEN)`, never with scale 0: the billboard
  matrix divides by the joint's own axis lengths, so 0 gives NaNs and it draws anyway. In a state's animation use a
  tiny scale (0.001) for "off".

- **The gun normals' bursts** (geno-fxnormals: `fx/efge_normals.py`, spawned by `rig/moves.py`'s `burst_fx` and
  `muzzle_fx`):
  - A move script spawns, on a gun blast's hitbox frame, one burst per hitbox sphere at the sphere's own TopN offset and
    a flash at the barrel's tip (`moves.MUZZLE`). A script spawn shows on the hitbox's first frame (measured).
  - Each burst is round in the stage plane (disc emitters with the axis toward the camera, drifting up), so no
    facing-aware spawn is needed: TopN's offset carries the facing.
  - Names: `N_<FORM>_<radius class>` (GUN, TAP, STAR, CANNON; classes 3.0, 3.6, 4.4, 5.2), `N_GUN_TIP_<class>` (the
    tip's star), `N_<FORM>_FLASH` and `N_EXHAUST` (a rocket's exhaust puff; `moves.exhaust_trail(s, a, b)` lays them
    along a frame's flight from a to b, 2.2 units apart at most, so the trail is unbroken at any speed: Double Punch
    spawns 22). Particles: a Hand Gun burst 5 (6 at the
    tip), a Star Gun spray 8, a Hand Cannon burst 6 and its muzzle 5. Per move, the up smash is the most at ~48 (the
    ceiling), then the get-ups ~44, the up air ~40, Double Punch's exhaust 22, the down smash ~22.
- **Measuring melee disjoints** (`director/gunfx_lab.py`, `fx/gunfxmeasure.py`): a coll 0 run on black and a coll 2 run
  of the same segments. For each frame with a hitbox, along the move's axis: the hitboxes' reach past the hurtboxes
  (the disjoint), how far anything drawn reaches past them, and the share of the disjoint hitbox area that's drawn
  (cover).
  - Make the capsule run without the performer's own effects (for Geno, no `EfGeData.dat`), since effects draw over
    capsules. A cast member's effects can't be removed, so their hitboxes are hull-filled.
  - `--overlay DIR` writes each segment's frames with the hitbox and hurtbox outlines, to check the masks.
- **The forward throw's Rocket Fist** (2026-09-29): `ROCKET_LAUNCH`, a small white four-point star at the wrist on the
  ignition (frame 18), and the Double Punch's exhaust (`moves.exhaust(s, 'R')`: `N_EXHAUST` at the flying fist each
  frame out, 18-22, and back, 28-32).
- **To add an effect:** add a generator in `efge.py`, spawn it from C with `efSync_Spawn(EF_GENO_GEN(n), gobj, &pos)` or
  from a move script with `gfx` id 22000+n. A model effect goes in the table's model list: datkit `ef-build` clones one
  from another file today; our own would reuse `ArticleModel.cs`.

## 4. Route 1: an article's own model (proven on the Geno Beam)

- **datkit `ArticleModel.cs`** builds an article's model from a spec, the way fighter-build builds his body:
  - joints;
  - meshes as triangle lists with vertex colour and alpha and optional UVs;
  - textures (any GX format);
  - the donor laser's two material setups (additive, and plain translucent), unlit;
  - each state's joint animation (looping tracks);
  - the item bone table, so a hitbox can ride a joint.
- `projects/geno/rig/articles.py` hands the spec to fighter-build (`model=`), and `GENO_BEAM_MODEL=0` builds the donor's.
- **The Geno Beam** (`projects/geno/fx/beam_model.py`):
  - **The look:** SMRPG's (the attract demo's Beam, and the ROM's five Beam effects EF0086-0090): a white core, a thin
    cyan rim, a soft blue glow, and a round bright end with a four-point flare.
  - **The build:** flat textured ribbons facing the camera, since the SNES draws it flat. The first pass, faceted shells
    like the laser's, read as a crystal lance.
  - **Joints:** root, trail and head.
  - **The item code** (`itGe_BeamRay`, decomp) turns the root along the flight like the laser's, stretches only the trail
    (the head keeps its shape), and scales both by the level.
  - **The hitboxes:** four spheres on the trail joint (bone 1), so they spread with the drawn beam and none sits behind the
    barrel at the spawn. Falco's laser has its trailing spheres ~9.5 units behind the muzzle on its first frame.
  - **Size:** following Michael's note, 12% thicker (2.2, 2.9, 3.8) and longer (to ~17.7 units at three stars), padded by
    the glow (half-width 4.8).
  - **Damage** is unchanged (6, 11, 17; 18.7 timed).

## 5. Limits

- **Memory.** Effect files load into the preload heap with the fighter's files. Vanilla series files run from 5 KB (Peach)
  to 163 KB (Falcon); ours was 20 KB, and is 117 KB since the Flash's fireball became the sun (2026-09-29: three
  64×64 RGBA8 frames, 48 KB, and the red flash's silhouette, 8 KB), between Pikachu's 114 KB and Fox's 124 KB.
  Textures dominate: a 64×64 IA8 frame is 8 KB, RGBA8 16 KB, CMP 2 KB. Keep his under ~150 KB.
  The Beam model adds 3 RGBA8/IA8 textures (~40 KB) to `PlGe.dat`.
- **Ids.** 1000 per slot, and ours are split 500 generators / 500 model effects. The generator id is a u16 in the child-
  spawn opcodes, which is fine. Slots: 14 free.
- **Counts.**
  - Particles and generators come from heap pools, not fixed arrays.
  - Model effects spawned through the async path are capped at 64 live, and the oldest is removed.
  - The timed burst is ~16 particles for ~30 frames, cheap next to Fox's or Ness's.
  - Translucent fill rate is the real cost: keep big additive quads (a Geno Flash sun) short-lived, as PK Flash's are.
- **Loaded only with Geno.** Bank 22 exists only when Geno is in the match. Kirby's copy spawns only then, and every spawn
  checks `efGe_Loaded()`.
- **Replays and netplay determinism:** particles use the game's RNG (`HSD_Randf`), as every vanilla effect does.

## 6. What each special would take (estimates, one session each unless noted)

| Special | SNES reference (local board) | Work | Size |
|---|---|---|---|
| Beam + timed stars | attract demo capture; EF0086-0090; SPR0516/0522/0798 | done: the timed stars, the charge's draw-in (2026-09-29), the bigger Beam drawn by level. All blue at every level (Michael: as SMRPG). Left, optional: the charge's red star counters over his head (SPR0798) as particles on the three star frames | 0.5 day |
| Finger Shot | SPR0029, SPR0527 (the pellet, and the mist that forms a small star) | done (2026-09-29): four golden slugs on the laser's four hitbox spheres, the muzzle puff | |
| Whirl | captured: the white-yellow disc streaking out with a trail of fading yellow ovals; a blue screen flash on the timed press; the hit explodes (SPR0517); EF0032 | done (2026-09-29): `fx/whirl_model.py` (a bladed disc, tilted, spun by state; aura), efge `WHIRL_RING` / `WHIRL_HIT` / `WHIRL_GRIND` / `WHIRL_CRIT`, spawned by the item code (`itGe_WhirlLook`, the hit callbacks); a spiked sun 2026-09-30 (Michael, after the remake's): small straight spikes round its rim, rotating, the trail's rings spiked too (`spikering`); its angle to the camera `whirl_model.LOOK` | |
| Blast | captured: blue sparkles at his hand, then flat columns of colour drop from the sky, each landing in a white cloud; SPR0532 | done (2026-09-29): `fx/blast_model.py` (the mark's floor oval and tell beam, one camera-facing column per SMRPG colour; the item code shows one, hidden by flag), efge `BLAST_CAST` / `BLAST_TELL` / `BLAST_LAND`; richer 2026-09-30 (Michael): three layers a column (glow, banded band, core), a shimmer, a foot flare, a taller fall; SMRPG's shaded cloud (texture group `cloud`) and a floor ring (`BLAST_LAND_RING`, `floorring`); over the void (`itGe_BlastOnFloor`) the oval and flare hide and a tail fades the column out, no cloud; the tell breathes over a long hold, and `itGe_BlastVanish` (`BLAST_VANISH`) is a cancelled mark's exit | |
| Star Road | none in SMRPG (the cannon launch) | done (2026-09-30, Michael): no-damage stars (`SR_BURST` 5 from each hand at the launch, `SR_TRAIL` one from his waist every 3 flight frames; 16 in all, at most 15 live), cream-white with a blue rim, spinning; `rig/moves.py` `s_launch` | |
| Flash | captured: a yellow glow as he becomes the cannon on its carriage, a fireball, a giant spinning star with a face that rounds into a sun, the screen flashing red; SPR0030, SPR0565. Michael's reference for the sun: the 2023 remake's (refboard/remake_sun_reference.png, local; studied, nothing taken) | done (2026-09-29); redone the same day on Michael's review: one sun for the whole move (`fx/flash_model.py`: a haze, two corona layers of flame tongues turning opposite ways and flickering, a disc with the remake's small surprised face as vertex-coloured geometry; camera-facing RBILLBOARD joints scaled by the item code, `itGe_FlashLook`, to 0.98x the hitbox's radius), the fireball the same sun small (efge `FLASH_FIREBALL`, texture group `sunball`), efge `FLASH_GLOW` (the move script), `FLASH_END` (the red flash: the sun's silhouette, texture group `bloom`), `FLASH_FINISH` (the finishing flash as the sun ends: `FLASH_FIN_STAR`, a glowing star, texture group `starflash`;
`FLASH_FIN_RING`, a round ring, `sunring`; `FLASH_FIN_SPARKS`, the gold stars; at the end of the specials' list),
`FLASH_BURST` (the burst's white heat over
the sweetspot's 8 frames, spawned with the sun; it took the unspawned `FLASH_RING`'s slot, so no id moved). Measured frame by frame against the hitbox: `director/flash_scale_lab.py`, `fx/sunmeasure.py`, `fx/sunchart.py` | |
| Flash's full-body cannon | SPR0030's frames | done (2026-09-29, geno-cannon): the body group's option 1 (`model/geno_cannon.py`, three joints of its own, `poses_air.cannon_pose`); the fireball leaves its barrel (`ftGe_FlashMuzzle`); DESIGN §12 | |
| Throw stars (up throw) | SPR0798, SPR0779; the demo's Star Gun (refboard/stargun_frames.png) | done (2026-09-29): a gold star on the Beam model's fourth joint (RBILLBOARD, spun by state 3's animation), shown only in the throw's state (`itGe_BeamParts`), a sparkle trail (`THROW_STAR_TRAIL`), the Star Gun's muzzle `N_STAR_FLASH` | |
| Muzzle flashes (normals) | SPR0527 | 2-3 generators (gun, star gun, cannon) replacing 1043 smoke / 1062 spark in the move scripts | 0.5-1 day |

## 7. Reference material (local only)

- **SNES capture tooling** (`~/games/smrpg/work/fx/`):
  - `drive_fx.lua` runs Mesen headless with screenshots over frame ranges.
  - The attract demo reaches a Geno Beam battle at frame ~27270, and again at ~43800.
  - The demo's battle is canned (patching Geno's starting spells changes nothing), but it casts spell 16 through the ally
    spell queue table at 0x35C992. `smrpg_spell16_{whirl,blast,flash}.sfc` are local ROM copies with that pointer set
    to spell 18, 19 or 20's, so the same demo battle casts the Whirl, Blast or Flash (reference captures only; the
    scene starts ~160 frames later, at ~27430).
- **Decoders** (repo, read the local ROM and disassembly):
  - `projects/geno/fx/smrpg_sprites.py`: battle sprites (molds and sequences, ROM palettes).
  - `smrpg_effects.py`: battle effects (a Lazy Shell port).
- **Boards:** `~/games/melee/sandbox/geno-fx/fx/` (sprites, effects, vanilla effect textures) and `boards/` (in game).
