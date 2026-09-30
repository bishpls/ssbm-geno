# What limb growth costs a move

From `director/labs/growth_cost.py`. A grown limb's hurtboxes grow with it (the engine measures a hurtbox's radius in its bone's space), so on the hit frames they reach further: "hurt +" (world units, outward). The cast's hitboxes ride their grown bones, so their net disjoint barely moves; Geno's stay put, so his hurtbox growth comes off his disjoint whole. A Geno move is **flagged** when its disjoint loss in its hit direction exceeds every Mario-family analog's. Moves in `moves.GROW_INTANG` (utilt) make the grown part intangible while grown, so their hurt + is negative: its hurtboxes are gone on those frames. The jabs keep their full growth and pay its cost (Michael, 2026-09-29), so they stay flagged by design.

## Geno

| Move | Direction | Hurt + | Disjoint before | Disjoint now | Change | Mario family (change) | Flag | Other directions (hurt + / disjoint change) |
|---|---|---|---|---|---|---|---|---|
| jab1 | fwd | 1.74 | 9.85 | 8.78 | -1.07 | Mario jab1 -0.27, Luigi jab1 -0.21, Doc jab1 -0.28 | **yes** |  |
| jab2 | fwd | 1.28 | 8.15 | 7.17 | -0.98 | Mario jab2 -0.27, Luigi jab2 +0.00, Doc jab2 -0.29 | **yes** |  |
| jab3 | fwd | 2.03 | 9.63 | 8.28 | -1.35 | Mario jab3 +1.07, Luigi jab3 -0.56, Doc jab3 +1.08 | **yes** |  |
| dash_attack | fwd | 0.0 | 3.88 | 3.88 | 0.0 | Luigi dash_attack -0.52 |  |  |
| utilt | up | 0.0 | 9.09 | 9.09 | 0.0 | Mario utilt -0.79, Luigi utilt -0.95, Doc utilt -0.82 |  | fwd -0.47 / +0.33, back -0.47 / +0.00 |
| fsmash | fwd | 0.0 | 23.78 | 23.78 | 0.0 | Mario fsmash +0.00, Luigi fsmash -2.83, Doc fsmash +0.00 |  |  |
| fsmash_hi | fwd | 0.0 | 23.58 | 23.58 | 0.0 | Mario fsmash_hi -0.08, Luigi fsmash_hi -2.90, Doc fsmash_hi -0.07 |  |  |
| fsmash_lw | fwd | 0.0 | 21.42 | 21.42 | 0.0 | Mario fsmash_lw -0.30, Luigi fsmash_lw -2.83, Doc fsmash_lw -0.29 |  |  |
| nair | back | 0.0 | 3.8 | 3.8 | 0.0 | Mario bair +0.35, Luigi bair +0.72, Doc bair +0.80, Luigi nair -0.17 |  | down -0.00 / -0.11 |
| grab | fwd | 0.96 | 2.85 | 2.18 | -0.67 | Mario grab -0.67, Luigi grab -0.76, Doc grab -0.19 |  |  |
| dash_grab | fwd | 0.81 | 2.86 | 2.06 | -0.8 | Mario dash_grab -0.80, Luigi dash_grab -0.91, Doc dash_grab -0.79 |  |  |
| pummel | fwd | 0.0 | 5.86 | 5.86 | 0.0 | Mario pummel +0.00, Luigi pummel +0.00 |  |  |

## The cast (every move that grows a limb 1.1x or more)

- fwd: hurt + median 0.92, 90th 3.53, max 11.55; disjoint change median +0.00, 10th -0.79, min -2.90 (238 moves)
- back: hurt + median 0.00, 90th 1.11, max 6.81; disjoint change median +0.00, 10th -0.43, min -3.07 (238 moves)
- up: hurt + median 0.00, 90th 1.41, max 5.07; disjoint change median +0.00, 10th -0.24, min -1.59 (238 moves)
- down: hurt + median -0.00, 90th 0.29, max 2.69; disjoint change median +0.00, 10th -0.19, min -2.78 (238 moves)

| Fighter | Move | Largest scale | Hurt + fwd / back / up / down | Disjoint change fwd / back / up / down |
|---|---|---|---|---|
| Doc | jab1 | 2.24 | 1.74 / 0.0 / 0 / -0.0 | -0.28 / 0.0 / 0.0 / 0.04 |
| Doc | jab2 | 1.96 | 1.94 / 0.0 / 0.0 / -0.0 | -0.29 / 0.0 / 0.0 / 0.02 |
| Doc | jab3 | 2.18 | 3.53 / 0.0 / 0.0 / 1.75 | 1.08 / -0.43 / 1.64 / 0.79 |
| Doc | ftilt_hi | 1.51 | 1.16 / 0.0 / 0.0 / -0.0 | -0.16 / 0.0 / 0.63 / -0.07 |
| Doc | ftilt | 1.51 | 1.3 / 0.0 / 0.0 / -0.0 | -0.09 / 0.0 / 0.03 / -0.03 |
| Doc | ftilt_lw | 1.51 | 1.24 / 0.0 / 0.0 / -0.0 | -0.12 / 0.0 / 0.0 / 0.17 |
| Doc | utilt | 3.01 | 1.15 / 0.0 / 2.5 / -0.0 | -0.46 / 0.61 / -0.82 / 0.2 |
| Doc | dtilt | 2.0 | 4.8 / 0.0 / 0.0 / -0.0 | -0.23 / 0.0 / -0.46 / 0.23 |
| Doc | fsmash_hi | 1.64 | 2.29 / 0.36 / 0.2 / 0.06 | -0.07 / 0.0 / -0.01 / -0.01 |
| Doc | fsmash | 1.64 | 2.04 / 0.27 / 0.21 / 0.09 | 0.0 / -0.33 / 0.0 / -0.01 |
| Doc | fsmash_lw | 1.57 | 1.36 / 0.37 / 0.18 / 0.07 | -0.29 / -0.12 / 0.0 / 0.0 |
| Doc | usmash | 1.1 | 0.0 / 0.0 / 0.0 / -0.0 | 0.38 / 0.0 / 0.0 / -0.14 |
| Doc | dsmash | 1.39 | 1.23 / 1.41 / 0.0 / -0.0 | -1.35 / -1.14 / -0.5 / 0.0 |
| Doc | fair | 2.4 | 2.65 / 0.0 / 0.0 / 0.21 | 0.01 / -0.34 / 1.09 / 1.71 |
| Doc | bair | 2.0 | 0.0 / 4.66 / 0.0 / 0.11 | -0.23 / 0.8 / 0.03 / -0.04 |
| Doc | uair | 1.75 | 2.82 / 1.01 / 3.06 / -0.0 | -0.02 / -0.08 / 0.07 / 0.75 |
| Doc | grab | 1.2 | 0.0 / 0.0 / 0.0 / -0.0 | -0.19 / 0.0 / 0.0 / 0.0 |
| Doc | dash_grab | 1.2 | 0.66 / 0.0 / 0.0 / -0.0 | -0.79 / 0.0 / 0.0 / 0.0 |
| Doc | pummel | 1.2 | 0.0 / 0.0 / 0.0 / -0.0 | 0.0 / 0.0 / 0.0 / 0.0 |
| Doc | ledge_quick | 1.82 | 0.81 / 0.0 / 0.16 / -0.0 | -0.03 / 0.0 / -0.21 / 0.0 |
| Doc | ledge_slow | 1.88 | 3.45 / 0.0 / 0.0 / -0.0 | 0.0 / -0.54 / -0.14 / 0.31 |
| Luigi | jab1 | 2.08 | 1.23 / 0.0 / 0.0 / -0.0 | -0.21 / 0.0 / 0.0 / 0.08 |
| Luigi | jab2 | 1.96 | 2.19 / 0.0 / 0.0 / -0.0 | 0.0 / 0.0 / 0.0 / 0.06 |
| Luigi | jab3 | 1.9 | 0.63 / 1.05 / 0.79 / 1.12 | -0.56 / -1.39 / -0.75 / -1.17 |
| Luigi | dash_attack | 1.68 | 0.46 / 0.0 / 0.0 / -0.0 | -0.52 / 0.0 / 0.0 / 0.0 |
| Luigi | ftilt_hi | 1.51 | 1.32 / 0.0 / 0.0 / -0.0 | -0.18 / 0.0 / 0.71 / -0.07 |
| Luigi | ftilt | 1.51 | 1.48 / 0.0 / 0.0 / -0.0 | -0.11 / 0.0 / 0.05 / -0.04 |
| Luigi | ftilt_lw | 1.51 | 1.41 / 0.0 / 0.0 / -0.0 | -0.13 / 0.0 / 0.0 / 0.19 |
| Luigi | utilt | 2.34 | 1.13 / 0.91 / 3.38 / -0.0 | -0.45 / 0.0 / -0.95 / 0.0 |
| Luigi | dtilt | 1.43 | 1.82 / 0.0 / 0.0 / -0.0 | 0.02 / 0.0 / -0.41 / 0.29 |
| Luigi | fsmash_hi | 1.86 | 3.17 / 0.11 / 0.23 / 0.19 | -2.9 / -0.4 / -0.11 / -0.37 |
| Luigi | fsmash | 1.86 | 3.62 / 0.11 / 0.24 / 0.19 | -2.83 / -0.33 / -0.11 / -0.38 |
| Luigi | fsmash_lw | 1.86 | 3.62 / 0.11 / 0.21 / 0.19 | -2.83 / -0.51 / -0.07 / -0.37 |
| Luigi | usmash | 1.1 | 0.0 / 0.0 / 0.0 / -0.0 | 0.43 / 0.0 / 0.0 / -0.15 |
| Luigi | dsmash | 1.39 | 1.4 / 1.6 / 0.0 / -0.0 | -1.55 / -1.3 / -0.49 / 0.0 |
| Luigi | nair | 1.12 | 0.68 / 0.0 / 0.57 / 0.01 | 0.03 / -0.17 / 0.03 / 0.01 |
| Luigi | fair | 2.03 | 1.23 / 0.0 / 0.0 / -0.0 | -0.14 / 0.0 / 0.51 / 0.33 |
| Luigi | bair | 1.8 | 0.0 / 4.31 / 0.0 / -0.0 | -0.86 / 0.72 / 0.02 / -0.01 |
| Luigi | uair | 1.75 | 2.74 / 0.33 / 3.52 / -0.0 | -0.05 / -0.22 / 0.07 / -0.68 |
| Luigi | dair | 1.3 | 0.72 / 0.0 / 0.0 / 0.86 | -0.11 / -0.1 / -0.24 / 0.01 |
| Luigi | grab | 1.2 | 0.78 / 0.0 / 0.0 / -0.0 | -0.76 / 0.0 / 0.0 / 0.0 |
| Luigi | dash_grab | 1.2 | 0.73 / 0.0 / 0.0 / -0.0 | -0.91 / 0.0 / 0 / 0.0 |
| Luigi | pummel | 1.2 | 0.0 / 0.0 / 0.0 / -0.0 | 0.0 / 0.0 / 0.0 / 0.0 |
| Luigi | ledge_quick | 1.82 | 0.93 / 0.0 / 0.25 / -0.0 | -0.03 / 0.0 / -0.24 / 0.0 |
| Luigi | ledge_slow | 1.88 | 3.91 / 0.0 / 0.0 / -0.0 | 0.0 / -0.63 / -0.16 / 0.35 |
| Mario | jab1 | 2.24 | 1.72 / 0.0 / 0.0 / -0.0 | -0.27 / 0.0 / 0.0 / 0.03 |
| Mario | jab2 | 1.96 | 1.91 / 0.0 / 0.0 / -0.0 | -0.27 / 0.0 / 0.0 / 0.03 |
| Mario | jab3 | 2.18 | 3.53 / 0.0 / 0.0 / 1.75 | 1.07 / -0.43 / 1.64 / 0.79 |
| Mario | ftilt_hi | 1.51 | 1.16 / 0.0 / 0.0 / -0.0 | -0.16 / 0.0 / 0.64 / 0.0 |
| Mario | ftilt | 1.51 | 1.3 / 0.0 / 0.0 / -0.0 | -0.1 / 0.0 / 0.03 / -0.03 |
| Mario | ftilt_lw | 1.51 | 1.25 / 0.0 / 0.0 / -0.0 | -0.12 / 0.0 / 0.0 / 0.35 |
| Mario | utilt | 3.01 | 1.05 / 0.0 / 2.32 / -0.0 | -0.5 / 0.48 / -0.79 / 0.22 |
| Mario | dtilt | 2.0 | 4.8 / 0.0 / 0.0 / -0.0 | -0.23 / 0.0 / -0.46 / 0.23 |
| Mario | fsmash_hi | 1.64 | 2.26 / 0.36 / 0.18 / 0.07 | -0.08 / 0.0 / -0.01 / -0.01 |
| Mario | fsmash | 1.64 | 2.03 / 0.27 / 0.2 / 0.09 | 0.0 / -0.33 / 0.0 / -0.01 |
| Mario | fsmash_lw | 2.06 | 1.34 / 0.37 / 0.18 / 0.07 | -0.3 / -0.12 / 0.0 / 0.0 |
| Mario | usmash | 1.1 | 0.0 / 0.0 / 0.0 / -0.0 | 0.34 / 0.0 / 0.0 / -0.12 |
| Mario | dsmash | 1.39 | 1.23 / 1.41 / 0.0 / -0.0 | -1.36 / -1.41 / -0.4 / 0.0 |
| Mario | fair | 2.4 | 2.62 / 0.0 / 0.0 / 0.11 | 0.03 / 0.0 / 1.09 / 1.81 |
| Mario | bair | 2.0 | 0.0 / 4.66 / 0.0 / -0.0 | -0.83 / 0.35 / 0.02 / -0.05 |
| Mario | uair | 1.75 | 2.93 / 1.12 / 3.07 / -0.0 | -0.02 / -0.08 / 0.07 / 0.75 |
| Mario | grab | 1.2 | 0.69 / 0.0 / 0.0 / -0.0 | -0.67 / 0.0 / 0.0 / 0 |
| Mario | dash_grab | 1.2 | 0.64 / 0.0 / 0.0 / -0.0 | -0.8 / 0.0 / 0.0 / 0.0 |
| Mario | pummel | 1.2 | 0.0 / 0.0 / 0.0 / -0.0 | 0.0 / 0.0 / 0.0 / 0.0 |
| Mario | ledge_quick | 1.82 | 0.82 / 0.0 / 0.22 / -0.0 | -0.03 / 0.0 / -0.21 / 0.0 |
| Mario | ledge_slow | 1.88 | 3.44 / 0.0 / 0 / -0.0 | 0.01 / -0.54 / -0.14 / 0.31 |
