# Fighting-game character design principles (for a Melee Geno)

Scope: general character design and balance lessons from traditional fighting games, meant to guide a new Melee fighter.
Platform-fighter specifics are covered in a separate report; section 2 only maps these lessons onto Melee.

How to read this:
- **Evidence** is a documented statement, quoted with a source tag like [S3]; the numbered list at the end gives each URL.
  Quotes are verbatim except for normalized punctuation and bracketed edits. Tags marked *(auto-captions)* come from
  YouTube auto-transcripts, so I added punctuation and flag any guessed words in [brackets].
- **Synthesis** is my own inference. **(uncertain)** marks claims I couldn't verify.
- Some of the evidence is secondary: EventHubs translations of Japanese interviews. These are labeled.

---

## 1. Principles

### P1. A character is a gameplan: sharp strengths, real weaknesses, and tools that feed each other

**Evidence**
- Guilty Gear Strive directors (4Gamer interview, EventHubs translation) [S14]. Katano: "Regarding balance, we first look at
  that character's strength, appeal, and what makes people excited about using them." Ishiwatari: "In past titles, we had
  characters where they're long-range fighters but were actually very strong up close or grapplers who were actually very
  strong with strikes ... our development is focusing on character concepts which make sense both to us and the players."
- Sirlin [S7]: "your offense options define your gameplan—what you're actually trying to do when you play." On Fantasy
  Strike [S8]: "By carefully crafting move design and making sure moves have several different uses, it turns out that
  radically simplifying the genre still preserves the core of what's good about it."
- Harada on Tekken 5 [S18]: a top player tuned every character with "similar values," and the game "was balanced during
  playtesting, but it wasn't fun." The fix was "character specific traits. What that meant was that each character had
  their strengths and weaknesses."
- Mike Z [S10]: "why bother creating someone who is just someone else with a slightly faster projectile?"
- Riot (2XKO live balance) [S20], on an over-performing character: "his intended weaknesses aren't sufficiently offsetting
  his intended strengths."

**Synthesis.** Write Geno's gameplan in one sentence before designing any move. For example: "controls mid-range with
projectile and disjoint, converts into edgeguards; loses close scrambles." Each tool should then create the situation
another tool cashes in: a projectile forces a jump, the anti-air punishes the jump, the knockdown sets up a tech chase or
edgeguard. A move that feeds nothing is chaff (Sirlin's term in [S2]). Give him a weakness the cast can actually exploit;
one that exists only on paper doesn't count.

### P2. Aim for strong, not dominant: power should feel high but stay fair

**Evidence**
- Mike Z [S10]: "All of our characters are really strong and good at what they do, and have a lot of little technical
  quirks to exploit. It's kind of a joke around the office that whenever we reveal a new one, people automatically say
  they're 'broken' because they have so many useful moves."
- Sirlin [S6]: "there are so many games that try to fix everything and nerf everything to such a low power level that even
  though things might be 'fair,' they are no longer fun."
- Sirlin, quoting Rob Pardo [S3]: Pardo "likes the player to feel like the tools they have are extremely powerful, even
  though they are actually fair."
- Ishiwatari [S14] calls his approach "wild balance": "we don't talk about what's strong or weak, but instead what's fun or
  boring ... We sharpen certain areas and in exchange we lower other areas." Katano gives the warning: "if you keep
  [buffing], you end up with several characters who basically excel at everything, and I don't think that's right, either."

**Synthesis.** Everyone here favors a high power level, but it comes paired with trades: every sharpened area is paid for
somewhere else. The slogan "if everything is broken, nothing is" is often credited to Mike Z, but I found no primary
source for it **(unverified)**.

### P3. Every strong option needs a counter, and so does that counter

**Evidence**
- Sirlin [S2]: "The worst thing you can have in a competitive multiplayer game is a dominant move ... a move that is
  strictly better than any other you could do." Also: "moves need to have counters. If you know what the opponent will do,
  you should generally have some way of dealing with that." His HD Remix Honda set shows the pattern. A jab torpedo destroys
  fireballs and the buttslam avoids them. Ken can wait and sweep to beat both, and the full-screen torpedo beats the wait.
- Sirlin [S2]: situations inside a match need not be fair ("the local level ... does NOT need to be fair"). Only the overall
  matchup does.
- Capcom, SF6 notes [S15]: "While those attacks are part of a character's identity, if they proved too difficult for
  characters to deal with, interactions would end up in stalemates, or they would end up being the best answer to all
  situations."
- Sirlin [S2]: fighting games are secretly double-blind. "You only know that 0.3 or 0.5 seconds ago he didn't [throw a
  fireball]."

**Synthesis.** For each of Geno's key moves, write down three things: what beats it, what beats that answer, and how Geno
gets back to the original move. Anything faster than human reaction is a guess, so it needs a real downside when guessed
wrong.

### P4. Never helpless, never unanswerable: shared defense, unique offense

**Evidence**
- Mike Z [S10]: "Every character has a tool for most situations; some are worse than others, of course, like a zoning
  character should be disadvantaged if the opponent gets in, but I tried to make sure no character is completely helpless
  at any time."
- Sirlin's Guilty Gear recipe [S7]: "a robust, shared system of defense and failsafes with diverse and unique attacks for
  each character." Even Guilty Gear's burst is counterable: "Even the failsafe itself has a counter."
- Capcom [S15]: "Without an invincible attack, it proved difficult to deal with strong wake-up pressure, so now all
  characters can perform a Drive Reversal on their wake-up recovery."
- Riot [S20], on Blitzcrank and Braum: "the fact that their fastest normals have 8 frames of startup makes it hard for them
  to scrap with the faster champions' 6-frame standing light attacks."
- Keits (Iron Galaxy, KI lead combat designer) describes the opposite failure *(auto-captions)* [S21]: "Jago is not weak
  anywhere on the screen." Wind kick carried Jago out of his one weak range while leaving him "only like negative two."

**Synthesis.** Two checks follow from this. First, Geno needs a usable answer in every state: neutral, pressured, juggled,
offstage, and on the ledge. Second, he needs at least one range or state where he is genuinely weak, and no single tool
should erase it.

### P5. Guard against loops with fault-tolerant rules, not one-off patches

**Evidence**
- Mike Z (2013) [S11]: "assume players can do EVERYTHING, and assume they have already found a way past all your built-in
  safeguards. Don't think a player can find an infinite combo because of X, Y and Z? Assume they already did, and make sure
  there is something stopping them anyway." He praises MvC2's undizzy because "1) It didn't matter what combo you did,
  after a while it would end, 2) It didn't affect the combo in any way until it was triggered, and 3) It didn't need any
  intentional exceptions." MvC3's hitstun decay had exceptions, so "the system was no longer fault-tolerant."
- Mike Z (2011) [S12] on Skullgirls' infinite detection: "it's not number-of-hits based, it's not timing based, it's based
  on the combo you're actually doing ... it rewards you for finding longer things you can do rather than easy loops." Lab
  Zero later tuned undizzy "so that resets must give the defender a larger window before no longer being penalized" [S13].
- Sirlin, HD Remix [S6]: "what if one of those 10 things is so abusable that it can be repeated over and over pretty
  mindlessly, leading to shallow gameplay? ... I can remove or tone down that 1 option and leave the other 9 just as strong
  as ever."
- Killer Instinct (Double Helix) [S22] used a "Knockout Value (KV) Meter" to stop infinites. After Evo play and telemetry showed
  "a reactionary playstyle that centered around breaking combos," they added Counter Breakers.
- Sirlin [S2]: "checkmate" situations can be acceptable when hard to earn ("he basically deserves to do 100% damage"). Even
  so, in HD Remix he replaced Honda's checkmate with a Yomi Layer 3 situation.

**Synthesis.** Treat every loop Geno can form as already found. That includes throw follow-ups, multi-hit moves with fixed
knockback, and shield-locking projectile pressure. Each one needs a structural stopper that doesn't depend on the specific
combo. Long, varied combos are fine.

### P6. Frame data is the language of balance; use it to set risk against reward

**Evidence**
- Core-A Gaming *(auto-captions)* [S26]: "Generally the cheaper move will trend towards a bigger hitbox and a smaller
  hurtbox." Overpowered means "super-fast startup, lots of active frames, short recovery," plus heavy hitstun and blockstun.
- Sirlin's GDC handout [S5] lists the dials: "the damage of a move, the speed, the length of time the hitting frames are
  active, the priority, the reach, the angle, whether it can be cancelled into other moves, whether it knocks down the
  opponent."
- Riot's post-launch tuning levers [S20]: "damage, hitbox/hurtbox changes, hit reaction and pushback, hitstun and blockstun
  duration, and occasionally minor animation speed adjustments to change startup and recovery."
- Capcom [S15]: "attacks that could be canceled into special moves, had good range and short recovery, we decided to adjust
  them by adding recovery, expanding their hurtbox." Also: the Perfect Parry "gave too high of a return" for its risk.

**Synthesis.** Every move needs a spec: startup, active frames, recovery, safety on hit and on block/shield, range, hurtbox
extension, and what it leads to. A move that is fast, long-lasting, low-recovery, long-reaching, and rewarding is broken
by construction. Pick two or three of those strengths per move and make the rest weaknesses.

### P7. Readability: the opponent must be able to see, learn, and name what beat them

**Evidence**
- Capcom's Luke notes [S16]: "Camera shake added if the attack is blocked on the final active frame. Note: This was added
  to make it easier to understand when Luke has an advantage."
- Sirlin on Pardo [S2]: "super weapons" "leave the victim feeling that there is nothing they could have done (checkmate!)."
  StarCraft's nuke works because of tells: "a red targeting dot on the victim's base, and a 10 second countdown."
- Matthew DeLucas (indie FG developer) [S27], on the complaint "How do I block that?!": "if a player is asking this, I feel
  there is a failure in clear visual recognition or consistency."
- Harada (Tekken 8) [S19]: "we try to avoid mechanics or systems that people have to study or look through a manual to
  learn them." Riot staffs character teams with a VFX artist "to give their moves clarity and flair" [S20].
- Mike Z [S10] built in "protection against high/low humanly-unblockable setups."

**Synthesis.** Each of Geno's moves should have a distinct silhouette, sound, and effect, and the tells should scale with
the payoff. Any charge state or buff (Geno Beam charge, Geno Boost) has to be visible across the screen.

### P8. Put the difficulty in decisions, not inputs, and never use execution as a balance lever

**Evidence**
- Sirlin [S6]: "Let's emphasize good decision making—the true core of competitive games—and get rid of artificially
  difficult commands."
- Seth Killian [S23]: "we build them assuming everybody can do all these things ... As an empirical fact, that's just wrong."
  [S24]: "Nobody is 'impressed' by your ability to do basic moves like a dragon punch -- the magic comes in from the
  mind-games, the knowledge, the creativity."
- Mike Z [S11]: "'Oh that's really good, let's just make it really hard!' That never works."
- Riot [S20]: characters that "scale heavily with a player's technical skill" over-perform at high levels.

**Synthesis.** Killian and Mike Z describe the same fact from two sides. Design inputs for people who struggle with them,
and balance numbers as if everyone executes perfectly. Tight timing can be flavor (Geno Whirl's timed hit is core SMRPG
identity), but it can't be what keeps a move fair.

### P9. Balance by trades and root causes: fix the disease, not the symptom

**Evidence**
- Keits *(auto-captions)* [S21], on complaints about Jago's healing: "we instead took four months to really study Jago and
  figure out the root of the problem, we wanted to find the disease not the symptom ... we nerfed [wind] kick frame
  advantage, we did[n't] nerf the healing." Six weeks later "Jago now had four or five bad matchups."
- Capcom on Luke [S16]: his anti-airs and pokes "had very few gaps, leading to matches losing momentum and coming to a
  standstill." Capcom weakened those and made his "forward advancing normals ... bolstered and made easier to use."
- Riot [S20]: "we'd prefer to make forward movement better, and attacking into a retreating opponent more reliable, rather
  than make backwards movement worse."
- Sirlin [S3] rejects extra HP as a fix because "it messes with players' expectations and intuitions about how many hit
  points Guile has." (A forum summary says Mike Z's 2014 UFGT panel also rejected HP tuning. I couldn't verify this
  because the video has no transcript **(uncertain)**.)

**Synthesis.** When a Geno move tests too strong, first ask what it lets him skip: his weak range, a counter, or a
commitment. Nerf that property, then give power back where he interacts.

### P10. Test with experts early, read data skeptically, and let the top tier set the target

**Evidence**
- Sirlin [S3]: empty the "god tier" first, then the "garbage tier," then compress. "If the top tier is the target, it's
  the bottom tier you should adjust the most." Pardo's advice for unknown power levels: "make it too powerful. If you make
  it too weak, then you run the risk of no one using it at all." And: "Ignore their first reactions to nerfs." On
  suspected broken tactics [S9]: "99% of the time ... there will either be a way to counter it or other even better tactics."
- Sirlin [S6]: "I tried to make the previously weak characters about 2nd tier, knowing that it's very possible for them to
  end up better than expected ... if I tried to make them top and they ended up even above that, it would be a major
  problem."
- Mike Z [S10] held weekly sessions with players matched to each archetype ("Peacock incorporates advice from Cable
  players"). After day 1 of Evo 2011 he overhauled Parasoul and had the changes "tested on day 2."
- Riot [S20] embeds a high-level analyst in each character team so the designer gets "the experience of getting bodied by
  their champion." They flag win rates outside 47–53%, and they write: "the hallmark of a deep and rewarding fighting game
  is that skilled players can disagree about the best way to play it." They also note that frustration "always feels worse
  than the actual winrate data indicates."
- Nakayama (SF6) [S17]: "Dhalsim has a low playrate, but that doesn't mean he's a 'weak' character."
- Alex Jaffe (GDC 2015) *(auto-captions)* [S25] showed that matchup charts can predict a dominant character before it is
  obvious. Of Brawl he says: "Meta Knight has to be played at least 55% of the time in any strong community."

**Synthesis.** Adding Geno to Melee is an HD Remix-shaped problem: the tier list is established, so its top sets the
target. During testing, deliberately overshoot. For release, aim for the top of the second tier, which leaves Sirlin's
margin for testers discovering more power later.

---

## 2. What transfers to Melee, and what doesn't

All of the following is **synthesis**. Exact Melee numbers belong to the platform-fighter report.

| Traditional concept | Melee counterpart | Verdict |
|---|---|---|
| Advantage on block | Safety on shield. Shieldstun is short, so safety depends on the attacker's endlag or L-canceled landing lag versus the defender's fastest out-of-shield option, and on spacing. Shields also shrink, can be poked, and lose to grabs. | **Transfers in spirit.** Spec shield safety at best and worst spacing. |
| Hitstun combos, scaling, undizzy | Knockback grows with percent, and DI, SDI, and teching give the defender input. Combos tend to end on their own as percent rises, but Melee has no burst or breaker. Its known holes are low-percent chaingrabs, grab infinites (wobbling), and fixed-knockback multi-hits. | **Transfers strongly (P5).** There is no system-wide backstop, so Geno himself must be fault-tolerant, especially at low percent. |
| Universal defense (P4) | Shield, roll, spotdodge, airdodge, tech, DI, and ledge options are the shared skeleton, and we shouldn't change them for the 26 existing characters. | **Transfers directly.** Geno's unique offense must be answerable with Melee's existing defense. |
| Health bars, rounds | Stocks and percent. A kill depends on knockback, position, DI, and weight. | **Partial.** Damage and kill power are separate levers. Edgeguards are Melee's checkmate situations (P3, P5). |
| Corner and screen position | The ledge, platforms, blast zones, and offstage space, where recovery becomes a weakness lever. | **New axis.** Strength can be paid for with an exploitable recovery. |
| Motion-input execution | Inputs are simple; execution lives in movement tech and timing. | **P8 transfers.** Add no motion inputs or frame-perfect gimmicks. |
| 2D zoning | Platforms, air mobility, and reflectors reshape projectile play. | **Partial.** Test projectiles against platforms and reflectors. |
| Tag, assists, meter | Absent. | **Doesn't transfer.** Gate Geno's strongest tools with commitment, tells, and charge time instead of meter. |
| Live patches, telemetry | A single mod build with a small tester pool. | **Adapt.** Use Sirlin-style tier lists and Jaffe-style matchup charts against the top 8 characters. |

---

## 3. Kit review checklist

**Identity**
- [ ] One-sentence gameplan: what he wins with, where he loses (P1).
- [ ] Every move feeds another move or covers a gap; cut the chaff (P1).
- [ ] No move is just another character's move with better numbers (P1).

**Power and counterplay**
- [ ] Each key move has a written counter, a counter to that counter, and a way back (P3).
- [ ] No move is the best answer to every situation (P3).
- [ ] The weak range or state is real and survives every mobility tool (P4, P9).
- [ ] The highest-payoff move (Geno Whirl) has tells, a punishable whiff, and a bounded payoff (P2, P7).

**Coverage**
- [ ] A usable option exists in neutral, while pressured on shield, while juggled, offstage, and on the ledge (P4).
- [ ] Anti-air, anti-projectile, and anti-pressure answers each exist, even if weak (P4).

**Frame data**
- [ ] Every move has startup, active frames, endlag or landing lag, shield safety at best and worst spacing, reach, and hurtbox (P6).
- [ ] No move combines fast startup, long active frames, low lag, long reach, and high reward (P6).
- [ ] Charge and buff states have time costs the opponent can act on (P6, P7).

**Loops and degenerate states**
- [ ] Assume every repeatable pattern is already found. List them, then prove each one terminates (P5).
- [ ] Throw follow-ups, fixed-knockback multi-hits, and shield-lock pressure are tested specifically (P5).
- [ ] At 0% against all 26 existing characters, nothing is a true zero-to-death without a meaningful DI or tech read (P5).

**Readability**
- [ ] Distinct silhouette, sound, and VFX per move; nothing that looks like X but works like Y (P7).
- [ ] State changes (charge, boost) are visible across the screen (P7).

**Execution**
- [ ] No motion inputs, and no frame-perfect requirement guards a move's balance (P8).
- [ ] Numbers are balanced as if execution is perfect (P8).

**Testing**
- [ ] Testers include mains of the archetypes Geno must beat and lose to (P10).
- [ ] Deliberately overshoot in early builds, then pull back; wait a few sessions before judging nerfs (P10).
- [ ] Record tier-list placements and a matchup chart; aim for the top of the second tier (P10).
- [ ] When something tests too strong, nerf the property that skips a weakness (P9).

---

## Not found, excluded, or thin coverage
- **Mike Z's UFGTX 2014 "How to Make Fighting Games" panel** (https://www.youtube.com/watch?v=gpXganAM_qA): the video has
  no transcript, and I only found secondary summaries. Its claims aren't quoted here.
- **Arc System Works (BlazBlue), Tekken's Michael Murray, and GDC talks specifically on fighting-game frame data**: I found
  no primary rationale beyond what's cited here. The web-search budget ran out before I could dig further.
- **2XKO character-level design diaries**: only secondary coverage exists (a Lux panel summary), so it's excluded.
- **A "How to Balance the Roster" video** that search results credited to Core-A Gaming turned out to be another channel,
  so it's excluded.

## Sources
- [S2] Sirlin, "Balancing Multiplayer Games, Part 2: Viable Options." https://www.sirlin.net/articles/balancing-multiplayer-games-part-2-viable-options
- [S3] Sirlin, "Part 3: Fairness." https://www.sirlin.net/articles/balancing-multiplayer-games-part-3-fairness
- [S5] Sirlin, GDC 2009 handout, "Balancing Multiplayer Competitive Games." https://static1.squarespace.com/static/50f14d35e4b0d70ab5fc4f24/t/53ef1dbae4b0a6d424125a6f/1408179642248/GDC+2009+sirlin+handout6.pdf
- [S6] Sirlin, "Street Fighter HD Remix Design Overview." https://www.sirlin.net/sf-hdr/street-fighter-hd-remix-design-overview
- [S7] Sirlin, "Designing Defensively: Guilty Gear." https://www.sirlin.net/articles/designing-defensively-guilty-gear
- [S8] Sirlin, "A New Era of Fighting Games." https://www.sirlin.net/posts/a-new-era-of-fighting-games
- [S9] Sirlin, *Playing to Win*, "What Should Be Banned?" https://www.sirlin.net/ptw-book/what-should-be-banned
- [S10] Shoryuken (2012), "Skullgirls – Mike Z Talks History, Development, and Gameplay Philosophy." http://shoryuken.com/2012/04/09/skullgirls-mike-z-talks-history-development-and-gameplay-philosophy/ (archived: https://web.archive.org/web/2012/http://shoryuken.com/2012/04/09/skullgirls-mike-z-talks-history-development-and-gameplay-philosophy/)
- [S11] Shoryuken (2013), "From Fighting Games to Making Games Part 3: Mike Zaimont." https://web.archive.org/web/2013/http://shoryuken.com/2013/08/05/from-fighting-games-to-making-games-part-3-mike-mike-z-zaimont-lab-zero-games/
- [S12] C. Nutt, Gamasutra (2011), "Interview: An Upstart Fighting Game Developer's Radical Re-Think." https://www.gamedeveloper.com/design/interview-an-upstart-fighting-game-developer-s-radical-re-think
- [S13] Lab Zero (2017), "Skullgirls 2nd Encore: Final Patch Notes." https://web.archive.org/web/2017/https://skullgirls.com/2017/03/skullgirls-2nd-encore-final-patch-notes/
- [S14] EventHubs (2021), translating 4Gamer: "Guilty Gear Strive Directors: We're looking to prioritize fun over the balance itself." https://www.eventhubs.com/news/2021/jun/10/guilty-gear-strive-directors-balance/
- [S15] Capcom, SF6 Battle Change List, 202405 Ver. (overall notes). https://www.streetfighter.com/6/buckler/en/battle_change/202405
- [S16] Capcom, SF6 Battle Change List, Luke 202405 Ver. https://www.streetfighter.com/6/buckler/en/battle_change/202405/luke
- [S17] EventHubs (2024), translating Famitsu: Nakayama on usage stats. https://www.eventhubs.com/news/2024/jun/10/sf6-usage-character-balance/
- [S18] EventHubs (2020): Harada on Tekken 5 balance. https://www.eventhubs.com/news/2020/oct/03/harada-recounts-top-balance-tekken/
- [S19] EventHubs (2023), from Game Informer: Tekken 8 balance philosophy. https://www.eventhubs.com/news/2023/mar/30/tekken-8-balance-philosophy/
- [S20] P. Miller, Riot (2025), "2XKO: Live Balance Philosophy." https://2xko.riotgames.com/en-us/news/dev/2xko-live-balance-philosophy/
- [S21] *Fight On: The Killer Instinct Story* (documentary; Keits segment at about 73–81 min). https://www.youtube.com/watch?v=ks4eZoG94Vs
- [S22] Z. Cunningham, Game Developer (2013), "Killer Instinct design philosophy and pricing will evolve fighting games." https://www.gamedeveloper.com/game-platforms/killer-instinct-design-philosophy-and-pricing-will-evolve-fighting-games
- [S23] E. Narcisse, Kotaku (2015), "Seth Killian Wants To Help You Not Suck At Fighting Games." https://kotaku.com/seth-killian-wants-to-help-you-not-suck-at-fighting-gam-1719033575
- [S24] O. Mejia, Shacknews (2015), Seth Killian interview on Rising Thunder. https://www.shacknews.com/article/90718/rising-thunders-seth-killian-discusses-simplicity-in-design-and-the-games-future
- [S25] A. Jaffe, GDC 2015, "Metagame Balance." Slides: https://media.gdcvault.com/gdc2015/presentations/Jaffe_Alexander_Metagame_Balance.pdf ; video: https://www.youtube.com/watch?v=miu3ldl-nY4
- [S26] Core-A Gaming, "Analysis: What Makes a Move Overpowered?" https://www.youtube.com/watch?v=uQnfm911Xoc
- [S27] M. DeLucas, Game Developer (2015), "Theory: Aiding Asymmetrical Balance with Frame Data." https://www.gamedeveloper.com/design/theory-aiding-asymmetrical-balance-with-frame-data
