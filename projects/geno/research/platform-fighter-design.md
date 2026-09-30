# Platform-fighter design and Melee's competitive reality (for a Melee Geno)

Research brief for adding Geno (Super Mario RPG) to Melee through the decompilation, aiming for a fighter near the top tiers,
not overpowered, coherent, and with counterplay. This report covers platform-fighter design and Melee's competitive reality.
General fighting-game design is in `fg-design-principles.md`, and measured Melee attributes are in `cast_attributes.csv`.

**Conventions.** **[E]** marks documented evidence (a linked quote or fact). **[S]** marks my synthesis. **[?]** marks a claim I
could not verify, or a number to check against the decomp. Quotes are verbatim. Where Sakurai speaks only in Japanese, I
paraphrase the auto-generated captions and label it "my paraphrase".

**Coverage limits.** I found no primary design talks by the Slap City, Brawlhalla or Nickelodeon All-Star Brawl designers, and
no Dan Fornace talk on Rivals design, so for those games I used the studios' patch notes and dev posts on Steam. The web-search
budget ran out partway through, so later sources were fetched directly (SmashWiki raw pages, the archived Project M dev blog,
Steam news).

---

## 1. Principles, with evidence

### P1. Sharpen strengths and weaknesses; don't converge the cast

- **[E]** Sakurai, *Amplify Both Strengths and Weaknesses* (YouTube, Aug 2024, [video](https://www.youtube.com/watch?v=fc-hOvTBTCc)):
  "The more similar you make different fighters' abilities, the more they'll start to feel like the same character. That's
  simply not fun." ([EventHubs](https://www.eventhubs.com/news/2024/aug/31/masahiro-sakurai-balance-solution-traits/)). "Variety
  among things like fighters is the very lifeblood of the game." ([Nintendo Life](https://www.nintendolife.com/news/2024/08/video-keep-your-peaks-and-valleys-sakurai-explains-fighter-balance-in-smash-bros)).
- **[E, my paraphrase]** In the same video Sakurai lists an attack's separate properties: power, startup, active duration,
  follow-through (end lag), launch, shield damage and shield stun. If a move must be adjusted, keep its high power as its
  identity and pay for it with longer end lag or a smaller hitbox. He calls shaving peaks and filling valleys a path to ruin.
- **[E]** Sakurai on uniqueness ([EventHubs, Apr 2024](https://www.eventhubs.com/news/2024/apr/10/smash-creator-unique-characters/)): "characters should be made unique enough
  that you can describe their distinctive traits in just a word or two." My paraphrase of the same video ([YouTube](https://www.youtube.com/watch?v=zwiS1L6QVY0)):
  every Ultimate DLC fighter got a bespoke mechanic needing its own code, and the method is to make a character bumpy first,
  then patch what becomes a problem.
- **[E]** Aether Studios, on Orcane in Rivals of Aether II ([Patch 1.3.3, Aug 2025](https://store.steampowered.com/news/app/2217000/view/1808061939507523)):
  with "fast movement, quick normals, strong zoning tools, and top tier recovery," Orcane "starts to lose his identity and falls
  back to basic fundamentals instead, which isn't what we envisioned."
- **[S]** A character with no weakness is overpowered, and it is also shapeless. The fix is to cut a whole category of strength,
  not to trim every number by 5%.

### P2. Balance serves fun and individuality, not symmetry

- **[E]** Sakurai, Famitsu vol. 480 ([Source Gaming translation](https://sourcegaming.info/2015/06/11/the-act-of-balancing-sakurai-famitsu-column-vol-480/)):
  "There's no point in making the game more balanced if it decreases the fun factor. To give an extreme example, I could make
  all the characters perform similarly to Mario and achieve perfect balance. However, that probably wouldn't be very fun at
  all."
- **[E]** His tuning target is the middle: "I'm aiming for intermediately-skilled players to be able to properly enjoy the game"
  (same column). But "Melee is the sharpest game in the series", and "I doubt we'll ever see one that's as geared toward
  hardcore gamers as Melee was" (1UP translation, in [Famitsu vol. 360, Source Gaming](https://sourcegaming.info/2015/06/29/lookingbackonmelee/)).
- **[S]** Sakurai's method (sharp identity, playtesting, final human judgment) transfers. His target (intermediate players, party
  play) does not, because competitive Melee is the high-skill end he moved away from.

### P3. Risk and reward are the core; reward should scale with risk

- **[E]** Sakurai, *Risk and Reward* ([YouTube](https://www.youtube.com/watch?v=FXqEykD5Ub4)): "Push and pull is the very core of
  game essence" ([Nintendo Life](https://www.nintendolife.com/news/2022/08/video-masahiro-sakurai-breaks-down-risk-and-reward-in-games)).
  My paraphrase: a Space Invaders cannon that could fire in any direction would look flashy but be poor design, unless shots
  were limited (to diagonals, or by count), and risk and reward should sit close together at matched sizes.
- **[E]** Sakurai's Smash 4 internal note for King Dedede's new projectile: "With side + B, throw a Gordo. One Gordo on screen at
  a time." ([Source Gaming, internal notes](https://sourcegaming.info/2017/06/23/internalnotes/)).
- **[S]** For a gunner this is the central rule. The design question is not how strong a shot is but how much it costs to fire,
  and how many can be on screen.

### P4. Counterplay and interaction beat raw power

- **[E]** Project M Dev Team (PMDT), on tethers ([3.5 Blogpost #2, Aug 2014](https://web.archive.org/web/20140808045127/http://projectmgame.com/en/news/dev-blogpost-2-tethers)):
  "When risk vs. reward assessments favor non-interaction, we feel the need to step in."
- **[E]** Aether Studios ([Rivals II, Dec 2024](https://store.steampowered.com/news/app/2217000/view/1784506359184286)): "We want to make
  sure projectiles have enough counterplay, since they can be frustrating to play against otherwise, so we're making parry
  faster specifically when used against projectiles." Also: "It's too early to make balance changes based on any tier lists, so
  instead we're targeting specific annoying, overcentralizing, or overly safe strategies."
- **[E]** Brawlhalla's Blue Mammoth weakened a bow attack "to create wider avenues for counterplay against this attack"
  ([Sep 2021](https://store.steampowered.com/news/app/291550/view/4020014099084713623)).
- **[E]** Celia Wagar ([CritPoints](https://critpoints.net/2017/07/07/what-makes-a-character-annoying/)): "The best way to make
  something less annoying to deal with is to provide multiple ways to deal with it, even if those multiple ways are just
  differences in spacing and timing."

### P5. Recoveries should test skill, and the edgeguarder should usually be favored

- **[E]** PMDT mission statement ([About page, 2013](https://web.archive.org/web/20130630200046/http://projectmgame.com:80/en/about)),
  modeled on Melee: "Offstage edgeguarding is risky but rewarding, while on-stage edgeguarding is safer but less rewarding.
  Recoveries generally require great skill to use, with the advantage usually being with the edgeguarding player, with some
  exceptions."
- **[E]** PMDT, *Recoveries* ([3.5 Blogpost #1, Aug 2014](https://web.archive.org/web/20140804053213/http://projectmgame.com/en/news/dev-blogpost-1-recoveries)):
  "The most common complaint leveled against PM is undoubtedly that 'the recoveries are too good', and we are inclined to
  agree." Their factors for judging a recovery: "recovery startup, ending/landing lag, linearity, timing
  flexibility, horizontal and vertical distance, hitbox protection, armor, sweet spot safety/ledgegrab box size & disjoint,
  character weight, fallspeed, air jumps, air drift speed." The goal: "the recovering victim should have just enough options
  that they feel a certain pressure to combine their limited recovery moves in ways that can surprise the edgeguarder."
- **[E]** Aether Studios had the same complaint in Rivals II ([Dec 2024](https://store.steampowered.com/news/app/2217000/view/1784506359184286)):
  "Recoveries being too strong, making successful edgeguards too rare."

### P6. Trim excess tools against global design goals

- **[E]** PMDT, *Trimming the Fat* ([3.5 Blogpost #7, Oct 2014](https://web.archive.org/web/20141020154955/http://projectmgame.com:80/en/news/dev-blogpost-7-trimming-the-fat)):
  "we believe our cast to possess tools that are a little too excessive in terms of flexibility, recovery prowess, punishment
  and more." Their review criteria, verbatim: static knockback that should scale with percent; "Balancing cooldowns with
  power/start-up/duration/utility"; "Tools that mitigate positional advantage (e.g. circumventing juggles, edge guards)";
  "Tools that provide excessive burst movement without appropriate risk"; "Moves that hit at unintuitive angles"; "Moves with
  SDI/hit-lag multipliers on them that circumvent the strength of Directional Influence"; "Recovery potency."
- **[E]** A warning from PM's history: in 3.02 "all the characters with projectiles, now had this amazing ability to zone other
  characters out"; 3.5 "toned all of this down" (Wagar, [CritPoints](https://critpoints.net/2016/10/22/project-m-intro-overview/),
  secondary but consistent with the PMDT posts).

### P7. In a Melee mod, the newcomer must fit the unchanged cast

- **[E]** Smash Remix leaves "the original 12 characters and general mechanics unchanged"; it "was envisioned to have tournaments
  where the new characters could be pitted against the old ones, with all the newcomers being viable against the originals."
  Its intentionally overpowered bosses are kept separate as "Bonus Characters" ([SmashWiki](https://www.ssbwiki.com/Smash_Remix)).
- **[E]** The Akaneia Build keeps all 26 Melee characters "unchanged from how they played in the original game"
  ([SmashWiki](https://www.ssbwiki.com/The_Akaneia_Build)).
- **[E]** Project+ says its new fighter Knuckles "has been polished and refined to fit in nicely with the existing cast" and was
  "Originally designed as a stronger version of Sonic" ([projectplusgame.com/knuckles](https://projectplusgame.com/knuckles)).
- **[S]** This is our constraint too. Players expect vanilla Melee around Geno, so we can't patch Fox, the ledge or shields to
  make room for him. Global problems (ledge stalling, chaingrabs, projectile camping) have to be solved inside his kit.

### P8. Adapting a licensed character: keep the soul, change the verbs

- **[E]** Rivals of Aether's Shovel Knight ([dev post, Aug 2018](https://store.steampowered.com/news/app/383980/view/2444779293759046757)).
  Trevor Youngblood: "A lot of Shovel Knight's relics are projectiles, which didn't really fit our vision of him, since we didn't
  want another projectile-focused zoner... Some relics, however, would be extremely busted if we kept their original
  functionality, like the War Horn or the Phase Locket, so we took some liberties." Dan Fornace: the source character was the
  "balanced, traditional character" of his own game, so "we had to come up with ideas that gave him a unique style while also
  pulling from Shovel Knight for inspiration." The team tried two designs before the shop mechanic.
- **[S]** Geno has the same problem, only worse. His SMRPG kit is almost all ranged (Geno Beam, Geno Whirl, Geno Blast, Geno
  Flash, arm-cannon shots) plus a buff (Geno Boost). Ported literally, he becomes a pure zoner, the archetype most likely to go
  degenerate in Melee (section 3). Iterate on the concept, as the Rivals team did, before tuning numbers.

### P9. How mod and indie teams test new fighters

- **[E]** Sakurai: "the most important resource for balancing is the report we receive from the playtesting team", plus
  "results from online battles" (Famitsu vol. 480).
- **[E]** PMDT: "We've done a lot of internal testing and asked high level Melee and Project M players alike what they think"
  ([Blogpost #6](https://web.archive.org/web/20141001152631/http://projectmgame.com/en/news/dev-blogpost-6-ledge-invincibility)).
  Also: "we are learning from our past mistakes of overbuffing/nerfing characters" and "the community wants to let the metagame
  develop unperturbed as much as possible" (Blogpost #1).
- **[E]** Smash Remix credits 18 named playtesters "and over 90 others" ([SmashWiki](https://www.ssbwiki.com/Smash_Remix)). Rivals
  II ran monthly closed betas before launch, with balance feedback on a Nolt board ([Jun 2024](https://store.steampowered.com/news/app/2217000/view/5842939267318007945)).
- **[E]** Akaneia's patch notes use Melee's own tuning language: "Breaks Crouch Cancel earlier, but is less reliable against
  floatier fighters"; "safer on hit, but still weak to ASDI Down"; "All throws are now weight-dependent"
  ([releases](https://github.com/akaneia/akaneia-build/releases)).

---

## 2. What makes a Melee character strong, trait by trait

**[E]** Context: Melee tier list #13, an average of 64 top players' lists, published March 29, 2021 by PGstats
([SmashWiki](https://www.ssbwiki.com/Tier_list)). **S:** Fox, Marth, Jigglypuff, Falco. **A:** Sheik, Captain Falcon, Peach.
**B+:** Ice Climbers, Pikachu, Yoshi, Samus. Young Link, Link and Mewtwo rank 17th, 18th and 20th of 26.

Unless noted, the quotes in this section are from the SmashWiki Melee character pages ([Fox](https://www.ssbwiki.com/Fox_(SSBM)),
[Falco](https://www.ssbwiki.com/Falco_(SSBM)), [Marth](https://www.ssbwiki.com/Marth_(SSBM)), [Sheik](https://www.ssbwiki.com/Sheik_(SSBM)),
[Jigglypuff](https://www.ssbwiki.com/Jigglypuff_(SSBM)), [Peach](https://www.ssbwiki.com/Peach_(SSBM)), [Captain Falcon](https://www.ssbwiki.com/Captain_Falcon_(SSBM)),
[Ice Climbers](https://www.ssbwiki.com/Ice_Climbers_(SSBM)), [Samus](https://www.ssbwiki.com/Samus_(SSBM))). SmashWiki is
community-written but heavily sourced.

1. **Mobility and movement options.** **[E]** Fox has "the second fastest dashing speed" and a jump of "only 3 frames before he
   leaves the ground". Falcon has "the single fastest dash speed". Jigglypuff has "the best air mobility in the game". Peach's
   float gives "completely lagless aerials." **[S]** Every S and A tier character has elite movement of some kind. It is the
   price of entry.
2. **Instant and frame-1 options.** **[E]** Fox's Reflector "comes out on frame 1". Jigglypuff's Rest has "no starting lag
   (hitting on the very first frame)". Samus's Screw Attack is "invincible for the first couple frames," which makes it a strong
   out-of-shield option. **[S]** Frame-1 tools let their owners escape pressure, start combos and win trades. They are the most
   dangerous thing to hand a newcomer.
3. **Range and disjoint.** **[E]** Marth's "primary strength is his great range... very large disjointed hitboxes", plus "the
   longest of the non-grapple grabs". Jigglypuff's "disjointed back aerial can stuff out most characters' approaches."
4. **Projectile quality.** See section 2a.
5. **Conversion (punish).** **[E]** Fox's placing rests on "his unparalleled comboing and damaging ability." Sheik's down throw
   "boasts a chain grab on many characters". Marth's up throw "can chain throw most fast fallers at low-to-mid percentages."
   Falcon's grab game is "among the most flexible and devastating in Melee" despite "poor grab range."
6. **Kill power and consistency.** **[E]** Fox's up smash and up air are "among the most powerful in the game". Against that,
   Marth's "Marthritis" ("Many of his quick, safe moves greatly lack in KO power") and Young Link's "inability to easily and
   efficiently land and KO with his finishers."
7. **Edgeguarding.** **[E]** Sheik's edgeguarding is "among the best in the game". Fox's shine is "of very low risk to use off the
   edge." Edgehogging works because "only one character may generally hold onto a ledge at a time" ([SmashWiki](https://www.ssbwiki.com/Edgehogging)).
8. **Recovery, and the trade-off it creates.** **[E]** Fox's recovery is long, but if the opponent reads it, "Fox will likely not be
   able to recover again". Falco's recovery is "among the worst in the game"; Falcon's is "mediocre." Peach's is "one of the best
   recoveries in the game"; Samus's is "among the longest and most flexible". **[S]** The fast-falling top tiers pay for their
   offense with exploitable recoveries. The floaty top tiers pay with vertical frailty and slow ground games.
9. **Weight and fall speed (how easily a character is comboed).** **[E]** Average NTSC weight is 90. Fox is 75, Falco 80, Marth
   87, Sheik and Peach 90, Falcon 104, Samus 110, Jigglypuff 60 ([Weight](https://www.ssbwiki.com/Weight)). Fall speeds: Falco
   3.1, Falcon 2.9, Fox 2.8, Marth 2.2, Sheik 2.13, Peach and Mewtwo 1.5, Samus 1.4, Jigglypuff 1.3 ([Falling speed](https://www.ssbwiki.com/Falling_speed);
   matches `cast_attributes.csv`). Fox, a light fast-faller, can be comboed or chaingrabbed by "nearly every character", making
   him "somewhat of a glass cannon." Jigglypuff "is among the hardest characters to combo" and "tends to sustain twice as much
   damage" per set. Mewtwo's "biggest flaw is its frailty".
10. **Shield pressure and safety.** **[E]** Falco's pillar combo "is notorious for wearing shields down quickly". Peach's down smash
    can "easily shield poke". L-canceling halves aerial landing lag, but "special moves that have landing lag cannot" be
    L-canceled ([SmashWiki](https://www.ssbwiki.com/L-canceling)).

**[S] The pattern.** Each top tier pairs two or three elite traits with one or two real liabilities:

- Fox: everything, paid for with combo food and an exploitable recovery.
- Marth: range, grab and mobility, paid for with inconsistent kills.
- Jigglypuff: air control and combo escape, paid for with weight and ground speed.
- Peach: air game and recovery, paid for with ground mobility.
- Sheik: punish and edgeguard, paid for with an average neutral.

This is Sakurai's peaks and valleys working as intended, in the one Smash built for experts.

### 2a. Projectiles in Melee: why some dominate and others don't

- **Falco's Blaster (dominant).** **[E]** Each shot "stuns the opponent" with set knockback, and a short hop skips the ending lag.
  It builds damage, aids approaches, and forces Falcon and Ganondorf to recover again and again ([Blaster (Falco)](https://www.ssbwiki.com/Blaster_(Falco))).
  Short-hop lasering up close "almost guarantees free grabs, smashes, or ways to start shine combos." Falco "has been a perpetual top tier character in both
  Melee and Brawl, due largely to his ability to outcamp nearly every other character" ([Camping](https://www.ssbwiki.com/Camping)).
- **Fox's Blaster (strong, differently).** **[E]** It has "no knockback or hitstun and does 1%-3% damage per shot", but it is fast
  and can be spammed. It is used "to camp and bring up damage", and "unstaling the rest of Fox's moves" ([Blaster (Fox)](https://www.ssbwiki.com/Blaster_(Fox))).
- **Sheik's Needle Storm (strong).** **[E]** Needles are "quick to charge, can travel quickly when thrown, and can cut through or
  stop most other projectiles". They have "high hitstun and low knockback" for intercepting linear recoveries, and "no landing
  lag after being used in midair", so hitstun or shieldstun leads straight into a grab. The charge is stored.
- **Peach's turnips (strong, item-based).** **[E]** Turnips "bounce off of opponents shields... so Peach can regrab the turnips"
  ([Vegetable](https://www.ssbwiki.com/Vegetable)).
- **Samus (upper-mid tier).** **[E]** A full Charge Shot does 25% with 13-frame startup ([Charge Shot](https://www.ssbwiki.com/Charge_Shot)).
  "If the missile is hit with a move that does at least 4%, the missile will break" ([Missile](https://www.ssbwiki.com/Missile)).
  Being floaty, she "can have particular difficulty in comboing fast-fallers."
- **Link and Young Link (lower tiers).** **[E]** Link's bow is "decidedly situational due to its low speed, knockback, and few
  follow-ups", and Link is "a particularly easy target for chain throwing and combos." Young Link's projectiles are better, but
  he struggles to kill.
- **Mewtwo's Shadow Ball (a strong move on a weak character).** **[E]** A full charge "can KO reliably at roughly ~100%". Its
  "jagged path" is hard to dodge, it takes "about half" a shield's health, and it recoils in the air ([Shadow Ball](https://www.ssbwiki.com/Shadow_Ball)).
  Mewtwo still sits near the bottom because of its frailty.
- **Universal counters.** **[E]** Powershielding a projectile ("2 frames for projectiles") reflects it, and the shielding player
  suffers "no shieldstun" ([Perfect shield](https://www.ssbwiki.com/Perfect_shield)). Reflectors "help prevent projectile camping
  and spamming". In Melee, "if a projectile is too strong for a reflector, the reflector breaks as if it was a shield and stuns
  the user" ([Reflection](https://www.ssbwiki.com/Reflection)).

**[S] What separates the dominant projectiles** from the weak ones is not damage. It is four things together:

- Low commitment: fired during movement, with landing lag removed by auto-cancel or no landing lag at all.
- Speed.
- A usable on-hit state: hitstun or shieldstun that leads straight into a grab, a shine or a combo.
- A body that can capitalize. Falco and Sheik can follow up; Samus and Mewtwo often can't.

Slow, breakable or low-hitstun projectiles on characters with poor follow-ups don't reach top tier.

---

## 3. Pitfalls in Melee's engine specifically

1. **Inescapable loops.** **[E]** Wobbling is an Ice Climbers infinite in which "Opponents cannot break out of the leader's grab".
   Get On My Level 2019 "was the first major to officially announce a wobbling ban", and The Big House 9, Pound 2020 and others
   followed ([Wobbling](https://www.ssbwiki.com/Wobbling)); it is now at the "discretion of tournament organizer"
   ([ruleset](https://www.ssbwiki.com/Tournament_rulesets_(SSBM))). Wagar: "Glitches weren't banned because they
   were undesired... they were banned on the basis of having no counterplay" ([CritPoints](https://critpoints.net/2017/11/25/critique-of-super-smash-brothers-melee-review-and-analysis/)).
   **[S]** Any Geno loop (a multi-hit disc, a beam-to-grab regrab) must have an escape through DI, SDI, a tech option or rising
   knockback, and should break with percent.
2. **Chaingrabs.** **[E]** Chaingrabs mostly work against "fastfallers, heavyweights, and large characters". Most become escapable
   as throw knockback grows, and the infinite ones often rely on set knockback ([Chain grab](https://www.ssbwiki.com/Chain_grab)). Sakurai's Smash 4 notes: "By repeating dash > grab > down
   throw, a pseudo-chain grab is possible, this should be removed." Akaneia made Wolf's throws weight-dependent. **[S]** Give Geno
   throws with knockback that grows with percent. Test every throw against Fox, Falco and Falcon at 0–60%.
3. **Ledge invincibility and planking.** **[E]** Melee has no engine limit on ledge regrabs. Tournaments use a ledge-grab limit,
   which SmashWiki summarizes as more than 40 grabs in a timeout, or more than 50 otherwise, losing the game ([ruleset](https://www.ssbwiki.com/Tournament_rulesets_(SSBM))).
   Project M removed ledge invincibility after five regrabs because "Fox stays entirely invincible from attack while
   simultaneously protecting the ledge... with hitboxes of his own" ([Blogpost #6](https://web.archive.org/web/20141001152631/http://projectmgame.com/en/news/dev-blogpost-6-ledge-invincibility)).
   PM's changelist gives its actionable ledge invincibility as 29 frames ([3.5 changelist](https://web.archive.org/web/20141119214707/http://projectmgame.com:80/en/news/project-m-3-5-changelist));
   **[?]** Melee's exact value needs checking in the decomp. **[S]** Geno must not have a ledge-drop projectile or recovery hitbox
   that safely covers the ledge while he regrabs.
4. **Stalling moves.** **[E]** Repeated Rising Pound, repeated Peach Bomber on a wall, and the Luigi Ladder are banned when used to
   stall ([ruleset](https://www.ssbwiki.com/Tournament_rulesets_(SSBM))). **[S]** Any Geno special that restores height or refreshes a
   jump (a Geno Boost hover, a disc ride) must lose height or be once per airtime.
5. **Recoveries that are too strong or too safe.** **[E]** PM tethers could "tether drop and retether up to 3 times", making
   punishes "dangerous and often not worth the risk" (Blogpost #2). **[S]** Of invincible or armored startup, long distance and
   hitbox cover, pick at most two.
6. **Projectile camping.** **[E]** See PM 3.02 → 3.5 (P6) and Falco (2a). Concrete PM 3.5 levers: Link's boomerang "cooldown for
   not being caught increased by 20 frames" and weaker return hits; Pit's grounded arrow "+8 frames endlag", with damage that
   "decays at a rate of 1 per every 5 frames" ([3.5 changelist](https://web.archive.org/web/20141119214707/http://projectmgame.com:80/en/news/project-m-3-5-changelist)).
7. **Anti-DI mechanics and odd angles.** **[E]** PM flagged SDI and hitlag multipliers that defeat DI, and unintuitive angles (P6).
   NASB's developers added hitstun scaling to a move they called "slow-mo auto-combo fodder" ([Oct 2021](https://store.steampowered.com/news/app/1414850/view/4698935641771424073)).
8. **Too many tools.** **[E]** See Orcane (P1) and PM's "excessive... flexibility" (P6). **[S]** The classic gunner overload
   combines Falco's hitstun and short-hop auto-cancel, Fox's fire rate, Sheik's projectile-cutting and no landing lag, and Samus's
   stored charge, all on a body with a good recovery. Each is fine alone. Together they recreate PM 3.02.

---

## 4. Implications for Geno (beam, disc and gunner kit)

These are **[S]** throughout, grounded in the evidence above.

1. **Write the headline first (P1).** Pick one identity for Geno and one thing he is bad at. One example: "a precision marksman
   who controls lanes with a charged beam and cashes in on reads with a timing-based disc; light and easy to combo, with a
   committal recovery." The rest of the kit serves that headline.
2. **Choose one role for the fast projectile.** Two proven templates exist: Falco-style (hitstun, slower fire rate, more ending
   lag on the ground) or Fox-style (no hitstun, fast chip damage, unstales his other moves). Don't ship both properties at once.
3. **Treat the charge beam as a Samus or Mewtwo-class threat and price it that way.** A stored charge keeps his neutral
   threatening all game. Costs to consider: a long charge; lag on charge-cancel (Samus's went from 1 frame in Smash 64 to 8 in
   Melee, [Charge Shot](https://www.ssbwiki.com/Charge_Shot)); a fixed lifetime; landing lag in the air that can't be
   L-canceled. Reflectors and powershields turn a full-charge beam against him, which matters because Fox and Falco both have
   frame-1 reflectors. **[?]** Melee's rule that an overpowered projectile breaks a reflector could cut the other way. Test both.
4. **Geno Whirl should be a sweetspot with a visible timing, not a lottery.** SMRPG's timed Whirl deals huge damage. In Melee
   it should be a telegraphed, high-reward hitbox that is punishable on whiff or on shield, never random (P4: stakes are fine if
   the opponent has several answers).
5. **Geno Boost: follow Sakurai's Shulk rule.** "Each mode has a weakness, but generally it should be better to use an Art than
   not" ([internal notes](https://sourcegaming.info/2017/06/23/internalnotes/)). The buff should have a real window to punish while
   it activates, and it should not stack with stored charges into a guaranteed kill.
6. **Limit what's on screen (P3).** One disc and one charged beam at a time. Consider cooldowns (the PM boomerang lever) and
   damage that falls off with distance (the Pit arrow lever). Decide whether each projectile clanks with attacks, whether it
   breaks under a damage threshold (the Missile lever), and whether it counts as "energy" that Ness can absorb.
7. **Physics: stay out of the extreme corners.** Floaty and heavy (Samus) lives very long; light and floaty (Mewtwo) is frail;
   light and fast-falling (Fox) is combo food. Mid weight (roughly 80–90) and mid fall speed (roughly 1.8–2.2) keep Geno
   comboable without being free. **[?]** Starting guesses; tune with `cast_attributes.csv` and matchups.
8. **Recovery.** Moderate distance with a real mixup (angle, or a disc as a platform), never hitbox protection, invincibility and
   distance together. A zoner with a great recovery removes the edgeguarder's reward, which is Melee's main check on campers.
9. **Close range needs its own answer.** The top tiers punish zoners by getting in. Geno needs one honest out-of-shield option
   and one get-off-me move. It should not be a frame-1 reflector, and it doesn't need to be frame 1 at all.
10. **Matchup targets.** He must be playable against:
    - Fox and Falco: reflectors, speed and lasers.
    - Marth: disjoint, and chaingrabs on fast fallers.
    - Sheik: needles "cut through or stop most other projectiles".
    - Jigglypuff: air camping.
    - Peach: turnips, float and a long recovery.
    - Ice Climbers: grab threat, and whether wobbling is legal where he's played.

---

## 5. Kit-review checklist for Melee

**Identity**
- [ ] Can the kit be described in "a word or two"? Is there at least one weakness a top player would name first?
- [ ] Is each move's peak kept, with its cost paid in end lag, hitbox size or commitment (Sakurai)?

**Neutral and projectiles**
- [ ] Startup, ending lag, landing behavior (auto-cancel, L-cancel, or special landing lag), speed, lifetime, and on-screen
      limit for every projectile.
- [ ] Does each projectile's on-hit or on-shield state lead to a guaranteed follow-up? If so, at what range? (This is where
      Falco and Sheik get their value.)
- [ ] Clanking or transcendent? Breakable at what damage? Reflectable? Absorbable (energy)? What happens on powershield?
- [ ] Can Geno force approaches on flat stages with no risk, like PM 3.02? Test on Final Destination against Falcon, Marth and
      Jigglypuff.

**Punish and kill**
- [ ] Every throw's knockback grows with percent. No chaingrab on Fox, Falco or Falcon past low percent.
- [ ] Every multi-hit and loop can be escaped with DI or SDI. No SDI or hitlag multipliers that defeat DI.
- [ ] Kill percents against Fox (75 weight) and Samus (110) are in line with Falco and Marth, not beyond them.

**Edge, recovery and defense**
- [ ] Recovery scored against PM's recovery factors (P5).
- [ ] Edgeguarders have a reliable, rewarding answer. Can he be edgehogged? Can he be intercepted?
- [ ] No safe ledge-stall loop (hitbox cover while regrabbing), no height-restoring stall special, and no need to rely on the
      ledge-grab limit to police him.
- [ ] Out-of-shield options and the get-off-me move are fast enough to survive shine and laser pressure, but not frame 1.

**Physics**
- [ ] Weight and fall speed chosen deliberately against the 26-character table. Survival, combo vulnerability and recovery
      checked together.

**Process and metrics**
- [ ] Iterate on the concept before tuning numbers (Rivals' Shovel Knight tried two designs first).
- [ ] Test with high-level Melee players on Slippi. Record which strategies feel "annoying, overcentralizing, or overly safe"
      (Rivals II), not just win rates.
- [ ] Track results against S and A tiers, kill and death percents, ledge grabs, projectiles per minute, and timeouts.
- [ ] Write patch notes in Melee terms (crouch cancel, ASDI down, weight-dependent throws), in rare, deliberate releases (PMDT).

---

## Sources

**Sakurai (primary; translations credited)**
- Famitsu vol. 480, "The Act of Balancing" (Source Gaming translation, 2015): https://sourcegaming.info/2015/06/11/the-act-of-balancing-sakurai-famitsu-column-vol-480/
- Famitsu vol. 360, "Looking Back on Melee" (Source Gaming, with 1UP translation): https://sourcegaming.info/2015/06/29/lookingbackonmelee/
- Famitsu vol. 512, "A Fair Chance" (Source Gaming, 2016; background only): https://sourcegaming.info/2016/09/07/512/
- Sakurai's internal Smash 4 development notes (Source Gaming, 2017): https://sourcegaming.info/2017/06/23/internalnotes/
- *Amplify Both Strengths and Weaknesses* (YouTube, 2024): https://www.youtube.com/watch?v=fc-hOvTBTCc. Quoted via EventHubs (https://www.eventhubs.com/news/2024/aug/31/masahiro-sakurai-balance-solution-traits/) and Nintendo Life (https://www.nintendolife.com/news/2024/08/video-keep-your-peaks-and-valleys-sakurai-explains-fighter-balance-in-smash-bros)
- Character uniqueness video (YouTube, 2024): https://www.youtube.com/watch?v=zwiS1L6QVY0. Quoted via EventHubs: https://www.eventhubs.com/news/2024/apr/10/smash-creator-unique-characters/
- *Risk and Reward* (YouTube, 2022): https://www.youtube.com/watch?v=FXqEykD5Ub4. Quoted via Nintendo Life: https://www.nintendolife.com/news/2022/08/video-masahiro-sakurai-breaks-down-risk-and-reward-in-games

**Project M, Project+ and Melee mods (primary)**
- PMDT, About / mission statement (2013): https://web.archive.org/web/20130630200046/http://projectmgame.com:80/en/about
- PMDT, 3.5 Blogpost #1, Recoveries: https://web.archive.org/web/20140804053213/http://projectmgame.com/en/news/dev-blogpost-1-recoveries
- PMDT, 3.5 Blogpost #2, Tethers: https://web.archive.org/web/20140808045127/http://projectmgame.com/en/news/dev-blogpost-2-tethers
- PMDT, 3.5 Blogpost #6, Ledge Invincibility: https://web.archive.org/web/20141001152631/http://projectmgame.com/en/news/dev-blogpost-6-ledge-invincibility
- PMDT, 3.5 Blogpost #7, Trimming the Fat: https://web.archive.org/web/20141020154955/http://projectmgame.com:80/en/news/dev-blogpost-7-trimming-the-fat
- PMDT, 3.5 changelist: https://web.archive.org/web/20141119214707/http://projectmgame.com:80/en/news/project-m-3-5-changelist
- Project+, Knuckles page: https://projectplusgame.com/knuckles
- Akaneia Build, README and release notes: https://github.com/akaneia/akaneia-build and https://github.com/akaneia/akaneia-build/releases
- SmashWiki, Smash Remix: https://www.ssbwiki.com/Smash_Remix. SmashWiki, The Akaneia Build: https://www.ssbwiki.com/The_Akaneia_Build

**Other platform fighters (studio posts)**
- Rivals of Aether, "From Hero to Rival: The Development of Shovel Knight" (2018): https://store.steampowered.com/news/app/383980/view/2444779293759046757
- Rivals of Aether II, Winter Festival notes (Dec 2024): https://store.steampowered.com/news/app/2217000/view/1784506359184286
- Rivals of Aether II, Patch 1.3.3 (Orcane, Aug 2025): https://store.steampowered.com/news/app/2217000/view/1808061939507523
- Rivals of Aether II, Developer Update, June 2024: https://store.steampowered.com/news/app/2217000/view/5842939267318007945
- Brawlhalla, Back to School 2021 notes: https://store.steampowered.com/news/app/291550/view/4020014099084713623
- Nickelodeon All-Star Brawl, Update 10-18-2021: https://store.steampowered.com/news/app/1414850/view/4698935641771424073

**Melee competitive reference (SmashWiki, community-sourced)**
- Tier list: https://www.ssbwiki.com/Tier_list
- Character pages: https://www.ssbwiki.com/Fox_(SSBM), https://www.ssbwiki.com/Falco_(SSBM), https://www.ssbwiki.com/Marth_(SSBM), https://www.ssbwiki.com/Sheik_(SSBM), https://www.ssbwiki.com/Jigglypuff_(SSBM), https://www.ssbwiki.com/Peach_(SSBM), https://www.ssbwiki.com/Captain_Falcon_(SSBM), https://www.ssbwiki.com/Ice_Climbers_(SSBM), https://www.ssbwiki.com/Samus_(SSBM), https://www.ssbwiki.com/Link_(SSBM), https://www.ssbwiki.com/Young_Link_(SSBM), https://www.ssbwiki.com/Mewtwo_(SSBM)
- Moves: https://www.ssbwiki.com/Blaster_(Fox), https://www.ssbwiki.com/Blaster_(Falco), https://www.ssbwiki.com/Needle_Storm, https://www.ssbwiki.com/Charge_Shot, https://www.ssbwiki.com/Missile, https://www.ssbwiki.com/Shadow_Ball, https://www.ssbwiki.com/Vegetable
- Mechanics and rules: https://www.ssbwiki.com/Weight, https://www.ssbwiki.com/Falling_speed, https://www.ssbwiki.com/Perfect_shield, https://www.ssbwiki.com/Reflection, https://www.ssbwiki.com/Edgehogging, https://www.ssbwiki.com/L-canceling, https://www.ssbwiki.com/Camping, https://www.ssbwiki.com/Chain_grab, https://www.ssbwiki.com/Wobbling, https://www.ssbwiki.com/Tournament_rulesets_(SSBM)

**Analysis (secondary)**
- Celia Wagar, CritPoints: https://critpoints.net/2016/10/22/project-m-intro-overview/, https://critpoints.net/2017/07/07/what-makes-a-character-annoying/, https://critpoints.net/2017/11/25/critique-of-super-smash-brothers-melee-review-and-analysis/
