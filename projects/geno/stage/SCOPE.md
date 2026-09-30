# Forest Maze: the technical scope

What adding a new stage to Melee takes, worked out from the decomp (`src/melee/gr`, `mp`, `mn`, `gm`, `lb`) and the
disc's stage files, with the pipeline planned by analogy with Geno's (`datkit fighter-build` from a spec and a glTF).
The design sketch is DESIGN.md; the measurements are `research/starters.md`.

## 0. Summary

| Piece | What it is | Estimate (agent-days) | Risk |
|---|---|---|---|
| Stage kind and tables | GrKind 0x47, a new StKind (286), `stage_datas` / `stage_id_map` / sound rows | 0.5 | low |
| Stage code | `grforest.c`: StageData, callbacks, OnInit (points, camera, blast zones); static, no hazards | 0.5 | low |
| `stage-build`: collision, points, params | datkit, from the stage spec (`layouts.py`), GrNBa.dat as the template | 1-1.5 | low (probe below) |
| Greybox model | the spec's outline extruded into boxes, per-part colours, one light | 0.5-1 | medium (static-mesh import) |
| Selection | an SSS slot: icon, name, preview, cursor box, random list | 2-3 | **high** (the SSS is a fixed grid in one model) |
| Music | the loop cut, variable HPS blocks, HPS id 0x64, the stage's music row | 1 (after Michael's pick) | low |
| Production art | stump, boughs, trunks, mushrooms, canopy, 3-4 background layers, fog, lights; Melee's look | 5-8, plus review rounds | medium (look under Melee's lighting) |
| Ambient effects | falling leaves (stage particles), light shafts | 1 | low |
| Records, random switch, counts | `mnstagesw` 29 → 30, `mncount`, `mndatadel`, `stage_mask` bit 29 | 0.5 | medium (hard-coded 29s) |
| **To the greybox milestone** | §5 | **about 3-4** | |
| **To a finished stage** | | **about 12-18** | |
| On hold | single-player modes; Japanese menus (`MnSlMap.dat`, the name texture) | about 0.5 each | |

The feasibility probe (Part D, §6) retired the biggest pipeline risk:
- a stage file written back through HSDRaw loads and plays identically (6/6 checks on the round-tripped Battlefield);
- a platform moved in collision and model together lands a fighter on the new height, and the model moved with it.

## 1. How the engine holds a stage

- **Two kinds.** `StKind` is the stage as chosen: 286 values, VS stages 0x00-0x20, then single-player and event
  variants. `stage_id_map[StKind]` gives the `GrKind`, the archive: 111 kinds, `gr/forward.h`. `stage_datas[GrKind]` is
  the `StageData` in the DOL (`ground.c`):
  - its callbacks per map gobj;
  - the archive's name (`"/GrNBa.dat"`);
  - `on_init` / `on_load` / `on_start` / `on_demo_init`;
  - `on_touch_line` and `on_check_shadow_render`;
  - an optional code-side collision binding table.
- **Loading** (`grDatFiles_801C6038`). The archive's `map_head` is required, and `grGroundParam` is required in
  practice. Everything else is optional and null-checked: `coll_data` (without it, a default collision loads),
  `itemdata`, `ALDYakuAll`, `map_ptcl`/`map_texg` (the stage's particle bank), `yakumono_param` (stage-code tuning),
  `map_plit` and `quake_model_set`.
- **Per-StKind parameters.** `grGroundParam` holds one row per StKind the archive serves: the music, the item-frequency
  multipliers and the sudden-death music. **A missing row hangs the game** on load ("not found stage param in DAT",
  `Ground_801C28CC`). The new file must carry a row for the new StKind.
- **Map gobjs.** `map_head.ModelGroups[i]` is map gobj `i`: a joint tree with meshes, its joint, material and shape
  animations, and optionally its own camera, lights, fog and collision links. The stage's code creates the ones it uses
  (`Ground_801C1A20`), each under a root scaled by `grGroundParam`'s stage scale.
- **General points.** `map_head.GeneralPoints` is a list of joint trees with (joint index, point type) pairs. Joint
  indices count depth first from the tree's root = 0, not entering an INSTANCE joint's children (`Ground_801C34AC`). The
  types:
  - 0-3 spawns, 4-7 respawns (5-7 fall back to 4);
  - 127-146 item spawns;
  - 148 the camera centre, 149/150 the camera range's corners, 151/152 the blast zones' corners;
  - 199-208 targets, 252-259 bumpers.
  - At init the stage code calls `Ground_801C39C0` (the camera range, relative to 148) and `Ground_801C3BB4` (the blast
    zones). **Without point 148 the engine ignores 149/150 and uses a default range**, ±170 / 120 / −60. Pokémon Stadium
    does this, measured in game.

## 2. The pieces

### 2.1 Stage kind and table entries (decomp, all inside `#ifndef MUST_MATCH`)

- `GrKind` **0x47** (`Gr_Kind_ForestMaze`): `stage_datas[0x47]` is currently a `grTe_StageData` filler. Point it at
  `grFm_StageData`.
- `lbAudioAx`'s stage sound table (`s32_arr_803BB6B0[0x6F][3]`, indexed by GrKind) already has a row 0x47. Set it:
  - [0] is the stage's sound-bank bit, 55 for none; a forest ambience bank is optional.
  - [1] and [2] are the reverb settings.
- `StKind` **286** (0x11E, `St_Kind_ForestMaze`), appended to `stage_id_map` (286 entries today) → `Gr_Kind_ForestMaze`.
  To check at build time: every table indexed by StKind, and `u16` storage (fine).
- **Unlocks:** none needed. `gm_80164430` returns true for any GrKind outside the 11-entry unlockable table.
- The director's `dsl.STAGE` gets `forest_maze: 286`, and labs can pick it the day the file exists.

### 2.2 The map file (`GrFm.dat`)

The roots, as the vanilla starters carry them (datkit `stage-dump` lists them):
- `map_head`;
- `coll_data`;
- `grGroundParam`;
- optional: `itemdata`, `ALDYakuAll`, `map_plit`, `map_ptcl` + `map_texg`, `quake_model_set`, `yakumono_param`.

A static starter needs `map_head`, `coll_data` and `grGroundParam`, plus `map_ptcl`/`map_texg` if leaves fall.

Map gobjs, following Battlefield's arrangement (7 gobjs, 452 KB):

| gobj | Content | Code |
|---|---|---|
| 0 | the general points' joint tree (no meshes; Battlefield's 22 joints) | `grAnime_801C8138` |
| 1 | the main stage and platforms (the play plane), bound to the collision | `Ground_InitMapCollAndAnim` on init, `Ground_UpdateMapColl` each frame (Battlefield's gobj 6; its flags `(1<<30)\|(1<<31)`) |
| 2-4 | background layers (trunks, canopy, far haze), each with its own fog and lights, some with slow joint or material animation | `grAnime_801C8138` + `grMaterial_801C94D8` |

The vanilla starters' budgets:

| Stage | File size | Gobjs | Meshes (DObjs) | Textures |
|---|---|---|---|---|
| Final Destination | 611 KB | 10 | 92 | 68 |
| Battlefield | 452 KB | 7 | 61 | 49 |
| Yoshi's Story | 825 KB | 4 | 195 | 171 |
| Dream Land | 657 KB | 8 | 79 | 84 |
| Fountain of Dreams | 1,119 KB | 5 | 197 | 193 |
| Pokémon Stadium | 1,469 KB | 3 | 122 | 115 |

(Stadium's transformations live in `GrPs1-4.dat`.) The Forest Maze should stay within the starters' range, about 1 MB
and 200 meshes: the stage shares memory with four fighters.

### 2.3 Collision

`coll_data` (HSDRaw `SBM_Coll_Data`; the engine's `MapCollData`, `mp/types.h`) holds:
- **Vertices** (x, y), in stage units: world ÷ stage scale.
- **Lines**, sorted into five contiguous ranges: floors, ceilings, right walls, left walls, dynamic. Each line has:
  - two vertex indices;
  - `prev` and `next` links to the lines it joins. At +4 and +6: **HSDRaw names these the other way round**; our tools
    use the engine's names;
  - alternate-group links (−1 when unused);
  - a surface kind: 1 floor, 2 ceiling, 4 right wall, 8 left wall;
  - a property byte: 0x01 pass-through, 0x02 ledge. The live flags show them as 0x100 and 0x200;
  - a material (sound and effects: Basic, Rock, Grass, Wood...).
- **Line groups** ("joints" in the engine): per group, the index and count of each kind of line, a bounding box, and a
  vertex range.
  - A map gobj's `CollisionLinks` (group, −1, joint index) binds a group to a joint. Its vertices are then in that
    joint's space and follow it (`mpLib_80055E9C`: vertex × joint matrix): the moving platforms.
  - Stage code can bind groups too (`StageData.joints`, Fountain of Dreams' `grIz_803E0D60`).
  - A static stage binds its groups to the stage gobj's root, or leaves them unbound. Unbound vertices are world ×
    stage scale.
- **Winding** (read from the six starters):
  - floors run left to right;
  - right walls top to bottom;
  - left walls bottom to top;
  - ceilings right to left.
  - The solid is on the right of each line's direction.
- **Grabbable ledges.** A floor line carries the ledge flag; its end that meets a wall is the corner a fighter hangs from.
  - The vanilla stages flag only the short end segments (Final Destination: 10.57 at each end; Battlefield: 8.4), and
    split the floor there.
  - The lab reads the corner the engine uses: `mv.co.cliff.ledge_id` in CliffWait, then that line's outer vertex. It
    matches the file to 0.001 on all six starters.
- **Pass-through platforms.** Floor lines with the pass-through property, `prev`/`next` −1, top surface only. A fighter
  lands from above and drops through with down.
- **Islands.** `mpIsland` builds connected floor chains at load (for the CPU and ledges): a main stage must be one
  chain, ledge to ledge.

What stage-build writes from the spec:
- vertices and lines in the engine's order and winding, the links, flags, materials, ranges and groups;
- group bounds;
- the ledge split;
- every value checked against `stage-dump` of the result and the in-game GRDUMP (§4).

### 2.4 Camera, blast zones, spawns, items

- **General points** (§1): one joint tree, root at 0, a child joint per point. It carries:
  - 148, 149, 150 (camera);
  - 151, 152 (blast zones);
  - 0-3 (spawns), 4-7 (respawns);
  - item spawns 127+. Battlefield has 8; `Stage_80224FDC` picks among them.
- **`grGroundParam`:**
  - stage scale (1.0 for ours);
  - the camera's fov, distance range, tilt and pan, track ratio, smoothing, pause-camera limits, and fixed-camera
    pose. Start from Battlefield's and tune in game;
  - item spawn weights per item (0x68-0xAE; items are off in competitive play);
  - the per-StKind rows (§2.7);
  - bubble (off-screen indicator) colours.

### 2.5 Lighting, fog, backgrounds

- **Lights.** Each map gobj carries `HSD_Light`s (Battlefield: 2 per gobj, Final Destination 2-3). `map_plit` holds the
  lights the fighters are lit by (`Ground_801C49B4` returns it, or a default set; `ftCo_09F4.c` builds the fighters'
  lights from it). Fighters take their lighting from the stage: a warm key from above left through the
  canopy, a cool fill, and ambient green bounce. Judge them on Geno and the cast in game, as the model's materials were
  (Melee brightens textures ×1.2 on the lit side, HANDOFF §5).
- **Fog.** `HSD_FogDesc` per gobj (type, start, end, colour). The background layers fade into warm green haze; the play
  plane has none.
- **Backgrounds.** Real 3D depth: layers at increasing z, so the match camera's moves give parallax for free. A gobj with
  its own camera (`callbacks[i].flags_b2`) renders as a separate backdrop (a skybox); the canopy could use one.
- **Performance.** No reflections (Fountain's lesson), few translucent layers, and textures sized to Melee's (Battlefield
  49 textures). Dolphin shows a missed frame as two logic frames per image, and the director's frame-sync hook drops
  them. A measure for heavy frames is to do.

### 2.6 The stage's own code (`gr/grforest.c`)

From `grbattle.c` (436 lines), minus its background-swap state machine. What a static starter needs:
- a `StageData`: GrKind 0x47, callbacks, `"/GrFm.dat"`, `OnInit`, `OnDemoInit`, `OnLoad`, `OnStart`, `callback4`
  (false), `on_touch_line` (NULL), `on_check_shadow_render` (true) and `flags2` 1;
- `OnInit`:
  - create gobjs 0, 1 and the background layers through the Battlefield pattern (`grBattle_80219D84`);
  - `Ground_801C39C0()` (camera);
  - `Ground_801C3BB4()` (blast zones);
  - `grLib_801C9A10()`;
- per gobj: init (`grAnime_801C8138`, or `Ground_InitMapCollAndAnim` for the play plane), a proc
  (`Ground_UpdateMapColl` for the play plane), and empty callbacks.

What a static starter leaves out:
- `yakumono_param`;
- hazards;
- `on_touch_line` (it returns a DynamicsDesc for surfaces that push fighters);
- the random background swaps;
- the demo-fight placement (BF places the four points for the title demo);
- `grZakoGenerator` (Multi-Man Melee's wire frames);
- any code-side collision bindings.

About 150 lines, all in a new non-matching file, plus the `configure.py` entry.

### 2.7 Music

- **An HPS id past the table,** as the fanfare did:
  - `hps_files[]` gets `"gr_forestmaze.hps"` at 0x64 (0x63 is `ff_geno.hps`);
  - `lbAudioAx_80023F28` resolves it and falls back to Battlefield's `sp_zako.hps` when the disc lacks it.
- **The stage's music row** in `grGroundParam`:
  - StKind 286;
  - `bgm` = 0x64;
  - `bgm_alt` = the other arrangement (0x65) with a chance, or −1;
  - sudden-death ids;
  - the behaviour flag. Behaviour 0 plays the main song only; Battlefield uses 6, alt at 12%, gated on `gm_80164ABC`.
- **The stream itself** (DESIGN §7): a loop cut of the chosen arrangement, 32 kHz DSP-ADPCM, with the loop start on a
  downbeat.
  - The vanilla stage streams vary their block sizes to put the boundary where the loop needs it; `hps.py` must learn
    that (0.5 day).
  - The stage list's music is in a table of its own; the Sound Test's song list is optional.

### 2.8 Selecting it: the stage select screen

**`mnstagesel.c`.**
- `mnStageSel_803F06D0[30]`: 29 stages plus random. Per entry: the icon joint, a state, the icon's animation frame, an
  index into the random list, the StKind, and the cursor box's half-extents and scale.
- The layout is fixed:
  - 11 stacked pairs of icons (22 stages);
  - 5 "special" icons (the past stages);
  - 2 large icons (Battlefield, Final Destination);
  - Random.
- `NUM_STAGES 29`, and 0x1D / 0x1E appear as bare numbers throughout.

**`MnSlMap.usd` (US) / `MnSlMap.dat` (JP).** One root, `MnSelectStageDataTable`. Twelve models:
- `PositionModel` has 20 joints, the icon positions: 19 slots and a root;
- the icon models (large, double, special, random) show a stage's icon by animation frame;
- `StageNameModel` shows the name by frame (20 × index);
- `StagePreviewModel` has 113 joints, the preview by frame (50 × index);
- the cursor and the Now Loading box.

**A 30th stage needs:**
- a new position joint;
- an icon frame, a name frame and a preview frame, textures added to those models' material animations;
- the table grown to 31, with `NUM_STAGES` and the 0x1D / 0x1E literals made symbolic;
- the random picker's pairing rule (`i < 22` pairs neighbours) left alone.

A new icon slot where nothing is today may need the layout reflowed. The alternative is a second "page": a button on the
SSS swaps the grid to a page of new stages, the 20XX/m-ex convention.

This is the Geno CSS work over again (`MenusGeno.cs`), on a less-explored file. **The riskiest piece.**

### 2.9 Records, the random list, counts

- **The random-stage list:** `GamePrefs.stage_mask` (u32; bits 0-28 now). The new stage takes bit 29. The default prefs
  are `U32_MAX`, so new saves have it on.
  - `gm_80164330`'s loops (`0x1D`) and `lbl_803B7808` (index → StKind) grow by one.
  - `mnstagesw.c` (the Random Stage Switch menu) has a fixed 29-entry grid (`mnStageSw_803ED4C4`, the icon table,
    `x2[NUM_STAGES]`, `x40[NUM_STAGES]` text objects) and needs a row and icon.
- **Counts:** `mncount.c` counts unlocked stages to 29 (the Data menu's stage count); `mndatadel.c` loops 0x1D.
- **Records:** VS Records keep no per-stage table. Tournament mode picks stages from its own list (`gmtoulib.c`); leave
  the new stage out of it.
- **Save data:** no format change; bit 29 already exists in the u32.

### 2.10 On hold (Michael, 2026-09-29): what they'd need

- **Single-player modes** (Classic, Adventure, All-Star, Events, Training, Home-Run, Multi-Man, Target Test) choose
  StKinds from their own tables. None picks the new stage unless we add it, so nothing is needed for them not to break.
  - Training mode picks its stage from the SSS: it follows §2.8, and needs the stage's music row (it plays the VS row).
  - All-Star or Event use would need their own StKind rows (in the stage file's params) and table entries.
- **Japanese menus:** `MnSlMap.dat` gets the same icon, preview and a Japanese name texture. The stage file has no
  language data.

## 3. The pipeline: `stage-build`, by analogy with `fighter-build`

`fighter-build` takes a rig spec, an animation spec, a glTF and template files (PlMr.dat, PlCo.dat) and writes a
fighter. `stage-build` does the same for a stage:

```
datkit.sh stage-build SPEC.json MODEL.gltf TEMPLATE_GrNBa.dat OUT/GrFm.dat [--layers BG.gltf,...] [--stkind 286]
```

- **The spec** (the stage spec in `layouts.py`, emitted as JSON):
  - the main stage's outline (ledges, side profile, floor segments and their materials, ledge splits);
  - platforms;
  - blast zones, camera range and centre;
  - spawns, respawns, item spawns;
  - the StKind rows (music ids);
  - the gobj list (which glTF node trees become which gobj, their fog, lights and animation).
- **The model:** a glTF with named node trees: `stage` (the play plane), `bg_*` layers. They are static meshes on rigid
  joints, simpler than Geno's skinned model.
- **The template:** Battlefield's file, for `grGroundParam`'s camera fields and the conventions of each root. As with
  `PlMr`, only what we replace changes.

**HSDRaw already reads and writes:**
- `SBM_Map_Head` (general points, model groups, splines, lights, MOBJs);
- `SBM_Map_GOBJ` (joint tree, anims, camera, lights, fog, collision links);
- `SBM_Coll_Data` (vertices, lines, groups);
- `SBM_GroundParam` (every field named, the StKind rows as `BGMData`);
- `SBM_GeneralPoints`;
- the whole HSD scene graph (JOBJ/DOBJ/MOBJ/TOBJ/POBJ, lights, fog, animation, particles);
- `SBM_MnSelectStageDataTable` for the SSS.

**The probe shows it writes a stage file the game loads unchanged (§6).**

Its gaps and quirks:
- HSDRaw names the line links the other way round (prev at +4, next at +6);
- its arrays are sized from their buffers, not the count fields, and a rewrite pads the vertex buffer to 0x20. Keep the
  count fields (`stage-patch` does);
- it repacks the file: a round trip is 13 KB smaller and not byte-identical, but equal as the engine reads it.

**What we write ourselves** (datkit C#, alongside `FighterBuild.cs`):
1. **Collision from the spec:** order, winding, links, flags, groups, bounds, the ledge split. 0.5 day.
2. **General points:** a joint tree from the spec's points. 0.25 day.
3. **`grGroundParam`:** copy the template's, set the scale and our StKind rows. 0.25 day.
4. **Map gobjs from the glTF:** reuse `GltfModel.cs`'s mesh and texture path for rigid, unskinned meshes (one joint per
   part). Per gobj lights and fog from the spec. 0.5-1 day, the main unknown: `GltfModel` is built for envelope-skinned
   fighters.
5. **The decomp side:** `grforest.c` and the table entries (§2.1, §2.6), hand-written once; a generated header
   (`gr_forest_ids.h`: GrKind, StKind, HPS id, gobj indices), as `ftgeno_*.h` are generated.
6. **The SSS:** a `menus-stage` command in the `MenusGeno.cs` style, for the icon, name and preview frames and the new
   position (§2.8).

**Verification** (the measurement loop, already built this round):
- `datkit stage-dump` on the output, against the spec, to 0.001;
- `starter_lab` pointed at the new StKind: every platform, both ledges, the blast zones and camera in game (GRDUMP);
- **edge match:** a front-camera render with each platform's collision projected on it; the model's top edge within one
  pixel of the collision line, per platform. The probe measured it this way (§6).

## 4. Tools built this round

- **`datkit stage-dump`** (`StageKit.cs`): a stage file in world space as the engine computes it, as JSON. It covers:
  - the stage scale;
  - joint-bound collision;
  - joint indices counted the engine's way;
  - animated joints' ranges;
  - camera and blast points;
  - music rows;
  - gobj budgets.
- **`datkit stage-patch`:** moves a joint and a collision line by world units, writing back through HSDRaw (the probe).
- **The director's `grdump` cue** (`DIR_GRDUMP` = 21): logs each frame it runs.
  - `STAGE`: the live blast zones, camera range and offset.
  - `LINE`: each live collision line after joint binding, with its flags.
  - `GROUND`: each fighter's floor line, and in the cliff states the ledge line it holds.
- **`stage/director/starter_lab.py`** (+ `run_starters.sh`):
  - drops a fighter onto every platform and the main stage;
  - hangs a fighter on each ledge;
  - dumps the live stage twice a second for a minute (three for Fountain of Dreams), so moving platforms and
    transformations are measured, not assumed.
- **`stage/starters.py`, `stage/layouts.py`:** the analysis, the tables, the envelope and the diagrams.

## 5. First milestone: the greybox

A greybox Forest Maze that **is selectable, loads, plays, has correct ledges and blast zones, and has placeholder art**,
as Geno's blocky rig was.

1. The layout Michael picks (DESIGN §6), as a spec.
2. `stage-build` writes `GrFm.dat`:
   - collision, points and params from the spec;
   - a greybox model with the play plane in flat colours (the stump brown, the platforms a lighter wood, each platform's
     top edge exactly on its collision);
   - one background card at depth, in fog green;
   - Battlefield's camera params and lights.
3. The decomp: GrKind 0x47, StKind 286, `grforest.c`, the stage's music row playing Battlefield's music until the
   arrangement lands.
4. **Selection, two options (Michael's call):**
   - (a) **a temporary hook**: on the SSS, Z on Battlefield's icon picks the Forest Maze. 0.25 day, and the greybox is
     playable at once;
   - (b) **the real slot** (§2.8). 2-3 days more before anyone plays it.
   - Recommendation: (a) for the greybox, (b) as milestone 2 alongside the art.
5. **Acceptance, measured:**
   - `starter_lab` on the new stage: every platform's height and extent, both ledges, blast zones and camera range
     match the spec to 0.01 in game;
   - the edge match within a pixel;
   - a Geno-versus-Fox playthrough, captured with game audio;
   - Michael plays it.
   - The matching build still matches (`08e0bf20`).
6. Then DESIGN §5's tests (bough camping, recovery, kill percents) on the greybox before any art.

## 6. The feasibility probe (Part D, 2026-09-29)

**Question:** can we author collision and move visuals together, write the stage file back through HSDRaw, and have the
game honour both?

**Method:**
- `datkit stage-patch` on the sandbox copy of Battlefield (`GrNBa.dat`, stage scale 0.8):
  - the left platform's joint (gobj 6, joint 13) moved up 8 world units (10 file units);
  - its collision line (line 2, vertices 23-24) moved up by the same.
- Installed on the sandbox disc only; the lab built against the patched dump.

**Results:**
- **Round trip, no edits.** HSDRaw repacks the file (452,171 → 439,139 bytes, not byte-identical). The dump is equal as
  the engine reads it (count fields kept). **In game, the full `starter_lab` passes 6/6**: platforms at 27.2 / 54.4 /
  27.2, ledges ±68.4, blast zones ±224 / 200 / −108.8, camera ±160 / 136 / −47.2.
- **Moved platform.** Fox falls onto the left platform and stands at **y = 35.20** (Wait, grounded, on line 2). The
  live collision logs line 2 at −57.6 to −20.0, y 35.200.
- **Visual.** In a res-2 front-camera frame, the moved platform's rim sits **65 px above the unmoved right platform's**,
  8.3 units at 7.8 px per unit (8 intended; ±0.13 per pixel of rim). Fox's feet sit on the moved model's surface. The
  frames are local: `~/games/melee/sandbox/geno-stage/board/probe_moved_*.png`.
- **The disc was restored** (`GrNBa.dat` byte-identical to the main disc's), and the frame dumps deleted.

**What it retires:**
- HSDRaw writing stage files the game loads;
- the collision and joint conventions (stage scale, joint indexing, unbound groups);
- our measurement loop.

**What it doesn't:**
- a file built from scratch rather than patched;
- new gobjs;
- a new GrKind or StKind;
- the SSS.
