# GENO — design draft v0 (for review)

A wholesale-new Melee fighter: Geno, the star spirit in a wooden doll (Super Mario RPG, 1996). This draft turns the research
(`research/`: fighting-game design, platform-fighter design, the source brief, the cast's measured attributes) and Michael's
direction into a kit to prototype and playtest. Everything here is a hypothesis; the numbers are starting points for the
labs and the human-test rounds.

## 1. The headline

**A pure zoner who controls the screen from every angle, fragile when caught and committal offstage.**

- **Direction (Michael):** a true zoner, which Smash has never quite had, in the space of BlazBlue's Nu-13 (Calamity
  Trigger): screen control that feels overwhelming to face, arguably overpowered, but *fun* on both sides.
- **The Melee problem (research):** a literal SMRPG port becomes a projectile camper, the archetype that goes degenerate in
  Melee (Project M 3.02 had to tone every projectile character down). Melee's defenders jump, wavedash, dash-dance,
  powershield (reflecting a projectile with a perfectly timed shield) and, as Fox and Falco, reflect on frame 1.
- **The resolution:** zoning by **placement and angles, not raw projectile strength.**
  - Each of Geno's threats covers a different lane: ground, straight line, falling from above, an arcing path.
  - Individually, each is slow to set up, readable and answerable.
  - Together, they carve the screen into safe and unsafe space, like Nu's swords.
  - The weakness is real: when someone gets in, or when he's offstage, Geno is in trouble.

**In "a word or two" (the research checklist): "star artillery."** The weakness a top player would name first: "light, floaty,
bad up close, and you can edgeguard him."

## 2. Pillars

1. **Every angle, one of each.** A straight lane (the Beam), a curving path (the Whirl) and a drop from above (the Blast).
   Threats can layer, which is the Nu fantasy, but only one of each type exists at a time, and each costs him a
   commitment to set (Sakurai: "One Gordo on screen at a time").
2. **Placement, then payoff.** Threats are *set* (a charged beam, a star marker, a hovering disc) and then *cashed* (a
   mistimed approach runs into them). The fun for Geno is building a web; the fun for the opponent is reading and cutting it.
3. **The doll is the identity.** Fists fly off, forearms are gun barrels, the body folds into a cannon, the star can leave
   the doll. Silhouettes and animations sell this; a generic arm-cannon reskin is the failure mode (source brief).
4. **Timing is flavour, not a balance lever.** SMRPG's timed hits live on: a press at the right moment gives a chime, a
   flash and a small bonus. The kit is balanced as if every press is perfect (research P8). The famous Whirl 9999 is at most
   an impractical easter egg or trailer-only.

## 3. Physics (against the measured cast)

Cast values are from `research/cast_attributes.csv` (the disc, all 26 characters).

| Attribute | Geno target | Cast min / median / max | Why |
|---|---|---|---|
| Weight | **82** | 55 / 90 / 117 | Light (SMRPG: high attack, low defence). Between Falco (80) and Mewtwo (85). |
| Fall speed | **1.8** (fast fall 2.4) | 1.3 / 1.9 / 3.1 | Just under median: not shine or chaingrab food like the spacies, not a Mewtwo balloon. Near Mario (1.7) and Marth (2.2). |
| Gravity | **0.085** | 0.064 / 0.0975 / 0.23 | Slightly floaty arcs (Marth's value) for aerial retreat. |
| Jumpsquat | **4** | 3 / 4 / 8 | Median. Not a movement monster. |
| Air speed | **1.0** | 0.68 / 0.9 / 1.35 | Above median: a retreating aerial zoner has to drift away well. Below Peach (1.1) and Mewtwo (1.2). |
| Dash / run | **1.55 / 1.6** | 1.0 / 1.45 / 2.0 and 1.1 / 1.5 / 2.3 | Slightly above median: mobile enough to reposition, not to chase. |
| Walk | **0.95** | 0.65 / 1.1 / 1.6 | Below median: he stands and aims rather than stalks. |
| Traction | **0.065** | 0.025 / 0.075 / 0.1 | Slightly slippery: a mid-long wavedash for repositioning. |
| Jumps | **2** | 2 / 2 / 6 | |
| Shield size | **11.9** | 6 / 11.9 / 31.2 | Median. |

**Checks (research §4.7):** stay out of the corners: floaty and heavy lives forever (Samus), light and floaty is frail
(Mewtwo), light and fast-falling is combo food (Fox). The research band is weight 80-90 and fall speed 1.8-2.2; these sit at
its light, floaty edge, because a zoner who gets caught should be hurt but not zero-to-deathed every time. Tune kill
percents against him to sit near Falco's and Marth's in the labs.

## 4. Systems

### 4a. Star Pieces (the resource) — proposal, needs Michael's call

SMRPG's plot is collecting the seven Star Pieces. Geno builds them in-match and spends them on **Geno Flash**, which Melee
has no Final Smash slot for (every fan design needs it somewhere).

- **Gain:** a perfectly timed hit, or a projectile that connects, earns a Star Piece (cap 7). They show as small stars
  orbiting him: readable across the screen (research P7). Being KO'd loses them all.
- **Spend:** at 7, down-B becomes Geno Flash (4c), then the stars reset.
- **Why:** it gives the zoner a *win condition* beyond chip damage, and gives the opponent a *timer* to play around: get in
  before seven, or respect the cannon. It also keeps Geno Flash out of neutral until it's earned.
- **Risks:** Melee has no meter anywhere, so this is a new rule players must learn, and it can snowball. Alternative: no
  resource; Geno Flash is a fully charged, timed down-B with a long, visible transformation.

### 4b. Timed hits

- Press A (or B for specials) within a short window at contact: a chime, a flash of rainbow stars, +10-15% damage or a
  property change (per move), and a Star Piece if 4a is in.
- Balanced as if always hit. No move is only safe or only kills *because* of the timed version.

## 5. Specials

| Slot | Move | Role | Shape (starting point) | Counterplay |
|---|---|---|---|---|
| Neutral B | **Geno Beam** | The straight lane; the long-range threat | Hold to charge through three visible stars (about 20 frames each). Release on a star for the timed bonus. Holding past the third star, the beam fires by itself after a short grace window. **No stored charge** (my call, not the research's: the research warns a stored charge "keeps his neutral threatening all game" and must be priced like Samus's; SMRPG's own verb is release-on-the-star, which also keeps him from reading as Samus). Full-charge beam: fast, long, moderate knockback. A tap fires **Finger Shot**, his one fast projectile, on Falco's template (research §4.2): real hitstun, a slow fire rate, ground ending lag. Air version: landing lag if he lands while firing. | Jump over it (it's a line); powershield reflects it; Fox and Falco reflect it (whether a full beam breaks their reflector is a lab question); the visible charge is a tell to approach on. |
| Side B | **Geno Whirl** | The curving path; space in front of him | A spinning gold disc thrown forward. Its path curves toward the stick (up or down arc) and travels a fixed distance, then **hovers briefly** as a buzzsaw zone (the 2023 remake made the Whirl a buzzsaw) before fading. **One on screen.** Pressing B while it hovers recalls it through him (a second hit on the way back). A timed press at contact crits for extra knockback, not damage. | Shield it; it's slow at the end of its path; a hit of 6% or more breaks it (the research's Missile lever); approach while it's out, since Geno's side B is on cooldown. |
| Down B | **Geno Blast** (Geno Flash at 7 Star Pieces) | The vertical drop; area denial and edgeguarding | Mark a spot at a distance picked by the stick (a visible star on the ground or in the air). About 30 frames later, beams rain onto the mark. Hold longer to widen the pattern. **One set of marks at a time.** Geno is committed during the call. | The mark is a tell with plenty of time to leave; he's vulnerable while calling it; it can't cover the ledge and the stage at once. |
| Down B (7 Stars) | **Geno Flash** | The earned super | He folds into the blue-and-gold cannon on its carriage (SMRPG's animation), is armoured but immobile, and fires a sun that grows across the stage. A long, loud transformation: the opponent sees it coming and can run or shield. High knockback; Star Pieces reset. | Reaction to the transformation; get behind or above the cannon; shield. |
| Up B | **Star Road** (cannon launch) | Recovery; the committal part of him | Folds into the cannon, aims across 8 or 16 directions for a few frames, fires himself as a star. **Moderate distance, the angle is the mixup, no hitbox during the flight,** and it ends in helpless fall (research §4.8: never hitbox protection, invincibility and distance together). Legacy XP's version has no helpless fall; ours does. | Predictable once aimed; edgehog, or wait at the landing point; stars on the flight path are a tell. |

## 6. Normals (starting shapes)

Close range is deliberately his weak range. Fast *get-off-me* tools exist but trade reward for speed. There's no frame-1
move, and no move combines fast startup, long active frames, low lag, long reach and high reward (research P6).

| Move | Idea | Target |
|---|---|---|
| Jab | Finger taps, into a rapid **Finger Shot** barrage (bullets leave the fingers) | Fast (frame 3), low reward: his get-off-me |
| Forward tilt | **Hand Gun**: a short forward wrist-gun blast | A spacing poke; safe only at max range |
| Up tilt | A ducking spin of the cape upward | Anti-air, slow |
| Down tilt | A low sweep of the cape | Trip or poke |
| Dash attack | A shoulder dive, doll-stiff | Committal |
| Forward smash | **Double Punch**: both fists launch as rockets and return | Long-range disjoint, punishable on whiff |
| Up smash | **Star Gun**: stars fired straight up from both wrists | His out-of-shield kill move; mid startup (frame 9-10), not a shine-speed escape |
| Down smash | **Hand Cannon** from both elbows, left and right | Covers rolls |
| Neutral air | A spinning doll: limbs out, a star at the core | Get-off-me in the air; frame 4-5, low reward |
| Forward air | A **Hand Gun** muzzle blast from the wrist: a long disjointed burst, not a travelling projectile | The retreating aerial wall (fired while drifting back), like Marth's forward air in role. Keeps the on-screen projectile count at three types. |
| Back air | An elbow Hand Cannon fired backward, with recoil forward | A kill move when turned around; recoil gives retreat or advance |
| Up air | Star Gun fired upward | Juggle; weaker than up smash |
| Down air | A falling stomp with his boots | A spike, slow; for edgeguards |
| Grab / throws | Short grab, since his hands are fists. Throws: a spinning fling (back), a star-burst pop (up), a flat toss (forward), a ground slam (down) | **Every throw is weight-dependent and grows with percent** (research: Akaneia's Wolf fix). No throw chains on anyone. His throws send the opponent *away* into his zone rather than into a combo. |

### Left out, deliberately

- **Geno Boost** (SMRPG's attack buff, with a timed press for defence). Four special slots are full, and the research warns
  that a buff on a zoner must not stack with charges into a guaranteed kill (§4.5, the Shulk rule). It could live on the
  taunt: a long, punishable animation that he spends the space he's made on. See question 5.
- **Stella 023** (the remake's train-part laser) and the 9999 Whirl: easter eggs or trailer nods only.

## 7. How the kit fits together (the web)

- **Geno Beam** holds the straight lane and forces the opponent to jump or shield.
- **Jumping** meets Geno Blast marks placed above, or the curving Whirl.
- **Shielding** lets the Blast land on the shield, or lets Geno reposition and recharge.
- **Getting in** is the answer, and Geno's close range is weak, so he spends his neutral keeping them out. He uses retreating
  forward airs, the Whirl's hover zone and Double Punch's range.
- **Once they're offstage,** Geno Blast and the Whirl edgeguard from safety, which is his real reward, and Star Pieces build
  toward Geno Flash.
- **Once he's offstage,** his recovery is long but committal and hitbox-less: the opponent's reward.

## 8. Loop and degeneracy audit (to prove in the labs)

- **Whirl hover and recall:** can they combine with Blast into an inescapable pattern? Rule: no combination holds a
  shielding opponent past shield break without a gap, and every hit can be SDI'd out.
- **Beam on Fox and Falco:** the full beam and their frame-1 reflectors. Test both outcomes of the reflector-break rule.
- **Star Pieces snowball:** gain rate caps, and loss on KO.
- **Ledge:** no projectile covers the ledge while he regrabs. Blast marks can't be placed on the ledge he holds.
- **Throws:** every throw against Fox, Falco and Falcon at 0-60%.
- **Camping on Final Destination:** Falcon, Marth and Jigglypuff must have a real, not theoretical, path in.

## 9. Test plan

1. **Engine prototype:** the blocky rig with Geno's final proportions (hurtboxes match the finished silhouette), blockout
   animations at exact timing, real hitboxes and specials code.
2. **Automated labs (the director):**
   - frame data and shield safety at best and worst spacing;
   - combos Geno gets on each weight class, and combos taken;
   - recovery distance and angles;
   - edgeguard coverage;
   - projectile interactions (reflectors, powershields, clanks, Ness's absorb).
3. **Human test rounds:** Michael and recruited players on Dolphin (possibly netplay). Record which strategies feel
   "annoying, overcentralizing, or overly safe" (Rivals II), not just who wins.
4. **Overshoot, then pull back:** start strong, and aim for the top of the second tier at release (Sirlin, HD Remix).

## 10. Open questions for Michael

1. **Star Pieces resource (4a), or no resource?** It's the biggest structural call.
2. **Is "a pure zoner with a bad close range" the fantasy,** or should he have one strong close-range option to be less
   one-dimensional? Nu-13 had almost none.
3. **Up B with no hitbox** (maximum edgeguard reward for opponents), or a small hitbox at the end?
4. **Timed hits:** on every move (Legacy XP), or only specials and a few signature normals (clearer, and different from
   Legacy XP)?
5. **Geno Boost on the taunt,** or left out?
