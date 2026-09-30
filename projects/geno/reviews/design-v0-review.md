# GENO design v0: review

Review of `DESIGN.md` v0, 2026-09-27. I read all of these: `DESIGN.md`, `research/platform-fighter-design.md`,
`research/fg-design-principles.md`, `research/geno-source.md` and `research/cast_attributes.csv`.

**Markers**
- **[V]** I checked it this session, in the research files, in the CSV (computed below), or on a page I fetched today (named).
- **[M]** It comes from my own knowledge of Melee or BlazBlue and I did not re-check it this session. The web-search budget was
  used up, so I could only fetch two pages directly: Dustloop's CT Nu-13 page and SmashWiki's Reflection page.
- **[I]** It is my inference or design judgment.

Frame numbers I propose are starting targets for the blockout. They are not claims about existing characters unless marked.
"Research-PF" means `platform-fighter-design.md` and "research-FG" means `fg-design-principles.md`. Both number their
principles P1-P10, so a bare "P7" is ambiguous (see §8).

---

## 0. Summary

**Verdict.** The draft has the right shape: lanes, one of each threat, a real weak range and a committal recovery. As
specified, though, it is **too weak, not degenerate**. The kit has the same structure as Link and Young Link, which have a
straight lane (arrow), a curving path (boomerang) and an arcing drop (bomb), and it is close to Samus's (a charge shot,
missiles and bombs). Those characters rank 11th to 18th [V research-PF §2]. Each of Geno's threats is "slow to set up,
readable and answerable". His hits don't convert. His close range has no floor. His physics sit in the light, floaty corner.
Melee's top tiers will walk through that. My estimate is a mid-tier character with losing matchups against Fox, Falco, Sheik
and Marth [I]. Two pieces also carry real degeneracy risk once they're tuned up: the Whirl's hover zone, which can become a
lock, and Blast cast from under the ledge, which is planking with stage coverage. With the fixes below, top of A tier is
realistic and a Nu-like feel is reachable [I].

**Top five must-fixes**
1. **Give every hit a cash-in.** Stray hits should turn into tech chases, edgeguards or juggles. This is Nu's knockdown and
   setplay translated into Melee.
2. **Cut the commitment, not the count.** Faster startup and no-stall aerial versions; a Beam charge of about 45 frames
   instead of 60, with a store that decays.
3. **A close-range floor:** a normal-length grab, an 8-frame out-of-shield nair that sends away, and a real anti-air.
4. **Fault-tolerant loop and ledge rules.** A ledge grab or helpless fall despawns his Whirl and Blast. The hover hits once
   per target. Shield pressure has a quantified gap rule.
5. **Physics out of the corner, and a complete spec.** Roughly weight 86, fall speed 1.9, gravity 0.095. Specify air
   acceleration, jump heights, landing lags and a hurtbox policy for the hat and cape.

**Open questions**
1. **Star Pieces:** no gameplay resource in v0. Geno Flash becomes the third-star charge of down-B.
2. **Close range:** add one honest *defensive* close-range option, but no offensive close-range game.
3. **Up B:** a small hitbox at *launch*, not at the end, and none during the flight.
4. **Timed hits:** on specials only for v0.
5. **Geno Boost:** leave it out of v0, or keep it as a cosmetic taunt.

---

## 1. Verdict in detail

**Is it a genuine pure zoner?** In intent, yes. §2's pillars are the right frame: one of each threat, placement then
payoff, and a web the opponent reads and cuts. §7 is a good first pass at making the tools feed each other.

**Is it at the intended power level?** No. It is below it, for four reasons that compound.

1. **Melee's historical data on this archetype is bad** [V research-PF §2a, §2]. Slow, breakable or low-hitstun projectiles
   on characters with poor follow-ups don't reach top tier. The research names four things that separate dominant projectiles:
   low commitment, speed, a usable on-hit state, and a body that can capitalize. The draft picks the opposite of three of them.
   Each threat is individually slow to set up, his throws deliberately reset to neutral, and his close range is weak. Only
   Finger Shot has Falco's properties.
2. **Melee movement outruns the setup times** [I, arithmetic from the CSV]. At run speed, Fox covers half of Final
   Destination (about 85.6 units) in about 39 frames and Falcon in about 37 [M for the stage width]. Sixty frames of standing
   Beam charge with no store is more than a full half-stage approach, and Falco's lasers and Sheik's needles interrupt it
   anyway. Wavedash, dash-dance and powershield all compress the space further.
3. **The risk-reward exchange is lopsided** [I]. As drafted, Geno needs five or six hits of chip to do what Fox, Marth or
   Sheik do off one grab. Against an 82-weight, 0.085-gravity body, that one grab also kills early off the top (Fox's
   up-throw into up-air, Marth's and Sheik's up-airs). Zoners win in Melee when a stray hit is worth a lot. Falco's laser into
   a grab or pillar, and Sheik's needles into a grab or edgeguard, are the evidence.
4. **Too many weaknesses stack at once** [I]. The draft is light, floaty, short-grabbed, slow out of shield, weak up close,
   committal offstage, and big-hurtboxed (the hat, collar and clogs). The research's pattern is two or three elite traits
   against one or two real liabilities [V research-PF §2]. The draft has one elite trait, zoning, and it isn't elite yet,
   against five or six liabilities. That describes Mewtwo, who ranks 20th.

**Would it be degenerate?** Not as written, because everything is too slow. The failure modes appear when you speed the kit
up, which you must do:
- the Whirl hover becoming a multi-hit lock;
- Blast and the Whirl covering the stage or ledge while Geno planks with fresh ledge invincibility;
- widened Blasts covering every tech option at once;
- vertical Blast columns poking shrunken shields;
- bair recoil or aerial charges stalling or extending his recovery;
- Star Pieces snowballing off Finger Shot chip.

Section 5 has the rules and the lab proofs for each.

**The power target** [I]. The owner asks for "at least the high end of powerful" and "preferably not OP", with CT Nu, who
was arguably overpowered, as the feel. The research's HD Remix advice fits: overshoot in the labs and release at the top of
A tier (Sheik, Falcon and Peach level), not S [V research-FG P10].

---

## 2. Must-fix problems, ranked

### MF1. Hits don't convert: the web is all tax and no cash-in

**Problem.** Every threat taxes movement: jump over this, leave that mark, shield the Whirl. None of them says what happens
when it *lands*. The throws "send the opponent away into his zone rather than into a combo". Star Pieces are the only
payoff, and the §4a gain rule makes them a snowball.

**Why it fails in Melee.** Link and Young Link already cover three lanes and still place 17th and 18th, largely because
their hits lead nowhere and they "struggle to kill" [V research-PF §2a]. The top-tier projectiles matter because of what
comes next: Falco's laser gives "free grabs, smashes, or ways to start shine combos", and Sheik's needles lead into a grab
[V research-PF §2a]. The draft's own §7 names "once they're offstage" as the real reward. Nothing in the kit is built to get
them there, or to cover the knockdowns that Melee's knockback produces.

**Fix: give each piece an on-hit state that another piece cashes in** [I]
- **Finger Shot:** Falco-style hitstun, but with a *short* guaranteed window. Within about 25 units it leads to jab, ftilt or
  grab. Beyond that it only interrupts.
- **Whirl, on the outbound hit:**
  - Angle 35-45°. It stays below tumble at 0-35% and starts tumbling around 40-55% on mids.
  - Tumble lands them in a **tech situation** 30-60 units away, which Blast, dsmash and Finger Shot cover (§3.4).
  - The timed crit adds knockback growth (×1.3-1.4) and kills from mid-range at about 120-135% on Fox.
- **Blast** uses Melee's per-hitbox "hits grounded / hits aerial" flags [M] to split its behaviour:
  - Against airborne targets, a **meteor angle** (about 270-280°, so it can be meteor-cancelled). Offstage, this is his
    lethal edgeguard.
  - Against grounded targets, a pop-up at 80-85°. That feeds up-air, the up-arced Whirl or a stored Beam, and it answers
    platform camping.
- **Full Beam (third star):** a real long-range kill threat, killing Fox from centre FD at about 115-125% with good DI. The
  opponent must respect a visible charge or store.
- **Throws** create *situations*, not chains:
  - fthrow and bthrow at 30-35° go toward the ledge. From about 50% at centre stage they put the opponent offstage, into
    Blast and Whirl edgeguards.
  - dthrow puts them in a knockdown or tech situation 20-40 units away at 0-60%.
  - uthrow is a vertical pop into Blast or up-air.
  - All of them are percent-scaling, with no set knockback and no regrab (see MF4).

### MF2. The tools are too slow and too committal for Melee movement

**Problem.** "Individually, each is slow to set up." The Beam needs about 60 frames standing (3 × 20) with no store and
fires itself. Blast has an unspecified call animation during which "Geno is committed", then a 30-frame delay. The Whirl "is
slow at the end of its path". No aerial version has a stated landing rule except Finger Shot's.

**Why it fails in Melee.** The research's first two traits of dominant projectiles are low commitment and speed
[V research-PF §2a]. Nu, the stated model, had swords that were fast, long-ranged and low-recovery and let her "act
immediately" [V Dustloop BBCT]. The draft copies Nu's layering but not the thing that made layering possible, which was
cheapness. Some matchup specifics:
- Falco's lasers and Sheik's needles interrupt a 60-frame charge. Sheik's needles "cut through or stop most other
  projectiles" [V research-PF §2a].
- Fox runs half of FD in about 39 frames [I].
- A projectile that locks Geno in an animation on a 30-frame telegraph gives the opponent a free approach even when they
  dodge the projectile.

**Fix** [I]
- **Price the tools by on-screen count and cooldown, not by animation** (Sakurai's Gordo rule is about count [V research-PF
  P3]).
- **Speed budgets.** Numbers are in §4.1. In short:
  - Finger Shot comes out on about frame 10 grounded and frame 7 aerial.
  - Whirl spawns on frame 15, IASA 32.
  - Blast places its mark on frame 10, IASA 30, with the beams landing about 32 frames after the mark.
  - Beam stars at frames 15, 30 and 45.
- **Aerial versions don't stall and have no special landing lag after a short early window** (Sheik's needles are the
  template: "no landing lag after being used in midair" [V research-PF §2a]).
- **Beam store with decay.** Shielding during the charge stores the current star count, shown as one to three stars circling
  his right fist. Each stored star decays after 150 frames. Firing from a store has no timed bonus: releasing on the star
  during a live charge is the skill path, and the store is the safe path. This keeps SMRPG's verb and answers the research's
  worry that a store "keeps his neutral threatening all game": it can't, because it decays. The research quotes Samus's
  Melee charge-cancel lag as 8 frames, so use 8 as the store lag [V research-PF §4.3].

### MF3. Close range has no floor: the Fox, Falco, Sheik and Marth pressure problem

**Problem.** The draft gives him a short grab ("since his hands are fists"), an up smash out of shield on frame 9-10 (10-11
frames out of shield), nair on frame 4-5, a "slow" up tilt, and every close move low-reward.

**Why it fails in Melee.** Shield grab is Melee's universal answer to pressure, and a short grab weakens it for no identity
gain. Without a real out-of-shield option, the characters with true or near-true shield pressure take stocks:
- Fox's drill into shine;
- Falco's pillars and SH laser into grab;
- Marth's tipper fair on shield;
- Sheik's ftilt and needles into grab.

Shield release is slow in Melee (about 15 frames [M]), so jump out of shield is the real escape, and his jump-out-of-shield
options are slow. The research asks for "one honest out-of-shield option and one get-off-me move" [V research-PF §4.9]. The
draft's §10 Q2 says Nu "had almost none", which is wrong [V Dustloop BBCT]:
- a 6-frame 5A as her fastest close option;
- a head-invulnerable 6A anti-air;
- a fast 2C;
- a backdash with 6 invulnerable frames.

Her weakness was "poor defensive options" in the sense of *slow reversals* (a 24-frame Distortion Drive) and low health. She
was not helpless.

**Fix** [I]. The close range stays weak on *reward*, not on *escape*.
- **Grab:** standard length (Falco or Mario class), standing grab on frame 7. The fists theme can live in the pummel and
  throws.
- **Nair:** frame 4, with a disjointed star core. Total out of shield is 8 frames (4 jumpsquat + 4). It sends at a low angle
  (about 35°) with base knockback that puts them at Finger Shot range, which resets to *his* range instead of combo.
- **Up tilt:** frame 6-7 with a disjointed cape arc, as the anti-air. Give the cape no hurtbox.
- **Up smash out of shield:** keep it at 10 frames total as the kill option.
- **Keep:** no frame-1 move, and no close-range combo starter.
- **Nu's backdash translated:** a long wavedash back (traction 0.06) plus good air acceleration (0.05). This is his real
  escape, and it is the part of Nu that transfers exactly.

### MF4. The loop, lock and ledge rules are too narrow (Mike Z's "assume they already found it")

**Problem.** §8's ledge rule is "Blast marks can't be placed on the ledge he holds." Nothing covers:
- **Ledge-drop, double jump, Blast on the stage lip, regrab.** Vanilla Melee regrants ledge invincibility on every regrab,
  which is why PM capped it [V research-PF §3.3]. That is planking while the stage is covered.
- **Whirl hovering over the ledge while he regrabs,** with the recall hit as ledge coverage.
- **The Whirl's "buzzsaw" hover.** A lingering multi-hit is a lock generator (hover into Blast column into Finger Shot).
- **A widened Blast covering tech-in-place and both tech rolls at once,** which is unreactable full coverage.
- **Vertical Blast columns poking shrunken shields** on tall characters (Marth, Sheik, Falcon, Ganondorf, Zelda) [I].
- **Blast plus Whirl plus Finger Shot on shield** with no stated gap.

**Why it fails in Melee.** Geno can't rely on patching the ledge or on the tournament ledge-grab limit [V research-PF P7,
§3.3]. Melee has no burst or combo breaker, so each loop has to end on its own [V research-FG §2].

**Fix: structural rules, in Mike Z's fault-tolerant style** [I]
1. **A ledge grab or helpless fall despawns his Whirl and cancels any pending Blast.** One rule kills plank-with-coverage
   and recovery-with-coverage.
2. **Blast can't be cast while Geno is below ledge height.** Edgeguards are cast from the stage or above. The Whirl stays
   usable offstage, because a deep edgeguard is a real risk.
3. **The hover hits each target once per throw.** No multi-hit. It does 4-5% and knocks away and up. The outbound hit and
   the recall hit are also once per target.
4. **Shield gap rule.** No sequence of Geno's hits on a shielding opponent (with or without Geno acting) may leave less than
   **9 frames** between the end of shieldstun and the next hit. That is Bowser's 8-frame jumpsquat plus one. The rule applies
   at every spacing, from any sequence, and at least once every 40 frames.
5. **Blast width cap.** One placement covers at most two of the four tech outcomes (in place, roll left, roll right, missed
   tech), measured from any knockdown his hits can cause.
6. **Shield-damage cap.** One full cycle (Finger Shot + Whirl + widened Blast) removes at most 30 of the shield's 60 HP [M].
   Measure poke exposure at 50% shield on the five tallest characters.
7. **Knockback growth ends every loop.** Every hit Geno lands that leads into another of his hits must stop being true
   by 60-80% on the heaviest characters, and must be SDI- or DI-escapable at every percent.

### MF5. Physics in the light, floaty corner, and the spec is incomplete

**Problem.** Weight 82, fall speed 1.8 and gravity 0.085 put him beside Mewtwo (85, 1.5, 0.082), the research's cautionary
tale, and he's lighter [V CSV]. The target "kill percents near Falco's and Marth's" doesn't match these numbers: Falco's
gravity is 0.17 and his fall speed 3.1, so Falco survives vertically far longer than a 0.085-gravity character can. The draft
also leaves out the attributes that decide how a retreating zoner plays:
- air acceleration and air friction;
- short-hop and full-jump velocity, and the double-jump multiplier;
- per-aerial landing lag;
- a hurtbox policy for the big hat, collar, cape and clogs.

**Why it fails in Melee.** Low gravity doesn't help retreat. Air speed and air acceleration do. What low gravity does is
lengthen the short hop, so every SH aerial and SH Finger Shot takes longer, and it lengthens juggles, which is Mewtwo's whole
problem. My rough simulation from the CSV values [I] gives these short hops:

| Character | SH airtime, no fast fall | With fast fall |
|---|---|---|
| Geno (draft) | about 37 frames | about 25 frames |
| Marth | about 37 | about 25 |
| Falco | about 24 | about 17 |

The simulation is rough, but the ratio is right. A head-heavy, three-heads-tall doll with a floppy hat is also a large
target and a shield-poke risk.

**Fix.** See §6 for the table. The short version: weight 86, fall 1.9, fast fall 2.6, gravity 0.095, air acceleration 0.05,
short-hop velocity 1.55, and landing lags specified. **No hurtbox on the hat point, cape or collar tips.** Shield coverage is
set to his head and hat band at full size.

### MF6. Star Pieces and Geno Flash, as specified, are either a snowball or dead weight

**Problem.**
- The gain rule "a projectile that connects earns a Star Piece" rewards the thing he's already winning at. Finger Shot chip
  reaches 7 in about 7 connects.
- Flash is described as reactable and escapable ("the opponent sees it coming and can run or shield"). A super like that is
  not a win condition.
- If the sun is large, armoured and long-lasting, it becomes a checkmate on small stages and a shield-break machine.
- At 7 pieces, down-B *becomes* Flash, so Geno loses Blast, his edgeguard and anti-platform tool, until he spends them. That
  forces bad spends.

**Why it fails in Melee.** Melee has no meter and no comeback mechanic, so a resource that grows with success compounds. A
new universal rule also has to be learned by every opponent [V draft §4a risks; research-FG §2 "Tag, assists, meter: doesn't
transfer"].

**Fix.** See Q1 in §7. Don't ship it in v0, and make Flash the third star of down-B.

### MF7. The draft contradicts itself on projectile discipline

**Problem.**
- The jab's rapid "Finger Shot barrage (bullets leave the fingers)" is a second fast projectile on A. That puts Fox's fire
  rate on the jab next to Falco's hitstun on neutral-B. The research warns against shipping both templates [V research-PF
  §4.2].
- It contradicts "his one fast projectile" and the fair note that keeps "the on-screen projectile count at three types".
- §1 promises a *ground* lane, but no move provides one.
- Finger Shot's on-screen cap is unstated.

**Fix** [I]
- The jab barrage is short muzzle hitboxes that don't travel more than about 1.5 body widths and are SDI-able. It ends in a
  push-away finisher.
- Cap Finger Shot at 2 on screen.
- Give the ground lane to the Whirl: a down-arced Whirl hits the floor and rolls along it for the rest of its travel. That is
  Nu's Sickle Storm, a ground-travelling blade [V Dustloop BBCT].

### MF8. Undefined interactions that the prototype will have to decide anyway

Decide all of these before the blockout. Most are one-line calls [I, except where marked].

- **Input conflict on the Whirl.** "Pressing B while it hovers recalls it" collides with neutral B (the Beam) and with the
  crit press. Use **side-B again** for both: during travel it is the crit, if pressed within about 4 frames of contact, and
  an early press voids the crit for that throw so mashing doesn't work. During hover it is the recall. Neutral B stays the
  Beam.
- **Blast geometry:**
  - how tall the column is (I suggest about 60 units above the mark);
  - whether it stops at the mark or at the first surface below it;
  - whether it passes through platforms (I suggest yes);
  - whether it survives Geno being hit (I suggest yes, since that is the "act immediately" payoff);
  - how it reads at FD's maximum camera zoom.
- **Energy or physical,** which decides whether Ness's PSI Magnet and Game & Watch's Oil Panic absorb it [M]:
  - Finger Shot is bullets, so physical.
  - The Beam, Blast and Whirl (a disc of light) are energy.
  - This gives two low tiers a matchup tool, which is healthy.
- **Blocking and reflection.** Link's and Young Link's shields block frontal projectiles while they stand, walk or crouch
  [M]. Blast from above and the curved Whirl are exactly the right answers to that, so lean in. Reflectors are more than Fox
  and Falco: Mario's and Dr. Mario's capes, Mewtwo's Confusion, Zelda's Nayru's Love and Ness's forward smash (the bat) all
  reflect [V SmashWiki Reflection]. Powershield reflects at 0.5× damage [V].
- **Reflector break.** It is real in Melee: "If a projectile is too strong for a reflector, the reflector breaks as if it was
  a shield and stuns the user" [V SmashWiki Reflection]. The threshold has to come from the decomp. **I recommend keeping
  every Geno projectile under it.** A shattered reflector means a shield-break stun, which is a stock off a knowledge check.
  Reflected damage is 1.5× for Fox and Falco [V], so check that a reflected full Beam (about 17% becoming about 26%) doesn't
  kill Geno below about 90%.
- **Clanks.**
  - Finger Shot against Falco's lasers and Sheik's needles.
  - The Whirl against incoming projectiles. **I suggest the Whirl cancels projectiles under 6% and survives, and breaks on
    6% or more.** That gives him a placed "his swords beat your shots" wall against Falco, Sheik, Samus, Link and Young Link,
    and they can still jump it.
  - Turnips and bombs against the Whirl.
- **Crouch height.** A projectile at Geno's arm height may sail over crouching Jigglypuff, Kirby, Pikachu, Fox and the Ice
  Climbers. Lab-check every projectile against every crouch hurtbox.
- **Double Punch's fists.** Make them bone-attached hitboxes on extended arms, not items, so shine can't reflect his fist.
  The fists are disjointed and have no hurtbox.

### MF9. Recovery numbers decide whether "committal" means "dead every time"

**Problem.** "Aims ... for a few frames", no hitbox, helpless fall, "moderate distance". The fold and aim window is the whole
question. At 20 or more frames with no hitbox, Sheik's needles, Falco's lasers, Marth, Fox's shine and Jigglypuff all get a
free hit before he moves.

**Other recovery risks.** Bair "recoil forward", Beam charging in the air and "committed during the call" Blasts are all
possible stalls or horizontal extensions if they touch his momentum.

**Fix** [I]
- **Timing:** fold on frame 6, a 12-frame aim window that auto-fires at the end, 16 directions, and travel of about 28 frames.
- **Distance:** total recovery (double jump plus up-B) between Falco's and Fox's, measured in the lab.
- **Landing and ledge:** 24 frames of special landing lag on stage, and ledge snap from frame 10 of travel.
- **No stalls:**
  - No aerial special changes vertical velocity.
  - Bair recoil only on the first bair per airtime, and capped below his air speed.
  - The Beam charges in the air under normal gravity.
- **Hitbox:** see Q3 for a small hitbox at launch.

---

## 3. The Nu-13 translation

### 3.1 What I know and what I'm inferring

**Known [V]: Dustloop's BBCT Nu-13 page, fetched 2026-09-27.** Its summary: "a highly mobile zoner who hits like a truck and
breaks the game's mechanics to win", "one of the best characters in Calamity Trigger", "arguably the easiest of the Top 3 to
play", and "remind you why everyone moved on to Continuum Shift". Specifics:
- **Health:** 10,000, listed as low.
- **Close range:** fastest option 5A at 6 frames; a head-invulnerable 6A; a fast 2C; a 24-frame backdash with frames 1-6
  invulnerable.
- **Drive swords:**
  - 5D: 13F startup, -10 on block, near full screen.
  - 2D: 11F, an anti-air that vacuums on hit.
  - 6D: an angled anti-air.
  - 4D: appears anywhere on screen, forcing a high/low mixup, with 30F startup.
  - All D moves have low recovery and let her "act immediately".
- **Specials:**
  - Sickle Storm (236D): a ground-travelling blade. The C version reverses or spawns behind the opponent.
  - Spike Chaser (214D): a delayed sword wave. The C version has longer range and is +20 on block.
  - Crescent Saber (j.214D): an overhead with a feint version.
- **Why she won:** "high-damage combos from fullscreen stray hits", "numerous hard knockdown enders", "huge meter gain",
  "consistent knockdowns", and Guard Libra abuse that could "lock the opponent in sword hell". (Guard Libra is CT's
  push-and-pull guard gauge; filling it crushes the guard.)
- **Weaknesses:** "low health", "slow reversal options" (a 24-frame Distortion Drive), "must rely on universal mechanics to
  escape pressure".

Dustloop's Central Fiction page, also fetched, adds that her swords are "faster and covers a longer range than most other
projectiles". That is a later version, and I'm using it only as consistent colour.

**From memory [M]:**
- Her CT Distortion Drives were named Legacy Edge (a sword barrage) and Calamity Sword (a reversal).
- CT had Barrier guard and Instant Block as universal defence.
- She had a gravity-themed special. The fetched page lists "Gravity Shield 214A/B/C" but the content was truncated, so I
  can't confirm what it did in CT.

**Inference [I]:** everything about how these traits map onto Melee.

### 3.2 What made CT Nu strong and fun, and what the draft captures

| CT Nu trait | Draft | Melee adaptation |
|---|---|---|
| **Cheap swords:** low recovery, "act immediately" | **Missed.** Every piece is "slow to set up"; Beam 60f; "committed during the call" | MF2: fast startup, no-stall aerials, count-limited instead of animation-limited |
| **Many angles at once:** horizontal (5D), steep anti-air (2D), 30° anti-approach (6D), anywhere on screen (4D) | **Partly.** Straight lane (Beam, Finger Shot), curve (Whirl), drop (Blast). No fast anti-air projectile; no ground lane | Up-arc Whirl as the angled anti-air; down-arc Whirl rolls along the ground (the ground lane); Finger Shot at SH-approach height is the "6D" |
| **4D: a threat that appears at the opponent's location on a delay** | **Captured** by Blast (stick-placed mark, ~30f delay) | Keep stick placement as a read, not tracking. A tracker would be too strong with Melee's movement tax [I] |
| **Sickle Storm reverses, or hits from behind** | **Captured** by the Whirl recall | Recall sends up (80°) into juggles, once per target |
| **Stray hit → big damage → hard knockdown → setplay** | **Missed.** Hits give chip and a Star Piece, then reset | **The most important missing piece (§3.4):** tech chase is Melee's okizeme |
| **Guard Libra: blocking swords had teeth** | Hinted ("Blast lands on the shield") | Shield chip and poke with a hard gap rule (MF4). Melee's shield break is a free stock, so there must be *no* lock |
| **Huge meter gain → Distortion Drives** | Star Pieces → Geno Flash | Don't import meter (Q1). Flash as a third-star read or punish |
| **Low health, slow reversals** | **Captured** (light, no frame-1) | Keep. But Nu still had a 6F button, invulnerable anti-airs and an invulnerable backdash (MF3) |
| **The fun for the Nu player:** creative layering, full-screen confirms | Pillar 2 ("building a web") | Needs cheapness (MF2) and cash-in (MF1) to be fun in practice |

### 3.3 What the opponent did, and what changes in Melee

Against CT Nu, the opponent tried to read the gaps between swords (her recovery windows), blocked through sword pressure
while the Guard Libra went against them, and hunted for the moment they breached the wall, where her low health and slow
reversals made a clean rushdown deadly [V for the last part, Dustloop: "Weak Under Pressure"]. Universal tools like Barrier
and Instant Block shaved the pressure [M].

Melee changes this in three ways [I]:
- **Movement is far stronger relative to projectile speed.** Wavedash, dash-dance and platforms give the opponent more
  approach paths than BlazBlue's dashes and air dashes, so Geno's tools need Nu-level cheapness just to register.
- **Powershield reflects,** which BlazBlue's Instant Block didn't [M]. So does a frame-1 shine. Melee zoning carries
  reflection risk, so Geno's gaps are more dangerous than Nu's were.
- **There's no guard crush from chip, but shield break is lethal.** Nu's "sword hell" becomes a loop problem in Melee (MF4).

### 3.4 The most important missing piece: stray hits into tech chase

Nu won off *stray hits that turned into damage, then into knockdowns, then into more swords*. Melee has the exact structural
equivalent: **tech chasing.** A knocked-down opponent picks from tech in place, tech roll toward, tech roll away, a missed
tech with getup options, or a sliding knockdown. Each tech has an invulnerable window, then a vulnerable end [M]. A zoner who
can cover different tech outcomes *from range with different pieces* is doing Nu's setplay in Melee's vocabulary. It is also
a real Melee skill test for both players: reading the tech, and teching unpredictably.

Concretely [I]:
1. **Knockdown sources:** Whirl outbound hit (35-45°), dthrow, dtilt at low percent, and the grounded Blast pop at mid
   percent.
2. **Coverage:**
   - Blast placed on the knockdown point covers tech in place and the missed-tech getup.
   - Finger Shot covers the roll away.
   - dsmash covers the roll toward and a stand-up (both sides).
   - The Whirl hover left beyond them covers a long roll away.
3. **Limits:**
   - A single Blast covers at most two outcomes (MF4 rule 5), so it's a read, not a lock.
   - Knockback growth moves them out of knockdown range by about 60-80% on mids.
   - The Blast's delay is tuned to the *end* of the tech animations, so a perfectly timed read is required.
4. **Offstage version:** the same pieces cover ledge options. The Blast meteor covers a high recovery, the Whirl covers the
   ledge snap, Finger Shot covers the low path. Melee's edgeguard is the second half of Nu's corner.

This single change turns the draft's "chip, reset, chip" loop into "chip, *knockdown*, read, big reward". That was the
engine of CT Nu's damage.

---

## 4. Per-move notes

### 4.1 Specials

| Move | Proposed targets [I] | Notes |
|---|---|---|
| **Finger Shot** (tap B) | Grounded: fires F10, IASA 34. Aerial: fires F7, 24f animation; 10f landing lag only if he lands during it. 3%, ~4 u/f, fades at ~75 units (under half of FD). Max 2 on screen. Physical; reflectable | Falco hitstun with a short range. The long lane belongs to the Beam. A floatier short hop makes SH-shot cycles ~40-50% slower and higher than Falco's (§6), which is a natural brake |
| **Geno Beam** | Stars at F15, 30, 45. Release within ±3f of a star's flash for the timed bonus (+10% damage, chime). Past star 3, 20f grace, then it auto-fires. Release startup 8f, endlag ~25f. Shield stores stars (8f lag); stored stars decay one per 150f. Full: ~17%, near-full-screen fast bolt, kills Fox mid-stage ~115-125%. Air: normal gravity while charging; 20f special landing lag only if he lands during release. Energy; reflectable (below the break threshold) | MF2. Visible charge and store are the opponent's tell (research-FG P7) |
| **Geno Whirl** | Spawn F15, IASA 32. Aerial: 12f landing lag only if he lands before F24. ~65 units of travel over ~28f, decelerating; stick curves it ±20° up or down. Down-arc rolls along the floor. Outbound hit 8% at 35-45°; crit (side-B within ~4f of contact) ×1.35 knockback growth. Hover 45f, 4-5%, once per target, knocks away and up. Recall with side-B: ~4 u/f, 6%, 80°, once per target. Breaks on any hit of 6%+; cancels incoming projectiles under 6%. Side-B locked while out, plus 30f after despawn unless caught | His most important piece. The hover-lock and plank rules are MF4. The draft's counterplay line "approach while it's out" needs rewording, because the hover zone is between them |
| **Geno Blast** | Mark appears F10, IASA 30. Distance from the stick (three presets or analog, ~25/50/75 units). Beams land ~32f after the mark. Column ~10 units wide, ~60 tall above the mark. Hold +18f to widen to 3 columns (±14u), capped by MF4 rule 5. 9% per column; airborne targets meteored (cancellable), grounded popped at 80-85°. One set of marks at a time. Unusable below ledge height; cancelled on ledge grab or helpless fall; survives Geno being hit. Energy | Melee precedent: Pikachu's Thunder (from above, an edgeguard and anti-platform tool) [M]. The anti-Link and Young Link shield lane |
| **Geno Flash** | Third star of down-B (Q1). ~75f to charge with visible cannon transformation, fires ~F90, the sun grows over ~40f to a radius of ~35-40u, lingers ~30f. Kills Fox ~70-80% at its core. **No armour in v0.** Endlag ~40f | A read and punish tool: shield break, missed tech, Rest, ledge. Not a neutral tool and not a win condition |
| **Star Road** (up-B) | Fold F6, 12f aim (auto-fires), 16 directions, ~28f travel. Distance between Falco's and Fox's. Launch hitbox (Q3): 4 active frames at the muzzle, 6-7%, sends away. No hitbox in flight. Helpless; 24f special landing lag on stage; ledge snap from travel F10 | MF9 |

### 4.2 Normals

| Move | Proposed targets [I] | Notes |
|---|---|---|
| Jab | F3, 3%. Rapid finger taps are **non-travelling** muzzle hitboxes; push-away finisher | Get-off-me. MF7 fixes the projectile contradiction |
| Forward tilt | F7-8, disjointed wrist blast, 10%. Safe only at max range on shield | A spacing poke. Fine as drafted |
| Up tilt | **F6-7** (not "slow"), disjointed cape arc (cape has no hurtbox), 30f total | His grounded anti-air. The draft's "slow" leaves no anti-air against Marth and Jigglypuff |
| Down tilt | F6, low profile, trips at low percent (Kirby's down tilt is the Melee precedent [M]) | A knockdown source for §3.4 |
| Dash attack | Committal, mid reward | Chaff, and that's acceptable (most Melee dash attacks are) |
| Forward smash | F14-16; fists on extended arm bones (not items); the outbound hit is strong, the return hit weak; ~45f total; kills Fox ~100-110% at the tip | A long disjoint, punishable on whiff and on shield. A timed-hit candidate if Q4 widens |
| Up smash | F9 (10 out of shield); kills Fox ~105-115% | Out-of-shield kill option. Fine as drafted |
| Down smash | F7-8, both sides; knockdown or roll cover | A tech-chase tool (§3.4) |
| Neutral air | F4, disjointed star core, low angle (~35°) away; landing lag 14 (7 L-cancelled) | Out of shield in 8 frames (MF3) |
| Forward air | F6, 3 active frames, long disjointed burst; landing lag 16 (8 L-cancelled); 10-11% | Keep it one notch below Marth's fair (Marth's is ~F4 with 15 landing lag [M]). A zoner shouldn't also own Marth's best move |
| Back air | F7-8, kill move when turned around; recoil only on the first bair per airtime, capped below air speed | Uncapped recoil is an aerial-spam recovery exploit (MF9) |
| Up air | F5-6, disjointed upward burst, not a projectile | Juggle; weaker than up smash |
| Down air | **Change it:** a downward muzzle blast, F8-10, a disjoint below him, meteor sweetspot (cancellable angle), landing lag 24 (12 L-cancelled) | The draft's slow boot stomp is chaff next to Blast's edgeguard. A floaty zoner needs a *landing* tool to escape juggles (Mewtwo's problem) more than a second spike |
| Grab and throws | Standard range, standing grab F7. fthrow/bthrow 30-35° toward the edge; dthrow knockdown; uthrow vertical pop. No set knockback; no regrab on Fox, Falco or Falcon at any percent | MF1 and MF3. "Every throw weight-dependent" is already Melee's default; the thing to ban is set-knockback throws [M] |

### 4.3 Chaff

As drafted, the dash attack, down air (the stomp, redundant with Blast's meteor), and the jab barrage's projectile version
are chaff. If the timed crit on the Whirl stays balanced as "always hit", it isn't a decision, only a chime. That's fine as
flavour, but it doesn't earn a design line.

### 4.4 Answers to the matchups that will test him

| Threat | Draft's answer | Gap | Fix |
|---|---|---|---|
| **Fox and Falco rushdown** (drill or pillar into shine, SH laser into grab) | "Getting in is the answer; his close range is weak" | No out-of-shield option, a short grab, slow up tilt | MF3's 8f nair out of shield, a normal grab, and the Whirl hover as a pre-placed wall. Crouch-cancel their drills at low percent (universal) |
| **Falco's lasers** (interrupt charges, outcamp) | None stated | Falco's laser is faster and cheaper than any Geno piece, and his reflector returns everything | The Whirl cancels shots under 6%; Beam store with decay; Blast from above (Falco's lasers are linear) |
| **Sheik's needles** (cut or stop projectiles, stored charge, no landing lag) | None | Needles beat Finger Shot and interrupt the Beam | Same Whirl property; Blast punishes a grounded needle charge; floatier Geno can't out-speed her, so he must out-angle her |
| **Platform camping** (Falco or Sheik on Battlefield's top platform) | Implicit (Blast) | None, once Blast is specified | The Blast pop on grounded targets works on platforms; the up-arc Whirl |
| **Jigglypuff** (air mobility 1.35, bair wall, ducks lines, Rest kills a light character early) | "Must have a real path in" (§8) | Lines miss her crouch and her drift; his anti-air is slow | Blast (anti-air from above), up-arc Whirl, F6 up tilt. Lab: crouch-height check. Risk: a mutual-camping timeout (§5) |
| **Peach's float** (lagless float aerials, turnips) | None | Float height sits between his lanes | Blast from above hits a floating Peach; Finger Shot at float height; decide whether the Whirl clanks turnips (MF8) |
| **Link and Young Link shields** (block frontal projectiles) | None | The straight lanes do nothing | Blast and the curved Whirl, which is exactly the lane design working |
| **Ness and Game & Watch absorbs** | Ness mentioned | Game & Watch's bucket absent | Energy tagging (MF8). A matchup tool for two low tiers is good |
| **Samus** (stored Charge Shot, missiles, heavy, great recovery) | None | His no-store Beam loses the charge war; she lives long | Store with decay; edgeguard with the Blast meteor |
| **Ice Climbers** (grab threat) | None | A short grab and weak close range | Zoning separates Nana (Whirl hover, Blast); a normal grab |

---

## 5. Degenerate-strategy audit, and what the labs must prove

| Strategy | Risk [I] | Rule | Lab proof (pass criterion) |
|---|---|---|---|
| **Planking with stage coverage** | High if Blast or the Whirl can be set from under the ledge | MF4 rules 1-2 | Script every ledge-drop → DJ → special → regrab sequence. Pass: no Geno hitbox is active on stage while he has ledge invincibility |
| **Ledge-drop Finger Shot regrab** | Medium; Falco has this in vanilla | Allowed for parity with Falco; don't extend it | Pass: coverage, measured in frames of hitbox on the stage lip per regrab cycle, is no greater than Falco's version |
| **Aerial stalls** (Beam charge, Blast call, Whirl throw, bair recoil) | Medium; the research's stalling rule [V research-PF §3.4] | No aerial special modifies vertical velocity; bair recoil once per airtime | Pass: max airtime from ledge-drop to landing, using any input string, is no more than 110% of the no-special airtime |
| **Final Destination camping and timeouts** | High for a zoner with air speed 1.0 and a projectile wall | None structural; counterplay in the kit | Pass: optimal-approach bots for Falcon, Marth and Jigglypuff reach close range within ~5 seconds on FD with at most ~15% taken on average; human sets record timeouts per set |
| **Mutual camping with Jigglypuff and Peach** | Medium | None | Record timeouts in human sets; flag if more than 1 in 10 games times out |
| **Shield lock or pressure without a gap** | High once the tools are fast | MF4 rule 4 | Brute-force every 2-4 piece ordering at every 5-unit spacing on the eight characters with the smallest shield-to-body coverage. Pass: a gap of 9f or more at least every 40f |
| **Shield break by chip or poke** | Medium (vertical columns on shrunken shields) | MF4 rule 6 | Pass: no ranged-only sequence breaks a full shield; poke exposure at 50% shield measured on Marth, Sheik, Falcon, Ganondorf and Zelda |
| **Whirl hover and Blast combination** | High with a multi-hit hover | Once-per-target hover; percent scaling | Pass: every two-piece string escapes by DI or SDI at every percent; none is true past 80% on any weight |
| **Recall sandwich** (hover → recall through them → dsmash) | Medium | Recall sends up at 80° | Pass: not true on any character past 30%, and escapable by SDI |
| **Tech-chase loop** (knockdown → Blast → knockdown) | Medium to high | MF4 rule 5; knockback growth | Pass: one placement covers two tech outcomes or fewer; the loop's knockdown range ends by 60-80% on mids |
| **Edgeguard checkmate** (Blast wall + Whirl + Finger Shot on slow recoveries) | Medium (strong edgeguarding is desirable in Melee) | One set of marks; ~32f tell; meteors are cancellable | Pass: for Falcon, Ganondorf, Falco, Dr. Mario and Ice Climbers, at least two recovery paths (timing or angle) beat any single coverage setup |
| **Throw chains** | Low as drafted | No set knockback | Pass: no regrab on Fox, Falco or Falcon from 0-60% with best DI and DI mixes (the draft's own test) |
| **Star Piece snowball** (if kept) | High with projectile-connect gain | See Q1 | Pass: median time to 7 pieces in human sets is at least 60 seconds of stock time |
| **Reflector break** | Medium, a knowledge-check stock loss | Keep every projectile under the threshold | Read the threshold from the decomp; assert each projectile's damage is below it |
| **Recovery reward** | Should favour the edgeguarder | MF9 numbers | Score against PM's recovery factors [V research-PF P5]; pass if Fox, Falco, Sheik, Marth and Jigglypuff each have a low-risk edgeguard on at least half of his recovery angles |

---

## 6. Physics against the CSV

Cast statistics computed from `cast_attributes.csv` [V]. I checked the draft's min, median and max figures: all correct.

| Attribute | Draft | Recommendation [I] | Why |
|---|---|---|---|
| Weight | 82 | **86** (84-88) | Keep him light, but not lighter than Mewtwo (85). Fox at 75 and Falco at 80 compensate with fall speed; Geno can't |
| Fall speed / fast fall | 1.8 / 2.4 | **1.9 / 2.6** | Median fall speed (1.9, like Pikachu and Bowser). Lets him get back to the ground out of juggles; still clear of the fast fallers' chaingrabs |
| Gravity | 0.085 | **0.095** (Mario's) | Low gravity lengthens juggles and the short hop and doesn't aid retreat. Air speed and acceleration do that. Also makes "vertical kill percent near Marth's" achievable |
| Air speed | 1.0 | 1.0 | Agree |
| **Air acceleration** | unspecified | **0.05** (Falco's; cast median 0.03) | The real retreat stat. How fast he can reverse drift into a retreating fair. Samus's 0.0125 is what bad looks like |
| **Air friction** | unspecified | 0.015-0.02 | Around the median |
| Jumpsquat | 4 | 4 | Agree |
| Dash / run | 1.55 / 1.6 | 1.55 / 1.6 | Agree |
| Walk | 0.95 | 0.95 | Agree |
| Traction | 0.065 | **0.06** | A Marth-length wavedash is his Nu "backdash" |
| Jumps | 2 | 2 | Agree. No multi-jump; that is a stall and recovery lever |
| **SH / FH vertical velocity** | unspecified | 1.55 / 2.5 (medians) | Keeps SH aerials low; my rough sim puts his SH at ~34f, or ~24f fast-fallen |
| **DJ multiplier** | unspecified | 0.95 | Median |
| **Landing lags** | unspecified | Normal 4; nair 14, fair 16, bair 18, uair 16, dair 24 (L-cancelled 7/8/9/8/12) | Specify them now; shield safety depends on them |
| Shield size | 11.9 | Set by coverage, not the median | The raw ShieldSize values look model-relative (Yoshi 6, Pichu 24.3, Bowser 31.25), so the median isn't a target [I; confirm in the decomp]. Cover the head and hat band at full shield |
| **Hurtboxes** | "match the finished silhouette" | **No hurtbox on the hat point, cape or collar tips.** Head hurtbox Marth-class. Body height within Marth's and Sheik's range | Decide before the blockout. A large doll silhouette is combo food and a shield-poke target |

**Kill-percent targets.** "Near Falco and Marth" isn't reachable with 0.085 gravity (Falco's is 0.17). Target "within ±5%
of Marth's" for both vertical and horizontal kills, and measure with Fox's up-throw into up-air, Marth's tipper fsmash and
Sheik's up-air.

---

## 7. The five open questions

1. **Star Pieces, or no resource?** **No gameplay resource in v0.** Make **Geno Flash the third star of down-B**: hold
   through Blast's first and second stars (widen), and the third turns into the cannon and sun (§4.1). This is SMRPG's verb,
   holding to the third star, and it's consistent with the Beam's stars. It keeps Blast available at all times, and it makes
   Flash a readable punish (shield break, missed tech, Rest, ledge) instead of a checkmate or a dud.

   Star Pieces can stay as a *cosmetic* timed-hit chain counter, like the remake's chain counter [V geno-source §2].

   If you want a resource anyway, gate it hard:
   - gain only from *distinct* move types, at most one per move type every 5 seconds;
   - lose two when Geno takes a strong hit;
   - reset on KO;
   - never replace Blast.

   Reason: gaining from projectile hits compounds success in a game with no comeback mechanic, and meter "doesn't transfer" to
   Melee [V research-FG §2].
2. **Pure zoner, or one strong close-range option?** **One honest *defensive* option** (an 8-frame nair out of shield that
   resets to range, plus a normal grab), and **no offensive close-range game.** Reason: Melee's rushdown characters will
   shield-pressure a character with no escape to death, and CT Nu herself had a 6-frame button, a head-invulnerable
   anti-air and an invulnerable backdash [V Dustloop BBCT]. The weakness should be *low reward up close*, not *no escape*.
3. **Up B with no hitbox, or a small hitbox at the end?** **A small hitbox at the *launch*:** a muzzle blast around the
   cannon on the fire frame, 4 active frames, 6-7%, sending away. **No hitbox in flight or at the end.** Reason: a hitbox at
   the end protects the ledge snap and landing, which are exactly what edgeguarders are meant to win. A hitbox at launch
   only stops "stand on the cannon for a free hit" during the 18-frame fold and aim. That leaves distance plus a small
   hitbox and no invulnerability, which is within the research's "pick at most two" [V research-PF §3.5].
4. **Timed hits on every move, or only specials and signatures?** **Specials only in v0** (Beam release, Whirl crit, Blast
   and Flash stars). Add Double Punch later if testers miss it. Reason: since balance assumes a perfect press
   [V research-FG P8], a timed press on a normal is a flat expert buff and a tax on everyone else, with no decision in it. On
   specials the timing *is* a decision: fire at star 2 now or wait for 3; crit or save side-B for the recall; widen or keep
   the Blast fast. It also avoids input overlap with jab strings, L-cancel and aerial presses, and it separates Geno from
   Legacy XP's "timed hits on everything" [V geno-source §6].
5. **Geno Boost on the taunt, or left out?** **Leave it out of v0.** At most, a cosmetic taunt with the red arrows. Revisit
   only if labs show him under target, and then only as a long, punishable, one-hit buff that can't stack with a stored Beam
   or Flash (the Shulk rule [V research-PF §4.5]). Reason: a buff funded by the space zoning creates is another snowball
   lever, and it is one more state for opponents to track in a game where taunts aren't normally gameplay (Luigi's taunt
   hitbox is the lone precedent [M]).

---

## 8. Factual errors and citation fixes

| Draft says | Correction |
|---|---|
| §1: "Project M 3.02 had to tone every projectile character down" | Backwards. 3.02 is the version where projectile characters could "zone other characters out", and **3.5** "toned all of this down" [V research-PF P6]. "Every projectile character" overstates a secondary source (Wagar). |
| §10 Q2: "Nu-13 had almost none" (close range) | CT Nu had a 6F 5A, a head-invulnerable 6A anti-air, a fast 2C and a backdash with frames 1-6 invulnerable. Her weakness was slow reversals and low health [V Dustloop BBCT]. |
| §5 Whirl: "a hit of 6% or more breaks it (the research's Missile lever)" | Melee's Missile breaks at 4% [V research-PF §2a]. 6% is our number; label it that way. |
| §3: "Tune kill percents against him to sit near Falco's and Marth's" | Not reachable with gravity 0.085 and fall speed 1.8. Falco's gravity is 0.17 and fall speed 3.1 [V CSV], so Falco survives vertically much longer. |
| §3: "Fall speed 1.8 ... Near Mario (1.7) and Marth (2.2)" | 1.8 sits next to Ness (1.83) and Mario (1.7). Marth's 2.2 isn't "near" it [V CSV]. Minor. |
| §3: Shield size "median 11.9" | The arithmetic is right, but the raw ShieldSize isn't comparable across characters (Yoshi 6, Pichu 24.3, Bowser 31.25). Tune to coverage [I; check the decomp]. |
| §5 Beam counterplay: "powershield reflects it; Fox and Falco reflect it" | Incomplete. Mario's and Dr. Mario's capes, Mewtwo's Confusion, Zelda's Nayru's Love and Ness's forward smash also reflect [V SmashWiki Reflection]. Game & Watch's Oil Panic absorbs energy, and Link's and Young Link's shields block frontal projectiles [M]. §9's lab list ("Ness's absorb") needs all of them. |
| §8 and §5: "whether a full beam breaks their reflector is a lab question" | The mechanic is confirmed for Melee: "If a projectile is too strong for a reflector, the reflector breaks as if it was a shield and stuns the user" [V SmashWiki Reflection]. Only the threshold is a lab question. I recommend staying under it (MF8). |
| §1 "Each of Geno's threats covers a different lane: ground, ..." | No move provides a ground lane. §2's pillars list only straight, curve and drop. Fix with the down-arc Whirl (MF7). |
| §6 fair "keeps the on-screen projectile count at three types"; jab "bullets leave the fingers"; Finger Shot "his one fast projectile" | Internally inconsistent (MF7). |
| "readable across the screen (research P7)", "(research P6)", "(research P8)" | Ambiguous. These are **research-FG** P7, P6 and P8. Research-PF's P6, P7 and P8 say different things (trimming tools, fitting the unchanged cast, adapting a licensed character). Cite by document. |
| §6 dsmash "Hand Cannon from both elbows" | In SMRPG, the Hand Cannon fires from the right elbow [V geno-source §2]. Artistic licence is fine; just not "SMRPG says". |
| §5 up-B: "Legacy XP's version has no helpless fall" | True, but incomplete: LXP's version costs his double jump and airdodge [V geno-source §6]. It wasn't free. |
| §6 throws: "Every throw is weight-dependent" | Melee's knockback formula already includes the victim's weight [M]. What makes chaingrabs is set knockback and low growth, so state the rule as "no set-knockback throws; no regrab past the listed percents". |
| §4b: "+10-15% damage" timed bonus | Not an error, but SMRPG's own numbers are +50% (close) and ×2 (perfect) on weapons, and +25% or +50% on specials [V geno-source §2]. The smaller number is right for Melee; just note that it's deliberate. |

Checked and correct: all the CSV comparisons in §3 (Falco 80 and Mewtwo 85, Marth's gravity 0.085, Peach's 1.1 and Mewtwo's
1.2 air speed, and every min, median and max); Sakurai's Gordo quote and source; research-PF §4.2, §4.5, §4.7 and §4.8; the
2023 buzzsaw Whirl; Stella 023; Geno Flash's cannon and sun; the seven Star Pieces.

---

## 9. What draft v1 should contain before the blockout

- **A frame table for every move:** startup, active frames, IASA, landing lag and L-cancelled lag, damage, angle, base
  knockback and growth, shieldstun, and safety on shield at best and worst spacing (research-FG P6).
- **For every projectile:**
  - speed, range or lifetime, and on-screen cap;
  - energy or physical;
  - reflectable, and its damage against the break threshold;
  - clank rules against lasers, needles and items;
  - behaviour when Geno is hit, grabs a ledge or enters helpless fall.
- **The rules in MF4,** written as code-level invariants the director's labs assert.
- **A hurtbox diagram** (hat, collar, cape, clogs) and a shield-coverage check at full and half shield.
- **The on-hit "cash-in" line for every move** (MF1): what it leads to, at what percent, against which weights.
- **A matchup sheet** against the top eight (Fox, Marth, Jigglypuff, Falco, Sheik, Falcon, Peach, plus Ice Climbers or
  Samus): each character's best answer to Geno, and Geno's answer to that (research-FG P3).
- **Implementation templates in the decomp** [I]: Link's boomerang (return and recall), Samus's Charge Shot (store and cancel
  lag), Pikachu's Thunder (a hitbox from above) and Young Link's arrows (a straight lane). Ported behaviour is known to work
  with Melee's reflect, absorb and clank code.

---

## Sources consulted this session

- The five project files listed at the top.
- Dustloop, BlazBlue: Calamity Trigger, Nu-13: https://www.dustloop.com/w/BBCT/Nu-13 (fetched 2026-09-27).
- Dustloop, BlazBlue: Central Fiction, Nu-13: https://www.dustloop.com/w/BBCF/Nu-13 (fetched 2026-09-27; later version,
  colour only).
- SmashWiki, Reflection: https://www.ssbwiki.com/Reflection (fetched 2026-09-27): the reflector-break rule, Fox and Falco's
  1.5× reflect damage, powershield's 0.5×, and the list of other reflectors.
- **Not verified this session (web search was exhausted):**
  - whether a Melee tier list newer than the research's 2021 PGstats list (#13) exists;
  - Melee's ledge-invincibility frame count;
  - Game & Watch's Oil Panic and Link's shield behaviour;
  - CT Nu's Distortion Drive and gravity-move details;
  - the exact frame data I cite from memory for Marth, and shield-release timing.

  These are marked [M] above.
