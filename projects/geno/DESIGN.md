# GENO: design v1.3 (for the blockout)

A wholesale-new Melee fighter: Geno, the star spirit in a wooden doll (Super Mario RPG, 1996). This turns the research
(`research/`), the cast's measured attributes (`research/cast_attributes.csv`) and Michael's direction into a kit to prototype
on the blocky rig and playtest. v0 was reviewed by a fighting-game design reviewer (`reviews/design-v0-review.md`, against
`reviews/design-v0.md`); v1 takes nearly all of that review, and the changelog at the end says what changed and why. Every
number here is a starting target for the labs, not a promise.

Citations name the document: **FG** is `research/fg-design-principles.md`, **PF** is `research/platform-fighter-design.md`,
**SRC** is `research/geno-source.md`, **REV** is the review.

## 1. The headline

**A pressure zoner: fast, aggressive screen control. He sends stars he can run in behind, pins shields with the Whirl and
crosses them up with a spinning nair, and turns stray hits into knockdowns and edgeguards. He pays for it with a light
body that falls fast enough to combo, and a finicky recovery.**

- **Direction (Michael):** a true zoner, which Smash has never quite had, in the space of BlazBlue's Nu-13 in Calamity
  Trigger: screen control that feels overwhelming to face, arguably overpowered, and fun on both sides.
- **Aggressive, not patient (Michael, v1.2):** exciting to play and to watch (the opposite of Jigglypuff's snoozefest
  reputation). Fast zone control and pressure, not Samus's heavy, poking, plodding projectiles. Nair is strong out of
  shield, as a crossup and as the follow-in behind his projectiles; the Whirl is slow enough to run behind and keep a shield
  under pressure. He pays in fragility: less weight and a finicky recovery. The matchups against the top tiers should be
  tight.
- **The Melee problem.** A literal SMRPG port is a projectile camper, the archetype that goes degenerate in Melee or, more
  often, simply loses to Melee movement. Project M 3.02 let projectile characters "zone other characters out" and 3.5 toned
  it down (PF P6). Slow, breakable projectiles on bodies that can't follow up (Link, Young Link, Samus) sit 11th to 18th (PF
  §2).
- **What made CT Nu work, and what transfers** (REV §3):
  - **Cheap threats.** Her swords had low recovery and let her act at once. v1 prices Geno's tools by on-screen count and
    cooldown, not by long animations.
  - **Many angles.** A straight lane, a curve, a drop from above and a ground lane.
  - **Stray hit, then knockdown, then more swords.** Melee's version is the **tech chase**: a knockdown forces a read on
    tech-in-place, roll toward, roll away or a missed tech, and Geno covers the options from range with different pieces.
    This is the single most important thing v0 lacked (§7).
  - **Weak under pressure, but not helpless.** Nu had a 6-frame button, an invulnerable anti-air and an invulnerable
    backdash. Geno's weakness is low *reward* up close, not no escape.
- **Power target:** tight matchups against the top tiers (Fox, Falco, Sheik, Marth, Jigglypuff, Peach, Falcon: each within
  45-55). Overshoot in the labs, then pull back (FG P10, Sirlin's HD Remix). Oppressive but beatable is acceptable; a
  pressure sequence with no answer is not (§8).

**In "a word or two" (PF checklist): star rush.** The weakness a top player names first: "he's light, he falls fast enough
to combo, and his recovery is a guessing game. Hit him once and edgeguard him."

## 2. Pillars

1. **Throw, then follow.** Every projectile is something he runs in behind. The Whirl is slower than his run and grinds a
   shield long enough for him to arrive; Finger Shot works off a short hop like Falco's laser. Pressure travels *with* him,
   which is what separates him from Samus and Link.
2. **Every angle, one of each.** A straight lane (the Beam and Finger Shot), a curve and a ground lane (the Whirl), and a
   drop from above (the Blast). Threats layer, which is the Nu fantasy, but only one of each exists at a time (Sakurai: "One
   Gordo on screen at a time", PF P3).
3. **Cheap to place, dangerous to touch.** Each piece is quick to set and has an on-hit state another piece cashes in (§7).
   The web taxes movement *and* pays off.
4. **The doll is the identity.** Fists fly off on arm bones, the forearms are gun barrels, the body folds into a cannon and
   the star can leave the doll. Silhouettes and animation sell it; a generic arm-cannon reskin is the failure mode (SRC).
5. **Timing is a decision, on specials only.** SMRPG's timed presses live on the specials: fire the Beam on star two now or
   wait for three, crit the Whirl or save side-B for the recall, keep the Blast fast or widen it. Everything is balanced as
   if every press is perfect (FG P8). The 9999 Whirl is at most an impractical easter egg or trailer-only.

## 3. Physics

Measured against the cast (`cast_attributes.csv`, all 26 characters from the disc; `research/cast_moves.md` has the
movement table). v1.2 moves him toward the fast, aggressive corner (Sheik and Falco) and pays for it with weight: a low
short hop whose aerials meet grounded opponents on the way up, a quick SHFFL cycle, and a fall fast enough that he gets
combo'd. v1.3 (Michael's hand playtest: "slippery") plants him: slower ground speed that visibly accelerates, jumpsquat 5,
a lower full hop and less air drift. He's a grounded character with middling anti-air, so the answer to his zoning is to
jump in, and his answer to that is up smash out of shield.

| Attribute | Geno | Cast min / median / max | Why |
|---|---|---|---|
| Weight | **80** | 55 / 90 / 117 | Falco's. The fragility he pays for aggression (Michael, v1.2; was 88) |
| Fall speed / fast fall | **2.3 / 3.0** | 1.3 / 1.9 / 3.1 | Between Sheik (2.13 / 3.0) and Falcon (2.9 / 3.5). Fast SHFFLs and landings on shield; the cost is that he gets combo'd. Must stay clear of Marth's and Sheik's chaingrabs on Fox and Falco (lab) |
| Gravity | **0.13** | 0.064 / 0.0975 / 0.23 | Falcon's. Short hop 11.3 units (Falco 11.6, Mario 11.0), 27 frames, **17 fast-fallen** (Fox 14, Falco 16, Falcon 20) |
| Air speed | **0.85** | 0.68 / 0.9 / 1.35 | v1.3: below median (was 1.0). A grounded character: the answer to his zoning is to jump in |
| Air acceleration | **0.035** | 0.0125 / 0.03 / 0.09 | v1.3 (was Falco's 0.05). How fast he reverses drift into a retreating aerial, the real retreat stat |
| Air friction | **0.0175** | — | Around the median |
| Jumpsquat | **5** | 3 / 4 / 8 | v1.3 (was 3): Falco, Peach. Out-of-shield nair on frame 8; up smash is his quicker out-of-shield answer |
| Short hop / full jump velocity | **1.65 / 2.75** | 1.5 / 2.1 and 2.4 / 3.7 (Marth / Fox) | Short hop 11.3; full hop 29 (v1.3, Fox's; was 36.1, median 32) |
| Double-jump multiplier | **0.95** | median | |
| Dash / run | **1.35 / 1.6** | 1.0 / 1.5 / 2.0 and 1.1 / 1.5 / 2.3 | v1.3 (was 1.8 / 1.9, "slippery"). Every dash starts at its initial speed on frame 1: 1.8 of 1.9 left nothing to accelerate into; now 84% of the run (Fox 86%, Marth 83%) with dash acceleration 0.08. Still faster than the Whirl, so he can run in behind it. Dash animation 18 frames (a released dash plays it all), skid 18, run turnaround 18 (Mario's 22 / 23 / 22) |
| Walk | **1.0** | 0.65 / 1.1 / 1.6 | |
| Traction | **0.08** | 0.025 / 0.075 / 0.1 | v1.3 (was 0.06): Fox's; less slide after a dash, a shorter wavedash |
| Jumps | **2** | 2 / 2 / 6 | No multi-jump (a stall and recovery lever) |
| Landing lag | normal 4; nair 14, fair 16, bair 18, uair 16, dair 24 | — | L-cancelled: 7 / 8 / 9 / 8 / 12 |
| Shield | **13.75**, centred by `rig/shieldfit.py` | — | The shield is a sphere on ThrowN of radius 0.575 × ShieldSize at full health (measured, `director/shield_lab.py`). While shielding the engine poses his whole body from the fighter data's shield pose (not the Guard animations): v1.3 writes his guard pose there (knees bent, head ducked, cap point flopped back) with ThrowN at the centre of the smallest sphere around his hurtboxes. Full shield covers every hurtbox by 0.65 (the cap by 0.36; Fox's stick out by ~1.8); from health ~50 the head and knees show. Tilting moves it along Mario's path, scaled |

**Hurtboxes:** no hurtbox on the hat point, cape or collar tips, and the fists have none when they fly. v1.3 (Michael,
with the production model): cast-typical limbs (arms 0.85, fists 1.0, thighs 1.05, shins 1.0, head 2.4, waist 2.6, hip
2.1). The v1.2 limbs were half the cast's (arms 0.5, legs 0.65; Sheik 0.72 / 0.96), so he was harder to hit than anyone
and the model came out spindly. The head hurtbox is
Marth-class and body height sits within Marth's and Sheik's. A big doll silhouette would otherwise be combo food and a
shield-poke target.

**Balance levers, in order:** air speed and fall speed first, since they set his offence and neutral as well as his defence
(Michael); then weight, now the fragility lever.

**Kill percents against him:** about 8-12% earlier than Marth's, vertically and horizontally. Measure with Fox's up-throw
into up-air, Marth's tipper forward smash and Sheik's up-air, and chart what combos him at 2.3 / 3.0 that doesn't combo
Marth.

## 4. Systems

- **Timed hits on specials only.** A press in a short window gives a chime, rainbow stars and a small bonus (+10% damage, or
  a property per move). SMRPG's own bonuses are +25-100%; the smaller number is deliberate. Normals have no timed press: on
  a normal it would be a flat buff for experts with no decision in it, and it would collide with jab strings, L-cancels and
  aerial inputs (REV Q4). It also separates Geno from Legacy XP's timed-everything.
- **No meter** (Michael): a per-character resource doesn't fit Melee's own design sensibility, even though later games added
  them. Geno Flash is the **third star of down-B** (§5), SMRPG's hold-to-the-third-star verb, so Blast is never lost and
  Flash is a read-and-punish tool rather than a checkmate or a dud.
- **Geno Boost** is out of v0. It could come back as a cosmetic taunt with the red arrows, or, only if the labs say he's
  under target, as a long, punishable, one-hit buff that can't stack with a stored Beam (the Shulk rule, PF §4.5).

## 5. Specials

Frame numbers count from the input (frame 1 = the first frame of the move). **IASA** is the first frame he can act.

| Slot | Move | Shape | Counterplay |
|---|---|---|---|
| Neutral B (tap) | **Finger Shot** | Four bullets from the right hand. Grounded: fires frame 10, IASA 34. Aerial: fires frame 7, 24-frame animation, 10 frames of landing lag only if he lands before frame 16. **Aerial shots angle ~10° down** (lab, v1.2: level shots from a short hop pass over a standing opponent, since his hand sits ~9 above his feet), so a short-hop shot meets standing opponents at mid-range: his version of Falco's short-hop laser, capped by the two-on-screen rule. 3%, ~4 units a frame, fades at ~75 units (under half of Final Destination). **Two on screen, max.** Falco's template: real hitstun, slow fire rate. Within ~25 units a hit leads to jab, forward tilt or grab; beyond that it only interrupts | Reflectors and powershield; Sheik's needles and Falco's lasers trade with it; short range means he can't wall the whole stage with it |
| Neutral B (hold) | **Geno Beam** | Three stars light at frames 20, 40 and 60 (v1.3; v1.2 had 15/30/45). Release within ±3 frames of a star's flash for the timed bonus. Just past star three's timed window it fires by itself (frame 64). Release: 8 frames of startup, ~25 of endlag. **No store** (v1.4, Michael: a slight balancing lever, and it separates him from Samus's and Mewtwo's charge shots): a shield press cancels the charge and its stars are lost. Kirby's copy matches. Full Beam: ~17%, a fast, near-full-screen bolt that kills Fox from centre stage at ~115-125%. Air: charges under normal gravity; 20 frames of landing lag only if he lands during the release. Energy | Jump it (a line); powershield and the reflectors (Fox, Falco, Mario's and Dr. Mario's capes, Mewtwo's Confusion, Zelda's Nayru's Love, Ness's bat); Ness's PSI Magnet and Game & Watch's bucket absorb it. The visible charge is the tell (FG P7) |
| Side B | **Geno Whirl** | A spinning disc of light, **the pressure piece he runs in behind** (v1.2). Spawns frame 12, IASA 24; aerial landing lag 12 only if he lands before frame 20. Travels ~1.35 units a frame easing to ~0.93 (~54 units over ~47 frames; v1.3 scaled with his run), slower than his run (1.6), so he can follow it in; the stick bends it ±20° up or down. **On a shield it grinds:** it presses against the shield and hits three more times, 3% each, 15, 28 and 41 frames after the contact (the first waits out the contact's hitlag and shieldstun; each leaves a gap of 5 or more, inside rule 4 of §8), then settles into the hover. It presses up to the shield's front and never through it: each grind hit knocks it back a little, and after the grind it backs off to ~5 units in front of the shield and hovers there (Michael, 2026-09-29). A light shield's pushback (16-19 units against 3-6 for a hard shield) outruns it, so a light shielder can slide out of the later grind hits, as Melee's light shield escapes pressure. After the outbound hit it **drops its hitbox and spins down for ~20 frames** (still recallable), then it's gone and side B is free (Michael, v1.2: a lingering hitbox that can't hit its only opponent again was noise). The 45-frame hover wall below is for a throw that hits nothing, and after a grind. From 40 units he arrives mid-grind, with the crossup nair, a tomahawk into grab, a spaced fair or a Blast mark on the roll. **The down-arc hits the floor and rolls along it: the ground lane** (Nu's Sickle Storm). Outbound hit 7% at ~40°: a stumble he runs into at low percent, tumbling from ~50% on mid-weights into a tech situation. **Crit:** side-B again within ~4 frames of contact multiplies knockback growth by ~1.35 (kills Fox from mid-range at ~120-135%); an early press voids the crit for that throw, so mashing doesn't work. Then it **hovers 45 frames**: 4-5%, once per target, knocks away and up. **Recall:** side-B during the hover pulls it back through him, ~4 units a frame, 6% at 80°, once per target. Breaks on any hit of 6% or more (our number; Samus's Missile breaks at 4%); cancels incoming projectiles under 6% and survives. Side-B is locked while it's out, plus 30 frames after it despawns unless he catches it. Energy | Shield it; jump the ground roll; break it with a 6% hit; Fox and Falco reflect it; while it's out, his side-B is spent |
| Down B | **Geno Blast** | **Either-or: the release decides** (v1.4, Michael). He raises both arms to the sky (the casting pose Blast and Flash share) and holds it while the stars light; the stick at the release sets the mark's distance (~25, 50 or 75 units ahead). A **tap** marks on frame 10 (IASA 38); a **release** from frame 10 on marks on the release frame (the release registers the frame after B is let go), IASA 28 frames after the mark: one column, or **three (±14 units) once the second star has lit** (frame 25, with the Beam's second-star sound), capped by rule 5 in §8; a late release commits longer. **Held to the third star (frame 49) it becomes Geno Flash instead, with no Blast** (grounded; airborne there is no Flash, and the widened Blast releases itself at the third star). **An aerial down B that lands mid-charge keeps its charge** (no landing lag, the count carries on), so the third star grounded is the Flash. Beams land ~32 frames after the mark: a column ~10 units wide and ~60 tall, **striking the floor under its own mark wherever Geno is** (each column finds the floor below it; over the void it sweeps 50 down from his height), passing through platforms, and it survives Geno being hit. 9% per column; **airborne targets are meteored** (cancellable), **grounded targets popped up** at 80-85° (the answer to platform camping). **One set of marks at a time. Unusable below ledge height (at the start and at the release: a release down there places no mark); cancelled by a ledge grab or helpless fall.** Energy. Melee precedent: Pikachu's Thunder | The mark is a ~32-frame tell (a bolt standing on the floor at the mark); the raised arms hide which it will be until he commits; move off it; it can't cover the stage and the ledge at once; meteor-cancel |
| Down B (third star) | **Geno Flash** | Hold down B to the third star (frame 49, grounded; v1.4: instead of the Blast, no mark) and he folds into the blue-and-gold cannon on its carriage (its own model since 2026-09-29, §12) and fires 54 frames later (frame 102 of the hold). **A sweetspot, then a sourspot, in time** (v1.5, Michael 2026-09-29): the sun appears as a **burst** the size of PK Flash's full explosion (radius 14.3), the kill hit for its first 8 frames: 18%, 45°, KBG 95, BKB 55, killing Fox from centre stage at 75% with or without DI (Michael: a little weaker than PK Flash's 65%, its charge and control being better). Then it grows over 40 frames to a **28** radius (was 38) and lingers 30 as the **late sun**: 12%, 45°, 85/45, killing only at ~150% (190% with DI). One hit per target: whoever the burst hit, the late sun can't. **No armour in v0.** Endlag ~40 | A read and punish tool: shield break, missed tech, Rest, a slow recovery. Run from the fold; hit him out of it |
| Up B | **Star Road** (cannon launch) | Folds into the cannon on frame 6, aims for 12 frames (it fires itself at the end), 16 directions, then travels 20 frames (v1.3; was 24, about Falco's distance with the double jump; now ~17% shorter). The ledge catches from travel frame 4, facing it (he faces the aim's horizontal direction), and as for everyone only while descending: a rising star pops over the ledge and catches it in the helpless fall. **A steep hit on a wall slides along it** (v1.3), so diving along an undercut wall reaches the ledge and rising along one pops over it; a level hit or the stage's underside stops the star dead, so a low recovery still has to be aimed. **A small hitbox at launch only** (4 frames at the muzzle, 6-7%, sends away), nothing in flight or at the end. Helpless fall with 0.6 drift; 30 frames of special landing lag on stage | The fold and aim is readable; edgehog; wait at the landing; a rising recovery ends above the ledge, open; a level shot into the wall is a lost stock. Legacy XP's version has no helpless fall but costs the double jump and airdodge; ours is helpless |

**Projectile rules, all of them:**
- **Reflector break is real in Melee:** "If a projectile is too strong for a reflector, the reflector breaks as if it was a
  shield and stuns the user" (SmashWiki, via REV). Every Geno projectile stays under the threshold (read it from the decomp),
  because a broken reflector is a stock lost to a knowledge check. Fox and Falco reflect at 1.5× damage, so a reflected
  full Beam must not kill Geno below ~90%.
- **Energy or physical:** Finger Shot is bullets (physical); the Beam, Whirl, Blast and Flash are energy, so Ness and
  Game & Watch can absorb them. That's a healthy matchup tool for two low tiers.
- **Link's and Young Link's shields** block frontal projectiles, so the Blast from above and the bent Whirl are the answers
  there. The lane design working as intended.
- **Crouch height:** every projectile is lab-checked against every crouch hurtbox (Jigglypuff, Kirby, Pikachu, Fox, the Ice
  Climbers).

## 6. Normals

Close range is pressure, not a combo engine (v1.2): a frame-6 out-of-shield nair that also crosses up and follows him in
behind the Whirl, a tomahawk into a standard grab, and a real anti-air (REV MF3). A clean nair leads to a follow-up at low
percent, but his kills still come from the Beam, back air, Double Punch, up smash and edgeguards. No frame-1 move.

| Move | Idea | Target |
|---|---|---|
| Jab | Finger taps into a rapid burst of **non-travelling** muzzle hitboxes (they reach ~1.5 body widths, SDI-able), then a push-away finisher | Frame 3, 3%. His get-off-me |
| Forward tilt | **Hand Gun**: a disjointed wrist blast | Frame 7-8, 10%. Safe only at max range on shield |
| Up tilt | A spin of the cape upward, disjointed (the cape has no hurtbox) | Frame 6-7, 30 total. His grounded anti-air against Marth and Jigglypuff |
| Down tilt | A low **Finger Shot** from the crouch, skipping along the floor (v1.2: a gun blast; a kick from his short legs couldn't reach the cast median) | Frame 6; trips at low percent (Kirby's down tilt is the precedent). A knockdown source |
| Dash attack | A doll-stiff shoulder dive | Committal, mid reward. Chaff, like most Melee dash attacks |
| Forward smash | **Double Punch**: both fists launch on extended arm bones (hitboxes, not items, so a shine can't reflect his fist) and return | Frame 14-16, ~45 total; strong outbound, weak return; kills Fox ~100-110% at the tip. Punishable on whiff and shield |
| Up smash | **Star Gun**: stars fired straight up from both wrists | Frame 9 (10 out of shield). His out-of-shield kill option; kills Fox ~105-115% |
| Down smash | **Twin Hand Cannons**, both sides at once (Michael, 2026-09-28: like Mega Man's two-sided blast in Ultimate) | Both arms fold into cannons and fire outward together on frame 7, 12% each side at a low 30°; the charge hold shows both cannons cocked low. Covers rolls and knockdowns on both sides at once (§7); total 44 (was 41 with the back side on 13) pays for the back side firing 6 frames sooner |
| Neutral air | A spinning doll with a disjointed star core, sweeping 360° and ending low behind him | **Frame 3** (6 out of shield, level with Sheik). Clean (frames 3-6) 12% at ~45°: a follow-up at low percent (grab, up tilt, another nair), a knockdown by mid; late (7-20) 7% at a low angle. L-cancelled 7. His out-of-shield option, his crossup (§6b) and the follow-in behind the Whirl |
| Forward air | A long disjointed **Hand Gun** burst, not a travelling projectile | **Late, long, strong at the tip** (v1.2; Byleth's lance aerials were Michael's reference): frame 9, 3 active; 13% at the tip out to ~20 units, 7% in the middle, nothing within ~6 units of him (point-blank is nair's job). From a short hop it meets standing opponents on the way up, not crouching ones |
| Back air | A **Hand Cannon** shot backward | The same treatment: frame 10, 14% at the tip out to ~20 units behind, weak in the middle; his turnaround kill. Recoil only on the first back air per airtime, capped below his air speed |
| Up air | A disjointed upward burst of stars | Frame 5-6. Juggle; weaker than up smash |
| Down air | A **rocket fist** straight down (Michael, 2026-09-29: the earlier "disjoint hand cannon shot" meant the rocket fist): the fist fires off the forearm, flies out to ~13 below him and returns, as Double Punch's fists do; disjoint, intangible while it's out, the hitboxes riding it | Frame 9-10 meteor sweetspot on the fist while it is near him, where the column's muzzle was (12%, 270°, airborne targets only, cancellable; a grounded opponent under it takes an 8% pop). The extended fist is the weak tail, 11-15 (5%, no spike). A travelling fist: full reach (13.0, Falcon's; the cast max is 13.9) on 12, home on 20. Otherwise the column's timing: active 9-15, IASA 38, landing lag 24 (frames 2-31), autocancel on 1 and 32+. Landing mid-flight, the fist eases home through a 6-frame blend into the landing. Michael (2026-09-28): it should read long, and the meteor stays close so the length doesn't make it a long-range spike. A landing tool out of juggles, which a floaty-ish zoner needs more than a second spike |
| Grab and throws | Standard range, standing grab frame 7: the fists shoot out on the arm bones and close, so their hurtboxes come along (not a disjoint). Each throw a weapon (§6f): Rocket Fist forward and Hand Cannon back at 30-35° toward the ledge; a point-blank Finger Shot down throw into a knockdown 20-40 units away; a Star Gun salvo on the up throw's vertical pop | No set-knockback throws, no regrab on Fox, Falco or Falcon at any percent. Throws make *situations* (§7), not chains |

### 6b. The normals budget (measured against the cast)

`research/cast_moves.md` measures every cast member's normals the way the game plays them (datkit `movedata`: the move
script replayed, the skeleton posed by the move's own animation at each active frame, hitboxes and hurtboxes placed in
world units, lunges and stretched limbs included; checked in game: Mario's jab connects from 20 units, as measured).
Medians below are the cast's. The first blockout's frame data landed where designed, but its reach and hitbox size sit at
the 2nd-10th percentile on nearly every normal: placeholder geometry, now to be set on purpose.

**The budget.** Geno's range lives in his specials. If his normals were also long, he'd be overloaded (a zoner who also
owns Marth's normals; REV MF3/§4.2). So the normals sit **around the cast median**, with exceptions that are his named
tools: Double Punch (the long disjoint, paid for with startup and endlag), Hand Gun's forward tilt and forward air (spacing
disjoints, a notch below Marth), the cape's up tilt (an anti-air disjoint) and the star core of neutral air (a large
get-off-me radius with short reach). The grab is standard (REV MF3). His close range stays low-reward, not short.

**Disjoint (Michael, v1.2): gun blasts may be disjoint; body moves carry their hurtboxes.** His SMRPG weapons are all
arm-guns (Finger Shot, Hand Gun, Hand Cannon, Double Punch, Star Gun), and his arms are short (4.45 units), so matching
the cast's reach means muzzle bursts that no hurtbox follows: forward tilt, down tilt, the smashes, fair, back air, up air
and down air measure at or above the top of the cast's disjoint. Ultimate's Mega Man pellets are a longer disjoint used for
neutral spacing. The body moves (grab, dash attack, dash grab) stay near the median. If the gun blasts prove too strong,
trim their range first.

Proposed targets (percentiles of the cast; reach is in the move's direction, disjoint is reach past his own hurtboxes):

| Move | Role | Reach | Radius | Disjoint | Startup / total (now) | Notes |
|---|---|---|---|---|---|---|
| Jab | Get-off-me, low reward | ~50th (~17) | ~50th | ~40th | f3 / 17 | Median jab; low damage keeps it low-reward |
| Forward tilt (Hand Gun) | Spacing poke, safe only at the tip | ~65th (~22) | ~50th | ~75th | f7 / 28 | A muzzle blast past the wrist; punishable when not at max range |
| Up tilt (cape) | Grounded anti-air | ~60th up | ~65th | ~70th up | f6 / 28 | The cape has no hurtbox, so the arc is disjointed |
| Down tilt | Low poke, knockdowns | ~45th | ~45th | high (a gun blast) | f6 / 22 | A low Finger Shot along the floor |
| Dash attack | Committal | ~45th | ~50th | ~40th | f6 / 38 | Needs the forward slide (animation root motion) |
| Forward smash (Double Punch) | The long disjoint | **~85th (~31)** | ~50th | **~85th** | f15 / 44 | Fists fly on the arm bones with no hurtbox; late and punishable |
| Up smash (Star Gun) | Out-of-shield kill | ~55th up | ~55th | ~60th up | f9 / 39 | |
| Down smash (twin Hand Cannons) | Roll and tech cover, both sides at once | ~50th | ~50th | ~55th | f7 both sides / 44 (IASA 43) | Measured (2026-09-28): reach 17.3 in front and behind (56th pct), disjoint 10.6 each side (83rd), active 7-9 |
| Neutral air (star core) | Out of shield, crossup, the follow-in | ~50th | **~80th** | ~65th | **f3** / 34 | A big disjointed core, a 360° sweep, low back at the top of the cast (7) |
| Forward air (Hand Gun) | The spacing wall | ~80th (~20, Marth 21) | ~35th | high | **f9** / 34 | Strong only at the tip, nothing within ~6 units; slower than Marth's (f4) |
| Back air (Hand Cannon) | Turnaround kill | ~80th back (~20) | ~40th | high | **f10** / 36 | The same tip-strong shape |
| Up air | Juggle | ~45th up | ~50th | ~50th up | f5 / 28 | |
| Down air (rocket fist) | Landing tool, meteor | ~50th below (~8 under his feet) | ~50th | ~55th below | f9 / 38 | Reaches 13.0 below (98th; the column did too, from 2026-09-28) |
| Grab / dash grab | Standard | ~50th (~13) | ~50th | ~50th | f7 / 30 | |

**Jump height and aerial geometry go together (Michael).** Whether an aerial can hit a grounded opponent while rising,
or only while falling, decides whether it's an approach tool, a wall, or a landing and retreat tool, so neither jump
height nor an aerial's reach is comparable alone (Falco's low short hop and huge full hop are his identity: short-hop
aerials that meet grounded opponents on the way up, full-hop dair and juggles). `research/aerial_profile.md` measures it
for the cast: Marth's short-hop fair hits even a crouching Fox while rising (the wall); Samus's high short hop leaves her
fair falling-only. Geno's blockout: short hop median (13.4, apex f17), but fair is falling-only and connects from 14
units (Marth 26), and full-hop dair covers 15 input frames (Fox, Falco, Marth 20-26). **Decided (Michael, v1.2): the aggressive
identity**, the closest of the three options to (B): a Falco-low short hop (11.3) whose aerials meet grounded opponents on
the way up (nair from its first rising frames, standing or crouching; fair a wall that rise-hits standing targets and
catches crouching ones late in the rise), and a full hop (36) for platforms, juggles and full-hop dair landing cover.
(A, a median hop that rise-hits standing targets only, and C, a floaty retreat zoner, were the alternatives.) Also: his crouch barely lowers him (13.3 of 15.2; Fox 10.8 of 15.6), which matters for crouch cancel and
ducking projectiles; and his hurtboxes are narrow (2.6 in front, the cast about 5), to be set to the final silhouette.

**Shape matters as much as reach (Michael).** Where each active frame covers decides how an aerial plays: an arc that
sweeps front to back (Marth's nair and dair) covers crossups and landing behind a shield; a narrow column straight down is
a spike and landing tool with no crossup. Advanced shield pressure mixes tomahawks (an empty jump into a grab) with
landing behind a shield while attacking, so crossup coverage and its safety are a budget item. Sweep charts
(`director/labs/sweeps.py`: per-frame spheres around the measured body, `board/sweeps_*.png`) show the cast's shapes, and
`research/aerial_shape.md` measures them: reach front, back and below the feet; **low back** (rear coverage within 4
units of the feet, the part that meets a shield as he lands behind it: Sheik's nair 6, Marth's and Falco's 5, Fox's 4);
and the sweep (where the hit sits on its first and last active frames: Marth's dair +6 → −6, Falcon's a column at 0).
Geno's blockout aerials are single small spheres at his waist, with no low coverage at all. Proposed shapes, with
targets in units (front / back / below the feet / low back / sweep):

| Aerial | Shape | Target | Its job |
|---|---|---|---|
| Nair (spinning doll) | A short 360° sweep ending low behind him; big core radius, short reach | 9 / 7 / 0 / **7** / +4 → −4 | **The crossup**: landing behind a shield while hitting, mixed with a tomahawk into his standard grab. His close-range shield pressure, low reward. Low back at the top of the cast (Sheik 6), since it's his named tool |
| Fair (Hand Gun) | A forward wall at the tip, chest to knee; nothing within ~6 units | 20 / none / 0 / none / steady at +12 | The spacing wall: late (frame 9) and strongest at the tip. Rise-hits standing targets from 25 units, not crouching ones. No crossup |
| Bair (Hand Cannon) | A compact blast behind at the tip, mid height | 0 / 20 / −2 / 20 / steady at −13 | Turnaround kill: late (frame 10) and strongest at the tip; no arc |
| Uair (Star Gun) | An overhead arc, front to back | 8 / 8 / — / — / +6 → −6 | Juggles; up ~22 (median). Marth's and Falcon's arc front to back; Fox's and Falco's the other way |
| Dair (muzzle blast) | **A narrow column straight down** | 6 / ≤3 / **8** / ≤3 / 0 → 0 | Meteor and landing cover under him (Falcon's 12 below, Peach's 9, Sheik's 6). Little rear coverage, so dair behind a shield is punishable and nair stays the crossup tool |

Low back is necessary for a crossup, not the whole story: whether it's safe also needs the shield bubble's size and the
on-shield frame advantage. Both go into the shield-safety lab (below), which lands aerials in front of and behind a
shielding Fox and Marth in game.

**Measured (v1.2, `research/cast_moves.md`, `aerial_shape.md`, `aerial_profile.md`; rebuilt and re-measured by
`rig/remeasure.sh`):** reach and hitbox size land on the targets above (forward tilt 22.5, Double Punch 30.9, fair 20.1,
back air 20.3, grab 12.8, dash attack 29.6 with its slide); the gun blasts' disjoint sits at or above the cast's top, the
grab's at the 33rd percentile. In game, every normal hits on its designed frame, and the tilts, smashes and grab connect
at their new tips. **On shield** (`research/shield_safety.md`, computed from the measured frame data with shieldstun =
0.45 x damage + 2): nair +0 at best (Fox's is +0), fair -1 from its tip, back air -1, up air -2, down air -5; forward tilt
-15 (safe only at the tip, by spacing), Double Punch -20 (Fox's forward smash -26), up smash -22. The Whirl's grind leaves 6
frames after each 3% hit (rule 4). In game (whirl lab): a SHFFL nair that meets the shield at the top of the short hop
lands -6 (it falls 6 frames after the hit; the computed +0 is a nair that hits just before landing), but the shield's
pushback leaves Fox ~15 units away and his shield grab whiffs. The L-cancel halves nair's landing lag (14 to 7) as set.

### 6c. Pummel, ledge attacks and get-up attacks (2026-09-28)

These are Melee's shared vocabulary, and the cast barely varies them. Every pummel is 3% in 24-30 frames. Every ledge attack
takes 54-56 frames under 100% and 69-70 from 100%. Every get-up attack takes 50 frames, does 6-8% and pushes at 361° (growth
50, base 80). `research/cast_moves.md` ("Pummel, ledge and get-up attacks") measures them the way the normals are
measured: datkit `movedata` replays the five actions, their intangibility, each side's coverage and, for ledge actions,
the TransN path, measured from the ledge corner (the engine places a ledge action at ledge + TransN).

**Geno takes the cast's medians.** Nothing in his design argues otherwise. These are escape and tempo options, not the
zoning the design is about, and his fragility is priced in weight and recovery, not here. Odd escape options would change
ledge and tech-chase situations for everyone in ways the design doesn't ask for. His identity lives in their shape: gun
blasts, not kicks.

| Move | Geno | Cast median (range) | Shape |
|---|---|---|---|
| Pummel (CatchAttack) | 3%, hits frame 9, 24 total | 3%, 9 (2-16), 24 (24-30) | The left hand holds; the right elbow draws back and the finger barrel jabs in with a point-blank pop (the jab's PULSE). Hits only the held opponent, like every pummel but Samus's |
| Ledge attack under 100% (CliffAttackQuick) | Intangible 1-20, on the stage frame 18, hits 24-28, 55 total, 8% at set knockback 90. Reach 23.3 from the ledge, 15.5 up; ends 7.2 onto the stage | 1-20, 18.5, 24 (5 active), 55, 8%; 23.9, 18.8; 7.3 | A snap pull-up (a dip into the hands, then yanked over the lip), a crouch on the corner, and a Hand Gun burst that rakes up from the floor (HANDGUN) |
| Ledge attack from 100% (CliffAttackSlow) | Intangible 1-37, on the stage 34, hits 41-44, 70 total, 8%. Reach 22.8, 11.4 up; ends 4.2 in | 1-37.5, 34, 41.5 (5), 70, 8%; 23.2, 12.2; 4.2 | A heavy haul up, both hands drawn back, and a two-handed Hand Cannon along the floor (HANDCANNON); the recoil rocks him back |
| Get-up attack, face up (DownAttackU) | Intangible 1-25; in front 19-20, behind 24-25; 50 total; 6% each. Reach 19.2 both ways, 14.4 up | 1-26; first hit 19; 50; 6%; 19.1 front, 19.2 back, 14.9 up | He jerks upright off his back as if his strings were yanked, fires low in front (the blast blooms upward on its second frame), then swings the other gun behind (his down smash's order) |
| Get-up attack, face down (DownAttackD) | Intangible 1-26; behind 19-20, in front 25-26; 50; 6%. 19.2 both ways, 14.4 up | 1-26; 19; 50; 6%; 19.0 front, 20.2 back, 14.9 up | A push-up into a crouch, firing behind as he rises, then in front (the cast's usual order face down); each blast blooms upward |

- **Reach is at the median, and the blasts are disjoint**, per §6b's rule for gun blasts. The disjoint changes little here:
  he's intangible until 3 frames before a ledge attack hits, and through both get-up hits.
- **The get-ups cover what the cast's cover** (Michael, round 2; they had reached 10.9 up against 14.9).
  `research/getup_cover.md` measures, from the cast's hitboxes:
  - the top of the hit region on each side;
  - its height 8 and 14 units out;
  - what covers the space over the fighter's own body;
  - the height an opponent must clear to pass over (within 3 units of a distance).

  Each of his shots is two frames: a low blast along the floor, then it blooms upward. The table below sits between the
  cast's 44th and 75th percentiles throughout:

  | Get-up coverage | Geno | Cast median, face up / face down |
  |---|---|---|
  | Top of the hit region | 14.4 | 14.8 front and 13.5 back / 13.5 and 14.2 |
  | Height 8 units out | 12.9 | 12.4 / 13.2 |
  | Height 14 units out | 14.4 | 13.6 front and 12.4 back / 11.1 and 12.4 |
  | Over his body | 10.8 | 11.4 / 11.2 |
  | Clearance to pass over, 8 units out | 14.0 | 14.6 / 14.9 |
- **The ledge attacks' reach up** stays near the cast's: the slow one 11.4 (median 12.2), and the quick one rakes up to 15.5
  (median 18.8, where the cast's leg swings arc higher).
- **Root motion is his own.** The ledge attacks key their own TransN path: from CliffWait's hang (12.56 below the ledge
  and 2.0 out, Mario's template path at his height), through a dip and the pull-up, onto the corner on the cast's median
  frame, then a step or two in. The get-ups start from his lying pose and end in his standing pose, since the engine
  never blends between actions.

**In game** (`director/pummel_ledge_getup_lab.py`, Final Destination, hitbox display on; strips go to `board/`):
- **Pummels:** four pummels on a held Fox each hit on their frame 9 (3%, then 2.7, 2.5 and 2.3 as they stale), and a
  forward throw (8%) and a down throw (5%) still work afterwards.
- **Ledge attacks:** caught from a drop off the left ledge. The quick one is on the stage by frame 19, hits on frame 24
  and ends in Wait 7.7 units in; the slow one is on it by 34, hits on 41 and ends 4.5 in. Both connect on a Fox 14 units
  from the ledge and at the tip, 26 units (the reach plus Fox's front body, less 1.5).
- **Get-ups:** from DownBoundU and DownBoundD between two Foxes. Face up hits the one in front on frame 19, then the one
  behind; face down hits behind first, then in front. Both connect at 13 and at 22 units, the tip on both sides.
- **A short hop over a get-up** (`director/ledge_floor_lab.py`; a Fox short-hopping from 14 units in front, at two
  timings): 2 of the 4 hops are hit, the ones low enough, and the two at the top of Fox's hop clear. Mario's get-ups give
  the same 2 of 4 (`LAB_CHAR=mario`), so the coverage plays like the cast's.

### 6d. Around the moves: the ledge and the floor (2026-09-28)

The states the moves start from and return to are his own blockout motion now. Their scripts stay the template's (sounds,
intangibility), and so do their lengths and the template's root-motion timing (the frame he stands on the stage, the
distances he rolls). `rig/states.py` has the keys.

- **The ledge catch is continuous.** The engine puts a catch at the ledge plus CliffCatch's TransN path, whatever
  position the ledge-grab box caught him in: from beside the ledge to ~15 units out, and 10-13 below it (his box is
  still Mario's: width 12, y-offset 15, height 10). Borrowing Mario's path, which starts 12.9 units out, he jumped outward
  up to ~7 units on the grab frame. A Geno-only hook in the decomp (`ftcliffcommon.c`, `#ifndef MUST_MATCH`) keeps him
  where he grabbed and eases the difference out over CliffCatch's first 6 frames, along his own path (a reach, a swing
  under the lip, into the hang). In game every catch moves the body at his own falling speed or less: falling near and
  far, drifting in, fast-falling, and Star Road from above (caught mid-travel) and from below (caught falling after it
  pops over). The offsets it absorbed were up to 7.6 units.
- **He hangs from the ledge.** The hang holds its TransN still, and fighter-build collapses a constant track into one
  key, which the game evaluates once. The engine takes TransN out of the skeleton every frame, so from CliffWait's
  second frame he was drawn standing on the ledge corner, and his hurtboxes were up there too. `anims.still_transn`
  keeps two keys for any root-motion action whose TransN holds still: CliffWait, and the wall and ceiling techs, whose
  offsets had been lost the same way. His palms now grip the lip, where the climbs' IK plants them.
- **Climbs, ledge rolls and ledge jumps** start from that hang and follow the ledge attacks' pull-up. They stand on the
  stage on the template's frames (20 quick, 34 slow), then step in (the climbs), roll 35 units (the rolls), or push off
  into the tuck the jump's second part starts from (the jumps). Beyond his own movement (a fall, the jump's launch), no
  body step at a change of action exceeds a unit.
- **The floor:**
  - the knockdown bounces (an impact, a rebound, a smaller one) into the lying pose;
  - the stand-ups sit up or push up into a crouch and rise to the idle;
  - the get-up rolls and tech rolls curl into a ball that rolls along the floor (a key every frame, lifted so its
    lowest point touches);
  - a hit while lying jolts him; the tech in place lands in a crouch;
  - the stamina collapse (DownSpot) buckles onto his face.

  No body step at a change of action exceeds 2 units.

### 6e. Defence and reaction states (2026-09-28)

Dodges, the shield's in and out, hit reactions and tumble, the lying idle, the wall and ceiling techs, the ledge jump's
rise, being grabbed, the dizzy and sleep, the trip and the clank are his own blockout motion (`rig/states_defense.py`).
Their scripts stay the template's (intangibility, sounds, timing), and so do their lengths and root-motion paths.

**They follow the cast's conventions**, sampled from the disc (`datkit fkdir` boards and `datkit bodydata`):
- **Forward roll:** the script reverses his facing on frame 20 (command 0x14), and the model follows at the next state,
  so the roll turns him round and ends facing back. The other rolls end facing the way they started.
- **Spot dodge:** twists toward the camera and back. **Air dodge:** folds and spins round with the arms flung out.
- **Hitstun:** the torso snaps back and the hips are driven back. High hits whip the head back; low hits buckle the knees.
- **Launches:** fold back with the limbs trailing, then open into the tumble.
- **DamageFlyRoll and DamageFall:** DamageFlyRoll spins upright about the vertical; DamageFall tumbles end over end.
  Both loop, and every launch, the wall splat and the trip end on the tumble's first frame.
- **Held high:** he stays upright with the hips pushed back. **Held low:** he leans away. **Asleep:** he sags on his
  strings.

**Hurtboxes against the cast** (`director/labs/body_cover.py` writes `research/body_moves.md`). Heights are shares of
standing height; front and back measure how much farther the hurtboxes reach than standing, so Geno's narrow standing box
(§6b) doesn't count against him. After three tuning passes, every state sits inside the cast's range bar these:

| State | Geno | Cast median | Why it stays |
|---|---|---|---|
| Backward roll, lowest point | 0.39 | 0.57 | The curled ball bottoms out inside the roll's intangible frames |
| DamageFall reach, front and back | 0.31 and 0.33 | 0.19 and 0.20 | His big head capsule swings round in the tumble. He's easier to hit tumbling, in keeping with his fragility. Michael (2026-09-28): keep it, it's extremely minor for balance |
| DownWaitD reach forward | 0.37 | 0.24 | Head first, lying face down: the head and cap |
| Asleep, lowest point | 0.74 | 0.55 | Deeper would sink his planted feet; a sleep with its own leg pose can go lower |
| Trip, depth below his position | 0.02 | 0.29 | The cast's trips drop below the floor line; his lands on it |
| Ceiling bonk and tech, wall-jump tech | short or rare | | 5-26 frames each |

**Shield:** the guard pose, SHIELD_CENTRE and the tilt table are unchanged. The engine draws the body from the shield
pose while he shields, so GuardOn only shapes the ramp in, and GuardOff the way out. `shieldfit.py`: at full shield
every hurtbox is inside, the head worst, by 0.54. Since the stance turned further toward the camera, the best-fit
centre has moved 1.5 forward.

**In game** (`director/defense_lab.py`, production model, strips in `board/`, the sample reel from `--mp4`). Every one
plays through without a pop:
- the rolls, spot dodge and air dodge;
- a jab, a forward tilt, a down tilt and an air hit;
- a launch straight up (tumble, knockdown, stand) and one sideways (tumbling into a ledge catch);
- the tech in place and the tech roll;
- a shield break through its launch, knockdown and stand-up into ~340 frames of dizzy;
- being grabbed (Fox's grab uses the low variant), pummelled three times and thrown;
- his own back throw, and a ledge jump.

At every change of state, the body steps at most 1.7 units more than he moves himself. The largest is the snap into the
struck pose on a hit, which the cast's hitstun also has.

**Being thrown:**
- When Geno is thrown, nothing of his own plays. The victim takes the thrower's Taro animation (a shared 52-node layout,
  not the fighter's own joints), and its XRotN is held to the thrower's ThrowN (the decomp names that part TransN2: its
  Fighter_Part enum is one short from part 16 on, so its 52 is PlCo.dat's "Throw").
- When Geno throws, the victim plays Geno's entries 262-265, on that shared layout, and rides his ThrowN (§6f).

### 6f. Throws: one weapon each (Michael, 2026-09-28)

The v1 throws were plain tosses. Michael: his identity is his gun-hand weapons and star magic, and throws that don't use
them are a missed opportunity, like Fox's and Falco's laser throws. Each throw now shows one signature weapon and keeps
its job (throws make situations, not chains, §7; no regrab on Fox, Falco or Falcon at 0-60%):

| Throw | Weapon | What happens | Numbers (target) | Job |
|---|---|---|---|---|
| Up | **Star Gun salvo** | Pops them straight up, points the Star Gun skyward, fires three small stars into them, like Fox's up throw | throw 4%, then 3 stars 1% each | the vertical pop into juggles |
| Back | **Hand Cannon** | Two clear beats (Michael): the move, swinging them round behind him and holding them at the muzzle; then the blast, the arm folding open into the cannon with a ka-chunk, a short hold, and BOOM, with muzzle flash, smoke and recoil through his body. The shot launches them; it must never read as a toss | 10% | his strongest throw; the ledge kill at high percent |
| Forward | **Rocket Fist** | Holds them at arm's length; the fist snaps into the rocket form, then rockets off the wrist (a small white star at the launch, an unbroken exhaust trail out and back, recoil driving him back) and launches them. Michael (2026-09-28) weighed a Mewtwo-style barrage and a point-blank Beam, then kept this one: the ignition reads as a blast, not a toss. He dropped its cannon-style explosion for the rocket's own launch (2026-09-29) | 8%, 35° toward the ledge | ledge situations |
| Down | **Point-blank Finger Shot** | Pins them to the floor and pumps a volley from the Finger Shot tubes into them, bouncing them into the tech-chase knockdown (like Fox's down throw) | throw 2%, then 3 shots 1% each | the tech chase |

**Weight** (Michael, 2026-09-28): the first cut was too fast, with no ka-chunk. Every throw gets mechanical beats: anticipation, a hold, the weapon transforming and locking, then the release, with follow-through; totals lengthen as needed (the cast runs ~30-60 frames).

**Prime, then blast** (Michael, 2026-09-29): the up, forward and back throws still read fast. "Sort of like a shotgun
pump-chunk-shot, it's very visually satisfying to prime the hit, then deliver the blast." Each gets a beat before its
blast, lengthened by the least that reads, and he accepts the cost ("a slight mechanical nerf ... more than acceptable to
make it look better"): the up throw holds the Star Gun's aim on them before it lets go, and the salvo chases them from
the release (so the stars "reliably link (with simple DI at least...) at lower percents", Michael, 2026-09-29); the
forward throw lifts them onto the
fist's line ("victim rises slightly, holding-hand rises slightly to match") and draws the fist back; the back throw
rocks the cannon back off their chest and rams it home before BOOM. The up throw's stars spray ("the first is straight
up, and the rest spread out a bit to left/right alternating and increasing the width slightly").

**The back throw's BOOM is one chunky single shot** (Michael, 2026-09-29): "the Hand Cannon actually fires multiple large
projectiles, not a single blast". The throw's old sound was SMRPG's Hand Cannon as its battle plays it (cock, cock,
boom), and it read as a double shot. He kept the animation and asked for "a chunkier single-shot blast". It is 550061:
SMRPG's Hand Cannon shot fired once, two semitones lower, with a hard attack and a low thump of our own under it
(`sound/gunfit.py` `shot()`). Its attack is its peak, heard on the BOOM frame (+0.2 frames). The back air, down smash
and slow ledge attack keep their cock-then-boom.

The up- and down-throw shots are **real projectiles**, as Fox's lasers are: the engine's per-fighter throw routine
(`ftFx_Throw_Anim` for Fox, called from `ftCo_Throw.c`) fires them when the throw's script sets a throw flag, so good DI can
slip some, and in doubles they can hit others. The cannon and the rocket fist are the launch itself. Victims play the
shared-skeleton throw animations (entries 262-265, kind 0x21) and ride ThrowN, which his throws animate.

**Built and measured** (2026-09-28: `rig/poses_throws.py`; in game on the Gate 2 model by `director/throws_lab.py`, on Fox
at Final Destination unless named). Frames are 1-based. Every throw is weight-independent now (the template's mask played
them at 100 / weight: 1.33x on Fox), so its beats keep their timing on every opponent; throws use one weight for
everyone, so Falco and Falcon launch exactly as Fox does (their own gravity sets the flight).

| Throw | Beats (frames) | Release | Total | Numbers | Launch on Fox (0 / 30 / 60%) |
|---|---|---|---|---|---|
| Forward | hand-off 1-4; held at arm's length 6-11; the rocket locks (ka 11, chunk 13); the lift 15-20, hoisted onto the fist's line, the hand rising with them; the prime 21-22, the fist drawn back, the left hand clamped, braced; ignition 23, the fist blasts off carrying them; it docks back on the wrist 38 | 27 | 55 | 8%, 35°, growth 70, base 64 | knockback 80 / 95 / 110 (tumble from 0%); lands 39 / 48 / 60 units out (2026-09-28; since the lift, 1-2 further) |
| Back | the move: hop pivot 3-12, brought up short at arm's length 13-19; the blast: the cannon locks against their chest (ka 20, chunk 22), braced 24-29, the prime (rocked back off them 30 with a rattle, rammed home 31 with a clack, a beat), BOOM 33, the recoil held 34-37 | 33 | 59 | 10%, 35° back (reversed facing), growth 75, base 62 | 82 / 101 / 120; 30 / 43 / 59 behind |
| Up | dip 1-5; heave 4-8, onto his left hand overhead 9; the Star Gun locks beneath them (ka 9, chunk 11); its aim held 11-15, sighting up the barrel at them, a tense on 15; popped off his fingertips 16; stars 17, 20, 23 at 6.5 units a frame, sprayed 0°, 6°, 12°, the widest to the side DI carries them | 16 | 54 | 4%, 90°, growth 100, base 86; stars 1% each | 106 / 118 / 131; peak 27.6 / 32.0 / 38.8 up, airtime 39 / 49 / 60 |
| Down | lift 4-10, held overhead 10-12; slam 15; a beat; the tubes lock (ka 19, chunk 21); shots 24, 28, 32; the pin shoves them off 35 | 35 | 52 | 2%, 40°, growth 50, base 80; shots 1% each | 90 / 94 / 98; the knockdown 36 / 39 / 41 out |

- **The carry.** ThrowN carries them through every throw: out on the rocket fist, round the swing to the cannon's mouth,
  up in front of his face into the Star Gun's line, down onto the floor. None drags them back over him (Fox stays
  5.5-9.3 units in front through the forward throw, 3.3-6.1 through the up throw, 3.1-7.0 through the down throw; the
  back throw swings him from 7 units in front round to 8 behind). Their animations are the cast's own, retimed to his
  beats (Fox's forward throw's victim, the rocket ride; Mario's up throw's, held up overhead), or composed from the
  cast's poses (the back throw: held, turned with the swing, flung out, facing him at the muzzle; the down throw: Fox's
  lift, slam and lying pose, then lying still under his palm through the shots, a flinch on each); `rig/taro.py`.
- **The victims against his hold** (2026-09-29, `throws_lab.py --grip`: the gap between his holding hand's hurtbox and
  their nearest one each held frame, and their body's centre frame to frame, on Fox, Falco, Falcon, Bowser and Pichu,
  against Fox's own throws on Fox). The hands hold them: mean gaps -0.1 to -1.5 on Fox, Falco and Falcon (overlapping a
  little, as a grip does); Pichu -2.4 to -4.0 and Bowser -6 to -9, whose hurtboxes are larger than the hand's reach
  into them (one victim animation plays on every skeleton, as the cast's do). Two donors didn't fit: Fox's down throw's
  frames 25-34 roll the body below its pivot, so his pin held them ~3.5 units into the floor (their lowest hurtbox
  -4.7 on average over 26-34, Fox's own throw's -1 to -2), and they popped up on the release; now authored lying still
  (-1.2; Falco -0.7, Falcon -0.6, Pichu -1.6). The release pops (the release frame's step against the flight's first):
  forward 4.5, back 3.5 (Fox's own 2.3, 4.8); up 9.4 to 4.9 and down 8.1 to 5.6 (Fox's own 12.0, 4.2).
- **The forward throw's lift** (2026-09-29): the rocket fist's line, the path the fist flies from the frame before its
  launch to the release, passed over them: in game their hurtboxes' centre sat 5.0 below it at the launch and their top
  1.0 below (`throws_lab.py --line`; offline, their skeleton's centre 5.7 and head 2.4 below, `throwview.py --line`).
  On the lift the opponent's pivot rises from 1.1 below his fist to 1.5 above it and 0.8 nearer (`GRIP_F`), their
  hanging body lifts with it (Fox's victim frames run back from their sag), and his hand rises 0.7. At the launch their
  centre sits 2.5 below the line and their top 1.8 above it: the fist drives through their upper body. The fist's path
  steepens from 32° to 37°, onto the 35° launch; Fox leaves from 8.7 up instead of 4.8.
- **The up throw's height** (Michael: the old one hardly displaced the target; it peaked ~17 and fell back on him). Fox
  now leaves from 14 up and peaks at 27.6 / 32.0 / 38.8. Fox's own up throw on Fox peaks at 27.1 / 29.9 / 33.0 (airtime
  34 / 40 / 47) and Falco's at 35.5 / 39.0 / 42.9 (39 / 43 / 47): Geno's sits between them, nearer Falco's at 60%. Falco
  and Falcon peak at 32.4 and 31.9 at 0%.
- **The projectiles.** Michael (2026-09-29): "I'm fine with DIing out of the star hits from upthrow at higher percents,
  but ideally it would reliably link (with simple DI at least, perfect smash DI is beyond human capability) at lower
  percents." Now all three stars hit (0.9% each: the throw's own hit has staled the move once) with no DI and with full
  DI either side at 0-80% on Fox, Falco and Falcon; with no DI through 160%. DI first keeps a star off at 90% (Fox DI
  toward his back, Falco either way), 100% (Fox toward his front, Falcon toward his back) and 140% (Falcon toward his
  front). Before (the aim held after the release) full DI kept all three off at 0-120%: by the first star Fox had
  drifted 12-14 units to the side and hung 11-20 above the muzzle, 30-50° off the barrel. The levers, chosen by replaying
  salvos against the logged flights offline (`director/labs/star_sim.py`, which matched the game's hits frame for
  frame): the aim before the release, so the stars fire 1, 4 and 7 frames after it, while DI has carried them only
  ~1 unit a frame; faster stars (5 to 6.5 units a frame); and the spray's handedness. The spray (`ftgeno_throw.c`) is
  as Michael asked: the first star up the barrel, then alternating and widening, k x 6°; its widest (the third) goes
  the way their knockback carries them (DI included, past 0.4 units a frame sideways), the second the other way; with
  no DI the second goes toward his front (logged 86°, 80°, 98°; with DI toward his front 86°, 92°, 74°). Bigger stars
  were not needed (Fox's throw lasers'
  size, 6). In doubles they hit a
  bystander: Falco, full-jumping beside him, took one star in one run and three in another. The down throw's shots meet
  an opponent he has pinned, so they always hit (1, 0.9, 0.9; a held fighter takes half, so each is 2 in the script, as
  Fox's are). Throw totals: up 6.7%, down 4.8%.
- **Regrabs** (Fox, Falco, Falcon, 0-60%): every throw tumbles from 0%, so the opponent techs or lies down on landing,
  and the forward, back and down throws land them 30-60 units away, well before he can act. With best DI no throw is
  regrabbed. The one opening: the up throw with **no DI** drops Fox straight back at his feet, and a dash grab out of
  the throw that connects in hitstun's last frames caught him at 0% and 20% (two of four timings each; none at 40%); DI
  either side lands him 24-30 units away and he escapes. Since the held aim (he is free 5 frames later) the same grabs,
  timed from his first free frame, catch him once in twelve (20%, the earliest timing); none with DI in. Since the aim
  moved before the release (2026-09-29), none of the twelve.
- **The primes' cost** (2026-09-29): the forward and back throws' new frames come before the release, so the opponent
  flies the same and is free as much sooner as he is (Fox mashing, landing and first action minus his free frame: within
  -5 to +4 frames on every forward and back throw try, from the forward throw's higher release). The up throw's came
  after it: 5 frames less advantage on every try. The totals: forward 50 to 55, back 56 to 59, up 44 to 49 frames.
  With the aim before the release (2026-09-29) the up throw is 54 frames, released on 16, and he is free 38 frames
  after the release as at 49: the stars carry no knockback, so landing through DI they add only hitlag, and Fox's first
  action (mashing) comes one frame sooner against his free frame than at 49 on every try.
- **Ledge kills** (his back or front to the ledge, 22 units in; a clean KO is Fox dead before he could act; DI down
  drops the launch to 17° above the horizontal, DI up raises it to 53°): the back throw from 140% with no DI (120% with
  DI down, 180% with DI up); the forward throw from 180% with no DI (160% with DI down; with DI up Fox could still act
  at 160%, and 180% went unmeasured).
- **Effects and sounds.** The rocket fist's own launch (Michael, 2026-09-29: "remove the explosion effect from
  fthrow"): a small white four-point star at the wrist on the ignition (`ROCKET_LAUNCH`) and Double Punch's exhaust
  (`N_EXHAUST`) laid along the fist's tail, frame to frame, out (23-27) and back (33-37) by `moves.exhaust_trail`
  (`poses_throws.rocket_tails`). The cast's common effects: the cannon's flash (1012) and smoke poured from a locator at the muzzle (1043 trails behind its joint, so
  the hidden left hand is turned about and slid there); the Star Gun's scatter of blue stars (1299); the slam's floor
  spikes (1030, Fox's own down throw's); a spark at the tubes (1062). Bank 55: the rattle and the ledge clack make each
  ka-chunk; HANDCANNON the boom, DOUBLEPUNCH the ignition, STARGUN and FINGERSHOT each shot.

## 7. How it fits together: tax, then cash-in

Every piece taxes movement, and every hit leads somewhere (REV MF1, §3.4).

- **The straight lane.** Finger Shot and the Beam force a jump or a shield. A Finger Shot hit up close gives a jab, tilt or
  grab; a full Beam kills.
- **Jumping** meets the up-bent Whirl, a Blast meteor, or up tilt.
- **Shielding** takes Blast columns and Whirl hits within the gap rule (§8), while Geno repositions or stores a Beam.
- **The follow-in (v1.2).** He sends the Whirl and runs in behind it; it grinds their shield (three hits, a 6-frame gap
  after each) while he arrives: the crossup nair behind the shield (out of shield-grab reach), a tomahawk into grab, a
  spaced fair, or a Blast mark on the roll. Every branch has an answer: jump out of a gap, roll, powershield the Whirl, or
  break it with a 6% hit.
- **Getting in** is the answer, and it's where he's fragile: light, a faster fall, combo'd. But up close he has a real
  game (the frame-6 out-of-shield nair, the crossup, the grab), so getting in is a fight, not a free win.
- **Stray hits make knockdowns.** The Whirl's outbound hit, down throw, down tilt and the grounded Blast pop put the
  opponent on the floor 20-60 units away. Then the read, from range:
  - a Blast on the knockdown point covers tech-in-place and the missed-tech getup;
  - Finger Shot covers the roll away;
  - down smash covers the roll toward and a stand-up;
  - a Whirl hovering beyond them covers a long roll away.
  One Blast covers at most two outcomes, so it's a read, not a lock, and knockback growth ends the knockdowns by ~60-80% on
  mid-weights.
- **Offstage is the payoff.** The same pieces cover recovery options: the Blast meteor covers a high recovery, the Whirl the
  ledge snap, Finger Shot the low path. Every recovery keeps at least two ways back (§8).
- **Geno offstage is theirs.** Moderate distance, a readable fold, no hitbox in flight, helpless.

## 8. Rules that end loops (written as invariants the labs assert)

Melee has no burst or combo breaker, so each of these has to end on its own (FG, Mike Z's "assume they already found it").

1. **A ledge grab or helpless fall despawns his Whirl and cancels any pending Blast.** One rule kills planking with stage
   coverage and recovering with coverage.
2. **No Blast below ledge height.** Edgeguards are cast from the stage or above. The Whirl stays usable offstage, since a
   deep edgeguard is a real risk.
3. **Once per target.** The hover, the outbound hit and the recall each hit a given opponent once per throw. Geno Flash's
   sun hits a given opponent once: the burst or the late sun, never both (one hitbox that weakens in place). The burst
   out-hits the late sun at every percent (18% to 12%; knockback 99.5 + 1.52q against 72 + 0.95q at Fox q%).
4. **The shield gap.** No sequence of his hits on a shielding opponent, at any spacing, leaves less than **5 frames**
   between the end of shieldstun and the next hit (the median jumpsquat, 4, plus one: most of the cast can jump out of
   any gap, and jumpsquat-5 characters shield-grab, roll or powershield), and there's such a gap at least every 40 frames.
   v1.1 had 9 (Bowser's jumpsquat plus one); the aggressive direction loosens it. On a hard shield, shieldstun is
   0.45 × damage + 2 frames, after hitlag (`ftCo_80092F2C` with PlCo.dat's constants).
5. **Blast width.** One placement covers at most two of the four tech outcomes, from any knockdown his hits cause.
6. **Shield damage.** A full cycle (Finger Shot, Whirl, widened Blast) removes at most half a full shield. Poke exposure is
   measured at half shield on the five tallest characters.
7. **Knockback growth ends every link** by 60-80% on the heaviest characters, and every link is escapable by DI or SDI at
   every percent.
8. **No stalls.** No aerial special changes his vertical velocity; the Beam charges under normal gravity; back air recoil
   once per airtime.

## 9. Labs (the director) and what passes

| Risk | Pass criterion |
|---|---|
| Planking with coverage | Every ledge-drop, double jump, special, regrab sequence: no Geno hitbox active on stage while he has ledge invincibility |
| Ledge-drop Finger Shot | No more stage-lip coverage per regrab cycle than Falco's laser version |
| Aerial stalls | Max airtime from ledge-drop to landing, any input string, ≤110% of the no-special airtime |
| Final Destination camping | Optimal-approach scripts for Falcon, Marth and Jigglypuff reach close range within ~5 s, taking ≤~15% on average |
| Shield pressure | Every 2-4 piece ordering at every 5-unit spacing, on the eight worst shield-coverage characters: a ≥5-frame gap at least every 40 frames |
| The follow-in | From every 5-unit spacing, 20-60 units: the frame he arrives against the Whirl's grind, and the on-shield advantage of each follow-up (nair in front and behind, tomahawk grab, fair, Blast) on Fox, Marth, Sheik and Peach shields |
| Shield break by chip | No ranged-only sequence breaks a full shield |
| Whirl and Blast strings | Every two-piece string escapable by DI or SDI; none true past 80% on any weight |
| Recall sandwich | Not true on anyone past 30%; SDI-escapable |
| Tech chase | One placement covers two outcomes or fewer; knockdowns end by 60-80% on mid-weights |
| Edgeguards | For Falcon, Ganondorf, Falco, Dr. Mario and the Ice Climbers, at least two recovery paths beat any single setup |
| Throws | No regrab on Fox, Falco or Falcon at 0-60% with best DI and DI mixes |
| Reflector break | Each projectile's damage asserted under the decomp's threshold |
| His recovery | Fox, Falco, Sheik, Marth and Jigglypuff each have a low-risk edgeguard on at least half his angles |
| Frame data | A generated table for every move: startup, active, IASA, landing lag, damage, angle, knockback, shield safety at best and worst spacing |

**Human rounds** (Michael and recruited players, on Dolphin or netplay): record which strategies feel "annoying,
overcentralizing, or overly safe" (Aether Studios on Rivals II, PF P4), timeouts per set (flag more than 1 in 10 games),
and who wins. Overshoot first, then pull back to the top of A tier.

## 10. Matchups to watch

| Opponent | Their best answer | Geno's answer |
|---|---|---|
| Fox, Falco | Rushdown: drill or pillar into shine; laser into grab; frame-1 reflectors; they combo his faster fall | The frame-6 out-of-shield nair, a normal grab, the Whirl grinding their shield; everything under the reflector-break line. He can't out-speed them, so he out-places them |
| Falco's lasers | Faster and cheaper than anything Geno has | The Whirl eats shots under 6%; Beam store; Blast from above (lasers are linear) |
| Sheik | Needles cut through projectiles and interrupt charges | The Whirl's projectile cancel; Blast punishes a grounded needle charge; out-angle her, since he can't out-speed her |
| Marth | Disjoint, and a big grab punish and juggles on a light, faster-falling character | Range: Finger Shot and the Whirl outrange his approach; up tilt against his aerials |
| Jigglypuff | Air mobility, ducks lines, Rest kills a light character | Blast from above, the up-bent Whirl, frame-6 up tilt. Watch for mutual-camping timeouts |
| Peach | Float between his lanes; turnips | Blast hits a floating Peach; Finger Shot at float height; decide whether the Whirl clanks turnips |
| Link, Young Link | Shields block frontal shots | Blast and the bent Whirl |
| Samus | A stored Charge Shot and a long life | His own store; the Blast meteor edgeguard |
| Ice Climbers | The grab | Zoning splits Nana (the hover, the Blast); a normal grab |

**Implementation templates in the decomp** (known to work with Melee's reflect, absorb and clank code): Link's boomerang
(the Whirl's return and recall), Samus's Charge Shot (store and cancel lag), Pikachu's Thunder (a hitbox from above), Young
Link's arrows (a straight lane).

## 11. Decided (Michael, 2026-09-27)

1. **No meter;** Flash is down-B's hold.
2. **Mid-weight, leaning strong** (88 to start); air speed and fall speed are the main levers.
3. **The icon keeps the old right-hand random corner;** random stays on the left.
4. **An aggressive identity** (supersedes item 2's weight): fast zone control and pressure rather than Samus's patience;
   exciting to play and watch; a strong nair (out of shield, crossup, the follow-in); a Whirl slow enough to run in behind;
   paid for with fragility (weight 80, a faster fall, a finicky recovery); tight matchups against the top tiers.
5. **Aerial shape is a design axis:** arcs versus columns, crossups against tomahawks (§6b).

## 12. Character parity: still open

Everything a vanilla character has that Geno doesn't yet (placeholders count as open):

- **Geno Flash's full-body cannon: done** (geno-cannon, 2026-09-29; the hook's spec was geno-fx's). SMRPG turns Geno into
  a blue-and-gold cannon on a wheeled carriage (SPR0030; the capture `~/games/melee/sandbox/geno-fx/fx/refboard/flash_frames.png`),
  and now so does the Flash. ART.md "Geno Flash's cannon" has the model; the interface:
  - **The action:** SpecialLwFlash, 94 frames (`rig/moves.py` `s_flash`). From frame 1 there's the transform sound and
    SMRPG's yellow glow (EfGeData.dat `FLASH_GLOW`); a second glow from frame 60 covers the fold back.
  - **Showing the cannon:** from `FLASH_CANNON_ON` (23) to `FLASH_CANNON_OFF` (76) `flash_cannon(s, on)` shows the body
    group's option 1, the cannon, in place of his whole body, and both arm groups' option 3 (none) (`rig.cannon_commands`).
    The swaps sit on the glow's pulses (measured in `flash_cannon_lab`: the first glow peaks on 5, 11, 17 and 23 and has
    faded by 29, the second peaks on 76).
  - **Resets:** every group reverts on any action change, so a hit, a grab or a KO during the Flash is Geno again on the
    change's frame (measured: hit on Flash frame 39 and 73, KO on 42: the body group is back to 0 on the hit's frame).
    `ftGe_Init_OnDeath` defaults every group at each spawn.
  - **Its joints:** `CannonN` (the carriage), `CannonBarrelN` (the barrel, on the trunnions) and `CannonWheelN` (the
    wheels), TopN's last children (`rig.CANNON_JOINTS`, joints 71-73; the decomp's `FTGE_JOINT_CANNON*`). They're new
    because every existing joint carries a hurtbox or an ancestor of one, or is the ECB, the camera target, a physics
    chain, a part pose or an engine attach point; appended last, no existing joint moves index. The cannon's motion is
    `poses_air.cannon_pose`.
  - **The muzzle:** `ftGe_FlashMuzzle` (decomp `ftgeno_specials.c`) is `CannonBarrelN`'s tip, `FTGE_CANNON_MUZZLE`
    (`rig.CANNON_MUZZLE`, 7.08) along its +Z: 6.76 ahead, 6.93 up on the shot.
  - **The shot:** the fireball leaves the muzzle on frame 49 and flies 5 frames to the sun's centre (30 ahead, 14 up),
    where the sun spawns on the script's flag at 54. The barrel is pitched 16.9° on 49, the fireball's path 16.92°.
  - **Budget:** 1,344 triangles high, 168 low, two textures (24 KiB), shown only while the body (5,034) is hidden.
  - **His hurtboxes follow the cannon** (Michael, 2026-09-29: "Makes sense on the cannon hurtbox change, but careful not
    to make it too small"). While the cannon shows, his hidden body lies curled in it (`poses_air.curl_pose`): the spine
    along the barrel, the head at the muzzle, the hips at the breech, the legs folded back over the breech and down to the
    wheels, the arms down the wheels. It rides the barrel's frame (the aim, the kick, the roll back, the hop), cuts in on
    23 as the cannon comes in and blends back to the Flash's own pose over 66-73, so the body he shows on 22 and from 76 is
    unchanged. Its parameters were fitted to the cannon's side silhouette (`labs/cannon_hurt.py fit`);
    `GENO_FLASH_CURL=0` builds without it (the A/B the checks below ran against).
    - **Measured** (`research/flash_hurtboxes.md`, remeasure.sh; the side view, rasterised): standing, his hurtboxes' area
      is 67.7 and their top 15.0; the cannon's silhouette at full size is 64.3 (0.95 of that) with its top at 9.15 (0.61).
      Before, the Flash kept his crouch: area 70 (1.03), top 13.8, covering 50% of the cannon with 54% of their area
      outside it (his head and shoulders over the barrel). Now, at full size (frames 30-66): area 65.1 (0.96), top 9.15
      (0.61), covering 90% of the cannon with 11% outside (at most 12%: the waist's capsule is fatter than the barrel).
      The uncovered 10% is the thin trail and the muzzle's lower lip.
    - **The cast's comparable states** against their own standing hurtboxes (area, top): Samus's Morph Ball 0.22, 0.42
      (the game swaps her capsules for one sphere of radius 2.64 on joint 2, about her ball's own size:
      `ftSs_SpecialLw_8012AEBC`), Yoshi's egg roll 0.68, 0.72, Bowser's Whirling Fortress 0.84, 0.79, Jigglypuff's Rollout
      0.96, 0.96, Kirby's Stone 0.99, 1.00, Jigglypuff's Rest 1.02, 0.96 (each about its own root: TransN, the fighter's
      movement, taken out). Each keeps its hurtboxes at its own visible form, whatever its size.
    - **The guardrail:** area at least the cast's median, 0.90 of standing (61.2): the cannon lands at 0.96, and the
      swaps dip to 0.89 for two frames (68-69, as the curl lets go; the ball itself is 0.90 on 22). Top at least the
      cast's lowest, 0.42 (6.3): it lands at 0.61 (0.68 in the kick), between the Morph Ball (0.42) and the egg (0.72). The cast's
      median top (0.88) would need capsules 4 units over the barrel, a floating head; the cannon's top, approved at its
      size, sets his, as each cast form's does.
    - **Gameplay:** frame data unchanged (the script and its timings are the same). Aimed (frame 40) his hurtboxes reach
      3.1 units further back (the trail; 4.9 in the recoil's roll back), 0.55 further forward (the muzzle) and 4.7 lower
      on top; the ECB's top (CapN, now at the muzzle) drops from 12.55 to 7.8 and its back (the knees) goes from 0.15 to
      -4.3 (-6.1 in the roll back). The Flash lab's hits, the interrupts and the
      KO land on the same frames for the same damage; Fox's forward smash KO now strikes a mid capsule and plays
      DamageFlyN (88) where it struck a high one (DamageFlyHi, 87): the same knockback and path.
    - **The fold out stays clean:** the capelet's side panels and the cap's point hang from the neck and head, so through
      the curl the neck keeps the Flash's own place and turn and the head its own turn (only its place moves, to the
      muzzle). Traced (GENO_DYN_TRACE, the dynamics' own solve), the side panels come out of the fold within 1° of before;
      the back panel, nudged by the curled body's collision spheres, is 32° off its rest on 76 (4° before) and back by 82,
      and the cap's floppy point swings further (70° at frame 80, 44° before) and is back by 88: both under the glow,
      which peaks on 76. The frames he shows (1-22, 76-94) are otherwise the same pose.
- **Kirby's copy ability and hat: done** (Michael, 2026-09-27; the hat 2026-09-29). Kirby who swallows Geno, or a Kirby
  holding Geno's copy, gets Kirby's version of the Geno Beam (tap for Finger Shot, charge, release, on the ground and in
  the air) with Geno's frame data, sounds and projectiles, played on the Samus copy's animations and lost like any copy
  (taunt, 1 in 32 knockback hits, a lost stock). Decomp `ftKirby/ftkirbyspecialgeno.c`; labs `director/kirby_lab.py`,
  `kirby_trio_lab.py`, `kirby_cpu_lab.py`, `kirby_hat_lab.py`. While he holds it he wears **Geno's own cap**: the
  production model's blue stocking cap with the rolled band, the yellow ribbon emblem and the two orange paper curls,
  refitted to his head. It goes on with the copy and comes off with it, on all six Kirby costumes, whatever Geno's
  costume (one model for all, as the vanilla caps).

  **The hat** (`PlKbCpGe.dat`; built from disc and model data, so it lives in `$MELEE_WORK/kirby_hat/` and on the disc,
  never in the repo). Rebuild and install:
  `.venv/bin/python projects/geno/rig/kirby_hat.py build --install` (a few seconds; `--set scale=1.9` and the like try a
  variant, `--out DIR` builds it elsewhere). The steps:
  - Blender (`rig/kirby_hat_model.py`, headless) takes the four cap meshes from `art/model/geno.gltf` (crown, band,
    curls, emblem) and the low model's cap from `geno_low.gltf`, posed on his skeleton with the point's chain drooped 12
    degrees a joint (a static drape: the hat file has no physics, like the vanilla caps).
  - It scales them 1.85 about the band's centre, leans the band back 26 degrees (Geno's own band leans 5.6) and seats
    the underside of the band's roll on Kirby's head sphere (centre (0, 5.58, 0), radius 5.0, fitted to `PlKbNr.dat`),
    0.15 inside it. A band hugs a ball best at its equator, which is how Geno wears it; on Kirby that covers his eyes,
    so the band sits on its lower edge as the vanilla caps do. Band edge: y 9.07 over the eyes, 5.82 behind (Luigi's cap
    9.43 and 5.65). Scale 1.72 perched it like a beanie; 2.0 covered his eyes.
  - It decimates each mesh to the vanilla budget (crown 312 to 140 triangles, band 192 to 71; curls 100 and emblem 48
    kept close to the source). The low model is Geno's own low cap (40, the emblem painted on) plus one layer of each curl,
    double-sided, at 36: collapsing both layers together shreds them, and the magnifier won't show the back-face lighting.
  - `kirby_hat.py` downscales the textures (crown 256x128 to 128x64, band 256x64 to 128x32, emblem 128x64 to 64x32,
    curls 32x128 to 16x64), and datkit's `kirby-hat` (`HatBuild.cs`) writes the meshes as rigid DObjs on Luigi's cap's
    joint with clones of its cap material, the visibility row (normal, low, normal), +0xC NULL, GX buffers aligned.
  - `check` then passes it, and `menus/gxalign.py` finds its 28 GPU buffers aligned. **Numbers** (datkit `meshstats`, which now reads hat files): normal 359 triangles in 4 DObjs
    (Luigi 360, Mario 332, Link 344), low 76 in 2 (Luigi and Mario 78, Link 96), 4 CMP textures 7.5 KiB (Luigi 18.2, Mario
    14.2), file 16.6 KB (Luigi 49.0).
  - **Checked in game** (`kirby_hat_lab.py`: KBHAT=costumes for the six costumes, idle, squat, jumps, the copy's Finger
    Shot, Beam and air charge, and the taunt that takes it off; KBHAT=compare:luigi|mario|link for a vanilla cap beside
    it at the same scale; KBHAT_GENO_COLOR for Geno's costume; `labs/kirby_hat_board.py` for slate-synced stills and
    strips).

  **The hat interface** (what the file provides):
  - **File:** `PlKbCpGe.dat` in the disc's `files/`, root symbol `ftDataKirbyCopyGeno`. The game looks for it once at boot
    and then preloads, loads and draws it like the vanilla caps (`ftKb_SpecialNGe_HatRow`, `ftKb_SpecialNGe_HatLoad`);
    without it Kirby wears no hat while he holds the copy.
  - **Layout:** the root is a `KirbyHatStruct` (0x20 bytes), as in Mario's and Luigi's caps (`PlKbCpMr.dat`,
    `PlKbCpLg.dat`, whose file structs are 0x18 long):
    - +0 `HSD_Joint*`, the hat: one root joint with the caps' translate (0, 5.62, 0) and the meshes (DObjs) on it, at most
      32. It's drawn with the matrix of Kirby's joint 6 (at (0, 5.62, 0), unrotated, in his rest pose), so the hat file's
      space is Kirby's rest model space.
    - +4 `FtPartsDesc`: `model_num` 1 and a visibility row of four `FtPartsVisLookup*`: [0] the normal mesh's DObjs, [1] the
      low-detail mesh's, [2] the normal again, [3] NULL.
    - +0xC, five words: NULL. No articles: the copy fires Geno's own Finger Shot and Beam from `PlGe.dat`.
  - **Art:** one model for all six Kirby costumes; CMP textures and the caps' material setup; GPU buffers on the 32-byte
    grid.
  - **Tools:** `rig/kirby_hat.py build [--install]` builds it, `check FILE` checks a file against this, `install FILE`
    puts it on the disc, `standin Lg` installs a vanilla cap renamed as a labelled stand-in, `remove` goes back to no hat.
- **Art:** his model is the production one (Gate 2). His menu art is rendered from it in game since 2026-09-28:
  `director/portrait_lab.py` freezes up to four Genos (one per costume) in the Geno Beam's charge with the stage hidden,
  and renders each on black and then on white; `menus/portrait.py` solves each pixel's colour and coverage from the pair
  (difference matting: exact edges, no key colour to fight a costume) and crops the art, cast-style:
  - the character select portrait, one per costume (136x188): the charge from 45 degrees in front, head at the top,
    cropped at the knees, his face and both heavy-lidded eyes (his look in SMRPG's art) with the steel barrel forward;
  - the stock icon, one per costume (24x24, 15 colours and a dark outline), from the same shot's head;
  - the CSS icon (costume 0's head in the icon frame, the name band cut from the disc's letters) and the VS Records face.
  `menus/build.py` keys them into the four menu files (portrait rows at 25 + 30 x costume; HUD and results stock icons at
  180 + costume) and `menus/out/install.sh` installs them. Verified in game: the CSS doors, the grid icon, the HUD, the
  results panels and the VS Records screen. Open: the winner banner and name label are still spliced from the results
  screen's own letters (fine), and the Japanese menu files aren't patched.
- **Victory poses:** his own since 2026-09-28 (`rig/states_misc.py`, written by datkit `DemoBuild.cs` into
  `GmRstMGe.dat` and PlGe.dat's demo rows 0-9; the decomp's results table and demo strings point at them): Win1 (B) twirls
  on the spot and points his gun hand at the camera with a wink, Win2 (Y) is a curtain call (the brim tipped, a stiff
  bow, the brim pulled low), Win3 (X) springs up into a Star Road V; losing, he claps, wooden.
- **Victory fanfare:** his own since 2026-09-28: `ff_geno.hps` (7.99 s, -15.0 LUFS like Mario's), our orchestral
  arrangement of Super Mario RPG's post-battle level-up music (ROM track 9, "Victory"), transcribed from the cartridge's
  sequence data and checked against its sound driver. The decomp plays it as HPS id 0x63 (`LBAX_HPS_GENO_FANFARE`, past the
  vanilla table, so 0x62 stays "no music"); a disc without the file plays Mario's. The file and its sources are game-derived
  and stay in `~/games/melee/work/music/fanfare/` (NOTES.md there); `tools/machinima/melee/audio/hps.py` builds the stream.
  `victory_lab.py` hears it (the director turns the music back on for the results).
- **Voice and character sounds:** he's silent, as in Super Mario RPG. Mario's voice (jumps, dodges, taunt, ledge, damage and
  KO cries, his victory poses, the crowd's "Ma-ri-o!") was still in the template's voice table and scripts until 2026-09-27;
  fighter-build now silences every sound from Mario's bank. His taunt has his own movement sounds (a clack, a creak, the
  joints clicking straight; 2026-09-28). His crowd cheer is his own (chant #2, 2026-09-28). On a KO and a star KO he
  stays silent (Michael, 2026-09-29): SMRPG gives him no hurt or KO sound, and Melee's shared KO boom, crowd and star-KO
  twinkle still play.
- **Moves on Mario's scripts:** none since 2026-09-28. The pummel, ledge attacks and get-up attacks are his own (§6c).
  Item swings and the screw item are the engine's common ones. His down air's landing hit (Mario's) was removed
  2026-09-27.
- **Placeholder motion still around the moves:** the attacks and specials (after the weapon-form parts).
  The ledge and floor states are his own since 2026-09-28 (§6d), and so are the dodges, shield in and out, hit reactions,
  tumble, techs, grabs, dizzy and sleep (§6e).
- **Items and character moments:** his own since 2026-09-28 (`rig/states_items.py`, `rig/states_misc.py`; checked in
  `director/items_lab.py` with real items): the pick-ups, every light throw (ground, dash, air), the crate carried and
  thrown, the bat and sword swings, the Ray Gun, the Super Scope, the hammer, the parasol, the Screw Attack, the idles
  (Wait1's breath and sway, Wait2's look at his hand), the taunt (a marionette's curtain call) and the entrance.
  ItemBlind has no state that plays it: none of the 341 common motion states names the animation, and no fighter's idle
  lists do (`datkit chances`); his, like the cast's, is a blinded grope (2026-09-29), checked in game through the director's
  `anim` cue. The light throws let go on their scripts' release frames (measured in game: 7, and Hi 9, dash 4, air Hi 6, the
  smash down throw 5), and each throw's release key lands on that frame (`states_items.RELEASE`). Heavy items: a crate is 15 a side, as tall as he is,
  and hangs on ThrowN by the centre of its near face (ItCo.dat's attach joint; measured in game). His arms can't hold it
  out past his nose or over his cap, so he tosses it up onto his head and carries it there, arms up either side of his
  head bracing its bottom (the cast carry it overhead; Mario hunched under it), and pitches it off for the heavy throws.
  His hands (Gate 2): the hand holding an item grips it
  (the decomp's `ftGe_Init_OnItemPickup` and its drop, visible and invisible partners, as the cast's: the engine keeps
  model part 1's pose while he holds one), the hammer takes his left hand too and pulls his cap low, and the win poses
  point, grip the brim and make fists. Open, Michael's call: every other action's fingers are the animation's, straight;
  a relaxed default (the open pose kept on both hands the way the item grip is) would change the whole moveset's look.
- **Costumes:** six, Melee's maximum (Captain Falcon and Kirby have six). Michael's call (2026-09-29): "the 5 from
  SMRPG are excellent", Geno in his party's colours, and a black-and-red Dark outfit, a fan favourite, as number 6.
  Mallow was his call from the start.

  | # | Code | Costume | Colours (texture targets, `model/costumes.py`) | Team |
  |---|---|---|---|---|
  | 0 | Nr | Geno | his own: blue cap and capelet, gold ribbon and lining | blue |
  | 1 | Re | Mario | red cap and capelet, his cap's white badge as the ribbon, overalls-blue lining, gold buttons (clasp) | red |
  | 2 | Gr | Bowser | shell-green cap and capelet, red hair (curls, piping), cream belly (lining, collar), white horns (ribbon) | green |
  | 3 | Wh | Mallow | his off-yellow cloud body (cap, collar), pink hair and shoes (curls, ribbon, boots), sky-blue pants (capelet) with white (lining, soles) | |
  | 4 | Pi | Peach | pink cap and capelet, blonde curls, her blue brooch (ribbon), white gloves (lining, collar) | |
  | 5 | Bk | Dark | black cap, capelet, collar and boots; red curls, ribbon, lining, clasp, collar piping and soles | |

  Dark's split: two were rendered in game. They're the same at stock-icon size (the collar barely shows); at the game's
  distance the one with his own brown boots and a red collar read as Geno in a black cape, and the black collar and boots
  with red piping and soles as one outfit, so that one is built. The other stays in the palette table as candidate Bd,
  with Star (Ye, gold) from the first review. Changing the set is a palette-table edit and a rebuild (`SET` in
  `model/costumes.py`, then `costumes.py --c` into the decomp).
  Geno Flash's cannon follows the costume: its barrel takes the capelet's colour (SMRPG's barrel is his capelet's blue,
  down to the points of its hem), and its brass, knob and carriage never change (2026-09-29).
  How it works: `model/costumes.py` recolours the cap, ribbon, curls, capelet, collar, lining, clasp and boots in OKLab,
  each texel keeping its offset from its colour family's mean so the felt and the folds survive (wood and the weapon forms
  never change); rig.py writes a model folder per costume beside the rig json; datkit fighter-build writes
  `PlGe<Cc>.dat` each (refused unless its meshes match costume 0's) and one lookup row per costume in PlGe.dat. The
  decomp's `ftgeno_costumes.h` (generated by `costumes.py --c`) lists them with the team row (red 1, blue 0, green 2);
  `ftGe_NumCostumes` counts the costume files on the disc at boot, so a disc with only PlGeNr.dat (the blocky rig, an
  older sandbox) offers one costume as before. Nothing downstream assumes fewer than six: the character select's
  portrait row is hud + costume x 30 (175 for Dark), the HUD and results stock icons 180 + costume (185), the results
  standings keep the costume in 6 bits, the records are per character. Kirby's copy doesn't read his costume. Verified
  in game (labs `costume_lab`, `costume_match_lab`, `costume_css_lab`, `costume_team_lab`): each costume in matches, the
  HUD and results (Dark winning), the CSS's X/Y cycling through all six and wrapping, a second Geno taking a free
  costume, the red team's costume; the matching build still matches.
- **Single-player modes:** Classic, Adventure, All-Star, Target Test, Multi-Man and Home-Run keep per-character records with
  no row for him, so the 1P select screens hide him (Training is the exception); he takes Mario's trophies and target stage.
- **Japanese menu files** (the `.dat` versions of MnSlChr, GmRst, MnMaAll, IfAll) aren't patched.

## Changelog

- **2026-09-29, the back throw's BOOM is one chunky single shot (Michael, §6f; geno-fxnormals):**
  - The old sound, 550002, is SMRPG's Hand Cannon as its battle plays it: ROM 109 triggered three times, 6 frames apart.
    It read as a double shot, and its boom was heard 12.1 frames after the BOOM frame (33).
  - The new sound, **550061 GENO_HANDCANNON_SHOT**, is ROM 109 fired once, the same boom 550060 cuts from the triple.
    It's two semitones lower, the first 20 ms are lifted 6 dB and the swell after them eased 4 dB, and it has a 4 ms
    noise click and a 92 -> 44 Hz sine thump of our own under it. 0.40 s at 22050 Hz, peak -3 dBFS.
  - **Measured against 550002:**
    - one attack, where 550002 had three (at 14, 106 and 168 ms);
    - its peak is its attack, at 2 ms (550002 peaked at 126 ms);
    - below 150 Hz, -5.0 dB of its energy against -10.4, and the loudest 100 ms there is -15.2 against -18.8 dBFS;
    - 30 dB down at 358 ms against 604, and it rings to -20 dB 318 ms after its peak against 382.
    - In game (`sound/soundsync.py`, the slate pulse), its attack lands +0.2 frames after the BOOM frame, which is also
      the frame the flash is first seen.
  - Only the back throw changed; back air, down smash and the slow ledge attack keep their cock-then-boom. The
    candidates are local, for a listen: the new shot without the pitch change, four semitones down, a louder thump, no
    thump.
  - **The bank:** 61 -> 62 sounds (the first 61 byte-identical), data_len 390272 of the 393216 booked. The decomp gate
    goes to 550061.

- **2026-09-29, polish: the low model's face, and the capelet over raised arms (geno-cannon; HANDOFF §7's two items).**
  Model only: no joint, animation, hurtbox, hitbox or frame changed (the remeasure's research diff is empty).
  - **The low model's face.** The game draws the low model in the off-screen magnifier bubble, at about 7.2 px a unit
    in a res-3 dump (`director/lowface_lab.py`: Geno, Mario and Link held above the screen, next to the high models at
    the same pixels). The cause was the texture's layout more than its format: one 64x64 CMP texture held the whole
    head, face and back mirrored, so the eye was 9x12 texels and CMP's 4x4 blocks smeared it (the eye's block 22.8 dB
    against its source, with a grey block beside it; 36.5 dB over the texture), and the low head had no nose. No mips
    (the cast's low models have none either). Now the low face has its own 64x64 texture of the face only (twice the
    texels across it), with the high model's eye drawn bold and large (28x14 texels), in CI8 (a 256-colour palette:
    worst 8x8 block 33.4 dB, largest error 7 levels, against CMP's 63). The back of the head uses the high model's
    `headback` texture and the nose the high model's nose mesh (6 triangles), both already in the file.
    | | before | after |
    |---|---|---|
    | low face texture | 64x64 CMP, 2,048 B, the whole head | 64x64 CI8, 4,608 B (4,096 + 512 palette), the face |
    | texture bytes only the low model uses | 2.0 KiB | 4.5 KiB |
    | low triangles (without the cannon) | 368 | 397 |
    | PlGeNr.dat | 450,624 B | 453,000 B |
    The cast's low models (from the disc): Mario 332 triangles, 11 textures, 38.5 KiB; Link 391, 15 textures, 57.4 KiB,
    two of them CI8 (8.5 and 16.5 KiB). Link sets the precedent for CI8 on a low model.
  - **The capelet over raised arms.** Measured offline with `model/cape_clip.py` on every action's FK (209 actions,
    8,042 frames, each arm): the area of the front panels that lies inside the arm (the elbow and wrist balls and the
    upper-arm and forearm lathes, deeper than 0.1), and how deep. Then in game (`director/capelet_lab.py`, close from
    three quarters, from the side and at match distance). Gate 2's skinning hung the panels on the torso and the chains,
    so a rising arm went through the panel's face. The fix is in the skinning (ART's note): the panels now ride the arm
    by their distance from it in the design pose (`geno_geo.CAPE_ARM`: rows 1-2, the dome, take 0.4 and 0.8 of the
    upper arm within ~1.2-2.3 units of it; the skirt rows 0.2 of the forearm), fitted by `model/cape_fit.py` against
    the measure (the cut area, the raised-arm cut area counted again, penalties for stretching the panels past Gate 2's
    worst and for moving how they hang in the idle, walk and run). `GENO_CAPE_GATE2=1` builds the old rule.
    | every action, each arm | Gate 2 | after |
    |---|---|---|
    | arm-frames with more than 0.25 sq u of panel inside the arm | 11,937 of 16,084 | 9,918 |
    | mean cut area (sq u) | 1.10 | 0.85 |
    | with that arm raised above horizontal (4,214): frames over 0.25 sq u | 4,022 | 1,607 |
    | ... mean cut area / 90th percentile | 1.27 / 1.67 | 0.36 / 0.93 |
    | the panels' worst stretch (99th percentile edge growth, units) | 2.13 | 1.96 |
    By move (frames with more than 0.25 sq u cut with an arm raised; mean cut area): the Flash and Blast cast (down B)
    48 -> 2, 2.69 -> 0.29; up smash 10 -> 2, 1.75 -> 1.23; up air 15 -> 1; up tilt 7 -> 6, 1.73 -> 1.18; up throw 33 -> 8,
    2.74 -> 1.97; the high forward smash 13 -> 0; the Beam's charge 21 -> 0; the taunt unchanged, 18 -> 18. The full table is on the review page. The idle's hang moved 0.06 units on average (0.43 at most).
  - **What got worse:** skinning is static, so a panel that rides the raised arm also follows it when it swings down
    and forward. 131 actions cut less, 67 more (by more than 0.05 sq u): the shield (4.01 -> 4.71), the item swings,
    the light down throw (0.99 -> 1.97), some landings, the walk (1.17 -> 1.69). A refit that charged every action's
    growth found no better point. The lever past this is pose-driven: a helper joint per side, keyed from the
    shoulder's elevation, so the panel rides the arm only when it rises. That adds two joints and a derived track to
    every action; it's Michael's call.
  - The capelet's and lining's AO bake moved a hair with the new rest shape (max 19 levels on 642 of 65,536 cape
    texels, 10 on the lining); the costumes recolour them as before.

- **2026-09-29, the up throw's stars link through simple DI, and the throws' victims fit his hold:**
  - Michael: "I'm fine with DIing out of the star hits from upthrow at higher percents, but ideally it would reliably
    link (with simple DI at least, perfect smash DI is beyond human capability) at lower percents." With full DI either
    way no star hit at 0-120% (the held aim let them drift 12-14 units). Now all three hit at 0-80% on Fox, Falco and
    Falcon with full DI either side, and through 160% with none; DI first saves them a star at 90-140% (§6f The
    projectiles, with the table).
  - How: the aim beat moved before the release. He heaves them onto his left hand overhead (9), the Star Gun forms
    beneath them (ka 9, chunk 11) and holds its aim (11-15), then he pops them off his fingertips (16) and the stars
    chase them at once (17, 20, 23), faster (5 to 6.5 units a frame). The spray keeps Michael's look (first up the
    barrel, then alternating and widening by 6°), its widest star now going the way DI carries them. Chosen by
    replaying salvos against the lab's logged flights (`director/labs/star_sim.py`; it matched the game's hits frame for
    frame); bigger stars weren't needed.
  - The trade: the held aim is 5 frames (11-15) instead of 7, and it holds them up rather than follows them; the throw
    is 54 frames (49), released on 16 (11), with the same 38 frames after the release, so the advantage and the flight
    (released 0.15 higher: peak 27.7) are unchanged (Fox, mashing, acts a frame sooner against his free frame); the
    no-DI dash regrab (1 in 12) is gone.
  - The victims (HANDOFF §7), measured against his holding hand and Fox's own throws on Fox, on Fox, Falco, Falcon,
    Bowser and Pichu (`throws_lab.py --grip`): the down throw's pin sank them ~3.5 units into the floor over its
    second half (Fox's donor frames roll the body below its pivot) and popped them up on the release; it is now
    authored lying still with a flinch on each shot (their lowest hurtbox -4.7 to -1.2 on Fox; the release pop 8.1 to
    5.6). The up throw's new overhead hold uses Mario's up throw's lifted pose (its release pop 9.4 to 4.9; Fox's own
    up throw's 12.0). The forward and back throws' donors fit (§6f The victims against his hold).

- **2026-09-29, KO sounds (Michael):** "Silence is fine". Geno has no KO or star-KO cry, as in SMRPG, where he never
  vocalizes and has no hurt or KO sound; the shared KO sounds play as for everyone.

- **2026-09-29, Geno Flash's finishing flash (Michael):** "the original's neat little flash effect at the end of the
  animation was a very nice touch, as were the rotating stars; the new version ends a bit plainly. Can we add in a
  similar finishing flash the top version has, both with a star instead of a diamond alongside the circular effect?"
  As the sun goes, its red silhouette flash (kept: the two work together, the star drawn over it) now carries a
  finishing flash: a pink-hot five-point star (the family of his other stars) where the old four-point flash was,
  popping at half the sun and swelling past its edge while it spins a sixth of a turn; a round ring running out round
  it (the old one was the Whirl's oval); and small gold stars thrown out, spinning away. Sized to the new sun (radius
  28): about 17 frames, the stars 25. Visual only: hits and timing are unchanged.

- **2026-09-29, Geno Flash's burst to 18% (Michael):** "I'd tune the sweetspot damage and knockback down a little
  more. The charge and control are both quite a bit better than PK Flash; take it down to 18%." The burst is now 18%,
  45°, KBG 95, BKB 55 (was 20%, 100/55). Measured in kill_lab on Fox from centre stage, clean KO at no DI / optimal DI:
  | 18% burst, KBG / BKB | 100 / 55 | **95 / 55 (built)** | 100 / 50 | 95 / 50 |
  |---|---|---|---|---|
  | kills Fox at | 70% / 70% | **75% / 75%** | 75% / 75% | 80% / 80% |
  - Built: 95/55, 10 points after a full PK Flash (65% / 65%). It trims the growth (the finishing lever) and keeps the
    base, so the burst's send at low percent is unchanged. 100/55 (the old sun's numbers) would kill only 5 later
    with no knockback cut; 95/50 is the next step if it still reads strong.
  - The late sun is unchanged (12%, 85/45; 150% / 190%). The burst out-hits it at every percent: at least 28
    knockback units more at 0%, the gap widening with percent (§8 rule 3). Size, timing and the one-hit rule are
    unchanged.

- **2026-09-29, Michael's calls on the Flash cannon and the rocket-fist down air:** the down air's fist clipping
  through the floor on landings mid-flight is acceptable (as Ganon's and Falcon's down-air legs do); the cannon's
  hurtbox height (0.61 of standing, the cannon's own top) is acceptable; the cannon's fold-back (the capelet's back
  panel and the cap point swinging a few frames longer, under the glow) is acceptable. The Flash's burst goes to 18%
  with a little less knockback ("The charge and control are both quite a bit better than PK Flash"): done, 18%, 95/55,
  75% (the entry above).

- **2026-09-29, Geno Flash: smaller, and a sweetspot then a sourspot in time (Michael; geno-fx):**
  - Michael: "The geno flash sun is excellent! It's just still too big ... reduce the size by an appreciable percentage,
    and update the hitbox to change to reflect the growing size, as well as scale the damage (higher on the smaller
    initial burst, lower damage and knockback for a lingering bigger-sun hit.) ... The point I feel most strongly about
    is that the final size should be significantly smaller than it current is. Maybe radius 28 for the final, and same
    size as PK flash for the initial hit and smaller-sun size?"
  - **Size.** The hitbox starts at PK Flash's full-charge radius (14.3: its script's 2150/256 x 1.7; measured 14.2) and
    grows over the same 40 frames to 28 (was 8 to 38). The drawn sun follows it (disc 1.01-1.02x the hitbox, flames
    1.18-1.24x, measured every frame): at full size it's ~34 across its radius, not ~46 (26% smaller, 45% less area).
    The fireball arrives at the burst's size, and the red flash is sized to the smaller sun.
  - **The hits.** One hitbox all through, weakening in place, so each opponent is hit once (§8 rule 3):
    - the **burst**, the sun's first 8 frames (radius 14.3 to 16.7), drawn white-hot: 20%, 45°, KBG 100, BKB 55;
    - the **late sun**, from frame 8 to its end: 12%, 45°, KBG 85, BKB 45.
    The appearance (frame 102 of the hold), the growth (40 frames), the linger (30) and the move's length are
    unchanged: the burst is the sun's first frames, so no timing moved.
  - **Kill percents on Fox**, measured in kill_lab from centre stage (clean KO: dead before he can act; optimal DI is
    the better of full perpendicular DI either way). Before: 70% / 70% at the sun's centre, 70% / 95% at its edge (18%,
    100/55 everywhere). After: the burst 60% / 60%, the late sun 150% / 190%.
  - **Anchors** (`director/finisher_lab.py`, the same way, as each connects): a full PK Flash (36%, 70°, 70/20, hits
    144 frames in) 65% / 65%; Falcon Punch (25%, 361, 102/30, frame 52) 50% / 70%; Warlock Punch (30%, 361, 100/30,
    frame 70) 35% / 50%; a full Charge Shot (25%, 361, 72/50) 70% / 100%. The burst kills with PK Flash's reliability,
    a little earlier, and, like it, shrugs off DI, from a move committed 102 frames.
  - **For Michael: 20% or 22% on the burst.** 20% (built): 60% at any DI. 22% (measured too): 50% / 55%, earlier
    than a DI'd Falcon Punch. The kill area is 81% smaller than the old sun's, which argues for more, but 22% makes it
    the cast's second-strongest finisher after Warlock Punch. One number in `rig/articles.py` (`FLASH_BURST`).
  - The kill lab's Flash test waited 90 frames for contact, not 102, so its DI began before the sun appeared. It's now
    measured, as is the new late-hit test (Fox 24 from the sun's centre); `KILL_SLOT` keeps a slow death from spilling
    into the next test. `dolphin.py --logonly` runs a lab with no dumps, unthrottled (a 60-test sweep in ~3 minutes).

- **2026-09-29, Geno Flash: his hurtboxes follow the cannon (geno-cannon; Michael: "Makes sense on the cannon hurtbox
  change, but careful not to make it too small").** His hidden body curls into the cannon while it shows (23-72): the
  spine along the barrel, the head at the muzzle, the legs and arms down the breech and the wheels, fitted to the
  cannon's side silhouette. At full size his hurtboxes cover 90% of the cannon (was 50%) with 11% of their area outside
  it (was 54%), area 0.96 of standing (was 1.03) and top 0.61 (was 0.92). The guardrail, from the cast's transformed
  states (Samus's Morph Ball, Kirby's Stone, Jigglypuff's Rest and Rollout, Yoshi's egg roll, Bowser's Whirling Fortress;
  `research/flash_hurtboxes.md`): area at least the cast's median 0.90, top at least the cast's lowest 0.42; met (the
  swaps dip to 0.89 for two frames). Frame data, hits and KOs unchanged; the KO's flight animation is DamageFlyN where it
  was DamageFlyHi (a mid capsule struck, not the head). The research otherwise doesn't move. §12 has the numbers.

- **2026-09-29, Geno Flash's cannon approved (Michael):** "Cannon size looks good. Timing and sounds are good. Wheels are
  good. Mallow cannon is good." So: the size (`rig.CANNON_K` 1.25, about Fox's height), the swap on 23 and 76 under the
  two glows, the wheeled carriage (SPR0030's gold half-discs read as wheels) and the barrel following the capelet (Mallow's
  sky blue) all stay. His hurtbox call: "Makes sense on the cannon hurtbox change, but careful not to make it too small"
  (the next entry).

- **2026-09-29, the forward throw's ignition is the rocket's own launch (Michael: "We should remove the explosion
  effect from fthrow, btw. I think that was a judgment question earlier I forgot to specify a choice on."):**
  - The cannon-style explosion is gone: the flash (1012), smoke (1043) and sparks (1062) at the ignition and in the
    exhaust. Its only ignition is now what `GENO_FTHROW_LAUNCH=1` built for his review, and the switch is gone: a small
    white four-point star at the wrist on 23 (`ROCKET_LAUNCH`).
  - The exhaust is Double Punch's unbroken trail: `moves.exhaust_trail` fed the fist's tail (its exhaust ring, 0.3
    behind HandN times the fist's growth, from the throw's own animation: `poses_throws.rocket_tails`), last frame to
    this, out (23-27) and back (33-37): 12 puffs. Along the tail's path (6.9 units out, 6.7 back) it is all drawn, with
    no gap; one puff a frame (`moves.exhaust`, now removed) left gaps of up to 0.09 at this throw's speed (it flies at
    most 2.6 a frame, Double Punch 4-8).
  - Unchanged: the sounds, timing, hit and launch (the script's other 16 commands are identical, and in `throws_lab`
    Fox's release, knockback, angle and landing match before and after, with and without DI).

- **2026-09-29, the gun sounds land on their shots (geno-fxnormals; Michael: "the sound is coming out delayed" on the
  ledge attack and maybe others):**
  - **Measured** (`sound/soundsync.py` on a `gunfx_lab` `GUNFX_SET=sound` run): for every gun move, the cue frame in the
    script, the first active frame (each burst is first seen on it), and when the sound's key transient is heard.
    The key transient is the Hand Gun's first shot, the Star Gun's first burst, the Hand Cannon's boom, or the pulse.
    - **Calibration:** each segment's slate plays the director's pulse (550000), heard with the slate's first image.
      Against the opening click and the opening's first image, that sits +1.07 frames (sd 0.24, 15 slates), a uniform
      dump latency, not a desync. Script sounds cued on their burst's frame land on it (the jabs' and down tilt's pulses
      +0.0 / +0.1).
  - **Before.** Every cue was already on its shot's first active frame, not the animation's start. The Hand Gun, Star
    Gun and pulses were heard within +0.3 frames of the shot. The Hand Cannon's boom was +11.9 (back air, down smash)
    and +12.2 (the slow ledge attack). SMRPG's Hand Cannon is one sound triggered three times, 6 frames apart (two
    arm-cocks, then the boom that rings), so played on the shot, its boom came 12 frames after it.
  - **Now.** The Hand Cannon is cut in two, the second cock (550059) and the boom with its ring (550060). The cock is
    cued 6 frames before the shot: back air 4, the slow ledge attack 35, and the down smash 2 (as the arms fold, before
    its charge). The boom is cued on the shot, so it lands at -0.1 / -0.1 / +0.2 frames. Every gun move's key transient
    is now within 0.3 frames of its first active frame (the third jab +0.9 against its first active frame, -0.1 against
    its burst's first image). No animation changed. The back throw keeps the full 550002; down air is left as it is.
  - **The bank:** 59 -> 61 sounds (the first 59 byte-identical; data_len 385216 of the 393216 booked). The decomp gate
    goes to 550060.

- **2026-09-29, the throws' weight and readability (Michael's review, §6f "Prime, then blast"):**
  - Up throw: "The effects on upthrow are excellent, but they're fast. Is it possible to extend the animation a little
    so there's a brief pose establishing the arm cannon position, then followed by the star shots? It's a slight
    mechanical nerf for multiplier to extend throw animations, but that's more than acceptable to make it look better."
    The Star Gun locks as before (ka 15, chunk 17) and now holds its aim 18-24, settling and sighting up the barrel, a
    tense on 24; the stars move from 20, 23, 26 to 25, 28, 31. 44 to 49 frames, released on 11 as before, so he is free
    5 frames later against every opponent.
  - The stars: "vary the horizontal angle of them slightly, where the first is straight up, and the rest spread out a
    bit to left/right alternating and increasing the width slightly, akin to a spray pattern". Star k leaves k x 6° off
    the barrel, odd toward his front, even toward his back: 86°, 80°, 98° (`ftgeno_throw.c`). With no DI all three
    still hit, at 0-60% on Fox and at 0% on Falco and Falcon. With full DI none does (one did at 0% before): the held
    aim gives DI 5 more frames, and the spray would need 30-50° to reach.
  - Forward throw: "raise the target up a bit more during the initial frames ... 'victim rises slightly, holding-hand
    rises slightly to match' piece before the rocket shot". Measured first: the fist's line passed over them (in game
    their top 1.0 below it at the launch). The lift (15-20) raises the pivot 2.6 against his fist and lifts the hanging
    body with it, his hand rising 0.7; at the launch their top sits 1.8 above the line and their centre 2.5 below it.
    Then the prime (21-22): the fist draws back along the line as the left hand clamps on, a soft rattle. The launch
    keeps its up-right line (the fist flies 37° up, was 32°; the knockback's 35° is unchanged). 50 to 55 frames,
    release 22 to 27.
  - Back throw ("similar principle for forward and backthrow ... prime the hit, then deliver the blast"): after the brace
    he rocks back, drawing the cannon off their chest (30, a rattle), rams it home (31, a clack), a beat, BOOM on 33.
    56 to 59 frames, release 30 to 33.
  - What it costs: the forward and back throws' frames come before the release, so their follow-ups are unchanged (Fox
    flies the same and Geno is free as much later as the release; the forward throw's higher release lands him 1-2
    units further). The up throw's advantage drops 5 frames; the no-DI dash-regrab opening (§6f Regrabs) closes from 4 of
    24 tries to 1. Every launch's knockback and angle is unchanged on Fox, Falco and Falcon (`throws_lab`), and the
    forward throw's ledge kills too (a clean KO from 180% with no DI, 160% with DI down), though Fox now leaves it 3.9
    higher.

- **2026-09-29, Geno Flash's sun, from Michael's review (geno-fx):**
  - Michael: "The effect is probably a little too big, and seems much bigger than the hitbox. Also, the effect ending in
    a pure circle looks a bit off -- see how it's updated in the remake to have a sun's corona? ... the rotating triangle
    effect in the SNES version was more of a 16-bit stylization of a sun's corona effect, and it'd be better to try to
    keep the visuals of the small/growing sun the same as the fully-expanded one, so we should probably replace the star
    effect ... note the mouth being a surprised o-shape rather than a smile." His reference is the 2023 remake's sun
    (a screenshot, local; studied, nothing taken from it).
  - **One sun for the whole move.** The fireball in flight is the sun, small, and grows into it. The sun is an orange
    disc (light yellow at its heart to deep orange at the rim, a thin bright rim), a corona of yellow flame tongues
    tipped orange in two layers that turn opposite ways and flicker, so the flames churn, and a small surprised face (two
    small dark oval eyes, a round "o" mouth). The star with a face is gone.
  - **Sized to the hitbox, measured every frame** (`director/flash_scale_lab.py`, `fx/sunmeasure.py`; the hitbox from
    the collision display, the drawn edge sector by sector round its centre). Before: the drawn edge sat at 1.07x the
    hitbox's radius on every frame of the growth and linger, the halo's faintest trace at 1.39x. After: the disc's edge
    at 1.01x (its body at 0.98x, the bright rim fading out on the hitbox's edge), the corona's median edge at 1.21x
    (1.16-1.25 as it churns), its tips (the 90th percentile) at 1.19-1.29x, the faintest trace at 1.24x (1.18-1.27): the
    whole sun drawn inside 1.3x its hitbox, the disc on its edge.
  - The cast draw their big shots much further past their hitboxes: Ness's PK Flash burst a median 1.4-2.7x its 14.2
    radius, Mewtwo's full Shadow Ball 1.7x, Samus's full Charge Shot 3.1x in its glow and 1.29x in its bright core. The
    corona is kept to about that core margin, since Michael asked for smaller.
  - **What makes it read big is the hitbox.** The old drawing was already within 7% of it. The hitbox grows to a 38
    radius, 2.7x PK Flash's, filling most of the screen's height at match distance. If Michael wants the sun smaller on
    screen, the lever is the hitbox (`FLASH_EXT` r1 38 in `rig/articles.py`), a balance change: it kills Fox at ~70-80%
    at its core.
  - **The red flash** as it ends now flashes the sun's own silhouette red (its disc and the flames' outline) over it as
    it goes, swelling a little as it fades: its edge at 1.13-1.18x the full hitbox, 1.29x at its faintest. It was a
    four-point flash inside an oval ring (to 1.30x, 1.41x at its faintest), which brought back the star Michael had the
    sun lose; a plain round red bloom (tried) ended the move on the pure circle he found off. This is a flag for
    Michael: the old flash is a revert of `efge.py` `flash_red`.
  - Hitbox, timing and damage are unchanged (the same hits in flash_fx_lab before and after; the hitbox's radius and
    centre match frame by frame in flash_scale_lab).

- **2026-09-29, the gun normals' sounds end with their moves (geno-fxnormals; Michael: "some of the gun normal sounds
  ... linger longer"; no animation extended):**
  - **Audit** (`sound/soundaudit.py` on `gunfx_lab` `GUNFX_SET=sound`, the game's own audio). The sound was heard past
    the move's end by: forward tilts +12 frames, forward air +11, up air +16, up smash +12, get-ups +10 / +11, back air
    +4, the quick ledge attack +4, the slow one +1. Down smash ended 7 inside, and the jabs' and down tilt's pulse (4
    frames) well inside. "Heard" means within 15 dB of the sound's peak; Melee's reverb then rings about 18 dB lower for
    another ~18 frames.
  - **The cause.** The Hand Gun (550001) is SMRPG's rattle of ten 62 ms shots at full level for 36 frames, the Star Gun
    (550004) a 48-frame cascade, and the Hand Cannon (550002) rings for 25 frames after its boom. Forward air and the
    first ledge attack play the same Hand Gun rattle.
  - **The fix.** Three shorter sounds with their own ids; the originals stay (the back throw plays 550002):
    - 550056, the Hand Gun's first four shots (14.5 frames), for the forward tilts, forward air, the quick ledge attack
      and the get-ups;
    - 550057, the Hand Cannon with its ring faded out by 28 frames (the cock, cock and boom whole), for back air, down
      smash and the slow ledge attack;
    - 550058, the Star Gun's cascade faded out by 27 frames, for up smash and up air.
    Each is sized to the tightest move of its form, so in game all end inside their moves: forward tilts -9 / -10,
    forward air -13, back air -4, up air -2, up smash -6, down smash -14, ledge quick -17, ledge slow -5, get-ups
    -12 / -11.
  - Down air is left as it is: it's being redesigned as a rocket fist (Michael).
  - **The pummel's puff is dropped** (Michael: "dropping pummel puff is fine").
  - **The bank:** 56 -> 59 sounds. The first 56 are byte-identical; data_len is 378432 of the 393216 booked. The decomp's
    gate goes to 550058 (`lbaudio_ax.c`). Build and install: `sound/gunfit.py`, then `sound/cheer/bank.py`, which now
    takes gunfit.json by default so a chant rebuild keeps them. The steps are in `~/games/melee/work/sfxbank/NOTES.md`.

- **2026-09-29, Geno Flash's full-body cannon (geno-cannon):** he now becomes SMRPG's blue-and-gold cannon on its wheeled
  carriage, in place of the twin Hand Cannon stub (§12; ART.md "Geno Flash's cannon").
  - The model: a stout barrel in his capelet's blue over wooden staves, bound in brass hoops, the capelet's points where
    the blue meets the ribbed brass breech, a big wooden back, a studded chase and a flared brass muzzle; two wooden wheels
    with brass tyres and iron hubs; wooden cheeks, bed and trail. 1,344 triangles high, 168 low, two textures (24 KiB).
  - The swap: the body group's option 1 (Samus's Morph Ball precedent), on frame 23 at the glow's last pulse, back on 76
    under a second glow (frame 60). Any action change is Geno again, and a metal Geno becomes a metal cannon.
  - The motion, on three joints of its own (the hurtbox bones keep the Flash's motion): it drops out of the glow small and
    nose down, lands on its wheels and rolls into place, raises the barrel onto the sun, dips, fires on 49 with the Hand
    Cannon's muzzle flash, kicks up and rolls back with a hop, rolls forward, then folds up into the glow.
  - The fireball leaves the barrel's tip (`ftGe_FlashMuzzle`, 6.76 ahead and 6.93 up; the stub's was 5.12 and 9.52).
  - Unchanged, measured in `flash_cannon_lab` before and after: his hurtboxes on every logged frame of the Flash, every hit
    and item hit, every action Fox and Geno go through; the research after `remeasure.sh`.

- **2026-09-29, the throws' own visuals (geno-fx):**
  - **Up throw:** its three Star Gun shots are SMRPG's Star Gun stars: spinning gold stars with a white highlight, each
    trailing sparkles. Their muzzle is the Star Gun's own flash (`N_STAR_FLASH`, shared with up smash and up air). They
    were the Beam's model drawn thin.
  - **Forward throw:** built for Michael's review: the Rocket Fist's own launch (a small white four-point star at the
    wrist, `ROCKET_LAUNCH`) with the Double Punch's exhaust out and back, in place of the cannon-style flash, smoke and
    sparks. Adopted as the only ignition on 2026-09-29 (above).
  - The throws' launches and hits are unchanged in throws_fx_lab before and after.


- **2026-09-29, the ledge and get-up blasts show their guns, and the rocket fists' exhaust is unbroken (geno-fxnormals;
  the coordinator's consistency calls, Michael can reverse them):**
  - **Weapon forms.** The quick ledge attack shows the Hand Gun from 21 (as he cocks it) to 33, over its hits (24-28).
    The slow one shows the Hand Cannon on both arms from 38 (the draw-back) to 50, after the recoil, over its hits
    (41-44). Each get-up shot shows the Hand Gun on its firing hand from 3 frames before the shot to 3 after: face up
    the right 16-22 and the left 21-27, face down the left 16-22 and the right 22-28. The bursts' flashes moved to the
    barrels' tips. Hit mid-form (`gunfx_lab` `ledge_quick_hit`: Fox's forward tilt lands on the quick ledge attack's
    frame 23 with the gun out), he leaves the action and the hand is back, as the engine resets the forms on any action
    change. Their reach is unchanged: ledge quick 0.93 (cover 0.59), ledge slow 0.86 (0.62), get-ups 0.88-0.95
    (0.50-0.61).
  - **Exhaust.** One puff a frame left gaps as wide as a frame's flight (Double Punch's fists fly 4-8 units a frame).
    Measured along the fists' line, only 0.28-0.53 of it was drawn, with gaps of 5.5 units. `moves.exhaust_trail` now lays
    the puffs along each frame's flight, 2.2 apart at most, from the fists' tails (`moves.fist_tails`, from
    `poses_ground.fs_hits`). The line is 1.00 drawn from frame 17 on, with no gap, for 22 puffs a Double Punch (11 a fist:
    1, 2, 4, 3, 1 over frames 14-18) against 14 before. N_EXHAUST's puff grew from 0.7 to 1.2 half-width so neighbours
    overlap. Any flying fist can use `exhaust_trail` with its own path (the forward throw's rocket).
  - Hitboxes and frame data unchanged.

- **2026-09-29, the gun normals show their hits, part 3: the Hand Cannon, the ledge and get-up blasts, the rocket fists'
  exhaust (geno-fxnormals):** measured as parts 1 and 2 (drawn reach past the body / the hitboxes' reach past it; cover
  of the disjoint hitbox area).
  - **Hand Cannon.** Back air -0.02 -> 0.92 (cover 0.00 -> 0.58; 0.98 facing left), down air 0.08 -> 0.96 (0.03 ->
    0.59), down smash 0.00 -> 0.82 / 0.84 in front and behind (0.06 -> 0.47 / 0.52): a heavy flash, a shock ring and
    smoke at the muzzle, and a hot glow and fire puffs that blacken to smoke on each sphere. The down air's tail burns a
    frame after its muzzle, with its hitbox.
  - **The slow ledge attack** fires the Hand Cannon's burst from both hands: 0.13 -> 0.95 (0.04 -> 0.57).
  - **The quick ledge attack** rakes the Hand Gun's burst up with its three hitbox frames: 0.06 -> 0.90 (0.04 -> 0.55).
  - **The get-ups** fire the Hand Gun's low blast, then its bloom a frame later, each on its own frame's spheres:
    0.84-0.94 on both sides (0.00-0.02 -> 0.50-0.55).
  - **Double Punch's flying fists** leave a thin trail of grey exhaust puffs, one a frame (`N_EXHAUST`; the forward
    throw's rocket reuses it). The fists are drawn, so the reach numbers don't apply.
  - Particles per move top out at the up smash's ~48 (the get-ups ~44, the down smash ~22). EfGeData.dat is 58 KB with
    the specials'. Hitboxes and frame data unchanged.

- **2026-09-29, Geno Flash's look (geno-fx):** it now plays SMRPG's sequence, in place of Ness's PK Flash.
  - He glows yellow as he becomes the cannon: a soft glow over his body and sparkles rising round it.
  - The cannon fires a round fireball on frame 49, which flies to the sun's spot.
  - Growing with the hitbox from frame 54, there's SMRPG's star with a face: red at its points, orange to yellow at
    its heart, two eyes and a smile, spinning.
  - Over the last part of the growth it rounds into the sun (the same face): the sun grows from a hot core until it
    covers the star's points. It lingers as the sun.
  - As it ends, SMRPG's red flash: a red bloom and a ring.
  - Hitbox, timing and damage are unchanged: the same hits in flash_fx_lab before and after.
  - The full-body cannon is still the Hand Cannon stub, with a clean hook for its model (§12, "Geno Flash's full-body
    cannon").

- **2026-09-29, the gun normals show their hits, part 2: the Star Gun, the down tilt and the pummel
  (geno-fxnormals):** measured as part 1 (drawn reach past the body / the hitboxes' reach past it; cover of the disjoint
  hitbox area).
  - Up smash 0.08 -> 0.95 (cover 0.09 -> 0.47), up air 0.20 -> 0.85 (0.20 -> 0.60): stars sprayed over each hitbox
    sphere on its frame, both wrists' flares and the column for the up smash (a second spray up the column on frame 11),
    each frame's sphere for the up air, so the stars trace its arc front to back.
  - Down tilt 0.03 -> 0.87 (0.03 -> 0.40): the Finger Shot's own muzzle puff at the tubes and the taps' burst on each
    sphere (Michael, via the coordinator: every gun move with an undrawn disjoint is in scope).
  - Pummel: a tap's pop on the held opponent. It hits only them, so it has no disjoint to show, and the game's hit spark
    mostly covers the pop.
  - Hitboxes and frame data unchanged.

- **2026-09-29, the Geno Blast's look (geno-fx):** it now looks like SMRPG's, in place of Pikachu's thunder bolt.
  - The cast: blue four-point sparkles rise at his hand.
  - The tell (the mark phase, 32 frames): a glowing oval on the floor, with a thin beam of light rising from it that
    widens as the strike nears, and sparkles rising. SMRPG has no tell; this is ours.
  - The strike: a flat column of light in one of SMRPG's colours in turn (white, purple, teal, yellow-green, yellow,
    orange, red, blue), so the widened three are three colours. It drops from high above and reaches down from the item
    (floor_y + 40) to the floor, as wide as its hitbox (12).
  - Each column lands in a white cloud with sparkles.
  - Mark and strike timing, the lift and the hitboxes are unchanged: the same hits in blast_fx_lab before and after.

- **2026-09-29, the Geno Whirl's look (geno-fx):** it now looks like SMRPG's, in place of Samus's charge-shot ball.
  - A white-yellow disc of light with four swept blades, tilted into the SNES's oval and spinning: fast in flight,
    slower in the hover. A soft aura pads its 3.6 hitbox.
  - A trail of fading yellow ovals, dropped every 3 frames of the throw and the recall.
  - The outbound hit bursts in a yellow-white ball with orange sparks (SPR0517), and each shield-grind hit throws sparks.
  - The timed crit adds a big blue-white flash and an expanding ring, standing in for SMRPG's blue screen flash.
  - The disc shrinks away over the spin-down after a hit and over the last 8 frames of its hover.
  - The hitbox, phases and timing are unchanged: the same hits, crit and grind hits in whirl_fx_lab before and after.

- **2026-09-29, the gun normals show their hits, part 1: the Hand Gun (geno-fxnormals; Michael: the gun moves must read
  in play, in SMRPG's spirit, adapted to Melee):** their reach is muzzle bursts no hurtbox follows, and nothing was drawn
  there.
  - **Measured first** (`director/gunfx_lab.py`, `fx/gunfxmeasure.py`, the match camera on black, 14.4 px/unit). The
    cast's drawn disjoints reach, past the body, this share of the hitboxes' reach past it: Ness's forward and back air
    0.94, Marth's forward smash 0.90, Falco's laser 1.01, Pikachu's forward smash 0.53 (0.92 on its longest frame) and
    Mewtwo's forward smash 1.38 (it overdraws). They draw over 0.26-0.58 of the disjoint hitbox area. Samus's forward
    smash is the exception and draws nothing past her cannon (-0.19). Geno before: 0.0-0.1, cover 0.0-0.10.
  - **Now** every gun blast spawns one burst on each hitbox sphere, the same TopN offset on the same frame, sized to its
    radius, plus a flash at the barrel. It shows on the first active frame. Jab 1-3 0.84 / 0.97 (cover 0.46-0.51), the
    three forward tilts 0.90-0.96 (0.45-0.48), forward air 0.92 (0.42), facing left the same (0.87-0.91). The look is
    in ART.md.
  - Hitboxes and frame data unchanged; `GENO_NORMALS_FX=0` builds without the bursts (the A/B).

- **2026-09-29, ItemBlind and the light throws' release frames:**
  - ItemBlind: nothing in the game plays it (none of the 341 common motion states names it, and no fighter's idle lists
    include it, all 27 read with the new `datkit chances`), so there is no real trigger. The director's new `anim` cue
    plays it through the engine's own idle-variant player (`ftCo_8008A6D8`, Wait's), in items_lab's 'blind' try beside
    Fox's. The cast's is a blinded grope (Fox's, Mario's: crouched, arms out feeling ahead, the head turning). His old
    dazzled loop rubbed his eyes behind his big head and read as a slump from the game's camera. Now the left arm gropes
    ahead, open-handed and sweeping, while the right forearm shades his eyes; halfway through both arms grope. Knees
    bobbing, head ducked and turning, 240 frames looped from and back to Wait1's first frame.
  - Light throws: each throw's item leaves the hand on its script's release frame, measured in game (items_lab
    `--releases`: the director's new LETGO line, with the action's animation frame): 7 for forward, back, down, the drop
    and the air forward, back and down; up 9, dash 4, air up 6. The smash throws match, except the smash down throw (5).
    The poses released a frame early (6, 6, 8, 6, 6, 3, 6, 6, 5, 6), so each is retimed onto its frame: the windup
    stretched to it and the follow-through fitted into the rest. The smash down throw gets its own animation, released
    on 5 (the template shares the down throw's). The air throws in the lab always come out as the smash versions (Z and
    a direction), which share the plain versions' animations and release frames.

- **2026-09-29, the grabs at parity with Mario's cost (Michael: "Bring the grab around parity with Mario's
  intangibility, I understand what it's asking now and the cast standard"):** the grab's and dash grab's fists grew 2.7x
  and their hurtboxes cost 1.37 and 1.36 of forward disjoint, about twice what Mario's growth costs him (grab 0.67, dash
  grab 0.80; `research/growth_cost.md`). They now peak at the sizes that cost the same, found by building each: the
  grab 1.83x (disjoint 2.85 to 2.18, cost 0.67; 13th to 21st percentile) and the dash grab 2.0x (2.87 to 2.07, cost
  0.80; 48th to 52nd). Tangible, as Mario's are. The fist then fills 0.32 and 0.35 of the grab box (Mario's 0.47; it
  was 0.175 unscaled). Same timing: the peak on the grab frame, back to 1 three frames later.

- **2026-09-29, the Finger Shot's look (geno-fx; Michael: "what happened to the finger bullets?"):** Falco's red laser
  stand-in read as nothing at match distance: its bright core was 0.5 units thick against a 2.3 hitbox.
  - It is now a volley of four golden slugs (the design's four bullets), each with a white-hot core, a halo and a short
    orange tracer. Each rides one of the laser's four hitbox spheres, so they string out with them along the flight. The
    core is 2.4 thick, as thick as the hitbox, and the halo reaches 6.2.
  - A grey mist puff at the fingertips condenses into a small yellow star with each shot (SMRPG's SPR0527).
  - The down throw's shots and Kirby's copy look the same.
  - The hitboxes, speed and damage are unchanged: the same hits in finger_lab before and after.

- **2026-09-29, jabs keep full growth, no intangibility (Michael):** "No invuln on jab, keep the better visual growth".
  Jab 1-3's grown hands (2.0x / 1.8x / 2.2x) now carry their grown hurtboxes, as the cast's grown limbs do. Disjoint:
  jab 1 9.85 -> 8.78 (79th percentile, unchanged rank), jab 2 8.15 -> 7.17, jab 3 9.63 -> 8.28 (`research/growth_cost.md`).
  The up tilt's grown hands stay intangible while grown (`moves.GROW_INTANG`).

- **2026-09-29, Michael's calls on the rocket fists, and the rest of the body-contact normals grow:**
  - Sizes: "I'll playtest the sizing later". Double Punch 2.8x, the grabs 2.7x and the forward throw 2.8x stay as built.
  - "Double Punch behavior only shrinking when returning to base model is good": the fists hold their size in flight.
  - The grab's hurtbox grows with its fist (forward disjoint 2.85 to 1.48; the dash grab's 2.87 to 1.51) and stays;
    he judges it in play. Measured since against the cast's own growth (`research/growth_cost.md`), it costs more than
    Mario's grab does (0.67; Luigi's 0.76): a 1.85x grab would cost what Mario's does, and fists intangible while grown
    would gain 0.69 instead (to 3.54; not built).
  - "Go ahead and make the change to the rest of the normals": each part sized so it fills its nearest hitbox as the
    cast's analog does (`research/fist_read.md`), peaking on the first active frame and easing back:
    - jab 1 / 2: the pointing hand 2.0 / 1.8 (cover 0.64 / 0.57: Mario's jab 1 / 2);
    - jab 3: both palms 2.2 (0.68; Mario's jab 3 kick 0.70);
    - up tilt: both hands 2.1 on the arc (0.31 of its bursts, Mario's up tilt on its first active frame);
    - pummel: the finger hand 1.25 (0.20; Mario's 0.19-0.21);
    - dash attack: the lead (gun) arm, from the shoulder, 1.3 (0.40; the cast's dash attacks 0.37-0.43);
    - neutral air: the back kick's shin and boot 1.3 on frame 12, eased back by 18 (0.63; the cast's kicks 0.50-0.72).
    No hitbox moves. The grown hands' hurtboxes would have cost the jabs 0.98-1.35 of forward disjoint and the up tilt
    1.5 (Mario's jabs lose 0.21-0.29 to theirs, because his hitboxes grow with the fist and Geno's don't), so the jabs'
    and up tilt's grown hands are intangible while grown, as Double Punch's fists are: they gain instead, jab 1 +0.40
    (9.85 to 10.25), jab 2 +0.47, jab 3 +0.45, up tilt forward +0.33. The nair's kick pops on frame 12 (a ramp from 9
    grew the shin on frame 11, its best back-disjoint frame, for a 0.29 loss); its back disjoint is unchanged, and the
    grown shin reaches up to 0.86 further back on 12-17. Dash attack and pummel change nothing. The gun moves, the ledge
    and get-up attacks and the specials are left to the effects work.

- **2026-09-29, the Geno Beam's look (Michael; geno-fx, projects/geno/fx/EFFECTS.md):**
  - The charge draws energy into the barrel, as the SNES does. Every 10 frames of the charge, a wave of small stars
    appears in a tight wedge ahead of and above the tip. The wave shimmers white, lavender and blue in step, converges on
    the tip, and a lavender flare pops there. The waves land as each star lights (charge frames 20, 40 and 60).
  - Each star adds to the waves: 3, 5, then 6 stars, each wave bigger than the last. Kirby's copy draws into its hand.
    The tap, the release and the fire are unchanged.
  - All blue at every level, as in SMRPG (Michael): no colour per charge level. Thickness is the level cue instead.
  - The Beam is drawn bigger (Michael: "a bit puny"). Against its hitbox it is now ~1.6-2.1x as thick in its glow,
    ~0.8-1.0x in its core, and ~1.45x as long, stepped 0.45 / 0.70 / 1 by star. That is inside the cast's own margins:
    Samus's full Charge Shot glows 3.1x its hitbox (measured in scale_lab). The hitbox is unchanged.

- **2026-09-29, the costume set (Michael):** "the 5 from SMRPG are excellent" (Geno, Mario, Bowser, Mallow, Peach, as
  built), "and let's include the black and red as a 'dark' outfit, which tends to be a fan favorite, for number 6". Dark
  (Bk) is built: black cap, capelet, collar and boots; red curls, ribbon, lining, clasp, collar piping and soles (§12
  "Costumes"), with its own portrait and stock icon. Six costumes, Melee's maximum; the teams are unchanged.

- **2026-09-29, the rocket fists grow on their hit frames (Michael: keep holding the size in flight, shrinking only on the way home; sizes to be playtested; the rest of the normals next):** Michael asked whether the
  rocket fists should grow as the cast's limbs do (Mario's jab fist), since they read well up close but get lost in play.
  The cast grow a body part on 376 of 666 moves, the cartoon cast on 70-100% (`research/limb_scale.md`). Sized by
  measurement (`research/fist_read.md`): on its first active frame Mario's fist fills 0.42 of his forward smash's hitbox
  radius (Doc 0.40), 0.47 of his grab's and 0.53-0.64 of the jabs'; Geno's filled 0.15 of Double Punch's (4.4) and 0.175
  of the grab's (4.0). So Double Punch's fists peak at 2.8x on frame 15 (cover 0.42), hold while they fly and ease home
  by the dock (27); the grab and dash grab peak at 2.7x on the grab frame (cover 0.47) and are back to 1 three frames
  later; the forward throw's fist grows 2.8x at the ignition (18) and eases home by the dock (33). At the match camera the
  fist goes from ~19 px across to ~53 (1056-line dump; Mario's jab fist 72). The hitboxes don't move (a grown fist pulls
  HandN in, so its box stays put; residue 0.02 at most). The hand's hurtbox grows with the fist, longer and fatter (the
  engine scales a hurtbox's radius by its bone's scale; datkit movedata now measures it so): the grab's forward disjoint
  drops from 2.85 to 1.48 on its active frames (33rd to 13th percentile; the dash grab's 2.87 to 1.51, 75th to 48th).
  Double Punch's fists are intangible while grown, so nothing else moves. (The jab grows since: the entry above.) Review: `~/games/melee/sandbox/geno-limbscale/boards/limbscale/review_limbscale.html`.

- **2026-09-29, Kirby's Geno hat:** Geno's own cap, refitted to Kirby's head (§12: how it's built and rebuilt, and its
  numbers against the vanilla caps). The copy's hat interface is unchanged; `PlKbCpGe.dat` drops in. Checked in game on
  all six Kirby costumes, beside Luigi's, Mario's and Link's caps, with Geno in his default and non-default costumes
  (Mallow's among them), through idle, squat, jumps, the copy's attacks and the taunt that takes it off.

- **2026-09-29, down air becomes a rocket fist (Michael):** "I misspoke on the earlier 'disjoint hand cannon shot.' I had
  intended 'hand cannon' to mean 'rocket fist' ... Let's try the rocket fist design, similar to ftilt and fsmash -- it's
  still intended to be long and disjointed, similar to those, with the meteor on the close / startup hit."
  - The fist fires straight down off the forearm, out to 13.0 below him and home, as Double Punch's fists do. It is
    intangible while out, and the hitboxes ride it.
  - The meteor (9-10) is on the fist while it's near him; the extended fist is the weak tail (11-15).
  - The column's frame data is kept: startup 9, active 9-15, IASA 38, landing lag 24, autocancel 1 and 32+.
  - The looks are Double Punch's: the fist grows on its hit frames (2.8), its exhaust trails it, and it plays Double Punch's sound.
  - Tried as a feasibility test, with the column kept (GENO_DAIR_CANNON=1 builds it) as the fallback. Michael also asked
    how the fist handles his fall, fast fall and early landings.

- **2026-09-29, the Whirl on a shield (Michael):** "the spindown is moving too far after it hits shield, ending up in a
  weird position past the character."
  - Measured on Mario, Fox and Bowser, with hard and lightest-analog shields, at full and depleted health, from both sides.
    On a hard shield the grind pressed on at 0.4 a frame and ended 6.6-8.9 units inside the shield, 1.4-3.7 past Mario's
    and Fox's centres. Its last hit then pushed them back towards Geno.
  - Now it presses only up to the shield's front, is knocked back by each grind hit, and after the grind settles 5 units
    in front of the shield. It ends 11-14 units short of the shielder's centre, and every hit pushes away.
  - Unchanged: the grind's hits (count, frames, damage) in every case. A light shield's pushback still outruns the disc.
    A depleted hard shield on Mario or Bowser is still shield-poked by the outbound hit.

- **2026-09-29, down B's four open calls (Michael):** all four approved as built.
  - Airborne at the third star (frame 49), the widened Blast releases itself. There is no aerial Flash.
  - A release below ledge height places no mark (the refusal at the start also applies at the release).
  - IASA is 28 frames after the release's mark, so a late release commits longer.
  - The second star lights with its own sound: the Beam's second-star sound (550012), on the charge's frame 25.

- **2026-09-29, down B's tell and the landing pop (review):**
  - The tell now stands on the floor. The stand-in model (Pikachu's thunder: one quad hanging 40 below its root) used to
    render under the stage. The item now rides 40 higher (the Blast's `lift`), and the strike's hitboxes move 40 down
    on it, so they sit on the bolt's lower end. Where they hit is unchanged.
  - The one-frame "pop" landing mid-charge was not the landing frame: that frame renders the grounded charge at its own
    frame, standing. The strip had shown the frame before it: a dropped dump image, now handled by per-segment sync
    slates. The frame before landing sinks up to ~3 below the floor. That is the engine's knee-height air ECB, as in
    every air-to-ground switch (Fox's plain landing sinks 4.2).
  - Open for Michael: whether Geno's air poses should fold the shins back so the feet stay above the floor on that frame.

- **2026-09-29, down B landing mid-charge (Michael):** an aerial down B that lands mid-charge keeps its charge; the third star grounded is Flash; no landing lag.

- **2026-09-28, costumes and menu art from the production model:** Michael's call: one costume uses Mallow's colour
  scheme; he's open on the rest (other character references, Geno's knight-like beta art, or red, green and blue for
  teams). Built: five costumes, Geno in his party's colours (Geno, Mario, Bowser, Mallow, Peach; red, blue and green for
  teams), recommended with two rendered alternates (Star, Shadow), the set pending his call (made 2026-09-29, above). The CSS
  portraits, stock icons, CSS icon and VS Records face are in-game renders of the production model in the Geno Beam's
  charge, one portrait and stock icon per costume (§12 "Art"), replacing the blocky rig's placeholders.

- **2026-09-28, down B is either-or (Michael):** holding to the end used to fire a Blast and then a Flash, and the Blast
  comboed into the Flash, which was too strong. Now the release decides:
  - a tap gives the single-column Blast, mark on frame 10, as before;
  - a release after the second star gives the widened three-column Blast, marked at the release;
  - holding to the third star turns the charge into Geno Flash instead, with no Blast.
  Both share the raised-arms casting pose until he commits. The mark's distance is read from the stick at release.

- **2026-09-28, the specials' own effects (geno-fx; projects/geno/fx/EFFECTS.md):** Geno has his own effect file,
  `EfGeData.dat` (effect slot 22, ids 22000-22999), loaded with him; the Beam's timed release bursts SMRPG's rainbow
  stars from it (a flash, a ring of eight rainbow stars, white twinkles) in place of Samus's full-charge flash. The Beam
  has its own model in SMRPG's look (white core, cyan rim, blue glow, round bright end). Michael: the Beam's hitbox may be
  slightly thicker and longer, padded by the glow, for the SNES look: its spheres are now 2.2, 2.9 and 3.8 (were 2.0, 2.6,
  3.4), four along the drawn beam (to ~17.7 at three stars) that spread with it as it leaves the barrel; damage unchanged.

- **2026-09-28, the crowd cheer:** Michael picked candidate #2 ("clearly wins"): Pichu's "ch" and "PEE", Ness's "n", and
  Mario's "o" lowered 3 semitones, spliced only from the crowd's own chants. It's `~/games/melee/work/crowd/shortlist/2_pc_pc_ns_mr.wav`
  as bank 55 sound 550053, installed with `sound/cheer/bank.py 2_pc_pc_ns_mr.wav` then `--install`; the crowd chants it
  in game (0.98 correlation in `cheer_lab`'s audio). Before this his chant field held the wrong "none" value (540001 for
  540000), so the crowd gasped, played 8 empty chants and cheered.

- **2026-09-28, Michael on the aerials and specials:** Star Road's twin Hand Cannon thrusters and the Blast's and Whirl's
  bare hands are right. The Beam's cancel works exactly as Samus's (and Mewtwo's) charge-shot cancel, but the stars are
  lost, not stored (the intended design). The timed release's chime uses SMRPG's own timed-hit sounds from the ROM,
  timed to fit. The shots leaving from the muzzle (4.3 further out) and down air's long downward disjoint (14.5; the cast
  maximum is 8.9) both stay.

- **2026-09-28, the throws (§6f):** all four built with one weapon each and in beats (Michael: the first cut was too fast,
  with no ka-chunk; the back throw is the move, then the blast; he kept the Rocket Fist's cannon-like ignition). The up and
  down throws' stars and shots are real projectiles (the decomp's `ftGe_Throw_Anim`). The throws are weight-independent.
  The up throw pops Fox to 27.6 at 0% (the old one peaked ~17), between Fox's and Falco's up throws. Forward and back
  throws tumble from 0% (base 64 and 62; were 55), so none is regrabbed with best DI. The victims play the cast's victim
  animations retimed to his beats, or composed ones (the back throw), instead of Mario's.

- **2026-09-28, Michael's calls on the animation pass:** heavy items ride on his head, arms bracing (a crate is his height,
  and his arms can't reach over the cap); the taunt is 110 frames (was 180); Wait2 stays as an in-match idle variant (the
  engine plays it ~30% of the time); a relaxed default hand in every pose (`rig.RELAXED_HAND`); the forward smash's fists
  connect at close range at every angle and charge (the blockout's whiff was a bug); rocket fists on both grabs; up tilt
  gets a star effect along its disjointed burst; the victory fanfare becomes our own arrangement of SMRPG's Level Up theme
  (Mario's is the fallback).

**v1.3, parity round 3 (2026-09-28):**
- The defence and reaction states are his own (§6e), each checked against the cast's hurtbox conventions
  (`research/body_moves.md`, from `datkit bodydata`).
- The tech in place and the tech rolls pop up with a hop, as the cast's do.
- The director gains a shield-health cue.
- Victims of his throws still play a standing pose in the wrong layout: a finding, for the attacks.

**v1.3, parity round 2 (2026-09-28):**
- The get-ups bloom upward to the cast's coverage (§6c; Michael), measured by `research/getup_cover.md`.
- The ledge catch is continuous: a Geno hook in the decomp eases the grab into his own path (§6d).
- He hangs from the ledge instead of being drawn on its corner: fighter-build had collapsed CliffWait's still TransN
  into a single key, evaluated once.
- The ledge and floor states around the moves are animated: the catch, the hang, the climbs, the ledge rolls and jumps,
  the knockdown bounce, the stand-ups, the rolls and the techs.
- The director's RESET clears the collision history (a reset from a ledge hang swept back under it), and its POS trace
  logs the hip joint too.

**v1.3, parity (2026-09-28):** the pummel, ledge attacks and get-up attacks are his own scripts and blockout animation, at
the cast's medians (§6c). The lying pose he gets knocked into now rests on the floor. `anims.down()` had offset his body
in its tipped frame, so every down action lay ~4 units up and 5.6 along the floor, with his hurtboxes up there too.

**v1.3 (Michael's first hand playtest, 2026-09-27):** a grounded character that feels planted. Slower ground movement
with felt acceleration (dash 1.35 / run 1.6, dash acceleration 0.08, Fox's traction 0.08; the Whirl slowed with him), a
shorter dash, skid and run turnaround (18 frames each), jumpsquat 5, full hop 29 (Fox's), less air speed (0.85) and
acceleration (0.035). Beam stars at 20/40/60; the Blast widens at 24 and becomes Flash at 48, with 8 more frames of endlag.
Star Road: 20 frames, the ledge catches from travel frame 4 (its travel never looked for ledges before), steep wall hits
slide. The shield covers him (his guard pose is now the fighter data's shield pose, fitted by `rig/shieldfit.py`); the grab
holds its victim at one point (the pull ends two frames after the grab, as Mario's).

**v1.2 (Michael's aggressive direction):** a pressure zoner. Physics toward Sheik and Falco (weight 80, fall 2.3 / 3.0,
gravity 0.13, jumpsquat 3, short hop 11.3, dash 1.8 / run 1.9). The Whirl slows down and grinds shields so he can follow
it in; Finger Shot gets a clean short-hop landing; nair goes to frame 3 with a clean hit and top-of-cast crossup coverage;
Star Road becomes finicky (shorter, a late facing-only ledge snap, no slide on walls). The shield-gap rule drops from 9
frames to 5. Aerial shape targets (§6b). Fair and back air become late, long and tip-strong (Byleth's lance aerials);
down tilt becomes a low Finger Shot; the grab's fists shoot out on the arm bones; the principle that gun blasts may be
disjoint and body moves carry their hurtboxes (§6b).

**v1.1:** Michael's decisions (§11): weight 88, lever order, no meter confirmed.

**v0 to v1:**

- **Tools are cheaper.** Beam stars at 15/30/45 (was 20/40/60) with a decaying store; Whirl, Blast and Finger Shot get
  frame budgets; aerial versions don't stall and have no special landing lag after a short window.
- **Hits cash in.** Knockdowns from the Whirl, down throw, down tilt and the Blast pop; the Blast meteors airborne targets
  and pops grounded ones; the full Beam kills; throws make situations. The tech chase is the new core loop.
- **A close-range floor:** a normal grab, an 8-frame out-of-shield nair, a frame 6-7 up tilt. v0's claim that Nu-13 "had
  almost none" up close was wrong.
- **Structural loop and ledge rules** (§8), replacing v0's single ledge rule.
- **Physics** out of Mewtwo's corner (weight 86, fall 1.9, gravity 0.095, air acceleration 0.05) and a complete spec
  (jumps, landing lags, hurtbox policy).
- **No meter;** Geno Flash is down-B's third star. Timed hits on specials only. Up-B gets a launch hitbox. Geno Boost is out.
- **Projectile discipline:** the jab's burst doesn't travel, Finger Shot is capped at two, and the Whirl's ground roll
  provides the ground lane v0 promised but never had.
- **Corrections:** it was PM 3.5 that toned down 3.02's zoning, not the other way round; Melee's Missile breaks at 4% (6%
  is our number for the Whirl); reflector break is confirmed Melee behaviour (only the threshold is open); more reflectors
  and absorbers are listed; research is cited by document.
